from chromadb import Collection

from app.retriever.vector_store import delete_document_chunks, rename_document_chunks
from app.schemas.documents import DocumentInfo


class DocumentNotFoundError(Exception):
    def __init__(self, document_id: str) -> None:
        super().__init__(f"Document '{document_id}' not found.")
        self.document_id = document_id


def list_documents(collection: Collection) -> list[DocumentInfo]:
    if collection.count() == 0:
        return []
    metadatas = collection.get(include=["metadatas"])["metadatas"]
    docs: dict[str, DocumentInfo] = {}
    for meta in metadatas:
        doc_id = meta["document_id"]
        if doc_id not in docs:
            docs[doc_id] = DocumentInfo(
                document_id=doc_id, filename=meta["filename"], chunk_count=0
            )
        docs[doc_id].chunk_count += 1
    return list(docs.values())


def delete_document(collection: Collection, document_id: str) -> int:
    found = collection.get(where={"document_id": document_id}, include=["metadatas"])
    chunk_count = len(found["ids"])
    if chunk_count == 0:
        raise DocumentNotFoundError(document_id)
    delete_document_chunks(collection, document_id)
    return chunk_count


def rename_document(collection: Collection, document_id: str, filename: str) -> DocumentInfo:
    chunk_count = rename_document_chunks(collection, document_id, filename)
    if chunk_count == 0:
        raise DocumentNotFoundError(document_id)
    return DocumentInfo(document_id=document_id, filename=filename, chunk_count=chunk_count)
