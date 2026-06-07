from functools import lru_cache
from openai import AsyncOpenAI
from chromadb import Collection


from app.core.config import get_settings
from app.core.chromadb import get_chroma_collection
from app.core.logging import get_logger

logger = get_logger(__name__)

@lru_cache
def get_openai_client() -> AsyncOpenAI:
    settings = get_settings()
    logger.info("Initializing AsyncOpenAI client")
    return AsyncOpenAI(api_key = settings.openai_api_key)

def get_collection() -> Collection:
    return get_chroma_collection()

