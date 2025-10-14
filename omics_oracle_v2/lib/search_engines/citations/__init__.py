"""
Citation search engines.

Individual clients for retrieving citation data from various sources.
"""

from omics_oracle_v2.lib.search_engines.citations.openalex import OpenAlexClient
from omics_oracle_v2.lib.search_engines.citations.pubmed import PubMedClient

__all__ = [
    "OpenAlexClient",
    "PubMedClient",
]
