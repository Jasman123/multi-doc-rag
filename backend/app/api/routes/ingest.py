from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from openai import AsyncOpenAI
from chromadb import Collection

from app.api.dependencies import get_openai_client, get_collection
from app.services.ingestion_service import ingest_document
from app.schemas.ingest import IngestResponse
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/ingest", tags=["Ingestion"])
ALLOWED_CONTENT_TYPES = {"application/pdf"}
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024

@router.post("/", response_model=list[IngestResponse])
async def ingest_documents(files: list[UploadFile] = File(...), collection: Collection = Depends(get_collection), openai_client: AsyncOpenAI = Depends(get_openai_client),) -> list[IngestResponse]:
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    results: list[IngestResponse] = []

    for file in files:
        logger.info(f"Upload: '{file.filename}' | type='{file.content_type}'")

        if file.content_type not in ALLOWED_CONTENT_TYPES:
            raise HTTPException(status_code=415, detail=f"'{file.filename}' is not a PDF.")
        
        file_bytes = await file.read()

        if len(file_bytes) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(status_code=413, detail=f"'{file.filename}' exceed 50MB.")
        
        if len(file_bytes) == 0:
            raise HTTPException(status_code=400, detail=f"'{file.filename}' is empty")
        
        try:
            result = await ingest_document(
                file_bytes=file_bytes,
                filename=file.filename or "unknown.pdf",
                collection=collection,
                openai_client=openai_client,
            )
            results.append(result)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        except Exception as e:
            logger.exception(f"Ingestion error for '{file.filename}': {e}")
            raise HTTPException(status_code=500, detail=str(e))

    return results


@router.get("/status")
async def collection_status(collection: Collection = Depends(get_collection)) -> dict:
    count = collection.count()
    return {"status": "ready", "total_chunks": count, "has_documents": count > 0}
   