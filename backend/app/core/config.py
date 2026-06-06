from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    openai_api_key: str 
    openai_embedding_model: str = "text-embedding-3-small"
    openai_chat_model: str = "gpt-4o-mini"

    chroma_persist_dir: str = "./storage/chroma"
    chroma_collection_name: str = "multi_doc_rag"

    chunk_size: int = 512
    chunk_overlap: int = 64

    top_k_vextor: int =5
    top_k_bm25: int = 5
    top_k_final: int = 4

    app_name: str = "Multi-Doc RAG"
    app_version: str = "1.0.0"
    debug: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

@lru_cache
def get_settings() -> Settings:
    return Settings

