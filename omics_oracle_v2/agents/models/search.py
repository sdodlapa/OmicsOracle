"""
Search models for Search Agent.

Defines input/output data structures for GEO dataset search operations.
"""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from ...lib.geo.models import GEOSeriesMetadata


class SearchInput(BaseModel):
    """Input for search operations."""

    search_terms: List[str] = Field(..., description="Search terms extracted from query", min_length=1)
    max_results: int = Field(default=50, description="Maximum number of results", ge=1, le=500)
    organism: Optional[str] = Field(default=None, description="Filter by organism (e.g., 'Homo sapiens')")
    study_type: Optional[str] = Field(
        default=None, description="Filter by study type (e.g., 'Expression profiling by array')"
    )
    min_samples: Optional[int] = Field(default=None, description="Minimum number of samples", ge=1)

    @field_validator("search_terms")
    @classmethod
    def validate_search_terms(cls, v: List[str]) -> List[str]:
        """Validate search terms are not empty."""
        if not v:
            raise ValueError("search_terms cannot be empty")
        # Remove empty strings
        terms = [t.strip() for t in v if t.strip()]
        if not terms:
            raise ValueError("search_terms cannot contain only empty strings")
        return terms


class RankedDataset(BaseModel):
    """Dataset with relevance ranking."""

    dataset: GEOSeriesMetadata = Field(..., description="GEO dataset")
    relevance_score: float = Field(..., description="Relevance score (0.0-1.0)", ge=0.0, le=1.0)
    match_reasons: List[str] = Field(default_factory=list, description="Reasons for relevance")

    class Config:
        """Pydantic config."""

        arbitrary_types_allowed = True


class SearchOutput(BaseModel):
    """Output from search operations."""

    datasets: List[RankedDataset] = Field(default_factory=list, description="Ranked search results")
    total_found: int = Field(..., description="Total number of results found", ge=0)
    search_terms_used: List[str] = Field(..., description="Search terms that were actually used")
    filters_applied: Dict[str, str] = Field(default_factory=dict, description="Filters that were applied")

    def get_top_datasets(self, n: int = 10) -> List[RankedDataset]:
        """
        Get top N datasets by relevance score.

        Args:
            n: Number of top datasets to return

        Returns:
            List of top N ranked datasets
        """
        return sorted(self.datasets, key=lambda d: d.relevance_score, reverse=True)[:n]

    def filter_by_score(self, min_score: float) -> List[RankedDataset]:
        """
        Filter datasets by minimum relevance score.

        Args:
            min_score: Minimum relevance score threshold

        Returns:
            List of datasets meeting the score threshold
        """
        return [d for d in self.datasets if d.relevance_score >= min_score]

    class Config:
        """Pydantic config."""

        arbitrary_types_allowed = True


__all__ = ["SearchInput", "SearchOutput", "RankedDataset"]
