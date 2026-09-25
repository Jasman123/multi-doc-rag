import re

from chromadb import Collection
from rank_bm25 import BM25Okapi

from app.core.logging import get_logger

logger = get_logger(__name__)
RRF_K = 60

_TOKEN_RE = re.compile(r"\w+", re.UNICODE)


def _tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall((text or "").lower())


def load_corpus(collection: Collection, where: dict | None = None) -> list[dict]:
    """Fetch the full collection (or a document_ids-filtered subset) as
    plain chunk dicts, so BM25 can index everything — not just whatever
    the vector search happened to return."""
    got = collection.get(where=where, include=["documents", "metadatas"])
    return [
        {"chunk_id": cid, "text": doc, "metadata": meta}
        for cid, doc, meta in zip(got["ids"], got["documents"], got["metadatas"])
        if doc
    ]


def bm25_search(query: str, corpus: list[dict], top_k: int) -> list[dict]:
    if not corpus:
        return []

    tokenized_corpus = [_tokenize(doc["text"]) for doc in corpus]
    bm25 = BM25Okapi(tokenized_corpus)

    scores = bm25.get_scores(_tokenize(query))
    scored = sorted(zip(scores, corpus), key=lambda x: x[0], reverse=True)

    results = [
        {**chunk, "bm25_score": float(score)}
        for score, chunk in scored[:top_k]
    ]

    logger.debug(f"BM25 returned {len(results)} results")
    return results


def reciprocal_rank_fusion(*ranked_lists: list[dict], top_k: int) -> list[dict]:
    rrf_scores: dict[str, float] = {}
    chunk_map: dict[str, dict] = {}

    for ranked_list in ranked_lists:
        for rank, chunk in enumerate(ranked_list):
            cid = chunk["chunk_id"]
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + 1.0 / (RRF_K + rank + 1)
            if cid not in chunk_map:
                chunk_map[cid] = chunk

    sorted_ids = sorted(rrf_scores, key=lambda x: rrf_scores[x], reverse=True)

    fused = []
    for cid in sorted_ids[:top_k]:
        chunk = chunk_map[cid].copy()
        chunk["rrf_score"] = round(rrf_scores[cid], 6)
        fused.append(chunk)

    logger.debug(f"RRF fusion | {len(ranked_lists)} lists | fused top-{top_k}: {len(fused)}")
    return fused
