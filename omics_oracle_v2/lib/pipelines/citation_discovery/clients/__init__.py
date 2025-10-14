"""
Citation Discovery API Clients
===============================

API clients for retrieving citation data from various sources.

Available Clients:
- OpenAlexClient: Access to OpenAlex citation database
- PubMedClient: Access to PubMed/NCBI citations
"""

from omics_oracle_v2.lib.pipelines.citation_discovery.clients.openalex import OpenAlexClient
from omics_oracle_v2.lib.pipelines.citation_discovery.clients.pubmed import PubMedClient

__all__ = ["OpenAlexClient", "PubMedClient"]
