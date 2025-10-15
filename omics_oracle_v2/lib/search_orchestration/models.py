"""
Search models for SearchOrchestrator.

Re-exports models from pipelines for backward compatibility.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from omics_oracle_v2.lib.search_engines.citations.models import Publication
from omics_oracle_v2.lib.search_engines.geo.models import GEOSeriesMetadata


@dataclass
class QueryProcessingContext:
    """Query processing context from QueryOptimizer for RAG enhancement."""

    extracted_entities: Dict[str, List[str]] = field(default_factory=dict)
    expanded_terms: List[str] = field(default_factory=list)
    geo_search_terms: List[str] = field(default_factory=list)
    search_intent: Optional[str] = None
    query_type: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "extracted_entities": self.extracted_entities,
            "expanded_terms": self.expanded_terms,
            "geo_search_terms": self.geo_search_terms,
            "search_intent": self.search_intent,
            "query_type": self.query_type,
        }


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
    query_processing: Optional[QueryProcessingContext] = None  # RAG Phase 3

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
            "query_processing": self.query_processing.to_dict() if self.query_processing else None,
        }
