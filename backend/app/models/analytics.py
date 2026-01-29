"""Analytics models and storage for page performance tracking."""

from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime, date, timedelta


class TrackEventRequest(BaseModel):
    """Request model for tracking events."""
    type: str
    data: Dict[str, Any] = {}


class PageAnalytics(BaseModel):
    """Daily aggregated analytics for a page."""
    id: str
    project_id: str
    date: date

    # Daily counts
    views: int = 0
    unique_visitors: int = 0
    cta_clicks: int = 0
    form_submissions: int = 0

    # Event breakdown (optional detail)
    events: Dict[str, Any] = {}

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "project_id": self.project_id,
            "date": self.date.isoformat(),
            "views": self.views,
            "unique_visitors": self.unique_visitors,
            "cta_clicks": self.cta_clicks,
            "form_submissions": self.form_submissions,
            "events": self.events,
        }


# In-memory storage (replace with database in production)
_analytics_storage: Dict[str, PageAnalytics] = {}


def generate_analytics_id() -> str:
    """Generate a unique analytics ID."""
    import time
    import secrets
    return f"analytics_{int(time.time())}_{secrets.token_hex(4)}"


def get_or_create_analytics(project_id: str, date: date) -> PageAnalytics:
    """Get or create analytics record for a project on a specific date."""
    # Generate a consistent key
    key = f"{project_id}:{date.isoformat()}"

    if key not in _analytics_storage:
        analytics = PageAnalytics(
            id=generate_analytics_id(),
            project_id=project_id,
            date=date,
            views=0,
            unique_visitors=0,
            cta_clicks=0,
            form_submissions=0,
            events={},
        )
        _analytics_storage[key] = analytics

    return _analytics_storage[key]


def save_analytics(analytics: PageAnalytics) -> None:
    """Save analytics record."""
    key = f"{analytics.project_id}:{analytics.date.isoformat()}"
    _analytics_storage[key] = analytics


def get_analytics_range(
    project_id: str,
    start_date: date,
    end_date: date,
) -> list[PageAnalytics]:
    """Get analytics for a date range."""
    results = []
    current = start_date

    while current <= end_date:
        key = f"{project_id}:{current.isoformat()}"
        if key in _analytics_storage:
            results.append(_analytics_storage[key])
        current = current + timedelta(days=1)

    return results


def hash_visitor(ip: str, date_salt: Optional[date] = None) -> str:
    """
    Hash IP for privacy-friendly unique visitor counting.

    Uses a daily salt so we can't track the same visitor across days.
    """
    import hashlib

    salt = (date_salt or date.today()).isoformat()
    return hashlib.sha256(f"{ip}{salt}".encode()).hexdigest()[:16]
