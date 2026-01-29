"""Stripe webhook service for handling billing events.

This is a MOCK implementation for development.
In production, you would:
1. Verify webhook signatures using Stripe's SDK
2. Use actual Stripe API for payment processing
3. Handle more edge cases and idempotency
"""

import hashlib
import hmac
import json
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from typing import Optional, Literal

from fastapi import HTTPException, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db.subscription import (
    SubscriptionPlan,
    UserSubscription,
    SubscriptionEvent,
)
from app.services.subscription_service import PLAN_LIMITS


# ============================================================
# Webhook Signature Verification (Mock)
# ============================================================

def verify_stripe_webhook_signature(
    payload: bytes,
    signature_header: str,
    webhook_secret: str,
) -> bool:
    """
    Verify Stripe webhook signature.

    In production, use stripe.Webhook.construct_event():
    ```python
    import stripe
    event = stripe.Webhook.construct_event(
        payload, signature_header, webhook_secret
    )
    ```

    For now, this is a mock that always returns True in dev mode.
    """
    # In development, skip verification
    # In production, implement proper HMAC verification
    return True


# ============================================================
# Event Type Constants
# ============================================================

StripeEventType = Literal[
    "checkout.session.completed",
    "customer.subscription.created",
    "customer.subscription.updated",
    "customer.subscription.deleted",
    "invoice.paid",
    "invoice.payment_failed",
    "invoice.upcoming",
    "payment_method.attached",
]


# ============================================================
# Stripe Webhook Service
# ============================================================

