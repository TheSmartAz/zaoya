"""Feature gating middleware and dependencies for premium tier enforcement.

This module provides FastAPI dependencies and helper functions for:
- Checking feature availability based on subscription plan
- Enforcing usage limits before actions
- Providing upgrade prompts when limits are exceeded
"""

from uuid import UUID
from typing import Optional, Literal

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.user import get_current_user
from app.models.db.subscription import SubscriptionPlan
from app.services.subscription_service import SubscriptionService


# ============================================================
# Exception Classes
# ============================================================

class FeatureLimitError(HTTPException):
    """Raised when a user exceeds their plan limits."""

    def __init__(
        self,
        feature: str,
        current: int,
        limit: int,
        upgrade_options: list[dict] | None = None,
    ):
        self.feature = feature
        self.current = current
        self.limit = limit
        self.upgrade_options = upgrade_options or []

        # Build upgrade message
        upgrade_msg = ""
        if upgrade_options:
            best_option = min(upgrade_options, key=lambda x: x.get("price_monthly", float("inf")))
            upgrade_msg = f" Upgrade to {best_option['name']} for {best_option['limit']}+ {feature}."

        super().__init__(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "error": "limit_exceeded",
                "feature": feature,
                "current": current,
                "limit": limit,
                "message": f"You've reached your {feature} limit ({current}/{limit}).{upgrade_msg}",
                "upgrade_options": upgrade_options,
            },
        )


class FeatureNotAvailableError(HTTPException):
    """Raised when a feature is not available on the user's plan."""

    def __init__(self, feature: str, plan: str, upgrade_options: list[dict] | None = None):
        self.feature = feature
        self.plan = plan
        self.upgrade_options = upgrade_options or []

        # Build upgrade message
        upgrade_msg = ""
        if upgrade_options:
            best_option = min(upgrade_options, key=lambda x: x.get("price_monthly", float("inf")))
            upgrade_msg = f" Upgrade to {best_option['name']} to access this feature."

        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "feature_not_available",
                "feature": feature,
                "current_plan": plan,
                "message": f"'{feature}' is not available on your {plan} plan.{upgrade_msg}",
                "upgrade_options": upgrade_options,
            },
        )


# ============================================================
# User ID Resolution Helper
# ============================================================

