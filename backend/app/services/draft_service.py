"""Draft service for multi-page project CRUD operations."""

from uuid import UUID, uuid4
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.models.db import Project, Snapshot, Page
from app.models.schemas import DraftUpdate, PageCreate


class DraftService:
    """Service for managing draft snapshots and their pages."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_draft(self, project_id: UUID, user_id: UUID) -> Snapshot:
        """Get existing draft or create new one for project."""
        # Verify user owns project
        project_result = await self.db.execute(
            select(Project).where(Project.id == project_id, Project.user_id == user_id)
        )
        project = project_result.scalar_one_or_none()
        if not project:
            raise ValueError("Project not found")

        # Look for existing draft
        draft_result = await self.db.execute(
            select(Snapshot).where(
                Snapshot.project_id == project_id,
                Snapshot.is_draft == True
            )
        )
        draft = draft_result.scalar_one_or_none()

        if draft:
            return draft

        # Create new draft
        draft = Snapshot(
            id=uuid4(),
            project_id=project_id,
            version_number=0,
            is_draft=True,
            design_system={},
            navigation={},
            interview_state={},
        )
        self.db.add(draft)
        await self.db.commit()
        await self.db.refresh(draft)

        # Update project's current_draft_id
        project.current_draft_id = draft.id
        await self.db.commit()

        return draft

    async def update_draft(self, project_id: UUID, user_id: UUID, update: DraftUpdate) -> Snapshot:
        """Update draft metadata (design system, navigation, summary)."""
        draft = await self.get_or_create_draft(project_id, user_id)

        if update.design_system is not None:
            draft.design_system = update.design_system.model_dump()
        if update.navigation is not None:
            draft.navigation = update.navigation.model_dump()
        if update.summary is not None:
            draft.summary = update.summary

        await self.db.commit()
        await self.db.refresh(draft)
        return draft

    async def get_draft_pages(self, project_id: UUID, user_id: UUID) -> list[Page]:
        """Get all pages in the draft."""
        draft = await self.get_or_create_draft(project_id, user_id)

        result = await self.db.execute(
            select(Page)
            .where(Page.snapshot_id == draft.id)
            .order_by(Page.display_order)
        )
        return list(result.scalars().all())

    async def add_page(self, project_id: UUID, user_id: UUID, page_data: PageCreate) -> Page:
        """Add a page to the draft."""
        draft = await self.get_or_create_draft(project_id, user_id)

        # Check if home page already exists if adding a home page
        if page_data.is_home:
            existing_home = await self.db.execute(
                select(Page).where(
                    Page.snapshot_id == draft.id,
                    Page.is_home == True
                )
            )
            if existing_home.scalar_one_or_none():
                raise ValueError("Home page already exists in this draft")

        # Check for duplicate slug
        existing_slug = await self.db.execute(
            select(Page).where(
                Page.snapshot_id == draft.id,
                Page.slug == page_data.slug
            )
        )
        if existing_slug.scalar_one_or_none():
            raise ValueError(f"Page with slug '{page_data.slug}' already exists in this draft")

        # Get next display order
        max_order_result = await self.db.execute(
            select(func.max(Page.display_order)).where(Page.snapshot_id == draft.id)
        )
        max_order = max_order_result.scalar() or 0

        page = Page(
            id=uuid4(),
            snapshot_id=draft.id,
            slug=page_data.slug,
            title=page_data.title,
            html=page_data.html,
            js=page_data.js,
            page_metadata=page_data.metadata or {},
            is_home=page_data.is_home,
            display_order=max_order + 1,
        )
        self.db.add(page)
        await self.db.commit()
        await self.db.refresh(page)
        return page

    async def update_page(self, project_id: UUID, user_id: UUID, page_id: UUID, update: dict) -> Page:
        """Update a page in the draft."""
        draft = await self.get_or_create_draft(project_id, user_id)

        result = await self.db.execute(
            select(Page).where(
                Page.id == page_id,
                Page.snapshot_id == draft.id
            )
        )
        page = result.scalar_one_or_none()
        if not page:
            raise ValueError("Page not found")

        for key, value in update.items():
            if value is not None and hasattr(page, key):
                setattr(page, key, value)

        await self.db.commit()
        await self.db.refresh(page)
        return page

    async def delete_page(self, project_id: UUID, user_id: UUID, page_id: UUID) -> None:
        """Delete a page from the draft."""
        draft = await self.get_or_create_draft(project_id, user_id)

        result = await self.db.execute(
            select(Page).where(
                Page.id == page_id,
                Page.snapshot_id == draft.id
            )
        )
        page = result.scalar_one_or_none()
        if not page:
            raise ValueError("Page not found")

        await self.db.delete(page)
        await self.db.commit()

    async def reorder_pages(self, project_id: UUID, user_id: UUID, page_ids: list[UUID]) -> None:
        """Reorder pages in the draft."""
        draft = await self.get_or_create_draft(project_id, user_id)

        # Verify all pages belong to this draft
        result = await self.db.execute(
            select(Page).where(
                Page.id.in_(page_ids),
                Page.snapshot_id == draft.id
            )
        )
        pages = result.scalars().all()
        if len(pages) != len(page_ids):
            raise ValueError("Some pages not found in this draft")

        # Update display orders
        page_map = {p.id: p for p in pages}
        for order, page_id in enumerate(page_ids):
            if page_id in page_map:
                page_map[page_id].display_order = order

        await self.db.commit()
