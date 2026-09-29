"""Integration tests for /api/v1/admin/* — real DB path, no dependency overrides for auth/db."""
import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_db_session
from app.db.user_repository import create_user
from app.main import create_app
from app.models.user import UserRole
from tests.conftest import override_db_session


@pytest.fixture
def admin_client(db_engine) -> TestClient:
    """Client with only the DB overridden — auth, admin routes, and provider
    config storage all run for real."""
    app = create_app()
    app.dependency_overrides[get_db_session] = override_db_session(db_engine)
    return TestClient(app, raise_server_exceptions=True)


async def _seed_admin(db_engine, email: str, password_hash: str = "unused"):
    from sqlalchemy.ext.asyncio import async_sessionmaker

    sessionmaker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with sessionmaker() as session:
        await create_user(session, email=email, hashed_password=password_hash, role=UserRole.admin)


def _login(client, email, password):
    return client.post("/api/v1/auth/login", json={"email": email, "password": password}).json()["access_token"]


# ── auth gating ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_llm_config_as_non_admin_returns_403(admin_client):
    admin_client.post("/api/v1/auth/register", json={"email": "plain@example.com", "password": "secret123"})
    token = _login(admin_client, "plain@example.com", "secret123")
    resp = admin_client.get("/api/v1/admin/config/llm", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_put_embedder_config_as_non_admin_returns_403(admin_client):
    admin_client.post("/api/v1/auth/register", json={"email": "plain2@example.com", "password": "secret123"})
    token = _login(admin_client, "plain2@example.com", "secret123")
    resp = admin_client.put(
        "/api/v1/admin/config/embedder",
        headers={"Authorization": f"Bearer {token}"},
        json={"provider_label": "openai", "model_name": "text-embedding-3-small"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_get_llm_config_without_auth_returns_401(admin_client):
    resp = admin_client.get("/api/v1/admin/config/llm")
    assert resp.status_code == 401


# ── happy path as admin ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_llm_config_before_setup_returns_null(admin_client, db_engine):
    from app.core.security import hash_password

    await _seed_admin(db_engine, "admin1@example.com", hash_password("secret123"))
    token = _login(admin_client, "admin1@example.com", "secret123")
    resp = admin_client.get("/api/v1/admin/config/llm", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json() is None


@pytest.mark.asyncio
async def test_update_then_get_llm_config_as_admin(admin_client, db_engine):
    from app.core.security import hash_password

    await _seed_admin(db_engine, "admin2@example.com", hash_password("secret123"))
    token = _login(admin_client, "admin2@example.com", "secret123")
    headers = {"Authorization": f"Bearer {token}"}

    put_resp = admin_client.put(
        "/api/v1/admin/config/llm",
        headers=headers,
        json={"provider_label": "openai", "model_name": "gpt-4o-mini", "temperature": 0, "api_key": "sk-real-key"},
    )
    assert put_resp.status_code == 200
    body = put_resp.json()
    assert body["api_key_set"] is True
    assert body["model_name"] == "gpt-4o-mini"
    assert "sk-real-key" not in put_resp.text  # plaintext never echoed back

    get_resp = admin_client.get("/api/v1/admin/config/llm", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["model_name"] == "gpt-4o-mini"
    assert "sk-real-key" not in get_resp.text


@pytest.mark.asyncio
async def test_update_embedder_config_supports_keyless_local_runtime(admin_client, db_engine):
    from app.core.security import hash_password

    await _seed_admin(db_engine, "admin3@example.com", hash_password("secret123"))
    token = _login(admin_client, "admin3@example.com", "secret123")
    headers = {"Authorization": f"Bearer {token}"}

    resp = admin_client.put(
        "/api/v1/admin/config/embedder",
        headers=headers,
        json={
            "provider_label": "ollama",
            "model_name": "nomic-embed-text",
            "base_url": "http://localhost:11434/v1",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["api_key_set"] is False
    assert body["base_url"] == "http://localhost:11434/v1"


@pytest.mark.asyncio
async def test_setting_and_clearing_api_key_in_same_request_returns_422(admin_client, db_engine):
    from app.core.security import hash_password

    await _seed_admin(db_engine, "admin4@example.com", hash_password("secret123"))
    token = _login(admin_client, "admin4@example.com", "secret123")
    headers = {"Authorization": f"Bearer {token}"}

    resp = admin_client.put(
        "/api/v1/admin/config/llm",
        headers=headers,
        json={
            "provider_label": "openai",
            "model_name": "gpt-4o-mini",
            "api_key": "sk-x",
            "clear_api_key": True,
        },
    )
    assert resp.status_code == 422
