"""
Pipeline orchestration modules.

This package contains high-level pipeline orchestrators that coordinate
multiple processing blocks to accomplish end-to-end workflows.

Pipelines:
- geo_citation_pipeline: GEO dataset search -> Citation discovery -> Full-text -> PDFs
- publication_pipeline: Publication search and metadata enrichment
"""

# Avoid circular imports - use lazy imports
__all__ = [
    "GEOCitationPipeline",
    "PublicationSearchPipeline",
]

def __getattr__(name):
    if name == "GEOCitationPipeline":
        from omics_oracle_v2.lib.pipelines.geo_citation_pipeline import GEOCitationPipeline
        return GEOCitationPipeline
    elif name == "PublicationSearchPipeline":
        from omics_oracle_v2.lib.pipelines.publication_pipeline import PublicationSearchPipeline
        return PublicationSearchPipeline
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
