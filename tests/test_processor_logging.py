from __future__ import annotations

from io import StringIO

from loguru import logger
from pdf_extractor.processor import PDFProcessor


def test_invalid_pdf_logs_error(tmp_path):
    invalid_pdf = tmp_path / "invalid.pdf"
    invalid_pdf.write_text("not a pdf")

    processor = PDFProcessor()

    sink = StringIO()
    handler_id = logger.add(sink, level="ERROR")
    processor.process_pdf(invalid_pdf)
    logger.remove(handler_id)

    output = sink.getvalue()
    assert "Error processing PDF" in output
    assert str(invalid_pdf) in output
