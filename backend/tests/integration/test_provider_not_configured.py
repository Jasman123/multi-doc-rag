"""Confirms the real (non-faked) get_llm/get_embedder dependencies — not just
the FakeLLM/FakeEmbedder overrides used elsewhere — correctly surface a 503
when no admin has configured a provider yet, instead of crashing."""
import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_collection, get_db_session
from app.main import create_app
from tests.conftest import override_db_session


@pytest.fixture
def unconfigured_client(db_engine, empty_collection) -> TestClient:
    """Only DB and the Chroma collection are overridden — get_llm/get_embedder
    run for real against an empty provider_configs table."""
    app = create_app()
    app.dependency_overrides[get_db_session] = override_db_session(db_engine)
    app.dependency_overrides[get_collection] = lambda: empty_collection
    return TestClient(app, raise_server_exceptions=True)


@pytest.mark.asyncio
async def test_query_returns_503_when_no_provider_configured(unconfigured_client):
    unconfigured_client.post("/api/v1/auth/register", json={"email": "u@example.com", "password": "secret123"})
    login = unconfigured_client.post("/api/v1/auth/login", json={"email": "u@example.com", "password": "secret123"})
    token = login.json()["access_token"]

    resp = unconfigured_client.post(
        "/api/v1/query/",
        headers={"Authorization": f"Bearer {token}"},
        json={"question": "anything", "document_ids": [], "top_k": 8},
    )
    assert resp.status_code == 503
