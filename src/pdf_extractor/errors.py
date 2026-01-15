"""User-friendly error handling for the PDF extractor.

This module provides functions to convert technical exceptions into
clear, actionable messages that help non-technical users understand
and resolve issues.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import NoReturn, Optional

import click
import yaml


class UserFriendlyError(click.ClickException):
    """An exception with a user-friendly message and optional hint."""

    def __init__(self, message: str, hint: Optional[str] = None) -> None:
        super().__init__(message)
        self.hint = hint

    def format_message(self) -> str:
        """Format the error message with optional hint."""
        msg = self.message
        if self.hint:
            msg += f"\n\nHint: {self.hint}"
        return msg


def friendly_exit(message: str, hint: Optional[str] = None) -> NoReturn:
    """Exit with a user-friendly error message.

    Parameters
    ----------
    message:
        The main error message to display.
    hint:
        Optional helpful suggestion for resolving the error.
    """
    click.echo(click.style("Error: ", fg="red", bold=True) + message, err=True)
    if hint:
        click.echo(click.style("Hint: ", fg="yellow") + hint, err=True)
    sys.exit(1)


def handle_file_not_found(path: Path, file_type: str = "file") -> str:
    """Generate a friendly message for missing files.

    Parameters
    ----------
    path:
        The path that was not found.
    file_type:
        Description of what type of file was expected (e.g., "PDF", "config").

    Returns
    -------
    str
        A user-friendly error message.
    """
    message = f"Could not find the {file_type}: {path}"

    # Provide specific hints based on the situation
    if file_type.lower() == "pdf":
        hint = "Please check that the file path is correct and the file exists."
    elif file_type.lower() == "config":
        hint = "You can run without a config file (defaults will be used) or create one."
    else:
        hint = "Please verify the path and try again."

    return f"{message}\n\nHint: {hint}"


def handle_invalid_pdf(path: Path) -> str:
    """Generate a friendly message for invalid PDF files.

    Parameters
    ----------
    path:
        The path to the invalid PDF.

    Returns
    -------
    str
        A user-friendly error message.
    """
    return (
        f"The file '{path.name}' doesn't appear to be a valid PDF.\n\n"
        "Hint: Make sure the file is a proper PDF document and not corrupted. "
        "If you renamed another file type to .pdf, it won't work."
    )


def handle_yaml_error(path: Path, error: yaml.YAMLError) -> str:
    """Generate a friendly message for YAML parsing errors.

    Parameters
    ----------
    path:
        The path to the config file with the error.
    error:
        The YAML error that occurred.

    Returns
    -------
    str
        A user-friendly error message with location info if available.
    """
    message = f"There's a formatting issue in your config file: {path.name}"

    # Try to extract line number from YAML error
    if hasattr(error, "problem_mark") and error.problem_mark:
        mark = error.problem_mark
        message += f"\n  -> Problem found at line {mark.line + 1}, column {mark.column + 1}"

    hint = (
        "YAML files are sensitive to indentation and special characters. "
        "Common issues:\n"
        "  - Missing colon after a key (e.g., 'setting value' should be 'setting: value')\n"
        "  - Incorrect indentation (use spaces, not tabs)\n"
        "  - Unquoted special characters"
    )

    return f"{message}\n\nHint: {hint}"


def handle_permission_error(path: Path, operation: str = "access") -> str:
    """Generate a friendly message for permission errors.

    Parameters
    ----------
    path:
        The path that couldn't be accessed.
    operation:
        What operation was attempted (read, write, access).

    Returns
    -------
    str
        A user-friendly error message.
    """
    return (
        f"Permission denied when trying to {operation}: {path}\n\n"
        "Hint: Check that you have the necessary permissions for this file or folder. "
        "On macOS/Linux, you may need to adjust file permissions with 'chmod'. "
        "On Windows, try running as Administrator if needed."
    )


def handle_no_pdfs_found(directory: Path) -> str:
    """Generate a friendly message when no PDFs are found.

    Parameters
    ----------
    directory:
        The directory that was searched.

    Returns
    -------
    str
        A user-friendly error message.
    """
    return (
        f"No PDF files found in: {directory}\n\n"
        "Hint: Place your PDF files in the input/pdfs/ folder, or specify a file directly:\n"
        "  pdf-extractor your-file.pdf\n"
        "  pdf-extractor --pdf path/to/your-file.pdf"
    )


def handle_extraction_error(path: Path, error: Exception) -> str:
    """Generate a friendly message for extraction errors.

    Parameters
    ----------
    path:
        The PDF file that failed to process.
    error:
        The exception that occurred.

    Returns
    -------
    str
        A user-friendly error message.
    """
    error_type = type(error).__name__

    # Provide specific hints for common errors
    if "password" in str(error).lower() or "encrypted" in str(error).lower():
        hint = "This PDF appears to be password-protected. Please provide an unprotected version."
    elif "memory" in str(error).lower():
        hint = "This PDF may be too large. Try processing fewer pages or closing other applications."
    elif "corrupt" in str(error).lower():
        hint = "The PDF file may be corrupted. Try re-downloading or obtaining a fresh copy."
    else:
        hint = "Check the log file (logs/extraction.log) for more details."

    return (
        f"Failed to extract text from: {path.name}\n"
        f"  -> {error_type}: {str(error)[:100]}\n\n"
        f"Hint: {hint}"
    )


def handle_import_error(module: str) -> str:
    """Generate a friendly message for missing dependencies.

    Parameters
    ----------
    module:
        The module that failed to import.

    Returns
    -------
    str
        A user-friendly error message.
    """
    return (
        f"Required module '{module}' is not installed.\n\n"
        "Hint: Run the following command to install dependencies:\n"
        "  pip install -e .\n"
        "Or if you're not using a virtual environment:\n"
        "  pip install --user -e ."
    )


# Mapping of technical exceptions to friendly handlers
def get_friendly_message(error: Exception, context: Optional[dict] = None) -> str:
    """Convert a technical exception to a user-friendly message.

    Parameters
    ----------
    error:
        The exception to convert.
    context:
        Optional context dictionary with keys like 'path', 'operation'.

    Returns
    -------
    str
        A user-friendly error message.
    """
    context = context or {}
    path = context.get("path")

    if isinstance(error, FileNotFoundError):
        return handle_file_not_found(
            Path(path) if path else Path(str(error)),
            context.get("file_type", "file"),
        )
    elif isinstance(error, PermissionError):
        return handle_permission_error(
            Path(path) if path else Path(str(error)),
            context.get("operation", "access"),
        )
    elif isinstance(error, yaml.YAMLError):
        return handle_yaml_error(
            Path(path) if path else Path("config.yaml"),
            error,
        )
    elif isinstance(error, ImportError):
        return handle_import_error(str(error))
    else:
        # Generic fallback
        return (
            f"An unexpected error occurred: {type(error).__name__}\n"
            f"  -> {str(error)[:200]}\n\n"
            "Hint: Check the log file (logs/extraction.log) for more details. "
            "If the problem persists, please report it at:\n"
            "  https://github.com/anthropics/pdf-extractor/issues"
        )
