"""Build run ORM model."""

from datetime import datetime
from uuid import uuid4 as uuid_generator

from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class BuildRun(Base):
    """Build runtime persistence model."""

    __tablename__ = "build_runs"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_generator)
    build_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), unique=True, index=True, default=uuid_generator)
    project_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    phase: Mapped[str] = mapped_column(String(20), default="planning")
    current_task_id: Mapped[str | None] = mapped_column(String(50))

    brief: Mapped[dict] = mapped_column(JSONB, default=dict)
    build_plan: Mapped[dict | None] = mapped_column(JSONB)
    product_doc: Mapped[dict | None] = mapped_column(JSONB)

    build_graph: Mapped[dict | None] = mapped_column(JSONB)
    patch_sets: Mapped[list | None] = mapped_column(JSONB)
    last_patch: Mapped[dict | None] = mapped_column(JSONB)

    validation_reports: Mapped[list | None] = mapped_column(JSONB)
    last_validation: Mapped[dict | None] = mapped_column(JSONB)

    check_reports: Mapped[list | None] = mapped_column(JSONB)
    last_checks: Mapped[dict | None] = mapped_column(JSONB)

    review_reports: Mapped[list | None] = mapped_column(JSONB)
    last_review: Mapped[dict | None] = mapped_column(JSONB)

    agent_usage: Mapped[list | None] = mapped_column(JSONB)
    last_agent_usage: Mapped[dict | None] = mapped_column(JSONB)

    history: Mapped[list | None] = mapped_column(JSONB)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
