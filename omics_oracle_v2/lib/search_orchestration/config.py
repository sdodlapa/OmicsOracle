"""
Simplified search configuration for SearchOrchestrator.

This replaces the complex UnifiedSearchConfig with a cleaner, more focused configuration.
"""

import os
from dataclasses import dataclass
from typing import Optional

from omics_oracle_v2.lib.publications.clients.pubmed import PubMedConfig


@dataclass
class SearchConfig:
    """
    Configuration for SearchOrchestrator.

    Simplified from UnifiedSearchConfig - focuses on essential settings.
    """

    # Search sources
    enable_geo: bool = True
    enable_pubmed: bool = True
    enable_openalex: bool = True
    enable_scholar: bool = False  # Often rate-limited, disabled by default

    # Query optimization
    enable_query_optimization: bool = True
    enable_ner: bool = True
    enable_sapbert: bool = True

    # Caching
    enable_cache: bool = True
    cache_host: str = "localhost"
    cache_port: int = 6379
    cache_db: int = 0
    cache_ttl: int = 86400  # 24 hours

    # Result limits
    max_geo_results: int = 100
    max_publication_results: int = 100

    # Client configs
    pubmed_config: Optional[PubMedConfig] = None
    openalex_email: Optional[str] = None  # For polite pool

    # Feature flags (for future expansion)
    enable_citations: bool = False
    enable_fulltext: bool = False

    def __post_init__(self):
        """Initialize default configs if not provided."""
        if self.pubmed_config is None:
            self.pubmed_config = PubMedConfig(
                email=os.getenv("NCBI_EMAIL", "sdodl001@odu.edu"),
                api_key=os.getenv("NCBI_API_KEY"),
            )
