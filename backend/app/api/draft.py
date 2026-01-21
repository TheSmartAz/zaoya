"""Draft API endpoints for multi-page project CRUD."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.user import get_current_user
from app.models.db import User
from app.services.draft_service import DraftService
from app.models.schemas import (
    DraftResponse,
    DraftUpdate,
    PageResponse,
    PageCreate,
    PageUpdate,
    ReorderPagesRequest,
)

router = APIRouter(prefix="/api/projects/{project_id}/draft", tags=["draft"])


@router.get("", response_model=DraftResponse)
async def get_draft(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get or create the current draft for a project."""
    from uuid import UUID

    service = DraftService(db)
    draft = await service.get_or_create_draft(UUID(project_id), current_user.id)
    return DraftResponse(
        id=draft.id,
        project_id=draft.project_id,
        version_number=draft.version_number,
        summary=draft.summary,
        design_system=draft.design_system or {},
        navigation=draft.navigation or {},
        created_at=draft.created_at,
    )


@router.post("", response_model=DraftResponse)
async def create_draft(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new draft (same as get)."""
    from uuid import UUID

    service = DraftService(db)
    draft = await service.get_or_create_draft(UUID(project_id), current_user.id)
    return DraftResponse(
        id=draft.id,
        project_id=draft.project_id,
        version_number=draft.version_number,
        summary=draft.summary,
        design_system=draft.design_system or {},
        navigation=draft.navigation or {},
        created_at=draft.created_at,
    )


@router.patch("", response_model=DraftResponse)
async def update_draft(
    project_id: str,
    update: DraftUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update draft design system or navigation."""
    from uuid import UUID

    service = DraftService(db)
    draft = await service.update_draft(UUID(project_id), current_user.id, update)
    return DraftResponse(
        id=draft.id,
        project_id=draft.project_id,
        version_number=draft.version_number,
        summary=draft.summary,
        design_system=draft.design_system or {},
        navigation=draft.navigation or {},
        created_at=draft.created_at,
    )


@router.get("/pages", response_model=list[PageResponse])
async def get_draft_pages(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all pages in the draft."""
    from uuid import UUID

    service = DraftService(db)
    pages = await service.get_draft_pages(UUID(project_id), current_user.id)
    return [
        PageResponse(
            id=p.id,
            slug=p.slug,
            title=p.title,
            html=p.html,
            js=p.js,
            metadata=p.page_metadata or {},
            is_home=p.is_home,
            display_order=p.display_order,
            created_at=p.created_at,
        )
        for p in pages
    ]


@router.post("/pages", response_model=PageResponse, status_code=status.HTTP_201_CREATED)
async def add_page(
    project_id: str,
    page_data: PageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a new page to the draft."""
    from uuid import UUID

    service = DraftService(db)
    # Convert metadata to dict
    page_dict = page_data.model_dump()
    page_dict["metadata"] = page_data.metadata or {}
    page = await service.add_page(UUID(project_id), current_user.id, PageCreate(**page_dict))
    return PageResponse(
        id=page.id,
        slug=page.slug,
        title=page.title,
        html=page.html,
        js=page.js,
        metadata=page.page_metadata or {},
        is_home=page.is_home,
        display_order=page.display_order,
        created_at=page.created_at,
    )


@router.patch("/pages/{page_id}", response_model=PageResponse)
async def update_page(
    project_id: str,
    page_id: str,
    update: PageUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a page in the draft."""
    from uuid import UUID

    service = DraftService(db)
    page = await service.update_page(
        UUID(project_id),
        current_user.id,
        UUID(page_id),
        update.model_dump(exclude_unset=True)
    )
    return PageResponse(
        id=page.id,
        slug=page.slug,
        title=page.title,
        html=page.html,
        js=page.js,
        metadata=page.page_metadata or {},
        is_home=page.is_home,
        display_order=page.display_order,
        created_at=page.created_at,
    )


@router.delete("/pages/{page_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_page(
    project_id: str,
    page_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a page from the draft."""
    from uuid import UUID

    service = DraftService(db)
    await service.delete_page(UUID(project_id), current_user.id, UUID(page_id))


@router.post("/pages/reorder", status_code=status.HTTP_204_NO_CONTENT)
async def reorder_pages(
    project_id: str,
    request: ReorderPagesRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reorder pages in the draft."""
    from uuid import UUID

    service = DraftService(db)
    await service.reorder_pages(UUID(project_id), current_user.id, request.page_ids)
