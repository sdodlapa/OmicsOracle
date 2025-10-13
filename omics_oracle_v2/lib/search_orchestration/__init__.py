"""
Search orchestration module for OmicsOracle.

Provides SearchOrchestrator for flat, parallel search architecture
across GEO datasets and publications (PubMed, OpenAlex, Scholar).
"""

from omics_oracle_v2.lib.search_orchestration.config import SearchConfig as OrchestratorConfig
from omics_oracle_v2.lib.search_orchestration.models import SearchInput
from omics_oracle_v2.lib.search_orchestration.models import SearchResult as OrchestratorSearchResult
from omics_oracle_v2.lib.search_orchestration.orchestrator import SearchOrchestrator

__all__ = [
    "SearchOrchestrator",
    "OrchestratorConfig",
    "OrchestratorSearchResult",
    "SearchInput",
]
