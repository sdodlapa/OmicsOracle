"""
Full-text source clients.

Individual clients for retrieving full-text content from various sources.
"""

from omics_oracle_v2.lib.fulltext.sources.libgen_client import LibGenClient
from omics_oracle_v2.lib.fulltext.sources.scihub_client import SciHubClient

__all__ = [
    "SciHubClient",
    "LibGenClient",
]
