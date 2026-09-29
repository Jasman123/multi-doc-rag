from sqlalchemy.ext.asyncio import AsyncSession

from app.models.app_setting import AppSetting


async def get_setting(db: AsyncSession, key: str) -> str | None:
    setting = await db.get(AppSetting, key)
    return setting.value if setting else None


async def set_setting(db: AsyncSession, key: str, value: str) -> None:
    setting = await db.get(AppSetting, key)
    if setting is None:
        db.add(AppSetting(key=key, value=value))
    else:
        setting.value = value
    await db.commit()
