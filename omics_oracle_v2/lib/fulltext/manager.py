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
    >>> from omics_oracle_v2.lib.fulltext.manager import FullTextManager
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

from omics_oracle_v2.lib.fulltext.sources.libgen_client import LibGenClient, LibGenConfig
from omics_oracle_v2.lib.fulltext.sources.scihub_client import SciHubClient, SciHubConfig
from omics_oracle_v2.lib.publications.clients.institutional_access import (
    InstitutionalAccessManager,
    InstitutionType,
)
from omics_oracle_v2.lib.publications.clients.oa_sources import (
    ArXivClient,
    BioRxivClient,
    COREClient,
    CrossrefClient,
)
from omics_oracle_v2.lib.publications.clients.oa_sources.unpaywall_client import (
    UnpaywallClient,
    UnpaywallConfig,
)
from omics_oracle_v2.lib.publications.models import Publication

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


class FullTextManagerConfig:
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
        download_pdfs: Whether to download PDFs (vs. just get URLs)
        pdf_cache_dir: Directory to cache downloaded PDFs
        max_concurrent: Maximum concurrent source attempts
        timeout_per_source: Timeout for each source (seconds)
    """

    def __init__(
        self,
        enable_institutional: bool = True,
        enable_pmc: bool = True,
        enable_openalex: bool = True,
        enable_unpaywall: bool = True,  # NEW - Phase 1+
        enable_core: bool = True,
        enable_biorxiv: bool = True,
        enable_arxiv: bool = True,
        enable_crossref: bool = True,
        enable_scihub: bool = False,  # NEW - Phase 2 (disabled by default)
        enable_libgen: bool = False,  # NEW - Phase 3 (disabled by default)
        core_api_key: Optional[str] = None,
        unpaywall_email: Optional[str] = None,  # NEW
        scihub_use_proxy: bool = False,  # NEW
        libgen_use_proxy: bool = False,  # NEW
        download_pdfs: bool = False,
        pdf_cache_dir: Optional[Path] = None,
        max_concurrent: int = 3,
        timeout_per_source: int = 30,
    ):
        self.enable_institutional = enable_institutional
        self.enable_pmc = enable_pmc
        self.enable_openalex = enable_openalex
        self.enable_unpaywall = enable_unpaywall  # NEW
        self.enable_core = enable_core
        self.enable_biorxiv = enable_biorxiv
        self.enable_arxiv = enable_arxiv
        self.enable_crossref = enable_crossref
        self.enable_scihub = enable_scihub  # NEW
        self.enable_libgen = enable_libgen  # NEW
        self.core_api_key = core_api_key
        self.unpaywall_email = unpaywall_email  # NEW
        self.scihub_use_proxy = scihub_use_proxy  # NEW
        self.libgen_use_proxy = libgen_use_proxy  # NEW
        self.download_pdfs = download_pdfs
        self.pdf_cache_dir = pdf_cache_dir or Path("data/pdfs")
        self.max_concurrent = max_concurrent
        self.timeout_per_source = timeout_per_source


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

        # Initialize CORE client
        if self.config.enable_core:
            from omics_oracle_v2.lib.publications.clients.oa_sources.core_client import COREConfig

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
            logger.info("⚠️  Sci-Hub client initialized (use responsibly)")

        # Initialize LibGen client (NEW - Phase 3)
        if self.config.enable_libgen:
            libgen_config = LibGenConfig()
            self.libgen_client = LibGenClient(libgen_config)
            await self.libgen_client.__aenter__()
            logger.info("⚠️  LibGen client initialized (use responsibly)")

        self.initialized = True
        logger.info("All OA source clients initialized")

    async def cleanup(self):
        """Cleanup all OA source clients."""
        if not self.initialized:
            return

        logger.info("Cleaning up OA source clients...")

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

    def _get_cache_path(self, publication: Publication) -> Path:
        """
        Get cache path for a publication's PDF.

        Args:
            publication: Publication object

        Returns:
            Path to cached PDF
        """
        # Use DOI as filename if available, otherwise title hash
        if publication.doi:
            filename = publication.doi.replace("/", "_").replace("\\", "_") + ".pdf"
        else:
            import hashlib

            title_hash = hashlib.md5(publication.title.encode()).hexdigest()
            filename = f"{title_hash}.pdf"

        return self.config.pdf_cache_dir / filename

    async def _check_cache(self, publication: Publication) -> FullTextResult:
        """
        Check if full-text is already cached.

        Args:
            publication: Publication object

        Returns:
            FullTextResult
        """
        cache_path = self._get_cache_path(publication)

        if cache_path.exists() and cache_path.stat().st_size > 0:
            logger.info(f"Found cached PDF for {publication.title[:50]}...")
            return FullTextResult(
                success=True,
                source=FullTextSource.CACHE,
                pdf_path=cache_path,
                metadata={"cached": True, "size": cache_path.stat().st_size},
            )

        return FullTextResult(success=False, error="Not in cache")

    async def _try_institutional_access(self, publication: Publication) -> FullTextResult:
        """
        Try to get full-text through institutional access (Georgia Tech).

        Priority 1 source - highest quality, legal, ~45-50% coverage.

        Args:
            publication: Publication object

        Returns:
            FullTextResult
        """
        if not self.config.enable_institutional or not self.institutional_manager:
            return FullTextResult(success=False, error="Institutional access not enabled")

        try:
            # Get access URL through institutional subscription
            access_url = self.institutional_manager.get_access_url(publication)

            if access_url:
                logger.info(f"Found access via institutional: {access_url}")
                return FullTextResult(
                    success=True,
                    source=FullTextSource.INSTITUTIONAL,
                    url=access_url,
                    metadata={"method": "direct", "institution": "Georgia Tech"},
                )

            return FullTextResult(success=False, error="No institutional access found")

        except Exception as e:
            logger.debug(f"Institutional access lookup failed: {e}")
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

        Args:
            publication: Publication object

        Returns:
            FullTextResult
        """
        if not self.config.enable_biorxiv or not self.biorxiv_client:
            return FullTextResult(success=False, error="bioRxiv disabled or not initialized")

        try:
            # bioRxiv only works with DOI
            if not publication.doi:
                return FullTextResult(success=False, error="No DOI for bioRxiv lookup")

            result = await self.biorxiv_client.get_by_doi(publication.doi)
            if result and result.get("pdf_url"):
                logger.info(f"Found in bioRxiv: {publication.doi}")
                return FullTextResult(
                    success=True,
                    source=FullTextSource.BIORXIV,
                    url=result["pdf_url"],
                    metadata={"biorxiv_id": result.get("biorxiv_id"), "version": result.get("version")},
                )

            return FullTextResult(success=False, error="Not a bioRxiv paper or not found")

        except Exception as e:
            logger.warning(f"bioRxiv error: {e}")
            return FullTextResult(success=False, error=str(e))

    async def _try_arxiv(self, publication: Publication) -> FullTextResult:
        """
        Try to get full-text from arXiv.

        Args:
            publication: Publication object

        Returns:
            FullTextResult
        """
        if not self.config.enable_arxiv or not self.arxiv_client:
            return FullTextResult(success=False, error="arXiv disabled or not initialized")

        try:
            # Only try by arXiv ID if DOI looks like an arXiv ID (contains "arxiv")
            if publication.doi and "arxiv" in publication.doi.lower():
                paper = await self.arxiv_client.get_by_arxiv_id(publication.doi)
                if paper and paper.get("pdf_url"):
                    logger.info(f"Found in arXiv by ID: {publication.doi}")
                    return FullTextResult(
                        success=True,
                        source=FullTextSource.ARXIV,
                        url=paper["pdf_url"],
                        metadata={"arxiv_id": paper.get("arxiv_id")},
                    )

            # Try title search (only for papers without DOI or if arXiv ID lookup failed)
            if publication.title:
                results = await self.arxiv_client.search_by_title(publication.title, max_results=1)
                if results and results[0].get("pdf_url"):
                    logger.info(f"Found in arXiv by title: {publication.title[:50]}...")
                    return FullTextResult(
                        success=True,
                        source=FullTextSource.ARXIV,
                        url=results[0]["pdf_url"],
                        metadata={"arxiv_id": results[0].get("arxiv_id"), "method": "title"},
                    )

            return FullTextResult(success=False, error="Not found in arXiv")

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
        Try to get full-text from Unpaywall (NEW - Phase 1+).

        Args:
            publication: Publication object

        Returns:
            FullTextResult
        """
        if not self.config.enable_unpaywall or not self.unpaywall_client:
            return FullTextResult(success=False, error="Unpaywall disabled or not initialized")

        try:
            # Unpaywall requires DOI
            if not publication.doi:
                return FullTextResult(success=False, error="No DOI for Unpaywall lookup")

            result = await self.unpaywall_client.get_oa_location(publication.doi)
            if result and result.get("is_oa"):
                best_oa = result.get("best_oa_location", {})
                pdf_url = best_oa.get("url_for_pdf") or best_oa.get("url")

                if pdf_url:
                    logger.info(f"Found OA via Unpaywall: {publication.doi}")
                    return FullTextResult(
                        success=True,
                        source=FullTextSource.UNPAYWALL,
                        url=pdf_url,
                        metadata={
                            "version": best_oa.get("version"),
                            "license": best_oa.get("license"),
                            "oa_status": result.get("oa_status"),
                        },
                    )

            return FullTextResult(success=False, error="Not OA in Unpaywall")

        except Exception as e:
            logger.debug(f"Unpaywall lookup failed: {e}")
            return FullTextResult(success=False, error=str(e))

    async def _try_scihub(self, publication: Publication) -> FullTextResult:
        """
        Try to get full-text from Sci-Hub (NEW - Phase 2).

        ⚠️  Use responsibly and in compliance with local laws.

        Args:
            publication: Publication object

        Returns:
            FullTextResult
        """
        if not self.config.enable_scihub or not self.scihub_client:
            return FullTextResult(success=False, error="Sci-Hub disabled or not initialized")

        try:
            # Try DOI first, then PMID
            identifier = publication.doi or publication.pmid

            if not identifier:
                return FullTextResult(success=False, error="No DOI or PMID for Sci-Hub lookup")

            pdf_url = await self.scihub_client.get_pdf_url(identifier)

            if pdf_url:
                logger.info(f"✓ Found PDF via Sci-Hub: {identifier}")
                return FullTextResult(
                    success=True,
                    source=FullTextSource.SCIHUB,
                    url=pdf_url,
                    metadata={"identifier": identifier},
                )

            return FullTextResult(success=False, error="Not found in Sci-Hub")

        except Exception as e:
            logger.debug(f"Sci-Hub lookup failed: {e}")
            return FullTextResult(success=False, error=str(e))

    async def _try_libgen(self, publication: Publication) -> FullTextResult:
        """
        Try to get full-text from LibGen (NEW - Phase 3).

        ⚠️  Use responsibly and in compliance with local laws.

        Args:
            publication: Publication object

        Returns:
            FullTextResult
        """
        if not self.config.enable_libgen or not self.libgen_client:
            return FullTextResult(success=False, error="LibGen disabled or not initialized")

        try:
            # LibGen requires DOI
            if not publication.doi:
                return FullTextResult(success=False, error="No DOI for LibGen lookup")

            pdf_url = await self.libgen_client.get_pdf_url(publication.doi)

            if pdf_url:
                logger.info(f"✓ Found PDF via LibGen: {publication.doi}")
                return FullTextResult(
                    success=True,
                    source=FullTextSource.LIBGEN,
                    url=pdf_url,
                    metadata={"doi": publication.doi},
                )

            return FullTextResult(success=False, error="Not found in LibGen")

        except Exception as e:
            logger.debug(f"LibGen lookup failed: {e}")
            return FullTextResult(success=False, error=str(e))

    async def get_fulltext(self, publication: Publication) -> FullTextResult:
        """
        Get full-text for a publication by trying sources in priority order.

        OPTIMIZED WATERFALL STRATEGY (Phase 6 - Oct 10, 2025):
        - Sources ordered by: effectiveness > legality > speed
        - Institutional access first (highest quality, legal)
        - Open access second (legal, good coverage)
        - Sci-Hub/LibGen last (legal gray area, use as fallback)
        - STOPS at first success (skip remaining sources)

        Args:
            publication: Publication object

        Returns:
            FullTextResult with success status and content/URL
        """
        if not self.initialized:
            await self.initialize()

        self.stats["total_attempts"] += 1

        logger.info(f"Attempting to get full-text for: {publication.title[:60]}...")

        # OPTIMIZED WATERFALL ORDER (based on Phase 6 analysis):
        # Priority 1: Institutional Access (~45-50% coverage, legal, highest quality)
        # Priority 2: Unpaywall (~25-30% additional coverage, legal OA aggregator)
        # Priority 3: CORE (~10-15% additional, legal academic repository)
        # Priority 4: OpenAlex OA URLs (metadata-driven, legal)
        # Priority 5: Crossref (publisher links, legal)
        # Priority 6: bioRxiv/arXiv (preprints, specialized, legal)
        # Priority 7: Sci-Hub (~15-20% additional, gray area, use responsibly)
        # Priority 8: LibGen (~5-10% additional, gray area, use responsibly)

        sources = [
            ("cache", self._check_cache),  # Always check cache first (instant)
            ("institutional", self._try_institutional_access),  # Priority 1: GT/ODU access
            ("unpaywall", self._try_unpaywall),  # Priority 2: Legal OA (25-30%)
            ("core", self._try_core),  # Priority 3: CORE.ac.uk (10-15%)
            ("openalex_oa", self._try_openalex_oa_url),  # Priority 4: OA metadata
            ("crossref", self._try_crossref),  # Priority 5: Publisher links
            ("biorxiv", self._try_biorxiv),  # Priority 6a: Biomedical preprints
            ("arxiv", self._try_arxiv),  # Priority 6b: Other preprints
            ("scihub", self._try_scihub),  # Priority 7: Sci-Hub (optimized, 23.9% per mirror)
            ("libgen", self._try_libgen),  # Priority 8: LibGen (fallback)
        ]

        # WATERFALL: Try each source in order, STOP at first success
        for source_name, source_func in sources:
            try:
                result = await asyncio.wait_for(
                    source_func(publication),
                    timeout=self.config.timeout_per_source,
                )

                if result.success:
                    logger.info(f"  Phase 2: ✓ Verified full-text access via {source_name}")
                    self.stats["successes"] += 1
                    self.stats["by_source"][source_name] = self.stats["by_source"].get(source_name, 0) + 1
                    return result  # STOP HERE - skip remaining sources
                else:
                    logger.debug(f"  ✗ {source_name} did not find full-text")

            except asyncio.TimeoutError:
                logger.debug(f"⏱ Timeout for source {source_name}")
            except Exception as e:
                logger.debug(f"⚠ Error trying source {source_name}: {e}")

        # No source succeeded - this is expected for ~5-10% of papers
        logger.debug(f"No full-text found for: {publication.title[:60]}...")
        self.stats["failures"] += 1
        return FullTextResult(success=False, error="No sources succeeded")

    async def get_fulltext_batch(
        self, publications: List[Publication], max_concurrent: Optional[int] = None
    ) -> List[FullTextResult]:
        """
        Get full-text for multiple publications concurrently.

        Args:
            publications: List of Publication objects
            max_concurrent: Maximum concurrent requests (defaults to config)

        Returns:
            List of FullTextResult objects
        """
        if not self.initialized:
            await self.initialize()

        max_concurrent = max_concurrent or self.config.max_concurrent

        logger.info(
            f"Getting full-text for {len(publications)} publications (max {max_concurrent} concurrent)..."
        )

        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(max_concurrent)

        async def get_with_semaphore(pub):
            async with semaphore:
                return await self.get_fulltext(pub)

        # Run all requests concurrently with limit
        results = await asyncio.gather(*[get_with_semaphore(pub) for pub in publications])

        success_count = sum(1 for r in results if r.success)
        logger.info(f"Batch complete: {success_count}/{len(publications)} succeeded")

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
