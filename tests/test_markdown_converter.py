"""Tests for :mod:`fabula_extractor.markdown_converter`."""

from __future__ import annotations

from fabula_extractor.markdown_converter import MarkdownConverter


# ---------------------------------------------------------------------------
# _apply_formatting

def test_apply_formatting_strips_all_by_default():
    """Without preservation options all markers should be removed."""
    conv = MarkdownConverter()
    line = "\u2022 **bold** *italic*"
    assert conv._apply_formatting(line) == "bold italic"


def test_apply_formatting_preserves_lists():
    """Bullet characters become markdown lists when preserving lists."""
    conv = MarkdownConverter({"markdown": {"preserve_formatting": ["lists"]}})
    assert conv._apply_formatting("\u2022 item") == "- item"


def test_apply_formatting_preserves_only_bold():
    """Bold markers can be preserved independently of italics."""
    conf = {"markdown": {"preserve_formatting": ["bold"]}}
    conv = MarkdownConverter(conf)
    line = "**bold** _italic_"
    assert conv._apply_formatting(line) == "**bold** italic"


def test_apply_formatting_preserves_only_italic():
    """Italic markers can be preserved while bold is stripped."""
    conf = {"markdown": {"preserve_formatting": ["italic"]}}
    conv = MarkdownConverter(conf)
    line = "__bold__ *italic*"
    assert conv._apply_formatting(line) == "bold *italic*"


# ---------------------------------------------------------------------------
# _chunk_text

def test_chunk_text_returns_single_chunk_when_size_zero():
    conv = MarkdownConverter({"output": {"chunk_size_kb": 0}})
    text = "hello world"
    assert conv._chunk_text(text) == [text]


def test_chunk_text_splits_long_text():
    conv = MarkdownConverter({"output": {"chunk_size_kb": 1}})
    text = "a" * 1500
    chunks = conv._chunk_text(text)
    assert len(chunks) == 2
    assert chunks[0] == "a" * 1024
    assert chunks[1] == "a" * 476


def test_chunk_text_handles_multibyte_characters():
    conv = MarkdownConverter({"output": {"chunk_size_kb": 1}})
    text = "\U0001F600" * 300  # 300 grinning face emojis
    chunks = conv._chunk_text(text)
    assert len(chunks) == 2
    assert len(chunks[0]) == 256  # 256 * 4 bytes == 1024
    assert len(chunks[1]) == 44
    assert "".join(chunks) == text
