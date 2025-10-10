"""
Workflows package

High-level workflows that orchestrate multiple components.
"""

from omics_oracle_v2.lib.workflows.geo_citation_pipeline import (
    CollectionResult,
    GEOCitationConfig,
    GEOCitationPipeline,
)

__all__ = [
    "GEOCitationPipeline",
    "GEOCitationConfig",
    "CollectionResult",
]
