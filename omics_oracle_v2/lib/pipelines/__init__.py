"""
Pipeline orchestration modules.

This package previously contained pipeline orchestrators. All pipelines have been
archived or replaced by SearchOrchestrator for direct client coordination.

Archived pipelines (see extras/pipelines/):
- geo_citation_pipeline: GEO dataset search -> Citation discovery -> Full-text -> PDFs (unused)
- publication_pipeline: Replaced by SearchOrchestrator calling PubMedClient directly (archived)
"""

# Empty - all pipelines archived
__all__ = []
