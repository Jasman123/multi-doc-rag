import chromadb
from chromadb import Collection
from chromadb.config import Settings as ChromaSettings

from app.core.config import get_settings
from app.core.logging import get_logger


logger = get_logger(__name__)


_client: chromadb.PersistentClient | None = None


def get_chroma_client() -> chromadb.PersistentClient:
    global _client

    if _client is None:
        settings = get_settings()
        logger.info(f"Initiating Chroma client at: {settings.chroma_persist_dir}")
        _client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        logger.info("Chroma client initialized")
    
    return _client

def get_chroma_collection()  -> Collection:
    settings = get_settings()
    client = get_chroma_client()

    collection = client.get_or_create_collection(
        name=settings.chroma_collection_name, metadata={"hnsw:space": "cosine"},
    )

    logger.info(
        f"Using collection: '{settings.chroma_collection_name}' "
        f"| docs: {collection.count()}"
    )
    return collection




