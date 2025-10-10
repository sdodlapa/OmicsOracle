"""
Full-text source clients.

Individual clients for retrieving full-text content from various sources.
"""

from omics_oracle_v2.lib.fulltext.sources.scihub_client import SciHubClient
from omics_oracle_v2.lib.fulltext.sources.libgen_client import LibGenClient

__all__ = [
    "SciHubClient",
    "LibGenClient",
]
