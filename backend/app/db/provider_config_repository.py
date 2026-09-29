from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.provider_config import ProviderRole, ProviderConfig

async def get_config_by_role(db: AsyncSession, role: ProviderRole) -> ProviderConfig | None:
    result = await db.execute(select(ProviderConfig).where(ProviderConfig.role == role))
    return result.scalar_one_or_none()

async def upsert_config(db: AsyncSession,
                        *,
                        role: ProviderRole,
                        provider_label: str,
                        model_name: str,
                        base_url: str | None,
                        temperature: float | None,
                        api_key_encrypted: str | None,
                        update_api_key: bool,) -> ProviderConfig:
    config = await get_config_by_role(db, role)
    if config is None:
        config = ProviderConfig(
            role=role,
            provider_label=provider_label,
            base_url=base_url,
            model_name=model_name,
            temperature=temperature,
            api_key_encrypted=api_key_encrypted if update_api_key else None,
        )
        db.add(config)
    else:
        config.provider_label = provider_label
        config.base_url = base_url
        config.model_name = model_name
        config.temperature = temperature
        if update_api_key:
            config.api_key_encrypted = api_key_encrypted

    await db.commit()
    await db.refresh(config)
    return config