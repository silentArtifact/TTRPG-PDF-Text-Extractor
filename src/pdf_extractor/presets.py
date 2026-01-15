"""Configuration presets for common extraction scenarios.

This module provides ready-to-use configuration presets that simplify
the extraction process for non-technical users. Instead of editing
YAML configuration files, users can select a preset that matches their
use case.
"""

from __future__ import annotations

import copy
from typing import Any, Dict

# Simple preset: Fast extraction with minimal processing
# Good for quick text extraction from clean, single-column PDFs
PRESET_SIMPLE: Dict[str, Any] = {
    "extraction": {
        "min_text_length": 10,
        "sort_blocks": False,
        "column_threshold": 0.3,
        "detect_headers_footers": False,
        "header_footer_margin": 0.1,
        "table_settings": {
            "vertical_strategy": "lines",
            "horizontal_strategy": "lines",
        },
        "block_indicators": [],
    },
    "markdown": {
        "chapter_patterns": [],
        "section_patterns": [],
        "preserve_formatting": ["bold", "italic", "lists"],
        "text_cleaning": {
            "normalize_unicode": True,
            "normalize_whitespace": True,
            "dehyphenate": True,
            "normalize_quotes": True,
            "render_tables": False,
            "remove_headers": False,
            "remove_footers": False,
        },
    },
    "output": {
        "chunk_size_kb": 0,
        "create_index": False,
    },
    "logging": {
        "level": "WARNING",
        "file": "logs/extraction.log",
    },
}

# Detailed preset: Full-featured extraction with all processing enabled
# Good for complex PDFs with multi-column layouts, tables, and headers/footers
PRESET_DETAILED: Dict[str, Any] = {
    "extraction": {
        "min_text_length": 10,
        "sort_blocks": True,
        "column_threshold": 0.3,
        "detect_headers_footers": True,
        "header_footer_margin": 0.1,
        "table_settings": {
            "vertical_strategy": "lines",
            "horizontal_strategy": "lines",
            "edge_min_length": 3,
            "min_words_horizontal": 1,
            "min_words_vertical": 1,
        },
        "block_indicators": [],
    },
    "markdown": {
        "chapter_patterns": [
            "^CHAPTER\\s+\\d+",
            "^Chapter\\s+\\d+",
        ],
        "section_patterns": [
            "^[A-Z][A-Z\\s]+$",
        ],
        "preserve_formatting": ["bold", "italic", "lists"],
        "text_cleaning": {
            "normalize_unicode": True,
            "normalize_whitespace": True,
            "dehyphenate": True,
            "normalize_quotes": True,
            "render_tables": True,
            "remove_headers": True,
            "remove_footers": True,
        },
    },
    "output": {
        "chunk_size_kb": 500,
        "create_index": True,
    },
    "logging": {
        "level": "INFO",
        "file": "logs/extraction.log",
    },
}

# Tables-only preset: Focused on table extraction
# Good for PDFs that are primarily tabular data (spreadsheets, forms, etc.)
PRESET_TABLES: Dict[str, Any] = {
    "extraction": {
        "min_text_length": 5,
        "sort_blocks": True,
        "column_threshold": 0.3,
        "detect_headers_footers": True,
        "header_footer_margin": 0.1,
        "table_settings": {
            "vertical_strategy": "lines_strict",
            "horizontal_strategy": "lines_strict",
            "edge_min_length": 3,
            "min_words_horizontal": 1,
            "min_words_vertical": 1,
        },
        "block_indicators": [],
    },
    "markdown": {
        "chapter_patterns": [],
        "section_patterns": [],
        "preserve_formatting": [],
        "text_cleaning": {
            "normalize_unicode": True,
            "normalize_whitespace": True,
            "dehyphenate": False,
            "normalize_quotes": True,
            "render_tables": True,
            "remove_headers": True,
            "remove_footers": True,
        },
    },
    "output": {
        "chunk_size_kb": 0,
        "create_index": False,
    },
    "logging": {
        "level": "INFO",
        "file": "logs/extraction.log",
    },
}

# Registry of all available presets
PRESETS: Dict[str, Dict[str, Any]] = {
    "simple": PRESET_SIMPLE,
    "detailed": PRESET_DETAILED,
    "tables": PRESET_TABLES,
}

# Human-readable descriptions for interactive mode
PRESET_DESCRIPTIONS: Dict[str, str] = {
    "simple": "Fast extraction with minimal processing (best for simple PDFs)",
    "detailed": "Full-featured extraction with tables and header/footer removal (recommended)",
    "tables": "Focused on table extraction (best for spreadsheets and forms)",
}


def get_preset(name: str) -> Dict[str, Any]:
    """Get a configuration preset by name.

    Parameters
    ----------
    name:
        The preset name (simple, detailed, or tables).

    Returns
    -------
    Dict[str, Any]
        The configuration dictionary for the preset.

    Raises
    ------
    ValueError
        If the preset name is not recognized.
    """
    name_lower = name.lower()
    if name_lower not in PRESETS:
        available = ", ".join(PRESETS.keys())
        raise ValueError(f"Unknown preset '{name}'. Available presets: {available}")
    return copy.deepcopy(PRESETS[name_lower])


def list_presets() -> Dict[str, str]:
    """Return a dictionary of preset names and their descriptions."""
    return PRESET_DESCRIPTIONS.copy()
