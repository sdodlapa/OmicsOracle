"""
Citation search engines.

Individual clients for retrieving citation data from various sources.
"""

from omics_oracle_v2.lib.search_engines.citations.openalex import OpenAlexClient
from omics_oracle_v2.lib.search_engines.citations.scholar import GoogleScholarClient
from omics_oracle_v2.lib.search_engines.citations.semantic_scholar import SemanticScholarClient

__all__ = [
    "OpenAlexClient",
    "SemanticScholarClient",
    "GoogleScholarClient",
]
