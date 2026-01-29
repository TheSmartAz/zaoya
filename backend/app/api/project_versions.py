"""Project version history API."""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.user import get_current_user_db
from app.models.db import Asset, Branch, ProjectPage, Project as DbProject
from app.models.schemas import (
    VersionResponse,
    VersionListResponse,
    VersionDetailResponse,
    VersionRollbackRequest,
    VersionChangeSummary,
    VersionPage,
    VersionQuota,
    BranchCreateRequest,
    BranchResponse,
)
from app.services.version_service import VersionService
from app.services.file_service import (
    _extract_components,
    _language_for_path,
    _unique_path,
    _slugify,
    _asset_filename,
    is_safe_virtual_path,
)

router = APIRouter(prefix="/api/projects/{project_id}/versions", tags=["versions"])

MAX_BRANCHES_PER_PROJECT = 3


class FileEntry(BaseModel):
    path: str
    source: str
    size: Optional[int] = None
    mime_type: Optional[str] = None
    language: Optional[str] = None


class FileListResponse(BaseModel):
    scope: str
    files: List[FileEntry]


class FileContentResponse(BaseModel):
    path: str
    source: str
    content: Optional[str] = None
    url: Optional[str] = None
    size: Optional[int] = None
    mime_type: Optional[str] = None
    language: Optional[str] = None


def _to_version_response(version) -> VersionResponse:
    summary_data = version.change_summary or {}
    summary = VersionChangeSummary(**summary_data)
    return VersionResponse(
        id=version.id,
        project_id=version.project_id,
        parent_version_id=version.parent_version_id,
        branch_id=version.branch_id,
        branch_label=version.branch_label,
        created_at=version.created_at,
        trigger_message_id=version.trigger_message_id,
        snapshot_id=version.snapshot_id,
        change_summary=summary,
        validation_status=version.validation_status,
        is_pinned=version.is_pinned,
    )


def _pages_from_snapshot(snapshot: dict) -> List[VersionPage]:
    pages: List[VersionPage] = []
    for raw in snapshot.get("pages", []) if isinstance(snapshot, dict) else []:
        if not isinstance(raw, dict):
            continue
        try:
            page = VersionPage(
                id=UUID(raw.get("id")),
                name=raw.get("name") or "Page",
                slug=raw.get("slug"),
                path=raw.get("path") or "/",
                is_home=bool(raw.get("is_home")),
                content=raw.get("content") or {},
                design_system=raw.get("design_system") or {},
                sort_order=raw.get("sort_order", 0),
            )
        except Exception:
            continue
        pages.append(page)
    return pages


def _build_version_files(snapshot: dict) -> tuple[list[FileEntry], dict[str, FileContentResponse]]:
    files: List[FileEntry] = []
    by_path: dict[str, FileContentResponse] = {}
    used_paths: set[str] = set()

    pages = snapshot.get("pages", []) if isinstance(snapshot, dict) else []
    for page in pages:
        if not isinstance(page, dict):
            continue
        slug = page.get("slug") or _slugify(page.get("name") or "page")
        content = page.get("content") or {}
        html = content.get("html") if isinstance(content, dict) else ""
        js = content.get("js") if isinstance(content, dict) else ""
        html = html or ""
        js = js or ""

        html_path = _unique_path(f"pages/{slug}.html", used_paths)
        html_entry = FileEntry(
            path=html_path,
            source="pages",
            size=len(html.encode("utf-8")) if html else 0,
            language=_language_for_path(html_path),
        )
        files.append(html_entry)
        by_path[html_path] = FileContentResponse(
            path=html_path,
            source="pages",
            content=html,
            size=html_entry.size,
            language=html_entry.language,
        )

        for name, segment in _extract_components(html):
            component_path = _unique_path(f"components/{slug}/{name}.html", used_paths)
            comp_entry = FileEntry(
                path=component_path,
                source="components",
                size=len(segment.encode("utf-8")) if segment else 0,
                language=_language_for_path(component_path),
            )
            files.append(comp_entry)
            by_path[component_path] = FileContentResponse(
                path=component_path,
                source="components",
                content=segment,
                size=comp_entry.size,
                language=comp_entry.language,
            )

        if js:
            js_path = _unique_path(f"pages/{slug}.js", used_paths)
            js_entry = FileEntry(
                path=js_path,
                source="pages",
                size=len(js.encode("utf-8")) if js else 0,
                language=_language_for_path(js_path),
            )
            files.append(js_entry)
            by_path[js_path] = FileContentResponse(
                path=js_path,
                source="pages",
                content=js,
                size=js_entry.size,
                language=js_entry.language,
            )

    return files, by_path


