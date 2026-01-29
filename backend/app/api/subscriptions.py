"""Subscriptions API for premium tier management."""

from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import Optional
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.user import get_current_user
from app.models.db import Project, Snapshot
from app.services.subscription_service import SubscriptionService, PLAN_LIMITS


# ============================================================
# Request/Response Models
# ============================================================

class UpgradeSubscriptionRequest(BaseModel):
    """Request to upgrade subscription."""
    plan_id: str
    billing_interval: str = "month"  # month or year


class CheckFeatureRequest(BaseModel):
    """Request to check if a feature is available."""
    feature: str
    current_usage: int = 0


class FeatureCheckResponse(BaseModel):
    """Response for feature availability check."""
    available: bool
    limit_info: Optional[dict] = None


router = APIRouter()


# ============================================================
# Helper Functions
# ============================================================

async def get_user_id(current_user: dict, db: AsyncSession) -> UUID:
    """Get UUID for current user."""
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
# Plans Endpoints
# ============================================================

@router.get("/subscriptions/plans")
async def list_plans(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List available subscription plans."""
    service = SubscriptionService(db)

    # Ensure default plans are seeded
    await service.seed_default_plans()

    plans = await service.get_all_plans()

    return {
        "plans": [
            {
                "id": plan.id,
                "name": plan.name,
                "description": plan.description,
                "price_monthly_usd": float(plan.price_monthly_usd),
                "price_yearly_usd": float(plan.price_yearly_usd),
                "limits": plan.limits,
                "features": plan.features,
                "display_order": plan.display_order,
            }
            for plan in plans
        ],
    }


# ============================================================
# User Subscription Endpoints
# ============================================================

@router.get("/subscriptions/current")
async def get_current_subscription(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's subscription and plan details."""
    user_id = await get_user_id(current_user, db)
    service = SubscriptionService(db)

    subscription, limits = await service.get_user_subscription(user_id)

    # Get usage summary
    usage = {}
    for feature in ["projects", "snapshots", "ai_generations_monthly", "experiments", "funnels"]:
        usage[feature] = await service._get_feature_usage(user_id, feature)

    return {
        "subscription": {
            "id": str(subscription.id) if subscription else None,
            "plan_id": subscription.plan_id if subscription else "free",
            "status": subscription.status if subscription else "active",
            "billing_interval": subscription.billing_interval if subscription else None,
            "cancel_at_period_end": subscription.cancel_at_period_end if subscription else None,
            "current_period_end": subscription.current_period_end.isoformat() if subscription and subscription.current_period_end else None,
        } if subscription else None,
        "limits": limits,
        "usage": usage,
    }


@router.get("/subscriptions/usage")
async def get_usage_summary(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed usage summary showing limits vs current usage."""
    user_id = await get_user_id(current_user, db)
    service = SubscriptionService(db)

    return await service.get_usage_summary(user_id)


@router.post("/subscriptions/upgrade")
async def upgrade_subscription(
    request: UpgradeSubscriptionRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upgrade or change subscription plan."""
    user_id = await get_user_id(current_user, db)
    service = SubscriptionService(db)

    try:
        subscription = await service.upgrade_subscription(
            user_id=user_id,
            new_plan_id=request.plan_id,
            billing_interval=request.billing_interval,
        )

        # Get plan details
        plan = await service.get_plan(request.plan_id)

        return {
            "subscription_id": str(subscription.id),
            "plan_id": subscription.plan_id,
            "status": subscription.status,
            "billing_interval": subscription.billing_interval,
            "next_billing_date": subscription.current_period_end.isoformat() if subscription.current_period_end else None,
            "plan": {
                "id": plan.id,
                "name": plan.name,
                "limits": plan.limits,
                "features": plan.features,
            } if plan else None,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/subscriptions/cancel")
async def cancel_subscription(
    cancel_at_period_end: bool = True,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cancel the user's subscription."""
    user_id = await get_user_id(current_user, db)
    service = SubscriptionService(db)

    try:
        subscription = await service.cancel_subscription(
            user_id=user_id,
            cancel_at_period_end=cancel_at_period_end,
        )

        return {
            "subscription_id": str(subscription.id),
            "status": subscription.status,
            "cancel_at_period_end": subscription.cancel_at_period_end,
            "effective_date": subscription.canceled_at.isoformat() if subscription.canceled_at else None,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================
# Feature Gating Endpoints
# ============================================================

@router.post("/subscriptions/check-feature")
async def check_feature(
    request: CheckFeatureRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Check if a feature is available for the current user.

    Useful for client-side feature gating.
    """
    user_id = await get_user_id(current_user, db)
    service = SubscriptionService(db)

    try:
        available, limit_info = await service.check_feature_available(
            user_id=user_id,
            feature=request.feature,
            current_usage=request.current_usage,
        )

        return FeatureCheckResponse(
            available=available,
            limit_info=limit_info,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================
# Billing Webhook (Stripe)
# ============================================================

@router.post("/webhooks/stripe")
async def stripe_webhook(
    raw_data: bytes,
    stripe_signature: str = Header(None, alias="Stripe-Signature"),
    db: AsyncSession = Depends(get_db),
):
    """
    Handle Stripe webhook events.

    Supports events:
    - checkout.session.completed: New subscription created
    - customer.subscription.created: Subscription initialized
    - customer.subscription.updated: Plan changed or renewed
    - customer.subscription.deleted: Subscription canceled
    - invoice.paid: Successful payment
    - invoice.payment_failed: Payment failed
    """
    from app.services.stripe_webhook_service import StripeWebhookService

    service = StripeWebhookService(db, webhook_secret=None)  # No secret in dev

    try:
        event = await service.handle_webhook(raw_data, stripe_signature)
        if event:
            return {"received": True, "event_id": str(event.id)}
        return {"received": True, "handled": False}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================
# Admin Endpoints
# ============================================================

@router.post("/admin/subscriptions/grant")
async def grant_free_subscription(
    request: dict,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Grant a free subscription to a user (admin only)."""
    # TODO: Add admin check
    user_id = UUID(request.get("user_id"))
    plan_id = request.get("plan_id", "free")

    service = SubscriptionService(db)

    subscription = await service.create_free_subscription(user_id)

    # Update to requested plan if not free
    if plan_id != "free":
        subscription = await service.upgrade_subscription(
            user_id=user_id,
            new_plan_id=plan_id,
            billing_interval="month",
        )

    return {
        "subscription_id": str(subscription.id),
        "plan_id": subscription.plan_id,
        "status": subscription.status,
    }


@router.post("/admin/subscriptions/{subscription_id}")
async def modify_subscription(
    subscription_id: str,
    request: dict,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Modify a user's subscription (admin only)."""
    # TODO: Add admin check

    try:
        sid = UUID(subscription_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Invalid subscription ID")

    from app.models.db.subscription import UserSubscription

    result = await db.execute(
        select(UserSubscription).where(UserSubscription.id == sid)
    )
    subscription = result.scalar_one_or_none()

    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    # Apply changes
    if "status" in request:
        subscription.status = request["status"]
    if "plan_id" in request:
        subscription.plan_id = request["plan_id"]
    if "billing_interval" in request:
        subscription.billing_interval = request["billing_interval"]

    subscription.updated_at = datetime.utcnow()
    await db.commit()

    return {
        "subscription_id": str(subscription.id),
        "plan_id": subscription.plan_id,
        "status": subscription.status,
    }
