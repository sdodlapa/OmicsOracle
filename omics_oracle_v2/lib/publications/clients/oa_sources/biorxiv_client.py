"""
bioRxiv and medRxiv API client for preprint access.

bioRxiv and medRxiv are preprint servers for biology and medicine.
They provide free access to 200K+ biomedical preprints.

API Documentation: https://api.biorxiv.org/
Rate Limits: No explicit limits (be polite)
Coverage: 200K+ biomedical preprints
DOI Pattern: 10.1101/*

Example:
    >>> from omics_oracle_v2.lib.publications.clients.oa_sources import BioRxivClient
    >>>
    >>> client = BioRxivClient()
    >>>
    >>> # Get preprint by DOI
    >>> result = await client.get_by_doi("10.1101/2023.01.01.123456")
    >>> if result:
    ...     print(f"PDF: {result['pdf_url']}")
    ...     print(f"Title: {result['title']}")
"""

import asyncio
import logging
import ssl
import time
from pathlib import Path
from typing import Dict, List, Optional

import aiohttp

from omics_oracle_v2.lib.search_engines.citations.base import BasePublicationClient
from omics_oracle_v2.lib.search_engines.citations.models import Publication, PublicationSource

logger = logging.getLogger(__name__)


class BioRxivConfig:
    """
    Configuration for bioRxiv/medRxiv API.

    Attributes:
        api_url: Base API URL
        timeout: Request timeout in seconds
        retry_count: Number of retries on failure
        rate_limit_per_second: Requests per second (be polite)
    """

    def __init__(
        self,
        api_url: str = "https://api.biorxiv.org",
        timeout: int = 30,
        retry_count: int = 3,
        rate_limit_per_second: int = 2,  # Be polite
    ):
        self.api_url = api_url
        self.timeout = timeout
        self.retry_count = retry_count
        self.rate_limit_per_second = rate_limit_per_second
        self.min_request_interval = 1.0 / rate_limit_per_second


