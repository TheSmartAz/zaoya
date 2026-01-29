"""Subscription service for premium tier management.

This service handles:
- Subscription plan management
- User subscription lifecycle
- Feature gating based on plan
- Billing integration (mocked for now)
- Usage limits enforcement
"""

from datetime import datetime, date, timedelta
from typing import Optional, Literal
from uuid import UUID, uuid4

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db.subscription import (
    SubscriptionPlan,
    UserSubscription,
    SubscriptionEvent,
)
from app.models.db import Project, Snapshot, Page, Version
from app.models.db.analytics import AnalyticsEvent


# Plan feature limits
PLAN_LIMITS = {
    "free": {
        "projects": 1,
        "pages_per_project": 3,
        "snapshots": 10,
        "versions": 5,
        "ai_generations_monthly": 5,
        "analytics_days": 7,
        "funnels": 0,
        "experiments": 0,
        "custom_domain": False,
        "api_access": False,
        "team_collaborators": 0,
        "priority_support": False,
    },
    "pro": {
        "projects": 10,
        "pages_per_project": 10,
        "snapshots": 100,
        "versions": 50,
        "ai_generations_monthly": 100,
        "analytics_days": 90,
        "funnels": 5,
        "experiments": 3,
        "custom_domain": True,
        "api_access": True,
        "team_collaborators": 3,
        "priority_support": False,
    },
    "team": {
        "projects": -1,  # unlimited
        "pages_per_project": -1,
        "snapshots": -1,
        "versions": -1,
        "ai_generations_monthly": 500,
        "analytics_days": 365,
        "funnels": -1,
        "experiments": -1,
        "custom_domain": True,
        "api_access": True,
        "team_collaborators": -1,
        "priority_support": True,
    },
}


