from pydantic import BaseModel, Field
from typing import Literal

class QueryRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)
    document_ids = list[str] = Field(default=[], description="Filter to specific docs. Empty = search all.")
    top_k: int = Field(default=4, get=1, le=10)

class CitedSource(BaseModel):
    document_id: str
    filename: str
    page: int
    snippet: str = Field(description="Exact chunk text used as context")
    relevance_score: float = Field(description="RRF fusion score - higher = more relevance")

class QueryRequest(BaseModel):
    status: Literal["success", "failed"]
    question: str
    answer: str
    sources: list[CitedSource]
    model_used: str
    total_chunks_searched: int

class QueryError(BaseModel):
    status: Literal["failed"] = "failed"
    question: str
    error: str
    