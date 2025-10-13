"""
Hybrid search combining keyword and semantic search.

Provides unified search interface with configurable ranking.

NEW: SearchOrchestrator - Flat search architecture replacing nested pipelines.
"""

from omics_oracle_v2.lib.search.advanced import AdvancedSearchConfig, AdvancedSearchPipeline
from omics_oracle_v2.lib.search.advanced import SearchResult as AdvancedSearchResult
from omics_oracle_v2.lib.search.config import SearchConfig as OrchestratorConfig
from omics_oracle_v2.lib.search.hybrid import HybridSearchEngine, SearchConfig, SearchResult
from omics_oracle_v2.lib.search.models import SearchInput
from omics_oracle_v2.lib.search.models import SearchResult as OrchestratorSearchResult
from omics_oracle_v2.lib.search.orchestrator import SearchOrchestrator

__all__ = [
    # Legacy semantic search
    "HybridSearchEngine",
    "SearchConfig",
    "SearchResult",
    "AdvancedSearchPipeline",
    "AdvancedSearchConfig",
    "AdvancedSearchResult",
    # New flat orchestrator
    "SearchOrchestrator",
    "OrchestratorConfig",
    "OrchestratorSearchResult",
    "SearchInput",
]
