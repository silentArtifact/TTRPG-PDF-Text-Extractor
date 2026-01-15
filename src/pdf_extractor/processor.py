"""PDF processing utilities.

This module exposes a :class:`PDFProcessor` capable of extracting text
blocks and tables from PDF documents.  It uses PyMuPDF for text
extraction and ``pdfplumber`` for table detection.  The result is a
JSON-serialisable data structure compatible with
:class:`~src.markdown_converter.MarkdownConverter`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

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

        try:
            with fitz.open(pdf_path) as doc, pdfplumber.open(pdf_path) as plumber:
                result["total_pages"] = doc.page_count

                for idx in range(doc.page_count):
                    page = doc.load_page(idx)
                    plumber_page = plumber.pages[idx]
                    page_info: Dict[str, Any] = {
                        "page_number": idx + 1,
                        "text_blocks": [],
                        "tables": [],
                    }

                    # Extract text blocks using PyMuPDF
                    for block in page.get_text("blocks"):
                        text = block[4].strip()
                        if len(text) < self.min_text_length:
                            continue
                        has_indicator = any(ind in text for ind in self.block_indicators)
                        page_info["text_blocks"].append(
                            {"text": text, "has_indicator": has_indicator}
                        )

                    result["text_blocks"] += len(page_info["text_blocks"])

                    # Extract tables using pdfplumber
                    tables = plumber_page.extract_tables(
                        table_settings=self.table_settings
                    )
                    page_info["tables"] = tables
                    result["tables"] += len(tables)

                    result["pages"].append(page_info)
        except Exception as exc:
            # In case of an invalid PDF or parsing error we simply return
            # whatever has been collected so far.  The calling code can
            # handle empty results and still cache the placeholder data.
            logger.exception(f"Error processing PDF {pdf_path}: {exc}")

        return result
