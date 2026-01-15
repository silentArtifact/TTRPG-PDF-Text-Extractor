"""Tests for the presets module."""

import pytest
import sys
from pathlib import Path
import importlib.util

# Load presets module directly without going through __init__.py
# This avoids triggering pdfplumber import which may have environment issues
_presets_path = Path(__file__).parent.parent / "src" / "pdf_extractor" / "presets.py"
_spec = importlib.util.spec_from_file_location("presets", _presets_path)
_presets_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_presets_module)

get_preset = _presets_module.get_preset
list_presets = _presets_module.list_presets
PRESET_DESCRIPTIONS = _presets_module.PRESET_DESCRIPTIONS
PRESET_SIMPLE = _presets_module.PRESET_SIMPLE
PRESET_DETAILED = _presets_module.PRESET_DETAILED
PRESET_TABLES = _presets_module.PRESET_TABLES
PRESETS = _presets_module.PRESETS


class TestGetPreset:
    """Tests for the get_preset function."""

    def test_get_simple_preset(self):
        """Test retrieving the simple preset."""
        preset = get_preset("simple")
        assert "extraction" in preset
        assert "markdown" in preset
        assert "output" in preset
        assert preset["extraction"]["sort_blocks"] is False

    def test_get_detailed_preset(self):
        """Test retrieving the detailed preset."""
        preset = get_preset("detailed")
        assert preset["extraction"]["sort_blocks"] is True
        assert preset["extraction"]["detect_headers_footers"] is True
        assert preset["markdown"]["text_cleaning"]["render_tables"] is True
        assert preset["output"]["create_index"] is True

    def test_get_tables_preset(self):
        """Test retrieving the tables preset."""
        preset = get_preset("tables")
        assert preset["markdown"]["text_cleaning"]["render_tables"] is True
        assert preset["markdown"]["text_cleaning"]["dehyphenate"] is False

    def test_get_preset_case_insensitive(self):
        """Test that preset names are case insensitive."""
        preset1 = get_preset("SIMPLE")
        preset2 = get_preset("Simple")
        preset3 = get_preset("simple")
        assert preset1 == preset2 == preset3

    def test_get_preset_returns_copy(self):
        """Test that get_preset returns a copy, not the original."""
        preset1 = get_preset("simple")
        preset1["test_key"] = "test_value"
        preset2 = get_preset("simple")
        assert "test_key" not in preset2

    def test_get_unknown_preset_raises(self):
        """Test that unknown preset names raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            get_preset("nonexistent")
        assert "Unknown preset" in str(exc_info.value)
        assert "nonexistent" in str(exc_info.value)


class TestListPresets:
    """Tests for the list_presets function."""

    def test_list_presets_returns_dict(self):
        """Test that list_presets returns a dictionary."""
        presets = list_presets()
        assert isinstance(presets, dict)

    def test_list_presets_contains_all_presets(self):
        """Test that list_presets contains all available presets."""
        presets = list_presets()
        assert "simple" in presets
        assert "detailed" in presets
        assert "tables" in presets

    def test_list_presets_returns_copy(self):
        """Test that list_presets returns a copy."""
        presets1 = list_presets()
        presets1["new_preset"] = "description"
        presets2 = list_presets()
        assert "new_preset" not in presets2


class TestPresetStructure:
    """Tests for preset configuration structure."""

    @pytest.mark.parametrize("preset_name", ["simple", "detailed", "tables"])
    def test_preset_has_required_sections(self, preset_name):
        """Test that all presets have required configuration sections."""
        preset = get_preset(preset_name)
        assert "extraction" in preset
        assert "markdown" in preset
        assert "output" in preset
        assert "logging" in preset

    @pytest.mark.parametrize("preset_name", ["simple", "detailed", "tables"])
    def test_preset_extraction_settings(self, preset_name):
        """Test that extraction settings are valid."""
        preset = get_preset(preset_name)
        extraction = preset["extraction"]
        assert "min_text_length" in extraction
        assert "sort_blocks" in extraction
        assert isinstance(extraction["min_text_length"], int)

    @pytest.mark.parametrize("preset_name", ["simple", "detailed", "tables"])
    def test_preset_markdown_settings(self, preset_name):
        """Test that markdown settings are valid."""
        preset = get_preset(preset_name)
        markdown = preset["markdown"]
        assert "text_cleaning" in markdown
        assert "normalize_unicode" in markdown["text_cleaning"]


class TestPresetDescriptions:
    """Tests for preset descriptions."""

    def test_all_presets_have_descriptions(self):
        """Test that all presets have descriptions."""
        for name in PRESETS.keys():
            assert name in PRESET_DESCRIPTIONS
            assert len(PRESET_DESCRIPTIONS[name]) > 0

    def test_descriptions_are_meaningful(self):
        """Test that descriptions are meaningful (not empty or placeholder)."""
        for name, desc in PRESET_DESCRIPTIONS.items():
            assert len(desc) > 10
            assert name.lower() not in desc.lower() or "extraction" in desc.lower()
