"""Snapshot service for version management."""

from uuid import UUID, uuid4
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from copy import deepcopy

from app.db import AsyncSessionLocal
from app.models.db import Project, Snapshot, Page
from app.models.schemas import CreateSnapshotRequest


class SnapshotService:
    """Service for managing immutable snapshots."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_snapshots(self, project_id: UUID, user_id: UUID) -> list[Snapshot]:
        """List all non-draft snapshots for a project."""
        # Verify user owns project
        project_result = await self.db.execute(
            select(Project).where(Project.id == project_id, Project.user_id == user_id)
        )
        if not project_result.scalar_one_or_none():
            raise ValueError("Project not found")

        result = await self.db.execute(
            select(Snapshot)
            .where(
                Snapshot.project_id == project_id,
                Snapshot.is_draft == False
            )
            .order_by(Snapshot.created_at.desc())
        )
        return list(result.scalars().all())

    async def create_snapshot(
        self,
        project_id: UUID,
        user_id: UUID,
        request: CreateSnapshotRequest
    ) -> Snapshot:
        """Create an immutable snapshot from the current draft."""
        from app.services.draft_service import DraftService

        draft_service = DraftService(self.db)
        draft = await draft_service.get_or_create_draft(project_id, user_id)

        # Get next version number
        max_version_result = await self.db.execute(
            select(func.max(Snapshot.version_number)).where(
                Snapshot.project_id == project_id,
                Snapshot.is_draft == False
            )
        )
        next_version = (max_version_result.scalar() or 0) + 1

        # Copy draft pages to new snapshot
        draft_pages_result = await self.db.execute(
            select(Page).where(Page.snapshot_id == draft.id)
        )
        draft_pages = draft_pages_result.scalars().all()

        # Create snapshot
        snapshot = Snapshot(
            id=uuid4(),
            project_id=project_id,
            version_number=next_version,
            summary=request.summary or f"Version {next_version}",
            design_system=deepcopy(draft.design_system) if draft.design_system else {},
            navigation=deepcopy(draft.navigation) if draft.navigation else {},
            is_draft=False,
        )
        self.db.add(snapshot)
        await self.db.flush()  # Get the ID

        # Copy pages
        for page in draft_pages:
            new_page = Page(
                id=uuid4(),
                snapshot_id=snapshot.id,
                slug=page.slug,
                title=page.title,
                html=page.html,
                js=page.js,
                page_metadata=deepcopy(page.page_metadata) if page.page_metadata else {},
                is_home=page.is_home,
                display_order=page.display_order,
            )
            self.db.add(new_page)

        await self.db.commit()
        await self.db.refresh(snapshot)
        return snapshot

    async def get_snapshot(self, project_id: UUID, user_id: UUID, snapshot_id: UUID) -> Optional[Snapshot]:
        """Get a specific snapshot."""
        # Verify user owns project
        project_result = await self.db.execute(
            select(Project).where(Project.id == project_id, Project.user_id == user_id)
        )
        if not project_result.scalar_one_or_none():
            raise ValueError("Project not found")

        result = await self.db.execute(
            select(Snapshot).where(
                Snapshot.id == snapshot_id,
                Snapshot.project_id == project_id
            )
        )
        return result.scalar_one_or_none()

    async def restore_snapshot(self, project_id: UUID, user_id: UUID, snapshot_id: UUID) -> Snapshot:
        """Restore a snapshot to become the new draft."""
        from app.services.draft_service import DraftService

        # Get the snapshot to restore
        snapshot = await self.get_snapshot(project_id, user_id, snapshot_id)
        if not snapshot:
            raise ValueError("Snapshot not found")

        if snapshot.is_draft:
            raise ValueError("Cannot restore a draft snapshot")

        draft_service = DraftService(self.db)

        # Get existing draft
        draft_result = await self.db.execute(
            select(Snapshot).where(
                Snapshot.project_id == project_id,
                Snapshot.is_draft == True
            )
        )
        old_draft = draft_result.scalar_one_or_none()

        # Create new draft from snapshot
        new_draft = Snapshot(
            id=uuid4(),
            project_id=project_id,
            version_number=0,
            summary=f"Restored from version {snapshot.version_number}",
            design_system=snapshot.design_system.copy() if snapshot.design_system else {},
            navigation=snapshot.navigation.copy() if snapshot.navigation else {},
            is_draft=True,
        )
        self.db.add(new_draft)
        await self.db.flush()

        # Copy pages from snapshot
        pages_result = await self.db.execute(
            select(Page).where(Page.snapshot_id == snapshot_id)
        )
        old_pages = pages_result.scalars().all()

        for page in old_pages:
            new_page = Page(
                id=uuid4(),
                snapshot_id=new_draft.id,
                slug=page.slug,
                title=page.title,
                html=page.html,
                js=page.js,
                page_metadata=page.page_metadata.copy() if page.page_metadata else {},
                is_home=page.is_home,
                display_order=page.display_order,
            )
            self.db.add(new_page)

        # Delete old draft (pages will cascade delete)
        if old_draft:
            await self.db.delete(old_draft)

        # Update project
        project_result = await self.db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = project_result.scalar_one()
        project.current_draft_id = new_draft.id

        await self.db.commit()
        await self.db.refresh(new_draft)
        return new_draft


class _SnapshotServiceFacade:
    """Facade for build runtime tooling (manages DB session internally)."""

    async def _get_project_user(self, db: AsyncSession, project_id: UUID) -> UUID:
        result = await db.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()
        if not project:
            raise ValueError("Project not found")
        return project.user_id

    async def create(self, project_id: str, reason: str, metadata: dict | None = None) -> str:
        from uuid import UUID as UUIDType

        async with AsyncSessionLocal() as db:
            project_uuid = UUIDType(project_id)
            user_id = await self._get_project_user(db, project_uuid)
            service = SnapshotService(db)
            request = CreateSnapshotRequest(summary=reason)
            snapshot = await service.create_snapshot(project_uuid, user_id, request)
            return str(snapshot.id)

    async def restore(self, snapshot_id: str, project_id: str) -> bool:
        from uuid import UUID as UUIDType

        async with AsyncSessionLocal() as db:
            project_uuid = UUIDType(project_id)
            user_id = await self._get_project_user(db, project_uuid)
            service = SnapshotService(db)
            await service.restore_snapshot(project_uuid, user_id, UUIDType(snapshot_id))
            return True


def get_snapshot_service() -> _SnapshotServiceFacade:
    """Return a snapshot service facade for internal tooling."""
    return _SnapshotServiceFacade()
