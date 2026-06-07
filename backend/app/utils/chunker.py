from dataclasses import dataclass, field
from app.utils.pdf_parser import ParsedPage
from app.core.config import get_settings
from app.core.logging import get_logger


logger = get_logger(__name__)


@dataclass
class TextChunk:
    chunk_id: str
    document_id: str
    filename: str
    page_number: int
    chunk_index: int
    text: str
    char_count: int = field(init=False)

    def __post_init__(self):
        self.char_count = len(self.text)


def chunk_pages(pages: list[ParsedPage], document_id: str, filename: str, chunk_size: int | None = None, chunk_overlap: int | None = None, ) -> list[TextChunk]:
    settings = get_settings()
    size = chunk_size or settings.chunk_size
    overlap = chunk_overlap or settings.chunk_overlap

    chunks: list[TextChunk] = []

    chunk_index = 0

    for page in pages:
        text = page.text.strip()

        if len(text) < 50 :
            logger.debug(f"Skipping near-empty page {page.page_number} in '{filename}'")
            continue
        start = 0
        while start < len(text):
            end = min(start + size, len(text))
            chunk_text = text[start:end].strip()

            if len(chunk_text) > 30:
                chunks.append(TextChunk(
                    chunk_id=f"{document_id}_chunk_{chunk_index}",
                    document_id=document_id,
                    filename=filename,
                    page_number=page.page_number,
                    chunk_index=chunk_index,
                    text=chunk_text,
                ))
                chunk_index += 1

            if end == len(text):
                break
            start += size - overlap

    logger.info(
        f"Chunked '{filename}' | {len(pages)} pages → {len(chunks)} chunks "
        f"| size={size} overlap={overlap}"
    )

    return chunks


