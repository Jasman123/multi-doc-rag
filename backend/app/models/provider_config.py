import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

class ProviderRole(str, enum.Enum):
    llm = "llm"
    embedder = "embedder"

class ProviderConfig(Base):
    __tablename__ = "provider_configs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role: Mapped[ProviderRole] = mapped_column(Enum(ProviderRole, native_enum=False, validate_strings=True), unique=True, nullable=False)
    provider_label: Mapped[str] = mapped_column(nullable=False)
    base_url: Mapped[str | None] = mapped_column(nullable=True)
    api_key_encrypted: Mapped[str | None] = mapped_column(nullable=True)
    model_name: Mapped[str] = mapped_column(nullable=False)
    temperature: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
     