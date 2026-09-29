from collections.abc import AsyncGenerator
from uuid import UUID

import jwt
from chromadb import Collection
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.openai_compatible_embedder import OpenAICompatibleEmbedderAdapter
from app.adapters.openai_compatible_llm import OpenAICompatibleLLMAdapter
from app.core.chromadb import get_chroma_collection
from app.core.crypto import decrypt_secret
from app.core.database import get_sessionmaker
from app.core.logging import get_logger
from app.core.security import decode_token
from app.db.provider_config_repository import get_config_by_role
from app.db.user_repository import get_user_by_id
from app.models.provider_config import ProviderRole
from app.models.user import User, UserRole
from app.ports.embedder_port import EmbedderPort
from app.ports.llm_port import LLMPort

logger = get_logger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        yield session
    # NOT @lru_cache — must be a fresh session per request


async def get_llm(db: AsyncSession = Depends(get_db_session)) -> LLMPort:
    config = await get_config_by_role(db, ProviderRole.llm)
    if config is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM provider not configured. An admin must set it up at /admin.html.",
        )
    api_key = decrypt_secret(config.api_key_encrypted) if config.api_key_encrypted else None
    logger.info(f"Initializing LLM adapter ({config.provider_label})")
    return OpenAICompatibleLLMAdapter(
        api_key=api_key,
        model=config.model_name,
        base_url=config.base_url,
        temperature=config.temperature if config.temperature is not None else 0,
    )


async def get_embedder(db: AsyncSession = Depends(get_db_session)) -> EmbedderPort:
    config = await get_config_by_role(db, ProviderRole.embedder)
    if config is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Embedder provider not configured. An admin must set it up at /admin.html.",
        )
    api_key = decrypt_secret(config.api_key_encrypted) if config.api_key_encrypted else None
    logger.info(f"Initializing Embedder adapter ({config.provider_label})")
    return OpenAICompatibleEmbedderAdapter(api_key=api_key, model=config.model_name, base_url=config.base_url)


def get_collection() -> Collection:
    return get_chroma_collection()


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db_session),
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
    except jwt.InvalidTokenError:
        raise credentials_error

    if payload.get("type") != "access":
        raise credentials_error

    try:
        user_id = UUID(payload["sub"])
    except (KeyError, ValueError):
        raise credentials_error

    user = await get_user_by_id(db, user_id)
    if user is None or not user.is_active:
        raise credentials_error

    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required.",
        )
    return user
