from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db_session, require_admin
from app.core.logging import get_logger
from app.models.user import User
from app.schemas.admin import ProviderConfigResponse, ProviderConfigUpdateRequest
from app.services.admin_service import (
    get_embedder_config,
    get_llm_config,
    update_embedder_config,
    update_llm_config,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/config/llm", response_model=ProviderConfigResponse | None)
async def get_llm_config_route(
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_admin),
) -> ProviderConfigResponse | None:
    return await get_llm_config(db)


@router.put("/config/llm", response_model=ProviderConfigResponse)
async def update_llm_config_route(
    request: ProviderConfigUpdateRequest,
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_admin),
) -> ProviderConfigResponse:
    try:
        return await update_llm_config(db, request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get("/config/embedder", response_model=ProviderConfigResponse | None)
async def get_embedder_config_route(
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_admin),
) -> ProviderConfigResponse | None:
    return await get_embedder_config(db)


@router.put("/config/embedder", response_model=ProviderConfigResponse)
async def update_embedder_config_route(
    request: ProviderConfigUpdateRequest,
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_admin),
) -> ProviderConfigResponse:
    try:
        return await update_embedder_config(db, request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
