from functools import lru_cache
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal

class Settings(BaseSettings):
    llm_provider: Literal["openai", "gemini"] = "openai"
    embedder_provider: Literal["openai", "gemini"] = "openai"
    
    openai_api_key: str | None = None
    openai_embedding_model: str = "text-embedding-3-small"
    openai_chat_model: str = "gpt-4o-mini"

    gemini_api_key: str | None = None
    gemini_chat_model: str = "gemini-2.5-flash"
    gemini_embedding_model: str = "gemini-embedding-001"

    chroma_persist_dir: str = "./storage/chroma"
    chroma_collection_name: str = "multi_doc_rag"

    chunk_size: int = 1000
    chunk_overlap: int = 150

    top_k_vector: int = 10
    top_k_bm25: int = 10
    top_k_final: int = 8

    rag_max_retries: int = 1
    grade_skip_similarity: float = 0.55
    query_expansion_languages: list[str] = ["Indonesian"]

    app_name: str = "Multi-Doc RAG"
    app_version: str = "1.0.0"
    debug: bool = False

    database_url: str
    secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @field_validator("database_url")
    @classmethod
    def _use_asyncpg_driver(cls, v: str) -> str:
        # Managed Postgres providers (Railway, Heroku, ...) hand out
        # postgres:// / postgresql:// URLs; SQLAlchemy's async engine needs
        # the asyncpg driver spelled out.
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+asyncpg://", 1)
        if v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

@lru_cache
def get_settings() -> Settings:
    return Settings()

