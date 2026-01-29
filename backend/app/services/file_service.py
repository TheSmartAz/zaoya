"""File catalog service for Code Tab (read-only)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional
from uuid import UUID
import re
from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db import Asset, Page, Project, ProjectPage, Snapshot
from app.services.template_renderer import strip_script_tags
from app.services.validator import extract_body_content

ALLOWED_SCOPES = {"draft", "snapshot", "published"}
MAX_TEXT_BYTES = 1_000_000  # 1MB guard for large files
TARGET_COMPONENT_TAGS = {"section", "header", "footer", "nav", "aside"}
VOID_TAGS = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
}

TAG_RE = re.compile(r"<(/?)([a-zA-Z0-9:-]+)([^>]*)>", re.DOTALL)


@dataclass
class FileRecord:
    path: str
    source: str
    content: Optional[str] = None
    url: Optional[str] = None
    size: Optional[int] = None
    mime_type: Optional[str] = None
    language: Optional[str] = None


@dataclass
class FileCatalog:
    files: List[FileRecord]
    by_path: Dict[str, FileRecord]


def normalize_scope(scope: Optional[str]) -> str:
    value = (scope or "draft").strip().lower()
    if value not in ALLOWED_SCOPES:
        raise ValueError("Invalid scope")
    return value


def is_safe_virtual_path(path: str) -> bool:
    if not path or path.startswith("/") or "\\" in path:
        return False
    if ".." in path.split("/"):
        return False
    return True


def _slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"^-+|-+$", "", value)
    return value or "page"


def _safe_filename(value: str) -> str:
    value = value.strip()
    value = re.sub(r"\s+", "-", value)
    value = re.sub(r"[^a-zA-Z0-9._-]+", "-", value)
    return value.strip("-_.") or "asset"


def _slugify_component(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"^-+|-+$", "", value)
    return value or "component"


def _component_name(tag: str, attrs: str, index: int) -> str:
    candidates = [
        r'data-component=["\']([^"\']+)["\']',
        r'id=["\']([^"\']+)["\']',
        r'aria-label=["\']([^"\']+)["\']',
    ]
    for pattern in candidates:
        match = re.search(pattern, attrs, re.IGNORECASE)
        if match:
            return _slugify_component(match.group(1))
    return f"{tag}-{index}"


def _extract_components(html: str) -> List[tuple[str, str]]:
    if not html:
        return []
    body = strip_script_tags(extract_body_content(html))
    if not body.strip():
        return []

    components: List[tuple[str, str]] = []
    stack: List[str] = []
    start_index: int | None = None
    start_tag: str | None = None
    start_attrs: str = ""
    component_index = 0

    for match in TAG_RE.finditer(body):
        closing = match.group(1) == "/"
        tag = match.group(2).lower()
        attrs = match.group(3) or ""
        token = match.group(0)
        self_closing = token.endswith("/>") or tag in VOID_TAGS

        if not closing:
            if start_index is None and tag in TARGET_COMPONENT_TAGS and len(stack) == 0:
                start_index = match.start()
                start_tag = tag
                start_attrs = attrs
            if not self_closing:
                stack.append(tag)
        else:
            if stack:
                while stack:
                    popped = stack.pop()
                    if popped == tag:
                        break
            if start_index is not None and tag == start_tag and len(stack) == 0:
                end_index = match.end()
                segment = body[start_index:end_index].strip()
                if segment and start_tag:
                    component_index += 1
                    name = _component_name(start_tag, start_attrs, component_index)
                    components.append((name, segment))
                start_index = None
                start_tag = None
                start_attrs = ""

    return components


def _language_for_path(path: str) -> str:
    ext = path.rsplit(".", 1)[-1].lower()
    if ext in {"html", "htm"}:
        return "html"
    if ext in {"js", "mjs", "cjs"}:
        return "javascript"
    if ext in {"css"}:
        return "css"
    if ext in {"json"}:
        return "json"
    if ext in {"md", "markdown"}:
        return "markdown"
    if ext in {"svg"}:
        return "xml"
    return "text"


def _unique_path(path: str, used: set[str]) -> str:
    if path not in used:
        used.add(path)
        return path
    base, ext = path, ""
    if "." in path:
        base, ext = path.rsplit(".", 1)
        ext = f".{ext}"
    suffix = 2
    while True:
        candidate = f"{base}-{suffix}{ext}"
        if candidate not in used:
            used.add(candidate)
            return candidate
        suffix += 1


async def _get_project_pages(
    db: AsyncSession,
    project_id: UUID,
    branch_id: UUID,
) -> List[ProjectPage]:
    result = await db.execute(
        select(ProjectPage)
        .where(
            ProjectPage.project_id == project_id,
            ProjectPage.branch_id == branch_id,
        )
        .order_by(ProjectPage.sort_order)
    )
    return list(result.scalars().all())


async def _get_draft_snapshot(db: AsyncSession, project_id: UUID) -> Optional[Snapshot]:
    result = await db.execute(
        select(Snapshot).where(Snapshot.project_id == project_id, Snapshot.is_draft == True)
    )
    return result.scalar_one_or_none()


async def _get_latest_snapshot(db: AsyncSession, project_id: UUID) -> Optional[Snapshot]:
    result = await db.execute(
        select(Snapshot)
        .where(Snapshot.project_id == project_id, Snapshot.is_draft == False)
        .order_by(Snapshot.created_at.desc())
    )
    return result.scalars().first()


async def _get_snapshot_pages(db: AsyncSession, snapshot_id: UUID) -> List[Page]:
    result = await db.execute(
        select(Page)
        .where(Page.snapshot_id == snapshot_id)
        .order_by(Page.display_order)
    )
    return list(result.scalars().all())


async def _get_assets(db: AsyncSession, project_id: UUID) -> List[Asset]:
    result = await db.execute(
        select(Asset).where(Asset.project_id == project_id).order_by(Asset.created_at.desc())
    )
    return list(result.scalars().all())


def _asset_filename(asset: Asset) -> str:
    original = asset.original_filename or ""
    if original:
        safe = _safe_filename(original)
    else:
        safe = f"asset-{asset.id}"
    if "." not in safe:
        parsed = urlparse(asset.url or "")
        ext = ""
        if parsed.path and "." in parsed.path:
            ext = parsed.path.rsplit(".", 1)[-1]
        if asset.mime_type and "/" in asset.mime_type:
            ext = asset.mime_type.split("/")[-1]
        if ext:
            safe = f"{safe}.{ext}"
    return safe


def _coerce_text(content: Optional[str]) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    return str(content)


async def build_file_catalog(
    db: AsyncSession,
    project: Project,
    scope: str,
) -> FileCatalog:
    scope_value = normalize_scope(scope)
    files: List[FileRecord] = []
    used_paths: set[str] = set()

    if scope_value == "draft":
        project_pages = await _get_project_pages(db, project.id, project.active_branch_id)
        if project_pages:
            for page in project_pages:
                slug = page.slug or _slugify(page.name)
                html = _coerce_text((page.content or {}).get("html"))
                js = _coerce_text((page.content or {}).get("js"))
                html_path = _unique_path(f"pages/{slug}.html", used_paths)
                files.append(
                    FileRecord(
                        path=html_path,
                        source="pages",
                        content=html,
                        size=len(html.encode("utf-8")) if html else 0,
                        language=_language_for_path(html_path),
                    )
                )
                for name, segment in _extract_components(html):
                    component_path = _unique_path(
                        f"components/{slug}/{name}.html",
                        used_paths,
                    )
                    files.append(
                        FileRecord(
                            path=component_path,
                            source="components",
                            content=segment,
                            size=len(segment.encode("utf-8")),
                            language=_language_for_path(component_path),
                        )
                    )
                if js.strip():
                    js_path = _unique_path(f"pages/{slug}.js", used_paths)
                    files.append(
                        FileRecord(
                            path=js_path,
                            source="pages",
                            content=js,
                            size=len(js.encode("utf-8")),
                            language=_language_for_path(js_path),
                        )
                    )
        else:
            draft = await _get_draft_snapshot(db, project.id)
            if draft:
                pages = await _get_snapshot_pages(db, draft.id)
                for page in pages:
                    slug = page.slug or _slugify(page.title)
                    html = _coerce_text(page.html)
                    js = _coerce_text(page.js)
                    html_path = _unique_path(f"pages/{slug}.html", used_paths)
                    files.append(
                        FileRecord(
                            path=html_path,
                            source="pages",
                            content=html,
                            size=len(html.encode("utf-8")) if html else 0,
                            language=_language_for_path(html_path),
                        )
                    )
                    for name, segment in _extract_components(html):
                        component_path = _unique_path(
                            f"components/{slug}/{name}.html",
                            used_paths,
                        )
                        files.append(
                            FileRecord(
                                path=component_path,
                                source="components",
                                content=segment,
                                size=len(segment.encode("utf-8")),
                                language=_language_for_path(component_path),
                            )
                        )
                    if js.strip():
                        js_path = _unique_path(f"pages/{slug}.js", used_paths)
                        files.append(
                            FileRecord(
                                path=js_path,
                                source="pages",
                                content=js,
                                size=len(js.encode("utf-8")),
                                language=_language_for_path(js_path),
                            )
                        )
    elif scope_value == "snapshot":
        snapshot = await _get_latest_snapshot(db, project.id)
        if snapshot:
            pages = await _get_snapshot_pages(db, snapshot.id)
            for page in pages:
                slug = page.slug or _slugify(page.title)
                html = _coerce_text(page.html)
                js = _coerce_text(page.js)
                html_path = _unique_path(f"pages/{slug}.html", used_paths)
                files.append(
                    FileRecord(
                        path=html_path,
                        source="pages",
                        content=html,
                        size=len(html.encode("utf-8")) if html else 0,
                        language=_language_for_path(html_path),
                    )
                )
                for name, segment in _extract_components(html):
                    component_path = _unique_path(
                        f"components/{slug}/{name}.html",
                        used_paths,
                    )
                    files.append(
                        FileRecord(
                            path=component_path,
                            source="components",
                            content=segment,
                            size=len(segment.encode("utf-8")),
                            language=_language_for_path(component_path),
                        )
                    )
                if js.strip():
                    js_path = _unique_path(f"pages/{slug}.js", used_paths)
                    files.append(
                        FileRecord(
                            path=js_path,
                            source="pages",
                            content=js,
                            size=len(js.encode("utf-8")),
                            language=_language_for_path(js_path),
                        )
                    )
    elif scope_value == "published":
        if project.published_snapshot_id:
            pages = await _get_snapshot_pages(db, project.published_snapshot_id)
            for page in pages:
                slug = page.slug or _slugify(page.title)
                html = _coerce_text(page.html)
                js = _coerce_text(page.js)
                html_path = _unique_path(f"pages/{slug}.html", used_paths)
                files.append(
                    FileRecord(
                        path=html_path,
                        source="pages",
                        content=html,
                        size=len(html.encode("utf-8")) if html else 0,
                        language=_language_for_path(html_path),
                    )
                )
                for name, segment in _extract_components(html):
                    component_path = _unique_path(
                        f"components/{slug}/{name}.html",
                        used_paths,
                    )
                    files.append(
                        FileRecord(
                            path=component_path,
                            source="components",
                            content=segment,
                            size=len(segment.encode("utf-8")),
                            language=_language_for_path(component_path),
                        )
                    )
                if js.strip():
                    js_path = _unique_path(f"pages/{slug}.js", used_paths)
                    files.append(
                        FileRecord(
                            path=js_path,
                            source="pages",
                            content=js,
                            size=len(js.encode("utf-8")),
                            language=_language_for_path(js_path),
                        )
                    )

    assets = await _get_assets(db, project.id)
    for asset in assets:
        filename = _asset_filename(asset)
        path = _unique_path(f"assets/{filename}", used_paths)
        files.append(
            FileRecord(
                path=path,
                source="assets",
                url=asset.url,
                size=asset.file_size_bytes,
                mime_type=asset.mime_type,
                language=_language_for_path(path),
            )
        )

    by_path = {record.path: record for record in files}
    return FileCatalog(files=files, by_path=by_path)


def enforce_text_limit(record: FileRecord) -> FileRecord:
    if record.content is None:
        return record
    raw = record.content.encode("utf-8")
    if len(raw) <= MAX_TEXT_BYTES:
        return record
    trimmed = raw[:MAX_TEXT_BYTES]
    record.content = trimmed.decode("utf-8", errors="ignore")
    record.size = len(raw)
    return record
