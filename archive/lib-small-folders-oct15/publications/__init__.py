"""
Publications Module - PubMed and OpenAlex Integration

This module provides publication search capabilities.

Key Components:
- PubMedClient: PubMed/Entrez API integration
- OpenAlexClient: OpenAlex API for citation discovery
- PDFDownloader: Full-text PDF retrieval

All pipeline orchestrators have been archived (see extras/pipelines/).
Production uses SearchOrchestrator for direct client coordination.
"""

from omics_oracle_v2.lib.search_engines.citations.config import (
    PublicationSearchConfig, PubMedConfig)
from omics_oracle_v2.lib.search_engines.citations.models import (
    Publication, PublicationResult, PublicationSearchResult, PublicationSource)

__all__ = [
    # Models
    "Publication",
    "PublicationSearchResult",
    "PublicationResult",
    "PublicationSource",
    # Configuration
    "PubMedConfig",
    "PublicationSearchConfig",
]

__version__ = "0.1.0"
