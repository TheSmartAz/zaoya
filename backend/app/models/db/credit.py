"""Credit ORM models for image generation."""

from datetime import datetime, date
from sqlalchemy import Column, String, Integer, Numeric, Boolean, Date, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from uuid import uuid4 as uuid_generator

from app.db import Base


class UserCredits(Base):
    """User credit balance (one row per user)."""

    __tablename__ = "user_credits"

    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)

    # Credit balances
    image_credits: Mapped[int] = mapped_column(Integer, default=0)
    purchased_credits: Mapped[int] = mapped_column(Integer, default=0)

    # Monthly reset tracking
    credits_used_this_month: Mapped[int] = mapped_column(Integer, default=0)
    monthly_credits: Mapped[int] = mapped_column(Integer, default=5)

    last_monthly_reset: Mapped[date | None] = mapped_column(Date)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class CreditTransaction(Base):
    """Credit transaction log."""

    __tablename__ = "credit_transactions"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_generator)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    amount: Mapped[int] = mapped_column(Integer, nullable=False)  # Positive = add, Negative = use
    transaction_type: Mapped[str] = mapped_column(String(50), nullable=False)  # monthly_refresh, purchase, usage, bonus
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    meta_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index("idx_credit_transactions_user_date", "user_id", "created_at"),
        Index(
            "idx_credit_transactions_type",
            "user_id",
            "transaction_type",
            postgresql_where="transaction_type IN ('usage', 'purchase')",
        ),
    )


class CreditPackage(Base):
    """Credit packages for one-time purchases."""

    __tablename__ = "credit_packages"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_generator)
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # "10 Credits", "50 Credits"
    credits: Mapped[int] = mapped_column(Integer, nullable=False)
    price_usd: Mapped[float] = mapped_column(Numeric(precision=10, scale=2), nullable=False)

    stripe_price_id: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index("idx_credit_packages_active", "is_active", "display_order"),
    )
