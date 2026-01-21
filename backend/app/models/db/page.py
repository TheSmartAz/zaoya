"""Page ORM model."""

from datetime import datetime
from sqlalchemy import Column, String, TEXT, Boolean, Integer, ForeignKey, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from uuid import UUID

from app.db import Base


class Page(Base):
    """Page model for multi-page projects."""

    __tablename__ = "pages"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    snapshot_id: Mapped[UUID] = mapped_column(ForeignKey("snapshots.id", ondelete="CASCADE"), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    html: Mapped[str] = mapped_column(TEXT, nullable=False)
    js: Mapped[str | None] = mapped_column(TEXT)
    metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
    is_home: Mapped[bool] = mapped_column(Boolean, default=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("slug ~ '^[a-z0-9]([a-z0-9-]*[a-z0-9])?$'", name="slug_format"),
        Index("uniq_home_per_snapshot", "snapshot_id", unique=True,
              postgresql_where="is_home = true"),
    )