class SubscriptionService:
    """Service for managing subscriptions and feature gates."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ============================================================
    # Plan Management
    # ============================================================

    async def get_all_plans(self) -> list[SubscriptionPlan]:
        """Get all available subscription plans."""
        result = await self.db.execute(
            select(SubscriptionPlan)
            .where(SubscriptionPlan.is_active == True)
            .order_by(SubscriptionPlan.display_order)
        )
        return list(result.scalars())

    async def get_plan(self, plan_id: str) -> SubscriptionPlan | None:
        """Get a specific plan by ID."""
        result = await self.db.execute(
            select(SubscriptionPlan).where(
                and_(
                    SubscriptionPlan.id == plan_id,
                    SubscriptionPlan.is_active == True
                )
            )
        )
        return result.scalar_one_or_none()

    def get_plan_limits(self, plan_id: str) -> dict:
        """Get feature limits for a plan."""
        return PLAN_LIMITS.get(plan_id, PLAN_LIMITS["free"])

    async def seed_default_plans(self) -> None:
        """Seed default subscription plans if they don't exist."""
        existing = await self.db.execute(
            select(func.count()).select_from(SubscriptionPlan)
        )
        count = existing.scalar() or 0

        if count > 0:
            return  # Already seeded

        plans = [
            SubscriptionPlan(
                id="free",
                name="Free",
                description="Perfect for trying out Zaoya",
                price_monthly_usd=0,
                price_yearly_usd=0,
                limits=PLAN_LIMITS["free"],
                features=[
                    "1 project",
                    "3 pages per project",
                    "10 snapshots",
                    "5 versions",
                    "5 AI generations/month",
                    "7-day analytics",
                ],
                display_order=0,
                created_at=datetime.utcnow(),
            ),
            SubscriptionPlan(
                id="pro",
                name="Pro",
                description="For creators who need more",
                price_monthly_usd=9.99,
                price_yearly_usd=99.99,
                limits=PLAN_LIMITS["pro"],
                features=[
                    "10 projects",
                    "10 pages per project",
                    "100 snapshots",
                    "50 versions",
                    "100 AI generations/month",
                    "90-day analytics",
                    "5 funnels",
                    "3 experiments",
                    "Custom domains",
                    "API access",
                ],
                display_order=1,
                created_at=datetime.utcnow(),
            ),
            SubscriptionPlan(
                id="team",
                name="Team",
                description="For teams and businesses",
                price_monthly_usd=29.99,
                price_yearly_usd=299.99,
                limits=PLAN_LIMITS["team"],
                features=[
                    "Unlimited projects",
                    "Unlimited pages",
                    "Unlimited snapshots",
                    "Unlimited versions",
                    "500 AI generations/month",
                    "1-year analytics",
                    "Unlimited funnels",
                    "Unlimited experiments",
                    "Custom domains",
                    "API access",
                    "Priority support",
                ],
                display_order=2,
                created_at=datetime.utcnow(),
            ),
        ]

        for plan in plans:
            self.db.add(plan)

        await self.db.commit()

    # ============================================================
    # User Subscription Management
    # ============================================================

    async def get_user_subscription(
        self,
        user_id: UUID,
    ) -> tuple[UserSubscription | None, dict]:
        """
        Get user's active subscription.

        Returns:
            (subscription object, limits dict)
        """
        result = await self.db.execute(
            select(UserSubscription).where(
                and_(
                    UserSubscription.user_id == user_id,
                    UserSubscription.status == "active",
                )
            )
            .order_by(UserSubscription.created_at.desc())
        )
        subscription = result.scalar_one_or_none()

        # Get plan limits
        if subscription:
            plan_id = subscription.plan_id
            limits = self.get_plan_limits(plan_id)
        else:
            # Free tier defaults
            limits = self.get_plan_limits("free")

        return subscription, limits

    async def create_free_subscription(
        self,
        user_id: UUID,
    ) -> UserSubscription:
        """Create a free tier subscription for a new user."""
        # Check if user already has a subscription
        existing = await self.db.execute(
            select(UserSubscription).where(UserSubscription.user_id == user_id)
        )
        if existing.scalar_one_or_none():
            return existing.scalar_one()

        subscription = UserSubscription(
            id=uuid4(),
            user_id=user_id,
            plan_id="free",
            status="active",
            billing_interval="month",
            created_at=datetime.utcnow(),
        )
        self.db.add(subscription)
        await self.db.commit()
        await self.db.refresh(subscription)

        return subscription

    async def upgrade_subscription(
        self,
        user_id: UUID,
        new_plan_id: str,
        billing_interval: Literal["month", "year"] = "month",
    ) -> UserSubscription:
        """Upgrade or change a user's subscription plan."""
        # Get current subscription
        result = await self.db.execute(
            select(UserSubscription).where(UserSubscription.user_id == user_id)
        )
        subscription = result.scalar_one_or_none()

        plan = await self.get_plan(new_plan_id)
        if not plan:
            raise ValueError(f"Plan {new_plan_id} not found")

        if subscription:
            # Update existing
            old_plan_id = subscription.plan_id
            subscription.plan_id = new_plan_id
            subscription.billing_interval = billing_interval
            subscription.status = "active"
            subscription.updated_at = datetime.utcnow()

            # Log change
            await self._log_event(
                subscription_id=subscription.id,
                event_type="plan_changed",
                event_data={
                    "from_plan": old_plan_id,
                    "to_plan": new_plan_id,
                    "interval": billing_interval,
                },
            )
        else:
            # Create new subscription
            subscription = UserSubscription(
                id=uuid4(),
                user_id=user_id,
                plan_id=new_plan_id,
                status="active",
                billing_interval=billing_interval,
                created_at=datetime.utcnow(),
            )
            self.db.add(subscription)

            # Log creation
            await self._log_event(
                subscription_id=subscription.id,
                event_type="subscription_created",
                event_data={
                    "plan": new_plan_id,
                    "interval": billing_interval,
                },
            )

        await self.db.commit()
        await self.db.refresh(subscription)

        return subscription

    async def cancel_subscription(
        self,
        user_id: UUID,
        cancel_at_period_end: bool = True,
    ) -> UserSubscription:
        """Cancel a user's subscription."""
        result = await self.db.execute(
            select(UserSubscription).where(
                and_(
                    UserSubscription.user_id == user_id,
                    UserSubscription.status == "active",
                )
            )
        )
        subscription = result.scalar_one_or_none()

        if not subscription:
            raise ValueError("No active subscription found")

        if cancel_at_period_end:
            subscription.cancel_at_period_end = True
        else:
            subscription.status = "canceled"
            subscription.canceled_at = datetime.utcnow()

        subscription.updated_at = datetime.utcnow()

        # Log cancellation
        await self._log_event(
            subscription_id=subscription.id,
            event_type="subscription_canceled",
            event_data={
                "cancel_at_period_end": cancel_at_period_end,
            },
        )

        await self.db.commit()
        await self.db.refresh(subscription)

        return subscription

    # ============================================================
    # Feature Gating
    # ============================================================

    async def check_feature_available(
        self,
        user_id: UUID,
        feature: str,
        current_usage: int = 0,
    ) -> tuple[bool, dict | None]:
        """
        Check if a user has access to a feature and if they've hit limits.

        Returns:
            (available, limit_info dict or None)

        Raises:
            FeatureLimitError if limit exceeded
        """
        subscription, limits = await self.get_user_subscription(user_id)

        # Check if feature exists in plan limits
        limit_value = limits.get(feature)
        if limit_value is None:
            # Feature not in plan (disabled)
            return (False, {"reason": "feature_not_available"})

        # -1 means unlimited
        if limit_value == -1:
            return (True, None)

        # Check if user has hit the limit
        if current_usage >= limit_value:
            # Get plan upgrade info
            result = await self.db.execute(
                select(SubscriptionPlan)
                .where(SubscriptionPlan.is_active == True)
                .order_by(SubscriptionPlan.display_order)
            )
            available_plans = result.scalars()

            upgrade_options = []
            for plan in available_plans:
                plan_limits = self.get_plan_limits(plan.id)
                if plan_limits.get(feature, 0) > limit_value:
                    upgrade_options.append({
                        "id": plan.id,
                        "name": plan.name,
                        "limit": plan_limits[feature],
                        "price_monthly": float(plan.price_monthly_usd),
                    })

            return (False, {
                "reason": "limit_exceeded",
                "current": current_usage,
                "limit": limit_value,
                "upgrade_options": upgrade_options,
            })

        return (True, None)

    async def enforce_limit(
        self,
        user_id: UUID,
        feature: str,
    ) -> bool:
        """
        Check if a feature action is allowed. Raises if not.

        Returns True if allowed.

        Raises:
            ValueError with error details
        """
        # Get current usage for this feature
        current_usage = await self._get_feature_usage(user_id, feature)

        available, limit_info = await self.check_feature_available(
            user_id, feature, current_usage
        )

        if not available:
            if limit_info and limit_info.get("reason") == "limit_exceeded":
                raise ValueError(
                    f"Feature limit exceeded: {feature} ({current_usage}/{limit_info['limit']}). "
                    f"Upgrade to access more."
                )
            raise ValueError(f"Feature not available: {feature}")

        return True

    async def _get_feature_usage(self, user_id: UUID, feature: str) -> int:
        """Get current usage count for a feature."""
        subscription, _ = await self.get_user_subscription(user_id)

        if feature == "projects":
            result = await self.db.execute(
                select(func.count()).select_from(Project).where(
                    Project.user_id == user_id
                )
            )
            return result.scalar() or 0

        if feature == "snapshots":
            result = await self.db.execute(
                select(func.count())
                .select_from(Snapshot)
                .where(
                    and_(
                        Snapshot.project_id.in_(
                            select(Project.id).where(Project.user_id == user_id)
                        )
                    )
                )
            )
            return result.scalar() or 0

        if feature == "versions":
            result = await self.db.execute(
                select(func.count())
                .select_from(Version)
                .where(
                    and_(
                        Version.project_id.in_(
                            select(Project.id).where(Project.user_id == user_id)
                        ),
                        Version.validation_status != "failed",
                    )
                )
            )
            return result.scalar() or 0

        if feature == "ai_generations_monthly":
            # Count image generations this month
            start_of_month = date.today().replace(day=1)
            start_dt = datetime.combine(start_of_month, datetime.min.time())

            from app.models.db.asset import Asset

            result = await self.db.execute(
                select(func.count())
                .select_from(Asset)
                .where(
                    and_(
                        Asset.user_id == user_id,
                        Asset.asset_type == "generated",
                        Asset.created_at >= start_dt,
                    )
                )
            )
            return result.scalar() or 0

        if feature == "experiments":
            # Count active experiments
            from app.models.db.experiment import Experiment

            result = await self.db.execute(
                select(func.count())
                .select_from(Experiment)
                .where(
                    and_(
                        Experiment.project_id.in_(
                            select(Project.id).where(Project.user_id == user_id)
                        ),
                        Experiment.status.in_(["draft", "running", "paused"]),
                    )
                )
            )
            return result.scalar() or 0

        if feature == "funnels":
            # Count funnels
            from app.models.db.analytics import AnalyticsFunnel

            result = await self.db.execute(
                select(func.count())
                .select_from(AnalyticsFunnel)
                .where(
                    AnalyticsFunnel.project_id.in_(
                        select(Project.id).where(Project.user_id == user_id)
                    )
                )
            )
            return result.scalar() or 0

        # Default to 0 for untracked features
        return 0

    # ============================================================
    # Billing Integration (Mock)
    # ============================================================

    async def handle_webhook_event(
        self,
        event_type: str,
        event_data: dict,
    ) -> SubscriptionEvent | None:
        """
        Handle Stripe webhook events (mocked for now).

        Event types:
        - checkout.completed: New subscription
        - invoice.paid: Subscription renewed
        - customer.subscription.updated: Subscription changed
        - customer.subscription.deleted: Subscription canceled
        """
        # In production, verify webhook signature
        # For now, just process the event

        subscription_id = event_data.get("subscription_id")
        if not subscription_id:
            return None

        # Get subscription by Stripe ID
        result = await self.db.execute(
            select(UserSubscription).where(
                UserSubscription.stripe_subscription_id == subscription_id
            )
        )
        subscription = result.scalar_one_or_none()

        if not subscription:
            return None

        # Process event
        if event_type == "customer.subscription.updated":
            # Update subscription details
            # In production, sync with Stripe data
            pass

        elif event_type == "customer.subscription.deleted":
            # Subscription was canceled externally
            subscription.status = "canceled"
            subscription.canceled_at = datetime.utcnow()

        elif event_type == "invoice.paid":
            # Invoice paid - log renewal
            await self._log_event(
                subscription_id=subscription.id,
                event_type="subscription_renewed",
                event_data={
                    "invoice_id": event_data.get("id"),
                    "amount": event_data.get("amount_paid"),
                },
            )

        subscription.updated_at = datetime.utcnow()
        await self.db.commit()

        # Log webhook event
        webhook_event = SubscriptionEvent(
            id=uuid4(),
            user_id=subscription.user_id,
            subscription_id=subscription_id,
            event_type=event_type,
            event_data=event_data,
            processed=True,
            created_at=datetime.utcnow(),
        )
        self.db.add(webhook_event)
        await self.db.commit()

        return webhook_event

    async def _log_event(
        self,
        subscription_id: UUID,
        event_type: str,
        event_data: dict | None = None,
    ) -> SubscriptionEvent:
        """Log a subscription event."""
        event = SubscriptionEvent(
            id=uuid4(),
            subscription_id=subscription_id,
            event_type=event_type,
            event_data=event_data,
            created_at=datetime.utcnow(),
        )
        self.db.add(event)
        await self.db.commit()
        return event

    async def get_usage_summary(
        self,
        user_id: UUID,
    ) -> dict:
        """Get a summary of user's current usage vs limits."""
        subscription, limits = await self.get_user_subscription(user_id)

        # Get current usage for all tracked features
        usage = {}
        for feature in [
            "projects",
            "snapshots",
            "versions",
            "ai_generations_monthly",
            "experiments",
            "funnels",
        ]:
            usage[feature] = await self._get_feature_usage(user_id, feature)

        return {
            "plan": subscription.plan_id if subscription else "free",
            "status": subscription.status if subscription else "active",
            "usage": usage,
            "limits": limits,
            "resets_at": subscription.current_period_end.isoformat() if subscription and subscription.current_period_end else None,
        }
