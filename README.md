# PDF Text Extractor

Automated extraction pipeline for converting PDF documents into markdown files.

## Overview

This tool extracts text from PDF documents and converts them into structured markdown files. It handles multi-column layouts, tables, and various text formatting. The output is optimized for use with Claude Projects and other AI tools.

## System Requirements

- macOS 10.15+
- Windows 10/11 (tested)
- Python 3.9+
- 16GB RAM recommended for processing large PDFs
- ~2GB free disk space for processing

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/pdf-extractor.git
cd pdf-extractor

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
pdf-extractor/
├── README.md
├── requirements.txt
├── setup.py
├── .gitignore
├── config.yaml
├── src/
│   └── pdf_extractor/
│       ├── __init__.py
│       ├── extractor.py
│       ├── processor.py
│       ├── markdown_converter.py
│       └── utils.py
├── input/
│   └── pdfs/          # Place your PDFs here
├── output/
│   ├── raw/           # Raw text extraction cache
│   ├── processed/     # Processed text
│   └── markdown/      # Final markdown files
├── logs/
│   └── extraction.log
└── tests/
    └── test_extraction.py
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

output:
  chunk_size_kb: 500  # Split large files
  create_index: true

logging:
  level: INFO
  file: logs/extraction.log
```

## Features

- **Text Extraction**: Uses PyMuPDF for accurate text block extraction
- **Table Detection**: Employs pdfplumber for reliable table parsing
- **Markdown Conversion**: Converts extracted content to clean markdown
- **Caching**: SHA256-based caching prevents redundant processing
- **Chunking**: Large files can be split into manageable chunks
- **Index Generation**: Creates an index file for batch processing
- **Configurable Patterns**: Customize header detection and formatting rules

## Dependencies

- `PyMuPDF>=1.26.3` - PDF text extraction
- `pdfplumber==0.10.3` - Table detection
- `pypdf==3.17.1` - PDF utilities
- `pyyaml==6.0.1` - Configuration parsing
- `tqdm==4.66.1` - Progress bars
- `click==8.1.7` - CLI framework
- `loguru==0.7.2` - Logging

## Usage

### Single PDF

```bash
pdf-extractor --pdf path/to/document.pdf
```

### All PDFs in Directory

```bash
pdf-extractor --all
```

### Custom Config

```bash
pdf-extractor --config custom-config.yaml
```

## License

MIT License
