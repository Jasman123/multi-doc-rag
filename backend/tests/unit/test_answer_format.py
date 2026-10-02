"""Unit tests for structured answer parsing (paragraph / steps / text fallback)."""
import json

from app.services.rag_graph.answer_format import parse_structured_answer


def test_paragraph():
    fmt, content, plain = parse_structured_answer(json.dumps({"format": "paragraph", "text": "Hello [1]"}))
    assert fmt == "paragraph"
    assert content.text == "Hello [1]"
    assert plain == "Hello [1]"


def test_steps_flattened():
    raw = json.dumps({
        "format": "steps",
        "intro": "Alur:",
        "steps": [{"title": "Surface Treatment", "detail": "Cleaning [2]"}, {"title": "Core Test"}],
    })
    fmt, content, plain = parse_structured_answer(raw)
    assert fmt == "steps"
    assert len(content.steps) == 2
    assert content.intro == "Alur:"
    assert plain == "Alur:\n1. Surface Treatment: Cleaning [2]\n2. Core Test"


def test_steps_skips_invalid_items():
    raw = json.dumps({"format": "steps", "steps": [{"title": " "}, "junk", {"title": "Keep", "detail": None}]})
    fmt, content, _ = parse_structured_answer(raw)
    assert fmt == "steps"
    assert [s.title for s in content.steps] == ["Keep"]
    assert content.steps[0].detail == ""


def test_json_in_code_fence():
    fmt, _, _ = parse_structured_answer('```json\n{"format": "paragraph", "text": "ok"}\n```')
    assert fmt == "paragraph"


def test_fallbacks_return_raw_text():
    for raw in [
        "just prose",
        "",
        '{"format": "table"}',
        '{"format": "steps", "steps": []}',
        '{"format": "paragraph", "text": " "}',
        '{"format": "paragraph", "text": 5}',
    ]:
        assert parse_structured_answer(raw) == ("text", None, raw)
