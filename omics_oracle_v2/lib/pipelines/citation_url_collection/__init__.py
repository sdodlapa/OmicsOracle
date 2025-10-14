"""
Pipeline 2: Citation URL Collection
====================================

Collects URLs for downloading papers from 11+ sources.

Sources:
- Institutional repositories
- PMC/Europe PMC
- Unpaywall
- CORE
- OpenAlex
- Crossref
- bioRxiv/medRxiv
- arXiv
- Sci-Hub
- Library Genesis
- And more...

Components:
- manager.py: Main URL collection orchestrator
- sources/: Individual source implementations
"""

from omics_oracle_v2.lib.pipelines.citation_url_collection.manager import FullTextManager

__all__ = ["FullTextManager"]
