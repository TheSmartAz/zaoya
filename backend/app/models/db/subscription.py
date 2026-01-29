"""Subscription ORM models for billing."""

from datetime import datetime
from sqlalchemy import Column, String, Integer, Numeric, Boolean, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column
from uuid import uuid4 as uuid_generator

from app.db import Base


class SubscriptionPlan(Base):
    """Subscription plan definitions."""

    __tablename__ = "subscription_plans"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)  # 'free', 'pro', 'team'
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))

    # Pricing
    price_monthly_usd: Mapped[float] = mapped_column(Numeric(precision=10, scale=2), nullable=False)
    price_yearly_usd: Mapped[float] = mapped_column(Numeric(precision=10, scale=2), nullable=False)

    # Stripe integration
    stripe_price_id_monthly: Mapped[str | None] = mapped_column(String(255))
    stripe_price_id_yearly: Mapped[str | None] = mapped_column(String(255))

    # Feature limits
    limits: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Features list for display
    features: Mapped[list[str] | None] = mapped_column(ARRAY(String(200)))

    display_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index("idx_plans_active_display", "is_active", "display_order"),
    )


class UserSubscription(Base):
    """User subscription records."""

    __tablename__ = "user_subscriptions"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_generator)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    plan_id: Mapped[str] = mapped_column(String(50), ForeignKey("subscription_plans.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active")  # active, canceled, past_due

    # Stripe integration
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255))
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(255))

    # Billing cycle
    billing_interval: Mapped[str] = mapped_column(String(10), nullable=False)  # month, year

    current_period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Trial
    trial_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    trial_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Cancellation
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, default=False)
    canceled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    # Indexes
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_user_subscriptions_user"),
        Index("idx_subscriptions_user", "user_id"),
        Index("idx_subscriptions_status", "status", "current_period_end"),
        Index(
            "idx_subscriptions_stripe",
            "stripe_subscription_id",
            postgresql_where="stripe_subscription_id IS NOT NULL",
        ),
    )


class SubscriptionEvent(Base):
    """Webhook event log."""

    __tablename__ = "subscription_events"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid_generator)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    subscription_id: Mapped[str | None] = mapped_column(String(255))

    event_type: Mapped[str] = mapped_column(String(100), nullable=False)

    stripe_event_id: Mapped[str | None] = mapped_column(String(255))
    event_data: Mapped[dict] = mapped_column(JSONB, nullable=False)

    processed: Mapped[bool] = mapped_column(Boolean, default=False)
    processing_error: Mapped[str | None] = mapped_column(String(255))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    # Indexes
    __table_args__ = (
        UniqueConstraint("stripe_event_id", name="uq_subscription_events_stripe_event"),
        Index("idx_subscription_events_user", "user_id", "created_at"),
        Index("idx_subscription_events_unprocessed", "processed", "created_at",
               postgresql_where="processed = false"),
    )
