"""
Full-Text Enrichment Module

This module handles full-text PDF retrieval and text extraction from multiple sources.

Key Components:
- FullTextManager: Coordinates PDF retrieval from 11+ sources
- Download Manager: Manages PDF downloads with retry logic
- Cache System: Multi-tier caching for fulltext content
- Source Clients: ArXiv, bioRxiv, CORE, Crossref, Unpaywall, PMC, SciHub, LibGen

Stages 6-8: Full-text enrichment pipeline
"""

from omics_oracle_v2.lib.enrichment.fulltext.manager import (
    FullTextManager,
    FullTextManagerConfig,
    FullTextResult,
    FullTextSource,
    SourceURL,
)

__all__ = [
    "FullTextManager",
    "FullTextManagerConfig",
    "FullTextResult",
    "FullTextSource",
    "SourceURL",
]
