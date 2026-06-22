"""Integration tests for POST /api/v1/query/."""
import pytest


# ── guard: empty collection ───────────────────────────────────────────────────

def test_query_empty_collection_returns_400(client_empty):
    resp = client_empty.post(
        "/api/v1/query/",
        json={"question": "What is this about?"},
    )
    assert resp.status_code == 400
    assert "No documents" in resp.json()["detail"]


# ── input validation ──────────────────────────────────────────────────────────

def test_query_question_below_min_length_returns_422(client_populated):
    resp = client_populated.post(
        "/api/v1/query/",
        json={"question": "Hi"},  # min_length = 3
    )
    assert resp.status_code == 422


def test_query_question_at_min_length_passes(client_populated):
    resp = client_populated.post(
        "/api/v1/query/",
        json={"question": "Hi?"},  # exactly 3 chars
    )
    assert resp.status_code == 200


def test_query_question_above_max_length_returns_422(client_populated):
    resp = client_populated.post(
        "/api/v1/query/",
        json={"question": "x" * 1001},  # max_length = 1000
    )
    assert resp.status_code == 422


def test_query_missing_question_field_returns_422(client_populated):
    resp = client_populated.post("/api/v1/query/", json={})
    assert resp.status_code == 422


def test_query_top_k_below_minimum_returns_422(client_populated):
    resp = client_populated.post(
        "/api/v1/query/",
        json={"question": "What is France?", "top_k": 0},  # ge=1
    )
    assert resp.status_code == 422


def test_query_top_k_above_maximum_returns_422(client_populated):
    resp = client_populated.post(
        "/api/v1/query/",
        json={"question": "What is France?", "top_k": 11},  # le=10
    )
    assert resp.status_code == 422


# ── successful query ──────────────────────────────────────────────────────────

def test_query_valid_returns_200(client_populated):
    resp = client_populated.post(
        "/api/v1/query/",
        json={"question": "What is the capital of France?"},
    )
    assert resp.status_code == 200


def test_query_response_schema(client_populated):
    resp = client_populated.post(
        "/api/v1/query/",
        json={"question": "Tell me about the documents."},
    )
    assert resp.status_code == 200
    body = resp.json()
    for field in ("status", "question", "answer", "sources",
                  "model_used", "total_chunks_searched"):
        assert field in body, f"Missing field: {field}"


def test_query_status_is_success(client_populated):
    resp = client_populated.post(
        "/api/v1/query/",
        json={"question": "What does the document contain?"},
    )
    assert resp.json()["status"] == "success"


def test_query_answer_is_nonempty_string(client_populated):
    resp = client_populated.post(
        "/api/v1/query/",
        json={"question": "Tell me about France."},
    )
    answer = resp.json()["answer"]
    assert isinstance(answer, str) and len(answer) > 0


def test_query_model_used_matches_fake_model(client_populated):
    resp = client_populated.post(
        "/api/v1/query/",
        json={"question": "What is the capital?"},
    )
    assert resp.json()["model_used"] == "fake-model"


def test_query_question_echoed_in_response(client_populated):
    question = "What is the capital of France?"
    resp = client_populated.post("/api/v1/query/", json={"question": question})
    assert resp.json()["question"] == question


def test_query_sources_have_required_fields(client_populated):
    resp = client_populated.post(
        "/api/v1/query/",
        json={"question": "Tell me about the content."},
    )
    for source in resp.json()["sources"]:
        for field in ("document_id", "filename", "page", "snippet", "relevance_score"):
            assert field in source, f"Source missing field: {field}"


def test_query_sources_snippet_is_truncated(client_populated):
    resp = client_populated.post(
        "/api/v1/query/",
        json={"question": "Tell me about the content."},
    )
    for source in resp.json()["sources"]:
        assert len(source["snippet"]) <= 300


def test_query_total_chunks_searched_is_int(client_populated):
    resp = client_populated.post(
        "/api/v1/query/",
        json={"question": "Any question here."},
    )
    assert isinstance(resp.json()["total_chunks_searched"], int)


# ── document_id filter ────────────────────────────────────────────────────────

def test_query_with_nonexistent_document_filter_returns_failed(client_populated):
    resp = client_populated.post(
        "/api/v1/query/",
        json={"question": "What is France?", "document_ids": ["doc_nonexistent"]},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "failed"


def test_query_with_matching_document_filter_returns_success(client_populated):
    resp = client_populated.post(
        "/api/v1/query/",
        json={"question": "What is France?", "document_ids": ["doc_abc"]},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"
