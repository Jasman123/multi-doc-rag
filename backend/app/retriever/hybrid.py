from rank_bm25 import BM25Okapi
from app.core.logging import get_logger

logger = get_logger(__name__)
RRF_K = 60

def _tokenize(text: str) -> list[str]:
    return text.lower().split()


def bm25_search(query: str, corpus: list[dict], top_k: int,) -> list[dict]:
    if not corpus:
        return []

    tokenized_corpus = [_tokenize(doc["text"]) for doc in corpus]
    bm25 = BM25Okapi(tokenized_corpus)

    scores = bm25.get_scores(_tokenize(query))
    scored = sorted(zip(scores, corpus), key=lambda x: x[0], reverse=True)

    results = []
    for score, chunk in scored[:top_k]:
        results.append({**chunk, "bm25_score": float(score)})
    
    logger.debug(f"BM25 returned {len(results)} results")
    return results

def reciprocal_rank_fusion(vector_results: list[dict], bm25_results: list[dict], top_k: int,) -> list[dict]:
    rrf_scores: dict[str, float] = {}
    chunk_map: dict[str, dict] = {}

    for rank, chunk in enumerate(vector_results):
        cid = chunk["chunk_id"]
        rrf_scores[cid] = rrf_scores.get(cid, 0.0) + 1.0 / (RRF_K + rank + 1)
        chunk_map[cid] = chunk 
    
    for rank, chunk in enumerate(bm25_results):
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

    logger.debug(
        f"RRF fusion | vector: {len(vector_results)} | "
        f"bm25: {len(bm25_results)} | fused top-{top_k}: {len(fused)}"
    )
    return fused