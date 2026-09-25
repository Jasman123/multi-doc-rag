from chromadb import Collection

from app.core.config import get_settings
from app.core.logging import get_logger
from app.ports.embedder_port import EmbedderPort
from app.ports.llm_port import LLMPort
from app.schemas.query import CitedSource, QueryRequest, QueryResponse
from app.services.rag_graph.context import build_context as _build_context  # noqa: F401 (re-exported for existing tests)
from app.services.rag_graph.graph import build_rag_graph
from app.services.rag_graph.nodes import RAGNodes

logger = get_logger(__name__)


async def answer_query(
    request: QueryRequest,
    collection: Collection,
    embedder: EmbedderPort,
    llm: LLMPort,
) -> QueryResponse:
    settings = get_settings()
    logger.info(f"RAG query: '{request.question[:80]}'")

    nodes = RAGNodes(collection=collection, embedder=embedder, llm=llm, settings=settings)
    graph = build_rag_graph(nodes, max_retries=settings.rag_max_retries)

    initial_state = {
        "question": request.question,
        "document_ids": request.document_ids or None,
        "top_k": request.top_k or settings.top_k_final,
        "attempt": 0,
    }
    final_state = await graph.ainvoke(initial_state, config={"recursion_limit": 12})

    if final_state["status"] == "failed":
        return QueryResponse(
            status="failed",
            question=request.question,
            answer=final_state["answer"],
            sources=[],
            model_used=llm.model_name,
            total_chunks_searched=collection.count(),
        )

    sources = [
        CitedSource(
            document_id=chunk["metadata"]["document_id"],
            filename=chunk["metadata"]["filename"],
            page=chunk["metadata"]["page_number"],
            snippet=chunk["text"][:300],
            relevance_score=chunk.get("similarity", 0.0),
        )
        for chunk in final_state["final_chunks"]
    ]

    logger.info(f"RAG complete | sources={len(sources)} | answer_len={len(final_state['answer'])}")

    return QueryResponse(
        status="success",
        question=request.question,
        answer=final_state["answer"],
        sources=sources,
        model_used=llm.model_name,
        total_chunks_searched=collection.count(),
    )
