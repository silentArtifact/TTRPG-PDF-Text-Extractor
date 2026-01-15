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
    # Use WARNING level since _load_config logs with logger.warning()
    handler_id = logger.add(sink, level="WARNING")

    extractor = PDFExtractor(str(missing))

    try:
        logger.remove(handler_id)
    except ValueError:
        pass
    output = sink.getvalue()

    assert extractor.config == {}
    assert "Config file not found" in output
    assert str(missing) in output


def test_bad_yaml_exits_with_error(tmp_path, capsys):
    """Invalid YAML config should exit with user-friendly error message."""
    bad = tmp_path / "bad.yaml"
    bad.write_text("bad: [unclosed")

    # friendly_exit calls sys.exit(1), so we expect SystemExit
    with pytest.raises(SystemExit) as exc_info:
        PDFExtractor(str(bad))

    assert exc_info.value.code == 1

    # Check that a user-friendly error was printed to stderr
    captured = capsys.readouterr()
    assert "formatting issue" in captured.err or "config" in captured.err.lower()
