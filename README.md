# Fabula Ultima PDF Text Extractor

Automated extraction pipeline for converting Fabula Ultima TTRPG PDFs into markdown files optimized for Claude Projects.

## Overview

This tool extracts text from illustrated TTRPG rulebooks (specifically Fabula Ultima PDFs from DriveThruRPG) and converts them into structured markdown files. It handles multi-column layouts, stat blocks, tables, and heavily illustrated content.

## System Requirements

- macOS 10.15+
- Windows 10/11 (tested)
- Python 3.9+
- 16GB RAM recommended for processing large PDFs
- ~2GB free disk space for processing

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/fabula-extractor.git
cd fabula-extractor

# Create virtual environment
python3 -m venv venv
source venv/bin/activate      # macOS/Linux
venv\Scripts\activate        # Windows

# Install dependencies
pip install -r requirements.txt
```

## Project Structure

```
fabula-extractor/
├── README.md
├── requirements.txt
├── setup.py
├── .gitignore
├── config.yaml
├── src/
│   ├── __init__.py
│   ├── extractor.py
│   ├── processor.py
│   ├── markdown_converter.py
│   └── utils.py
├── input/
│   └── pdfs/          # Place your PDFs here
├── output/
│   ├── raw/           # Raw text extraction
│   ├── processed/     # Cleaned text
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
python -m fabula_extractor.extractor  # or use the console script: fabula-extractor

# Find results in output/markdown/
ls output/markdown/
```

## Core Implementation

### requirements.txt
```
PyMuPDF>=1.26.3
pdfplumber==0.10.3
pypdf==3.17.1
pyyaml==6.0.1
tqdm==4.66.1
click==8.1.7
loguru==0.7.2
```

### config.yaml
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
    
  # RPG-specific patterns
  stat_block_indicators:
    - "HP:"
    - "MP:"
    - "Defense:"
    - "M.Defense:"
    - "Initiative:"
    
markdown:
  # Header detection patterns
  chapter_patterns:
    - "^CHAPTER\s+\d+"
    - "^Chapter\s+\d+"
  
  section_patterns:
    - "^[A-Z][A-Z\s]+$"  # All caps headers
    
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

### src/extractor.py
```python
#!/usr/bin/env python3
"""
Main extraction orchestrator for Fabula Ultima PDFs
"""

import sys
from pathlib import Path
from typing import List, Dict, Optional
import yaml
import click
from loguru import logger
from tqdm import tqdm

from .processor import PDFProcessor
from .markdown_converter import MarkdownConverter
from .utils import setup_logging, validate_pdf, get_file_hash


class FabulaExtractor:
    def __init__(self, config_path: str = "config.yaml"):
        self.config = self._load_config(config_path)
        self.processor = PDFProcessor(self.config)
        self.converter = MarkdownConverter(self.config)
        setup_logging(self.config['logging'])
        
    def _load_config(self, config_path: str) -> Dict:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def extract_pdf(self, pdf_path: Path) -> Optional[Dict]:
        """Extract text from a single PDF"""
        logger.info(f"Processing: {pdf_path.name}")
        
        # Validate PDF
        if not validate_pdf(pdf_path):
            logger.error(f"Invalid PDF: {pdf_path}")
            return None
            
        # Check cache
        file_hash = get_file_hash(pdf_path)
        cache_path = Path(f"output/raw/{file_hash}.json")
        
        if cache_path.exists():
            logger.info("Using cached extraction")
            return self._load_cache(cache_path)
        
        # Extract text
        try:
            result = self.processor.process_pdf(pdf_path)
            
            # Save raw extraction
            self._save_cache(cache_path, result)
            
            # Convert to markdown
            markdown = self.converter.convert(result)
            
            # Save markdown
            output_path = Path(f"output/markdown/{pdf_path.stem}.md")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(markdown, encoding='utf-8')
            
            logger.success(f"Saved: {output_path}")
            return result
            
        except Exception as e:
            logger.exception(f"Failed to process {pdf_path}: {e}")
            return None
    
    def extract_all(self, pdf_dir: Path = Path("input/pdfs")) -> Dict:
        """Extract all PDFs in directory"""
        pdf_files = list(pdf_dir.glob("*.pdf"))
        
        if not pdf_files:
            logger.error(f"No PDFs found in {pdf_dir}")
            return {}
        
        logger.info(f"Found {len(pdf_files)} PDFs")
        results = {}
        
        with tqdm(pdf_files, desc="Extracting PDFs") as pbar:
            for pdf_path in pbar:
                pbar.set_description(f"Processing {pdf_path.name}")
                result = self.extract_pdf(pdf_path)
                if result:
                    results[pdf_path.name] = result
        
        # Create index
        if self.config['output']['create_index']:
            self._create_index(results)
            
        return results
    
    def _create_index(self, results: Dict):
        """Create index file for all extracted content"""
        index_path = Path("output/markdown/INDEX.md")
        
        content = ["# Fabula Ultima Content Index\n\n"]
        
        for filename, data in results.items():
            content.append(f"## {filename}\n")
            content.append(f"- Pages: {data['total_pages']}\n")
            content.append(f"- Text blocks: {data['text_blocks']}\n")
            content.append(f"- Tables: {data['tables']}\n")
            content.append(f"- File: [{filename}](./{Path(filename).stem}.md)\n\n")
        
        index_path.write_text(''.join(content))
        logger.info("Created index file")


@click.command()
@click.option('--pdf', type=click.Path(exists=True), help='Single PDF to process')
@click.option('--all', is_flag=True, help='Process all PDFs in input directory')
@click.option('--config', default='config.yaml', help='Config file path')
def main(pdf: Optional[str], all: bool, config: str):
    """Fabula Ultima PDF Text Extractor"""
    extractor = FabulaExtractor(config)
    
    if pdf:
        extractor.extract_pdf(Path(pdf))
    elif all:
        extractor.extract_all()
    else:
        # Default: process all
        extractor.extract_all()


if __name__ == "__main__":
    main()
```

### src/processor.py
```python
"""
PDF processing module with RP
