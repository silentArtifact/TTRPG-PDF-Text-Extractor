"""Utilities for converting extracted PDF data to Markdown.

This module contains :class:`MarkdownConverter` which takes the structured
dictionary produced by :class:`src.processor.PDFProcessor` and converts it into
Markdown text.  The converter performs a few convenience features:

* Chapter and section headings are detected using regular expression patterns
  supplied in the configuration file.
* Simple formatting such as bold, italic and lists can be preserved or stripped
  depending on configuration.
* Generated Markdown can be split into multiple chunks when exceeding the
  configured ``chunk_size_kb`` output limit.
* Text is cleaned and normalized for better readability.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict, Iterable, List, Optional

# Ligature mappings for normalization
LIGATURE_MAP: Dict[str, str] = {
    "\ufb00": "ff",   # ff ligature
    "\ufb01": "fi",   # fi ligature
    "\ufb02": "fl",   # fl ligature
    "\ufb03": "ffi",  # ffi ligature
    "\ufb04": "ffl",  # ffl ligature
    "\ufb05": "st",   # st ligature (long s + t)
    "\ufb06": "st",   # st ligature
}

# Smart quote and special character mappings
CHAR_REPLACEMENTS: Dict[str, str] = {
    "\u2018": "'",    # Left single quote
    "\u2019": "'",    # Right single quote
    "\u201c": '"',    # Left double quote
    "\u201d": '"',    # Right double quote
    "\u2013": "-",    # En dash
    "\u2014": "--",   # Em dash
    "\u2026": "...",  # Ellipsis
    "\u00a0": " ",    # Non-breaking space
    "\u00ad": "",     # Soft hyphen (remove)
    "\u200b": "",     # Zero-width space (remove)
    "\u2022": "-",    # Bullet
    "\u00b7": "-",    # Middle dot (bullet alternative)
}


class MarkdownConverter:
    """Convert structured extraction data into Markdown."""

    def __init__(self, config: Dict | None = None) -> None:
        self.config = config or {}

        md_conf = self.config.get("markdown", {})
        self.chapter_patterns: List[re.Pattern] = [
            re.compile(p) for p in md_conf.get("chapter_patterns", [])
        ]
        self.section_patterns: List[re.Pattern] = [
            re.compile(p) for p in md_conf.get("section_patterns", [])
        ]

        preserve: Iterable[str] = md_conf.get("preserve_formatting", [])
        self.preserve_bold = "bold" in preserve
        self.preserve_italic = "italic" in preserve
        self.preserve_lists = "lists" in preserve

        # Text cleaning options
        text_cleaning = md_conf.get("text_cleaning", {})
        self.normalize_unicode: bool = text_cleaning.get("normalize_unicode", True)
        self.normalize_whitespace: bool = text_cleaning.get("normalize_whitespace", True)
        self.dehyphenate: bool = text_cleaning.get("dehyphenate", True)
        self.normalize_quotes: bool = text_cleaning.get("normalize_quotes", True)
        self.render_tables: bool = text_cleaning.get("render_tables", True)
        self.remove_headers: bool = text_cleaning.get("remove_headers", True)
        self.remove_footers: bool = text_cleaning.get("remove_footers", True)

        self.chunk_size_kb: int = self.config.get("output", {}).get(
            "chunk_size_kb", 0
        )
        # ``last_chunks`` stores the most recent chunked output from
        # :meth:`convert`.  The extractor can use this attribute if it wishes to
        # write multiple files.
        self.last_chunks: List[str] = []

    # ------------------------------------------------------------------
    def convert(self, result: Dict) -> str:
        """Convert ``result`` data to a Markdown string.

        Parameters
        ----------
        result:
            The structured extraction dictionary produced by
            :class:`PDFProcessor`.

        Returns
        -------
        str
            The Markdown representation of ``result``.  If the resulting text
            exceeds ``chunk_size_kb`` the complete markdown is returned while
            ``self.last_chunks`` stores the individual chunks.
        """

        lines: List[str] = []

        for page in result.get("pages", []):
            # Process text blocks
            block_texts: List[str] = []
            for block in page.get("text_blocks", []):
                # Skip headers/footers if configured
                if self.remove_headers and block.get("is_header"):
                    continue
                if self.remove_footers and block.get("is_footer"):
                    continue

                text = block.get("text", "")
                # Apply text normalization
                text = self._normalize_text(text)
                block_texts.append(text)

            # Join blocks and apply dehyphenation across block boundaries
            page_text = "\n\n".join(block_texts)
            if self.dehyphenate:
                page_text = self._dehyphenate_text(page_text)

            # Process lines for markdown formatting
            for raw_line in page_text.splitlines():
                line = self._apply_formatting(raw_line)

                if self._matches_any(line, self.chapter_patterns):
                    lines.append(f"# {line.strip()}\n\n")
                elif self._matches_any(line, self.section_patterns):
                    lines.append(f"## {line.strip()}\n\n")
                else:
                    lines.append(f"{line}\n")

            # Render tables if enabled
            if self.render_tables:
                for table in page.get("tables", []):
                    if table:
                        lines.append("\n")
                        lines.append(self._render_table(table))
                        lines.append("\n")

            # Separate pages with a blank line for readability
            if lines and not lines[-1].endswith("\n\n"):
                lines.append("\n")

        markdown = "".join(lines)

        # Apply final whitespace normalization
        if self.normalize_whitespace:
            markdown = self._normalize_whitespace(markdown)

        markdown = markdown.strip() + "\n"

        # Store chunked output for optional use by callers
        self.last_chunks = self._chunk_text(markdown)
        return markdown

    # ------------------------------------------------------------------
    def _matches_any(self, text: str, patterns: Iterable[re.Pattern]) -> bool:
        """Check if ``text`` matches any of the regular expressions."""

        return any(pat.search(text) for pat in patterns)

    # ------------------------------------------------------------------
    def _apply_formatting(self, line: str) -> str:
        """Apply formatting preservation or stripping rules to ``line``."""

        text = line.rstrip()

        # List markers: replace bullet characters with markdown lists or remove
        if self.preserve_lists:
            text = re.sub(r"^[\u2022•·]\s*", "- ", text.strip())
        else:
            text = re.sub(r"^[\u2022•·]\s*", "", text.strip())

        # Bold and italic markers
        if not self.preserve_bold:
            text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
            text = re.sub(r"__([^_]+)__", r"\1", text)
        if not self.preserve_italic:
            # Remove single * or _ surrounding text but keep ** for bold
            text = re.sub(r"(?<!\*)\*(?!\*)([^*]+)(?<!\*)\*(?!\*)", r"\1", text)
            text = re.sub(r"_(.+?)_", r"\1", text)

        return text

    # ------------------------------------------------------------------
    def _normalize_text(self, text: str) -> str:
        """Apply Unicode normalization and character replacements.

        Parameters
        ----------
        text:
            Raw text to normalize.

        Returns
        -------
        str
            Normalized text with ligatures expanded and special characters
            replaced.
        """
        if not self.normalize_unicode:
            return text

        # Apply Unicode NFC normalization first
        text = unicodedata.normalize("NFC", text)

        # Expand ligatures
        for ligature, replacement in LIGATURE_MAP.items():
            text = text.replace(ligature, replacement)

        # Normalize quotes and special characters if enabled
        if self.normalize_quotes:
            for char, replacement in CHAR_REPLACEMENTS.items():
                text = text.replace(char, replacement)

        return text

    # ------------------------------------------------------------------
    def _dehyphenate_text(self, text: str) -> str:
        """Rejoin words split across lines with hyphens.

        Handles cases like:
            "The docu-\\nment" -> "The document"

        Only rejoins when the hyphen is at end of line followed by a
        lowercase letter on the next line (indicating word continuation).

        Parameters
        ----------
        text:
            Text with potential hyphenated line breaks.

        Returns
        -------
        str
            Text with rejoined words.
        """
        # Pattern matches: word-\n followed by lowercase continuation
        # This avoids breaking intentional hyphens (e.g., "self-aware")
        pattern = r"(\w)-\n(\s*)([a-z])"
        return re.sub(pattern, r"\1\3", text)

    # ------------------------------------------------------------------
    def _normalize_whitespace(self, text: str) -> str:
        """Normalize excessive whitespace while preserving paragraph structure.

        Parameters
        ----------
        text:
            Text with potential whitespace issues.

        Returns
        -------
        str
            Text with normalized whitespace.
        """
        # Replace multiple spaces with single space (but not at line start)
        text = re.sub(r"(?<!^)[ \t]+", " ", text, flags=re.MULTILINE)

        # Normalize line endings
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # Collapse more than 2 consecutive newlines to 2 (preserve paragraph breaks)
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Remove trailing whitespace from lines
        text = re.sub(r"[ \t]+$", "", text, flags=re.MULTILINE)

        return text

    # ------------------------------------------------------------------
    def _render_table(self, table: List[List[Optional[str]]]) -> str:
        """Convert a table to Markdown format.

        Parameters
        ----------
        table:
            List of rows, each row is a list of cell values.

        Returns
        -------
        str
            Markdown-formatted table.
        """
        if not table or not table[0]:
            return ""

        lines: List[str] = []

        # Clean cell values
        def clean_cell(val: Optional[str]) -> str:
            if val is None:
                return ""
            # Replace newlines within cells and escape pipes
            cleaned = str(val).replace("\n", " ").replace("|", "\\|").strip()
            return cleaned

        # Calculate column widths for alignment
        col_count = max(len(row) for row in table)
        col_widths = [3] * col_count  # Minimum width of 3

        for row in table:
            for i, cell in enumerate(row):
                if i < col_count:
                    width = len(clean_cell(cell))
                    col_widths[i] = max(col_widths[i], width)

        # Build header row (first row of table)
        header_cells = [clean_cell(c) for c in table[0]]
        while len(header_cells) < col_count:
            header_cells.append("")
        header = "| " + " | ".join(
            cell.ljust(col_widths[i]) for i, cell in enumerate(header_cells)
        ) + " |"
        lines.append(header)

        # Build separator row
        separator = "| " + " | ".join("-" * w for w in col_widths) + " |"
        lines.append(separator)

        # Build data rows
        for row in table[1:]:
            cells = [clean_cell(c) for c in row]
            while len(cells) < col_count:
                cells.append("")
            row_str = "| " + " | ".join(
                cell.ljust(col_widths[i]) for i, cell in enumerate(cells)
            ) + " |"
            lines.append(row_str)

        return "\n".join(lines)

    # ------------------------------------------------------------------
    def _chunk_text(self, text: str) -> List[str]:
        """Split ``text`` into chunks based on ``chunk_size_kb``.

        Chunks are broken at paragraph boundaries (double newlines) when
        possible for better readability.

        Parameters
        ----------
        text:
            Markdown text to chunk.

        Returns
        -------
        List[str]
            List of chunk strings.  If ``chunk_size_kb`` is 0 or less, the
            entire text is returned as a single chunk.
        """

        if self.chunk_size_kb <= 0:
            return [text]

        limit = self.chunk_size_kb * 1024
        chunks: List[str] = []

        # Split into paragraphs first
        paragraphs = re.split(r"(\n\n+)", text)

        current_chunk: List[str] = []
        current_size = 0

        for para in paragraphs:
            para_size = len(para.encode("utf-8"))

            # If single paragraph exceeds limit, split it by lines
            if para_size > limit:
                # Flush current chunk first
                if current_chunk:
                    chunks.append("".join(current_chunk))
                    current_chunk = []
                    current_size = 0

                # Split large paragraph by lines
                lines = para.split("\n")
                for line in lines:
                    line_with_newline = line + "\n"
                    line_size = len(line_with_newline.encode("utf-8"))

                    if current_size + line_size > limit and current_chunk:
                        chunks.append("".join(current_chunk))
                        current_chunk = []
                        current_size = 0

                    current_chunk.append(line_with_newline)
                    current_size += line_size
            elif current_size + para_size > limit and current_chunk:
                # Would exceed limit - start new chunk
                chunks.append("".join(current_chunk))
                current_chunk = [para]
                current_size = para_size
            else:
                current_chunk.append(para)
                current_size += para_size

        if current_chunk:
            chunks.append("".join(current_chunk))

        return chunks

