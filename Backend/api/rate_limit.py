"""API rate limiting to prevent abuse."""
import os

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse

# Env is loaded in Backend.main / worker_main before routers import this module.
_DEFAULT = os.getenv("RATE_LIMIT_DEFAULT", "120/minute")
RATE_LIMIT_GENERATE = os.getenv("RATE_LIMIT_GENERATE", "15/minute")
RATE_LIMIT_AUTH = os.getenv("RATE_LIMIT_AUTH", "30/minute")

limiter = Limiter(key_func=get_remote_address, default_limits=[_DEFAULT])


async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "detail": str(exc.detail),
            "retry_after": "Please wait before making another request",
        },
    )
