"""Integration tests for /api/v1/auth/* — exercises the real JWT + DB path (no auth overrides)."""
import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_db_session
from app.db.user_repository import create_user
from app.main import create_app
from app.models.user import UserRole
from tests.conftest import override_db_session


@pytest.fixture
def auth_client(db_engine) -> TestClient:
    """Client with only the DB overridden — login/tokens/get_current_user run for real."""
    app = create_app()
    app.dependency_overrides[get_db_session] = override_db_session(db_engine)
    return TestClient(app, raise_server_exceptions=True)


# ── register ─────────────────────────────────────────────────────────────────

def test_register_returns_201_and_no_password_hash(auth_client):
    resp = auth_client.post(
        "/api/v1/auth/register", json={"email": "new@example.com", "password": "secret123"}
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "new@example.com"
    assert "password" not in body
    assert "hashed_password" not in body


def test_register_duplicate_email_returns_409(auth_client):
    auth_client.post("/api/v1/auth/register", json={"email": "dupe@example.com", "password": "secret123"})
    resp = auth_client.post("/api/v1/auth/register", json={"email": "dupe@example.com", "password": "secret123"})
    assert resp.status_code == 409


def test_register_short_password_returns_422(auth_client):
    resp = auth_client.post("/api/v1/auth/register", json={"email": "x@example.com", "password": "short"})
    assert resp.status_code == 422


# ── login ────────────────────────────────────────────────────────────────────

def test_login_returns_tokens(auth_client):
    auth_client.post("/api/v1/auth/register", json={"email": "login@example.com", "password": "secret123"})
    resp = auth_client.post("/api/v1/auth/login", json={"email": "login@example.com", "password": "secret123"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["token_type"] == "bearer"


def test_login_wrong_password_returns_401(auth_client):
    auth_client.post("/api/v1/auth/register", json={"email": "login2@example.com", "password": "secret123"})
    resp = auth_client.post("/api/v1/auth/login", json={"email": "login2@example.com", "password": "wrong"})
    assert resp.status_code == 401


# ── /auth/me ─────────────────────────────────────────────────────────────────

def test_me_with_valid_access_token_returns_user(auth_client):
    auth_client.post("/api/v1/auth/register", json={"email": "me@example.com", "password": "secret123"})
    login = auth_client.post("/api/v1/auth/login", json={"email": "me@example.com", "password": "secret123"})
    token = login.json()["access_token"]
    resp = auth_client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "me@example.com"


def test_me_without_token_returns_401(auth_client):
    resp = auth_client.get("/api/v1/auth/me")
    assert resp.status_code == 401


def test_me_with_garbage_token_returns_401(auth_client):
    resp = auth_client.get("/api/v1/auth/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert resp.status_code == 401


# ── /auth/refresh ────────────────────────────────────────────────────────────

def test_refresh_with_valid_token_issues_new_access_token(auth_client):
    auth_client.post("/api/v1/auth/register", json={"email": "refresh@example.com", "password": "secret123"})
    login = auth_client.post("/api/v1/auth/login", json={"email": "refresh@example.com", "password": "secret123"})
    refresh_token = login.json()["refresh_token"]
    resp = auth_client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    assert resp.json()["access_token"]


def test_refresh_with_garbage_token_returns_401(auth_client):
    resp = auth_client.post("/api/v1/auth/refresh", json={"refresh_token": "not-a-real-token"})
    assert resp.status_code == 401


# ── /auth/users (admin-only) ─────────────────────────────────────────────────

async def _seed_admin(db_engine, email: str, password_hash: str = "unused"):
    from sqlalchemy.ext.asyncio import async_sessionmaker

    sessionmaker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with sessionmaker() as session:
        await create_user(session, email=email, hashed_password=password_hash, role=UserRole.admin)


@pytest.mark.asyncio
async def test_users_as_non_admin_returns_403(auth_client):
    auth_client.post("/api/v1/auth/register", json={"email": "plain@example.com", "password": "secret123"})
    login = auth_client.post("/api/v1/auth/login", json={"email": "plain@example.com", "password": "secret123"})
    token = login.json()["access_token"]
    resp = auth_client.get("/api/v1/auth/users", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_users_as_admin_returns_200(auth_client, db_engine):
    from app.core.security import hash_password

    await _seed_admin(db_engine, "admin@example.com", hash_password("secret123"))
    login = auth_client.post("/api/v1/auth/login", json={"email": "admin@example.com", "password": "secret123"})
    token = login.json()["access_token"]
    resp = auth_client.get("/api/v1/auth/users", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
