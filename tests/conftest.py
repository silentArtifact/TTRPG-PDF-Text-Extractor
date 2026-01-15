"""Shared pytest fixtures for pdf_extractor tests."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def fixtures_dir() -> Path:
    """Return the path to the test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_pdf(fixtures_dir) -> Path:
    """Return path to the sample PDF fixture."""
    return fixtures_dir / "sample.pdf"


@pytest.fixture
def root_config() -> Path:
    """Return path to the root config.yaml file."""
    return Path(__file__).resolve().parent.parent / "config.yaml"
