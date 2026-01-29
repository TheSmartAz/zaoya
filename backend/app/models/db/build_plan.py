"""Build plan ORM model for multi-page builds."""

from __future__ import annotations

import enum
from datetime import datetime
from uuid import uuid4 as uuid_generator

from sqlalchemy import DateTime, Enum, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class BuildStatus(enum.Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BuildPlan(Base):
    """BuildPlan snapshot persisted for build progress tracking."""

    __tablename__ = "build_plans"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_generator)
    project_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    pages: Mapped[list] = mapped_column(JSONB, default=list)
    tasks: Mapped[list] = mapped_column(JSONB, default=list)

    total_tasks: Mapped[int] = mapped_column(Integer, default=0)
    completed_tasks: Mapped[int] = mapped_column(Integer, default=0)
    failed_tasks: Mapped[int] = mapped_column(Integer, default=0)

    estimated_duration_ms: Mapped[int | None] = mapped_column(Integer)
    actual_duration_ms: Mapped[int | None] = mapped_column(Integer)
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)

    status: Mapped[BuildStatus] = mapped_column(Enum(BuildStatus), default=BuildStatus.DRAFT)

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "project_id": str(self.project_id),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "pages": self.pages or [],
            "tasks": self.tasks or [],
            "total_tasks": self.total_tasks,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "estimated_duration_ms": self.estimated_duration_ms,
            "actual_duration_ms": self.actual_duration_ms,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "status": self.status.value if self.status else None,
        }
