"""Authentication endpoints — register, login, profile."""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field
from Backend.auth.jwt import hash_password, verify_password, create_token
from Backend.db.repository import UserRepository
from Backend.api.rate_limit import limiter, RATE_LIMIT_AUTH

router = APIRouter(prefix="/auth", tags=["Authentication"])
user_repo = UserRepository()


class RegisterRequest(BaseModel):
    email: str = Field(..., min_length=5)
    name: str = Field(..., min_length=2)
    password: str = Field(..., min_length=6)


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    name: str
    email: str


@router.post("/register", response_model=TokenResponse)
@limiter.limit(RATE_LIMIT_AUTH)
async def register(request: Request, req: RegisterRequest):
    existing = await user_repo.get_by_email(req.email)
    if existing:
        raise HTTPException(400, "Email already registered")

    hashed = hash_password(req.password)
    await user_repo.create(email=req.email, name=req.name, hashed_password=hashed)

    token = create_token({"email": req.email, "name": req.name})
    return TokenResponse(access_token=token, name=req.name, email=req.email)


@router.post("/login", response_model=TokenResponse)
@limiter.limit(RATE_LIMIT_AUTH)
async def login(request: Request, req: LoginRequest):
    user = await user_repo.get_by_email(req.email)
    if not user or not verify_password(req.password, user["hashed_password"]):
        raise HTTPException(401, "Invalid email or password")

    token = create_token({"email": user["email"], "name": user["name"]})
    return TokenResponse(access_token=token, name=user["name"], email=user["email"])
