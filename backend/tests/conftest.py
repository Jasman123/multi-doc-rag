import os
import uuid

# Must be set before any app.* import so get_settings() doesn't fail.
os.environ.setdefault("OPENAI_API_KEY", "test-key-sk-0000")

import chromadb
import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_collection, get_embedder, get_llm
from app.main import create_app
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


def _build_client(llm, embedder, collection) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_llm] = lambda: llm
    app.dependency_overrides[get_embedder] = lambda: embedder
    app.dependency_overrides[get_collection] = lambda: collection
    return TestClient(app, raise_server_exceptions=True)


@pytest.fixture
def client_empty(fake_llm, fake_embedder, empty_collection) -> TestClient:
    """HTTP client wired to an empty collection."""
    return _build_client(fake_llm, fake_embedder, empty_collection)


@pytest.fixture
def client_populated(fake_llm, fake_embedder, populated_collection) -> TestClient:
    """HTTP client wired to a pre-populated collection."""
    return _build_client(fake_llm, fake_embedder, populated_collection)
