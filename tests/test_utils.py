"""Tests for :mod:`fabula_extractor.utils`."""

from __future__ import annotations

from pathlib import Path

from fabula_extractor.utils import validate_pdf


def test_validate_pdf_accepts_valid_pdf():
    """A real PDF should be accepted."""
    fixture = Path(__file__).parent / "fixtures" / "sample.pdf"
    assert validate_pdf(fixture)


def test_validate_pdf_rejects_text_file(tmp_path):
    """Files without a PDF extension should be rejected."""
    txt_file = tmp_path / "file.txt"
    txt_file.write_text("just some text")
    assert not validate_pdf(txt_file)


def test_validate_pdf_rejects_invalid_header(tmp_path):
    """A ``.pdf`` file without the ``%PDF`` header should be rejected."""
    fake_pdf = tmp_path / "fake.pdf"
    fake_pdf.write_text("not really a pdf")
    assert not validate_pdf(fake_pdf)
