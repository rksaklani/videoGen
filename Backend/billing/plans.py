"""
Subscription plans and credit system.

Plans:
  Free:       5 videos/month, 5s max, watermark
  Creator:    100 videos/month, 30s max, no watermark
  Pro:        500 videos/month, 120s max, priority queue
  Enterprise: Unlimited, custom duration, dedicated GPU
"""

PLANS = {
    "free": {
        "name": "Free",
        "price_monthly": 0,
        "stripe_price_id": None,
        "videos_per_month": 5,
        "max_duration_seconds": 5,
        "max_avatars": 1,
        "watermark": True,
        "priority": False,
        "features": ["5 videos/month", "5 second max", "1 avatar", "Watermark"],
    },
    "creator": {
        "name": "Creator",
        "price_monthly": 29,
        "stripe_price_id": "",  # Set from Stripe dashboard
        "videos_per_month": 100,
        "max_duration_seconds": 30,
        "max_avatars": 5,
        "watermark": False,
        "priority": False,
        "features": ["100 videos/month", "30 second max", "5 avatars", "No watermark", "300+ voices"],
    },
    "pro": {
        "name": "Pro",
        "price_monthly": 79,
        "stripe_price_id": "",  # Set from Stripe dashboard
        "videos_per_month": 500,
        "max_duration_seconds": 120,
        "max_avatars": 20,
        "watermark": False,
        "priority": True,
        "features": ["500 videos/month", "2 minute max", "20 avatars", "No watermark", "Priority queue", "Multi-character", "Voice cloning"],
    },
    "enterprise": {
        "name": "Enterprise",
        "price_monthly": 299,
        "stripe_price_id": "",  # Set from Stripe dashboard
        "videos_per_month": 99999,
        "max_duration_seconds": 300,
        "max_avatars": 100,
        "watermark": False,
        "priority": True,
        "features": ["Unlimited videos", "5 minute max", "100 avatars", "Dedicated GPU", "API access", "Custom branding", "SLA support"],
    },
}


def get_plan(plan_id: str) -> dict:
    return PLANS.get(plan_id, PLANS["free"])


def get_all_plans() -> list:
    return [{"id": k, **v} for k, v in PLANS.items()]
