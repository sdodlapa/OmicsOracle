"""
Search module for OmicsOracle.

Provides SearchOrchestrator for flat, parallel search architecture
across GEO datasets and publications (PubMed, OpenAlex, Scholar).
"""

from omics_oracle_v2.lib.search.config import SearchConfig as OrchestratorConfig
from omics_oracle_v2.lib.search.models import SearchInput
from omics_oracle_v2.lib.search.models import SearchResult as OrchestratorSearchResult
from omics_oracle_v2.lib.search.orchestrator import SearchOrchestrator

__all__ = [
    "SearchOrchestrator",
    "OrchestratorConfig",
    "OrchestratorSearchResult",
    "SearchInput",
]
