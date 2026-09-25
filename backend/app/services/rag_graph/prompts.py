ANALYZE_PROMPT = """Rewrite this search question for retrieving passages from a document \
that may be written in a different language than the question.

Reply with ONLY a JSON object, no other text:
{{"variants": ["<original question, unchanged>", "<question translated into {target_language}, \
with 1-3 likely synonyms of the key terms added>"]}}

Question: {question}"""

REWRITE_PROMPT = """A previous search for this question did not find enough relevant content. \
Generate better search variants.

Original question: {question}
Already tried: {tried_variants}
What was missing: {missing_info}

Reply with ONLY a JSON object, no other text:
{{"variants": ["<original question, unchanged>", "<a differently-phrased or more specific \
variant, in {target_language} if that helps>"]}}"""

GRADE_PROMPT = """Given this question and these retrieved passages, judge whether the passages \
contain enough information to answer the question. Passages may be in a different language \
than the question — treat translations/synonyms as matches.

Question: {question}

Passages:
{candidates}

Reply with ONLY a JSON object, no other text:
{{"verdict": "sufficient" | "partial" | "insufficient", "missing": "<brief note on what's \
missing, empty string if sufficient>"}}"""

GENERATE_SYSTEM_PROMPT = """\
You are a precise document intelligence assistant.
Answer using ONLY the numbered context chunks below.
- The chunks may be in a different language from the question (e.g. Indonesian documents, \
English question). Treat translations and synonyms as matches (e.g. "obligations" ~ \
"kewajiban" / "tanggung jawab").
- If the context fully answers the question, answer directly.
- If it answers only partly, give what the context supports and clearly say what's missing.
- If a list or section continues across chunks, combine the items in order.
- Only if NOTHING in the context is relevant, reply exactly: \
"I cannot find this in the provided documents."
- Never add facts that are not in the context. Do not guess.
- Cite chunks inline as [1], [2] matching the chunk numbers.

Context:
{context}"""
