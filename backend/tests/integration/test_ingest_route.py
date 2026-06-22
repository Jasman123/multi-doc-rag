"""Integration tests for POST /api/v1/ingest/ and GET /api/v1/ingest/status."""
import fitz  # PyMuPDF
import pytest


def _make_pdf(text: str = "Hello from a test PDF document. " * 20) -> bytes:
    """Create a minimal valid PDF with extractable text using PyMuPDF."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    data = doc.tobytes()
    doc.close()
    return data


VALID_PDF = _make_pdf()


# ── health ────────────────────────────────────────────────────────────────────

def test_health_endpoint(client_empty):
    resp = client_empty.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


# ── input validation ──────────────────────────────────────────────────────────

def test_ingest_no_files_returns_422(client_empty):
    resp = client_empty.post("/api/v1/ingest/")
    assert resp.status_code == 422


def test_ingest_non_pdf_content_type_returns_415(client_empty):
    resp = client_empty.post(
        "/api/v1/ingest/",
        files=[("files", ("doc.txt", b"plain text content", "text/plain"))],
    )
    assert resp.status_code == 415


def test_ingest_empty_file_returns_400(client_empty):
    resp = client_empty.post(
        "/api/v1/ingest/",
        files=[("files", ("empty.pdf", b"", "application/pdf"))],
    )
    assert resp.status_code == 400


def test_ingest_oversized_file_returns_413(client_empty):
    huge_bytes = b"%PDF-1.4 " + b"x" * (51 * 1024 * 1024)
    resp = client_empty.post(
        "/api/v1/ingest/",
        files=[("files", ("big.pdf", huge_bytes, "application/pdf"))],
    )
    assert resp.status_code == 413


# ── successful ingestion ──────────────────────────────────────────────────────

def test_ingest_valid_pdf_returns_200(client_empty):
    resp = client_empty.post(
        "/api/v1/ingest/",
        files=[("files", ("test.pdf", VALID_PDF, "application/pdf"))],
    )
    assert resp.status_code == 200


def test_ingest_response_is_a_list(client_empty):
    resp = client_empty.post(
        "/api/v1/ingest/",
        files=[("files", ("test.pdf", VALID_PDF, "application/pdf"))],
    )
    assert isinstance(resp.json(), list)
    assert len(resp.json()) == 1


def test_ingest_response_schema(client_empty):
    resp = client_empty.post(
        "/api/v1/ingest/",
        files=[("files", ("test.pdf", VALID_PDF, "application/pdf"))],
    )
    doc = resp.json()[0]
    assert doc["filename"] == "test.pdf"
    assert doc["status"] in ("success", "partial")
    assert doc["document_id"].startswith("doc_")
    assert isinstance(doc["chunk_created"], int)
    assert isinstance(doc["pages_processed"], int)


def test_ingest_multiple_files_returns_one_result_each(client_empty):
    resp = client_empty.post(
        "/api/v1/ingest/",
        files=[
            ("files", ("a.pdf", VALID_PDF, "application/pdf")),
            ("files", ("b.pdf", VALID_PDF, "application/pdf")),
        ],
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_ingest_same_file_twice_same_document_id(client_empty):
    """Identical bytes → same SHA-256 → same document_id (idempotent)."""
    def _upload():
        return client_empty.post(
            "/api/v1/ingest/",
            files=[("files", ("same.pdf", VALID_PDF, "application/pdf"))],
        ).json()[0]["document_id"]

    assert _upload() == _upload()


# ── status endpoint ───────────────────────────────────────────────────────────

def test_status_empty_collection(client_empty):
    resp = client_empty.get("/api/v1/ingest/status")
    assert resp.status_code == 200
    body = resp.json()
    assert body["has_documents"] is False
    assert body["total_chunks"] == 0
    assert body["document_count"] == 0


def test_status_after_successful_ingest(client_empty):
    client_empty.post(
        "/api/v1/ingest/",
        files=[("files", ("test.pdf", VALID_PDF, "application/pdf"))],
    )
    resp = client_empty.get("/api/v1/ingest/status")
    assert resp.status_code == 200
    body = resp.json()
    if body["has_documents"]:
        assert body["document_count"] >= 1
        assert body["total_chunks"] >= 1
        assert any(d["filename"] == "test.pdf" for d in body["documents"])
