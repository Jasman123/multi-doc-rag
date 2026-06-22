from functools import lru_cache

from chromadb import Collection

from app.adapters.openai_embedder import OpenAIEmbedderAdapter
from app.adapters.openai_llm import OpenAILLMAdapter
from app.core.chromadb import get_chroma_collection
from app.core.config import get_settings
from app.core.logging import get_logger
from app.ports.embedder_port import EmbedderPort
from app.ports.llm_port import LLMPort

logger = get_logger(__name__)


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
