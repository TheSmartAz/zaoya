"""ProductDoc ORM model."""

from datetime import datetime
from uuid import uuid4 as uuid_generator

from sqlalchemy import DateTime, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class ProductDoc(Base):
    """Structured ProductDoc stored per project."""

    __tablename__ = "product_docs"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_generator)
    project_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    overview: Mapped[str] = mapped_column(Text, nullable=False)
    target_users: Mapped[list | None] = mapped_column(JSONB, default=list)
    content_structure: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    design_requirements: Mapped[dict | None] = mapped_column(JSONB)
    page_plan: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    technical_constraints: Mapped[list | None] = mapped_column(JSONB)
    interview_answers: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)

    generation_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_generated_at: Mapped[datetime | None] = mapped_column(DateTime)

    project = relationship("Project", back_populates="product_doc")

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "project_id": str(self.project_id),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "overview": self.overview,
            "target_users": self.target_users or [],
            "content_structure": self.content_structure or {"sections": []},
            "design_requirements": self.design_requirements,
            "page_plan": self.page_plan or {"pages": []},
            "technical_constraints": self.technical_constraints,
            "interview_answers": self.interview_answers or [],
            "generation_count": self.generation_count,
            "last_generated_at": self.last_generated_at.isoformat()
            if self.last_generated_at
            else None,
        }
