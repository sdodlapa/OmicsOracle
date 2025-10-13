"""
Search models for SearchOrchestrator.

Re-exports models from pipelines for backward compatibility.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List

from omics_oracle_v2.lib.search_engines.geo.models import GEOSeriesMetadata
from omics_oracle_v2.lib.search_engines.citations.models import Publication


@dataclass
class SearchInput:
    """Input parameters for search."""

    query: str
    search_type: str = "auto"  # auto, geo, publication, hybrid
    max_geo_results: int = 100
    max_publication_results: int = 100
    use_cache: bool = True


@dataclass
class SearchResult:
    """
    Unified search result containing both GEO datasets and publications.

    Compatible with the existing SearchResult from unified_search_pipeline.
    """

    query: str
    optimized_query: str
    query_type: str
    geo_datasets: List[GEOSeriesMetadata] = field(default_factory=list)
    publications: List[Publication] = field(default_factory=list)
    total_results: int = 0
    search_time_ms: float = 0.0
    cache_hit: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "query": self.query,
            "optimized_query": self.optimized_query,
            "query_type": self.query_type,
            "geo_datasets": [
                d.model_dump() if hasattr(d, "model_dump") else d.__dict__ for d in self.geo_datasets
            ],
            "publications": [
                p.model_dump() if hasattr(p, "model_dump") else p.__dict__ for p in self.publications
            ],
            "total_results": self.total_results,
            "search_time_ms": self.search_time_ms,
            "cache_hit": self.cache_hit,
            "metadata": self.metadata,
        }
