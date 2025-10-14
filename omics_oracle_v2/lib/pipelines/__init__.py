"""
Pipeline Organization
=====================

This package contains the three main pipelines of OmicsOracle:

1. citation_discovery/    - Discovers papers that cite GEO datasets
2. citation_url_collection/ - Collects URLs for downloading papers
3. citation_download/     - Downloads PDFs from collected URLs

Each pipeline is independent and can be used separately.
"""

# Convenience imports for backward compatibility
from omics_oracle_v2.lib.pipelines.citation_discovery.geo_discovery import GEOCitationDiscovery
from omics_oracle_v2.lib.pipelines.citation_download.download_manager import PDFDownloadManager
from omics_oracle_v2.lib.pipelines.citation_url_collection.manager import FullTextManager

__all__ = [
    "GEOCitationDiscovery",
    "FullTextManager",
    "PDFDownloadManager",
]
