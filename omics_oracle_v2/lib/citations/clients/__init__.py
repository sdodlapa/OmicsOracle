"""
Citation API clients.

Individual clients for retrieving citation data from various sources.
"""

from omics_oracle_v2.lib.citations.clients.openalex import OpenAlexClient
from omics_oracle_v2.lib.citations.clients.semantic_scholar import SemanticScholarClient
from omics_oracle_v2.lib.citations.clients.scholar import GoogleScholarClient

__all__ = [
    "OpenAlexClient",
    "SemanticScholarClient",
    "GoogleScholarClient",
]
