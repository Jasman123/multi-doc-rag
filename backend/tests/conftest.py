import os
import uuid
from collections.abc import AsyncGenerator

# Must be set before any app.* import so get_settings() doesn't fail.
os.environ.setdefault("OPENAI_API_KEY", "test-key-sk-0000")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/unused_in_tests")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")

import chromadb
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.api.dependencies import get_collection, get_current_user, get_db_session, get_embedder, get_llm
from app.core.database import Base
from app.main import create_app
from app.models.user import User, UserRole
from app.ports.embedder_port import EmbedderPort
from app.ports.llm_port import LLMPort

_EMBED_DIM = 4  # tiny fixed dimension so tests don't need a real model


class FakeLLM(LLMPort):
    """Deterministic LLM that records every call for assertion."""

    def __init__(self, answer: str = "Test answer from fake LLM.") -> None:
        self._answer = answer
        self.calls: list[list[dict]] = []

    @property
    def model_name(self) -> str:
        return "fake-model"

    async def chat(self, messages: list[dict[str, str]]) -> str:
        self.calls.append(messages)
        return self._answer


class FakeEmbedder(EmbedderPort):
    """Returns deterministic _EMBED_DIM-dimensional vectors."""

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [[float(i % _EMBED_DIM) / max(_EMBED_DIM, 1)] * _EMBED_DIM
                for i, _ in enumerate(texts)]


# ── fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def fake_llm() -> FakeLLM:
    return FakeLLM()


@pytest.fixture
def fake_embedder() -> FakeEmbedder:
    return FakeEmbedder()


@pytest.fixture
def empty_collection():
    """Fresh in-memory ChromaDB collection with no documents."""
    client = chromadb.EphemeralClient()
    return client.create_collection(f"test_empty_{uuid.uuid4().hex[:8]}")


@pytest.fixture
def populated_collection():
    """In-memory ChromaDB collection pre-loaded with one chunk."""
    chroma_client = chromadb.EphemeralClient()
    col = chroma_client.create_collection(f"test_populated_{uuid.uuid4().hex[:8]}")
    col.upsert(
        ids=["doc_abc_chunk_0"],
        embeddings=[[0.0] * _EMBED_DIM],
        documents=["The capital of France is Paris."],
        metadatas=[{
            "document_id": "doc_abc",
            "filename": "test.pdf",
            "page_number": 1,
            "chunk_index": 0,
        }],
    )
    return col


@pytest.fixture
async def db_engine() -> AsyncGenerator[AsyncEngine, None]:
    """In-memory async SQLite DB, fresh schema per test.

    StaticPool is required: without it, SQLAlchemy hands out a *new*
    aiosqlite connection (i.e. a brand-new empty `:memory:` DB) per
    checkout, so the app's requests wouldn't see the schema/rows set up
    here. StaticPool pins the engine to a single underlying connection
    for the test's lifetime, shared by test code and app code alike.
    """
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def db_session(db_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Direct session handle for service-layer unit tests (no HTTP/DI involved)."""
    sessionmaker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with sessionmaker() as session:
        yield session


@pytest.fixture
def fake_user() -> User:
    return User(
        id=uuid.uuid4(),
        email="user@example.com",
        hashed_password="unused",
        role=UserRole.user,
        is_active=True,
        token_version=0,
    )


@pytest.fixture
def fake_admin() -> User:
    return User(
        id=uuid.uuid4(),
        email="admin@example.com",
        hashed_password="unused",
        role=UserRole.admin,
        is_active=True,
        token_version=0,
    )


def override_db_session(db_engine: AsyncEngine):
    """Build a get_db_session-compatible override bound to a given engine."""
    sessionmaker = async_sessionmaker(db_engine, expire_on_commit=False)

    async def _get_db_session() -> AsyncGenerator[AsyncSession, None]:
        async with sessionmaker() as session:
            yield session

    return _get_db_session


def _build_client(llm, embedder, collection, current_user, db_engine) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_llm] = lambda: llm
    app.dependency_overrides[get_embedder] = lambda: embedder
    app.dependency_overrides[get_collection] = lambda: collection
    app.dependency_overrides[get_current_user] = lambda: current_user
    app.dependency_overrides[get_db_session] = override_db_session(db_engine)
    return TestClient(app, raise_server_exceptions=True)


@pytest.fixture
def client_empty(fake_llm, fake_embedder, empty_collection, fake_admin, db_engine) -> TestClient:
    """HTTP client wired to an empty collection, authenticated as an admin
    (admin passes both the ingest admin-only check and the query any-user check)."""
    return _build_client(fake_llm, fake_embedder, empty_collection, fake_admin, db_engine)


@pytest.fixture
def client_populated(fake_llm, fake_embedder, populated_collection, fake_admin, db_engine) -> TestClient:
    """HTTP client wired to a pre-populated collection, authenticated as an admin."""
    return _build_client(fake_llm, fake_embedder, populated_collection, fake_admin, db_engine)
