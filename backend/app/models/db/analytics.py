"""Analytics ORM models."""

from datetime import datetime, date
from sqlalchemy import Column, String, Integer, Boolean, TEXT, DateTime, Date, Numeric, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid import uuid4 as uuid_generator

from app.db import Base


class AnalyticsEvent(Base):
    """Raw analytics event with time-series optimization."""

    __tablename__ = "analytics_events"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_generator)
    project_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    visitor_id: Mapped[str] = mapped_column(String(64), nullable=False)
    session_id: Mapped[str | None] = mapped_column(String(64))
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    event_name: Mapped[str | None] = mapped_column(String(100))
    properties: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Context metadata
    referrer: Mapped[str | None] = mapped_column(TEXT)
    utm_source: Mapped[str | None] = mapped_column(String(100))
    utm_medium: Mapped[str | None] = mapped_column(String(100))
    utm_campaign: Mapped[str | None] = mapped_column(String(100))
    device_type: Mapped[str] = mapped_column(String(20), default="desktop")
    browser: Mapped[str | None] = mapped_column(String(50))
    country: Mapped[str | None] = mapped_column(String(2))
    city: Mapped[str | None] = mapped_column(String(100))

    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index("idx_events_project_timestamp", "project_id", "timestamp"),
        Index("idx_events_timestamp_brin", "timestamp", postgresql_using="brin"),
        Index("idx_events_properties", "properties", postgresql_using="gin"),
        Index("idx_events_session", "session_id", "timestamp"),
        Index("idx_events_project_type", "project_id", "event_type", "timestamp"),
    )


class AnalyticsSession(Base):
    """Aggregated visitor session."""

    __tablename__ = "analytics_sessions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    visitor_id: Mapped[str] = mapped_column(String(64), nullable=False)
    project_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    page_views: Mapped[int] = mapped_column(Integer, default=0)
    events: Mapped[int] = mapped_column(Integer, default=0)

    entry_page: Mapped[str | None] = mapped_column(String(100))
    exit_page: Mapped[str | None] = mapped_column(String(100))
    duration_seconds: Mapped[int | None] = mapped_column(Integer)

    device_type: Mapped[str] = mapped_column(String(20), default="desktop")
    browser: Mapped[str | None] = mapped_column(String(50))
    country: Mapped[str | None] = mapped_column(String(2))

    # Indexes
    __table_args__ = (
        Index("idx_sessions_visitor_project", "visitor_id", "project_id", "started_at"),
        Index("idx_sessions_project_started", "project_id", "started_at"),
    )


class AnalyticsDaily(Base):
    """Pre-aggregated daily statistics."""

    __tablename__ = "analytics_daily"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_generator)
    project_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)

    # Daily metrics
    views: Mapped[int] = mapped_column(Integer, default=0)
    unique_visitors: Mapped[int] = mapped_column(Integer, default=0)
    sessions: Mapped[int] = mapped_column(Integer, default=0)
    cta_clicks: Mapped[int] = mapped_column(Integer, default=0)
    form_submissions: Mapped[int] = mapped_column(Integer, default=0)

    # Engagement metrics
    avg_session_duration: Mapped[int | None] = mapped_column(Integer)
    bounce_rate: Mapped[float | None] = mapped_column(Numeric(precision=5, scale=2))

    # Breakdowns
    device_counts: Mapped[dict | None] = mapped_column(JSONB)
    top_pages: Mapped[dict | None] = mapped_column(JSONB)
    traffic_sources: Mapped[dict] = mapped_column(JSONB, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    # Indexes
    __table_args__ = (
        UniqueConstraint("project_id", "date", name="uq_analytics_daily_project_date"),
        Index("idx_daily_project_date", "project_id", "date"),
        Index(
            "idx_daily_recent",
            "project_id",
            "date",
            postgresql_where="date >= CURRENT_DATE - INTERVAL '90 days'",
        ),
    )


class AnalyticsFunnel(Base):
    """User-defined conversion funnel."""

    __tablename__ = "analytics_funnels"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_generator)
    project_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    steps: Mapped[dict] = mapped_column(JSONB, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    created_by_id: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))

    # Indexes
    __table_args__ = (
        Index("idx_funnels_project", "project_id"),
    )


class AnalyticsCohort(Base):
    """Cohort analysis data."""

    __tablename__ = "analytics_cohorts"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_generator)
    project_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    cohort_type: Mapped[str] = mapped_column(String(50), nullable=False)
    cohort_date: Mapped[date] = mapped_column(Date, nullable=False)
    cohort_label: Mapped[str] = mapped_column(String(100), nullable=False)

    initial_size: Mapped[int] = mapped_column(Integer, nullable=False)
    period_data: Mapped[dict] = mapped_column(JSONB, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index("idx_cohorts_project_date", "project_id", "cohort_date"),
    )