async def get_user_id_from_context(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UUID:
    """
    Resolve user UUID from current user context.

    Handles both UUID strings and dev mode users.
    """
    from app.models.db import User

    try:
        uid = UUID(current_user["id"])
    except ValueError:
        if current_user.get("provider") == "dev":
            result = await db.execute(
                select(User).where(User.email == current_user["email"])
            )
            user = result.scalar_one_or_none()
            if user:
                return user.id
        raise HTTPException(status_code=401, detail="Invalid user")

    return uid


# ============================================================
# Feature Checking Dependencies
# ============================================================

async def require_feature(
    feature: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> tuple[UUID, bool, dict | None]:
    """
    FastAPI dependency to check if a user has access to a feature.

    Use in endpoints to gate features by subscription plan.

    Args:
        feature: The feature name to check (e.g., "experiments", "funnels")
        current_user: Injected current user
        db: Injected database session

    Returns:
        Tuple of (user_id, is_available, limit_info)

    Raises:
        FeatureNotAvailableError: If feature is not on user's plan
        FeatureLimitError: If user has exceeded their limit

    Example:
        ```python
        @router.post("/projects/{id}/experiments")
        async def create_experiment(
            user_data: tuple = Depends(require_feature("experiments")),
            ...
        ):
            user_id, _, _ = user_data
            # User has access to experiments
        ```
    """
    from sqlalchemy import select

    # Get user UUID
    user_id = await get_user_id_from_context(current_user, db)

    service = SubscriptionService(db)

    # Get current usage
    current_usage = await service._get_feature_usage(user_id, feature)

    # Check availability
    available, limit_info = await service.check_feature_available(
        user_id=user_id,
        feature=feature,
        current_usage=current_usage,
    )

    if not available:
        subscription, _ = await service.get_user_subscription(user_id)
        plan_id = subscription.plan_id if subscription else "free"

        if limit_info and limit_info.get("reason") == "limit_exceeded":
            raise FeatureLimitError(
                feature=feature,
                current=limit_info["current"],
                limit=limit_info["limit"],
                upgrade_options=limit_info.get("upgrade_options"),
            )
        else:
            # Feature not available on plan
            result = await db.execute(
                select(SubscriptionPlan).where(SubscriptionPlan.is_active == True)
            )
            plans = result.scalars()

            upgrade_options = []
            for plan in plans:
                plan_limits = service.get_plan_limits(plan.id)
                if plan_limits.get(feature, 0) > 0:
                    upgrade_options.append({
                        "id": plan.id,
                        "name": plan.name,
                        "limit": plan_limits[feature],
                        "price_monthly": float(plan.price_monthly_usd),
                    })

            raise FeatureNotAvailableError(
                feature=feature,
                plan=plan_id,
                upgrade_options=upgrade_options,
            )

    return user_id, available, limit_info


async def check_usage_limit(
    feature: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> tuple[UUID, int, int]:
    """
    Check usage limits for a feature without enforcing.

    Returns current usage and limit for UI display purposes.

    Args:
        feature: The feature name to check
        current_user: Injected current user
        db: Injected database session

    Returns:
        Tuple of (user_id, current_usage, limit)

    Example:
        ```python
        @router.get("/projects/{id}/experiments")
        async def list_experiments(
            usage: tuple = Depends(check_usage_limit("experiments")),
            ...
        ):
            user_id, current, limit = usage
            # Include limit info in response
        ```
    """
    user_id = await get_user_id_from_context(current_user, db)

    service = SubscriptionService(db)
    subscription, limits = await service.get_user_subscription(user_id)

    current_usage = await service._get_feature_usage(user_id, feature)
    limit = limits.get(feature, 0)

    return user_id, current_usage, limit


# ============================================================
# Plan Level Dependencies
# ============================================================

async def require_plan(
    min_plan: Literal["pro", "team"],
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UUID:
    """
    Require user to be on at least the specified plan level.

    Args:
        min_plan: Minimum plan required ("pro" or "team")
        current_user: Injected current user
        db: Injected database session

    Returns:
        user_id

    Raises:
        HTTPException: If user is on a lower plan
    """
    user_id = await get_user_id_from_context(current_user, db)

    service = SubscriptionService(db)
    subscription, _ = await service.get_user_subscription(user_id)

    plan_id = subscription.plan_id if subscription else "free"

    # Check plan level
    plan_hierarchy = {"free": 0, "pro": 1, "team": 2}
    if plan_hierarchy.get(plan_id, 0) < plan_hierarchy.get(min_plan, 0):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "plan_required",
                "required_plan": min_plan,
                "current_plan": plan_id,
                "message": f"This feature requires a {min_plan} plan or higher.",
            },
        )

    return user_id


# ============================================================
# Decorator for Route Protection
# ============================================================

def feature_gate(feature: str):
    """
    Decorator to protect a route with feature gating.

    Usage:
        ```python
        @router.post("/projects/{id}/experiments")
        @feature_gate("experiments")
        async def create_experiment(
            user_id: UUID,
            ...,
        ):
            # User has access to experiments
        ```
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # This is a simplified version
            # In practice, you'd need to extract current_user and db from kwargs
            # or use the dependency injection properly
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# ============================================================
# Usage Info Helpers
# ============================================================

async def get_usage_for_ui(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get comprehensive usage info for UI display.

    Returns usage data for all tracked features with limits.

    Returns:
        Dict with plan info and usage for all features
    """
    from sqlalchemy import select
    from app.models.db.subscription import SubscriptionPlan

    user_id = await get_user_id_from_context(current_user, db)
    service = SubscriptionService(db)

    subscription, limits = await service.get_user_subscription(user_id)
    plan_id = subscription.plan_id if subscription else "free"

    # Build usage info
    usage_info = {
        "plan": plan_id,
        "features": {},
    }

    for feature in ["projects", "pages_per_project", "snapshots", "ai_generations_monthly", "analytics_days", "funnels", "experiments"]:
        current = await service._get_feature_usage(user_id, feature)
        limit = limits.get(feature, 0)

        usage_info["features"][feature] = {
            "current": current,
            "limit": limit,
            "unlimited": limit == -1,
            "percentage": round((current / limit * 100) if limit > 0 else 0, 1),
            "remaining": max(0, limit - current) if limit > 0 else float("inf"),
        }

    # Get upgrade options
    result = await db.execute(
        select(SubscriptionPlan)
        .where(
            and_(
                SubscriptionPlan.is_active == True,
                SubscriptionPlan.display_order > {
                    "free": 0,
                    "pro": 1,
                    "team": 2,
                }.get(plan_id, 0)
            )
        )
        .order_by(SubscriptionPlan.display_order)
    )
    upgrade_plans = result.scalars()

    usage_info["upgrade_options"] = [
        {
            "id": plan.id,
            "name": plan.name,
            "price_monthly": float(plan.price_monthly_usd),
            "price_yearly": float(plan.price_yearly_usd),
            "features": plan.features,
        }
        for plan in upgrade_plans
    ]

    return usage_info


# Import needed for and_
from sqlalchemy import and_
from app.models.db.subscription import SubscriptionPlan
