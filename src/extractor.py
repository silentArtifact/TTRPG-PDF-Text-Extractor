#!/usr/bin/env python3
"""Main extraction orchestrator for Fabula Ultima PDFs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

import click
import yaml
from loguru import logger
from tqdm import tqdm

from .markdown_converter import MarkdownConverter
from .processor import PDFProcessor
from .utils import get_file_hash, setup_logging, validate_pdf


class FabulaExtractor:
    """Coordinate PDF processing and markdown conversion."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        self.config = self._load_config(config_path)
        self.processor = PDFProcessor(self.config)
        self.converter = MarkdownConverter(self.config)
        setup_logging(self.config.get("logging"))

    # ------------------------------------------------------------------
    # Configuration and caching helpers
    # ------------------------------------------------------------------
    def _load_config(self, config_path: str) -> Dict:
        """Load YAML configuration file."""
        with open(config_path, "r", encoding="utf-8") as fh:
            return yaml.safe_load(fh)

    def _save_cache(self, cache_path: Path, data: Dict) -> None:
        """Write raw extraction data to a JSON cache file."""
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with cache_path.open("w", encoding="utf-8") as fh:
            json.dump(data, fh)

    def _load_cache(self, cache_path: Path) -> Dict:
        """Load previously cached extraction data."""
        with cache_path.open("r", encoding="utf-8") as fh:
            return json.load(fh)

    # ------------------------------------------------------------------
    # Extraction methods
    # ------------------------------------------------------------------
    def extract_pdf(self, pdf_path: Path) -> Optional[Dict]:
        """Extract text from a single PDF file."""
        logger.info(f"Processing: {pdf_path.name}")

        if not validate_pdf(pdf_path):
            logger.error(f"Invalid PDF: {pdf_path}")
            return None

        file_hash = get_file_hash(pdf_path)
        cache_path = Path(f"output/raw/{file_hash}.json")

        if cache_path.exists():
            logger.info("Using cached extraction")
            return self._load_cache(cache_path)

        try:
            result = self.processor.process_pdf(pdf_path)
            self._save_cache(cache_path, result)

            markdown = self.converter.convert(result)
            output_path = Path(f"output/markdown/{pdf_path.stem}.md")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(markdown, encoding="utf-8")

            logger.success(f"Saved: {output_path}")
            return result
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.exception(f"Failed to process {pdf_path}: {exc}")
            return None

    def extract_all(self, pdf_dir: Path = Path("input/pdfs")) -> Dict:
        """Extract all PDF files in ``pdf_dir``."""
        pdf_files = list(pdf_dir.glob("*.pdf"))
        if not pdf_files:
            logger.error(f"No PDFs found in {pdf_dir}")
            return {}

        logger.info(f"Found {len(pdf_files)} PDFs")
        results: Dict[str, Dict] = {}

        with tqdm(pdf_files, desc="Extracting PDFs") as bar:
            for pdf_path in bar:
                bar.set_description(f"Processing {pdf_path.name}")
                result = self.extract_pdf(pdf_path)
                if result is not None:
                    results[pdf_path.name] = result

        if self.config.get("output", {}).get("create_index"):
            self._create_index(results)

        return results

    # ------------------------------------------------------------------
    # Output helpers
    # ------------------------------------------------------------------
    def _create_index(self, results: Dict) -> None:
        """Create an index markdown file summarising results."""
        index_path = Path("output/markdown/INDEX.md")
        lines = ["# Fabula Ultima Content Index\n\n"]
        for filename, data in results.items():
            lines.append(f"## {filename}\n")
            lines.append(f"- Pages: {data.get('total_pages', 0)}\n")
            lines.append(f"- Text blocks: {data.get('text_blocks', 0)}\n")
            lines.append(f"- Tables: {data.get('tables', 0)}\n")
            lines.append(
                f"- File: [{filename}](./{Path(filename).stem}.md)\n\n"
            )

        index_path.parent.mkdir(parents=True, exist_ok=True)
        index_path.write_text("".join(lines), encoding="utf-8")
        logger.info("Created index file")


@click.command()
@click.option("--pdf", type=click.Path(exists=True), help="Single PDF to process")
@click.option(
    "--all",
    "process_all",
    is_flag=True,
    help="Process all PDFs in input directory",
)
@click.option("--config", default="config.yaml", help="Config file path")
def main(pdf: Optional[str], process_all: bool, config: str) -> None:
    """Fabula Ultima PDF Text Extractor."""
    extractor = FabulaExtractor(config)

    if pdf:
        extractor.extract_pdf(Path(pdf))
    elif process_all:
        extractor.extract_all()
    else:
        extractor.extract_all()


if __name__ == "__main__":  # pragma: no cover - CLI entry
    main()

