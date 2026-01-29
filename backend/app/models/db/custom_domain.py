"""CustomDomain ORM model for custom domain support."""

from datetime import datetime, timedelta
from sqlalchemy import Column, String, DateTime, ForeignKey, CheckConstraint, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from uuid import uuid4 as uuid_generator

from app.db import Base


class CustomDomain(Base):
    """Custom domain configuration for a project."""

    __tablename__ = "custom_domains"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid_generator
    )
    project_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # Enforces 1:1 mapping
        index=True
    )

    # Domain info
    domain: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    is_apex: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Verification
    verification_token: Mapped[str] = mapped_column(String(64), nullable=False)
    verification_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verification_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # SSL status (informational, Caddy manages actual certs)
    ssl_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    ssl_provisioned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Operational fields
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failure_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="custom_domain")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Set verification expiry to 7 days from creation if not provided
        if not self.verification_expires_at:
            self.verification_expires_at = datetime.utcnow() + timedelta(days=7)

    __table_args__ = (
        CheckConstraint(
            "verification_status IN ('pending', 'verified', 'failed', 'active')",
            name="valid_verification_status"
        ),
        CheckConstraint(
            "ssl_status IN ('pending', 'provisioning', 'active', 'error')",
            name="valid_ssl_status"
        ),
    )

    @property
    def is_active(self) -> bool:
        """Check if domain is fully active (verified and SSL working)."""
        return self.verification_status == "active" and self.ssl_status == "active"

    @property
    def is_verified(self) -> bool:
        """Check if domain ownership is verified."""
        return self.verification_status in ("verified", "active")

    @property
    def is_pending(self) -> bool:
        """Check if domain is still pending verification."""
        return self.verification_status == "pending"

    @property
    def is_expired(self) -> bool:
        """Check if verification period has expired."""
        if self.verification_status != "pending":
            return False
        return datetime.utcnow() > self.verification_expires_at
