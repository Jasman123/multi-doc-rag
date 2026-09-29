from chromadb import Collection
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_collection, require_admin
from app.core.logging import get_logger
from app.models.user import User
from app.schemas.documents import DeleteResponse, DocumentInfo, RenameRequest
from app.services.document_service import (
    DocumentNotFoundError,
    delete_document,
    list_documents,
    rename_document,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.get("/", response_model=list[DocumentInfo])
async def list_documents_route(
    collection: Collection = Depends(get_collection),
    _: User = Depends(require_admin),
) -> list[DocumentInfo]:
    return list_documents(collection)


@router.patch("/{document_id}", response_model=DocumentInfo)
async def rename_document_route(
    document_id: str,
    request: RenameRequest,
    collection: Collection = Depends(get_collection),
    _: User = Depends(require_admin),
) -> DocumentInfo:
    try:
        return rename_document(collection, document_id, request.filename)
    except DocumentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{document_id}", response_model=DeleteResponse)
async def delete_document_route(
    document_id: str,
    collection: Collection = Depends(get_collection),
    _: User = Depends(require_admin),
) -> DeleteResponse:
    try:
        deleted = delete_document(collection, document_id)
    except DocumentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    logger.info(f"Deleted document '{document_id}' ({deleted} chunks)")
    return DeleteResponse(document_id=document_id, chunks_deleted=deleted)
