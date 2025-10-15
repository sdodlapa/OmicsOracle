"""
Text Enrichment Pipeline (Pipeline 4)

This pipeline is responsible for extracting and enriching text from PDFs/XML.
It converts raw PDFs into structured, enriched text ready for AI/ChatGPT.

Features:
- PDF text extraction (pypdf)
- Section detection (Introduction, Methods, Results, Discussion)
- Table extraction and parsing
- Reference/bibliography parsing
- Content normalization (format-agnostic output)
- ChatGPT-optimized formatting
- Quality scoring and filtering
- Batch processing with concurrency control
- Smart caching (avoid re-parsing)
- Optional GROBID integration (requires external service)

Integration Contract:
- Input: Path to PDF file + optional metadata
- Output: EnrichmentResult with structured content
- Format: Normalized JSON (title, abstract, sections, tables, references)

Usage:
    >>> from omics_oracle_v2.lib.pipelines.text_enrichment import PDFExtractor
    >>>
    >>> extractor = PDFExtractor(enable_enrichment=True)
    >>> result = extractor.extract_text(pdf_path, metadata={"title": "..."})
    >>> print(f"Quality: {result['quality_score']}")
    >>> print(f"Sections: {list(result['sections'].keys())}")

Batch Processing:
    >>> from omics_oracle_v2.lib.pipelines.text_enrichment import process_pdfs_batch
    >>> import asyncio
    >>> from pathlib import Path
    >>>
    >>> pdfs = list(Path("data/pdfs").glob("*.pdf"))
    >>> result = asyncio.run(process_pdfs_batch(pdfs, max_concurrent=5))
    >>> print(f"Success: {result.success_rate:.1f}%")

Enrichers (Modular Components):
    >>> from omics_oracle_v2.lib.pipelines.text_enrichment.enrichers import (
    ...     SectionDetector,
    ...     TableExtractor,
    ...     ReferenceParser,
    ...     ChatGPTFormatter
    ... )

Quality Scoring:
    >>> from omics_oracle_v2.lib.pipelines.text_enrichment import QualityScorer
    >>> metrics = QualityScorer.score_content(enriched)
    >>> print(f"Grade: {metrics.grade}, Score: {metrics.total_score}")

Author: OmicsOracle Team
Created: October 14, 2025 (Pipeline Separation & Enrichment)
"""

from omics_oracle_v2.lib.pipelines.text_enrichment.batch_processor import BatchProcessor, process_pdfs_batch
from omics_oracle_v2.lib.pipelines.text_enrichment.cache_db import FullTextCacheDB
from omics_oracle_v2.lib.pipelines.text_enrichment.enrichers import (
    ChatGPTFormatter,
    ReferenceParser,
    SectionDetector,
    TableExtractor,
)
from omics_oracle_v2.lib.pipelines.text_enrichment.normalizer import ContentNormalizer
from omics_oracle_v2.lib.pipelines.text_enrichment.parsed_cache import ParsedCache
from omics_oracle_v2.lib.pipelines.text_enrichment.pdf_parser import PDFExtractor
from omics_oracle_v2.lib.pipelines.text_enrichment.quality_scorer import QualityScorer

__all__ = [
    # Main extractor
    "PDFExtractor",
    # Enrichers
    "SectionDetector",
    "TableExtractor",
    "ReferenceParser",
    "ChatGPTFormatter",
    # Batch processing
    "BatchProcessor",
    "process_pdfs_batch",
    # Quality assessment
    "QualityScorer",
    # Caching
    "ParsedCache",
    "FullTextCacheDB",
    # Utilities
    "ContentNormalizer",
]
