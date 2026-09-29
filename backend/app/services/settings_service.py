from sqlalchemy.ext.asyncio import AsyncSession

from app.db.app_setting_repository import get_setting, set_setting
from app.models.app_setting import SHOW_SOURCES_KEY
from app.schemas.admin import AppSettingsResponse


async def get_show_sources(db: AsyncSession) -> bool:
    """Sources are hidden unless an admin has explicitly enabled them."""
    return await get_setting(db, SHOW_SOURCES_KEY) == "true"


async def get_app_settings(db: AsyncSession) -> AppSettingsResponse:
    return AppSettingsResponse(show_sources=await get_show_sources(db))


async def update_app_settings(db: AsyncSession, show_sources: bool) -> AppSettingsResponse:
    await set_setting(db, SHOW_SOURCES_KEY, "true" if show_sources else "false")
    return AppSettingsResponse(show_sources=show_sources)
