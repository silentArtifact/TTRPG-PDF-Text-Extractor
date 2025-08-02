"""Tests for :mod:`fabula_extractor.extractor`."""

from __future__ import annotations

import json
from pathlib import Path

from fabula_extractor.extractor import FabulaExtractor


def _root_config() -> Path:
    return Path(__file__).resolve().parent.parent / "config.yaml"


def test_extract_pdf_and_cache(tmp_path, monkeypatch):
    """Processing a PDF should create markdown and cache files."""
    monkeypatch.chdir(tmp_path)

    fixture = Path(__file__).parent / "fixtures" / "sample.pdf"
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_bytes(fixture.read_bytes())

    extractor = FabulaExtractor(str(_root_config()))

    call_count = 0

    def fake_process(_):
        nonlocal call_count
        call_count += 1
        return {
            "pages": [],
            "total_pages": 1,
            "text_blocks": 0,
            "tables": 0,
        }

    extractor.processor.process_pdf = fake_process
    result = extractor.extract_pdf(pdf_path)

    md_path = tmp_path / "output" / "markdown" / "sample.md"
    assert md_path.exists()

    cache_dir = tmp_path / "output" / "raw"
    cache_files = list(cache_dir.glob("*.json"))
    assert cache_files
    cached_content = json.loads(cache_files[0].read_text())

    assert call_count == 1  # processor called once
    assert result == cached_content

    # Replace processor to ensure cached data is used on second run
    call_count_second = 0

    def should_not_run(_):
        nonlocal call_count_second
        call_count_second += 1
        return {}

    extractor.processor.process_pdf = should_not_run
    result2 = extractor.extract_pdf(pdf_path)

    assert call_count_second == 0  # cache hit, processor not called
    assert result2 == cached_content


def test_extract_all_creates_index(tmp_path, monkeypatch):
    """``extract_all`` should generate an index file."""
    monkeypatch.chdir(tmp_path)

    fixture = Path(__file__).parent / "fixtures" / "sample.pdf"
    pdf_dir = Path("input") / "pdfs"
    pdf_dir.mkdir(parents=True)
    for name in ("a.pdf", "b.pdf"):
        (pdf_dir / name).write_bytes(fixture.read_bytes())

    extractor = FabulaExtractor(str(_root_config()))

    def fake_process(_):
        return {"total_pages": 1, "text_blocks": 1, "tables": 0}

    extractor.processor.process_pdf = fake_process
    extractor.extract_all(pdf_dir)

    index_path = Path("output") / "markdown" / "INDEX.md"
    assert index_path.exists()
    content = index_path.read_text()
    assert "a.pdf" in content and "b.pdf" in content

