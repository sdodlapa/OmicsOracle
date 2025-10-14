"""
Citation Discovery API Clients
===============================

API clients for retrieving citation data from various sources.

Available Clients:
- OpenAlexClient: Access to OpenAlex citation database
- PubMedClient: Access to PubMed/NCBI citations
- SemanticScholarClient: Access to Semantic Scholar citation database (NEW!)
"""

from omics_oracle_v2.lib.pipelines.citation_discovery.clients.openalex import (
    OpenAlexClient,
)
from omics_oracle_v2.lib.pipelines.citation_discovery.clients.pubmed import (
    PubMedClient,
)
from omics_oracle_v2.lib.pipelines.citation_discovery.clients.semantic_scholar import (
    SemanticScholarClient,
)

__all__ = ["OpenAlexClient", "PubMedClient", "SemanticScholarClient"]
