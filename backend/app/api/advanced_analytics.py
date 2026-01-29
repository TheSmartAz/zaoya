"""Advanced Analytics API endpoints for funnels, cohorts, and insights."""

from datetime import date, timedelta
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.db import Project
from app.models.user import get_current_user
from app.services.advanced_analytics_service import AdvancedAnalyticsService


# ============================================================
# Request/Response Models
# ============================================================

class CreateFunnelRequest(BaseModel):
    """Request to create a funnel."""
    name: str
    steps: list[dict]


class AnalyzeFunnelRequest(BaseModel):
    """Request to analyze a funnel."""
    name: str
    steps: list[dict]
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    segment_by: Optional[str] = None


class AttributionQuery(BaseModel):
    """Query model for attribution."""
    model: Optional[str] = None


router = APIRouter()


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
# Funnel Analysis Endpoints
# ============================================================

@router.post("/projects/{project_id}/funnels")
async def create_funnel(
    project_id: str,
    request: CreateFunnelRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new funnel definition."""
    project = await get_project_for_user(project_id, current_user["id"], db)
    service = AdvancedAnalyticsService(db)

    funnel = await service.create_funnel(
        project_id=project.id,
        name=request.name,
        steps=request.steps,
        created_by_id=UUID(current_user["id"]) if current_user.get("id") else project.user_id,
    )

    return {
        "id": str(funnel.id),
        "name": funnel.name,
        "steps": funnel.steps,
        "created_at": funnel.created_at.isoformat(),
    }


@router.post("/projects/{project_id}/funnels/analyze")
async def analyze_funnel(
    project_id: str,
    request: AnalyzeFunnelRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Analyze a conversion funnel.

    Request body:
    {
        "name": "Checkout Funnel",
        "steps": [
            {"name": "Visit", "event_type": "page_view", "filters": {"url": "/"}},
            {"name": "View Product", "event_type": "page_view", "filters": {"url": "/product"}},
            {"name": "Add to Cart", "event_type": "cta_click", "filters": {"element_id": "add-to-cart"}},
            {"name": "Checkout", "event_type": "page_view", "filters": {"url": "/checkout"}},
            {"name": "Purchase", "event_type": "form_submit", "filters": {"form_id": "order"}}
        ],
        "start_date": "2024-01-01",
        "end_date": "2024-01-31"
    }
    """
    project = await get_project_for_user(project_id, current_user["id"], db)
    service = AdvancedAnalyticsService(db)

    # Build funnel definition from request
    funnel_def = {
        "name": request.name,
        "steps": request.steps,
    }

    results = await service.analyze_funnel(
        project_id=project.id,
        funnel_def=funnel_def,
        start_date=request.start_date,
        end_date=request.end_date,
        segment_by=request.segment_by,
    )

    return results


@router.get("/projects/{project_id}/funnels/saved")
async def list_saved_funnels(
    project_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List saved funnel definitions."""
    project = await get_project_for_user(project_id, current_user["id"], db)

    from app.models.db.analytics import AnalyticsFunnel

    result = await db.execute(
        select(AnalyticsFunnel)
        .where(AnalyticsFunnel.project_id == project.id)
        .order_by(AnalyticsFunnel.created_at.desc())
    )

    funnels = []
    for funnel in result.scalars():
        funnels.append({
            "id": str(funnel.id),
            "name": funnel.name,
            "steps": funnel.steps,
            "created_at": funnel.created_at.isoformat(),
        })

    return {"funnels": funnels}


# ============================================================
# Cohort Analysis Endpoints
# ============================================================

@router.get("/projects/{project_id}/cohorts/retention")
async def get_retention_cohorts(
    project_id: str,
    start_date: Optional[date] = None,
    periods: int = 8,
    period_days: int = 7,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get retention cohort analysis.

    Shows weekly signup cohorts and their retention over time.
    """
    project = await get_project_for_user(project_id, current_user["id"], db)
    service = AdvancedAnalyticsService(db)

    cohorts = await service.calculate_retention_cohort(
        project_id=project.id,
        start_date=start_date,
        periods=periods,
        period_days=period_days,
    )

    return {
        "cohorts": cohorts,
        "periods": periods,
        "period_days": period_days,
    }


@router.get("/projects/{project_id}/cohorts/channels")
async def get_channel_cohorts(
    project_id: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get cohort analysis by acquisition channel (UTM source).

    Shows performance comparison of different traffic sources.
    """
    project = await get_project_for_user(project_id, current_user["id"], db)
    service = AdvancedAnalyticsService(db)

    # Default to last 30 days
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)

    channels = await service.get_channel_cohorts(
        project_id=project.id,
        start_date=start_date,
        end_date=end_date,
    )

    return {
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
        },
        "channels": channels,
    }


# ============================================================
# Insights Endpoints
# ============================================================

@router.get("/projects/{project_id}/insights")
async def get_insights(
    project_id: str,
    days: int = 30,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get actionable insights from analytics data.

    Detects anomalies, trends, and provides recommendations.
    """
    project = await get_project_for_user(project_id, current_user["id"], db)
    service = AdvancedAnalyticsService(db)

    insights = await service.get_insights(
        project_id=project.id,
        days=days,
    )

    return insights


# ============================================================
# Real-time Analytics Endpoints
# ============================================================

@router.get("/projects/{project_id}/realtime/sessions")
async def get_active_sessions(
    project_id: str,
    minutes: int = 5,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get currently active sessions on the site."""
    project = await get_project_for_user(project_id, current_user["id"], db)
    service = AdvancedAnalyticsService(db)

    sessions = await service.get_active_sessions(
        project_id=project.id,
        minutes=minutes,
    )

    return {
        "active_sessions": len(sessions),
        "sessions": sessions,
        "minutes": minutes,
    }


@router.get("/projects/{project_id}/realtime/sessions/{session_id}")
async def get_session_recording(
    project_id: str,
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get detailed session recording (event timeline).

    Useful for understanding user journeys.
    """
    project = await get_project_for_user(project_id, current_user["id"], db)
    service = AdvancedAnalyticsService(db)

    # Verify session belongs to this project
    from app.models.db.analytics import AnalyticsSession

    session_check = await db.execute(
        select(AnalyticsSession).where(
            and_(
                AnalyticsSession.id == session_id,
                AnalyticsSession.project_id == project.id
            )
        )
    )
    if not session_check.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Session not found")

    recording = await service.get_session_recording(session_id)

    if not recording:
        raise HTTPException(status_code=404, detail="Session not found")

    return recording


# ============================================================
# Attribution & Heatmap Endpoints
# ============================================================

@router.get("/projects/{project_id}/attribution")
async def get_attribution(
    project_id: str,
    model: str = "first_touch",
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get attribution breakdown by traffic source."""
    project = await get_project_for_user(project_id, current_user["id"], db)
    service = AdvancedAnalyticsService(db)

    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)

    model = model if model in {"first_touch", "last_touch", "linear"} else "first_touch"

    channels = await service.get_attribution(
        project_id=project.id,
        start_date=start_date,
        end_date=end_date,
        model=model,
    )

    return {
        "model": model,
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
        },
        "channels": channels,
    }


@router.get("/projects/{project_id}/heatmap")
async def get_heatmap(
    project_id: str,
    page_url: str = "/",
    grid: int = 20,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get heatmap data for a page."""
    project = await get_project_for_user(project_id, current_user["id"], db)
    service = AdvancedAnalyticsService(db)

    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)

    grid = min(max(grid, 5), 50)

    return await service.get_heatmap(
        project_id=project.id,
        page_url=page_url,
        start_date=start_date,
        end_date=end_date,
        grid=grid,
    )
