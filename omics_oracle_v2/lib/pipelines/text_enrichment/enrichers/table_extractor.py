"""
Table Extractor

Extracts tables from PDF text and attempts to parse structure.
Supports both pypdf tables and text-based table detection.
"""

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

from pypdf import PdfReader

logger = logging.getLogger(__name__)


@dataclass
class Table:
    """Represents an extracted table."""

    table_number: int  # Table number in paper (Table 1, Table 2, etc.)
    caption: Optional[str] = None  # Table caption/title
    headers: List[str] = field(default_factory=list)  # Column headers
    rows: List[List[str]] = field(default_factory=list)  # Table data rows
    page_number: Optional[int] = None  # Page where table appears
    raw_text: str = ""  # Raw text representation
    confidence: float = 0.5  # Parsing confidence


@dataclass
class TableExtractionResult:
    """Result of table extraction."""

    tables: List[Table] = field(default_factory=list)
    table_count: int = 0
    method: str = "text_detection"


class TableExtractor:
    """Extracts tables from PDFs."""

    # Patterns for detecting table captions
    CAPTION_PATTERNS = [
        re.compile(r"^table\s+(\d+)[\.:]\s*(.+)", re.IGNORECASE),
        re.compile(r"^table\s+(\d+)\s*$", re.IGNORECASE),
    ]

    def __init__(self):
        """Initialize table extractor."""
        pass

    def extract_tables(self, pdf_path: Path) -> TableExtractionResult:
        """
        Extract tables from PDF.

        Args:
            pdf_path: Path to PDF file

        Returns:
            TableExtractionResult with extracted tables
        """
        try:
            reader = PdfReader(pdf_path)

            # Extract text from all pages
            page_texts = []
            for page in reader.pages:
                page_texts.append(page.extract_text())

            # Detect tables from text
            tables = self._detect_tables_from_text(page_texts)

            return TableExtractionResult(tables=tables, table_count=len(tables), method="text_detection")

        except Exception as e:
            logger.error(f"Table extraction failed for {pdf_path}: {e}")
            return TableExtractionResult(tables=[], table_count=0)

    def _detect_tables_from_text(self, page_texts: List[str]) -> List[Table]:
        """
        Detect tables from page text using caption markers and structure.

        This is a heuristic approach - looks for "Table X:" patterns.
        """
        tables = []

        for page_num, page_text in enumerate(page_texts, start=1):
            lines = page_text.split("\n")

            for i, line in enumerate(lines):
                # Check if line is table caption
                caption_match = self._match_table_caption(line)

                if caption_match:
                    table_num, caption = caption_match

                    # Try to extract table content (next N lines that look tabular)
                    table_content = self._extract_table_content(lines[i + 1 : i + 50])

                    table = Table(
                        table_number=table_num,
                        caption=caption,
                        page_number=page_num,
                        raw_text=table_content,
                        confidence=0.6,
                    )

                    tables.append(table)

        return tables

    def _match_table_caption(self, line: str) -> Optional[Tuple[int, str]]:
        """
        Check if line is a table caption.

        Returns:
            Tuple of (table_number, caption) or None
        """
        line_clean = line.strip()

        for pattern in self.CAPTION_PATTERNS:
            match = pattern.match(line_clean)
            if match:
                table_num = int(match.group(1))
                caption = match.group(2) if match.lastindex >= 2 else ""
                return (table_num, caption.strip())

        return None

    def _extract_table_content(self, lines: List[str]) -> str:
        """
        Extract table content following a caption.

        Heuristic: Take lines until we hit a blank line or non-tabular text.
        """
        table_lines = []

        for line in lines:
            line_clean = line.strip()

            # Stop at blank line
            if not line_clean:
                break

            # Stop if we hit another section header or table caption
            if any(
                keyword in line_clean.lower()
                for keyword in ["figure", "table", "introduction", "methods", "results"]
            ):
                if table_lines:  # Only stop if we've collected some lines
                    break

            table_lines.append(line_clean)

            # Limit table size
            if len(table_lines) > 40:
                break

        return "\n".join(table_lines)

    def parse_table_structure(self, table: Table) -> Table:
        """
        Attempt to parse table structure into headers and rows.

        This is basic parsing - looks for delimiter patterns.
        """
        if not table.raw_text:
            return table

        lines = [line.strip() for line in table.raw_text.split("\n") if line.strip()]

        if not lines:
            return table

        # Assume first line is headers (common pattern)
        # Try tab-separated, then space-separated
        if "\t" in lines[0]:
            delimiter = "\t"
        else:
            delimiter = None  # Will use split() for whitespace

        # Parse headers
        if delimiter:
            table.headers = [h.strip() for h in lines[0].split(delimiter)]
        else:
            table.headers = lines[0].split()

        # Parse rows
        for line in lines[1:]:
            if delimiter:
                row = [cell.strip() for cell in line.split(delimiter)]
            else:
                row = line.split()

            if row:
                table.rows.append(row)

        # Update confidence based on structure consistency
        if table.headers and table.rows:
            table.confidence = 0.8

        return table
