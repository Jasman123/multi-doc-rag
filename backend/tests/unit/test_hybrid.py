"""Unit tests for BM25 search and Reciprocal Rank Fusion."""
import pytest

from app.retriever.hybrid import RRF_K, bm25_search, reciprocal_rank_fusion


def _chunk(cid: str, text: str, score: float = 1.0) -> dict:
    return {"chunk_id": cid, "text": text, "metadata": {}, "score": score}


# ── bm25_search ───────────────────────────────────────────────────────────────

def test_bm25_empty_corpus_returns_empty():
    assert bm25_search("any query", [], top_k=5) == []


def test_bm25_returns_at_most_top_k():
    corpus = [_chunk(f"c{i}", f"document about topic {i}") for i in range(10)]
    results = bm25_search("topic", corpus, top_k=3)
    assert len(results) <= 3


def test_bm25_scores_are_attached():
    corpus = [_chunk("c1", "python programming"), _chunk("c2", "javascript web")]
    results = bm25_search("python", corpus, top_k=2)
    for r in results:
        assert "bm25_score" in r
        assert isinstance(r["bm25_score"], float)


def test_bm25_most_relevant_ranked_first():
    corpus = [
        _chunk("few", "apple banana cherry"),
        _chunk("many", "apple apple apple apple apple"),
        _chunk("none", "completely unrelated zebra"),
    ]
    results = bm25_search("apple", corpus, top_k=3)
    assert results[0]["chunk_id"] == "many"


def test_bm25_preserves_other_fields():
    corpus = [_chunk("c1", "hello world")]
    results = bm25_search("hello", corpus, top_k=1)
    assert results[0]["chunk_id"] == "c1"
    assert results[0]["text"] == "hello world"


def test_bm25_top_k_larger_than_corpus():
    corpus = [_chunk("c1", "text one"), _chunk("c2", "text two")]
    results = bm25_search("text", corpus, top_k=100)
    assert len(results) == 2


# ── reciprocal_rank_fusion ────────────────────────────────────────────────────

def test_rrf_both_lists_empty():
    assert reciprocal_rank_fusion([], [], top_k=4) == []


def test_rrf_only_vector_results():
    vector = [_chunk("c1", "alpha"), _chunk("c2", "beta")]
    result = reciprocal_rank_fusion(vector, [], top_k=10)
    assert len(result) == 2
    assert all("rrf_score" in r for r in result)


def test_rrf_only_bm25_results():
    bm25 = [_chunk("c1", "alpha"), _chunk("c2", "beta")]
    result = reciprocal_rank_fusion([], bm25, top_k=10)
    assert len(result) == 2


def test_rrf_deduplicates_shared_chunks():
    shared = _chunk("shared", "shared content")
    vector = [shared, _chunk("v_only", "vector only")]
    bm25 = [shared, _chunk("b_only", "bm25 only")]
    result = reciprocal_rank_fusion(vector, bm25, top_k=10)
    ids = [r["chunk_id"] for r in result]
    assert len(ids) == len(set(ids)), "Duplicate chunk_ids found"


def test_rrf_shared_chunk_scores_higher_than_single_list_chunks():
    shared = _chunk("shared", "shared doc")
    vec_only = _chunk("vec_only", "only in vector")
    bm25_only = _chunk("bm25_only", "only in bm25")
    result = reciprocal_rank_fusion(
        [shared, vec_only], [shared, bm25_only], top_k=10
    )
    scores = {r["chunk_id"]: r["rrf_score"] for r in result}
    assert scores["shared"] > scores["vec_only"]
    assert scores["shared"] > scores["bm25_only"]


def test_rrf_respects_top_k():
    vector = [_chunk(f"v{i}", f"doc {i}") for i in range(5)]
    bm25 = [_chunk(f"b{i}", f"doc {i}") for i in range(5)]
    result = reciprocal_rank_fusion(vector, bm25, top_k=3)
    assert len(result) <= 3


def test_rrf_scores_use_rrf_k_constant():
    """Score formula: 1/(RRF_K + rank + 1). First rank-0 chunk from vector only."""
    chunk = _chunk("c0", "text")
    result = reciprocal_rank_fusion([chunk], [], top_k=1)
    expected = round(1.0 / (RRF_K + 0 + 1), 6)
    assert result[0]["rrf_score"] == expected


def test_rrf_descending_score_order():
    chunks = [_chunk(f"c{i}", f"doc {i}") for i in range(5)]
    result = reciprocal_rank_fusion(chunks, [], top_k=5)
    scores = [r["rrf_score"] for r in result]
    assert scores == sorted(scores, reverse=True)
