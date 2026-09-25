from app.core.config import Settings
from app.core.logging import get_logger
from app.ports.embedder_port import EmbedderPort
from app.ports.llm_port import LLMPort
from app.retriever.hybrid import bm25_search, load_corpus, reciprocal_rank_fusion
from app.retriever.vector_store import attach_similarity, vector_search
from app.services.rag_graph.context import build_context
from app.services.rag_graph.parsing import parse_json_loose
from app.services.rag_graph.prompts import (
    ANALYZE_PROMPT,
    GENERATE_SYSTEM_PROMPT,
    GRADE_PROMPT,
    REWRITE_PROMPT,
)
from app.services.rag_graph.state import RAGState

logger = get_logger(__name__)


class RAGNodes:
    """Node implementations for the RAG graph. Each method takes/returns a
    partial state dict — LangGraph merges the return value into state.
    Depends only on the existing LLMPort/EmbedderPort adapters and
    app.retriever functions, so swapping in an on-prem model/embedder
    needs no changes here."""

    def __init__(self, collection, embedder: EmbedderPort, llm: LLMPort, settings: Settings):
        self.collection = collection
        self.embedder = embedder
        self.llm = llm
        self.settings = settings

    async def precheck(self, state: RAGState) -> dict:
        return {"corpus_empty": self.collection.count() == 0}

    async def analyze_query(self, state: RAGState) -> dict:
        question = state["question"]
        target_language = self.settings.query_expansion_languages[0]
        prompt = ANALYZE_PROMPT.format(question=question, target_language=target_language)

        variants = [question]
        try:
            raw = await self.llm.chat([{"role": "user", "content": prompt}])
            parsed = parse_json_loose(raw)
            if parsed and isinstance(parsed.get("variants"), list):
                for v in parsed["variants"]:
                    if isinstance(v, str) and v.strip() and v.strip() not in variants:
                        variants.append(v.strip())
        except Exception as e:
            logger.warning(f"Query analysis failed, using original question only: {e}")

        return {"query_variants": variants[:3]}

    async def retrieve(self, state: RAGState) -> dict:
        settings = self.settings
        variants = state.get("query_variants") or [state["question"]]
        document_ids = state.get("document_ids")
        where = {"document_id": {"$in": document_ids}} if document_ids else None

        query_embeddings = await self.embedder.embed(variants)

        vector_lists = await vector_search(
            query_embeddings=query_embeddings,
            collection=self.collection,
            top_k=settings.top_k_vector,
            document_ids=document_ids,
        )

        corpus = load_corpus(self.collection, where=where)
        bm25_lists = [
            bm25_search(query=variant, corpus=corpus, top_k=settings.top_k_bm25)
            for variant in variants
        ]

        candidate_count = state.get("top_k", settings.top_k_final)
        fused = reciprocal_rank_fusion(*vector_lists, *bm25_lists, top_k=candidate_count)

        if fused:
            attach_similarity(fused, query_embeddings, self.collection)

        logger.info(
            f"retrieve | variants={variants} | candidates={len(fused)} | attempt={state.get('attempt', 0)}"
        )
        return {"candidates": fused}

    async def grade(self, state: RAGState) -> dict:
        candidates = state["candidates"]
        top_similarity = max((c.get("similarity", 0.0) for c in candidates), default=0.0)

        if top_similarity >= self.settings.grade_skip_similarity:
            logger.info(f"grade | skipped — top similarity {top_similarity:.2f} above threshold")
            return {"grade": "sufficient", "missing_info": ""}

        snippet_block = "\n\n".join(f"[{i}] {c['text'][:400]}" for i, c in enumerate(candidates, 1))
        prompt = GRADE_PROMPT.format(question=state["question"], candidates=snippet_block)

        verdict, missing = "sufficient", ""
        try:
            raw = await self.llm.chat([{"role": "user", "content": prompt}])
            parsed = parse_json_loose(raw)
            v = parsed.get("verdict") if parsed else None
            if v in ("sufficient", "partial", "insufficient"):
                verdict = v
                missing = parsed.get("missing", "") if parsed else ""
            else:
                raise ValueError(f"unexpected/missing verdict: {v!r}")
        except Exception as e:
            # Fail open: an ungradeable response should never block the answer.
            logger.warning(f"Grading failed, treating as sufficient: {e}")

        logger.info(f"grade | verdict={verdict} | missing={missing!r}")
        return {"grade": verdict, "missing_info": missing}

    async def rewrite_query(self, state: RAGState) -> dict:
        question = state["question"]
        tried = state.get("query_variants", [question])
        target_language = self.settings.query_expansion_languages[0]
        prompt = REWRITE_PROMPT.format(
            question=question,
            tried_variants=", ".join(tried),
            missing_info=state.get("missing_info", ""),
            target_language=target_language,
        )

        variants = [question]
        try:
            raw = await self.llm.chat([{"role": "user", "content": prompt}])
            parsed = parse_json_loose(raw)
            if parsed and isinstance(parsed.get("variants"), list):
                for v in parsed["variants"]:
                    if isinstance(v, str) and v.strip() and v.strip() not in variants:
                        variants.append(v.strip())
        except Exception as e:
            logger.warning(f"Query rewrite failed, retrying with original question only: {e}")

        return {"query_variants": variants[:3], "attempt": state.get("attempt", 0) + 1}

    async def generate(self, state: RAGState) -> dict:
        candidates = state["candidates"]
        context = build_context(candidates)
        messages = [
            {"role": "system", "content": GENERATE_SYSTEM_PROMPT.format(context=context)},
            {"role": "user", "content": state["question"]},
        ]
        answer = await self.llm.chat(messages)
        return {"answer": answer, "status": "success", "final_chunks": candidates}

    async def no_results(self, state: RAGState) -> dict:
        return {
            "answer": "No documents found. Please ingest documents first.",
            "status": "failed",
            "final_chunks": [],
        }
