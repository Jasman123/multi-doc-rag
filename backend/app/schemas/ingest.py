from pydantic import BaseModel, Field
from typing import Literal

class IngestResponse(BaseModel):
    status: Literal["success", "partial", "failed"]
    document_id: str = Field(description="Unique ID assigned to this document.")
    filename: str
    chunk_created: int = Field(description="Number of chunks embedded and stored")
    pages_processed: int
    message: str

class ingestError(BaseModel):
    status: Literal["failed"] = "failed"
    filename: str
    error: str
    detail: str | None = None

    