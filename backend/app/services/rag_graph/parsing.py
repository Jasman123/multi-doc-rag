import json
import re


def parse_json_loose(text: str) -> dict | None:
    """Best-effort JSON extraction from an LLM reply. Handles replies
    wrapped in prose or markdown fences around a single {...} object.
    Returns None (never raises) if nothing parseable is found — callers
    must have a sensible fallback, since a local/on-prem model behind
    LLMPort may not follow a JSON-only instruction as reliably as
    OpenAI's models do."""
    if not text:
        return None
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
