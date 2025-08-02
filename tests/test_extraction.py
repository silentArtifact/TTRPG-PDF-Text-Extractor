"""Tests for :mod:`src.extractor`."""

from __future__ import annotations

import json
from pathlib import Path

from src.extractor import FabulaExtractor


def _root_config() -> Path:
    return Path(__file__).resolve().parent.parent / "config.yaml"


def test_extract_pdf_and_cache(tmp_path, monkeypatch):
    """Processing a PDF should create markdown and cache files."""
    monkeypatch.chdir(tmp_path)

    pdf_path = Path("sample.pdf")
    pdf_path.write_bytes(b"fake pdf data")

    extractor = FabulaExtractor(str(_root_config()))
    extractor.extract_pdf(pdf_path)

    md_path = tmp_path / "output" / "markdown" / "sample.md"
    assert md_path.exists()

    cache_dir = tmp_path / "output" / "raw"
    cache_files = list(cache_dir.glob("*.json"))
    assert cache_files
    cached_content = json.loads(cache_files[0].read_text())

    # Replace processor to ensure cached data is used on second run
    call_count = 0

    def fake_process(_):
        nonlocal call_count
        call_count += 1
        return {"total_pages": 2}

    extractor.processor.process_pdf = fake_process
    result = extractor.extract_pdf(pdf_path)

    assert call_count == 0  # cache hit, processor not called
    assert result == cached_content


def test_extract_all_creates_index(tmp_path, monkeypatch):
    """``extract_all`` should generate an index file."""
    monkeypatch.chdir(tmp_path)

    pdf_dir = Path("input/pdfs")
    pdf_dir.mkdir(parents=True)
    (pdf_dir / "a.pdf").write_bytes(b"a")
    (pdf_dir / "b.pdf").write_bytes(b"b")

    extractor = FabulaExtractor(str(_root_config()))

    def fake_process(_):
        return {"total_pages": 1, "text_blocks": 1, "tables": 0}

    extractor.processor.process_pdf = fake_process
    extractor.extract_all(pdf_dir)

    index_path = Path("output/markdown/INDEX.md")
    assert index_path.exists()
    content = index_path.read_text()
    assert "a.pdf" in content and "b.pdf" in content

