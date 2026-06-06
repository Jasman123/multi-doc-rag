import fitz
from dataclasses import dataclass
from app.core.logging import get_logger


logger = get_logger(__name__)

@dataclass
class ParsedPage:
    page_number: int
    text: str
    char_count: int


def parse_pdf(file_bytes: bytes, filename: str) -> list[ParsedPage]:
    pages: list[ParsedPage] = []

    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception as e:
        raise ValueError(f"Cannot open PDF '{filename}' : {e}") from e
    
    if doc.page_count == 0:
        raise ValueError(f"PDF '{filename}' has no pages")
    
    logger.info(f"Parsing '{filename}' | {doc.page_count} pages")


    for i, page in enumerate(doc):
        text = page.get_text("text")
        text = " ".join(text.split())

        pages.append(ParsedPage(
            page_number=i+1,
            text=text,
            char_count=len(text),
        ))

    doc.close()
    total_chars = sum(p.char_count for p in pages)
    empty_pages = sum(1 for p in pages if p.char_count < 50)

    logger.info(
        f"Parsed '{filename}' | {len(pages)} pages | "
        f"{total_chars} chars | {empty_pages} near-empty pages"
    )

    if total_chars < 100:
        logger.warning(
            f"'{filename}' has very little extractable text. "
            "May be a scanned/image PDF."
        )

    return pages

