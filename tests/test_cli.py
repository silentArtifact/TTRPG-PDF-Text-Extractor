"""Tests for the CLI interface in :mod:`pdf_extractor.extractor`."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from pdf_extractor.extractor import main, PDFExtractor


@pytest.fixture
def runner():
    """Create a CliRunner instance."""
    return CliRunner()


@pytest.fixture
def sample_pdf():
    """Return path to the test fixture PDF."""
    return Path(__file__).parent / "fixtures" / "sample.pdf"


class TestListPresets:
    """Tests for --list-presets option."""

    def test_list_presets_shows_all_presets(self, runner):
        """Test that --list-presets shows available presets."""
        result = runner.invoke(main, ["--list-presets"])
        assert result.exit_code == 0
        assert "simple" in result.output.lower()
        assert "detailed" in result.output.lower()
        assert "tables" in result.output.lower()

    def test_list_presets_has_descriptions(self, runner):
        """Test that preset descriptions are shown."""
        result = runner.invoke(main, ["--list-presets"])
        assert result.exit_code == 0
        # Should have some description text
        assert len(result.output) > 50


class TestSinglePdfExtraction:
    """Tests for single PDF extraction."""

    def test_nonexistent_pdf_shows_error(self, runner, tmp_path):
        """Test that missing PDF file shows user-friendly error."""
        fake_pdf = tmp_path / "nonexistent.pdf"
        result = runner.invoke(main, [str(fake_pdf)])
        assert result.exit_code != 0
        assert "not find" in result.output.lower() or "error" in result.output.lower()

    def test_non_pdf_file_shows_error(self, runner, tmp_path):
        """Test that non-PDF files are rejected."""
        txt_file = tmp_path / "file.txt"
        txt_file.write_text("not a pdf")
        result = runner.invoke(main, [str(txt_file)])
        assert result.exit_code != 0
        assert "pdf" in result.output.lower()

    def test_pdf_option_works(self, runner, tmp_path, sample_pdf, monkeypatch):
        """Test that --pdf option works."""
        monkeypatch.chdir(tmp_path)
        pdf_copy = tmp_path / "test.pdf"
        pdf_copy.write_bytes(sample_pdf.read_bytes())

        with patch.object(PDFExtractor, "extract_pdf") as mock_extract:
            mock_extract.return_value = {"total_pages": 1}
            result = runner.invoke(main, ["--pdf", str(pdf_copy)])
            # Should call extract_pdf
            assert mock_extract.called

    def test_positional_pdf_argument(self, runner, tmp_path, sample_pdf, monkeypatch):
        """Test positional PDF argument."""
        monkeypatch.chdir(tmp_path)
        pdf_copy = tmp_path / "test.pdf"
        pdf_copy.write_bytes(sample_pdf.read_bytes())

        with patch.object(PDFExtractor, "extract_pdf") as mock_extract:
            mock_extract.return_value = {"total_pages": 1}
            result = runner.invoke(main, [str(pdf_copy)])
            assert mock_extract.called


class TestPresetOption:
    """Tests for --preset option."""

    def test_preset_simple_is_accepted(self, runner, tmp_path, sample_pdf, monkeypatch):
        """Test that --preset simple works."""
        monkeypatch.chdir(tmp_path)
        pdf_copy = tmp_path / "test.pdf"
        pdf_copy.write_bytes(sample_pdf.read_bytes())

        with patch.object(PDFExtractor, "extract_pdf") as mock_extract:
            mock_extract.return_value = {"total_pages": 1}
            result = runner.invoke(main, ["--preset", "simple", str(pdf_copy)])
            assert "simple" in result.output.lower()

    def test_preset_detailed_is_accepted(self, runner, tmp_path, sample_pdf, monkeypatch):
        """Test that --preset detailed works."""
        monkeypatch.chdir(tmp_path)
        pdf_copy = tmp_path / "test.pdf"
        pdf_copy.write_bytes(sample_pdf.read_bytes())

        with patch.object(PDFExtractor, "extract_pdf") as mock_extract:
            mock_extract.return_value = {"total_pages": 1}
            result = runner.invoke(main, ["--preset", "detailed", str(pdf_copy)])
            assert "detailed" in result.output.lower()

    def test_preset_tables_is_accepted(self, runner, tmp_path, sample_pdf, monkeypatch):
        """Test that --preset tables works."""
        monkeypatch.chdir(tmp_path)
        pdf_copy = tmp_path / "test.pdf"
        pdf_copy.write_bytes(sample_pdf.read_bytes())

        with patch.object(PDFExtractor, "extract_pdf") as mock_extract:
            mock_extract.return_value = {"total_pages": 1}
            result = runner.invoke(main, ["--preset", "tables", str(pdf_copy)])
            assert "tables" in result.output.lower()

    def test_invalid_preset_rejected(self, runner):
        """Test that invalid preset names are rejected."""
        result = runner.invoke(main, ["--preset", "invalid", "file.pdf"])
        assert result.exit_code != 0


class TestQuietOption:
    """Tests for --quiet option."""

    def test_quiet_suppresses_banner(self, runner, tmp_path, sample_pdf, monkeypatch):
        """Test that --quiet suppresses the welcome banner."""
        monkeypatch.chdir(tmp_path)
        pdf_copy = tmp_path / "test.pdf"
        pdf_copy.write_bytes(sample_pdf.read_bytes())

        with patch.object(PDFExtractor, "extract_pdf") as mock_extract:
            mock_extract.return_value = {"total_pages": 1}
            result = runner.invoke(main, ["--quiet", str(pdf_copy)])
            # Should not contain the banner
            assert "PDF Text Extractor" not in result.output


class TestAllOption:
    """Tests for --all option."""

    def test_all_option_processes_directory(self, runner, tmp_path, sample_pdf, monkeypatch):
        """Test that --all processes the input directory."""
        monkeypatch.chdir(tmp_path)

        # Create input directory with PDF
        pdf_dir = tmp_path / "input" / "pdfs"
        pdf_dir.mkdir(parents=True)
        (pdf_dir / "test.pdf").write_bytes(sample_pdf.read_bytes())

        with patch.object(PDFExtractor, "extract_all") as mock_extract:
            mock_extract.return_value = {}
            result = runner.invoke(main, ["--all"])
            assert mock_extract.called


class TestHelpOption:
    """Tests for --help option."""

    def test_help_shows_usage(self, runner):
        """Test that --help shows usage information."""
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Usage" in result.output
        assert "--pdf" in result.output
        assert "--preset" in result.output
        assert "--all" in result.output
        assert "--interactive" in result.output
        assert "--quiet" in result.output
