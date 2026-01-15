"""PDF processing utilities.

This module exposes a :class:`PDFProcessor` capable of extracting text
blocks and tables from PDF documents.  It uses PyMuPDF for text
extraction and ``pdfplumber`` for table detection.  The result is a
JSON-serialisable data structure compatible with
:class:`~src.markdown_converter.MarkdownConverter`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple

from loguru import logger

try:
    import fitz  # type: ignore
except ModuleNotFoundError:
    try:
        import pymupdf as fitz  # type: ignore
    except ModuleNotFoundError as exc:
        raise ImportError("PyMuPDF is required; install with 'pip install pymupdf'") from exc

import pdfplumber


class PDFProcessor:
    """Process PDFs into structured data."""

    def __init__(self, config: Dict | None = None) -> None:
        self.config = config or {}
        extraction = self.config.get("extraction", {})
        self.min_text_length: int = extraction.get("min_text_length", 0)
        self.table_settings: Dict[str, Any] = extraction.get("table_settings", {})
        self.block_indicators: List[str] = extraction.get(
            "block_indicators", []
        )
        self.sort_blocks: bool = extraction.get("sort_blocks", True)
        self.column_threshold: float = extraction.get("column_threshold", 0.3)
        self.detect_headers_footers: bool = extraction.get("detect_headers_footers", True)
        self.header_footer_margin: float = extraction.get("header_footer_margin", 0.1)

    # ------------------------------------------------------------------
    def _detect_headers_footers(
        self, result: Dict[str, Any], page_heights: List[float]
    ) -> None:
        """Detect and flag repeating headers and footers.

        Analyzes text blocks that appear in the top or bottom margin
        across multiple pages with similar content. Marks them with
        ``is_header`` or ``is_footer`` flags.

        Parameters
        ----------
        result:
            The extraction result dictionary to modify in place.
        page_heights:
            List of page heights for margin calculations.
        """
        if not result.get("pages") or len(result["pages"]) < 3:
            return  # Need at least 3 pages for meaningful detection

        # Collect potential headers (top margin) and footers (bottom margin)
        header_candidates: Dict[str, int] = {}
        footer_candidates: Dict[str, int] = {}

        for page_idx, page in enumerate(result["pages"]):
            page_height = page_heights[page_idx] if page_idx < len(page_heights) else 800
            header_zone = page_height * self.header_footer_margin
            footer_zone = page_height * (1 - self.header_footer_margin)

            for block in page.get("text_blocks", []):
                bbox = block.get("bbox")
                if not bbox:
                    continue

                # Normalize text for comparison (strip page numbers)
                text = block.get("text", "").strip()
                normalized = self._normalize_for_comparison(text)
                if not normalized or len(normalized) < 3:
                    continue

                # Check if in header zone
                if bbox[1] < header_zone:
                    header_candidates[normalized] = header_candidates.get(normalized, 0) + 1

                # Check if in footer zone
                if bbox[3] > footer_zone:
                    footer_candidates[normalized] = footer_candidates.get(normalized, 0) + 1

        # Identify repeating headers/footers (appear on > 50% of pages)
        threshold = len(result["pages"]) * 0.5
        repeating_headers = {k for k, v in header_candidates.items() if v >= threshold}
        repeating_footers = {k for k, v in footer_candidates.items() if v >= threshold}

        # Mark blocks
        for page_idx, page in enumerate(result["pages"]):
            page_height = page_heights[page_idx] if page_idx < len(page_heights) else 800
            header_zone = page_height * self.header_footer_margin
            footer_zone = page_height * (1 - self.header_footer_margin)

            for block in page.get("text_blocks", []):
                bbox = block.get("bbox")
                if not bbox:
                    continue

                text = block.get("text", "").strip()
                normalized = self._normalize_for_comparison(text)

                if bbox[1] < header_zone and normalized in repeating_headers:
                    block["is_header"] = True
                if bbox[3] > footer_zone and normalized in repeating_footers:
                    block["is_footer"] = True

    # ------------------------------------------------------------------
    def _normalize_for_comparison(self, text: str) -> str:
        """Normalize text for header/footer comparison.

        Removes page numbers and normalizes whitespace.
        """
        import re
        # Remove common page number patterns
        text = re.sub(r"^\d+\s*$", "", text)
        text = re.sub(r"^page\s*\d+", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\d+\s*$", "", text)
        # Normalize whitespace
        text = " ".join(text.split())
        return text.lower()

    # ------------------------------------------------------------------
    def _sort_blocks_by_reading_order(
        self, blocks: List[Dict[str, Any]], page_width: float
    ) -> List[Dict[str, Any]]:
        """Sort text blocks into natural reading order.

        Handles multi-column layouts by detecting columns based on
        horizontal position and sorting top-to-bottom within each column,
        then left-to-right across columns.

        Parameters
        ----------
        blocks:
            List of block dictionaries with 'bbox' coordinates.
        page_width:
            Width of the page for column detection.

        Returns
        -------
        List[Dict[str, Any]]
            Blocks sorted in reading order.
        """
        if not blocks:
            return blocks

        # Detect columns by clustering x-positions
        x_positions = [(b["bbox"][0] + b["bbox"][2]) / 2 for b in blocks]
        threshold = page_width * self.column_threshold

        # Group blocks into columns
        columns: List[List[Dict[str, Any]]] = []
        sorted_by_x = sorted(zip(x_positions, blocks), key=lambda x: x[0])

        current_col: List[Dict[str, Any]] = []
        current_x = None

        for x_pos, block in sorted_by_x:
            if current_x is None or abs(x_pos - current_x) < threshold:
                current_col.append(block)
                if current_x is None:
                    current_x = x_pos
                else:
                    current_x = (current_x + x_pos) / 2
            else:
                if current_col:
                    columns.append(current_col)
                current_col = [block]
                current_x = x_pos

        if current_col:
            columns.append(current_col)

        # Sort blocks within each column by vertical position (top to bottom)
        for col in columns:
            col.sort(key=lambda b: b["bbox"][1])

        # Flatten columns (left to right)
        result = []
        for col in columns:
            result.extend(col)

        return result

    # ------------------------------------------------------------------
    def process_pdf(self, pdf_path: Path) -> Dict[str, Any]:
        """Extract text blocks and tables from ``pdf_path``.

        Parameters
        ----------
        pdf_path:
            Path to the PDF file.

        Returns
        -------
        Dict[str, Any]
            Structured extraction data with per-page details and summary
            counts.
        """

        result: Dict[str, Any] = {
            "pages": [],
            "total_pages": 0,
            "text_blocks": 0,
            "tables": 0,
        }

        page_heights: List[float] = []
        try:
            with fitz.open(pdf_path) as doc, pdfplumber.open(pdf_path) as plumber:
                result["total_pages"] = doc.page_count

                for idx in range(doc.page_count):
                    page = doc.load_page(idx)
                    plumber_page = plumber.pages[idx]
                    page_width = page.rect.width
                    page_height = page.rect.height
                    page_heights.append(page_height)
                    page_info: Dict[str, Any] = {
                        "page_number": idx + 1,
                        "text_blocks": [],
                        "tables": [],
                    }

                    # Extract text blocks using PyMuPDF with position info
                    raw_blocks: List[Dict[str, Any]] = []
                    for block in page.get_text("blocks"):
                        text = block[4].strip()
                        if len(text) < self.min_text_length:
                            continue
                        has_indicator = any(ind in text for ind in self.block_indicators)
                        raw_blocks.append({
                            "text": text,
                            "has_indicator": has_indicator,
                            "bbox": (block[0], block[1], block[2], block[3]),
                        })

                    # Sort blocks by reading order if enabled
                    if self.sort_blocks:
                        raw_blocks = self._sort_blocks_by_reading_order(
                            raw_blocks, page_width
                        )

                    page_info["text_blocks"] = raw_blocks
                    result["text_blocks"] += len(raw_blocks)

                    # Extract tables using pdfplumber
                    tables = plumber_page.extract_tables(
                        table_settings=self.table_settings
                    )
                    page_info["tables"] = tables
                    result["tables"] += len(tables)

                    result["pages"].append(page_info)

                # Detect headers and footers after all pages processed
                if self.detect_headers_footers:
                    self._detect_headers_footers(result, page_heights)

        except Exception as exc:
            # In case of an invalid PDF or parsing error we simply return
            # whatever has been collected so far.  The calling code can
            # handle empty results and still cache the placeholder data.
            logger.exception(f"Error processing PDF {pdf_path}: {exc}")

        return result
