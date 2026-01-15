"""Utility helpers for the extractor project."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Dict, Optional

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


def validate_pdf(path: Path) -> bool:
    """Check that ``path`` is an existing, readable PDF file.

    Validates that the file exists, has a ``.pdf`` extension, is readable,
    and begins with the standard ``%PDF`` header.
    """
    pdf_path = Path(path)
    if not pdf_path.exists() or pdf_path.suffix.lower() != ".pdf":
        return False
    try:
        with pdf_path.open("rb") as fh:
            header = fh.read(4)
            if not header.startswith(b"%PDF"):
                return False
        return True
    except OSError:
        return False


def get_file_hash(path: Path) -> str:
    """Return a SHA256 hash of ``path``'s contents."""
    data = Path(path).read_bytes()
    return hashlib.sha256(data).hexdigest()


def save_cache(path: Path, data: Dict) -> None:
    """Write ``data`` to ``path`` as JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh)


def load_cache(path: Path) -> Dict:
    """Read and return JSON data from ``path``."""
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)

