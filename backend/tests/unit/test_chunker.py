"""Unit tests for the text chunking logic."""
import pytest

from app.utils.chunker import TextChunk, chunk_pages
from app.utils.pdf_parser import ParsedPage

DOC_ID = "doc_test123"
FNAME = "test.pdf"


def _page(num: int, text: str) -> ParsedPage:
    return ParsedPage(page_number=num, text=text, char_count=len(text))


# ── basic behaviour ───────────────────────────────────────────────────────────

def test_normal_page_produces_chunks():
    pages = [_page(1, "A" * 600)]
    chunks = chunk_pages(pages, DOC_ID, FNAME, chunk_size=512, chunk_overlap=64)
    assert len(chunks) >= 1
    assert all(isinstance(c, TextChunk) for c in chunks)


def test_returns_empty_list_for_no_pages():
    assert chunk_pages([], DOC_ID, FNAME) == []


def test_short_page_is_skipped():
    pages = [_page(1, "Hi")]  # < 50 chars — below the skip threshold
    assert chunk_pages(pages, DOC_ID, FNAME) == []


def test_empty_page_is_skipped():
    pages = [_page(1, "")]
    assert chunk_pages(pages, DOC_ID, FNAME) == []


# ── chunk metadata ────────────────────────────────────────────────────────────

def test_chunk_ids_are_sequential_and_unique():
    pages = [_page(1, "Word " * 200)]
    chunks = chunk_pages(pages, DOC_ID, FNAME, chunk_size=100, chunk_overlap=0)
    ids = [c.chunk_id for c in chunks]
    assert len(ids) == len(set(ids))
    for i, chunk in enumerate(chunks):
        assert chunk.chunk_id == f"{DOC_ID}_chunk_{i}"


def test_chunk_metadata_fields():
    pages = [_page(3, "Content " * 80)]
    chunks = chunk_pages(pages, DOC_ID, FNAME, chunk_size=200, chunk_overlap=0)
    for chunk in chunks:
        assert chunk.document_id == DOC_ID
        assert chunk.filename == FNAME
        assert chunk.page_number == 3


def test_char_count_matches_text_length():
    pages = [_page(1, "Hello world! " * 50)]
    chunks = chunk_pages(pages, DOC_ID, FNAME, chunk_size=100, chunk_overlap=0)
    for chunk in chunks:
        assert chunk.char_count == len(chunk.text)


# ── multi-page ────────────────────────────────────────────────────────────────

def test_multiple_pages_all_chunked():
    pages = [_page(i, "Content on this page. " * 40) for i in range(1, 4)]
    chunks = chunk_pages(pages, DOC_ID, FNAME, chunk_size=200, chunk_overlap=0)
    page_nums = {c.page_number for c in chunks}
    assert page_nums == {1, 2, 3}


def test_chunk_index_is_global_across_pages():
    pages = [_page(1, "A " * 100), _page(2, "B " * 100)]
    chunks = chunk_pages(pages, DOC_ID, FNAME, chunk_size=100, chunk_overlap=0)
    indices = [c.chunk_index for c in chunks]
    assert indices == list(range(len(chunks)))


# ── overlap ───────────────────────────────────────────────────────────────────

def test_overlap_produces_more_chunks_than_no_overlap():
    text = "Word " * 200  # ~1 000 chars
    pages = [_page(1, text)]
    no_overlap = chunk_pages(pages, DOC_ID, FNAME, chunk_size=200, chunk_overlap=0)
    with_overlap = chunk_pages(pages, DOC_ID, FNAME, chunk_size=200, chunk_overlap=100)
    assert len(with_overlap) > len(no_overlap)


def test_zero_overlap_no_repeated_content():
    text = "ABCDE " * 100
    pages = [_page(1, text)]
    chunks = chunk_pages(pages, DOC_ID, FNAME, chunk_size=100, chunk_overlap=0)
    # Concatenating chunks should not contain more chars than the original
    total_chars = sum(len(c.text) for c in chunks)
    assert total_chars <= len(text.strip())
