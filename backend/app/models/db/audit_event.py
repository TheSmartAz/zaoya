"""AuditEvent ORM model for activity logging."""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from uuid import uuid4 as uuid_generator
from typing import Any

from app.db import Base


class AuditEvent(Base):
    """Audit log entry for tracking user and system actions."""

    __tablename__ = "audit_events"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid_generator
    )
    user_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    team_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True  # Future: for team support
    )

    # Action details
    action: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)
    resource_id: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    # Additional context
    meta_data: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSONB, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)  # IPv6 compatible
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    # Common action constants for custom domains
    class Actions:
        DOMAIN_ADDED = "domain.added"
        DOMAIN_VERIFIED = "domain.verified"
        DOMAIN_REMOVED = "domain.removed"
        DOMAIN_VERIFICATION_FAILED = "domain.verification_failed"

    # Common resource types
    class ResourceTypes:
        CUSTOM_DOMAIN = "custom_domain"
        PROJECT = "project"
        USER = "user"
