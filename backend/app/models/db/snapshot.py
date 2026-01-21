"""Snapshot ORM model."""

from datetime import datetime
from sqlalchemy import Column, String, TEXT, ForeignKey, Boolean, ExcludeConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from uuid import UUID

from app.db import Base


class Snapshot(Base):
    """Snapshot model for versioning."""

    __tablename__ = "snapshots"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    version_number: Mapped[int] = mapped_column(nullable=False)
    summary: Mapped[str | None] = mapped_column(TEXT)
    design_system: Mapped[dict] = mapped_column(JSONB, default=dict)
    navigation: Mapped[dict] = mapped_column(JSONB, default=dict)
    is_draft: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    __table_args__ = (
        ExcludeConstraint(
            ("project_id", "="), ("is_draft", "="),
            where="is_draft = true",
            name="at_most_one_draft_per_project"
        ),
    )
