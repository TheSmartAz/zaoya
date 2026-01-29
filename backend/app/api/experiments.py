"""Experiments API endpoints for A/B testing."""

from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Optional
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.db import Project, Experiment
from app.models.user import get_current_user
from app.models.schemas import (
    ExperimentCreateRequest,
    ExperimentUpdateRequest,
    VariantCreateRequest,
    VariantUpdateRequest,
    TrackConversionRequest,
)
from app.services.experiment_service import ExperimentService
from app.services.rate_limiter import tracking_rate_limiter


# ============================================================
router = APIRouter()


def _get_client_ip(request: Request) -> str:
    """Get client IP from request headers."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    return request.client.host if request.client else "unknown"


# ============================================================
# Helper Functions
# ============================================================

async def get_project_for_user(
    project_id: str,
    user_id: str,
    db: AsyncSession,
) -> Project:
    """Get project and verify user ownership."""
    try:
        pid = UUID(project_id) if isinstance(project_id, str) else project_id
        uid = UUID(user_id) if isinstance(user_id, str) else user_id
    except ValueError:
        raise HTTPException(status_code=404, detail="Project not found")

    result = await db.execute(
        select(Project).where(
            Project.id == pid,
            Project.user_id == uid
        )
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return project


# ============================================================
# Experiment CRUD Endpoints
# ============================================================

@router.post("/projects/{project_id}/experiments")
async def create_experiment(
    project_id: str,
    request: ExperimentCreateRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new A/B testing experiment."""
    project = await get_project_for_user(project_id, current_user["id"], db)
    service = ExperimentService(db)

    try:
        experiment = await service.create_experiment(
            project_id=project.id,
            name=request.name,
            traffic_split=request.traffic_split,
            conversion_goal=request.conversion_goal,
            created_by_id=UUID(current_user["id"]) if current_user.get("id") else project.user_id,
        )

        return {
            "id": str(experiment.id),
            "name": experiment.name,
            "status": experiment.status,
            "traffic_split": experiment.traffic_split,
            "conversion_goal": experiment.conversion_goal,
            "created_at": experiment.created_at.isoformat(),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/projects/{project_id}/experiments")
async def list_experiments(
    project_id: str,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List experiments for a project."""
    project = await get_project_for_user(project_id, current_user["id"], db)
    service = ExperimentService(db)

    experiments = await service.list_experiments(
        project_id=project.id,
        status=status,
    )

    return {
        "experiments": [
            {
                "id": str(e.id),
                "name": e.name,
                "status": e.status,
                "traffic_split": e.traffic_split,
                "conversion_goal": e.conversion_goal,
                "start_date": e.start_date.isoformat() if e.start_date else None,
                "end_date": e.end_date.isoformat() if e.end_date else None,
                "created_at": e.created_at.isoformat(),
            }
            for e in experiments
        ]
    }


@router.get("/projects/{project_id}/experiments/{experiment_id}")
async def get_experiment(
    project_id: str,
    experiment_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get details of a specific experiment."""
    project = await get_project_for_user(project_id, current_user["id"], db)
    service = ExperimentService(db)

    try:
        eid = UUID(experiment_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Invalid experiment ID")

    experiment = await service.get_experiment(eid)
    if not experiment or experiment.project_id != project.id:
        raise HTTPException(status_code=404, detail="Experiment not found")

    return {
        "id": str(experiment.id),
        "name": experiment.name,
        "status": experiment.status,
        "traffic_split": experiment.traffic_split,
        "conversion_goal": experiment.conversion_goal,
        "start_date": experiment.start_date.isoformat() if experiment.start_date else None,
        "end_date": experiment.end_date.isoformat() if experiment.end_date else None,
        "winner_variant_id": str(experiment.winner_variant_id) if experiment.winner_variant_id else None,
        "created_at": experiment.created_at.isoformat(),
    }


@router.patch("/projects/{project_id}/experiments/{experiment_id}")
async def update_experiment(
    project_id: str,
    experiment_id: str,
    request: ExperimentUpdateRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an experiment (only in draft status)."""
    project = await get_project_for_user(project_id, current_user["id"], db)
    service = ExperimentService(db)

    try:
        eid = UUID(experiment_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Invalid experiment ID")

    try:
        experiment = await service.update_experiment(
            experiment_id=eid,
            name=request.name,
            traffic_split=request.traffic_split,
            conversion_goal=request.conversion_goal,
        )

        # Verify ownership
        if experiment.project_id != project.id:
            raise HTTPException(status_code=404, detail="Experiment not found")

        return {
            "id": str(experiment.id),
            "name": experiment.name,
            "status": experiment.status,
            "traffic_split": experiment.traffic_split,
            "conversion_goal": experiment.conversion_goal,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/projects/{project_id}/experiments/{experiment_id}")
async def delete_experiment(
    project_id: str,
    experiment_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an experiment (only in draft status)."""
    project = await get_project_for_user(project_id, current_user["id"], db)
    service = ExperimentService(db)

    try:
        eid = UUID(experiment_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Invalid experiment ID")

    # Verify ownership first
    experiment = await service.get_experiment(eid)
    if not experiment or experiment.project_id != project.id:
        raise HTTPException(status_code=404, detail="Experiment not found")

    try:
        await service.delete_experiment(eid)
        return {"deleted": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================
# Variant Management Endpoints
# ============================================================

@router.post("/projects/{project_id}/experiments/{experiment_id}/variants")
async def add_variant(
    project_id: str,
    experiment_id: str,
    request: VariantCreateRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a variant to an experiment."""
    project = await get_project_for_user(project_id, current_user["id"], db)
    service = ExperimentService(db)

    try:
        eid = UUID(experiment_id)
        sid = UUID(request.snapshot_id) if request.snapshot_id else None
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    # Verify ownership
    experiment = await service.get_experiment(eid)
    if not experiment or experiment.project_id != project.id:
        raise HTTPException(status_code=404, detail="Experiment not found")

    try:
        variant = await service.add_variant(
            experiment_id=eid,
            name=request.name,
            is_control=request.is_control,
            snapshot_id=sid,
            page_content=request.page_content,
        )

        return {
            "id": str(variant.id),
            "name": variant.name,
            "is_control": variant.is_control,
            "snapshot_id": str(variant.snapshot_id) if variant.snapshot_id else None,
            "created_at": variant.created_at.isoformat(),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/projects/{project_id}/experiments/{experiment_id}/variants")
async def list_variants(
    project_id: str,
    experiment_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all variants for an experiment."""
    project = await get_project_for_user(project_id, current_user["id"], db)
    service = ExperimentService(db)

    try:
        eid = UUID(experiment_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Invalid experiment ID")

    # Verify ownership
    experiment = await service.get_experiment(eid)
    if not experiment or experiment.project_id != project.id:
        raise HTTPException(status_code=404, detail="Experiment not found")

    variants = await service.get_variants(eid)

    return {
        "variants": [
            {
                "id": str(v.id),
                "name": v.name,
                "is_control": v.is_control,
                "snapshot_id": str(v.snapshot_id) if v.snapshot_id else None,
                "page_content": v.page_content,
                "created_at": v.created_at.isoformat(),
            }
            for v in variants
        ]
    }


@router.patch("/projects/{project_id}/experiments/{experiment_id}/variants/{variant_id}")
async def update_variant(
    project_id: str,
    experiment_id: str,
    variant_id: str,
    request: VariantUpdateRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a variant (only in draft status)."""
    project = await get_project_for_user(project_id, current_user["id"], db)
    service = ExperimentService(db)

    try:
        eid = UUID(experiment_id)
        vid = UUID(variant_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Invalid ID format")

    # Verify ownership
    experiment = await service.get_experiment(eid)
    if not experiment or experiment.project_id != project.id:
        raise HTTPException(status_code=404, detail="Experiment not found")

    try:
        variant = await service.update_variant(
            variant_id=vid,
            name=request.name,
            page_content=request.page_content,
        )

        return {
            "id": str(variant.id),
            "name": variant.name,
            "is_control": variant.is_control,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/projects/{project_id}/experiments/{experiment_id}/variants/{variant_id}")
async def delete_variant(
    project_id: str,
    experiment_id: str,
    variant_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a variant (only in draft status)."""
    project = await get_project_for_user(project_id, current_user["id"], db)
    service = ExperimentService(db)

    try:
        eid = UUID(experiment_id)
        vid = UUID(variant_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Invalid ID format")

    # Verify ownership
    experiment = await service.get_experiment(eid)
    if not experiment or experiment.project_id != project.id:
        raise HTTPException(status_code=404, detail="Experiment not found")

    try:
        await service.delete_variant(vid)
        return {"deleted": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================
# Experiment Lifecycle Endpoints
# ============================================================

@router.post("/projects/{project_id}/experiments/{experiment_id}/start")
async def start_experiment(
    project_id: str,
    experiment_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Start an experiment (draft -> running)."""
    project = await get_project_for_user(project_id, current_user["id"], db)
    service = ExperimentService(db)

    try:
        eid = UUID(experiment_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Invalid experiment ID")

    # Verify ownership
    experiment = await service.get_experiment(eid)
    if not experiment or experiment.project_id != project.id:
        raise HTTPException(status_code=404, detail="Experiment not found")

    try:
        experiment = await service.start_experiment(
            experiment_id=eid,
            started_by_id=UUID(current_user["id"]) if current_user.get("id") else project.user_id,
        )

        return {
            "id": str(experiment.id),
            "status": experiment.status,
            "start_date": experiment.start_date.isoformat() if experiment.start_date else None,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/projects/{project_id}/experiments/{experiment_id}/pause")
async def pause_experiment(
    project_id: str,
    experiment_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Pause a running experiment."""
    project = await get_project_for_user(project_id, current_user["id"], db)
    service = ExperimentService(db)

    try:
        eid = UUID(experiment_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Invalid experiment ID")

    # Verify ownership
    experiment = await service.get_experiment(eid)
    if not experiment or experiment.project_id != project.id:
        raise HTTPException(status_code=404, detail="Experiment not found")

    try:
        experiment = await service.pause_experiment(
            experiment_id=eid,
            paused_by_id=UUID(current_user["id"]) if current_user.get("id") else project.user_id,
        )

        return {
            "id": str(experiment.id),
            "status": experiment.status,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/projects/{project_id}/experiments/{experiment_id}/resume")
async def resume_experiment(
    project_id: str,
    experiment_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Resume a paused experiment."""
    project = await get_project_for_user(project_id, current_user["id"], db)
    service = ExperimentService(db)

    try:
        eid = UUID(experiment_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Invalid experiment ID")

    # Verify ownership
    experiment = await service.get_experiment(eid)
    if not experiment or experiment.project_id != project.id:
        raise HTTPException(status_code=404, detail="Experiment not found")

    try:
        experiment = await service.resume_experiment(
            experiment_id=eid,
            resumed_by_id=UUID(current_user["id"]) if current_user.get("id") else project.user_id,
        )

        return {
            "id": str(experiment.id),
            "status": experiment.status,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/projects/{project_id}/experiments/{experiment_id}/complete")
async def complete_experiment(
    project_id: str,
    experiment_id: str,
    request: dict = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Complete an experiment and optionally declare a winner.

    Request body: {"winner_variant_id": "uuid"} (optional)
    """
    project = await get_project_for_user(project_id, current_user["id"], db)
    service = ExperimentService(db)

    try:
        eid = UUID(experiment_id)
        winner_id = UUID(request.get("winner_variant_id")) if request and request.get("winner_variant_id") else None
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    # Verify ownership
    experiment = await service.get_experiment(eid)
    if not experiment or experiment.project_id != project.id:
        raise HTTPException(status_code=404, detail="Experiment not found")

    try:
        experiment = await service.complete_experiment(
            experiment_id=eid,
            completed_by_id=UUID(current_user["id"]) if current_user.get("id") else project.user_id,
            winner_variant_id=winner_id,
        )

        return {
            "id": str(experiment.id),
            "status": experiment.status,
            "end_date": experiment.end_date.isoformat() if experiment.end_date else None,
            "winner_variant_id": str(experiment.winner_variant_id) if experiment.winner_variant_id else None,
            "winner_confidence": float(experiment.winner_confidence) if experiment.winner_confidence else None,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================
# Results & Analytics Endpoints
# ============================================================

@router.get("/projects/{project_id}/experiments/{experiment_id}/results")
async def get_experiment_results(
    project_id: str,
    experiment_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get comprehensive results for an experiment."""
    project = await get_project_for_user(project_id, current_user["id"], db)
    service = ExperimentService(db)

    try:
        eid = UUID(experiment_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Invalid experiment ID")

    # Verify ownership
    experiment = await service.get_experiment(eid)
    if not experiment or experiment.project_id != project.id:
        raise HTTPException(status_code=404, detail="Experiment not found")

    return await service.get_experiment_results(eid)


# ============================================================
# Public Tracking Endpoints (no auth required)
# ============================================================

@router.get("/experiments/{public_id}/variant")
async def get_assigned_variant_public(
    public_id: str,
    request: Request,
    visitor_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Get the assigned variant for a visitor (public endpoint).

    Uses deterministic hashing to consistently assign the same visitor
    to the same variant.
    """
    from sqlalchemy import select
    from app.models.db import Project

    # Rate limit (10 req/min per IP per public page)
    client_ip = _get_client_ip(request)
    identifier = f"exp_assign:{public_id}:{client_ip}"
    is_limited, remaining = await tracking_rate_limiter.check_and_record(
        identifier=identifier,
        max_attempts=10,
        window_seconds=60,
    )
    if is_limited:
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please try again later.",
            headers={
                "Retry-After": "60",
                "X-RateLimit-Limit": "10",
                "X-RateLimit-Remaining": str(remaining),
                "X-RateLimit-Window": "60",
            },
        )

    if not visitor_id:
        visitor_id = f"v_{uuid4().hex}"

    # Get project by public_id
    result = await db.execute(
        select(Project).where(
            Project.public_id == public_id,
            Project.status == "published"
        )
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get running experiments for this project
    service = ExperimentService(db)
    experiments = await service.list_experiments(
        project_id=project.id,
        status="running",
    )

    variants_data = []
    for exp in experiments:
        try:
            variant, is_new = await service.get_or_assign_variant(
                experiment_id=exp.id,
                visitor_id=visitor_id,
            )
            variants_data.append({
                "experiment_id": str(exp.id),
                "variant_id": str(variant.id),
                "variant_name": variant.name,
                "is_control": variant.is_control,
                "content": variant.page_content,
            })
        except ValueError:
            # Skip experiments that can't be assigned
            pass

    return {
        "experiments": variants_data,
        "visitor_id": visitor_id,
    }


@router.post("/experiments/{public_id}/track")
async def track_conversion_public(
    public_id: str,
    visitor_id: str,
    request: TrackConversionRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Track a conversion event (public endpoint).

    Called from published pages when a conversion goal is met.
    """
    from sqlalchemy import select
    from app.models.db import Project

    # Get project by public_id
    result = await db.execute(
        select(Project).where(
            Project.public_id == public_id,
            Project.status == "published"
        )
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    service = ExperimentService(db)
    experiments = await service.list_experiments(
        project_id=project.id,
        status="running",
    )

    tracked_count = 0
    for exp in experiments:
        # Check if conversion goal matches
        goal_type = exp.conversion_goal.get("type")
        if goal_type and goal_type == request.goal_type:
            success = await service.track_conversion(
                experiment_id=exp.id,
                visitor_id=visitor_id,
                goal_type=request.goal_type,
                goal_metadata=request.goal_metadata,
            )
            if success:
                tracked_count += 1

    return {
        "tracked": tracked_count,
        "visitor_id": visitor_id,
    }
