from openai import AsyncOpenAI
from chromadb import Collection 

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from app.retriever.vector_store import vector_search
from app.retriever.hybrid import bm25_search, reciprocal_rank_fusion
from app.schemas.query import QueryRequest, QueryResponse, CitedSource
from app.core.config import get_settings
from app.core.logging import get_logger


logger = get_logger(__name__)

RAG_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are a precise document intelligence assistant.
Answer ONLY using the provided context chunks.
If the answer is not in the context, say "I cannot find this in the provided documents."
Never make up information. Be factual and concise.

Context:
{context}"""
    ),
    ("human", "{question}"),
])

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

async def answer_query(request: QueryRequest, collection: Collection, openai_client: AsyncOpenAI,) -> QueryResponse:
    settings = get_settings()
    logger.info(f"RAG query: '{request.question[:80]}'")

    vector_results = await vector_search(
        query = request.question, collection=collection, openai_client=openai_client, top_k=settings.top_k_vector, document_ids=request.document_ids or None,
    )

    total_chunks_searched = collection.count()
    bm25_results = bm25_search(
        query=request.question, corpus=vector_results, top_k=settings.top_k_bm25,
    )

    fused_chunks = reciprocal_rank_fusion(
        vector_results=vector_results, bm25_results=bm25_results, top_k=request.top_k or settings.top_k_final
    )

    if not fused_chunks:
        return QueryResponse(
            status="failed", question=request.question, answer="No documents found. Please ingest documents first.", sources=[], model_used=settings.openai_chat_model, total_chunks_searched=total_chunks_searched,
            )
    context = _build_context(fused_chunks)

    llm = ChatOpenAI(
        model=settings.openai_chat_model, temperature=0, api_key=settings.openai_api_key,
    )

    chain = (RunnablePassthrough() | RAG_PROMPT | llm | StrOutputParser())
    answer = await chain.ainvoke({
        "context": context, "question":request.question,
    })

    sources = [
        CitedSource(
        document_id=chunk["metadata"]["document_id"],
        filename=chunk["metadata"]["filename"],
        page=chunk["metadata"]["page_number"],
        snippet=chunk["text"][:300],
        relevance_score=chunk.get("rrf_score",0.0)
        )
        for chunk in fused_chunks
    ]

    logger.info(f"RAG complete | sources={len(sources)} | answer_len={len(answer)}")

    return QueryResponse(
        status="success",
        question=request.question,
        answer=answer,
        sources=sources,
        model_used=settings.openai_chat_model,
        total_chunks_searched=total_chunks_searched,
    )
