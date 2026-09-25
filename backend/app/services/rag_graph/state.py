from typing import Literal, TypedDict


class RAGState(TypedDict, total=False):
    # set by the caller (rag_service.answer_query)
    question: str
    document_ids: list[str] | None
    top_k: int

    # set by precheck
    corpus_empty: bool

    # set by analyze_query / rewrite_query
    query_variants: list[str]

    # set by retrieve — fused, similarity-scored chunks from the latest attempt
    candidates: list[dict]

    # set by grade
    grade: Literal["sufficient", "partial", "insufficient"]
    missing_info: str

    # loop control
    attempt: int

    # set by generate / no_results
    answer: str
    status: Literal["success", "failed"]
    final_chunks: list[dict]
