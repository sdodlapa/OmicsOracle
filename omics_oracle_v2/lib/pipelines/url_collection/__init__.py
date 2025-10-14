"""
URL Collection Pipeline

This pipeline is responsible for collecting full-text URLs from multiple sources
in a waterfall strategy. It does NOT download or parse content - only collects URLs.

Sources (in priority order):
1. Institutional Access (GT/ODU)
2. PubMed Central (PMC)
3. OpenAlex OA URLs
4. Unpaywall
5. CORE
6. bioRxiv/medRxiv
7. arXiv
8. Crossref
9. Sci-Hub (optional, disabled by default)
10. LibGen (optional, disabled by default)

Integration Contract:
- Input: Publication object with identifiers (DOI, PMID, etc.)
- Output: FullTextResult with list of URLs (SourceURL objects)
- Each URL classified by type (PDF_DIRECT, LANDING_PAGE, etc.)

Usage:
    >>> from omics_oracle_v2.lib.pipelines.url_collection import FullTextManager
    >>>
    >>> manager = FullTextManager()
    >>> await manager.initialize()
    >>>
    >>> result = await manager.get_all_fulltext_urls(publication)
    >>> if result.success:
    >>>     print(f"Found {len(result.all_urls)} URLs")

Author: OmicsOracle Team
Created: October 14, 2025 (Pipeline Separation)
"""

from omics_oracle_v2.lib.pipelines.url_collection.manager import (
    FullTextManager,
    FullTextManagerConfig,
    FullTextResult,
    FullTextSource,
    SourceURL,
)
from omics_oracle_v2.lib.pipelines.url_collection.url_validator import URLType, URLValidator

__all__ = [
    "FullTextManager",
    "FullTextManagerConfig",
    "FullTextResult",
    "FullTextSource",
    "SourceURL",
    "URLType",
    "URLValidator",
]
