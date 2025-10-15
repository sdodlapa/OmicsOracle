"""
Citation search engines.

Core models and base classes for citation search.
Client implementations moved to pipelines/citation_discovery/clients/

For backward compatibility, re-export from pipelines:
"""

from omics_oracle_v2.lib.pipelines.citation_discovery.clients.openalex import \
    OpenAlexClient
from omics_oracle_v2.lib.pipelines.citation_discovery.clients.pubmed import \
    PubMedClient

__all__ = [
    "OpenAlexClient",
    "PubMedClient",
]