async def _append_assets(
    db: AsyncSession,
    project_id: UUID,
    files: list[FileEntry],
    by_path: dict[str, FileContentResponse],
    used_paths: set[str],
) -> None:
    result = await db.execute(
        select(Asset).where(Asset.project_id == project_id).order_by(Asset.created_at.desc())
    )
    for asset in result.scalars().all():
        filename = _asset_filename(asset)
        path = _unique_path(f"assets/{filename}", used_paths)
        entry = FileEntry(
            path=path,
            source="assets",
            size=asset.file_size_bytes,
            mime_type=asset.mime_type,
            language=_language_for_path(path),
        )
        files.append(entry)
        by_path[path] = FileContentResponse(
            path=path,
            source="assets",
            url=asset.url,
            size=asset.file_size_bytes,
            mime_type=asset.mime_type,
            language=entry.language,
        )


@router.get("", response_model=VersionListResponse)
async def list_versions(
    project_id: str,
    branch_id: Optional[str] = Query(None),
    include_failed: bool = Query(False),
    current_user=Depends(get_current_user_db),
    db: AsyncSession = Depends(get_db),
):
    try:
        project_uuid = UUID(project_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid project ID") from exc

    branch_uuid = None
    if branch_id:
        try:
            branch_uuid = UUID(branch_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid branch ID") from exc

    service = VersionService(db)
    try:
        versions = await service.list_versions(
            project_uuid,
            current_user.id,
            branch_uuid,
            include_failed=include_failed,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    quota_data = None
    if branch_uuid:
        quota_data = await service.get_version_quota(project_uuid, current_user.id, branch_uuid)
    return VersionListResponse(
        versions=[_to_version_response(v) for v in versions],
        quota=VersionQuota(**quota_data) if quota_data else None,
    )


@router.get("/{version_id}", response_model=VersionDetailResponse)
async def get_version_detail(
    project_id: str,
    version_id: str,
    include_diff: bool = Query(False),
    current_user=Depends(get_current_user_db),
    db: AsyncSession = Depends(get_db),
):
    try:
        project_uuid = UUID(project_id)
        version_uuid = UUID(version_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid ID") from exc

    service = VersionService(db)
    try:
        version = await service.get_version(project_uuid, current_user.id, version_uuid)
        snapshot = await service.get_version_snapshot(project_uuid, current_user.id, version_uuid)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    pages = _pages_from_snapshot(snapshot)
    if include_diff:
        diff_stats = await service.get_version_page_diffs(
            project_uuid,
            current_user.id,
            version_uuid,
        )
        updated_pages = []
        for page in pages:
            stats = diff_stats.get(str(page.id))
            if stats:
                updated_pages.append(
                    page.model_copy(
                        update={
                            "lines_added": stats.get("lines_added"),
                            "lines_deleted": stats.get("lines_deleted"),
                            "is_missing": stats.get("is_missing"),
                        }
                    )
                )
            else:
                updated_pages.append(page)
        pages = updated_pages
    return VersionDetailResponse(**_to_version_response(version).model_dump(), pages=pages)


@router.post("/{version_id}/rollback", response_model=VersionResponse)
async def rollback_version_pages(
    project_id: str,
    version_id: str,
    request: VersionRollbackRequest,
    current_user=Depends(get_current_user_db),
    db: AsyncSession = Depends(get_db),
):
    try:
        project_uuid = UUID(project_id)
        version_uuid = UUID(version_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid ID") from exc

    service = VersionService(db)
    try:
        version = await service.rollback_pages(
            project_uuid,
            current_user.id,
            version_uuid,
            request.page_ids,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_version_response(version)


@router.post("/{version_id}/restore", response_model=VersionResponse)
async def restore_version(
    project_id: str,
    version_id: str,
    current_user=Depends(get_current_user_db),
    db: AsyncSession = Depends(get_db),
):
    try:
        project_uuid = UUID(project_id)
        version_uuid = UUID(version_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid ID") from exc

    service = VersionService(db)
    try:
        version = await service.restore_version(project_uuid, current_user.id, version_uuid)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_version_response(version)


@router.post("/{version_id}/pin", response_model=VersionResponse)
async def pin_version(
    project_id: str,
    version_id: str,
    current_user=Depends(get_current_user_db),
    db: AsyncSession = Depends(get_db),
):
    try:
        project_uuid = UUID(project_id)
        version_uuid = UUID(version_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid ID") from exc

    service = VersionService(db)
    try:
        version = await service.pin_version(project_uuid, current_user.id, version_uuid, True)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_version_response(version)


@router.delete("/{version_id}/pin", response_model=VersionResponse)
async def unpin_version(
    project_id: str,
    version_id: str,
    current_user=Depends(get_current_user_db),
    db: AsyncSession = Depends(get_db),
):
    try:
        project_uuid = UUID(project_id)
        version_uuid = UUID(version_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid ID") from exc

    service = VersionService(db)
    try:
        version = await service.pin_version(project_uuid, current_user.id, version_uuid, False)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_version_response(version)


@router.get("/{version_id}/files", response_model=FileListResponse)
async def list_version_files(
    project_id: str,
    version_id: str,
    current_user=Depends(get_current_user_db),
    db: AsyncSession = Depends(get_db),
):
    try:
        project_uuid = UUID(project_id)
        version_uuid = UUID(version_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid ID") from exc

    service = VersionService(db)
    try:
        snapshot = await service.get_version_snapshot(project_uuid, current_user.id, version_uuid)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    files, by_path = _build_version_files(snapshot)
    used_paths = {entry.path for entry in files}
    await _append_assets(db, project_uuid, files, by_path, used_paths)

    return FileListResponse(scope="version", files=files)


@router.get("/{version_id}/files/content", response_model=FileContentResponse)
async def get_version_file_content(
    project_id: str,
    version_id: str,
    path: str = Query(..., min_length=1, max_length=500),
    current_user=Depends(get_current_user_db),
    db: AsyncSession = Depends(get_db),
):
    if not is_safe_virtual_path(path):
        raise HTTPException(status_code=400, detail="Invalid file path")

    try:
        project_uuid = UUID(project_id)
        version_uuid = UUID(version_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid ID") from exc

    service = VersionService(db)
    try:
        snapshot = await service.get_version_snapshot(project_uuid, current_user.id, version_uuid)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    files, by_path = _build_version_files(snapshot)
    used_paths = {entry.path for entry in files}
    await _append_assets(db, project_uuid, files, by_path, used_paths)

    record = by_path.get(path)
    if not record:
        raise HTTPException(status_code=404, detail="File not found")
    return record


@router.post("/{version_id}/branch", response_model=BranchResponse)
async def create_branch_from_version(
    project_id: str,
    version_id: str,
    request: BranchCreateRequest,
    current_user=Depends(get_current_user_db),
    db: AsyncSession = Depends(get_db),
):
    try:
        project_uuid = UUID(project_id)
        version_uuid = UUID(version_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid ID") from exc

    project_result = await db.execute(
        select(DbProject).where(
            DbProject.id == project_uuid,
            DbProject.user_id == current_user.id,
        )
    )
    project = project_result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    count_result = await db.execute(
        select(func.count()).select_from(Branch).where(Branch.project_id == project_uuid)
    )
    if (count_result.scalar_one() or 0) >= MAX_BRANCHES_PER_PROJECT:
        raise HTTPException(status_code=400, detail="Branch limit reached")

    existing = await db.execute(
        select(Branch).where(
            Branch.project_id == project_uuid,
            Branch.name == request.name,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Branch name already exists")

    service = VersionService(db)
    try:
        version = await service.get_version(project_uuid, current_user.id, version_uuid)
        snapshot = await service.get_version_snapshot(project_uuid, current_user.id, version_uuid)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    branch = Branch(
        id=uuid4(),
        project_id=project_uuid,
        name=request.name,
        label=request.label or request.name,
        parent_branch_id=version.branch_id,
        created_from_version_id=version.id,
        is_default=False,
    )
    db.add(branch)
    await db.flush()

    pages = snapshot.get("pages", []) if isinstance(snapshot, dict) else []
    has_home = False
    created_pages: list[ProjectPage] = []
    for index, page in enumerate(pages):
        if not isinstance(page, dict):
            continue
        is_home = bool(page.get("is_home"))
        if is_home:
            has_home = True
        created_pages.append(
            ProjectPage(
                id=uuid4(),
                project_id=project_uuid,
                branch_id=branch.id,
                name=page.get("name") or f"Page {index + 1}",
                slug=page.get("slug"),
                path=page.get("path") or ("/" if is_home else f"/page-{index+1}"),
                is_home=is_home,
                sort_order=page.get("sort_order", index),
                content=page.get("content") or {},
                design_system=page.get("design_system") or {},
            )
        )

    if created_pages and not has_home:
        created_pages[0].is_home = True
        created_pages[0].path = "/"

    for page in created_pages:
        db.add(page)

    await db.flush()

    try:
        await service.create_version_from_project(
            project_id=project_uuid,
            user_id=current_user.id,
            description=f"Branched from {version_uuid}",
            validation_status="passed",
            branch_id=branch.id,
            parent_version_id=version.id,
        )
    except Exception:
        pass

    if request.set_active:
        project.active_branch_id = branch.id

    await db.commit()
    await db.refresh(branch)
    return BranchResponse.model_validate(branch)
