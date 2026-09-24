from collections.abc import AsyncGenerator
from functools import lru_cache
from uuid import UUID

import jwt
from chromadb import Collection
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.openai_embedder import OpenAIEmbedderAdapter
from app.adapters.openai_llm import OpenAILLMAdapter
from app.core.chromadb import get_chroma_collection
from app.core.config import get_settings
from app.core.database import get_sessionmaker
from app.core.logging import get_logger
from app.core.security import decode_token
from app.db.user_repository import get_user_by_id
from app.models.user import User, UserRole
from app.ports.embedder_port import EmbedderPort
from app.ports.llm_port import LLMPort

logger = get_logger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


@lru_cache
def get_llm() -> LLMPort:
    settings = get_settings()
    logger.info("Initializing LLM adapter (OpenAI)")
    return OpenAILLMAdapter(
        api_key=settings.openai_api_key,
        model=settings.openai_chat_model,
    )


@lru_cache
def get_embedder() -> EmbedderPort:
    settings = get_settings()
    logger.info("Initializing Embedder adapter (OpenAI)")
    return OpenAIEmbedderAdapter(
        api_key=settings.openai_api_key,
        model=settings.openai_embedding_model,
    )


def get_collection() -> Collection:
    return get_chroma_collection()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        yield session
    # NOT @lru_cache — must be a fresh session per request


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
