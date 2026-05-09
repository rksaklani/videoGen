"""
Usage tracking — count videos per user per month.
"""
from datetime import datetime
from loguru import logger
from Backend.billing.plans import get_plan


class UsageTracker:
    """Track video generation usage per user."""

    def __init__(self):
        # In-memory usage (replace with MongoDB in production)
        self._usage = {}  # {email: {month: count}}

    def _get_month_key(self) -> str:
        return datetime.utcnow().strftime("%Y-%m")

    def get_usage(self, email: str) -> dict:
        month = self._get_month_key()
        count = self._usage.get(email, {}).get(month, 0)
        return {"email": email, "month": month, "videos_generated": count}

    def increment(self, email: str):
        month = self._get_month_key()
        if email not in self._usage:
            self._usage[email] = {}
        self._usage[email][month] = self._usage[email].get(month, 0) + 1
        logger.info(f"Usage: {email} → {self._usage[email][month]} videos this month")

    def check_limit(self, email: str, plan_id: str = "free") -> dict:
        """Check if user has remaining quota."""
        plan = get_plan(plan_id)
        month = self._get_month_key()
        used = self._usage.get(email, {}).get(month, 0)
        limit = plan["videos_per_month"]
        remaining = max(0, limit - used)

        return {
            "allowed": remaining > 0,
            "used": used,
            "limit": limit,
            "remaining": remaining,
            "plan": plan_id,
        }

    def get_plan_limits(self, plan_id: str = "free") -> dict:
        """Get limits for a plan."""
        plan = get_plan(plan_id)
        return {
            "videos_per_month": plan["videos_per_month"],
            "max_duration_seconds": plan["max_duration_seconds"],
            "max_avatars": plan["max_avatars"],
            "watermark": plan["watermark"],
        }
