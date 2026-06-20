from openai import AsyncOpenAI
from chromadb import Collection


from app.core.config import get_settings
from app.core.logging import get_logger
from app.utils.chunker import TextChunk


logger = get_logger(__name__)

EMBED_BATCH_SIZE = 100

async def embded_text(text: list[str], client: AsyncOpenAI) -> list[list[float]]:
    settings = get_settings()
    all_embdeddings : list[list[float]] = []

    for i in range(0, len(text), EMBED_BATCH_SIZE):
        batch = text[i:i + EMBED_BATCH_SIZE]
        logger.debug(f"Embedding batch {i// EMBED_BATCH_SIZE} | len{len(batch)} text")

        response = await client.embeddings.create(model=settings.openai_embedding_model, input=batch,)
        batch_embeddings = [item.embedding for item in response.data]
        all_embdeddings.extend(batch_embeddings)

    return all_embdeddings

async def store_chunks(chunks: list[TextChunk], collection: Collection, openai_client: AsyncOpenAI,) -> int:
    if not chunks:
        logger.warning("store_chunks called with empty chunk list")
        return 0
    
    texts = [chunk.text for chunk in chunks]
    logger.info(f"Embedding {len(texts)} chunk...")

    embeddings = await embded_text(texts, openai_client)
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

    logger.info(f"Stored {len(chunks)} chunk in ChromaDB")
    return len(chunks)

async def vector_search(query: str, collection: Collection, openai_client: AsyncOpenAI, top_k: int, document_ids: list[str] | None = None) -> list[dict]:
        query_embedding = await embded_text([query], openai_client)
        where_filter = None
        if document_ids:
             where_filter = {"document_id": {"$in": document_ids}}
        
        results = collection.query(
             query_embeddings=query_embedding,
             n_results=top_k,
             where=where_filter,
             include=["documents", "metadatas", "distances"]
        )

        output = []
        if results["ids"] and results["ids"][0]:
             for i, chunk_id in enumerate(results["ids"][0]):
                  text = results["documents"][0][i]
                  if text is None:
                       logger.warning(f"Skipping chunk {chunk_id} — null document text in ChromaDB index")
                       continue
                  output.append({
                       "chunk_id": chunk_id,
                       "text": text,
                       "metadata": results["metadatas"][0][i],
                       "score": 1 - results["distances"][0][i],
                  })
        logger.debug(f"Vector search returned {len(output)} results")
        return output
                  