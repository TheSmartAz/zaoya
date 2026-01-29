"""Experiment ORM models for A/B testing."""

from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, Numeric, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid import uuid4 as uuid_generator

from app.db import Base


class Experiment(Base):
    """A/B testing experiment."""

    __tablename__ = "experiments"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_generator)
    project_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="draft")  # draft, running, paused, completed

    # Traffic configuration
    traffic_split: Mapped[dict] = mapped_column(JSONB, nullable=False)  # [50, 50] or [70, 30]

    # Conversion goal
    conversion_goal: Mapped[dict] = mapped_column(JSONB, nullable=False)

    start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    winner_variant_id: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True))
    winner_confidence: Mapped[float | None] = mapped_column(Numeric(precision=5, scale=2))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    created_by_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Indexes
    __table_args__ = (
        Index("idx_experiments_project_status", "project_id", "status"),
        Index("idx_experiments_status_dates", "status", "start_date"),
    )


class ExperimentVariant(Base):
    """A/B test variant (control or treatment)."""

    __tablename__ = "experiment_variants"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_generator)
    experiment_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # "Control", "Variant A"
    is_control: Mapped[bool] = mapped_column(Boolean, default=False)

    # Page content
    snapshot_id: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("snapshots.id", ondelete="SET NULL"))
    page_content: Mapped[dict | None] = mapped_column(JSONB)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index("uniq_control_per_experiment", "experiment_id",
               postgresql_where="is_control = true", unique=True),
        Index("idx_variants_experiment", "experiment_id"),
    )


class ExperimentResult(Base):
    """Aggregated statistics for experiment variants."""

    __tablename__ = "experiment_results"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_generator)
    experiment_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False)
    variant_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("experiment_variants.id", ondelete="CASCADE"), nullable=False)

    # Metrics
    visitors: Mapped[int] = mapped_column(Integer, default=0)
    conversions: Mapped[int] = mapped_column(Integer, default=0)
    conversion_rate: Mapped[float | None] = mapped_column(Numeric(precision=5, scale=2))

    # Statistical analysis
    confidence_level: Mapped[float | None] = mapped_column(Numeric(precision=5, scale=2))
    is_significant: Mapped[bool] = mapped_column(Boolean, default=False)
    p_value: Mapped[float | None] = mapped_column(Numeric(precision=10, scale=8))

    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    # Indexes
    __table_args__ = (
        UniqueConstraint("experiment_id", "variant_id", name="uq_experiment_result_experiment_variant"),
        Index("idx_results_experiment_variant", "experiment_id", "variant_id"),
    )


class ExperimentAssignment(Base):
    """Visitor-to-variant assignment mapping."""

    __tablename__ = "experiment_assignments"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_generator)
    experiment_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False)
    variant_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("experiment_variants.id", ondelete="CASCADE"), nullable=False)
    visitor_id: Mapped[str] = mapped_column(String(64), nullable=False)

    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index("idx_assignments_experiment_visitor", "experiment_id", "visitor_id"),
        UniqueConstraint("experiment_id", "visitor_id", name="uq_experiment_assignment_experiment_visitor"),
    )


class ExperimentConversion(Base):
    """Individual conversion events for experiments."""

    __tablename__ = "experiment_conversions"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_generator)
    experiment_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False)
    variant_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("experiment_variants.id", ondelete="CASCADE"), nullable=False)
    visitor_id: Mapped[str] = mapped_column(String(64), nullable=False)

    goal_type: Mapped[str] = mapped_column(String(50), nullable=False)
    goal_metadata: Mapped[dict | None] = mapped_column(JSONB)

    converted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index("idx_conversions_experiment_variant", "experiment_id", "variant_id", "converted_at"),
        UniqueConstraint("experiment_id", "variant_id", "visitor_id", name="uq_experiment_conversion_experiment_variant_visitor"),
    )


class ExperimentAuditLog(Base):
    """Audit log for experiment status changes."""

    __tablename__ = "experiment_audit_log"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_generator)
    experiment_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)  # created, started, paused, etc.

    old_status: Mapped[str | None] = mapped_column(String(20))
    new_status: Mapped[str | None] = mapped_column(String(20))
    audit_data: Mapped[dict | None] = mapped_column(JSONB)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    created_by_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=False)

    # Indexes
    __table_args__ = (
        Index("idx_audit_log_experiment", "experiment_id", "created_at"),
    )
