"""Tests for :mod:`pdf_extractor.processor` improvements."""

from __future__ import annotations

from pdf_extractor.processor import PDFProcessor


# ---------------------------------------------------------------------------
# Block sorting

def test_sort_blocks_by_reading_order_single_column():
    """Blocks in a single column should be sorted top to bottom."""
    processor = PDFProcessor()
    blocks = [
        {"text": "Third", "bbox": (50, 200, 150, 250), "has_indicator": False},
        {"text": "First", "bbox": (50, 10, 150, 50), "has_indicator": False},
        {"text": "Second", "bbox": (50, 100, 150, 150), "has_indicator": False},
    ]
    sorted_blocks = processor._sort_blocks_by_reading_order(blocks, 500)
    texts = [b["text"] for b in sorted_blocks]
    assert texts == ["First", "Second", "Third"]


def test_sort_blocks_by_reading_order_two_columns():
    """Multi-column layouts should read left column first, then right."""
    processor = PDFProcessor()
    blocks = [
        {"text": "Col2 Top", "bbox": (350, 10, 450, 50), "has_indicator": False},
        {"text": "Col1 Bottom", "bbox": (50, 100, 150, 150), "has_indicator": False},
        {"text": "Col1 Top", "bbox": (50, 10, 150, 50), "has_indicator": False},
        {"text": "Col2 Bottom", "bbox": (350, 100, 450, 150), "has_indicator": False},
    ]
    sorted_blocks = processor._sort_blocks_by_reading_order(blocks, 500)
    texts = [b["text"] for b in sorted_blocks]
    assert texts == ["Col1 Top", "Col1 Bottom", "Col2 Top", "Col2 Bottom"]


def test_sort_blocks_empty_list():
    """Empty block list should return empty list."""
    processor = PDFProcessor()
    assert processor._sort_blocks_by_reading_order([], 500) == []


def test_sort_blocks_disabled():
    """Sorting can be disabled via config."""
    config = {"extraction": {"sort_blocks": False}}
    processor = PDFProcessor(config)
    assert processor.sort_blocks is False


# ---------------------------------------------------------------------------
# Header/footer detection

def test_detect_headers_footers_marks_repeating_headers():
    """Repeating text in header zone should be flagged."""
    processor = PDFProcessor()
    result = {
        "pages": [
            {
                "text_blocks": [
                    {"text": "Document Title", "bbox": (50, 20, 200, 50)},
                    {"text": "Content 1", "bbox": (50, 200, 400, 400)},
                ]
            },
            {
                "text_blocks": [
                    {"text": "Document Title", "bbox": (50, 20, 200, 50)},
                    {"text": "Content 2", "bbox": (50, 200, 400, 400)},
                ]
            },
            {
                "text_blocks": [
                    {"text": "Document Title", "bbox": (50, 20, 200, 50)},
                    {"text": "Content 3", "bbox": (50, 200, 400, 400)},
                ]
            },
        ]
    }
    processor._detect_headers_footers(result, [800, 800, 800])

    for page in result["pages"]:
        for block in page["text_blocks"]:
            if block["text"] == "Document Title":
                assert block.get("is_header") is True
            else:
                assert block.get("is_header") is not True


def test_detect_headers_footers_needs_minimum_pages():
    """Detection requires at least 3 pages."""
    processor = PDFProcessor()
    result = {
        "pages": [
            {"text_blocks": [{"text": "Header", "bbox": (50, 20, 200, 50)}]},
            {"text_blocks": [{"text": "Header", "bbox": (50, 20, 200, 50)}]},
        ]
    }
    processor._detect_headers_footers(result, [800, 800])
    # Should not crash, and no flags should be set (not enough pages)
    for page in result["pages"]:
        for block in page["text_blocks"]:
            assert block.get("is_header") is None


def test_detect_headers_footers_disabled():
    """Detection can be disabled via config."""
    config = {"extraction": {"detect_headers_footers": False}}
    processor = PDFProcessor(config)
    assert processor.detect_headers_footers is False


# ---------------------------------------------------------------------------
# Text normalization for comparison

def test_normalize_for_comparison_removes_page_numbers():
    """Page numbers should be stripped for comparison."""
    processor = PDFProcessor()
    assert processor._normalize_for_comparison("42") == ""
    assert processor._normalize_for_comparison("Page 42") == ""
    assert processor._normalize_for_comparison("page 1") == ""


def test_normalize_for_comparison_preserves_content():
    """Non-page-number text should be preserved (lowercased)."""
    processor = PDFProcessor()
    assert processor._normalize_for_comparison("Document Title") == "document title"
    assert processor._normalize_for_comparison("Introduction") == "introduction"


def test_normalize_for_comparison_strips_trailing_numbers():
    """Trailing numbers (like chapter numbers) should be stripped."""
    processor = PDFProcessor()
    assert processor._normalize_for_comparison("Chapter 5") == "chapter"
