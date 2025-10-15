"""
Enhanced PDF Text Extraction and Enrichment

Combines basic pypdf extraction with modular enrichers for comprehensive processing.
"""

import logging
from pathlib import Path
from typing import Dict, Optional

from pypdf import PdfReader

from omics_oracle_v2.lib.pipelines.text_enrichment.enrichers import (
    ChatGPTFormatter,
    ReferenceParser,
    SectionDetector,
    TableExtractor,
)

logger = logging.getLogger(__name__)


class PDFExtractor:
    """
    Extract and enrich text from PDF files.

    Capabilities:
    - Basic text extraction (pypdf)
    - Section detection (Introduction, Methods, Results, Discussion)
    - Table extraction and parsing
    - Reference/bibliography parsing
    - ChatGPT-optimized formatting
    """

    def __init__(self, enable_enrichment: bool = True):
        """
        Initialize PDF extractor.

        Args:
            enable_enrichment: Whether to run enrichers (sections, tables, etc.)
        """
        self.enable_enrichment = enable_enrichment

        if enable_enrichment:
            self.section_detector = SectionDetector()
            self.table_extractor = TableExtractor()
            self.reference_parser = ReferenceParser()
            self.chatgpt_formatter = ChatGPTFormatter()

    def extract_text(
        self, pdf_path: Path, metadata: Optional[Dict] = None, context: Optional[str] = None
    ) -> Optional[Dict[str, any]]:
        """
        Extract and enrich text from PDF.

        Args:
            pdf_path: Path to PDF file
            metadata: Optional metadata (title, authors, doi, pmid, etc.)
            context: Optional context about paper usage

        Returns:
            Dict with extracted text, sections, tables, and ChatGPT-formatted content
        """
        try:
            # Step 1: Extract raw text
            reader = PdfReader(pdf_path)

            text_parts = []
            for page in reader.pages:
                text_parts.append(page.extract_text())

            full_text = "\n\n".join(text_parts)

            # Basic result
            result = {
                "full_text": full_text,
                "page_count": len(reader.pages),
                "text_length": len(full_text),
                "extraction_method": "pypdf",
            }

            # Return early if enrichment disabled
            if not self.enable_enrichment:
                return result

            # Step 2: Detect sections
            title = metadata.get("title") if metadata else None
            section_result = self.section_detector.detect_sections(full_text, title=title)

            # Convert Section objects to dicts for JSON serialization
            result["sections"] = {
                name: {
                    "name": sec.name,
                    "title": sec.title,
                    "content": sec.content,
                    "start_pos": sec.start_pos,
                    "end_pos": sec.end_pos,
                    "confidence": sec.confidence,
                }
                for name, sec in section_result.sections.items()
            }
            result["section_order"] = section_result.section_order
            result["abstract"] = section_result.abstract

            # Step 3: Extract tables
            table_result = self.table_extractor.extract_tables(pdf_path)
            result["tables"] = table_result.tables
            result["table_count"] = table_result.table_count

            # Step 4: Parse references
            if "references" in section_result.sections:
                ref_text = section_result.sections["references"].content
                ref_result = self.reference_parser.parse_references(ref_text)
                result["references"] = ref_result.references
                result["reference_count"] = ref_result.reference_count
                result["dois_found"] = ref_result.dois_found
                result["pmids_found"] = ref_result.pmids_found

            # Step 5: Format for ChatGPT
            formatted = self.chatgpt_formatter.format(
                text=full_text,
                title=title,
                sections=section_result.sections,
                tables=table_result.tables,
                references=result.get("references"),
                metadata=metadata,
                context=context,
            )

            result["chatgpt_formatted"] = formatted.to_dict()
            result["chatgpt_prompt"] = self.chatgpt_formatter.format_for_prompt(formatted)

            # Quality scoring
            result["quality_score"] = self._calculate_quality_score(result)

            # Add convenient top-level accessors for common sections
            sections_dict = result.get("sections", {})
            result["methods"] = sections_dict.get("methods", {}).get("content", "")
            result["results"] = sections_dict.get("results", {}).get("content", "")
            result["discussion"] = sections_dict.get("discussion", {}).get("content", "")
            result["conclusion"] = sections_dict.get("conclusion", {}).get("content", "")

            return result

        except Exception as e:
            logger.error(f"Failed to extract PDF text from {pdf_path}: {e}")
            return None

    def _calculate_quality_score(self, result: Dict) -> float:
        """
        Calculate quality score for extracted content.

        Score based on:
        - Text length (substantial content)
        - Sections detected
        - Abstract present
        - Tables extracted
        - References parsed
        """
        score = 0.0

        # Text length (0-0.3)
        text_len = result.get("text_length", 0)
        if text_len > 10000:
            score += 0.3
        elif text_len > 5000:
            score += 0.2
        elif text_len > 1000:
            score += 0.1

        # Sections (0-0.3)
        section_count = len(result.get("sections", {}))
        if section_count >= 4:  # Intro, Methods, Results, Discussion
            score += 0.3
        elif section_count >= 2:
            score += 0.2
        elif section_count >= 1:
            score += 0.1

        # Abstract (0-0.2)
        if result.get("abstract"):
            score += 0.2

        # Tables (0-0.1)
        if result.get("table_count", 0) > 0:
            score += 0.1

        # References (0-0.1)
        if result.get("reference_count", 0) > 0:
            score += 0.1

        return min(score, 1.0)
