from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db_session, require_admin
from app.core.logging import get_logger
from app.db.user_repository import list_users
from app.models.user import User
from app.schemas.auth import(
    LoginRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserResponse,
    UserCreateRequest
)
from app.services.auth_service import (
    authenticate_user,
    issue_tokens,
    refresh_tokens,
    register_user,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(request: UserCreateRequest, db: AsyncSession = Depends(get_db_session),) -> UserResponse:
    try:
        return await register_user(db, request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db_session),) -> TokenResponse:
    try:
        user = await authenticate_user(db, request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    return issue_tokens(user)

@router.post("/refresh", response_model=TokenResponse)
async def refresh(request: RefreshTokenRequest, db: AsyncSession = Depends(get_db_session),) -> TokenResponse:
    try:
        return await refresh_tokens(db, request.refresh_token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(current_user)

@router.get("/users", response_model=list[UserResponse])
async def list_all_users(
    db: AsyncSession = Depends(get_db_session),
    _: User = Depends(require_admin),
) -> list[UserResponse]:
    """Admin-only illustrative endpoint — demonstrates the role-check dependency in practice."""
    users = await list_users(db)
    return [UserResponse.model_validate(u) for u in users]  
