"""
Citation discovery modules.

Handles finding papers that cite a given publication.
"""

from omics_oracle_v2.lib.citations.discovery.geo_discovery import (
    CitationDiscoveryResult,
    GEOCitationDiscovery,
)

__all__ = [
    "GEOCitationDiscovery",
    "CitationDiscoveryResult",
]
