"""Utility helpers for the extractor project."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path
from typing import Optional

from loguru import logger


def setup_logging(config: Optional[dict] = None) -> None:
    """Configure basic logging using loguru."""
    config = config or {}
    level = config.get("level", "INFO")

    logger.remove()
    logger.add(sys.stderr, level=level)

    logfile = config.get("file")
    if logfile:
        log_path = Path(logfile)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        logger.add(log_path, level=level)


def validate_pdf(pdf_path: Path) -> bool:
    """Simple PDF file validation."""
    return pdf_path.exists() and pdf_path.suffix.lower() == ".pdf"


def get_file_hash(pdf_path: Path) -> str:
    """Return a SHA256 hash of ``pdf_path``'s contents."""
    data = pdf_path.read_bytes()
    return hashlib.sha256(data).hexdigest()

