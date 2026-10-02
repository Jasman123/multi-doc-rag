from pydantic import BaseModel, ConfigDict, Field
from typing import Literal

class Step(BaseModel):
    title: str
    detail: str = ""

class AnswerContent(BaseModel):
    format: Literal["paragraph", "steps"]
    text: str | None = None
    intro: str | None = None
    steps: list[Step] | None = None

class QueryRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)
    document_ids: list[str] = Field(default=[], description="Filter to specific docs. Empty = search all.")
    top_k: int = Field(default=8, ge=1, le=10)

class CitedSource(BaseModel):
    document_id: str
    filename: str
    page: int
    snippet: str = Field(description="Exact chunk text used as context")
    relevance_score: float = Field(description="Cosine similarity to the query (0-1). Not a percentage confidence score.")

class QueryResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    status: Literal["success", "failed"]
    question: str
    answer: str
    format: Literal["text", "paragraph", "steps"] = "text"
    content: AnswerContent | None = None
    sources: list[CitedSource]
    model_used: str
    total_chunks_searched: int

class QueryError(BaseModel):
    status: Literal["failed"] = "failed"
    question: str
    error: str
    