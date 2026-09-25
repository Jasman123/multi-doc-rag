import numpy as np
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

def delete_document_chunks(collection: Collection, document_id: str) -> None:
    collection.delete(where={"document_id":document_id})


async def vector_search(
    query_embeddings: list[list[float]],
    collection: Collection,
    top_k: int,
    document_ids: list[str] | None = None,
) -> list[list[dict]]:
    if not query_embeddings:
        return []
    
    where_filter = {"document_id": {"$in": document_ids}} if document_ids else None


    results = collection.query(
        query_embeddings=query_embeddings,
        n_results=top_k,
        where=where_filter,
        include=["documents", "metadatas", "distances"],
    )

    all_lists: list[list[dict]] = []
    for q, chunk_ids in enumerate(results["ids"] or []):
        output = []
        for i, chunk_id in enumerate(chunk_ids):
            text = results["documents"][q][i]
            if text is None:
                logger.warning(f"Skipping chunk {chunk_id} — null document text in ChromaDB")
                continue
            output.append({
                "chunk_id": chunk_id,
                "text": text,
                "metadata": results["metadatas"][q][i],
                "score": 1 - results["distances"][q][i],
            })
        all_lists.append(output)

    logger.debug(f"Vector search returned {[len(o) for o in all_lists]} results for {len(query_embeddings)} variant(s)")
    return all_lists

def attach_similarity(chunks: list[dict], query_embeddings: list[list[float]], collection: Collection) -> None:
    ids = [c["chunk_id"] for c in chunks]
    got = collection.get(ids=ids, include=["embeddings"])
    emb_by_id = dict(zip(got["ids"], got["embeddings"]))

    q = np.asarray(query_embeddings, dtype=float)
    q_norms = np.linalg.norm(q, axis=1)

    for chunk in chunks:
        emb = emb_by_id.get(chunk["chunk_id"])
        if emb is None:
            chunk["similarity"] = 0.0
            continue
        e = np.asarray(emb, dtype=float)
        e_norm = np.linalg.norm(e)
        valid = (q_norms > 0) & (e_norm > 0)
        if not valid.any():
            chunk["similarity"] = 0.0
            continue
        sims = (q[valid] @ e) / (q_norms[valid] * e_norm)
        chunk["similarity"] = float(np.clip(sims.max(), 0.0, 1.0))
