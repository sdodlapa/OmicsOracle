"""Open Access (OA) source clients."""

from omics_oracle_v2.lib.pipelines.url_collection.sources.oa_sources.arxiv_client import ArXivClient
from omics_oracle_v2.lib.pipelines.url_collection.sources.oa_sources.biorxiv_client import BioRxivClient
from omics_oracle_v2.lib.pipelines.url_collection.sources.oa_sources.core_client import COREClient
from omics_oracle_v2.lib.pipelines.url_collection.sources.oa_sources.crossref_client import CrossrefClient
from omics_oracle_v2.lib.pipelines.url_collection.sources.oa_sources.pmc_client import PMCClient, PMCConfig
from omics_oracle_v2.lib.pipelines.url_collection.sources.oa_sources.unpaywall_client import (
    UnpaywallClient,
    UnpaywallConfig,
)

from omics_oracle_v2.lib.enrichment.fulltext.sources.oa_sources.arxiv_client import ArXivClient
from omics_oracle_v2.lib.enrichment.fulltext.sources.oa_sources.biorxiv_client import BioRxivClient
from omics_oracle_v2.lib.enrichment.fulltext.sources.oa_sources.core_client import COREClient
from omics_oracle_v2.lib.enrichment.fulltext.sources.oa_sources.crossref_client import CrossrefClient
from omics_oracle_v2.lib.enrichment.fulltext.sources.oa_sources.pmc_client import PMCClient, PMCConfig
from omics_oracle_v2.lib.enrichment.fulltext.sources.oa_sources.unpaywall_client import (
    UnpaywallClient,
    UnpaywallConfig,
)

__all__ = [
    "ArXivClient",
    "BioRxivClient",
    "COREClient",
    "CrossrefClient",
    "PMCClient",
    "PMCConfig",
    "UnpaywallClient",
    "UnpaywallConfig",
]
