"""
Open Access source clients for full-text acquisition.

This package contains clients for various open access repositories
and aggregators to maximize full-text coverage for academic research.

Legal Sources (Phase 1):
- CORE: 45M+ open access papers
- arXiv: 2M+ preprints (physics, CS, math, some bio)
- bioRxiv/medRxiv: 200K+ biomedical preprints
- Crossref: Publisher full-text links

All sources are 100% legal for academic research purposes.
"""

from omics_oracle_v2.lib.publications.clients.oa_sources.arxiv_client import ArXivClient
from omics_oracle_v2.lib.publications.clients.oa_sources.biorxiv_client import BioRxivClient
from omics_oracle_v2.lib.publications.clients.oa_sources.core_client import COREClient
from omics_oracle_v2.lib.publications.clients.oa_sources.crossref_client import CrossrefClient

__all__ = ["COREClient", "BioRxivClient", "ArXivClient", "CrossrefClient"]
