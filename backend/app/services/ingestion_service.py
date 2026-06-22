import hashlib

from chromadb import Collection

from app.core.logging import get_logger
from app.ports.embedder_port import EmbedderPort
from app.retriever.vector_store import store_chunks
from app.schemas.ingest import IngestResponse
from app.utils.chunker import chunk_pages
from app.utils.pdf_parser import parse_pdf

logger = get_logger(__name__)


async def ingest_document(
    file_bytes: bytes,
    filename: str,
    collection: Collection,
    embedder: EmbedderPort,
) -> IngestResponse:
    document_id = f"doc_{hashlib.sha256(file_bytes).hexdigest()[:12]}"
    logger.info(f"Starting ingestion | file='{filename}' | doc_id='{document_id}'")

    pages = parse_pdf(file_bytes, filename)

    chunks = chunk_pages(pages=pages, document_id=document_id, filename=filename)
    if not chunks:
        logger.warning(f"No chunks from '{filename}' - possible scanned PDF")
        return IngestResponse(
            status="partial",
            document_id=document_id,
            filename=filename,
            chunk_created=0,
            pages_processed=len(pages),
            message="PDF parsed but no text extracted. May be a scanned PDF.",
        )

    chunks_stored = await store_chunks(
        chunks=chunks, collection=collection, embedder=embedder
    )

    logger.info(
        f"Ingestion complete | '{filename}' | "
        f"pages={len(pages)} | chunks={chunks_stored}"
    )

    return IngestResponse(
        status="success",
        document_id=document_id,
        filename=filename,
        chunk_created=chunks_stored,
        pages_processed=len(pages),
        message=f"Successfully ingested '{filename}'.",
    )
