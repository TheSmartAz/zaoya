"""Asset ORM models for image library."""

from datetime import datetime
from sqlalchemy import Column, String, Integer, TEXT, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column
from uuid import uuid4 as uuid_generator

from app.db import Base


class Asset(Base):
    """Image or other asset file."""

    __tablename__ = "assets"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_generator)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    project_id: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL"))

    asset_type: Mapped[str] = mapped_column(String(20), nullable=False)  # generated, uploaded

    url: Mapped[str] = mapped_column(TEXT, nullable=False)
    thumbnail_url: Mapped[str | None] = mapped_column(TEXT)
    original_filename: Mapped[str | None] = mapped_column(String(255))

    # For generated images
    prompt: Mapped[str | None] = mapped_column(TEXT)
    generation_provider: Mapped[str | None] = mapped_column(String(50))
    generation_metadata: Mapped[dict | None] = mapped_column(JSONB)

    # File metadata
    file_size_bytes: Mapped[int | None] = mapped_column(Integer)
    mime_type: Mapped[str | None] = mapped_column(String(100))
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)

    # Organization
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(String(50)))
    alt_text: Mapped[str | None] = mapped_column(TEXT)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index("idx_assets_user_created", "user_id", "created_at"),
        Index("idx_assets_project", "project_id", "created_at"),
        Index("idx_assets_tags", "tags", postgresql_using="gin"),
        Index("idx_assets_user_type", "user_id", "asset_type"),
        Index("idx_assets_metadata", "generation_metadata", postgresql_using="gin"),
    )
