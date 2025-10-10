"""
Pipeline orchestration modules.

This package contains high-level pipeline orchestrators that coordinate
multiple processing blocks to accomplish end-to-end workflows.

Pipelines:
- geo_citation_pipeline: GEO dataset search -> Citation discovery -> Full-text -> PDFs
- publication_pipeline: Publication search and metadata enrichment
"""

from omics_oracle_v2.lib.pipelines.geo_citation_pipeline import GEOCitationPipeline
from omics_oracle_v2.lib.pipelines.publication_pipeline import PublicationSearchPipeline

__all__ = [
    "GEOCitationPipeline",
    "PublicationSearchPipeline",
]
