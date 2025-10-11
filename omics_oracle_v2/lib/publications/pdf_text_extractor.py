"""PDF text extraction for OmicsOracle.

Extracts text content from PDF files using multiple methods with fallbacks.
Handles modern PDFs, scanned PDFs, and HTML sources.

Note: This extractor focuses on extracting text FROM PDFs.
For finding PDF URLs, see FullTextManager in lib/fulltext/manager.py
"""

import logging
import re
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Try to import PDF libraries (graceful degradation if not installed)
try:
    import pdfplumber

    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False
    logger.warning("pdfplumber not installed - will use PyPDF2 only")

try:
    import PyPDF2

    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False
    logger.warning("PyPDF2 not installed - PDF extraction disabled")

try:
    from bs4 import BeautifulSoup

    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False
    logger.warning("BeautifulSoup not installed - HTML extraction disabled")


class PDFTextExtractor:
    """Extract text content from PDF files.

    Supports multiple extraction methods with automatic fallback:
    1. pdfplumber (best for modern PDFs with tables)
    2. PyPDF2 (fallback for simple text extraction)

    Also supports HTML text extraction via BeautifulSoup.
    """

    def __init__(self):
        """Initialize full-text extractor."""
        self.capabilities = {"pdfplumber": HAS_PDFPLUMBER, "pypdf2": HAS_PYPDF2, "html": HAS_BS4}

        if not (HAS_PDFPLUMBER or HAS_PYPDF2):
            logger.error("No PDF extraction libraries available! Install pdfplumber or PyPDF2")

    def extract_from_pdf(self, pdf_path: Path) -> Optional[str]:
        """Extract text from PDF using multiple methods.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Extracted text or None if failed
        """
        if not pdf_path.exists():
            logger.error(f"PDF not found: {pdf_path}")
            return None

        text = None

        # Try pdfplumber first (best for modern PDFs)
        if HAS_PDFPLUMBER:
            try:
                text = self._extract_with_pdfplumber(pdf_path)
                if text and len(text) > 100:
                    logger.info(f"Extracted {len(text)} chars with pdfplumber from {pdf_path.name}")
                    return self.clean_text(text)
            except Exception as e:
                logger.debug(f"pdfplumber failed for {pdf_path.name}: {e}")

        # Fallback to PyPDF2
        if HAS_PYPDF2:
            try:
                text = self._extract_with_pypdf2(pdf_path)
                if text and len(text) > 100:
                    logger.info(f"Extracted {len(text)} chars with PyPDF2 from {pdf_path.name}")
                    return self.clean_text(text)
            except Exception as e:
                logger.debug(f"PyPDF2 failed for {pdf_path.name}: {e}")

        logger.warning(f"Could not extract text from {pdf_path}")
        return None

    def _extract_with_pdfplumber(self, pdf_path: Path) -> Optional[str]:
        """Extract using pdfplumber (recommended).

        Args:
            pdf_path: Path to PDF

        Returns:
            Extracted text or None
        """
        text_parts = []

        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                try:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
                except Exception as e:
                    logger.debug(f"Failed to extract page {page_num}: {e}")
                    continue

        return "\n".join(text_parts) if text_parts else None

    def _extract_with_pypdf2(self, pdf_path: Path) -> Optional[str]:
        """Extract using PyPDF2 (fallback).

        Args:
            pdf_path: Path to PDF

        Returns:
            Extracted text or None
        """
        text_parts = []

        with open(pdf_path, "rb") as f:
            try:
                reader = PyPDF2.PdfReader(f)
                for page_num, page in enumerate(reader.pages, 1):
                    try:
                        text = page.extract_text()
                        if text:
                            text_parts.append(text)
                    except Exception as e:
                        logger.debug(f"Failed to extract page {page_num}: {e}")
                        continue
            except Exception as e:
                logger.error(f"Failed to read PDF {pdf_path}: {e}")
                return None

        return "\n".join(text_parts) if text_parts else None

    def extract_from_html(self, html_content: str) -> Optional[str]:
        """Extract text from HTML (for PMC, arXiv, etc.).

        Args:
            html_content: HTML content as string

        Returns:
            Extracted text or None
        """
        if not HAS_BS4:
            logger.error("BeautifulSoup not installed - cannot extract from HTML")
            return None

        try:
            soup = BeautifulSoup(html_content, "html.parser")

            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()

            # Get text
            text = soup.get_text(separator="\n")

            if text and len(text) > 100:
                logger.info(f"Extracted {len(text)} chars from HTML")
                return self.clean_text(text)

        except Exception as e:
            logger.error(f"Failed to extract from HTML: {e}")

        return None

    def clean_text(self, text: str) -> str:
        """Clean extracted text by removing artifacts and normalizing.

        Args:
            text: Raw extracted text

        Returns:
            Cleaned text
        """
        if not text:
            return ""

        # Remove null bytes and other control characters
        text = text.replace("\x00", "")
        text = re.sub(r"[\x01-\x08\x0B-\x0C\x0E-\x1F]", "", text)

        # Remove excessive newlines (keep max 2)
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Remove page numbers (common patterns)
        # Pattern: standalone numbers on their own line
        text = re.sub(r"\n\s*\d+\s*\n", "\n", text)

        # Remove excessive whitespace
        text = re.sub(r" {2,}", " ", text)
        text = re.sub(r"\t+", " ", text)

        # Remove common PDF artifacts
        text = text.replace("", "")  # Common artifact character

        # Remove repeated hyphens (header/footer separators)
        text = re.sub(r"-{3,}", "", text)
        text = re.sub(r"_{3,}", "", text)

        # Normalize line breaks around sentences
        # If a line ends with a period, ensure single newline
        text = re.sub(r"\.\n\n+", ".\n", text)

        # Remove leading/trailing whitespace from each line
        lines = [line.strip() for line in text.split("\n")]
        text = "\n".join(line for line in lines if line)

        return text.strip()

    def extract_sections(self, text: str) -> Dict[str, str]:
        """Extract structured sections from full text.

        Attempts to identify: Abstract, Introduction, Methods, Results, Discussion, Conclusions

        Args:
            text: Full text

        Returns:
            Dict of section_name -> section_text
        """
        sections = {}

        if not text:
            return sections

        # Common section headers (case-insensitive patterns)
        section_patterns = {
            "abstract": r"\n\s*ABSTRACT\s*\n",
            "introduction": r"\n\s*(INTRODUCTION|Background)\s*\n",
            "methods": r"\n\s*(METHODS|Materials and Methods|Experimental Procedures)\s*\n",
            "results": r"\n\s*RESULTS\s*\n",
            "discussion": r"\n\s*DISCUSSION\s*\n",
            "conclusions": r"\n\s*(CONCLUSIONS?|Concluding Remarks)\s*\n",
            "references": r"\n\s*(REFERENCES|Bibliography)\s*\n",
        }

        # Find section positions
        section_positions = {}
        for section_name, pattern in section_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                section_positions[section_name] = match.start()

        # Sort sections by position
        sorted_sections = sorted(section_positions.items(), key=lambda x: x[1])

        # Extract text between sections
        for i, (section_name, start_pos) in enumerate(sorted_sections):
            # Find end position (start of next section or end of text)
            if i < len(sorted_sections) - 1:
                end_pos = sorted_sections[i + 1][1]
            else:
                end_pos = len(text)

            section_text = text[start_pos:end_pos].strip()

            # Remove section header from text
            section_text = re.sub(
                section_patterns[section_name], "", section_text, flags=re.IGNORECASE
            ).strip()

            if section_text:
                sections[section_name] = section_text

        return sections

    def get_text_stats(self, text: str) -> Dict[str, int]:
        """Get statistics about extracted text.

        Args:
            text: Extracted text

        Returns:
            Dict with word count, character count, etc.
        """
        if not text:
            return {"characters": 0, "words": 0, "lines": 0}

        words = text.split()
        lines = text.split("\n")

        return {
            "characters": len(text),
            "words": len(words),
            "lines": len(lines),
            "avg_word_length": round(sum(len(w) for w in words) / len(words), 2) if words else 0,
        }