class StripeWebhookService:
    """Service for handling Stripe webhook events."""

    def __init__(self, db: AsyncSession, webhook_secret: str | None = None):
        self.db = db
        self.webhook_secret = webhook_secret or "whsec_mock_secret"

    async def handle_webhook(
        self,
        payload: bytes,
        signature_header: str | None,
    ) -> SubscriptionEvent | None:
        """
        Process an incoming Stripe webhook event.

        Returns:
            The logged SubscriptionEvent, or None if event was ignored
        """
        # Verify signature (mocked in dev)
        if signature_header and not verify_stripe_webhook_signature(
            payload, signature_header, self.webhook_secret
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature",
            )

        # Parse event
        try:
            event_data = json.loads(payload)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON payload",
            )

        event_type = event_data.get("type")
        data = event_data.get("data", {})
        stripe_object = data.get("object", {})

        # Route to appropriate handler
        handler = self._get_handler(event_type)
        if handler:
            return await handler(stripe_object, event_data)
        else:
            # Log unhandled event
            await self._log_unknown_event(event_type, event_data)
            return None

    def _get_handler(self, event_type: str):
        """Get the handler function for an event type."""
        handlers = {
            "checkout.session.completed": self._handle_checkout_completed,
            "customer.subscription.created": self._handle_subscription_created,
            "customer.subscription.updated": self._handle_subscription_updated,
            "customer.subscription.deleted": self._handle_subscription_deleted,
            "invoice.paid": self._handle_invoice_paid,
            "invoice.payment_failed": self._handle_invoice_payment_failed,
        }
        return handlers.get(event_type)

    # ============================================================
    # Event Handlers
    # ============================================================

    async def _handle_checkout_completed(
        self,
        session: dict,
        event_data: dict,
    ) -> SubscriptionEvent:
        """
        Handle checkout.session.completed event.

        This is triggered when a customer completes the checkout flow.
        """
        stripe_subscription_id = session.get("subscription")
        customer_id = session.get("customer")
        user_id = self._extract_user_id_from_metadata(session)

        if not user_id:
            # Try to find user by customer email
            customer_email = session.get("customer_details", {}).get("email")
            if customer_email:
                from app.models.db import User
                result = await self.db.execute(
                    select(User).where(User.email == customer_email)
                )
                user = result.scalar_one_or_none()
                if user:
                    user_id = user.id

        if not user_id:
            # Log and return - we can't process without a user
            return await self._log_event(
                user_id=uuid4(),  # Placeholder
                event_type="checkout.session.completed",
                event_data={"error": "No user found", "session": session},
                processed=False,
            )

        # Map price to plan
        plan_id = self._get_plan_from_price_id(session.get("display_items", [{}])[0].get("price", {}).get("id", ""))

        # Create or update subscription
        result = await self.db.execute(
            select(UserSubscription).where(
                UserSubscription.user_id == user_id
            )
        )
        subscription = result.scalar_one_or_none()

        if subscription:
            # Update existing
            subscription.plan_id = plan_id
            subscription.status = "active"
            subscription.stripe_subscription_id = stripe_subscription_id
            subscription.stripe_customer_id = customer_id
            subscription.updated_at = datetime.utcnow()
        else:
            # Create new
            subscription = UserSubscription(
                id=uuid4(),
                user_id=user_id,
                plan_id=plan_id,
                status="active",
                billing_interval=self._get_interval_from_price(session),
                stripe_subscription_id=stripe_subscription_id,
                stripe_customer_id=customer_id,
                created_at=datetime.utcnow(),
            )
            self.db.add(subscription)

        await self.db.commit()
        await self.db.refresh(subscription)

        # Log the event
        return await self._log_event(
            subscription_id=subscription.id,
            event_type="checkout.session.completed",
            event_data={
                "stripe_subscription_id": stripe_subscription_id,
                "plan_id": plan_id,
            },
            processed=True,
        )

    async def _handle_subscription_created(
        self,
        stripe_sub: dict,
        event_data: dict,
    ) -> SubscriptionEvent:
        """Handle customer.subscription.created event."""
        # Find subscription by stripe ID
        result = await self.db.execute(
            select(UserSubscription).where(
                UserSubscription.stripe_subscription_id == stripe_sub.get("id")
            )
        )
        subscription = result.scalar_one_or_none()

        if subscription:
            # Already created via checkout
            subscription.status = stripe_sub.get("status", "active")
            await self.db.commit()

        return await self._log_event(
            subscription_id=subscription.id if subscription else uuid4(),
            event_type="customer.subscription.created",
            event_data={"stripe_id": stripe_sub.get("id")},
            processed=bool(subscription),
        )

    async def _handle_subscription_updated(
        self,
        stripe_sub: dict,
        event_data: dict,
    ) -> SubscriptionEvent:
        """Handle customer.subscription.updated event."""
        result = await self.db.execute(
            select(UserSubscription).where(
                UserSubscription.stripe_subscription_id == stripe_sub.get("id")
            )
        )
        subscription = result.scalar_one_or_none()

        if not subscription:
            return await self._log_event(
                subscription_id=uuid4(),
                event_type="customer.subscription.updated",
                event_data={"error": "Subscription not found", "stripe_id": stripe_sub.get("id")},
                processed=False,
            )

        # Update status and other fields
        old_status = subscription.status
        subscription.status = stripe_sub.get("status", subscription.status)

        # Check for plan change
        items = stripe_sub.get("items", {}).get("data", [])
        if items:
            price_id = items[0].get("price", {}).get("id", "")
            new_plan_id = self._get_plan_from_price_id(price_id)
            if new_plan_id != subscription.plan_id:
                old_plan = subscription.plan_id
                subscription.plan_id = new_plan_id

                # Log plan change
                await self._log_event(
                    subscription_id=subscription.id,
                    event_type="plan_changed_via_stripe",
                    event_data={"from_plan": old_plan, "to_plan": new_plan_id},
                )

        subscription.updated_at = datetime.utcnow()
        await self.db.commit()

        return await self._log_event(
            subscription_id=subscription.id,
            event_type="customer.subscription.updated",
            event_data={"old_status": old_status, "new_status": subscription.status},
            processed=True,
        )

    async def _handle_subscription_deleted(
        self,
        stripe_sub: dict,
        event_data: dict,
    ) -> SubscriptionEvent:
        """Handle customer.subscription.deleted event (subscription canceled)."""
        result = await self.db.execute(
            select(UserSubscription).where(
                UserSubscription.stripe_subscription_id == stripe_sub.get("id")
            )
        )
        subscription = result.scalar_one_or_none()

        if subscription:
            subscription.status = "canceled"
            subscription.canceled_at = datetime.utcnow()
            subscription.cancel_at_period_end = False
            subscription.updated_at = datetime.utcnow()
            await self.db.commit()

        return await self._log_event(
            subscription_id=subscription.id if subscription else uuid4(),
            event_type="customer.subscription.deleted",
            event_data={"stripe_id": stripe_sub.get("id")},
            processed=bool(subscription),
        )

    async def _handle_invoice_paid(
        self,
        invoice: dict,
        event_data: dict,
    ) -> SubscriptionEvent:
        """Handle invoice.paid event (successful payment)."""
        stripe_subscription_id = invoice.get("subscription")

        result = await self.db.execute(
            select(UserSubscription).where(
                UserSubscription.stripe_subscription_id == stripe_subscription_id
            )
        )
        subscription = result.scalar_one_or_none()

        if not subscription:
            return await self._log_event(
                subscription_id=uuid4(),
                event_type="invoice.paid",
                event_data={"error": "Subscription not found", "stripe_subscription_id": stripe_subscription_id},
                processed=False,
            )

        # Update period end date
        period_end = invoice.get("period_end")
        if period_end:
            subscription.current_period_end = datetime.fromtimestamp(period_end)

        # If subscription was canceled, ensure it's active now that payment succeeded
        if subscription.status == "past_due":
            subscription.status = "active"

        subscription.updated_at = datetime.utcnow()
        await self.db.commit()

        return await self._log_event(
            subscription_id=subscription.id,
            event_type="invoice.paid",
            event_data={
                "amount_paid": invoice.get("amount_paid"),
                "currency": invoice.get("currency"),
            },
            processed=True,
        )

    async def _handle_invoice_payment_failed(
        self,
        invoice: dict,
        event_data: dict,
    ) -> SubscriptionEvent:
        """Handle invoice.payment_failed event."""
        stripe_subscription_id = invoice.get("subscription")

        result = await self.db.execute(
            select(UserSubscription).where(
                UserSubscription.stripe_subscription_id == stripe_subscription_id
            )
        )
        subscription = result.scalar_one_or_none()

        if subscription:
            subscription.status = "past_due"
            subscription.updated_at = datetime.utcnow()
            await self.db.commit()

        return await self._log_event(
            subscription_id=subscription.id if subscription else uuid4(),
            event_type="invoice.payment_failed",
            event_data={"stripe_subscription_id": stripe_subscription_id},
            processed=bool(subscription),
        )

    # ============================================================
    # Helper Methods
    # ============================================================

    def _extract_user_id_from_metadata(self, obj: dict) -> UUID | None:
        """Extract user ID from object metadata."""
        metadata = obj.get("metadata", {})
        user_id_str = metadata.get("user_id")

        if user_id_str:
            try:
                return UUID(user_id_str)
            except ValueError:
                pass

        return None

    def _get_plan_from_price_id(self, price_id: str) -> str:
        """
        Map Stripe price ID to internal plan ID.

        In production, this would query the database or a config mapping.
        For now, use a simple convention:
        - price_*_free -> free
        - price_*_pro -> pro
        - price_*_team -> team
        """
        price_id_lower = price_id.lower()

        if "_team_" in price_id_lower or price_id_lower.endswith("_team"):
            return "team"
        elif "_pro_" in price_id_lower or price_id_lower.endswith("_pro"):
            return "pro"
        else:
            return "free"

    def _get_interval_from_price(self, session: dict) -> str:
        """Extract billing interval from checkout session."""
        items = session.get("display_items", [{}])
        if items:
            recurring = items[0].get("price", {}).get("recurring", {})
            return recurring.get("interval", "month")
        return "month"

    async def _log_event(
        self,
        event_type: str,
        event_data: dict | None = None,
        processed: bool = True,
        subscription_id: UUID | None = None,
        user_id: UUID | None = None,
    ) -> SubscriptionEvent:
        """Log a subscription/billing event."""
        event = SubscriptionEvent(
            id=uuid4(),
            user_id=user_id or uuid4(),
            subscription_id=subscription_id,
            event_type=event_type,
            event_data=event_data,
            processed=processed,
            created_at=datetime.utcnow(),
        )
        self.db.add(event)
        await self.db.commit()
        return event

    async def _log_unknown_event(self, event_type: str, event_data: dict) -> None:
        """Log an unhandled event type for monitoring."""
        event = SubscriptionEvent(
            id=uuid4(),
            user_id=uuid4(),  # Placeholder
            event_type=f"unknown_{event_type}",
            event_data=event_data,
            processed=False,
            created_at=datetime.utcnow(),
        )
        self.db.add(event)
        await self.db.commit()


