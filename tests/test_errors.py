"""Tests for the errors module."""

import pytest
import sys
from pathlib import Path
import importlib.util

import yaml

# Load errors module directly without going through __init__.py
# This avoids triggering pdfplumber import which may have environment issues
_errors_path = Path(__file__).parent.parent / "src" / "pdf_extractor" / "errors.py"
_spec = importlib.util.spec_from_file_location("errors", _errors_path)
_errors_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_errors_module)

UserFriendlyError = _errors_module.UserFriendlyError
handle_file_not_found = _errors_module.handle_file_not_found
handle_invalid_pdf = _errors_module.handle_invalid_pdf
handle_yaml_error = _errors_module.handle_yaml_error
handle_permission_error = _errors_module.handle_permission_error
handle_no_pdfs_found = _errors_module.handle_no_pdfs_found
handle_extraction_error = _errors_module.handle_extraction_error
handle_import_error = _errors_module.handle_import_error
get_friendly_message = _errors_module.get_friendly_message


class TestUserFriendlyError:
    """Tests for the UserFriendlyError class."""

    def test_message_only(self):
        """Test error with message only."""
        error = UserFriendlyError("Test message")
        assert error.message == "Test message"
        assert error.hint is None

    def test_message_with_hint(self):
        """Test error with message and hint."""
        error = UserFriendlyError("Test message", hint="Try this")
        assert error.message == "Test message"
        assert error.hint == "Try this"

    def test_format_message_without_hint(self):
        """Test format_message without hint."""
        error = UserFriendlyError("Test message")
        assert error.format_message() == "Test message"

    def test_format_message_with_hint(self):
        """Test format_message includes hint."""
        error = UserFriendlyError("Test message", hint="Try this")
        formatted = error.format_message()
        assert "Test message" in formatted
        assert "Try this" in formatted
        assert "Hint:" in formatted


class TestHandleFileNotFound:
    """Tests for handle_file_not_found function."""

    def test_pdf_file_not_found(self):
        """Test message for missing PDF file."""
        msg = handle_file_not_found(Path("/test/file.pdf"), "PDF")
        assert "PDF" in msg
        assert "/test/file.pdf" in msg
        assert "Hint:" in msg

    def test_config_file_not_found(self):
        """Test message for missing config file."""
        msg = handle_file_not_found(Path("config.yaml"), "config")
        assert "config" in msg
        assert "config.yaml" in msg

    def test_generic_file_not_found(self):
        """Test message for generic file."""
        msg = handle_file_not_found(Path("/some/file"), "file")
        assert "file" in msg


class TestHandleInvalidPdf:
    """Tests for handle_invalid_pdf function."""

    def test_includes_filename(self):
        """Test that message includes the filename."""
        msg = handle_invalid_pdf(Path("/test/document.pdf"))
        assert "document.pdf" in msg

    def test_includes_valid_pdf_mention(self):
        """Test that message mentions valid PDF."""
        msg = handle_invalid_pdf(Path("/test/file.pdf"))
        assert "valid PDF" in msg

    def test_includes_hint(self):
        """Test that message includes a hint."""
        msg = handle_invalid_pdf(Path("/test/file.pdf"))
        assert "Hint:" in msg


class TestHandleYamlError:
    """Tests for handle_yaml_error function."""

    def test_basic_yaml_error(self):
        """Test message for basic YAML error."""
        try:
            yaml.safe_load("key: [invalid")
        except yaml.YAMLError as e:
            msg = handle_yaml_error(Path("config.yaml"), e)
            assert "config.yaml" in msg
            assert "Hint:" in msg

    def test_mentions_common_issues(self):
        """Test that message mentions common YAML issues."""
        try:
            yaml.safe_load("bad yaml:")
        except yaml.YAMLError as e:
            msg = handle_yaml_error(Path("test.yaml"), e)
            assert "colon" in msg.lower() or "indentation" in msg.lower()


class TestHandlePermissionError:
    """Tests for handle_permission_error function."""

    def test_read_permission(self):
        """Test message for read permission error."""
        msg = handle_permission_error(Path("/test/file.pdf"), "read")
        assert "read" in msg
        assert "Permission" in msg

    def test_write_permission(self):
        """Test message for write permission error."""
        msg = handle_permission_error(Path("/test/dir"), "write")
        assert "write" in msg

    def test_includes_hint(self):
        """Test that message includes permission hint."""
        msg = handle_permission_error(Path("/test"), "access")
        assert "Hint:" in msg
        assert "permission" in msg.lower()


class TestHandleNoPdfsFound:
    """Tests for handle_no_pdfs_found function."""

    def test_includes_directory(self):
        """Test that message includes the directory path."""
        msg = handle_no_pdfs_found(Path("/test/pdfs"))
        assert "/test/pdfs" in msg

    def test_includes_usage_hint(self):
        """Test that message includes usage hint."""
        msg = handle_no_pdfs_found(Path("input/pdfs"))
        assert "pdf-extractor" in msg
        assert "Hint:" in msg


class TestHandleExtractionError:
    """Tests for handle_extraction_error function."""

    def test_generic_error(self):
        """Test message for generic extraction error."""
        error = ValueError("Something went wrong")
        msg = handle_extraction_error(Path("/test/doc.pdf"), error)
        assert "doc.pdf" in msg
        assert "ValueError" in msg

    def test_password_error(self):
        """Test message for password-related error."""
        error = Exception("PDF is password protected")
        msg = handle_extraction_error(Path("/test/doc.pdf"), error)
        assert "password" in msg.lower()

    def test_memory_error(self):
        """Test message for memory-related error."""
        error = Exception("Out of memory")
        msg = handle_extraction_error(Path("/test/doc.pdf"), error)
        assert "memory" in msg.lower() or "large" in msg.lower()


class TestHandleImportError:
    """Tests for handle_import_error function."""

    def test_includes_module_name(self):
        """Test that message includes the module name."""
        msg = handle_import_error("pdfplumber")
        assert "pdfplumber" in msg

    def test_includes_install_instructions(self):
        """Test that message includes installation instructions."""
        msg = handle_import_error("test_module")
        assert "pip install" in msg


class TestGetFriendlyMessage:
    """Tests for get_friendly_message function."""

    def test_file_not_found(self):
        """Test handling FileNotFoundError."""
        error = FileNotFoundError("file.pdf")
        msg = get_friendly_message(error, {"path": "/test/file.pdf", "file_type": "PDF"})
        assert "PDF" in msg

    def test_permission_error(self):
        """Test handling PermissionError."""
        error = PermissionError("Permission denied")
        msg = get_friendly_message(error, {"path": "/test/file", "operation": "read"})
        assert "Permission" in msg

    def test_yaml_error(self):
        """Test handling YAMLError."""
        try:
            yaml.safe_load("invalid: [")
        except yaml.YAMLError as error:
            msg = get_friendly_message(error, {"path": "config.yaml"})
            assert "config.yaml" in msg

    def test_import_error(self):
        """Test handling ImportError."""
        error = ImportError("No module named 'test'")
        msg = get_friendly_message(error)
        assert "module" in msg.lower()

    def test_generic_error(self):
        """Test handling generic errors."""
        error = RuntimeError("Something unexpected")
        msg = get_friendly_message(error)
        assert "unexpected" in msg.lower() or "RuntimeError" in msg
        assert "Hint:" in msg
