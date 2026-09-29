from pydantic import BaseModel, Field, field_validator


class DocumentInfo(BaseModel):
    document_id: str
    filename: str
    chunk_count: int


class RenameRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=255)

    @field_validator("filename")
    @classmethod
    def _clean(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("filename must not be blank")
        if "/" in value or "\\" in value:
            raise ValueError("filename must not contain path separators")
        return value


class DeleteResponse(BaseModel):
    document_id: str
    chunks_deleted: int
