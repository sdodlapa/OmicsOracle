"""
Workflows package

High-level workflows that orchestrate multiple components.
"""

from omics_oracle_v2.lib.workflows.geo_citation_pipeline import (
    GEOCitationPipeline,
    GEOCitationConfig,
    CollectionResult,
)

__all__ = [
    "GEOCitationPipeline",
    "GEOCitationConfig",
    "CollectionResult",
]
