"""Project ORM model."""

from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import Column, String, Boolean, TEXT, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid import uuid4 as uuid_generator

from app.db import Base

if TYPE_CHECKING:
    from app.models.db.project_page import ProjectPage
    from app.models.db.product_doc import ProductDoc
    from app.models.db.custom_domain import CustomDomain


class Project(Base):
    """Project model."""

    __tablename__ = "projects"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_generator)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    owner_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    public_id: Mapped[str | None] = mapped_column(String(8), unique=True)
    slug: Mapped[str | None] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    template_id: Mapped[str | None] = mapped_column(String(50))
    template_inputs: Mapped[dict] = mapped_column(JSONB, default=dict)
    render_templates: Mapped[dict] = mapped_column(
        JSONB,
        default=lambda: {
            "preview": "preview_template_v1",
            "publish": "publish_template_v1",
        },
    )
    status: Mapped[str] = mapped_column(String(20), default="draft")
    current_draft_id: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("snapshots.id"))
    published_snapshot_id: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("snapshots.id"))
    active_branch_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("branches.id", ondelete="SET NULL"),
        nullable=True,
    )
    notification_email: Mapped[str | None] = mapped_column(String(255))
    notification_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    published_at: Mapped[datetime | None] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    pages: Mapped[list["ProjectPage"]] = relationship(
        back_populates="project", order_by="ProjectPage.sort_order"
    )
    product_doc: Mapped["ProductDoc | None"] = relationship(
        back_populates="project",
        uselist=False,
        cascade="all, delete-orphan",
    )
    custom_domain: Mapped["CustomDomain | None"] = relationship(
        back_populates="project",
        uselist=False,
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint("slug ~ '^[a-z0-9]([a-z0-9-]*[a-z0-9])?$'", name="slug_format"),
    )
