"""Tests for :mod:`pdf_extractor.markdown_converter`."""

from __future__ import annotations

from pdf_extractor.markdown_converter import MarkdownConverter


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
    """Chunking splits at paragraph boundaries when possible."""
    conv = MarkdownConverter({"output": {"chunk_size_kb": 1}})
    # Create text with paragraphs that will require splitting
    para1 = "a" * 600
    para2 = "b" * 600
    text = para1 + "\n\n" + para2
    chunks = conv._chunk_text(text)
    assert len(chunks) == 2
    assert para1 in chunks[0]
    assert para2 in chunks[1]


def test_chunk_text_handles_multibyte_characters():
    """Chunking handles multibyte characters correctly."""
    conv = MarkdownConverter({"output": {"chunk_size_kb": 1}})
    # Create paragraphs with emojis
    para1 = "\U0001F600" * 150  # 600 bytes
    para2 = "\U0001F600" * 150  # 600 bytes
    text = para1 + "\n\n" + para2
    chunks = conv._chunk_text(text)
    assert len(chunks) == 2
    assert "".join(chunks) == text


# ---------------------------------------------------------------------------
# Text normalization

def test_normalize_text_expands_ligatures():
    """Ligatures should be expanded to their component characters."""
    conv = MarkdownConverter()
    text = "The \ufb01le contains \ufb02owers"  # fi and fl ligatures
    result = conv._normalize_text(text)
    assert "file" in result
    assert "flowers" in result


def test_normalize_text_converts_smart_quotes():
    """Smart quotes should be converted to straight quotes."""
    conv = MarkdownConverter()
    text = "\u201cHello\u201d said \u2018John\u2019"
    result = conv._normalize_text(text)
    assert '"Hello"' in result
    assert "'John'" in result


def test_normalize_text_disabled():
    """Normalization can be disabled via config."""
    conf = {"markdown": {"text_cleaning": {"normalize_unicode": False}}}
    conv = MarkdownConverter(conf)
    text = "\ufb01le"  # fi ligature
    result = conv._normalize_text(text)
    assert result == text  # unchanged


# ---------------------------------------------------------------------------
# Dehyphenation

def test_dehyphenate_text_rejoins_split_words():
    """Hyphenated line breaks should be rejoined."""
    conv = MarkdownConverter()
    text = "docu-\nment"
    result = conv._dehyphenate_text(text)
    assert result == "document"


def test_dehyphenate_preserves_intentional_hyphens():
    """Intentional hyphens not at line breaks should be preserved."""
    conv = MarkdownConverter()
    text = "self-aware person"
    result = conv._dehyphenate_text(text)
    assert result == "self-aware person"


# ---------------------------------------------------------------------------
# Whitespace normalization

def test_normalize_whitespace_collapses_multiple_spaces():
    """Multiple spaces should be collapsed to single space."""
    conv = MarkdownConverter()
    text = "hello    world"
    result = conv._normalize_whitespace(text)
    assert "    " not in result
    assert "hello world" in result


def test_normalize_whitespace_limits_newlines():
    """More than 2 consecutive newlines should be reduced to 2."""
    conv = MarkdownConverter()
    text = "para1\n\n\n\npara2"
    result = conv._normalize_whitespace(text)
    assert "\n\n\n" not in result
    assert "para1\n\npara2" in result


# ---------------------------------------------------------------------------
# Table rendering

def test_render_table_creates_markdown_table():
    """Tables should be rendered in markdown format."""
    conv = MarkdownConverter()
    table = [
        ["Name", "Age"],
        ["Alice", "30"],
    ]
    result = conv._render_table(table)
    assert "| Name" in result
    assert "| Alice" in result
    assert "---" in result


def test_render_table_handles_empty_cells():
    """Empty cells should be handled gracefully."""
    conv = MarkdownConverter()
    table = [
        ["A", None, "C"],
        ["1", "2", None],
    ]
    result = conv._render_table(table)
    assert result  # Should not crash


def test_render_table_escapes_pipes():
    """Pipe characters in cells should be escaped."""
    conv = MarkdownConverter()
    table = [
        ["A|B", "C"],
        ["1", "2"],
    ]
    result = conv._render_table(table)
    assert "\\|" in result


# ---------------------------------------------------------------------------
# Header/footer filtering

def test_convert_skips_headers_when_configured():
    """Blocks marked as headers should be skipped."""
    conv = MarkdownConverter()
    data = {
        "pages": [{
            "text_blocks": [
                {"text": "Page Header", "is_header": True},
                {"text": "Main content"},
            ],
            "tables": [],
        }]
    }
    result = conv.convert(data)
    assert "Page Header" not in result
    assert "Main content" in result


def test_convert_skips_footers_when_configured():
    """Blocks marked as footers should be skipped."""
    conv = MarkdownConverter()
    data = {
        "pages": [{
            "text_blocks": [
                {"text": "Main content"},
                {"text": "Page 1", "is_footer": True},
            ],
            "tables": [],
        }]
    }
    result = conv.convert(data)
    assert "Page 1" not in result
    assert "Main content" in result


def test_convert_keeps_headers_when_disabled():
    """Headers should be kept when remove_headers is False."""
    conf = {"markdown": {"text_cleaning": {"remove_headers": False}}}
    conv = MarkdownConverter(conf)
    data = {
        "pages": [{
            "text_blocks": [
                {"text": "Page Header", "is_header": True},
                {"text": "Main content"},
            ],
            "tables": [],
        }]
    }
    result = conv.convert(data)
    assert "Page Header" in result
    assert "Main content" in result
