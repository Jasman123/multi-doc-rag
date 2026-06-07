from fastapi import APIRouter, Depends, HTTPException
from openai import AsyncOpenAI
from chromadb import Collection

from app.api.dependencies import get_openai_client, get_collection
from app.services.rag_service import answer_query
from app.schemas.query import QueryRequest, QueryResponse
from app.core.logging import get_logger


logger = get_logger(__name__)
router = APIRouter(prefix="/query", tags=["Query"])

@router.post("/", response_model=QueryResponse)
async def query_documents(request: QueryRequest, collection: Collection = Depends(get_collection), openai_client: AsyncOpenAI = Depends(get_openai_client),) -> QueryResponse:
    logger.info(f"Query: '{request.question[:80]}'")

    if collection.count() == 0:
        raise HTTPException(status_code=400, detail="No documents yet. Upload PDFs via Post /ingest first.")
    
    try:
        return await answer_query(
            request=request, collection=collection, openai_client=openai_client,
        )
    except Exception as e:
        logger.exception(f" RAG pipline error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    