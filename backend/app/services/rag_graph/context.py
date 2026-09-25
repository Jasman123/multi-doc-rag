def build_context(chunks: list[dict]) -> str:
    parts = []
    for i, chunk in enumerate(chunks, 1):
        meta = chunk.get("metadata", {})
        parts.append(
            f"[{i}] Source: {meta.get('filename', 'unknown')} | "
            f"Page {meta.get('page_number', '?')}\n"
            f"{chunk['text']}"
        )
    return "\n\n".join(parts)
