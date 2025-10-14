"""
Pipeline 1: Citation Discovery
================================

Discovers scientific papers that cite GEO datasets using multiple sources.

Current Sources:
- PubMed (via E-utilities API)
- OpenAlex (via REST API)

Components:
- geo_discovery.py: Main discovery orchestrator
- clients/: API clients for each data source
"""

from omics_oracle_v2.lib.pipelines.citation_discovery.geo_discovery import GEOCitationDiscovery

__all__ = ["GEOCitationDiscovery"]
