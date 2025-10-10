"""
Publications Module - PubMed, PMC, and Google Scholar Integration

This module provides comprehensive publication search and analysis capabilities,
including PubMed, PubMed Central, and Google Scholar integration.

Key Components:
- PublicationSearchPipeline: Main pipeline following the golden pattern
- PubMedClient: PubMed/Entrez API integration
- GoogleScholarClient: Google Scholar scraping (Week 3)
- PDFDownloader: Full-text PDF retrieval (Week 4)
- PublicationRanker: Relevance-based ranking

Week 1-2 Focus: PubMed integration with basic ranking
Week 3: Enhanced publications (Scholar, citations)
Week 4: PDF processing and full-text extraction
"""

from omics_oracle_v2.lib.pipelines.publication_pipeline import PublicationSearchPipeline
from omics_oracle_v2.lib.publications.config import PublicationSearchConfig, PubMedConfig
from omics_oracle_v2.lib.publications.models import (
    Publication,
    PublicationResult,
    PublicationSearchResult,
    PublicationSource,
)

__all__ = [
    # Models
    "Publication",
    "PublicationSearchResult",
    "PublicationResult",
    "PublicationSource",
    # Configuration
    "PubMedConfig",
    "PublicationSearchConfig",
    # Pipeline
    "PublicationSearchPipeline",
]

__version__ = "0.1.0"
