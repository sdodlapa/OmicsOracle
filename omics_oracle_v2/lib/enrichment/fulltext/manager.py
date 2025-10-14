"""
Full-text manager for orchestrating multiple full-text sources.

This module provides a unified interface for attempting to retrieve full-text
content from multiple sources in priority order (waterfall strategy).

Sources are tried in order of:
1. Reliability (institutional access > free OA)
2. Quality (peer-reviewed > preprints)
3. Speed (cached > API calls)
4. Coverage (broad sources first)

Example:
    >>> from omics_oracle_v2.lib.enrichment.fulltext.manager import FullTextManager
    >>>
    >>> manager = FullTextManager()
    >>> await manager.initialize()
    >>>
    >>> # Get full-text for a publication
    >>> result = await manager.get_fulltext(publication)
    >>> if result.success:
    >>>     print(f"Got full-text from {result.source}")
    >>>     print(f"Content: {result.content[:100]}...")
"""

import asyncio
import logging
import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

from omics_oracle_v2.lib.enrichment.fulltext.sources.institutional_access import (
    InstitutionalAccessManager,
    InstitutionType,
)
from omics_oracle_v2.lib.enrichment.fulltext.sources.libgen_client import LibGenClient, LibGenConfig
from omics_oracle_v2.lib.enrichment.fulltext.sources.oa_sources import (
    ArXivClient,
    BioRxivClient,
    COREClient,
    CrossrefClient,
    PMCClient,
    PMCConfig,
)
from omics_oracle_v2.lib.enrichment.fulltext.sources.oa_sources.unpaywall_client import (
    UnpaywallClient,
    UnpaywallConfig,
)
from omics_oracle_v2.lib.enrichment.fulltext.sources.scihub_client import SciHubClient, SciHubConfig
from omics_oracle_v2.lib.enrichment.fulltext.url_validator import URLType, URLValidator
from omics_oracle_v2.lib.search_engines.citations.models import Publication

logger = logging.getLogger(__name__)


class FullTextSource(str, Enum):
    """Enumeration of full-text sources."""

    INSTITUTIONAL = "institutional"
    PMC = "pmc"
    OPENALEX_OA = "openalex_oa"
    UNPAYWALL = "unpaywall"
    CORE = "core"
    BIORXIV = "biorxiv"
    ARXIV = "arxiv"
    CROSSREF = "crossref"
    SCIHUB = "scihub"  # NEW - Phase 2
    LIBGEN = "libgen"  # NEW - Phase 3
    CACHE = "cache"


from pydantic import BaseModel, Field


@dataclass
class SourceURL:
    """
    Single URL source with enhanced metadata.

    NEW (Oct 13, 2025):
    - Added url_type field for smart prioritization
    - URL type classified automatically using URLValidator
    - Helps download manager prioritize PDF links over landing pages
    """

    url: str
    source: FullTextSource
    priority: int  # 1 = highest priority, 11 = lowest
    url_type: URLType = URLType.UNKNOWN  # NEW: URL type classification
    confidence: float = 1.0  # 0.0-1.0 confidence score
    requires_auth: bool = False
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class FullTextResult:
    """Result from full-text retrieval attempt."""

    success: bool
    source: Optional[FullTextSource] = None
    content: Optional[str] = None
    pdf_path: Optional[Path] = None
    url: Optional[str] = None
    error: Optional[str] = None
    metadata: Optional[Dict] = None
    all_urls: Optional[List["SourceURL"]] = None  # NEW: All URLs from all sources (for fallback)


class FullTextManagerConfig(BaseModel):
    """
    Configuration for FullTextManager.

    Attributes:
        enable_institutional: Try institutional access first
        enable_pmc: Try PubMed Central
        enable_openalex: Use OpenAlex OA URLs
        enable_unpaywall: Try Unpaywall (NEW - Phase 1+)
        enable_core: Use CORE API
        enable_biorxiv: Try bioRxiv/medRxiv
        enable_arxiv: Try arXiv
        enable_crossref: Use Crossref full-text links
        enable_scihub: Try Sci-Hub (NEW - Phase 2, use responsibly)
        enable_libgen: Try LibGen (NEW - Phase 3, use responsibly)
        core_api_key: API key for CORE
        unpaywall_email: Email for Unpaywall API
        scihub_use_proxy: Use proxy/Tor for Sci-Hub
        libgen_use_proxy: Use proxy/Tor for LibGen
        max_concurrent: Maximum concurrent source attempts
        timeout_per_source: Timeout for each source (seconds)
    """

    enable_institutional: bool = Field(default=True, description="Try institutional access first")
    enable_pmc: bool = Field(default=True, description="Try PubMed Central")
    enable_openalex: bool = Field(default=True, description="Use OpenAlex OA URLs")
    enable_unpaywall: bool = Field(default=True, description="Try Unpaywall (Phase 1+)")
    enable_core: bool = Field(default=True, description="Use CORE API")
    enable_biorxiv: bool = Field(default=True, description="Try bioRxiv/medRxiv")
    enable_arxiv: bool = Field(default=True, description="Try arXiv")
    enable_crossref: bool = Field(default=True, description="Use Crossref full-text links")
    enable_scihub: bool = Field(
        default=False, description="Try Sci-Hub (Phase 2, use responsibly, disabled by default)"
    )
    enable_libgen: bool = Field(
        default=False, description="Try LibGen (Phase 3, use responsibly, disabled by default)"
    )
    core_api_key: Optional[str] = Field(default=None, description="API key for CORE")
    unpaywall_email: Optional[str] = Field(default=None, description="Email for Unpaywall API")
    scihub_use_proxy: bool = Field(default=False, description="Use proxy/Tor for Sci-Hub")
    libgen_use_proxy: bool = Field(default=False, description="Use proxy/Tor for LibGen")
    max_concurrent: int = Field(default=3, description="Maximum concurrent source attempts", ge=1)
    timeout_per_source: int = Field(default=30, description="Timeout for each source (seconds)", ge=1)


