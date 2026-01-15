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
"""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List


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
            for block in page.get("text_blocks", []):
                text = block.get("text", "")
                for raw_line in text.splitlines():
                    line = self._apply_formatting(raw_line)

                    if self._matches_any(line, self.chapter_patterns):
                        lines.append(f"# {line.strip()}\n\n")
                    elif self._matches_any(line, self.section_patterns):
                        lines.append(f"## {line.strip()}\n\n")
                    else:
                        lines.append(f"{line}\n")

            # Separate pages with a blank line for readability
            if lines and not lines[-1].endswith("\n\n"):
                lines.append("\n")

        markdown = "".join(lines).strip() + "\n"

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
    def _chunk_text(self, text: str) -> List[str]:
        """Split ``text`` into chunks based on ``chunk_size_kb``.

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
        current: List[str] = []
        current_size = 0

        for char in text:
            char_size = len(char.encode("utf-8"))
            if current_size + char_size > limit and current:
                chunks.append("".join(current))
                current = []
                current_size = 0

            current.append(char)
            current_size += char_size

        if current:
            chunks.append("".join(current))

        return chunks

