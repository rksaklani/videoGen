"""JWT authentication for the Avatar API."""
import os
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import hashlib
import secrets
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from loguru import logger

SECRET_KEY = (os.getenv("JWT_SECRET") or "").strip()
if not SECRET_KEY:
    SECRET_KEY = "videogen-dev-only-unsafe"
    logger.warning("JWT_SECRET is not set — using an insecure development default; set JWT_SECRET in production.")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = int(os.getenv("ACCESS_TOKEN_EXPIRE_HOURS", "24"))

security = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    """Hash password using SHA-256 + salt (simple, no bcrypt dependency issues)."""
    salt = secrets.token_hex(16)
    hashed = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}${hashed}"


def verify_password(plain: str, hashed: str) -> bool:
    """Verify password against stored hash."""
    try:
        salt, stored_hash = hashed.split("$", 1)
        return hashlib.sha256((salt + plain).encode()).hexdigest() == stored_hash
    except Exception:
        return False


def create_token(data: dict, expires_hours: int = ACCESS_TOKEN_EXPIRE_HOURS) -> str:
    to_encode = data.copy()
    to_encode["exp"] = datetime.utcnow() + timedelta(hours=expires_hours)
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None


_ANON = {"email": "anonymous", "name": "Anonymous"}


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """Like ``get_current_user`` but never 401: missing or bad JWT → anonymous (for list/read UX)."""
    if not credentials:
        return _ANON.copy()
    payload = decode_token(credentials.credentials)
    if not payload:
        logger.debug("JWT present but invalid or expired — treating as anonymous")
        return _ANON.copy()
    return {"email": payload.get("email"), "name": payload.get("name")}


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Require a valid JWT, or anonymous when no ``Authorization`` header is sent.

    If the client sends ``Authorization: Bearer …`` and the token is invalid/expired, returns **401**
    so browsers can clear stale ``localStorage`` tokens. Omit the header entirely to use the anonymous user.
    """
    if not credentials:
        return _ANON.copy()

    payload = decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"email": payload.get("email"), "name": payload.get("name")}
