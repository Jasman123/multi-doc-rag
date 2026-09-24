import uuid

import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)

from app.db.user_repository import create_user, get_user_by_email, get_user_by_id
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, UserCreateRequest, UserResponse


async def register_user(db: AsyncSession, request: UserCreateRequest) -> UserResponse:
    existing = await get_user_by_email(db, request.email)

    if existing is not None:
        raise ValueError(f"Email: '{request.email}' is already registered.")

    user = await create_user(db, email=request.email, hashed_password=hash_password(request.password))
    return UserResponse.model_validate(user)

async def authenticate_user(db: AsyncSession, request: LoginRequest) -> User:
    user = await get_user_by_email(db, request.email)
    if user is None or not verify_password(request.password, user.hashed_password):
        raise ValueError("Invalid email or password.")
    if not user.is_active:
        raise ValueError("This account has been deactivated.")
    return user

def issue_tokens(user: User) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(str(user.id), user.role.value),
        refresh_token=create_refresh_token(str(user.id), user.token_version),
    )

async def refresh_tokens(db: AsyncSession, refresh_token: str) -> TokenResponse:
    try:
        payload = decode_token(refresh_token)
    except jwt.InvalidTokenError as exc:
        raise ValueError("Invalid or expired refresh token.") from exc

    if payload.get("type") != "refresh":
        raise ValueError("Invalid token type.")

    try:
        user_id = uuid.UUID(payload["sub"])
    except (KeyError, ValueError) as exc:
        raise ValueError("Invalid refresh token payload.") from exc

    user = await get_user_by_id(db, user_id)
    if user is None or not user.is_active:
        raise ValueError("User not found or inactive.")
    if payload.get("ver") != user.token_version:
        raise ValueError("Refresh token has been revoked.")

    return issue_tokens(user)
