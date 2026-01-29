"""Public read API for published pages (cacheable, no auth required)."""

from fastapi import APIRouter, HTTPException, Request, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.db import get_db
from app.models.db import Project, Snapshot, Page, User


router = APIRouter(prefix="/public", tags=["public"])


@router.get("/projects/{public_id}")
async def get_published_project(
    public_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get published project manifest (navigation, design system, pages list).

    This endpoint is cacheable and powers the published site experience.
    """
    # Get project with published snapshot
    result = await db.execute(
        select(Project).where(
            Project.public_id == public_id,
            Project.status == 'published'
        )
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not project.published_snapshot_id:
        raise HTTPException(status_code=404, detail="Project not published")

    # Get snapshot
    snapshot_result = await db.execute(
        select(Snapshot).where(Snapshot.id == project.published_snapshot_id)
    )
    snapshot = snapshot_result.scalar_one_or_none()
    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot not found")

    # Resolve vanity base path if available
    base_path = f"/p/{public_id}"
    if project.user_id and project.slug:
        user_result = await db.execute(
            select(User).where(User.id == project.user_id)
        )
        user = user_result.scalar_one_or_none()
        if user and user.username:
            base_path = f"/u/{user.username}/{project.slug}"

    # Get pages
    pages_result = await db.execute(
        select(Page).where(Page.snapshot_id == snapshot.id)
        .order_by(Page.display_order)
    )
    pages = list(pages_result.scalars().all())

    return {
        "public_id": public_id,
        "name": project.name,
        "design_system": snapshot.design_system or {},
        "navigation": snapshot.navigation or {},
        "summary": snapshot.summary,
        "pages": [
            {
                "slug": p.slug,
                "title": p.title,
                "is_home": p.is_home,
                "url": f"{base_path}/{'' if p.is_home else p.slug}".rstrip("/"),
            }
            for p in pages
        ],
    }


@router.get("/projects/{public_id}/page")
@router.get("/projects/{public_id}/pages/{page_slug}")
async def get_published_page(
    public_id: str,
    page_slug: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific published page's HTML content.

    - If page_slug is None or empty, returns the home page
    - Otherwise returns the page with the matching slug
    """
    # Get project
    project_result = await db.execute(
        select(Project).where(
            Project.public_id == public_id,
            Project.status == 'published'
        )
    )
    project = project_result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get snapshot
    snapshot_result = await db.execute(
        select(Snapshot).where(Snapshot.id == project.published_snapshot_id)
    )
    snapshot = snapshot_result.scalar_one_or_none()
    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot not found")

    # Get page - if no slug provided, get home page
    if not page_slug:
        page_result = await db.execute(
            select(Page).where(
                Page.snapshot_id == snapshot.id,
                Page.is_home == True
            )
        )
    else:
        page_result = await db.execute(
            select(Page).where(
                Page.snapshot_id == snapshot.id,
                Page.slug == page_slug
            )
        )

    page = page_result.scalar_one_or_none()
    if not page:
        # If specific slug not found, try home page as fallback
        if page_slug:
            page_result = await db.execute(
                select(Page).where(
                    Page.snapshot_id == snapshot.id,
                    Page.is_home == True
                )
            )
            page = page_result.scalar_one_or_none()
        if not page:
            raise HTTPException(status_code=404, detail="Page not found")

    return {
        "slug": page.slug,
        "title": page.title,
        "html": page.html,
        "js": page.js,
        "metadata": page.page_metadata or {},
        "is_home": page.is_home,
    }


@router.get("/projects/{public_id}/experiment")
async def get_experiment_variant(
    public_id: str,
    visitor_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get the active experiment variant for a visitor.

    Uses deterministic hashing to assign the same visitor to the same variant.
    Returns the variant content for rendering.
    """
    from app.models.db.experiment import Experiment, ExperimentAssignment, ExperimentVariant
    import hashlib

    # Get project
    project_result = await db.execute(
        select(Project).where(
            Project.public_id == public_id,
            Project.status == 'published'
        )
    )
    project = project_result.scalar_one_or_none()
    if not project:
        return {"experiments": []}

    # Get active experiments for this project
    experiments_result = await db.execute(
        select(Experiment).where(
            Experiment.project_id == project.id,
            Experiment.status == 'running'
        )
    )
    experiments = list(experiments_result.scalars().all())

    variants_data = []

    for exp in experiments:
        # Check for existing assignment
        assignment_result = await db.execute(
            select(ExperimentAssignment).where(
                ExperimentAssignment.experiment_id == exp.id,
                ExperimentAssignment.visitor_id == visitor_id
            )
        )
        assignment = assignment_result.scalar_one_or_none()

        if assignment:
            # Get assigned variant
            variant_result = await db.execute(
                select(ExperimentVariant).where(
                    ExperimentVariant.id == assignment.variant_id
                )
            )
            variant = variant_result.scalar_one_or_none()
            if variant:
                variants_data.append({
                    "experiment_id": str(exp.id),
                    "variant_id": str(variant.id),
                    "name": variant.name,
                    "is_control": variant.is_control,
                    "content": variant.page_content or {},
                })
        else:
            # Assign new variant using deterministic hashing
            variants_result = await db.execute(
                select(ExperimentVariant).where(
                    ExperimentVariant.experiment_id == exp.id
                ).order_by(ExperimentVariant.is_control.desc())
            )
            variants = list(variants_result.scalars().all())

            if variants:
                # Use consistent hash to pick variant
                hash_input = f"{visitor_id}:{exp.id}"
                hash_value = int(hashlib.sha256(hash_input.encode()).hexdigest(), 16)
                variant_index = hash_value % len(variants)
                selected = variants[variant_index]

                # Store assignment
                from uuid import uuid4
                new_assignment = ExperimentAssignment(
                    id=uuid4(),
                    experiment_id=exp.id,
                    variant_id=selected.id,
                    visitor_id=visitor_id,
                )
                db.add(new_assignment)
                await db.commit()

                variants_data.append({
                    "experiment_id": str(exp.id),
                    "variant_id": str(selected.id),
                    "name": selected.name,
                    "is_control": selected.is_control,
                    "content": selected.page_content or {},
                })

    return {"experiments": variants_data}


@router.post("/projects/{public_id}/track")
async def track_analytics(
    public_id: str,
    event_data: dict,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Track analytics event for a published page.

    This endpoint is designed to be called from published pages.
    For the actual tracking, use /api/analytics/track/{public_id} instead.
    This is a convenience alias for the public API.
    """
    from app.services.analytics_service import AnalyticsService

    # Verify project exists
    project_result = await db.execute(
        select(Project).where(
            Project.public_id == public_id,
            Project.status == 'published'
        )
    )
    project = project_result.scalar_one_or_none()
    if not project:
        return {"success": False}

    # Generate visitor ID
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent", "")
    visitor_id = AnalyticsService.hash_visitor(client_ip, user_agent)

    # Track the event
    service = AnalyticsService(db)
    await service.track_event(
        project_id=project.id,
        visitor_id=visitor_id,
        event_type=event_data.get("type", "custom"),
        properties=event_data.get("data", {}),
        context={
            "referrer": request.headers.get("referer"),
            "device_type": event_data.get("device_type", "desktop"),
        },
    )

    return {"success": True}
