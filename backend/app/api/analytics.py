"""Analytics API endpoints for tracking and dashboard."""

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime, timedelta

from ..models.analytics import (
    TrackEventRequest,
    get_or_create_analytics,
    save_analytics,
    get_analytics_range,
    hash_visitor,
)
from ..models.user import get_current_user
from .projects import get_project

router = APIRouter()


@router.post("/track/{public_id}")
async def track_event(
    public_id: str,
    request: Request,
    event: TrackEventRequest,
):
    """
    Track an analytics event for a published page.

    Silently fails for invalid pages to prevent information leakage.
    Uses fire-and-forget approach - doesn't block page loads.
    """
    # Import here to avoid circular imports
    from .projects import _published_pages

    # Verify page exists (silently fail if not)
    page_data = _published_pages.get(public_id)
    if not page_data:
        return {"success": False}

    project_id = page_data.get("projectId")
    if not project_id:
        return {"success": False}

    today = date.today()

    # Get or create today's analytics record
    analytics = get_or_create_analytics(project_id, today)

    # Update based on event type
    if event.type == "page_view":
        analytics.views += 1

        # Track unique visitors (privacy-friendly hashed IP)
        client_ip = request.client.host
        visitor_hash = hash_visitor(client_ip, today)

        visitors = analytics.events.get("visitors", [])
        if visitor_hash not in visitors:
            analytics.unique_visitors += 1
            visitors.append(visitor_hash)
            analytics.events["visitors"] = visitors

    elif event.type == "cta_click":
        analytics.cta_clicks += 1

        # Track specific button/link
        event_name = event.data.get("element", "unknown")
        click_key = f"click:{event_name}"
        analytics.events[click_key] = analytics.events.get(click_key, 0) + 1

    elif event.type == "form_submit":
        analytics.form_submissions += 1

        form_id = event.data.get("form_id", "default")
        submit_key = f"submit:{form_id}"
        analytics.events[submit_key] = analytics.events.get(submit_key, 0) + 1

    # Save analytics
    save_analytics(analytics)

    return {"success": True}


@router.get("/projects/{project_id}/analytics")
async def get_analytics_dashboard(
    project_id: str,
    days: int = 30,
    current_user: dict = Depends(get_current_user),
):
    """
    Get analytics dashboard data for a project.

    Returns aggregated totals, trends, and daily breakdown.
    """
    # Verify project ownership
    project = get_project(project_id, current_user["id"])
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Validate days parameter
    days = min(90, max(7, days))

    end_date = date.today()
    start_date = end_date - timedelta(days=days - 1)

    # Get analytics data
    daily_data = get_analytics_range(project_id, start_date, end_date)

    # Calculate totals
    totals = {
        "views": sum(d.views for d in daily_data),
        "unique_visitors": sum(d.unique_visitors for d in daily_data),
        "cta_clicks": sum(d.cta_clicks for d in daily_data),
        "form_submissions": sum(d.form_submissions for d in daily_data),
    }

    # Calculate trends (compare to previous period)
    prev_start = start_date - timedelta(days=days)
    prev_end = start_date - timedelta(days=1)
    prev_data = get_analytics_range(project_id, prev_start, prev_end)

    prev_totals = {
        "views": sum(d.views for d in prev_data),
        "unique_visitors": sum(d.unique_visitors for d in prev_data),
    }

    trends = {
        "views": calculate_trend(totals["views"], prev_totals["views"]),
        "visitors": calculate_trend(totals["unique_visitors"], prev_totals["unique_visitors"]),
    }

    # Build daily breakdown
    daily = []
    for d in daily_data:
        daily.append({
            "date": d.date.isoformat(),
            "views": d.views,
            "visitors": d.unique_visitors,
            "clicks": d.cta_clicks,
            "submissions": d.form_submissions,
        })

    # Fill in missing dates with zeros
    filled_daily = fill_missing_dates(daily, start_date, end_date)

    return {
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "days": days,
        },
        "totals": totals,
        "trends": trends,
        "daily": filled_daily,
    }


def calculate_trend(current: int, previous: int) -> float:
    """
    Calculate percentage trend between two periods.

    Returns:
        Percentage change (positive = growth, negative = decline)
    """
    if previous == 0:
        return 100.0 if current > 0 else 0.0
    return round((current - previous) / previous * 100, 1)


def fill_missing_dates(daily: list, start_date: date, end_date: date) -> list:
    """Fill missing dates with zero values."""
    date_map = {d["date"]: d for d in daily}

    filled = []
    current = start_date

    while current <= end_date:
        date_str = current.isoformat()
        if date_str in date_map:
            filled.append(date_map[date_str])
        else:
            filled.append({
                "date": date_str,
                "views": 0,
                "visitors": 0,
                "clicks": 0,
                "submissions": 0,
            })
        current = current + timedelta(days=1)

    return filled
