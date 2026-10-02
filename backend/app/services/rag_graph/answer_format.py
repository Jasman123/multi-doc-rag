from app.schemas.query import AnswerContent, Step
from app.services.rag_graph.parsing import parse_json_loose


def _build_content(parsed: dict) -> AnswerContent | None:
    fmt = parsed.get("format")

    if fmt == "paragraph":
        text = parsed.get("text")
        if isinstance(text, str) and text.strip():
            return AnswerContent(format="paragraph", text=text.strip())

    if fmt == "steps" and isinstance(parsed.get("steps"), list):
        steps = [
            Step(title=s["title"].strip(), detail=str(s.get("detail") or "").strip())
            for s in parsed["steps"]
            if isinstance(s, dict) and isinstance(s.get("title"), str) and s["title"].strip()
        ]
        if steps:
            intro = parsed.get("intro")
            return AnswerContent(
                format="steps",
                intro=intro.strip() if isinstance(intro, str) and intro.strip() else None,
                steps=steps,
            )

    return None  # unknown format / empty content -> caller falls back to raw text


def flatten(content: AnswerContent) -> str:
    """Plain-text rendition kept in QueryResponse.answer for older clients."""
    if content.format == "paragraph":
        return content.text or ""
    lines = [content.intro] if content.intro else []
    for i, step in enumerate(content.steps or [], 1):
        lines.append(f"{i}. {step.title}: {step.detail}" if step.detail else f"{i}. {step.title}")
    return "\n".join(lines)


def parse_structured_answer(raw: str) -> tuple[str, AnswerContent | None, str]:
    """Returns (format, content, plain_answer). Never raises: anything unparseable
    falls back to ("text", None, raw) — a local model may ignore the JSON-only rule."""
    parsed = parse_json_loose(raw)
    content = _build_content(parsed) if isinstance(parsed, dict) else None
    if content is None:
        return "text", None, raw
    return content.format, content, flatten(content)
