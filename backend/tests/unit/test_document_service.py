import pytest

from app.services.document_service import (
    DocumentNotFoundError,
    delete_document,
    list_documents,
    rename_document,
)


def test_list_documents_groups_by_document(two_doc_collection):
    docs = {d.document_id: d for d in list_documents(two_doc_collection)}
    assert set(docs) == {"doc_aaa", "doc_bbb"}
    assert docs["doc_aaa"].chunk_count == 3


def test_list_documents_empty(empty_collection):
    assert list_documents(empty_collection) == []


def test_delete_document_removes_only_target(two_doc_collection):
    assert delete_document(two_doc_collection, "doc_aaa") == 3
    remaining = {d.document_id for d in list_documents(two_doc_collection)}
    assert remaining == {"doc_bbb"}
    assert two_doc_collection.count() == 3


def test_delete_unknown_document_raises(two_doc_collection):
    with pytest.raises(DocumentNotFoundError):
        delete_document(two_doc_collection, "doc_nope")
    assert two_doc_collection.count() == 6  # nothing touched


def test_rename_updates_all_chunks_and_keeps_other_metadata(two_doc_collection):
    info = rename_document(two_doc_collection, "doc_aaa", "renamed.pdf")
    assert info.chunk_count == 3
    got = two_doc_collection.get(where={"document_id": "doc_aaa"}, include=["metadatas"])
    assert {m["filename"] for m in got["metadatas"]} == {"renamed.pdf"}
    assert sorted(m["chunk_index"] for m in got["metadatas"]) == [0, 1, 2]
    other = two_doc_collection.get(where={"document_id": "doc_bbb"}, include=["metadatas"])
    assert {m["filename"] for m in other["metadatas"]} == {"b.pdf"}


def test_rename_unknown_document_raises(two_doc_collection):
    with pytest.raises(DocumentNotFoundError):
        rename_document(two_doc_collection, "doc_nope", "x.pdf")
