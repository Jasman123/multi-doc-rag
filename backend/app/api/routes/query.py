from chromadb import Collection
from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_collection, get_embedder, get_llm
from app.core.logging import get_logger
from app.ports.embedder_port import EmbedderPort
from app.ports.llm_port import LLMPort
from app.schemas.query import QueryRequest, QueryResponse
from app.services.rag_service import answer_query

logger = get_logger(__name__)
router = APIRouter(prefix="/query", tags=["Query"])


@router.post("/", response_model=QueryResponse)
async def query_documents(
    request: QueryRequest,
    collection: Collection = Depends(get_collection),
    embedder: EmbedderPort = Depends(get_embedder),
    llm: LLMPort = Depends(get_llm),
) -> QueryResponse:
    logger.info(f"Query: '{request.question[:80]}'")

    if collection.count() == 0:
        raise HTTPException(
            status_code=400,
            detail="No documents yet. Upload PDFs via POST /ingest first.",
        )

    try:
        return await answer_query(
            request=request, collection=collection, embedder=embedder, llm=llm
        )
    except Exception as e:
        logger.exception(f"RAG pipeline error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