# ============================================================
# Test Data / Mock Helpers
# ============================================================

class MockStripeEvents:
    """Mock Stripe webhook events for testing."""

    @staticmethod
    def checkout_session_completed(
        user_id: str,
        plan_id: str = "pro",
        interval: str = "month",
    ) -> dict:
        """Generate a mock checkout.session.completed event."""
        price_map = {
            "free": "price_free_monthly",
            "pro": "price_pro_monthly",
            "team": "price_team_monthly",
        }

        return {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_" + user_id[:8],
                    "object": "checkout.session",
                    "subscription": "sub_test_" + user_id[:8],
                    "customer": "cus_test_" + user_id[:8],
                    "customer_details": {
                        "email": f"user{user_id[:8]}@example.com",
                    },
                    "display_items": [
                        {
                            "price": {
                                "id": price_map.get(plan_id, "price_free_monthly"),
                                "recurring": {"interval": interval},
                            }
                        }
                    ],
                    "metadata": {"user_id": user_id},
                }
            },
        }

    @staticmethod
    def invoice_paid(subscription_id: str, amount: int = 999) -> dict:
        """Generate a mock invoice.paid event."""
        return {
            "type": "invoice.paid",
            "data": {
                "object": {
                    "id": "in_test_" + subscription_id[:8],
                    "subscription": subscription_id,
                    "amount_paid": amount,
                    "currency": "usd",
                    "period_end": 1735689600,  # 2025-01-01
                }
            },
        }

    @staticmethod
    def subscription_deleted(subscription_id: str) -> dict:
        """Generate a mock subscription.deleted event."""
        return {
            "type": "customer.subscription.deleted",
            "data": {
                "object": {
                    "id": subscription_id,
                    "status": "canceled",
                }
            },
        }
