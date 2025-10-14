"""
Text Enrichment Pipeline

This pipeline is responsible for extracting and enriching text from PDFs/XML.
It converts raw PDFs into structured, enriched text ready for AI/ChatGPT.

Features:
- PDF text extraction (pypdf + GROBID planned)
- Section detection (Introduction, Methods, Results, Discussion)
- Content normalization (format-agnostic output)
- Smart caching (avoid re-parsing)

Integration Contract:
- Input: Path to PDF or XML file
- Output: EnrichmentResult with structured content
- Format: Normalized JSON (title, abstract, sections, tables, figures)

Usage:
    >>> from omics_oracle_v2.lib.pipelines.text_enrichment import PDFExtractor
    >>>
    >>> extractor = PDFExtractor()
    >>> result = await extractor.extract_text(pdf_path)
    >>> print(f"Sections: {list(result['sections'].keys())}")

Author: OmicsOracle Team
Created: October 14, 2025 (Pipeline Separation)
"""

from omics_oracle_v2.lib.pipelines.text_enrichment.cache_db import FullTextCacheDB
from omics_oracle_v2.lib.pipelines.text_enrichment.normalizer import ContentNormalizer
from omics_oracle_v2.lib.pipelines.text_enrichment.parsed_cache import ParsedCache
from omics_oracle_v2.lib.pipelines.text_enrichment.pdf_parser import PDFExtractor

__all__ = [
    "PDFExtractor",
    "ParsedCache",
    "FullTextCacheDB",
    "ContentNormalizer",
]
