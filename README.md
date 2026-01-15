# PDF Text Extractor

Automated extraction pipeline for converting PDF documents into markdown files.

## Overview

This tool extracts text from PDF documents and converts them into structured markdown files. It handles multi-column layouts, tables, and various text formatting. The output is optimized for use with Claude Projects and other AI tools.

## System Requirements

- Linux (tested)
- macOS 10.15+
- Windows 10/11 (tested)
- Python 3.9+
- 16GB RAM recommended for processing large PDFs
- ~2GB free disk space for processing

## Installation

```bash
# Clone the repository
git clone https://github.com/silentArtifact/TTRPG-PDF-Text-Extractor.git
cd TTRPG-PDF-Text-Extractor

# Create virtual environment
python3 -m venv venv
source venv/bin/activate      # macOS/Linux
venv\Scripts\activate        # Windows

# Install the package and dependencies
pip install -e .

# On Windows ensure PyMuPDF is installed:
python -m pip install --upgrade pip
pip install pymupdf
```

## Project Structure

```
TTRPG-PDF-Text-Extractor/
├── README.md
├── requirements.txt
├── setup.py
├── .gitignore
├── config.yaml
├── src/
│   └── pdf_extractor/
│       ├── __init__.py
│       ├── __main__.py       # Module entry point
│       ├── errors.py         # User-friendly error handling
│       ├── extractor.py
│       ├── markdown_converter.py
│       ├── presets.py        # Configuration presets
│       ├── processor.py
│       └── utils.py
├── input/
│   └── pdfs/                 # Place your PDFs here
├── output/
│   ├── raw/                  # Raw text extraction cache
│   ├── processed/            # Processed text
│   └── markdown/             # Final markdown files
├── logs/
│   └── extraction.log
└── tests/
    ├── fixtures/             # Test fixtures
    ├── test_config_loading.py
    ├── test_errors.py
    ├── test_extraction.py
    ├── test_markdown_converter.py
    ├── test_presets.py
    ├── test_processor.py
    ├── test_processor_logging.py
    └── test_utils.py
```

## Quick Start

```bash
# Place PDFs in input/pdfs/
cp ~/Downloads/*.pdf input/pdfs/                    # macOS/Linux
copy %USERPROFILE%\Downloads\*.pdf input\pdfs\      # Windows

# Run extraction
python -m pdf_extractor  # or use the console script: pdf-extractor

# Find results in output/markdown/
ls output/markdown/
```

## Configuration

The `config.yaml` file controls extraction behavior:

```yaml
extraction:
  # Text extraction settings
  min_text_length: 10
  page_separator: "\n\n=== PAGE {} ===\n\n"

  # Reading order settings
  sort_blocks: true              # Sort text blocks by reading order
  column_threshold: 0.3          # Threshold for detecting columns (0-1)

  # Header/footer detection
  detect_headers_footers: true   # Detect repeating headers/footers
  header_footer_margin: 0.1      # Top/bottom margin zone (fraction of page height)

  # Table detection
  table_settings:
    vertical_strategy: "lines"
    horizontal_strategy: "lines"
    edge_min_length: 3
    min_words_horizontal: 1
    min_words_vertical: 1

  # Block indicator patterns - text blocks containing these strings
  # will be flagged with has_indicator: true in the output
  block_indicators: []

markdown:
  # Header detection patterns
  chapter_patterns:
    - "^CHAPTER\\s+\\d+"
    - "^Chapter\\s+\\d+"

  section_patterns:
    - "^[A-Z][A-Z\\s]+$"  # All caps headers

  # Conversion rules
  preserve_formatting:
    - bold
    - italic
    - lists

  # Text cleaning options
  text_cleaning:
    normalize_unicode: true      # Expand ligatures and normalize Unicode
    normalize_whitespace: true   # Clean up excessive whitespace
    dehyphenate: true            # Rejoin words split across lines
    normalize_quotes: true       # Convert smart quotes to straight quotes
    render_tables: true          # Render tables as markdown tables
    remove_headers: true         # Remove detected repeating page headers
    remove_footers: true         # Remove detected repeating page footers

output:
  chunk_size_kb: 500  # Split large files (breaks at paragraph boundaries)
  create_index: true

logging:
  level: INFO
  file: logs/extraction.log
```

## Features

- **Text Extraction**: Uses PyMuPDF for accurate text block extraction
- **Table Detection**: Employs pdfplumber for reliable table parsing
- **Markdown Conversion**: Converts extracted content to clean markdown
- **Interactive Mode**: Guided prompts for an easy user experience
- **Presets**: Built-in configuration presets (simple, detailed, tables)
- **Caching**: SHA256-based caching prevents redundant processing
- **Chunking**: Large files can be split into manageable chunks
- **Index Generation**: Creates an index file for batch processing
- **Configurable Patterns**: Customize header detection and formatting rules
- **User-Friendly Errors**: Clear error messages with helpful suggestions

## Dependencies

- `PyMuPDF>=1.26.3` - PDF text extraction
- `pdfplumber==0.10.3` - Table detection
- `pypdf==3.17.1` - PDF utilities
- `pyyaml==6.0.1` - Configuration parsing
- `tqdm==4.66.1` - Progress bars
- `click==8.1.7` - CLI framework
- `loguru==0.7.2` - Logging
- `questionary==2.0.1` - Interactive mode prompts

## Usage

### Single PDF

```bash
pdf-extractor document.pdf
# Or using the --pdf option:
pdf-extractor --pdf path/to/document.pdf
```

### All PDFs in Directory

```bash
pdf-extractor --all
# Or simply run without arguments to process input/pdfs/:
pdf-extractor
```

### Interactive Mode

For guided prompts and a user-friendly experience:

```bash
pdf-extractor --interactive
# Or use the short form:
pdf-extractor -i
```

### Presets

Use built-in configuration presets for common use cases:

```bash
# Simple - Fast extraction, minimal processing
pdf-extractor --preset simple document.pdf

# Detailed - Full extraction with tables (default behavior)
pdf-extractor --preset detailed document.pdf

# Tables - Focused on table extraction
pdf-extractor --preset tables document.pdf

# List available presets
pdf-extractor --list-presets
```

### Quiet Mode

Suppress progress output (only show errors):

```bash
pdf-extractor --quiet document.pdf
pdf-extractor -q --all
```

### Custom Config

```bash
pdf-extractor --config custom-config.yaml document.pdf
```

## License

MIT License
