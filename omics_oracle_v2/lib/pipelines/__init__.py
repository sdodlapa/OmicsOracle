"""
Pipeline Organization
=====================

This package contains Pipeline 1 (Citation Discovery):

1. citation_discovery/    - Discovers papers that cite GEO datasets
   - Uses 5 sources: PubMed, OpenAlex, Semantic Scholar, Europe PMC, OpenCitations
   - Includes quality validation (Phase 9)
   - Includes metrics logging (Phase 10)

Note: Pipeline 2 (URL Collection) and Pipeline 3 (PDF Download) are in:
- omics_oracle_v2.lib.enrichment.fulltext.manager (FullTextManager)
- omics_oracle_v2.lib.enrichment.fulltext.download_manager (PDFDownloadManager)

These are the ACTIVE implementations used by the API.
"""

# Convenience imports for backward compatibility
from omics_oracle_v2.lib.pipelines.citation_discovery.geo_discovery import GEOCitationDiscovery

# NOTE: FullTextManager and PDFDownloadManager have moved to enrichment/fulltext/
# Import them from there:
# from omics_oracle_v2.lib.enrichment.fulltext.manager import FullTextManager
# from omics_oracle_v2.lib.enrichment.fulltext.download_manager import PDFDownloadManager

__all__ = [
    "GEOCitationDiscovery",
]