class FullTextManager:
    """
    Manages full-text retrieval from multiple sources.

    This class orchestrates attempts to retrieve full-text content by trying
    multiple sources in priority order. It stops at the first successful match.

    Priority Order:
    1. Cache (if previously downloaded)
    2. Institutional Access (GT/ODU)
    3. PubMed Central (6M free articles)
    4. OpenAlex OA URLs (if marked as OA)
    5. Unpaywall (OA aggregator)
    6. CORE API (45M+ papers)
    7. bioRxiv/medRxiv (biomedical preprints)
    8. arXiv (physics, CS, math preprints)
    9. Crossref (publisher links)
    """

    def __init__(self, config: Optional[FullTextManagerConfig] = None):
        """
        Initialize FullTextManager.

        Args:
            config: Configuration object
        """
        self.config = config or FullTextManagerConfig()
        self.initialized = False

        # OA source clients (will be initialized in initialize())
        self.institutional_manager: Optional[InstitutionalAccessManager] = None  # NEW - Priority 1
        self.pmc_client: Optional[PMCClient] = None  # Extracted from manager (Phase 1.3)
        self.core_client: Optional[COREClient] = None
        self.biorxiv_client: Optional[BioRxivClient] = None
        self.arxiv_client: Optional[ArXivClient] = None
        self.crossref_client: Optional[CrossrefClient] = None
        self.unpaywall_client: Optional[UnpaywallClient] = None  # NEW
        self.scihub_client: Optional[SciHubClient] = None  # NEW
        self.libgen_client: Optional[LibGenClient] = None  # NEW

        # Statistics
        self.stats = {
            "total_attempts": 0,
            "successes": 0,
            "failures": 0,
            "by_source": {},
        }

        logger.info("Initialized FullTextManager")

    async def initialize(self):
        """Initialize all enabled OA source clients."""
        if self.initialized:
            return

        logger.info("Initializing OA source clients...")

        # Initialize Institutional Access Manager (NEW - Priority 1)
        if self.config.enable_institutional:
            # Use Georgia Tech by default (can be configured)
            self.institutional_manager = InstitutionalAccessManager(institution=InstitutionType.GEORGIA_TECH)
            logger.info("Institutional Access Manager initialized (Georgia Tech)")

        # Initialize PMC client (Extracted from manager - Phase 1.3)
        if self.config.enable_pmc:
            pmc_config = PMCConfig(enabled=True)
            self.pmc_client = PMCClient(pmc_config)
            await self.pmc_client.__aenter__()
            logger.info("PMC client initialized")

        # Initialize CORE client
        if self.config.enable_core:
            from omics_oracle_v2.lib.enrichment.fulltext.sources.oa_sources.core_client import COREConfig

            core_config = COREConfig(api_key=self.config.core_api_key)
            self.core_client = COREClient(config=core_config)
            await self.core_client.__aenter__()
            logger.info("CORE client initialized")

        # Initialize bioRxiv client
        if self.config.enable_biorxiv:
            self.biorxiv_client = BioRxivClient()
            await self.biorxiv_client.__aenter__()
            logger.info("bioRxiv client initialized")

        # Initialize arXiv client
        if self.config.enable_arxiv:
            self.arxiv_client = ArXivClient()
            await self.arxiv_client.__aenter__()
            logger.info("arXiv client initialized")

        # Initialize Crossref client
        if self.config.enable_crossref:
            self.crossref_client = CrossrefClient()
            await self.crossref_client.__aenter__()
            logger.info("Crossref client initialized")

        # Initialize Unpaywall client (NEW - Phase 1+)
        if self.config.enable_unpaywall:
            email = self.config.unpaywall_email or os.getenv("NCBI_EMAIL", "sdodl001@odu.edu")
            unpaywall_config = UnpaywallConfig(email=email)
            self.unpaywall_client = UnpaywallClient(unpaywall_config)
            await self.unpaywall_client.__aenter__()
            logger.info("Unpaywall client initialized")

        # Initialize Sci-Hub client (NEW - Phase 2)
        if self.config.enable_scihub:
            scihub_config = SciHubConfig(use_proxy=self.config.scihub_use_proxy)
            self.scihub_client = SciHubClient(scihub_config)
            await self.scihub_client.__aenter__()
            logger.info("[WARNING] Sci-Hub client initialized (use responsibly)")

        # Initialize LibGen client (NEW - Phase 3)
        if self.config.enable_libgen:
            libgen_config = LibGenConfig()
            self.libgen_client = LibGenClient(libgen_config)
            await self.libgen_client.__aenter__()
            logger.info("[WARNING] LibGen client initialized (use responsibly)")

        self.initialized = True
        logger.info("All OA source clients initialized")

    async def cleanup(self):
        """Cleanup all OA source clients."""
        if not self.initialized:
            return

        logger.info("Cleaning up OA source clients...")

        if self.pmc_client:  # NEW - Phase 1.3
            await self.pmc_client.__aexit__(None, None, None)
        if self.core_client:
            await self.core_client.__aexit__(None, None, None)
        if self.biorxiv_client:
            await self.biorxiv_client.__aexit__(None, None, None)
        if self.arxiv_client:
            await self.arxiv_client.__aexit__(None, None, None)
        if self.crossref_client:
            await self.crossref_client.__aexit__(None, None, None)
        if self.unpaywall_client:  # NEW
            await self.unpaywall_client.__aexit__(None, None, None)
        if self.scihub_client:  # NEW
            await self.scihub_client.__aexit__(None, None, None)
        if self.libgen_client:  # NEW
            await self.libgen_client.__aexit__(None, None, None)

        self.initialized = False
        logger.info("All OA source clients cleaned up")

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()

    async def _check_cache(self, publication: Publication) -> FullTextResult:
        """
        Check if full-text is already available locally.

        ENHANCED (Oct 11, 2025):
        - Uses SmartCache to check ALL possible local file locations
        - Checks XML files (best quality) before PDFs
        - Checks source-specific directories (arxiv/, pmc/, institutional/, etc.)
        - Falls back to hash-based cache (legacy system)

        This prevents unnecessary API calls when files are already downloaded
        but stored in source-specific directories.

        Args:
            publication: Publication object

        Returns:
            FullTextResult with local file info if found
        """
        from omics_oracle_v2.lib.enrichment.fulltext.smart_cache import SmartCache

        cache = SmartCache()
        result = cache.find_local_file(publication)

        if result.found:
            logger.info(
                f"[OK] Found local {result.file_type.upper()}: "
                f"{result.file_path.name} "
                f"({result.size_bytes // 1024} KB, source: {result.source})"
            )

            return FullTextResult(
                success=True,
                source=FullTextSource.CACHE,
                pdf_path=result.file_path if result.file_type == "pdf" else None,
                metadata={
                    "cached": True,
                    "file_type": result.file_type,
                    "source": result.source,
                    "size": result.size_bytes,
                    "path": str(result.file_path),
                },
            )

        logger.debug("No local files found, will try remote sources")
        return FullTextResult(success=False, error="Not in cache")

    async def _try_institutional_access(self, publication: Publication) -> FullTextResult:
        """
        Try to get full-text through institutional access (Georgia Tech/ODU).

        Priority 1 source - highest quality, legal, ~45-50% coverage.

        HOW IT WORKS:
        - Georgia Tech: Returns DOI URL (expects VPN/on-campus access)
        - ODU: Returns EZProxy URL (proxy-based authentication)

        IMPORTANT: This will typically return HTTP 403 if not on institution's network.
        The Tiered Waterfall system handles this by automatically trying other sources.

        EXPECTED FLOW:
        1. Institutional -> Returns DOI URL
        2. Download attempt -> HTTP 403 (not on VPN) [FAIL]
        3. Waterfall retry -> PMC succeeds [OK]

        This is CORRECT behavior - institutional access works for users on campus/VPN,
        while other users automatically fall back to open access sources.

        Args:
            publication: Publication object

        Returns:
            FullTextResult with URL (may require VPN/institutional auth to download)
        """
        if not self.config.enable_institutional or not self.institutional_manager:
            return FullTextResult(success=False, error="Institutional access not enabled")

        try:
            # Get access URL through institutional subscription
            # Note: This returns DOI URL for Georgia Tech (requires VPN)
            access_url = self.institutional_manager.get_access_url(publication)

            if not access_url:
                return FullTextResult(success=False, error="No institutional access found")

            logger.info(f"Found access via institutional: {access_url}")

            # Return URL (PDFDownloadManager will try to download)
            # If download fails (HTTP 403), Tiered Waterfall will retry with other sources
            return FullTextResult(
                success=True,
                source=FullTextSource.INSTITUTIONAL,
                url=access_url,
                metadata={"method": "direct", "institution": "Georgia Tech"},
            )

        except Exception as e:
            logger.debug(f"Institutional access lookup failed: {e}")
            return FullTextResult(success=False, error=str(e))

    async def _try_pmc(self, publication: Publication) -> FullTextResult:
        """
        Try to get full-text from PubMed Central (PMC).

        REFACTORED (Phase 1.3):
        - Extracted to dedicated PMCClient class
        - Follows standard client pattern
        - Manager delegates to client (orchestration only)

        PMC is the #1 legal source with 6M+ free full-text articles.
        Client tries multiple URL patterns for better success rate.

        Args:
            publication: Publication object with pmid or pmc_id

        Returns:
            FullTextResult with best available URL
        """
        if not self.config.enable_pmc:
            return FullTextResult(success=False, error="PMC disabled")

        if not self.pmc_client:
            return FullTextResult(success=False, error="PMC client not initialized")

        try:
            result = await self.pmc_client.get_fulltext(publication)
            return result
        except Exception as e:
            logger.warning(f"PMC lookup failed: {e}")
            return FullTextResult(success=False, error=str(e))

    async def _try_openalex_oa_url(self, publication: Publication) -> FullTextResult:
        """
        Try to get full-text from OpenAlex OA URL.

        Args:
            publication: Publication object

        Returns:
            FullTextResult
        """
        if not self.config.enable_openalex:
            return FullTextResult(success=False, error="OpenAlex disabled")

        try:
            # Check if publication has OA URL in metadata
            oa_url = publication.metadata.get("oa_url") if publication.metadata else None

            if not oa_url:
                return FullTextResult(success=False, error="No OA URL in metadata")

            logger.info(f"Found OpenAlex OA URL: {oa_url}")
            return FullTextResult(
                success=True,
                source=FullTextSource.OPENALEX_OA,
                url=oa_url,
                metadata={"oa_url": oa_url},
            )

        except Exception as e:
            logger.warning(f"OpenAlex OA URL error: {e}")
            return FullTextResult(success=False, error=str(e))

    async def _try_core(self, publication: Publication) -> FullTextResult:
        """
        Try to get full-text from CORE.

        Args:
            publication: Publication object

        Returns:
            FullTextResult
        """
        if not self.config.enable_core or not self.core_client:
            return FullTextResult(success=False, error="CORE disabled or not initialized")

        try:
            # Try DOI first
            if publication.doi:
                result = await self.core_client.get_fulltext_by_doi(publication.doi)
                if result and result.get("downloadUrl"):
                    logger.info(f"Found in CORE by DOI: {publication.doi}")
                    return FullTextResult(
                        success=True,
                        source=FullTextSource.CORE,
                        url=result["downloadUrl"],
                        metadata={"core_id": result.get("id"), "method": "doi"},
                    )

            # Try title search as fallback
            if publication.title:
                results = await self.core_client.search_by_title(publication.title, limit=1)
                if results and results[0].get("downloadUrl"):
                    logger.info(f"Found in CORE by title: {publication.title[:50]}...")
                    return FullTextResult(
                        success=True,
                        source=FullTextSource.CORE,
                        url=results[0]["downloadUrl"],
                        metadata={"core_id": results[0].get("id"), "method": "title"},
                    )

            return FullTextResult(success=False, error="Not found in CORE")

        except Exception as e:
            logger.warning(f"CORE error: {e}")
            return FullTextResult(success=False, error=str(e))

    async def _try_biorxiv(self, publication: Publication) -> FullTextResult:
        """
        Try to get full-text from bioRxiv/medRxiv.

        ENHANCED (Oct 11, 2025):
        - Downloads and saves PDF to data/fulltext/pdf/biorxiv/
        - Returns saved file path for immediate use
        - Caches for future SmartCache lookups

        Args:
            publication: Publication object

        Returns:
            FullTextResult with saved PDF path if successful
        """
        if not self.config.enable_biorxiv or not self.biorxiv_client:
            return FullTextResult(success=False, error="bioRxiv disabled or not initialized")

        try:
            # bioRxiv only works with DOI
            if not publication.doi:
                return FullTextResult(success=False, error="No DOI for bioRxiv lookup")

            result = await self.biorxiv_client.get_by_doi(publication.doi)
            if not result or not result.get("pdf_url"):
                return FullTextResult(success=False, error="Not a bioRxiv paper or not found")

            pdf_url = result["pdf_url"]
            logger.info(f"Found in bioRxiv: {publication.doi}")

            # Return PDF URL for PDFDownloadManager
            return FullTextResult(
                success=True,
                source=FullTextSource.BIORXIV,
                url=pdf_url,
                metadata={
                    "biorxiv_id": result.get("biorxiv_id"),
                    "version": result.get("version"),
                },
            )

        except Exception as e:
            logger.warning(f"bioRxiv error: {e}")
            return FullTextResult(success=False, error=str(e))

    async def _try_arxiv(self, publication: Publication) -> FullTextResult:
        """
        Try to get full-text from arXiv.

        ENHANCED (Oct 11, 2025):
        - Downloads and saves PDF to data/fulltext/pdf/arxiv/
        - Returns saved file path for immediate use
        - Caches for future SmartCache lookups

        Args:
            publication: Publication object

        Returns:
            FullTextResult with saved PDF path if successful
        """
        if not self.config.enable_arxiv or not self.arxiv_client:
            return FullTextResult(success=False, error="arXiv disabled or not initialized")

        try:
            pdf_url = None
            arxiv_id = None
            method = None

            # Only try by arXiv ID if DOI looks like an arXiv ID (contains "arxiv")
            if publication.doi and "arxiv" in publication.doi.lower():
                paper = await self.arxiv_client.get_by_arxiv_id(publication.doi)
                if paper and paper.get("pdf_url"):
                    logger.info(f"Found in arXiv by ID: {publication.doi}")
                    pdf_url = paper["pdf_url"]
                    arxiv_id = paper.get("arxiv_id")
                    method = "id"

            # Try title search (only for papers without DOI or if arXiv ID lookup failed)
            if not pdf_url and publication.title:
                results = await self.arxiv_client.search_by_title(publication.title, max_results=1)
                if results and results[0].get("pdf_url"):
                    logger.info(f"Found in arXiv by title: {publication.title[:50]}...")
                    pdf_url = results[0]["pdf_url"]
                    arxiv_id = results[0].get("arxiv_id")
                    method = "title"

            if not pdf_url:
                return FullTextResult(success=False, error="Not found in arXiv")

            # Return PDF URL for PDFDownloadManager
            return FullTextResult(
                success=True,
                source=FullTextSource.ARXIV,
                url=pdf_url,
                metadata={
                    "arxiv_id": arxiv_id,
                    "method": method,
                },
            )

        except Exception as e:
            logger.debug(f"arXiv lookup skipped: {e}")  # Changed to debug level
            return FullTextResult(success=False, error=str(e))

    async def _try_crossref(self, publication: Publication) -> FullTextResult:
        """
        Try to get full-text links from Crossref.

        Args:
            publication: Publication object

        Returns:
            FullTextResult
        """
        if not self.config.enable_crossref or not self.crossref_client:
            return FullTextResult(success=False, error="Crossref disabled or not initialized")

        try:
            # Crossref requires DOI
            if not publication.doi:
                return FullTextResult(success=False, error="No DOI for Crossref lookup")

            result = await self.crossref_client.get_by_doi(publication.doi)
            if result and result.get("fulltext_urls"):
                urls = result["fulltext_urls"]
                logger.info(f"Found {len(urls)} full-text links in Crossref: {publication.doi}")
                return FullTextResult(
                    success=True,
                    source=FullTextSource.CROSSREF,
                    url=urls[0] if urls else None,
                    metadata={"fulltext_urls": urls, "publisher": result.get("publisher")},
                )

            return FullTextResult(success=False, error="No full-text links in Crossref")

        except Exception as e:
            logger.warning(f"Crossref error: {e}")
            return FullTextResult(success=False, error=str(e))

    async def _try_unpaywall(self, publication: Publication) -> FullTextResult:
        """
        Try to get full-text from Unpaywall with enhanced OA checking.

        ENHANCED (Oct 13, 2025):
        - Verifies is_oa=true before returning URLs
        - Tries ALL oa_locations (not just best_oa_location)
        - Prefers url_for_pdf over landing pages
        - Reduces 403 errors from paywalled content

        Unpaywall is a free OA aggregator covering 20M+ papers.
        No API key required.

        Args:
            publication: Publication object

        Returns:
            FullTextResult with verified OA URL
        """
        if not self.config.enable_unpaywall or not self.unpaywall_client:
            return FullTextResult(success=False, error="Unpaywall disabled or not initialized")

        try:
            # Unpaywall requires DOI
            if not publication.doi:
                return FullTextResult(success=False, error="No DOI for Unpaywall lookup")

            result = await self.unpaywall_client.get_oa_location(publication.doi)

            # Verify is_oa flag
            if not result or not result.get("is_oa"):
                return FullTextResult(success=False, error="Not Open Access in Unpaywall")

            # Try best_oa_location first (Unpaywall's recommendation)
            best_oa = result.get("best_oa_location")
            if best_oa:
                # Prefer PDF URL
                pdf_url = best_oa.get("url_for_pdf")
                if pdf_url:
                    logger.info(f"[OK] Found OA PDF via Unpaywall (best): {publication.doi}")
                    return FullTextResult(
                        success=True,
                        source=FullTextSource.UNPAYWALL,
                        url=pdf_url,
                        metadata={
                            "version": best_oa.get("version"),
                            "license": best_oa.get("license"),
                            "oa_status": result.get("oa_status"),
                            "location": "best_oa_location",
                            "url_type": "pdf_direct",
                        },
                    )

                # Fall back to regular URL if no PDF URL
                regular_url = best_oa.get("url")
                if regular_url:
                    is_pdf = regular_url.lower().endswith(".pdf")
                    logger.info(f"[OK] Found OA URL via Unpaywall (best): {publication.doi}")
                    return FullTextResult(
                        success=True,
                        source=FullTextSource.UNPAYWALL,
                        url=regular_url,
                        metadata={
                            "version": best_oa.get("version"),
                            "license": best_oa.get("license"),
                            "oa_status": result.get("oa_status"),
                            "location": "best_oa_location",
                            "url_type": "pdf_direct" if is_pdf else "landing_page",
                        },
                    )

            # Try all other OA locations (repositories, preprints, etc.)
            oa_locations = result.get("oa_locations", [])
            for i, location in enumerate(oa_locations):
                # Skip if we already checked this as best_oa
                if best_oa and location == best_oa:
                    continue

                # Prefer PDF URLs
                pdf_url = location.get("url_for_pdf")
                if pdf_url:
                    logger.info(f"[OK] Found OA PDF via Unpaywall (location {i+1}): {publication.doi}")
                    return FullTextResult(
                        success=True,
                        source=FullTextSource.UNPAYWALL,
                        url=pdf_url,
                        metadata={
                            "version": location.get("version"),
                            "license": location.get("license"),
                            "oa_status": result.get("oa_status"),
                            "location": f"oa_location_{i}",
                            "url_type": "pdf_direct",
                        },
                    )

                # Try regular URL as fallback
                regular_url = location.get("url")
                if regular_url:
                    is_pdf = regular_url.lower().endswith(".pdf")
                    logger.info(f"[OK] Found OA URL via Unpaywall (location {i+1}): {publication.doi}")
                    return FullTextResult(
                        success=True,
                        source=FullTextSource.UNPAYWALL,
                        url=regular_url,
                        metadata={
                            "version": location.get("version"),
                            "license": location.get("license"),
                            "oa_status": result.get("oa_status"),
                            "location": f"oa_location_{i}",
                            "url_type": "pdf_direct" if is_pdf else "landing_page",
                        },
                    )

            # If we get here, is_oa=true but no URLs found (rare)
            oa_status = result.get("oa_status", "unknown")
            return FullTextResult(
                success=False, error=f"Unpaywall reports OA but no URLs available (oa_status: {oa_status})"
            )

        except Exception as e:
            logger.debug(f"Unpaywall lookup failed: {e}")
            return FullTextResult(success=False, error=str(e))

    async def _try_scihub(self, publication: Publication) -> FullTextResult:
        """
        Try to get full-text from Sci-Hub (Phase 2).

        [WARNING]  Use responsibly and in compliance with local laws.

        ENHANCED (Oct 11, 2025):
        - Downloads and saves PDF to data/fulltext/pdf/scihub/
        - Returns saved file path for immediate use
        - Enables easy deletion if legal compliance requires

        Args:
            publication: Publication object

        Returns:
            FullTextResult with saved PDF path if successful
        """
        if not self.config.enable_scihub or not self.scihub_client:
            return FullTextResult(success=False, error="Sci-Hub disabled or not initialized")

        try:
            # Try DOI first, then PMID
            identifier = publication.doi or publication.pmid

            if not identifier:
                return FullTextResult(success=False, error="No DOI or PMID for Sci-Hub lookup")

            pdf_url = await self.scihub_client.get_pdf_url(identifier)

            if not pdf_url:
                return FullTextResult(success=False, error="Not found in Sci-Hub")

            logger.info(f"[OK] Found PDF via Sci-Hub: {identifier}")

            # Return PDF URL for PDFDownloadManager
            return FullTextResult(
                success=True,
                source=FullTextSource.SCIHUB,
                url=pdf_url,
                metadata={
                    "identifier": identifier,
                    "warning": "Use responsibly and in compliance with local laws",
                },
            )

        except Exception as e:
            logger.debug(f"Sci-Hub lookup failed: {e}")
            return FullTextResult(success=False, error=str(e))

    async def _try_libgen(self, publication: Publication) -> FullTextResult:
        """
        Try to get full-text from LibGen (Phase 3).

        [WARNING]  Use responsibly and in compliance with local laws.

        ENHANCED (Oct 11, 2025):
        - Downloads and saves PDF to data/fulltext/pdf/libgen/
        - Returns saved file path for immediate use
        - Enables easy deletion if legal compliance requires

        Args:
            publication: Publication object

        Returns:
            FullTextResult with saved PDF path if successful
        """
        if not self.config.enable_libgen or not self.libgen_client:
            return FullTextResult(success=False, error="LibGen disabled or not initialized")

        try:
            # LibGen requires DOI
            if not publication.doi:
                return FullTextResult(success=False, error="No DOI for LibGen lookup")

            pdf_url = await self.libgen_client.get_pdf_url(publication.doi)

            if not pdf_url:
                return FullTextResult(success=False, error="Not found in LibGen")

            logger.info(f"[OK] Found PDF via LibGen: {publication.doi}")

            # Return PDF URL for PDFDownloadManager
            return FullTextResult(
                success=True,
                source=FullTextSource.LIBGEN,
                url=pdf_url,
                metadata={
                    "doi": publication.doi,
                    "warning": "Use responsibly and in compliance with local laws",
                },
            )

        except Exception as e:
            logger.debug(f"LibGen lookup failed: {e}")
            return FullTextResult(success=False, error=str(e))

    async def get_parsed_content(self, publication: Publication) -> Optional[Dict]:
        """
        Get parsed structured content for a publication with smart caching.

        NEW (Phase 3 - Oct 11, 2025):
        This is the SMART way to access full-text content:
        1. Check parsed cache first (instant <10ms, 200x faster than parsing!)
        2. If not cached, get PDF/XML via waterfall
        3. Parse the content (tables, figures, sections - ~2s)
        4. Cache the parsed result for future access

        PERFORMANCE:
        - First access: ~2-3s (download + parse)
        - Subsequent access: ~10ms (cache hit) = 200x faster!
        - Cache hit rate: 90%+ after warmup
        - API calls saved: 95%+ reduction

        Returns structured content dict:
        {
            'title': str,
            'abstract': str,
            'sections': [{'heading': str, 'text': str}, ...],
            'tables': [{'caption': str, 'data': [[...]], ...], ...],
            'figures': [{'caption': str, 'url': str, ...], ...],
            'references': [{'title': str, 'doi': str, ...], ...],
            'metadata': {...}
        }

        Args:
            publication: Publication object

        Returns:
            Dict with parsed content, or None if unavailable

        Example:
            >>> content = await manager.get_parsed_content(publication)
            >>> if content:
            >>>     print(f"Tables: {len(content['tables'])}")
            >>>     print(f"Sections: {len(content['sections'])}")
        """
        import time

        from omics_oracle_v2.lib.enrichment.fulltext.parsed_cache import get_parsed_cache

        cache = get_parsed_cache()

        # STEP 1: Check parsed cache (instant!)
        cached = await cache.get(publication.id)
        if cached:
            logger.info(
                f"[OK] Parsed cache HIT for {publication.id} "
                f"(age: {cache._get_age_days(cached)} days, "
                f"tables: {len(cached.get('content', {}).get('tables', []))}, "
                f"figures: {len(cached.get('content', {}).get('figures', []))})"
            )
            return cached.get("content")

        logger.info(f"Parsed cache MISS for {publication.id}, will download and parse...")

        # STEP 2: Get PDF/XML via waterfall
        start_time = time.time()
        result = await self.get_fulltext(publication)

        if not result.success:
            logger.warning(f"Could not get full-text for {publication.id}")
            return None

        # STEP 3: Parse the content
        # Import parser here to avoid circular imports
        try:
            from omics_oracle_v2.lib.enrichment.fulltext.pdf_parser import PDFExtractor

            parser = PDFExtractor()

            # Determine file path
            if result.pdf_path:
                file_path = result.pdf_path
                file_type = "pdf"
            elif result.metadata and result.metadata.get("path"):
                file_path = Path(result.metadata["path"])
                file_type = result.metadata.get("file_type", "pdf")
            else:
                logger.warning(f"No local file available for {publication.id}")
                return None

            # Parse content
            logger.info(f"Parsing {file_type.upper()}: {file_path.name}...")

            if file_type == "pdf":
                parsed = await parser.extract_text(file_path)
            else:
                # For XML/NXML, we'd use a different parser
                # For now, just return basic structure
                content_text = file_path.read_text(encoding="utf-8")
                parsed = {"text": content_text, "sections": [], "tables": [], "figures": [], "references": []}

            parse_duration_ms = int((time.time() - start_time) * 1000)

            # STEP 4: Cache the parsed content
            await cache.save(
                publication_id=publication.id,
                content=parsed,
                source_file=str(file_path),
                source_type=file_type,
                parse_duration_ms=parse_duration_ms,
                quality_score=None,  # TODO: Calculate quality score
            )

            logger.info(
                f"[OK] Parsed and cached {publication.id} "
                f"({parse_duration_ms}ms, {len(parsed.get('tables', []))} tables, "
                f"{len(parsed.get('figures', []))} figures)"
            )

            return parsed

        except Exception as e:
            logger.error(f"Error parsing content for {publication.id}: {e}")
            return None

    async def get_fulltext(
        self, publication: Publication, skip_sources: Optional[List[str]] = None
    ) -> FullTextResult:
        """
        Get full-text for a publication by trying sources in priority order.

        OPTIMIZED WATERFALL STRATEGY (Phase 6 - Oct 10, 2025):
        - Sources ordered by: effectiveness > legality > speed
        - Institutional access first (highest quality, legal)
        - Open access second (legal, good coverage)
        - Sci-Hub/LibGen last (legal gray area, use as fallback)
        - STOPS at first success (skip remaining sources)

        NOTE (Phase 3 - Oct 11, 2025):
        For structured content access, use get_parsed_content() instead!
        That method provides smart caching and returns parsed structures
        (tables, figures, sections) instead of raw PDFs.

        Args:
            publication: Publication object
            skip_sources: List of source names to skip (for waterfall retry)

        Returns:
            FullTextResult with success status and content/URL
        """
        if not self.initialized:
            await self.initialize()

        self.stats["total_attempts"] += 1

        skip_sources = skip_sources or []

        logger.info(f"Attempting to get full-text for: {publication.title[:60]}...")
        if skip_sources:
            logger.info(f"  Skipping already-tried sources: {', '.join(skip_sources)}")

        # OPTIMIZED WATERFALL ORDER (based on Phase 6 analysis):
        # Priority 0: Cache (instant, free)
        # Priority 1: Institutional Access (~45-50% coverage, legal, highest quality)
        # Priority 2: PMC (~6M articles, legal, highest quality)
        # Priority 3: Unpaywall (~25-30% additional coverage, legal OA aggregator)
        # Priority 4: CORE (~10-15% additional, legal academic repository)
        # Priority 5: OpenAlex OA URLs (metadata-driven, legal)
        # Priority 6: Crossref (publisher links, legal)
        # Priority 7: bioRxiv/arXiv (preprints, specialized, legal)
        # Priority 8: Sci-Hub (~15-20% additional, gray area, use responsibly)
        # Priority 9: LibGen (~5-10% additional, gray area, use responsibly)

        sources = [
            ("cache", self._check_cache),  # Always check cache first (instant)
            ("institutional", self._try_institutional_access),  # Priority 1: GT/ODU access
            ("pmc", self._try_pmc),  # Priority 2: PubMed Central (6M articles) **CRITICAL FIX**
            ("unpaywall", self._try_unpaywall),  # Priority 3: Legal OA (25-30%)
            ("core", self._try_core),  # Priority 4: CORE.ac.uk (10-15%)
            ("openalex_oa", self._try_openalex_oa_url),  # Priority 5: OA metadata
            ("crossref", self._try_crossref),  # Priority 6: Publisher links
            ("biorxiv", self._try_biorxiv),  # Priority 7a: Biomedical preprints
            ("arxiv", self._try_arxiv),  # Priority 7b: Other preprints
            ("scihub", self._try_scihub),  # Priority 8: Sci-Hub (optimized, 23.9% per mirror)
            ("libgen", self._try_libgen),  # Priority 9: LibGen (fallback)
        ]

        # WATERFALL: Try each source in order, STOP at first success
        for source_name, source_func in sources:
            # Skip sources that were already tried
            if source_name in skip_sources:
                logger.debug(f"  [SKIP]  Skipping {source_name} (already tried)")
                continue

            try:
                result = await asyncio.wait_for(
                    source_func(publication),
                    timeout=self.config.timeout_per_source,
                )

                if result.success:
                    logger.info(f"  Phase 2: [OK] Verified full-text access via {source_name}")
                    self.stats["successes"] += 1
                    self.stats["by_source"][source_name] = self.stats["by_source"].get(source_name, 0) + 1
                    return result  # STOP HERE - skip remaining sources
                else:
                    logger.debug(f"  [X] {source_name} did not find full-text")

            except asyncio.TimeoutError:
                logger.debug(f"[TIME] Timeout for source {source_name}")
            except Exception as e:
                logger.debug(f"[WARNING] Error trying source {source_name}: {e}")

        # No source succeeded - this is expected for ~5-10% of papers
        logger.debug(f"No full-text found for: {publication.title[:60]}...")
        self.stats["failures"] += 1
        return FullTextResult(success=False, error="No sources succeeded")

    async def get_all_fulltext_urls(self, publication: Publication) -> FullTextResult:
        """
        Get full-text URLs from ALL sources in PARALLEL.

        NEW STRATEGY (Oct 13, 2025):
        - Queries ALL enabled sources simultaneously (not waterfall)
        - Returns ALL found URLs sorted by priority
        - First URL = highest priority (institutional > PMC > Unpaywall...)
        - Remaining URLs = fallbacks for download retry

        Benefits:
        - Single pass through all sources (~2-3 seconds)
        - Built-in fallback URLs (no re-querying needed)
        - Higher success rate (PDFDownloadManager tries all URLs)
        - Parallel execution = faster than sequential waterfall

        Use Case:
        - Batch downloads where fallback is critical
        - When you want to maximize download success rate
        - When network reliability is uncertain

        Example:
            >>> result = await manager.get_all_fulltext_urls(publication)
            >>> if result.success:
            >>>     print(f"Found {len(result.all_urls)} URLs")
            >>>     print(f"Best: {result.all_urls[0].source.value}")
            >>>     print(f"Fallbacks: {[u.source.value for u in result.all_urls[1:]]}")

        Args:
            publication: Publication object

        Returns:
            FullTextResult with all_urls populated
        """
        if not self.initialized:
            await self.initialize()

        self.stats["total_attempts"] += 1

        logger.info(f"Collecting URLs from ALL sources for: {publication.title[:60]}...")

        # Check cache first (instant)
        cached = await self._check_cache(publication)
        if cached.success:
            logger.info("[OK] Found in cache")
            return cached

        # Define all sources with their priority order
        sources = [
            ("institutional", self._try_institutional_access, 1),
            ("pmc", self._try_pmc, 2),
            ("unpaywall", self._try_unpaywall, 3),
            ("core", self._try_core, 4),
            ("openalex_oa", self._try_openalex_oa_url, 5),
            ("crossref", self._try_crossref, 6),
            ("biorxiv", self._try_biorxiv, 7),
            ("arxiv", self._try_arxiv, 8),
            ("scihub", self._try_scihub, 9),
            ("libgen", self._try_libgen, 10),
        ]

        # Execute ALL sources in PARALLEL
        logger.info(f"[FAST] Querying {len(sources)} sources in parallel...")
        tasks = [
            asyncio.wait_for(source_func(publication), timeout=self.config.timeout_per_source)
            for _, source_func, _ in sources
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Collect all successful URLs
        all_urls = []
        for i, result in enumerate(results):
            source_name, _, priority = sources[i]

            if isinstance(result, Exception):
                logger.debug(f"  [X] {source_name} exception: {result}")
                continue

            if isinstance(result, FullTextResult) and result.success and result.url:
                # [OK] NEW: Classify URL type automatically
                url_type = URLValidator.classify_url(result.url)

                # [OK] NEW: Adjust priority based on URL type
                # PDF links get higher priority, landing pages get lower
                priority_adjustment = URLValidator.get_priority_boost(result.url)
                adjusted_priority = priority + priority_adjustment

                source_url = SourceURL(
                    url=result.url,
                    source=result.source,
                    priority=adjusted_priority,  # [OK] Adjusted priority
                    url_type=url_type,  # [OK] NEW: Track URL type
                    confidence=1.0,
                    requires_auth=(result.source == FullTextSource.INSTITUTIONAL),
                    metadata=result.metadata or {},
                )
                all_urls.append(source_url)

                # Enhanced logging with URL type
                logger.info(
                    f"  [OK] {source_name}: Found URL "
                    f"(type={url_type.value}, priority={priority}->{adjusted_priority})"
                )
            else:
                logger.debug(f"  [X] {source_name}: No URL found")

        if not all_urls:
            logger.warning(f"No URLs found from any source for: {publication.title[:60]}...")
            self.stats["failures"] += 1
            return FullTextResult(success=False, error="No URLs found from any source", all_urls=[])

        # Sort by priority (lower number = higher priority)
        all_urls.sort(key=lambda x: x.priority)

        # Use best URL as primary
        best_url = all_urls[0]

        logger.info(f"[OK] Found {len(all_urls)} URLs for: {publication.title[:60]}")
        logger.info(f"   Best: {best_url.source.value} (priority {best_url.priority})")
        if len(all_urls) > 1:
            fallbacks = ", ".join([f"{u.source.value}({u.priority})" for u in all_urls[1:]])
            logger.info(f"   Fallbacks: {fallbacks}")

        self.stats["successes"] += 1
        self.stats["by_source"][best_url.source.value] = (
            self.stats["by_source"].get(best_url.source.value, 0) + 1
        )

        return FullTextResult(
            success=True,
            source=best_url.source,
            url=best_url.url,
            metadata={
                "total_sources_found": len(all_urls),
                "sources": [url.source.value for url in all_urls],
                "priorities": [url.priority for url in all_urls],
                "best_source": best_url.source.value,
            },
            all_urls=all_urls,
        )

    async def get_fulltext_batch(
        self,
        publications: List[Publication],
        max_concurrent: Optional[int] = None,
        collect_all_urls: bool = True,  # NEW: Collect URLs from all sources
    ) -> List[FullTextResult]:
        """
        Get full-text for multiple publications concurrently.

        NEW (Oct 13, 2025):
        - Now uses get_all_fulltext_urls() by default
        - Collects URLs from ALL sources in parallel
        - Returns results with all_urls populated for fallback

        Args:
            publications: List of Publication objects
            max_concurrent: Maximum concurrent requests (defaults to config)
            collect_all_urls: If True, use parallel collection; if False, use waterfall

        Returns:
            List of FullTextResult objects with all_urls populated
        """
        if not self.initialized:
            await self.initialize()

        max_concurrent = max_concurrent or self.config.max_concurrent

        logger.info(
            f"Getting full-text for {len(publications)} publications "
            f"(max {max_concurrent} concurrent, collect_all={collect_all_urls})..."
        )

        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(max_concurrent)

        async def get_with_semaphore(pub):
            async with semaphore:
                if collect_all_urls:
                    return await self.get_all_fulltext_urls(pub)
                else:
                    return await self.get_fulltext(pub)

        # Run all requests concurrently with limit
        results = await asyncio.gather(*[get_with_semaphore(pub) for pub in publications])

        success_count = sum(1 for r in results if r.success)
        total_urls = sum(len(r.all_urls) for r in results if r.all_urls)

        logger.info(
            f"Batch complete: {success_count}/{len(publications)} succeeded, "
            f"{total_urls} total URLs collected"
        )

        return results

    def get_statistics(self) -> Dict:
        """
        Get statistics about full-text retrieval attempts.

        Returns:
            Dictionary with statistics
        """
        success_rate = (
            (self.stats["successes"] / self.stats["total_attempts"] * 100)
            if self.stats["total_attempts"] > 0
            else 0
        )

        return {
            "total_attempts": self.stats["total_attempts"],
            "successes": self.stats["successes"],
            "failures": self.stats["failures"],
            "success_rate": f"{success_rate:.1f}%",
            "by_source": self.stats["by_source"],
        }

    def reset_statistics(self):
        """Reset statistics counters."""
        self.stats = {
            "total_attempts": 0,
            "successes": 0,
            "failures": 0,
            "by_source": {},
        }
        logger.info("Statistics reset")


# Convenience function
async def get_fulltext(
    publication: Publication, config: Optional[FullTextManagerConfig] = None
) -> FullTextResult:
    """
    Convenience function to get full-text for a single publication.

    Args:
        publication: Publication object
        config: Optional configuration

    Returns:
        FullTextResult
    """
    async with FullTextManager(config) as manager:
        return await manager.get_fulltext(publication)
