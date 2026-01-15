#!/usr/bin/env python3
"""Main extraction orchestrator for PDF documents."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List, Optional

import click
import yaml
from loguru import logger
from tqdm import tqdm

from .errors import (
    friendly_exit,
    get_friendly_message,
    handle_invalid_pdf,
    handle_no_pdfs_found,
    handle_yaml_error,
)
from .markdown_converter import MarkdownConverter
from .presets import PRESET_DESCRIPTIONS, get_preset, list_presets
from .processor import PDFProcessor
from .utils import (
    get_file_hash,
    load_cache,
    save_cache,
    setup_logging,
    validate_pdf,
)


class PDFExtractor:
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
        try:
            with open(config_path, "r", encoding="utf-8") as fh:
                return yaml.safe_load(fh) or {}
        except FileNotFoundError:
            logger.warning(f"Config file not found: {config_path}. Using defaults.")
            return {}
        except yaml.YAMLError as exc:
            friendly_msg = handle_yaml_error(Path(config_path), exc)
            friendly_exit(friendly_msg)


    # ------------------------------------------------------------------
    # Extraction methods
    # ------------------------------------------------------------------
    def extract_pdf(self, pdf_path: Path, verbose: bool = True) -> Optional[Dict]:
        """Extract text from a single PDF file.

        Parameters
        ----------
        pdf_path:
            Path to the PDF file to extract.
        verbose:
            If True, print user-friendly progress messages.

        Returns
        -------
        Optional[Dict]
            Extraction result dictionary, or None if extraction failed.
        """
        if verbose:
            click.echo(f"  Processing: {pdf_path.name}")

        logger.info(f"Processing: {pdf_path.name}")

        if not validate_pdf(pdf_path):
            msg = handle_invalid_pdf(pdf_path)
            logger.error(msg)
            if verbose:
                click.echo(click.style(f"  Error: {msg}", fg="red"), err=True)
            return None

        file_hash = get_file_hash(pdf_path)
        cache_path = Path("output") / "raw" / f"{file_hash}.json"

        if cache_path.exists():
            logger.info("Using cached extraction")
            if verbose:
                click.echo(click.style("    Using cached data", fg="cyan"))
            return load_cache(cache_path)

        try:
            result = self.processor.process_pdf(pdf_path)
            pages = result.get("total_pages", 0)
            tables = result.get("tables", 0)

            save_cache(cache_path, result)

            markdown = self.converter.convert(result)
            output_path = Path("output") / "markdown" / f"{pdf_path.stem}.md"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(markdown, encoding="utf-8")

            logger.success(f"Saved: {output_path}")
            if verbose:
                click.echo(click.style(f"    Extracted {pages} pages", fg="green"))
                if tables > 0:
                    click.echo(click.style(f"    Found {tables} tables", fg="green"))
                click.echo(click.style(f"    Saved to: {output_path}", fg="green"))
            return result
        except Exception as exc:  # pragma: no cover - defensive logging
            friendly_msg = get_friendly_message(exc, {"path": pdf_path})
            logger.exception(f"Failed to process {pdf_path}: {exc}")
            if verbose:
                click.echo(click.style(f"  Error: {friendly_msg}", fg="red"), err=True)
            return None

    def extract_all(
        self, pdf_dir: Path = Path("input") / "pdfs", verbose: bool = True
    ) -> Dict:
        """Extract all PDF files in ``pdf_dir``.

        Parameters
        ----------
        pdf_dir:
            Directory containing PDF files to process.
        verbose:
            If True, print user-friendly progress messages.

        Returns
        -------
        Dict
            Dictionary mapping filenames to extraction results.
        """
        pdf_files = list(pdf_dir.glob("*.pdf"))
        if not pdf_files:
            msg = handle_no_pdfs_found(pdf_dir)
            logger.error(msg)
            if verbose:
                click.echo(click.style(f"Error: {msg}", fg="red"), err=True)
            return {}

        if verbose:
            click.echo(f"\nFound {len(pdf_files)} PDF(s) to process\n")

        logger.info(f"Found {len(pdf_files)} PDFs")
        results: Dict[str, Dict] = {}
        success_count = 0
        fail_count = 0

        for pdf_path in pdf_files:
            result = self.extract_pdf(pdf_path, verbose=verbose)
            if result is not None:
                results[pdf_path.name] = result
                success_count += 1
            else:
                fail_count += 1
            if verbose:
                click.echo("")  # Blank line between files

        if self.config.get("output", {}).get("create_index"):
            self._create_index(results)

        # Print summary
        if verbose:
            click.echo(click.style("=" * 40, fg="blue"))
            click.echo(click.style("Summary:", bold=True))
            click.echo(click.style(f"  Successfully processed: {success_count}", fg="green"))
            if fail_count > 0:
                click.echo(click.style(f"  Failed: {fail_count}", fg="red"))
            click.echo(click.style(f"\nOutput saved to: output/markdown/", fg="cyan"))

        return results

    # ------------------------------------------------------------------
    # Output helpers
    # ------------------------------------------------------------------
    def _create_index(self, results: Dict) -> None:
        """Create an index markdown file summarising results."""
        index_path = Path("output") / "markdown" / "INDEX.md"
        lines = ["# PDF Content Index\n\n"]
        for filename, data in results.items():
            lines.append(f"## {filename}\n")
            lines.append(f"- Pages: {data.get('total_pages', 0)}\n")
            lines.append(f"- Text blocks: {data.get('text_blocks', 0)}\n")
            lines.append(f"- Tables: {data.get('tables', 0)}\n")
            link_path = Path(".") / f"{Path(filename).stem}.md"
            lines.append(f"- File: [{filename}]({link_path})\n\n")

        index_path.parent.mkdir(parents=True, exist_ok=True)
        index_path.write_text("".join(lines), encoding="utf-8")
        logger.info("Created index file")


def _run_interactive_mode(config: Optional[str] = None) -> None:
    """Run the extractor in interactive mode with guided prompts.

    This provides a user-friendly experience for non-technical users
    by guiding them through the extraction process step by step.
    """
    try:
        import questionary
    except ImportError:
        friendly_exit(
            "Interactive mode requires the 'questionary' package.",
            "Install it with: pip install questionary",
        )

    click.echo(click.style("\n=== PDF Text Extractor ===\n", fg="blue", bold=True))
    click.echo("Welcome! This tool extracts text from PDF files.\n")

    # Ask what they want to do
    action = questionary.select(
        "What would you like to do?",
        choices=[
            questionary.Choice("Extract a single PDF file", value="single"),
            questionary.Choice("Extract all PDFs in a folder", value="all"),
            questionary.Choice("Learn about presets", value="presets"),
            questionary.Choice("Exit", value="exit"),
        ],
    ).ask()

    if action == "exit" or action is None:
        click.echo("Goodbye!")
        return

    if action == "presets":
        click.echo(click.style("\nAvailable Presets:\n", bold=True))
        for name, desc in PRESET_DESCRIPTIONS.items():
            click.echo(f"  {click.style(name, fg='cyan')}: {desc}")
        click.echo(
            "\nUse presets with: pdf-extractor --preset <name> your-file.pdf\n"
        )
        return

    # Ask about preset preference
    preset_choice = questionary.select(
        "Which extraction preset would you like to use?",
        choices=[
            questionary.Choice(
                "Detailed - Full extraction with tables (Recommended)",
                value="detailed",
            ),
            questionary.Choice(
                "Simple - Fast extraction, minimal processing",
                value="simple",
            ),
            questionary.Choice(
                "Tables - Focused on table extraction",
                value="tables",
            ),
            questionary.Choice(
                "Custom - Use config.yaml file",
                value="custom",
            ),
        ],
    ).ask()

    if preset_choice is None:
        return

    # Load configuration
    if preset_choice == "custom":
        extractor = PDFExtractor(config or "config.yaml")
    else:
        preset_config = get_preset(preset_choice)
        extractor = PDFExtractor.__new__(PDFExtractor)
        extractor.config = preset_config
        extractor.processor = PDFProcessor(preset_config)
        extractor.converter = MarkdownConverter(preset_config)
        setup_logging(preset_config.get("logging"))

    if action == "single":
        # Ask for file path
        pdf_path_str = questionary.path(
            "Enter the path to your PDF file:",
            only_directories=False,
        ).ask()

        if not pdf_path_str:
            return

        pdf_path = Path(pdf_path_str)
        if not pdf_path.exists():
            friendly_exit(f"File not found: {pdf_path}")

        if not pdf_path.suffix.lower() == ".pdf":
            friendly_exit(
                f"'{pdf_path.name}' doesn't appear to be a PDF file.",
                "Make sure the file has a .pdf extension.",
            )

        click.echo("")
        extractor.extract_pdf(pdf_path, verbose=True)

    elif action == "all":
        # Ask for directory
        default_dir = Path("input") / "pdfs"
        use_default = questionary.confirm(
            f"Use default folder ({default_dir})?",
            default=True,
        ).ask()

        if use_default:
            pdf_dir = default_dir
        else:
            pdf_dir_str = questionary.path(
                "Enter the path to the folder containing PDFs:",
                only_directories=True,
            ).ask()
            if not pdf_dir_str:
                return
            pdf_dir = Path(pdf_dir_str)

        if not pdf_dir.exists():
            friendly_exit(f"Directory not found: {pdf_dir}")

        extractor.extract_all(pdf_dir, verbose=True)

    click.echo(click.style("\nDone! Check the output/markdown/ folder for results.\n", fg="green"))


def _list_pdf_files(directory: Path) -> List[Path]:
    """List PDF files in a directory for display."""
    return sorted(directory.glob("*.pdf"))


@click.command()
@click.argument("pdf_file", type=click.Path(), required=False)
@click.option(
    "--pdf",
    "pdf_option",
    type=click.Path(exists=True),
    help="Single PDF to process (alternative to positional argument)",
)
@click.option(
    "--all",
    "process_all",
    is_flag=True,
    help="Process all PDFs in input directory",
)
@click.option(
    "--config",
    default="config.yaml",
    help="Config file path",
)
@click.option(
    "--preset",
    type=click.Choice(["simple", "detailed", "tables"], case_sensitive=False),
    help="Use a configuration preset instead of config file",
)
@click.option(
    "--interactive", "-i",
    is_flag=True,
    help="Run in interactive mode with guided prompts",
)
@click.option(
    "--quiet", "-q",
    is_flag=True,
    help="Suppress progress output (only show errors)",
)
@click.option(
    "--list-presets",
    is_flag=True,
    help="Show available presets and exit",
)
def main(
    pdf_file: Optional[str],
    pdf_option: Optional[str],
    process_all: bool,
    config: str,
    preset: Optional[str],
    interactive: bool,
    quiet: bool,
    list_presets: bool,
) -> None:
    """PDF Text Extractor - Extract text and tables from PDF documents.

    \b
    Examples:
      pdf-extractor document.pdf          Extract a single PDF
      pdf-extractor --all                 Extract all PDFs in input/pdfs/
      pdf-extractor -i                    Interactive mode (guided prompts)
      pdf-extractor --preset simple doc.pdf   Use simple preset

    \b
    Presets:
      simple    - Fast extraction, minimal processing
      detailed  - Full extraction with tables (default behavior)
      tables    - Focused on table extraction
    """
    # Handle --list-presets
    if list_presets:
        click.echo(click.style("\nAvailable Presets:\n", bold=True))
        for name, desc in PRESET_DESCRIPTIONS.items():
            click.echo(f"  {click.style(name, fg='cyan', bold=True)}")
            click.echo(f"    {desc}\n")
        return

    # Handle interactive mode
    if interactive:
        _run_interactive_mode(config)
        return

    # Determine which PDF path to use (positional or --pdf option)
    pdf_path_str = pdf_file or pdf_option

    # Print welcome banner unless quiet
    if not quiet:
        click.echo(click.style("\nPDF Text Extractor\n", fg="blue", bold=True))

    # Load configuration (from preset or file)
    if preset:
        if not quiet:
            click.echo(f"Using preset: {click.style(preset, fg='cyan')}\n")
        preset_config = get_preset(preset)
        extractor = PDFExtractor.__new__(PDFExtractor)
        extractor.config = preset_config
        extractor.processor = PDFProcessor(preset_config)
        extractor.converter = MarkdownConverter(preset_config)
        setup_logging(preset_config.get("logging"))
    else:
        extractor = PDFExtractor(config)

    verbose = not quiet

    # Process based on arguments
    if pdf_path_str:
        # Single PDF specified
        pdf_path = Path(pdf_path_str)
        if not pdf_path.exists():
            friendly_exit(
                f"Could not find PDF file: {pdf_path}",
                "Please check that the file path is correct.",
            )
        if not pdf_path.suffix.lower() == ".pdf":
            friendly_exit(
                f"'{pdf_path.name}' doesn't appear to be a PDF file.",
                "Make sure the file has a .pdf extension.",
            )
        extractor.extract_pdf(pdf_path, verbose=verbose)
    elif process_all:
        extractor.extract_all(verbose=verbose)
    else:
        # Default: process all PDFs in input directory
        extractor.extract_all(verbose=verbose)


if __name__ == "__main__":  # pragma: no cover - CLI entry
    main()

