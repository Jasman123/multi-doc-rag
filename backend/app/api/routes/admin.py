from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db_session, require_admin
from app.core.logging import get_logger
from app.models.provider_config import ProviderRole
from app.models.user import User
from app.schemas.admin import ProviderConfigResponse, ProviderConfigUpdateRequest
from app.services.admin_service import get_config, update_config

logger = get_logger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/config/{role}", response_model=ProviderConfigResponse | None)
async def get_config_route(
    role: ProviderRole,
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_admin),
) -> ProviderConfigResponse | None:
    return await get_config(db, role)


@router.put("/config/{role}", response_model=ProviderConfigResponse)
async def update_config_route(
    role: ProviderRole,
    request: ProviderConfigUpdateRequest,
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_admin),
) -> ProviderConfigResponse:
    try:
        return await update_config(db, role, request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
