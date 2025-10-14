"""Simple PDF text extraction using pypdf."""

import logging
from pathlib import Path
from typing import Dict, Optional

from pypdf import PdfReader

logger = logging.getLogger(__name__)


class PDFExtractor:
    """Extract text from PDF files."""

    @staticmethod
    def extract_text(pdf_path: Path) -> Optional[Dict[str, any]]:
        """
        Extract text from PDF.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Dict with extracted text and metadata, or None if failed
        """
        try:
            reader = PdfReader(pdf_path)

            # Extract all text
            text_parts = []
            for page in reader.pages:
                text_parts.append(page.extract_text())

            full_text = "\n\n".join(text_parts)

            return {
                "full_text": full_text,
                "page_count": len(reader.pages),
                "text_length": len(full_text),
                "extraction_method": "pypdf",
            }

        except Exception as e:
            logger.error(f"Failed to extract PDF text from {pdf_path}: {e}")
            return None
