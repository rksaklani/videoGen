"""Billing API endpoints — plans, checkout, usage, webhooks."""
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from loguru import logger

from Backend.auth.jwt import get_current_user
from Backend.billing.plans import get_all_plans, get_plan
from Backend.billing.stripe_service import StripeService
from Backend.billing.usage import UsageTracker

router = APIRouter(prefix="/billing", tags=["Billing"])
usage_tracker = UsageTracker()


@router.get("/plans")
async def list_plans():
    """List all available subscription plans."""
    return {"plans": get_all_plans()}


@router.get("/usage")
async def get_usage(user: dict = Depends(get_current_user)):
    """Get current month's usage for the logged-in user."""
    usage = usage_tracker.get_usage(user["email"])
    limits = usage_tracker.check_limit(user["email"], "free")  # TODO: get user's actual plan
    return {**usage, **limits}


@router.post("/checkout")
async def create_checkout(
    plan_id: str,
    user: dict = Depends(get_current_user),
):
    """Create a Stripe Checkout session to subscribe to a plan."""
    plan = get_plan(plan_id)
    if not plan or plan_id == "free":
        raise HTTPException(400, "Invalid plan or free plan doesn't need checkout")

    stripe_price_id = plan.get("stripe_price_id")
    if not stripe_price_id:
        raise HTTPException(400, f"Stripe price not configured for plan: {plan_id}")

    try:
        result = StripeService.create_checkout_session(
            email=user["email"],
            plan_id=plan_id,
            stripe_price_id=stripe_price_id,
        )
        return result
    except Exception as e:
        raise HTTPException(500, f"Checkout failed: {str(e)}")


@router.post("/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events (subscription created, cancelled, etc)."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = StripeService.verify_webhook(payload, sig_header)
    except Exception:
        raise HTTPException(400, "Invalid webhook signature")

    event_type = event["type"]
    data = event["data"]["object"]

    if event_type == "checkout.session.completed":
        email = data.get("customer_email") or data.get("metadata", {}).get("email")
        plan_id = data.get("metadata", {}).get("plan_id")
        customer_id = data.get("customer")
        logger.info(f"Subscription created: {email} → {plan_id} (customer: {customer_id})")
        # TODO: Update user's plan in database

    elif event_type == "customer.subscription.deleted":
        customer_id = data.get("customer")
        logger.info(f"Subscription cancelled: customer {customer_id}")
        # TODO: Downgrade user to free plan

    elif event_type == "invoice.payment_failed":
        customer_id = data.get("customer")
        logger.warning(f"Payment failed: customer {customer_id}")

    return JSONResponse({"status": "ok"})


@router.post("/portal")
async def customer_portal(user: dict = Depends(get_current_user)):
    """Get Stripe Customer Portal URL for managing subscription."""
    # TODO: Get customer_id from database
    raise HTTPException(501, "Customer portal not yet configured. Set up Stripe first.")
