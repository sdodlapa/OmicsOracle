"""
Pipeline Organization
=====================

This package contains all 4 production pipelines:

1. citation_discovery/  - Pipeline 1: Discovers papers that cite GEO datasets
   - Uses 5 sources: PubMed, OpenAlex, Semantic Scholar, Europe PMC, OpenCitations
   - Includes quality validation (Phase 9)
   - Includes metrics logging (Phase 10)

2. url_collection/      - Pipeline 2: Collects fulltext URLs from multiple sources
   - 11 sources: PMC, Unpaywall, CORE, Institutional, etc.
   - Priority-based ordering
   - Comprehensive URL metadata

3. pdf_download/        - Pipeline 3: Downloads PDFs with smart caching
   - Waterfall fallback through all available URLs
   - PDF validation and deduplication
   - Smart filesystem caching

4. text_enrichment/     - Pipeline 4: Extracts and enriches text from PDFs
   - PyMuPDF-based extraction
   - Quality scoring
   - Content normalization
   - Parsed content caching

Unified Integration:
-------------------
- PipelineCoordinator: Coordinates all pipelines with unified database + storage
- Automatic recording to database tables
- GEO-centric file organization
- Transaction support and error logging

All pipelines are production-ready and tested.
"""

# Convenience imports
from omics_oracle_v2.lib.pipelines.citation_discovery.geo_discovery import GEOCitationDiscovery
from omics_oracle_v2.lib.pipelines.coordinator import PipelineCoordinator
from omics_oracle_v2.lib.pipelines.pdf_download import PDFDownloadManager
from omics_oracle_v2.lib.pipelines.text_enrichment import PDFExtractor
from omics_oracle_v2.lib.pipelines.url_collection import FullTextManager

__all__ = [
    # Individual Pipelines
    "GEOCitationDiscovery",
    "FullTextManager",
    "PDFDownloadManager",
    "PDFExtractor",
    # Unified Coordinator
    "PipelineCoordinator",
]
