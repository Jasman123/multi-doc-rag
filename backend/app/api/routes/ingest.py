from chromadb import Collection
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.api.dependencies import get_collection, get_current_user, get_embedder, require_admin
from app.core.logging import get_logger
from app.models.user import User
from app.ports.embedder_port import EmbedderPort
from app.schemas.ingest import IngestResponse
from app.services.ingestion_service import ingest_document
from app.services.document_service import list_documents

logger = get_logger(__name__)

router = APIRouter(prefix="/ingest", tags=["Ingestion"])
ALLOWED_CONTENT_TYPES = {"application/pdf"}
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024


@router.post("/", response_model=list[IngestResponse])
async def ingest_documents(
    files: list[UploadFile] = File(...),
    collection: Collection = Depends(get_collection),
    embedder: EmbedderPort = Depends(get_embedder),
    current_user: User = Depends(require_admin),
) -> list[IngestResponse]:
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    results: list[IngestResponse] = []

    for file in files:
        logger.info(f"Upload: '{file.filename}' | type='{file.content_type}'")

        if file.content_type not in ALLOWED_CONTENT_TYPES:
            raise HTTPException(
                status_code=415, detail=f"'{file.filename}' is not a PDF."
            )

        file_bytes = await file.read()

        if len(file_bytes) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=413, detail=f"'{file.filename}' exceeds 50 MB."
            )

        if len(file_bytes) == 0:
            raise HTTPException(
                status_code=400, detail=f"'{file.filename}' is empty."
            )

        try:
            result = await ingest_document(
                file_bytes=file_bytes,
                filename=file.filename or "unknown.pdf",
                collection=collection,
                embedder=embedder,
            )
            results.append(result)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        except Exception as e:
            logger.exception(f"Ingestion error for '{file.filename}': {e}")
            raise HTTPException(status_code=500, detail=str(e))

    return results


@router.get("/status")
async def collection_status(
    collection: Collection = Depends(get_collection),
    _: User = Depends(get_current_user),
) -> dict:
    count = collection.count()
    doc_list = [d.model_dump() for d in list_documents(collection)]
    return {
        "status": "ready",
        "total_chunks": count,
        "document_count": len(doc_list),
        "has_documents": count > 0,
        "documents": doc_list,
    }
