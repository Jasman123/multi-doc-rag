from chromadb import Collection

from app.core.config import get_settings
from app.core.logging import get_logger
from app.ports.embedder_port import EmbedderPort
from app.ports.llm_port import LLMPort
from app.retriever.hybrid import bm25_search, reciprocal_rank_fusion
from app.retriever.vector_store import vector_search
from app.schemas.query import CitedSource, QueryRequest, QueryResponse

logger = get_logger(__name__)

_RAG_SYSTEM_PROMPT = """\
You are a precise document intelligence assistant.
Answer ONLY using the provided context chunks.
If the answer is not in the context, say "I cannot find this in the provided documents."
Never make up information. Be factual and concise.

Context:
{context}"""


def _build_context(chunks: list[dict]) -> str:
    parts = []
    for i, chunk in enumerate(chunks, 1):
        meta = chunk.get("metadata", {})
        parts.append(
            f"[{i}] Source: {meta.get('filename', 'unknown')} | "
            f"Page {meta.get('page_number', '?')}\n"
            f"{chunk['text']}"
        )
    return "\n\n".join(parts)


async def answer_query(
    request: QueryRequest,
    collection: Collection,
    embedder: EmbedderPort,
    llm: LLMPort,
) -> QueryResponse:
    settings = get_settings()
    logger.info(f"RAG query: '{request.question[:80]}'")

    vector_results = await vector_search(
        query=request.question,
        collection=collection,
        embedder=embedder,
        top_k=settings.top_k_vector,
        document_ids=request.document_ids or None,
    )

    total_chunks_searched = collection.count()
    bm25_results = bm25_search(
        query=request.question, corpus=vector_results, top_k=settings.top_k_bm25
    )

    fused_chunks = reciprocal_rank_fusion(
        vector_results=vector_results,
        bm25_results=bm25_results,
        top_k=request.top_k or settings.top_k_final,
    )

    if not fused_chunks:
        return QueryResponse(
            status="failed",
            question=request.question,
            answer="No documents found. Please ingest documents first.",
            sources=[],
            model_used=llm.model_name,
            total_chunks_searched=total_chunks_searched,
        )

    context = _build_context(fused_chunks)
    messages = [
        {"role": "system", "content": _RAG_SYSTEM_PROMPT.format(context=context)},
        {"role": "user", "content": request.question},
    ]
    answer = await llm.chat(messages)

    sources = [
        CitedSource(
            document_id=chunk["metadata"]["document_id"],
            filename=chunk["metadata"]["filename"],
            page=chunk["metadata"]["page_number"],
            snippet=chunk["text"][:300],
            relevance_score=chunk.get("rrf_score", 0.0),
        )
        for chunk in fused_chunks
    ]

    logger.info(f"RAG complete | sources={len(sources)} | answer_len={len(answer)}")

    return QueryResponse(
        status="success",
        question=request.question,
        answer=answer,
        sources=sources,
        model_used=llm.model_name,
        total_chunks_searched=total_chunks_searched,
    )
