"""Unit tests for auth_service — register/login/refresh against an in-memory DB."""
import pytest

from app.core.security import decode_token
from app.db.user_repository import bump_token_version, create_user, get_user_by_email
from app.schemas.auth import LoginRequest, UserCreateRequest
from app.services.auth_service import (
    authenticate_user,
    issue_tokens,
    refresh_tokens,
    register_user,
)

pytestmark = pytest.mark.asyncio


# ── register_user ────────────────────────────────────────────────────────────

async def test_register_user_creates_user(db_session):
    request = UserCreateRequest(email="new@example.com", password="secret123")
    response = await register_user(db_session, request)
    assert response.email == "new@example.com"
    assert response.role == "user"


async def test_register_user_persists_hashed_not_plaintext_password(db_session):
    request = UserCreateRequest(email="new@example.com", password="secret123")
    await register_user(db_session, request)
    user = await get_user_by_email(db_session, "new@example.com")
    assert user.hashed_password != "secret123"


async def test_register_user_duplicate_email_raises(db_session):
    request = UserCreateRequest(email="dupe@example.com", password="secret123")
    await register_user(db_session, request)
    with pytest.raises(ValueError, match="already registered"):
        await register_user(db_session, request)


# ── authenticate_user ────────────────────────────────────────────────────────

async def test_authenticate_user_correct_credentials_succeeds(db_session):
    await register_user(db_session, UserCreateRequest(email="a@example.com", password="secret123"))
    user = await authenticate_user(db_session, LoginRequest(email="a@example.com", password="secret123"))
    assert user.email == "a@example.com"


async def test_authenticate_user_wrong_password_raises(db_session):
    await register_user(db_session, UserCreateRequest(email="a@example.com", password="secret123"))
    with pytest.raises(ValueError, match="Invalid email or password"):
        await authenticate_user(db_session, LoginRequest(email="a@example.com", password="wrong"))


async def test_authenticate_user_unknown_email_raises(db_session):
    with pytest.raises(ValueError, match="Invalid email or password"):
        await authenticate_user(db_session, LoginRequest(email="ghost@example.com", password="secret123"))


async def test_authenticate_user_inactive_account_raises(db_session):
    from app.core.security import hash_password

    user = await create_user(
        db_session, email="inactive@example.com", hashed_password=hash_password("secret123")
    )
    user.is_active = False
    await db_session.commit()
    with pytest.raises(ValueError, match="deactivated"):
        await authenticate_user(db_session, LoginRequest(email="inactive@example.com", password="secret123"))


# ── issue_tokens / refresh_tokens ────────────────────────────────────────────

async def test_issue_tokens_access_token_matches_user(db_session):
    user = await create_user(db_session, email="tok@example.com", hashed_password="unused")
    tokens = issue_tokens(user)
    payload = decode_token(tokens.access_token)
    assert payload["sub"] == str(user.id)
    assert payload["role"] == user.role.value


async def test_refresh_tokens_valid_token_issues_new_pair(db_session):
    user = await create_user(db_session, email="ref@example.com", hashed_password="unused")
    tokens = issue_tokens(user)
    new_tokens = await refresh_tokens(db_session, tokens.refresh_token)
    payload = decode_token(new_tokens.access_token)
    assert payload["sub"] == str(user.id)


async def test_refresh_tokens_garbage_token_raises(db_session):
    with pytest.raises(ValueError, match="Invalid or expired"):
        await refresh_tokens(db_session, "not-a-real-token")


async def test_refresh_tokens_access_token_used_as_refresh_raises(db_session):
    user = await create_user(db_session, email="wrongtype@example.com", hashed_password="unused")
    tokens = issue_tokens(user)
    with pytest.raises(ValueError, match="Invalid token type"):
        await refresh_tokens(db_session, tokens.access_token)


async def test_refresh_tokens_revoked_after_bump_token_version(db_session):
    """Logout-everywhere: bumping token_version invalidates outstanding refresh tokens."""
    user = await create_user(db_session, email="revoked@example.com", hashed_password="unused")
    tokens = issue_tokens(user)
    await bump_token_version(db_session, user)
    with pytest.raises(ValueError, match="revoked"):
        await refresh_tokens(db_session, tokens.refresh_token)
