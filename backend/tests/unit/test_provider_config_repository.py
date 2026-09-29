import pytest

from app.db.provider_config_repository import get_config_by_role, upsert_config
from app.models.provider_config import ProviderRole


@pytest.mark.asyncio
async def test_upsert_creates_then_updates_in_place(db_session):
    created = await upsert_config(
        db_session,
        role=ProviderRole.llm,
        provider_label="openai",
        model_name="gpt-4o-mini",
        base_url=None,
        temperature=0,
        api_key_encrypted="ciphertext-1",
        update_api_key=True,
    )
    updated = await upsert_config(
        db_session,
        role=ProviderRole.llm,
        provider_label="gemini",
        model_name="gemini-2.5-flash",
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        temperature=0.3,
        api_key_encrypted=None,
        update_api_key=False,
    )

    assert created.id == updated.id  # still exactly one row for this role
    assert updated.provider_label == "gemini"
    assert updated.api_key_encrypted == "ciphertext-1"  # untouched since update_api_key=False

    fetched = await get_config_by_role(db_session, ProviderRole.llm)
    assert fetched.model_name == "gemini-2.5-flash"


@pytest.mark.asyncio
async def test_upsert_can_clear_the_key(db_session):
    await upsert_config(
        db_session,
        role=ProviderRole.embedder,
        provider_label="openai",
        model_name="text-embedding-3-small",
        base_url=None,
        temperature=None,
        api_key_encrypted="ciphertext-1",
        update_api_key=True,
    )
    cleared = await upsert_config(
        db_session,
        role=ProviderRole.embedder,
        provider_label="ollama",
        model_name="nomic-embed-text",
        base_url="http://localhost:11434/v1",
        temperature=None,
        api_key_encrypted=None,
        update_api_key=True,
    )

    assert cleared.api_key_encrypted is None


@pytest.mark.asyncio
async def test_get_config_by_role_returns_none_when_absent(db_session):
    assert await get_config_by_role(db_session, ProviderRole.llm) is None
