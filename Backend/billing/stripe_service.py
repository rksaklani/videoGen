"""
Stripe integration — checkout, subscriptions, webhooks.
"""
import os
import stripe
from loguru import logger

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


class StripeService:
    """Handles all Stripe operations."""

    @staticmethod
    def create_checkout_session(email: str, plan_id: str, stripe_price_id: str) -> dict:
        """Create a Stripe Checkout session for subscription."""
        if not stripe.api_key:
            raise ValueError("Stripe API key not configured")

        try:
            session = stripe.checkout.Session.create(
                customer_email=email,
                payment_method_types=["card"],
                line_items=[{"price": stripe_price_id, "quantity": 1}],
                mode="subscription",
                success_url=f"{FRONTEND_URL}/dashboard/settings?billing=success",
                cancel_url=f"{FRONTEND_URL}/pricing?billing=cancelled",
                metadata={"plan_id": plan_id, "email": email},
            )
            logger.info(f"Checkout session created for {email}: {plan_id}")
            return {"checkout_url": session.url, "session_id": session.id}
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {e}")
            raise

    @staticmethod
    def create_portal_session(customer_id: str) -> dict:
        """Create a Stripe Customer Portal session for managing subscription."""
        try:
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=f"{FRONTEND_URL}/dashboard/settings",
            )
            return {"portal_url": session.url}
        except stripe.error.StripeError as e:
            logger.error(f"Stripe portal error: {e}")
            raise

    @staticmethod
    def verify_webhook(payload: bytes, sig_header: str) -> dict:
        """Verify and parse a Stripe webhook event."""
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, STRIPE_WEBHOOK_SECRET
            )
            return event
        except (ValueError, stripe.error.SignatureVerificationError) as e:
            logger.error(f"Webhook verification failed: {e}")
            raise

    @staticmethod
    def get_customer_subscription(customer_id: str) -> dict:
        """Get active subscription for a customer."""
        try:
            subs = stripe.Subscription.list(customer=customer_id, status="active", limit=1)
            if subs.data:
                sub = subs.data[0]
                return {
                    "subscription_id": sub.id,
                    "status": sub.status,
                    "plan": sub.metadata.get("plan_id", "unknown"),
                    "current_period_end": sub.current_period_end,
                }
            return None
        except stripe.error.StripeError:
            return None
