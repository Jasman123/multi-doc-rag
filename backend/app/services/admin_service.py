from sqlalchemy.ext.asyncio import AsyncSession

from app.core.crypto import encrypt_secret
from app.db.provider_config_repository import get_config_by_role, upsert_config
from app.models.provider_config import ProviderConfig, ProviderRole
from app.schemas.admin import ProviderConfigResponse, ProviderConfigUpdateRequest


def _to_response(config: ProviderConfig) -> ProviderConfigResponse:
    return ProviderConfigResponse(
        role=config.role.value,
        provider_label=config.provider_label,
        base_url=config.base_url,
        api_key_set=config.api_key_encrypted is not None,
        model_name=config.model_name,
        temperature=config.temperature,
        updated_at=config.updated_at,
    )


async def get_llm_config(db: AsyncSession) -> ProviderConfigResponse | None:
    config = await get_config_by_role(db, ProviderRole.llm)
    return _to_response(config) if config else None


async def get_embedder_config(db: AsyncSession) -> ProviderConfigResponse | None:
    config = await get_config_by_role(db, ProviderRole.embedder)
    return _to_response(config) if config else None


async def update_llm_config(db: AsyncSession, request: ProviderConfigUpdateRequest) -> ProviderConfigResponse:
    return await _update_config(db, ProviderRole.llm, request)


async def update_embedder_config(db: AsyncSession, request: ProviderConfigUpdateRequest) -> ProviderConfigResponse:
    return await _update_config(db, ProviderRole.embedder, request)


async def _update_config(
    db: AsyncSession, role: ProviderRole, request: ProviderConfigUpdateRequest
) -> ProviderConfigResponse:
    if request.api_key and request.clear_api_key:
        raise ValueError("Cannot both set and clear the API key in the same request.")

    update_api_key = bool(request.api_key) or request.clear_api_key
    api_key_encrypted = encrypt_secret(request.api_key) if request.api_key else None

    config = await upsert_config(
        db,
        role=role,
        provider_label=request.provider_label,
        base_url=request.base_url,
        model_name=request.model_name,
        temperature=request.temperature,
        api_key_encrypted=api_key_encrypted,
        update_api_key=update_api_key,
    )
    return _to_response(config)
