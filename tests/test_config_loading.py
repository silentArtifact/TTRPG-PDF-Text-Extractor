"""Tests for configuration loading in :mod:`pdf_extractor.extractor`."""

from __future__ import annotations

from io import StringIO
from pathlib import Path

import pytest
from loguru import logger

from pdf_extractor.extractor import PDFExtractor


def test_missing_config_uses_defaults(tmp_path):
    missing = tmp_path / "missing.yaml"
    sink = StringIO()
    handler_id = logger.add(sink, level="ERROR")

    extractor = PDFExtractor(str(missing))

    try:
        logger.remove(handler_id)
    except ValueError:
        pass
    output = sink.getvalue()

    assert extractor.config == {}
    assert "Config file not found" in output
    assert str(missing) in output


def test_bad_yaml_raises_value_error(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("bad: [unclosed")

    sink = StringIO()
    handler_id = logger.add(sink, level="ERROR")

    with pytest.raises(ValueError):
        PDFExtractor(str(bad))

    try:
        logger.remove(handler_id)
    except ValueError:
        pass
    output = sink.getvalue()

    assert "Invalid YAML" in output
    assert str(bad) in output