class BioRxivClient(BasePublicationClient):
    """
    Client for bioRxiv and medRxiv preprint repositories.

    bioRxiv: Biology preprints
    medRxiv: Medical and health sciences preprints

    Features:
    - DOI-based lookup (10.1101/*)
    - Direct PDF URLs
    - Metadata enrichment
    - Version tracking
    """

    def __init__(self, config: Optional[BioRxivConfig] = None):
        """
        Initialize bioRxiv/medRxiv client.

        Args:
            config: bioRxiv configuration (optional)
        """
        self.config = config or BioRxivConfig()
        super().__init__(self.config)
        self.last_request_time = 0.0
        self.session = None

        # Create SSL context
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE

        logger.info(f"bioRxiv/medRxiv client initialized")

    @property
    def source_name(self) -> str:
        """Get the name of this publication source."""
        return "biorxiv"

    def _rate_limit(self):
        """Enforce rate limiting."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.config.min_request_interval:
            sleep_time = self.config.min_request_interval - elapsed
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def _is_biorxiv_doi(self, doi: str) -> bool:
        """
        Check if DOI is from bioRxiv or medRxiv.

        Args:
            doi: DOI to check

        Returns:
            True if bioRxiv/medRxiv DOI (10.1101/*)
        """
        if not doi:
            return False
        # Clean DOI
        doi = doi.replace("https://doi.org/", "").replace("http://doi.org/", "")
        return doi.startswith("10.1101/")

    async def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """
        Make API request with retry logic.

        Args:
            endpoint: API endpoint
            params: Query parameters

        Returns:
            Response JSON or None on failure
        """
        self._rate_limit()

        url = f"{self.config.api_url}{endpoint}"

        if not self.session:
            connector = aiohttp.TCPConnector(ssl=self.ssl_context)
            self.session = aiohttp.ClientSession(connector=connector)

        for attempt in range(self.config.retry_count):
            try:
                async with self.session.get(url, params=params, timeout=self.config.timeout) as response:
                    if response.status == 200:
                        return await response.json()

                    elif response.status == 404:
                        logger.debug(f"Not found in bioRxiv/medRxiv: {endpoint}")
                        return None

                    elif response.status == 429:
                        # Rate limited
                        wait_time = (attempt + 1) * 3  # Longer wait for preprint servers
                        logger.warning(f"Rate limited by bioRxiv, waiting {wait_time}s")
                        await asyncio.sleep(wait_time)
                        continue

                    else:
                        logger.warning(f"bioRxiv API error {response.status}: {endpoint}")
                        return None

            except aiohttp.ClientError as e:
                logger.warning(f"Network error on bioRxiv request: {e}")
                if attempt < self.config.retry_count - 1:
                    await asyncio.sleep(attempt + 1)
                    continue
                return None

            except Exception as e:
                logger.error(f"Error making bioRxiv request: {e}")
                return None

        return None

    async def get_by_doi(self, doi: str) -> Optional[Dict]:
        """
        Get preprint by DOI.

        Args:
            doi: DOI (must be 10.1101/*)

        Returns:
            Dictionary with:
                - title: Paper title
                - pdf_url: Direct PDF URL
                - abstract: Abstract text
                - date: Publication date
                - version: Version number
                - server: 'biorxiv' or 'medrxiv'
        """
        if not doi:
            return None

        # Clean DOI
        doi = doi.replace("https://doi.org/", "").replace("http://doi.org/", "")

        # Check if it's a bioRxiv/medRxiv DOI
        if not self._is_biorxiv_doi(doi):
            logger.debug(f"Not a bioRxiv/medRxiv DOI: {doi}")
            return None

        logger.info(f"Searching bioRxiv/medRxiv for DOI: {doi}")

        # Try both servers
        for server in ["biorxiv", "medrxiv"]:
            endpoint = f"/details/{server}/{doi}"
            data = await self._make_request(endpoint)

            if data and data.get("collection"):
                # Get first (usually latest) version
                paper = data["collection"][0]

                result = {
                    "doi": doi,
                    "title": paper.get("title"),
                    "abstract": paper.get("abstract"),
                    "authors": paper.get("authors"),
                    "date": paper.get("date"),
                    "category": paper.get("category"),
                    "version": paper.get("version"),
                    "server": server,
                    # Construct PDF URL
                    "pdf_url": f"https://www.{server}.org/content/{doi}v{paper.get('version', 1)}.full.pdf",
                    "url": f"https://www.{server}.org/content/{doi}v{paper.get('version', 1)}",
                }

                logger.info(f"✓ Found in {server}: {result['title'][:50]}")
                return result

        logger.debug(f"Not found in bioRxiv or medRxiv: {doi}")
        return None

    async def search_by_title(self, title: str, server: str = "biorxiv", limit: int = 10) -> List[Dict]:
        """
        Search preprints by title.

        Note: bioRxiv API doesn't have direct title search.
        This method searches recent papers and filters by title.

        Args:
            title: Search term
            server: 'biorxiv' or 'medrxiv'
            limit: Max results

        Returns:
            List of matching preprints
        """
        logger.info(f"Searching {server} for title: {title[:50]}")

        # bioRxiv doesn't have full-text search API
        # Instead, we can search recent papers by interval
        # This is a limitation of the bioRxiv API

        logger.warning("bioRxiv API doesn't support title search - use DOI lookup instead")
        return []

    async def fetch_by_id(self, identifier: str) -> Optional[Publication]:
        """
        Fetch a publication by DOI (implements BasePublicationClient interface).

        Args:
            identifier: DOI (must be 10.1101/*)

        Returns:
            Publication if found, None otherwise
        """
        result = await self.get_by_doi(identifier)
        if result:
            return self._convert_to_publication(result)
        return None

    async def search(self, query: str, max_results: int = 100, **kwargs) -> List[Publication]:
        """
        Search for publications (implements BasePublicationClient interface).

        Note: bioRxiv API has limited search capabilities.
        Best used for DOI-based lookup.

        Args:
            query: Search query (DOI recommended)
            max_results: Maximum results
            **kwargs: Additional filters

        Returns:
            List of publications
        """
        # Try as DOI
        if self._is_biorxiv_doi(query):
            result = await self.get_by_doi(query)
            if result:
                return [self._convert_to_publication(result)]

        logger.warning("bioRxiv search works best with DOI - general search not supported")
        return []

    def _convert_to_publication(self, result: Dict) -> Publication:
        """
        Convert bioRxiv/medRxiv result to Publication object.

        Args:
            result: bioRxiv/medRxiv result dictionary

        Returns:
            Publication object
        """
        # Parse authors
        authors = []
        authors_str = result.get("authors", "")
        if authors_str:
            # Authors are semicolon-separated
            authors = [a.strip() for a in authors_str.split(";") if a.strip()]

        # Create publication
        pub = Publication(
            title=result.get("title", ""),
            authors=authors,
            abstract=result.get("abstract", ""),
            publication_date=None,  # Would need to parse date string
            journal=result.get("server", "bioRxiv"),
            doi=result.get("doi"),
            source=PublicationSource.OPENALEX,  # Use OPENALEX as closest match
            metadata={
                "server": result.get("server"),
                "version": result.get("version"),
                "category": result.get("category"),
                "preprint": True,
                "pdf_url": result.get("pdf_url"),
                "url": result.get("url"),
            },
        )

        # Store PDF URL
        if result.get("pdf_url"):
            pub.pdf_url = result["pdf_url"]

        return pub

    async def download_pdf(self, pdf_url: str, output_path: Path) -> bool:
        """
        Download PDF from bioRxiv/medRxiv.

        Args:
            pdf_url: PDF URL
            output_path: Path to save PDF

        Returns:
            True if successful
        """
        if not pdf_url:
            return False

        logger.info(f"Downloading PDF from bioRxiv/medRxiv: {pdf_url}")

        if not self.session:
            connector = aiohttp.TCPConnector(ssl=self.ssl_context)
            self.session = aiohttp.ClientSession(connector=connector)

        try:
            async with self.session.get(pdf_url, timeout=self.config.timeout) as response:
                if response.status == 200:
                    content = await response.read()

                    # Verify PDF
                    if content[:4] != b"%PDF":
                        logger.warning("Not a valid PDF")
                        return False

                    # Save
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(output_path, "wb") as f:
                        f.write(content)

                    file_size = output_path.stat().st_size
                    logger.info(f"✓ Downloaded PDF: {output_path.name} ({file_size} bytes)")
                    return True

                else:
                    logger.warning(f"Failed to download PDF: HTTP {response.status}")
                    return False

        except Exception as e:
            logger.error(f"Error downloading PDF from bioRxiv/medRxiv: {e}")
            return False

    async def close(self):
        """Close the HTTP session."""
        if self.session:
            await self.session.close()
            self.session = None

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
