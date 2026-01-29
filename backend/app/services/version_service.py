"""Version service for project history (snapshots + diffs)."""

from __future__ import annotations

from datetime import datetime
import json
from typing import Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from diff_match_patch import diff_match_patch
from sqlalchemy import select, desc, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db import (
    Project,
    ProjectPage,
    Branch,
    Version,
    VersionSnapshot,
    VersionDiff,
    VersionAttempt,
)
from app.services.subscription_service import SubscriptionService

FULL_SNAPSHOT_WINDOW = 3
MAX_PINNED_VERSIONS = 3


def _slugify(value: str) -> str:
    value = value.lower().strip()
    value = "-".join(value.split())
    cleaned = []
    for ch in value:
        if ch.isalnum() or ch == "-":
            cleaned.append(ch)
    result = "".join(cleaned).strip("-")
    return result or "page"


def _snapshot_to_text(snapshot: dict) -> str:
    return json.dumps(snapshot, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _apply_patch(base_text: str, diff_text: str) -> str:
    dmp = diff_match_patch()
    patches = dmp.patch_fromText(diff_text)
    result_text, results = dmp.patch_apply(patches, base_text)
    if not all(results):
        raise ValueError("Failed to apply version diff")
    return result_text


def _count_line_changes(old: str, new: str) -> Tuple[int, int]:
    old_lines = old.splitlines()
    new_lines = new.splitlines()
    from difflib import SequenceMatcher

    matcher = SequenceMatcher(a=old_lines, b=new_lines)
    added = 0
    deleted = 0
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "insert":
            added += j2 - j1
        elif tag == "delete":
            deleted += i2 - i1
        elif tag == "replace":
            deleted += i2 - i1
            added += j2 - j1
    return added, deleted


def _page_content_to_text(content: object) -> str:
    if not isinstance(content, dict):
        return ""
    html = content.get("html") or ""
    js = content.get("js") or ""
    if html and js:
        return f"{html}\n\n{js}"
    return html or js or ""


def _file_map_from_snapshot(snapshot: dict) -> Dict[str, str]:
    files: Dict[str, str] = {}
    pages = snapshot.get("pages", []) if isinstance(snapshot, dict) else []
    for page in pages:
        if not isinstance(page, dict):
            continue
        slug = page.get("slug") or _slugify(page.get("name") or "page")
        content = page.get("content") or {}
        if isinstance(content, dict):
            html = content.get("html") or ""
            js = content.get("js") or ""
        else:
            html = ""
            js = ""
        files[f"pages/{slug}.html"] = html
        if js:
            files[f"pages/{slug}.js"] = js
    return files


def _calculate_change_summary(
    previous: Optional[dict],
    current: dict,
    description: str = "",
    tasks_completed: Optional[List[str]] = None,
) -> dict:
    prev_files = _file_map_from_snapshot(previous) if previous else {}
    curr_files = _file_map_from_snapshot(current)

    files_changed = 0
    lines_added = 0
    lines_deleted = 0

    all_paths = set(prev_files.keys()) | set(curr_files.keys())
    for path in all_paths:
        old = prev_files.get(path, "")
        new = curr_files.get(path, "")
        if old == new:
            continue
        files_changed += 1
        added, deleted = _count_line_changes(old, new)
        lines_added += added
        lines_deleted += deleted

    return {
        "files_changed": files_changed,
        "lines_added": lines_added,
        "lines_deleted": lines_deleted,
        "tasks_completed": tasks_completed or [],
        "description": description or "",
    }


def _snapshot_from_pages(pages: List[ProjectPage]) -> dict:
    return {
        "captured_at": datetime.utcnow().isoformat(),
        "pages": [
            {
                "id": str(page.id),
                "name": page.name,
                "slug": page.slug,
                "path": page.path,
                "is_home": page.is_home,
                "content": page.content or {},
                "design_system": page.design_system or {},
                "sort_order": page.sort_order,
                "updated_at": page.updated_at.isoformat() if page.updated_at else None,
            }
            for page in pages
        ],
    }


class VersionService:
    """Version system management."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.dmp = diff_match_patch()

    async def _get_project_or_404(self, project_id: UUID, user_id: UUID) -> Project:
        result = await self.db.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()
        if not project or (project.owner_id != user_id and project.user_id != user_id):
            raise ValueError("Project not found")
        return project

    async def _ensure_default_branch(self, project_id: UUID) -> Branch:
        result = await self.db.execute(
            select(Branch).where(Branch.project_id == project_id, Branch.is_default == True)
        )
        branch = result.scalar_one_or_none()
        if branch:
            return branch
        branch = Branch(
            id=uuid4(),
            project_id=project_id,
            name="main",
            label="Main",
            is_default=True,
        )
        self.db.add(branch)
        await self.db.flush()
        return branch

    async def _get_active_branch(self, project: Project) -> Branch:
        if project.active_branch_id:
            branch = await self.db.get(Branch, project.active_branch_id)
            if branch:
                return branch
        branch = await self._ensure_default_branch(project.id)
        project.active_branch_id = branch.id
        await self.db.flush()
        return branch

    async def _get_latest_version(
        self,
        project_id: UUID,
        branch_id: Optional[UUID],
        *,
        include_failed: bool = False,
    ) -> Optional[Version]:
        query = select(Version).where(Version.project_id == project_id)
        if branch_id:
            query = query.where(Version.branch_id == branch_id)
        if not include_failed:
            query = query.where(Version.validation_status != "failed")
        result = await self.db.execute(query.order_by(desc(Version.created_at)).limit(1))
        return result.scalars().first()

    async def get_version_quota(
        self,
        project_id: UUID,
        user_id: UUID,
        branch_id: Optional[UUID] = None,
    ) -> dict:
        subscription_service = SubscriptionService(self.db)
        _, limits = await subscription_service.get_user_subscription(user_id)
        limit_value = limits.get("versions", -1)
        if limit_value is None:
            limit_value = -1

        project = await self._get_project_or_404(project_id, user_id)
        if branch_id is None:
            branch = await self._get_active_branch(project)
            branch_id = branch.id

        result = await self.db.execute(
            select(func.count())
            .select_from(Version)
            .where(
                Version.project_id == project_id,
                Version.branch_id == branch_id,
                Version.validation_status != "failed",
            )
        )
        used = result.scalar() or 0

        if limit_value == -1:
            return {
                "limit": -1,
                "used": used,
                "warning": False,
                "can_create": True,
            }

        warning_threshold = max(0, limit_value - 1)
        warning = used >= warning_threshold
        can_create = used < limit_value
        return {
            "limit": limit_value,
            "used": used,
            "warning": warning,
            "can_create": can_create,
        }

    async def _load_snapshot_data(self, snapshot_id: UUID) -> dict:
        snapshot = await self.db.get(VersionSnapshot, snapshot_id)
        return snapshot.snapshot_data if snapshot else {}

    async def _load_version_snapshot_data(self, version: Version) -> dict:
        if version.snapshot_id:
            return await self._load_snapshot_data(version.snapshot_id)
        result = await self.db.execute(
            select(VersionDiff).where(VersionDiff.version_id == version.id)
        )
        diff = result.scalar_one_or_none()
        if not diff or not diff.base_version_id:
            return {}
        base_version = await self.db.get(Version, diff.base_version_id)
        if not base_version or not base_version.snapshot_id:
            return {}
        base_data = await self._load_snapshot_data(base_version.snapshot_id)
        base_text = _snapshot_to_text(base_data)
        restored_text = _apply_patch(base_text, diff.diff_text)
        return json.loads(restored_text)

    async def list_versions(
        self,
        project_id: UUID,
        user_id: UUID,
        branch_id: Optional[UUID] = None,
        *,
        include_failed: bool = False,
    ) -> List[Version]:
        project = await self._get_project_or_404(project_id, user_id)
        query = select(Version).where(Version.project_id == project_id)
        if branch_id:
            query = query.where(Version.branch_id == branch_id)
        if not include_failed:
            query = query.where(Version.validation_status != "failed")
        result = await self.db.execute(query.order_by(desc(Version.created_at)))
        return list(result.scalars().all())

    async def get_version(
        self,
        project_id: UUID,
        user_id: UUID,
        version_id: UUID,
    ) -> Version:
        await self._get_project_or_404(project_id, user_id)
        result = await self.db.execute(
            select(Version).where(Version.id == version_id, Version.project_id == project_id)
        )
        version = result.scalar_one_or_none()
        if not version:
            raise ValueError("Version not found")
        return version

    async def get_version_snapshot(
        self,
        project_id: UUID,
        user_id: UUID,
        version_id: UUID,
    ) -> dict:
        version = await self.get_version(project_id, user_id, version_id)
        return await self._load_version_snapshot_data(version)

    async def get_version_page_diffs(
        self,
        project_id: UUID,
        user_id: UUID,
        version_id: UUID,
    ) -> dict[str, dict[str, object]]:
        project = await self._get_project_or_404(project_id, user_id)
        version = await self.get_version(project_id, user_id, version_id)
        branch_id = version.branch_id or (await self._get_active_branch(project)).id
        snapshot = await self._load_version_snapshot_data(version)
        pages = snapshot.get("pages", []) if isinstance(snapshot, dict) else []

        result = await self.db.execute(
            select(ProjectPage).where(
                ProjectPage.project_id == project_id,
                ProjectPage.branch_id == branch_id,
            )
        )
        current_pages = {str(page.id): page for page in result.scalars().all()}

        diffs: dict[str, dict[str, object]] = {}
        for page in pages:
            if not isinstance(page, dict):
                continue
            page_id = page.get("id")
            if not page_id:
                continue
            current_page = current_pages.get(str(page_id))
            if not current_page:
                diffs[str(page_id)] = {
                    "lines_added": 0,
                    "lines_deleted": 0,
                    "is_missing": True,
                }
                continue
            current_text = _page_content_to_text(current_page.content or {})
            target_text = _page_content_to_text(page.get("content") or {})
            added, deleted = _count_line_changes(current_text, target_text)
            diffs[str(page_id)] = {
                "lines_added": added,
                "lines_deleted": deleted,
                "is_missing": False,
            }
        return diffs

    async def create_version_from_project(
        self,
        project_id: UUID,
        user_id: UUID,
        *,
        description: str = "",
        tasks_completed: Optional[List[str]] = None,
        validation_status: str = "passed",
        trigger_message_id: Optional[UUID] = None,
        branch_id: Optional[UUID] = None,
        parent_version_id: Optional[UUID] = None,
    ) -> Version:
        project = await self._get_project_or_404(project_id, user_id)
        if branch_id:
            branch = await self.db.get(Branch, branch_id)
            if not branch or branch.project_id != project_id:
                raise ValueError("Branch not found")
        else:
            branch = await self._get_active_branch(project)

        pages_result = await self.db.execute(
            select(ProjectPage)
            .where(ProjectPage.project_id == project_id)
            .where(ProjectPage.branch_id == branch.id)
            .order_by(ProjectPage.sort_order)
        )
        pages = list(pages_result.scalars().all())
        snapshot_data = _snapshot_from_pages(pages)

        if validation_status == "failed":
            await self.record_failed_version(
                project_id=project_id,
                user_id=user_id,
                branch_id=branch.id,
                description=description,
                error_message="Version marked as failed",
                trigger_message_id=trigger_message_id,
                snapshot_data=snapshot_data,
            )
            raise ValueError("Failed version recorded")

        quota = await self.get_version_quota(project_id, user_id, branch.id)

        parent_version = await self._get_latest_version(
            project_id,
            branch.id,
            include_failed=False,
        )
        if parent_version_id:
            parent_override = await self.db.get(Version, parent_version_id)
            if parent_override and parent_override.project_id == project_id:
                parent_version = parent_override
        parent_snapshot = (
            await self._load_version_snapshot_data(parent_version)
            if parent_version
            else None
        )
        change_summary = _calculate_change_summary(
            parent_snapshot,
            snapshot_data,
            description=description,
            tasks_completed=tasks_completed,
        )

        version_snapshot = VersionSnapshot(
            id=uuid4(),
            project_id=project_id,
            snapshot_data=snapshot_data,
        )
        self.db.add(version_snapshot)
        await self.db.flush()

        version = Version(
            id=uuid4(),
            project_id=project_id,
            parent_version_id=parent_version.id if parent_version else None,
            branch_id=branch.id,
            branch_label=branch.label or branch.name,
            trigger_message_id=trigger_message_id,
            snapshot_id=version_snapshot.id,
            change_summary=change_summary,
            validation_status=validation_status,
            is_pinned=False,
        )
        self.db.add(version)
        await self.db.flush()

        await self._enforce_snapshot_window(project_id, branch.id)
        await self._prune_versions_to_limit(project_id, branch.id, quota.get("limit", -1))

        await self.db.commit()
        await self.db.refresh(version)
        return version

    async def record_failed_version(
        self,
        project_id: UUID,
        user_id: UUID,
        *,
        branch_id: Optional[UUID],
        description: str,
        error_message: str,
        trigger_message_id: Optional[UUID] = None,
        snapshot_data: Optional[dict] = None,
        validation_errors: Optional[list] = None,
        retry_of: Optional[UUID] = None,
    ) -> VersionAttempt:
        project = await self._get_project_or_404(project_id, user_id)
        branch = None
        if branch_id:
            branch = await self.db.get(Branch, branch_id)
        if not branch:
            branch = await self._get_active_branch(project)

        parent_version = await self._get_latest_version(
            project_id,
            branch.id,
            include_failed=False,
        )
        attempt = VersionAttempt(
            id=uuid4(),
            project_id=project_id,
            branch_id=branch.id,
            parent_version_id=parent_version.id if parent_version else None,
            trigger_message_id=trigger_message_id,
            snapshot_data=snapshot_data or {},
            validation_errors=validation_errors or [],
            error_message=error_message,
            retry_of=retry_of,
            created_at=datetime.utcnow(),
        )
        self.db.add(attempt)
        await self.db.flush()
        return attempt

    async def _prune_versions_to_limit(
        self,
        project_id: UUID,
        branch_id: UUID,
        limit: int,
    ) -> None:
        if limit == -1:
            return

        result = await self.db.execute(
            select(Version)
            .where(
                Version.project_id == project_id,
                Version.branch_id == branch_id,
                Version.validation_status != "failed",
            )
            .order_by(desc(Version.created_at))
        )
        versions = list(result.scalars().all())
        if len(versions) <= limit:
            return

        base_refs_result = await self.db.execute(
            select(VersionDiff.base_version_id)
            .where(VersionDiff.project_id == project_id)
            .where(VersionDiff.base_version_id.is_not(None))
        )
        base_refs = {row[0] for row in base_refs_result.fetchall()}

        deletable: list[Version] = []
        remaining = len(versions)
        for version in reversed(versions):
            if remaining <= limit:
                break
            if version.is_pinned or version.id in base_refs:
                continue
            deletable.append(version)
            remaining -= 1

        for version in deletable:
            if version.snapshot_id:
                snapshot = await self.db.get(VersionSnapshot, version.snapshot_id)
                if snapshot:
                    await self.db.delete(snapshot)
            await self.db.delete(version)

        if deletable:
            await self.db.flush()
            await self._enforce_snapshot_window(project_id, branch_id)

    async def _enforce_snapshot_window(self, project_id: UUID, branch_id: UUID) -> None:
        result = await self.db.execute(
            select(Version)
            .where(
                Version.project_id == project_id,
                Version.branch_id == branch_id,
                Version.validation_status != "failed",
            )
            .order_by(desc(Version.created_at))
        )
        versions = list(result.scalars().all())
        if not versions:
            return

        keep_ids = {v.id for v in versions[:FULL_SNAPSHOT_WINDOW]}
        keep_ids.update({v.id for v in versions if v.is_pinned})

        anchors: List[Version] = [v for v in versions if v.id in keep_ids and v.snapshot_id]
        if not anchors:
            return

        for version in versions:
            if version.id in keep_ids:
                if not version.snapshot_id:
                    snapshot_data = await self._load_version_snapshot_data(version)
                    snapshot = VersionSnapshot(
                        id=uuid4(),
                        project_id=project_id,
                        snapshot_data=snapshot_data,
                    )
                    self.db.add(snapshot)
                    await self.db.flush()
                    version.snapshot_id = snapshot.id
                continue

            base_version = next(
                (anchor for anchor in anchors if anchor.created_at >= version.created_at),
                None,
            )
            if not base_version:
                base_version = anchors[-1]

            if not base_version or not base_version.snapshot_id:
                continue

            base_data = await self._load_snapshot_data(base_version.snapshot_id)
            version_data = await self._load_version_snapshot_data(version)
            base_text = _snapshot_to_text(base_data)
            version_text = _snapshot_to_text(version_data)
            patches = self.dmp.patch_make(base_text, version_text)
            diff_text = self.dmp.patch_toText(patches)

            existing = await self.db.execute(
                select(VersionDiff).where(VersionDiff.version_id == version.id)
            )
            diff_row = existing.scalar_one_or_none()
            if diff_row:
                diff_row.diff_text = diff_text
                diff_row.base_version_id = base_version.id
            else:
                self.db.add(
                    VersionDiff(
                        id=uuid4(),
                        project_id=project_id,
                        version_id=version.id,
                        base_version_id=base_version.id,
                        diff_text=diff_text,
                    )
                )

            if version.snapshot_id:
                snapshot = await self.db.get(VersionSnapshot, version.snapshot_id)
                version.snapshot_id = None
                if snapshot:
                    await self.db.delete(snapshot)

    async def pin_version(
        self,
        project_id: UUID,
        user_id: UUID,
        version_id: UUID,
        pin: bool,
    ) -> Version:
        version = await self.get_version(project_id, user_id, version_id)
        if pin and not version.is_pinned:
            result = await self.db.execute(
                select(Version).where(Version.project_id == project_id, Version.is_pinned == True)
            )
            pinned = list(result.scalars().all())
            if len(pinned) >= MAX_PINNED_VERSIONS:
                raise ValueError("Pinned version limit reached")
            version.is_pinned = True
            if not version.snapshot_id:
                snapshot_data = await self._load_version_snapshot_data(version)
                snapshot = VersionSnapshot(
                    id=uuid4(),
                    project_id=project_id,
                    snapshot_data=snapshot_data,
                )
                self.db.add(snapshot)
                await self.db.flush()
                version.snapshot_id = snapshot.id
        elif not pin and version.is_pinned:
            version.is_pinned = False

        branch_id = version.branch_id
        if not branch_id:
            branch = await self._ensure_default_branch(project_id)
            branch_id = branch.id
            version.branch_id = branch_id

        await self._enforce_snapshot_window(project_id, branch_id)
        await self.db.commit()
        await self.db.refresh(version)
        return version

    async def rollback_pages(
        self,
        project_id: UUID,
        user_id: UUID,
        version_id: UUID,
        page_ids: List[UUID],
    ) -> Version:
        project = await self._get_project_or_404(project_id, user_id)
        if not page_ids:
            raise ValueError("No pages selected")
        version = await self.get_version(project_id, user_id, version_id)
        branch_id = version.branch_id or (await self._get_active_branch(project)).id
        snapshot = await self.get_version_snapshot(project_id, user_id, version_id)
        pages_data = {
            str(page.get("id")): page
            for page in snapshot.get("pages", [])
            if isinstance(page, dict)
        }

        result = await self.db.execute(
            select(ProjectPage)
            .where(
                ProjectPage.project_id == project_id,
                ProjectPage.branch_id == branch_id,
                ProjectPage.id.in_(page_ids),
            )
        )
        pages = list(result.scalars().all())
        if len(pages) != len(page_ids):
            raise ValueError("Some pages not found")

        restored_home = False
        for page in pages:
            data = pages_data.get(str(page.id))
            if not data:
                raise ValueError("Page not found in target version")
            page.name = data.get("name", page.name)
            page.slug = data.get("slug", page.slug)
            page.path = data.get("path", page.path)
            page.is_home = bool(data.get("is_home", page.is_home))
            page.content = data.get("content") or {}
            page.design_system = data.get("design_system") or {}
            page.sort_order = data.get("sort_order", page.sort_order)
            page.updated_at = datetime.utcnow()
            if page.is_home:
                restored_home = True

        if restored_home:
            await self.db.execute(
                update(ProjectPage)
                .where(
                    ProjectPage.project_id == project_id,
                    ProjectPage.branch_id == branch_id,
                    ProjectPage.id.notin_(page_ids),
                )
                .values(is_home=False)
            )

        await self.db.commit()
        return await self.create_version_from_project(
            project_id=project_id,
            user_id=user_id,
            description=f"Rollback from version {version_id}",
            tasks_completed=[f"Rollback {len(page_ids)} page(s)"],
            validation_status="passed",
            branch_id=branch_id,
        )

    async def restore_version(
        self,
        project_id: UUID,
        user_id: UUID,
        version_id: UUID,
    ) -> Version:
        project = await self._get_project_or_404(project_id, user_id)
        version = await self.get_version(project_id, user_id, version_id)
        branch_id = version.branch_id or (await self._get_active_branch(project)).id
        snapshot = await self.get_version_snapshot(project_id, user_id, version_id)
        pages_data = [page for page in snapshot.get("pages", []) if isinstance(page, dict)]
        if not pages_data:
            raise ValueError("No pages found in version")

        result = await self.db.execute(
            select(ProjectPage).where(
                ProjectPage.project_id == project_id,
                ProjectPage.branch_id == branch_id,
            )
        )
        current_pages = {str(page.id): page for page in result.scalars().all()}

        restored_home_id: Optional[str] = None
        for data in pages_data:
            page_id = data.get("id")
            if not page_id:
                continue
            page = current_pages.get(page_id)
            if not page:
                page = ProjectPage(
                    id=UUID(page_id),
                    project_id=project_id,
                    branch_id=branch_id,
                    name=data.get("name") or "Page",
                    slug=data.get("slug"),
                    path=data.get("path") or "/",
                    is_home=bool(data.get("is_home")),
                    sort_order=data.get("sort_order", 0),
                    content=data.get("content") or {},
                    design_system=data.get("design_system") or {},
                )
                self.db.add(page)
            else:
                page.name = data.get("name", page.name)
                page.slug = data.get("slug", page.slug)
                page.path = data.get("path", page.path)
                page.is_home = bool(data.get("is_home", page.is_home))
                page.sort_order = data.get("sort_order", page.sort_order)
                page.content = data.get("content") or {}
                page.design_system = data.get("design_system") or {}
                page.updated_at = datetime.utcnow()
            if page.is_home:
                restored_home_id = page_id

        if restored_home_id:
            await self.db.execute(
                update(ProjectPage)
                .where(
                    ProjectPage.project_id == project_id,
                    ProjectPage.branch_id == branch_id,
                    ProjectPage.id != UUID(restored_home_id),
                )
                .values(is_home=False)
            )

        await self.db.commit()
        return await self.create_version_from_project(
            project_id=project_id,
            user_id=user_id,
            description=f"Restored version {version_id}",
            tasks_completed=["Restore version"],
            validation_status="passed",
            branch_id=branch_id,
        )
