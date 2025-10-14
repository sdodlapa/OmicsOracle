"""
PubMed Central (PMC) client for finding open access full-text papers.

PMC (https://www.ncbi.nlm.nih.gov/pmc/) is the #1 legal source with 6M+ free full-text articles.
Provides multiple URL patterns for maximum success rate.

API Documentation: https://www.ncbi.nlm.nih.gov/pmc/tools/id-converter-api/
"""

import logging
import ssl
import xml.etree.ElementTree as ET
from typing import Optional

import aiohttp
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# Import these from manager to avoid circular imports
# Will be properly imported at runtime
FullTextResult = None
FullTextSource = None


def _ensure_imports():
    """Lazy import to avoid circular dependency."""
    global FullTextResult, FullTextSource
    if FullTextResult is None:
        from omics_oracle_v2.lib.pipelines.url_collection.manager import FullTextResult as FTR
        from omics_oracle_v2.lib.pipelines.url_collection.manager import FullTextSource as FTS

        FullTextResult = FTR
        FullTextSource = FTS


class PMCConfig(BaseModel):
    """Configuration for PMC client."""

    enabled: bool = Field(True, description="Enable PMC lookups")
    timeout: int = Field(10, ge=1, le=60, description="Request timeout in seconds")
    retry_count: int = Field(3, ge=1, le=5, description="Number of retries")


