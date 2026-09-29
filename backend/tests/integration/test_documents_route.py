"""Integration tests for /api/v1/documents (admin-only list / rename / delete)."""
import pytest

from app.api.dependencies import get_current_user

BASE = "/api/v1/documents"


def test_list_documents(client_two_docs):
    resp = client_two_docs.get(f"{BASE}/")
    assert resp.status_code == 200
    assert {d["document_id"] for d in resp.json()} == {"doc_aaa", "doc_bbb"}


def test_delete_document_then_status_reflects_it(client_two_docs):
    resp = client_two_docs.delete(f"{BASE}/doc_aaa")
    assert resp.status_code == 200
    assert resp.json() == {"document_id": "doc_aaa", "chunks_deleted": 3}
    status = client_two_docs.get("/api/v1/ingest/status").json()
    assert status["document_count"] == 1
    assert status["total_chunks"] == 3


def test_delete_twice_returns_404(client_two_docs):
    client_two_docs.delete(f"{BASE}/doc_aaa")
    assert client_two_docs.delete(f"{BASE}/doc_aaa").status_code == 404


def test_rename_document(client_two_docs):
    resp = client_two_docs.patch(f"{BASE}/doc_aaa", json={"filename": "  new name.pdf "})
    assert resp.status_code == 200
    assert resp.json()["filename"] == "new name.pdf"
    names = {d["document_id"]: d["filename"] for d in client_two_docs.get(f"{BASE}/").json()}
    assert names["doc_aaa"] == "new name.pdf"
    assert names["doc_bbb"] == "b.pdf"


def test_rename_unknown_document_returns_404(client_two_docs):
    assert client_two_docs.patch(f"{BASE}/doc_nope", json={"filename": "x.pdf"}).status_code == 404


@pytest.mark.parametrize("bad", ["", "   ", "a/b.pdf", "a\\b.pdf", "x" * 256])
def test_rename_invalid_name_returns_422(client_two_docs, bad):
    assert client_two_docs.patch(f"{BASE}/doc_aaa", json={"filename": bad}).status_code == 422


# ── authorization ─────────────────────────────────────────────────────────────

@pytest.mark.parametrize("method, path, body", [
    ("get", f"{BASE}/", None),
    ("patch", f"{BASE}/doc_aaa", {"filename": "x.pdf"}),
    ("delete", f"{BASE}/doc_aaa", None),
])
def test_non_admin_gets_403(client_two_docs, fake_user, method, path, body):
    client_two_docs.app.dependency_overrides[get_current_user] = lambda: fake_user
    resp = getattr(client_two_docs, method)(path, **({"json": body} if body else {}))
    assert resp.status_code == 403


def test_non_admin_delete_leaves_data_intact(client_two_docs, fake_user, two_doc_collection):
    client_two_docs.app.dependency_overrides[get_current_user] = lambda: fake_user
    client_two_docs.delete(f"{BASE}/doc_aaa")
    assert two_doc_collection.count() == 6


# ── interaction with query / ingest ──────────────────────────────────────────

def test_query_after_deleting_all_documents_returns_400(client_two_docs):
    client_two_docs.delete(f"{BASE}/doc_aaa")
    client_two_docs.delete(f"{BASE}/doc_bbb")
    resp = client_two_docs.post("/api/v1/query/", json={"question": "anything at all?"})
    assert resp.status_code == 400
    assert "No documents" in resp.json()["detail"]


def test_query_filtered_to_deleted_document_does_not_500(client_two_docs):
    client_two_docs.delete(f"{BASE}/doc_aaa")
    resp = client_two_docs.post(
        "/api/v1/query/",
        json={"question": "anything at all?", "document_ids": ["doc_aaa"]},
    )
    assert resp.status_code != 500
