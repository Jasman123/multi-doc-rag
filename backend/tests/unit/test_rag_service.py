"""Unit tests for the RAG service (answer_query + _build_context)."""
import chromadb
import pytest

from app.schemas.query import QueryRequest
from app.services.rag_service import _build_context, answer_query

_EMBED_DIM = 4
_BASE_EMBEDDING = [0.0] * _EMBED_DIM
_BASE_METADATA = {
    "document_id": "doc1",
    "filename": "geo.pdf",
    "page_number": 1,
    "chunk_index": 0,
}


def _col_with_chunks(name: str, n: int = 1):
    col = chromadb.EphemeralClient().create_collection(name)
    for i in range(n):
        col.upsert(
            ids=[f"c{i}"],
            embeddings=[_BASE_EMBEDDING],
            documents=[f"Chunk {i}: The capital of France is Paris."],
            metadatas=[{**_BASE_METADATA, "chunk_index": i}],
        )
    return col


# ── _build_context ────────────────────────────────────────────────────────────

def test_build_context_single_chunk():
    chunks = [{
        "text": "Paris is the capital of France.",
        "metadata": {"filename": "geo.pdf", "page_number": 2},
    }]
    ctx = _build_context(chunks)
    assert "[1]" in ctx
    assert "geo.pdf" in ctx
    assert "Page 2" in ctx
    assert "Paris is the capital" in ctx


def test_build_context_multiple_chunks_numbered():
    chunks = [
        {"text": "First chunk", "metadata": {"filename": "a.pdf", "page_number": 1}},
        {"text": "Second chunk", "metadata": {"filename": "b.pdf", "page_number": 3}},
    ]
    ctx = _build_context(chunks)
    assert "[1]" in ctx
    assert "[2]" in ctx
    assert "a.pdf" in ctx
    assert "b.pdf" in ctx


def test_build_context_missing_metadata_uses_defaults():
    chunks = [{"text": "Some text", "metadata": {}}]
    ctx = _build_context(chunks)
    assert "unknown" in ctx
    assert "?" in ctx


# ── answer_query — no documents ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_answer_query_empty_collection_returns_failed(fake_llm, fake_embedder):
    col = chromadb.EphemeralClient().create_collection("empty")
    req = QueryRequest(question="What is the capital of France?")
    resp = await answer_query(request=req, collection=col,
                              embedder=fake_embedder, llm=fake_llm)
    assert resp.status == "failed"
    assert "No documents found" in resp.answer
    assert resp.sources == []


@pytest.mark.asyncio
async def test_answer_query_empty_collection_llm_not_called(fake_llm, fake_embedder):
    col = chromadb.EphemeralClient().create_collection("empty2")
    req = QueryRequest(question="What is the capital of France?")
    await answer_query(request=req, collection=col,
                       embedder=fake_embedder, llm=fake_llm)
    assert fake_llm.calls == []


# ── answer_query — with documents ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_answer_query_success_status(fake_llm, fake_embedder):
    col = _col_with_chunks("success_test")
    req = QueryRequest(question="What is the capital of France?")
    resp = await answer_query(request=req, collection=col,
                              embedder=fake_embedder, llm=fake_llm)
    assert resp.status == "success"


@pytest.mark.asyncio
async def test_answer_query_calls_llm_with_system_and_user_messages(fake_llm, fake_embedder):
    col = _col_with_chunks("llm_call_test")
    req = QueryRequest(question="Tell me about France.")
    await answer_query(request=req, collection=col,
                       embedder=fake_embedder, llm=fake_llm)
    assert len(fake_llm.calls) == 1
    roles = [m["role"] for m in fake_llm.calls[0]]
    assert "system" in roles
    assert "user" in roles


@pytest.mark.asyncio
async def test_answer_query_system_message_contains_context(fake_llm, fake_embedder):
    col = _col_with_chunks("ctx_test")
    req = QueryRequest(question="What is in the document?")
    await answer_query(request=req, collection=col,
                       embedder=fake_embedder, llm=fake_llm)
    system_msg = next(m for m in fake_llm.calls[0] if m["role"] == "system")
    assert "Paris" in system_msg["content"]


@pytest.mark.asyncio
async def test_answer_query_user_message_is_question(fake_llm, fake_embedder):
    col = _col_with_chunks("user_msg_test")
    question = "What is the capital of France?"
    req = QueryRequest(question=question)
    await answer_query(request=req, collection=col,
                       embedder=fake_embedder, llm=fake_llm)
    user_msg = next(m for m in fake_llm.calls[0] if m["role"] == "user")
    assert user_msg["content"] == question


@pytest.mark.asyncio
async def test_answer_query_answer_comes_from_llm(fake_llm, fake_embedder):
    col = _col_with_chunks("answer_test")
    req = QueryRequest(question="What is the capital?")
    resp = await answer_query(request=req, collection=col,
                              embedder=fake_embedder, llm=fake_llm)
    assert resp.answer == fake_llm._answer


@pytest.mark.asyncio
async def test_answer_query_model_used_is_llm_model_name(fake_llm, fake_embedder):
    col = _col_with_chunks("model_name_test")
    req = QueryRequest(question="Capital of France?")
    resp = await answer_query(request=req, collection=col,
                              embedder=fake_embedder, llm=fake_llm)
    assert resp.model_used == fake_llm.model_name


@pytest.mark.asyncio
async def test_answer_query_sources_populated(fake_llm, fake_embedder):
    col = _col_with_chunks("sources_test")
    req = QueryRequest(question="What does the document say?")
    resp = await answer_query(request=req, collection=col,
                              embedder=fake_embedder, llm=fake_llm)
    assert len(resp.sources) >= 1
    src = resp.sources[0]
    assert src.document_id == "doc1"
    assert src.filename == "geo.pdf"
    assert src.page == 1


@pytest.mark.asyncio
async def test_answer_query_question_echoed_in_response(fake_llm, fake_embedder):
    col = _col_with_chunks("echo_test")
    question = "Tell me something interesting."
    req = QueryRequest(question=question)
    resp = await answer_query(request=req, collection=col,
                              embedder=fake_embedder, llm=fake_llm)
    assert resp.question == question


@pytest.mark.asyncio
async def test_answer_query_document_id_filter(fake_llm, fake_embedder):
    """Filtering to a non-existent document_id yields 'failed' status."""
    col = _col_with_chunks("filter_test")
    req = QueryRequest(question="Filtered query?", document_ids=["doc_nonexistent"])
    resp = await answer_query(request=req, collection=col,
                              embedder=fake_embedder, llm=fake_llm)
    assert resp.status == "failed"
