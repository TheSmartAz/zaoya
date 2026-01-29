"""Snapshot ORM model."""

from datetime import datetime
from sqlalchemy import Column, String, TEXT, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import JSONB, UUID, ExcludeConstraint
from sqlalchemy.orm import Mapped, mapped_column
from uuid import uuid4 as uuid_generator

from app.db import Base


class Snapshot(Base):
    """Snapshot model for versioning."""

    __tablename__ = "snapshots"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_generator)
    project_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    version_number: Mapped[int] = mapped_column(nullable=False)
    summary: Mapped[str | None] = mapped_column(TEXT)
    design_system: Mapped[dict] = mapped_column(JSONB, default=dict)
    navigation: Mapped[dict] = mapped_column(JSONB, default=dict)
    interview_state: Mapped[dict] = mapped_column(JSONB, default=dict)
    is_draft: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    __table_args__ = (
        ExcludeConstraint(
            ("project_id", "="), ("is_draft", "="),
            where="is_draft = true",
            name="at_most_one_draft_per_project"
        ),
    )
