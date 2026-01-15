"""Tests for :mod:`pdf_extractor.utils`."""

from __future__ import annotations

import hashlib
from pathlib import Path

from pdf_extractor.utils import (
    get_file_hash,
    load_cache,
    save_cache,
    validate_pdf,
)


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


def test_validate_pdf_handles_missing_file(tmp_path):
    """Non-existent files should return ``False``."""
    missing = tmp_path / "missing.pdf"
    assert not validate_pdf(missing)


def test_get_file_hash_matches_hashlib(tmp_path):
    """``get_file_hash`` should return the SHA256 digest of a file."""
    data_file = tmp_path / "data.bin"
    data = b"hello world"
    data_file.write_bytes(data)
    expected = hashlib.sha256(data).hexdigest()
    assert get_file_hash(data_file) == expected


def test_save_and_load_cache_roundtrip(tmp_path):
    """Data saved with ``save_cache`` should load back the same."""
    cache_path = tmp_path / "cache.json"
    payload = {"a": 1, "b": "two"}
    save_cache(cache_path, payload)
    assert load_cache(cache_path) == payload