class PMCClient:
    """
    Client for PubMed Central (PMC) full-text access.

    PMC provides multiple URL patterns:
    1. PMC OA API (FTP links - most reliable for OA articles)
    2. Direct PDF URLs (https://pmc.ncbi.nlm.nih.gov/articles/PMC{id}/pdf/)
    3. EuropePMC PDF render (https://europepmc.org/articles/PMC{id}?pdf=render)
    4. PMC reader view (fallback - landing page)

    Features:
    - Automatic PMID -> PMCID conversion via E-utilities
    - Multiple URL patterns for maximum success
    - SSL context for institutional networks
    - 6M+ open access articles

    Example:
        >>> config = PMCConfig(enabled=True)
        >>> async with PMCClient(config) as client:
        ...     result = await client.get_fulltext(publication)
        ...     if result.success:
        ...         print(result.url)
    """

    def __init__(self, config: PMCConfig):
        """
        Initialize PMC client.

        Args:
            config: PMC configuration
        """
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None

        # SSL context for institutional networks
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE

        logger.info("PMC client initialized")

    async def __aenter__(self):
        """Async context manager entry."""
        connector = aiohttp.TCPConnector(ssl=self.ssl_context)
        self.session = aiohttp.ClientSession(connector=connector)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def close(self) -> None:
        """Close the aiohttp session."""
        if self.session:
            await self.session.close()
            self.session = None

    async def get_fulltext(self, publication) -> "FullTextResult":
        """
        Get full-text from PMC with multiple URL patterns.

        Tries multiple strategies:
        1. Extract PMC ID from publication (pmcid, pmc_id, metadata)
        2. Convert PMID -> PMCID via E-utilities (fallback)
        3. Try multiple URL patterns in priority order

        Args:
            publication: Publication object with pmid or pmc_id

        Returns:
            FullTextResult with best available URL
        """
        _ensure_imports()  # Lazy import to avoid circular dependency

        if not self.config.enabled:
            return FullTextResult(success=False, error="PMC disabled")

        try:
            # Extract PMC ID
            pmc_id = await self._extract_pmc_id(publication)
            if not pmc_id:
                return FullTextResult(success=False, error="No PMC ID found")

            # Try multiple URL patterns
            result = await self._try_url_patterns(pmc_id)
            return result

        except Exception as e:
            logger.warning(f"PMC lookup failed: {e}")
            return FullTextResult(success=False, error=str(e))

    async def _extract_pmc_id(self, publication) -> Optional[str]:
        """
        Extract PMC ID from publication using multiple methods.

        Tries in order:
        1. Direct pmcid attribute (most reliable - from PubMed fetch)
        2. Legacy pmc_id attribute
        3. Extract from publication metadata
        4. Fetch PMC ID from PMID using E-utilities (fallback)

        Args:
            publication: Publication object

        Returns:
            PMC ID (numeric only) or None
        """
        pmc_id = None

        # Method 1: Direct pmcid attribute
        if hasattr(publication, "pmcid") and publication.pmcid:
            pmc_id = publication.pmcid.replace("PMC", "").strip()
            logger.info(f"Using PMC ID from publication.pmcid: PMC{pmc_id}")
            return pmc_id

        # Method 2: Legacy pmc_id attribute
        if hasattr(publication, "pmc_id") and publication.pmc_id:
            pmc_id = publication.pmc_id.replace("PMC", "").strip()
            logger.info(f"Using PMC ID from publication.pmc_id: PMC{pmc_id}")
            return pmc_id

        # Method 3: Extract from publication metadata
        if publication.metadata and publication.metadata.get("pmc_id"):
            pmc_id = publication.metadata["pmc_id"].replace("PMC", "").strip()
            logger.info(f"Using PMC ID from metadata: PMC{pmc_id}")
            return pmc_id

        # Method 4: Fetch PMC ID from PMID using E-utilities
        if hasattr(publication, "pmid") and publication.pmid:
            pmc_id = await self._convert_pmid_to_pmcid(publication.pmid)
            if pmc_id:
                logger.info(f"Converted PMID {publication.pmid} -> PMC{pmc_id} via E-utilities")
                return pmc_id

        return None

    async def _convert_pmid_to_pmcid(self, pmid: str) -> Optional[str]:
        """
        Convert PMID to PMCID using NCBI E-utilities ID converter.

        Args:
            pmid: PubMed ID

        Returns:
            PMC ID (numeric only) or None
        """
        try:
            url = f"https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/?ids={pmid}&format=json"

            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    records = data.get("records", [])
                    if records and len(records) > 0:
                        pmc_id = records[0].get("pmcid", "").replace("PMC", "").strip()
                        return pmc_id if pmc_id else None

        except Exception as e:
            logger.debug(f"PMID->PMCID conversion failed: {e}")

        return None

    async def _try_url_patterns(self, pmc_id: str) -> "FullTextResult":
        """
        Try multiple PMC URL patterns in priority order.

        Pattern priority:
        1. PMC OA API (most reliable for OA articles)
        2. Direct PDF URL
        3. EuropePMC PDF render
        4. PMC reader view (landing page fallback)

        Args:
            pmc_id: PMC ID (numeric only)

        Returns:
            FullTextResult with best available URL
        """
        # Pattern 1: Try PMC OA API (most reliable)
        result = await self._try_oa_api(pmc_id)
        if result.success:
            return result

        # Pattern 2: Direct PMC PDF URL
        result = await self._try_direct_pdf(pmc_id)
        if result.success:
            return result

        # Pattern 3: EuropePMC PDF render
        result = await self._try_europepmc(pmc_id)
        if result.success:
            return result

        # Pattern 4: PMC reader view (landing page fallback)
        result = await self._try_reader_view(pmc_id)
        if result.success:
            return result

        # All patterns failed
        return FullTextResult(success=False, error=f"All PMC URL patterns failed for PMC{pmc_id}")

    async def _try_oa_api(self, pmc_id: str) -> "FullTextResult":
        """
        Try PMC Open Access API (most reliable for OA articles).

        Returns FTP links that can be converted to HTTPS.

        Args:
            pmc_id: PMC ID (numeric only)

        Returns:
            FullTextResult with PDF URL from OA API
        """
        try:
            oa_api_url = f"https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?id=PMC{pmc_id}"

            async with self.session.get(oa_api_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    xml_content = await response.text()
                    root = ET.fromstring(xml_content)

                    # Look for PDF link
                    for link in root.findall('.//link[@format="pdf"]'):
                        href = link.get("href")
                        if href:
                            # Convert ftp:// to https://
                            pdf_link = href.replace(
                                "ftp://ftp.ncbi.nlm.nih.gov/", "https://ftp.ncbi.nlm.nih.gov/"
                            )
                            logger.info(f"[PMC] Found PMC{pmc_id} via OA API: {pdf_link}")
                            return FullTextResult(
                                success=True,
                                source=FullTextSource.PMC,
                                url=pdf_link,
                                metadata={
                                    "pmc_id": f"PMC{pmc_id}",
                                    "pattern": "oa_api",
                                    "url_type": "pdf_direct",
                                },
                            )

        except Exception as e:
            logger.debug(f"PMC OA API failed: {e}")

        return FullTextResult(success=False, error="OA API failed")

    async def _try_direct_pdf(self, pmc_id: str) -> "FullTextResult":
        """
        Try direct PMC PDF URL.

        Args:
            pmc_id: PMC ID (numeric only)

        Returns:
            FullTextResult with direct PDF URL
        """
        try:
            direct_pdf_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmc_id}/pdf/"

            async with self.session.head(
                direct_pdf_url, timeout=aiohttp.ClientTimeout(total=5), allow_redirects=True
            ) as response:
                if response.status == 200:
                    logger.info(f"[PMC] Found PMC{pmc_id} via direct PDF: {direct_pdf_url}")
                    return FullTextResult(
                        success=True,
                        source=FullTextSource.PMC,
                        url=direct_pdf_url,
                        metadata={
                            "pmc_id": f"PMC{pmc_id}",
                            "pattern": "direct_pdf",
                            "url_type": "pdf_direct",
                        },
                    )

        except Exception as e:
            logger.debug(f"PMC direct PDF failed: {e}")

        return FullTextResult(success=False, error="Direct PDF failed")

    async def _try_europepmc(self, pmc_id: str) -> "FullTextResult":
        """
        Try EuropePMC PDF render.

        Args:
            pmc_id: PMC ID (numeric only)

        Returns:
            FullTextResult with EuropePMC URL
        """
        try:
            europepmc_url = f"https://europepmc.org/articles/PMC{pmc_id}?pdf=render"

            async with self.session.head(
                europepmc_url, timeout=aiohttp.ClientTimeout(total=5), allow_redirects=True
            ) as response:
                if response.status == 200:
                    logger.info(f"[PMC] Found PMC{pmc_id} via EuropePMC: {europepmc_url}")
                    return FullTextResult(
                        success=True,
                        source=FullTextSource.PMC,
                        url=europepmc_url,
                        metadata={
                            "pmc_id": f"PMC{pmc_id}",
                            "pattern": "europepmc",
                            "url_type": "pdf_direct",
                        },
                    )

        except Exception as e:
            logger.debug(f"EuropePMC failed: {e}")

        return FullTextResult(success=False, error="EuropePMC failed")

    async def _try_reader_view(self, pmc_id: str) -> "FullTextResult":
        """
        Try PMC reader view (landing page fallback).

        Args:
            pmc_id: PMC ID (numeric only)

        Returns:
            FullTextResult with reader view URL
        """
        try:
            reader_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmc_id}/?report=reader"

            async with self.session.head(
                reader_url, timeout=aiohttp.ClientTimeout(total=5), allow_redirects=True
            ) as response:
                if response.status == 200:
                    logger.warning(f"[PMC] Found PMC{pmc_id} reader view (landing page): {reader_url}")
                    return FullTextResult(
                        success=True,
                        source=FullTextSource.PMC,
                        url=reader_url,
                        metadata={
                            "pmc_id": f"PMC{pmc_id}",
                            "pattern": "reader_view",
                            "url_type": "landing_page",
                        },
                    )

        except Exception as e:
            logger.debug(f"PMC reader view failed: {e}")

        return FullTextResult(success=False, error="Reader view failed")
