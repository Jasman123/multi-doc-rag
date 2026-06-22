from chromadb import Collection

from app.core.logging import get_logger
from app.ports.embedder_port import EmbedderPort
from app.utils.chunker import TextChunk

logger = get_logger(__name__)


async def store_chunks(
    chunks: list[TextChunk],
    collection: Collection,
    embedder: EmbedderPort,
) -> int:
    if not chunks:
        logger.warning("store_chunks called with empty chunk list")
        return 0

    texts = [chunk.text for chunk in chunks]
    logger.info(f"Embedding {len(texts)} chunks...")

    embeddings = await embedder.embed(texts)

    ids = [chunk.chunk_id for chunk in chunks]
    metadatas = [
        {
            "document_id": chunk.document_id,
            "filename": chunk.filename,
            "page_number": chunk.page_number,
            "chunk_index": chunk.chunk_index,
        }
        for chunk in chunks
    ]

    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
    )

    logger.info(f"Stored {len(chunks)} chunks in ChromaDB")
    return len(chunks)


async def vector_search(
    query: str,
    collection: Collection,
    embedder: EmbedderPort,
    top_k: int,
    document_ids: list[str] | None = None,
) -> list[dict]:
    query_embedding = await embedder.embed([query])

    where_filter = None
    if document_ids:
        where_filter = {"document_id": {"$in": document_ids}}

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k,
        where=where_filter,
        include=["documents", "metadatas", "distances"],
    )

    output = []
    if results["ids"] and results["ids"][0]:
        for i, chunk_id in enumerate(results["ids"][0]):
            text = results["documents"][0][i]
            if text is None:
                logger.warning(
                    f"Skipping chunk {chunk_id} — null document text in ChromaDB"
                )
                continue
            output.append(
                {
                    "chunk_id": chunk_id,
                    "text": text,
                    "metadata": results["metadatas"][0][i],
                    "score": 1 - results["distances"][0][i],
                }
            )

    logger.debug(f"Vector search returned {len(output)} results")
    return output
