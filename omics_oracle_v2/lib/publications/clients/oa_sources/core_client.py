"""
CORE (Connecting Open Access Repositories) API client.

CORE aggregates open access research papers from repositories worldwide.
Provides access to 45M+ full-text papers with a free API.

API Documentation: https://core.ac.uk/documentation/api
Rate Limits: Free tier with API key (generous limits)
Coverage: 45M+ open access full texts

Example:
    >>> from omics_oracle_v2.lib.publications.clients.oa_sources import COREClient
    >>>
    >>> client = COREClient(api_key="YOUR_API_KEY")
    >>>
    >>> # Search by DOI
    >>> result = await client.get_fulltext_by_doi("10.1038/nature12345")
    >>> if result and result.get('downloadUrl'):
    ...     print(f"PDF available: {result['downloadUrl']}")
    >>>
    >>> # Search by title
    >>> results = await client.search_by_title("CRISPR gene editing")
"""

import asyncio
import logging
import ssl
import time
from pathlib import Path
from typing import Dict, List, Optional

import aiohttp

from omics_oracle_v2.lib.publications.clients.base import BasePublicationClient
from omics_oracle_v2.lib.publications.models import Publication, PublicationSource

logger = logging.getLogger(__name__)


class COREConfig:
    """
    Configuration for CORE API.

    Attributes:
        api_key: CORE API key (required)
        api_url: Base API URL
        timeout: Request timeout in seconds
        retry_count: Number of retries on failure
        rate_limit_per_second: Requests per second
    """

    def __init__(
        self,
        api_key: str,
        api_url: str = "https://api.core.ac.uk/v3",
        timeout: int = 30,
        retry_count: int = 3,
        rate_limit_per_second: int = 10,
    ):
        if not api_key:
            raise ValueError("CORE API key is required")

        self.api_key = api_key
        self.api_url = api_url
        self.timeout = timeout
        self.retry_count = retry_count
        self.rate_limit_per_second = rate_limit_per_second
        self.min_request_interval = 1.0 / rate_limit_per_second


class COREClient(BasePublicationClient):
    """
    Client for CORE (Connecting Open Access Repositories) API.

    CORE aggregates research papers from thousands of open access repositories
    worldwide, providing access to 45M+ full-text papers.

    Features:
    - DOI-based search
    - Title-based search
    - Direct PDF download URLs
    - Full-text content
    - Metadata enrichment
    """

    def __init__(self, config: Optional[COREConfig] = None, api_key: Optional[str] = None):
        """
        Initialize CORE client.

        Args:
            config: CORE configuration
            api_key: API key (alternative to config)
        """
        if config:
            self.config = config
        elif api_key:
            self.config = COREConfig(api_key=api_key)
        else:
            raise ValueError("Either config or api_key must be provided")

        super().__init__(self.config)
        self.last_request_time = 0.0
        self.session = None

        # Create SSL context that doesn't verify certificates (for Georgia Tech VPN)
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE

        logger.info(f"CORE client initialized with API URL: {self.config.api_url}")

    @property
    def source_name(self) -> str:
        """Get the name of this publication source."""
        return "core"

    def _rate_limit(self):
        """Enforce rate limiting."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.config.min_request_interval:
            sleep_time = self.config.min_request_interval - elapsed
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    async def _make_request(
        self, endpoint: str, params: Optional[Dict] = None, method: str = "GET"
    ) -> Optional[Dict]:
        """
        Make API request with retry logic.

        Args:
            endpoint: API endpoint (e.g., "/works/search")
            params: Query parameters
            method: HTTP method

        Returns:
            Response JSON or None on failure
        """
        self._rate_limit()

        url = f"{self.config.api_url}{endpoint}"
        params = params or {}
        params["apiKey"] = self.config.api_key

        if not self.session:
            connector = aiohttp.TCPConnector(ssl=self.ssl_context)
            self.session = aiohttp.ClientSession(connector=connector)

        for attempt in range(self.config.retry_count):
            try:
                async with self.session.get(url, params=params, timeout=self.config.timeout) as response:
                    if response.status == 200:
                        return await response.json()

                    elif response.status == 404:
                        logger.debug(f"Not found in CORE: {endpoint}")
                        return None

                    elif response.status == 429:
                        # Rate limited
                        wait_time = (attempt + 1) * 2
                        logger.warning(f"Rate limited by CORE, waiting {wait_time}s")
                        await asyncio.sleep(wait_time)
                        continue

                    elif response.status == 401:
                        logger.error("CORE API key invalid or expired")
                        return None

                    else:
                        logger.warning(f"CORE API error {response.status}: {endpoint}")
                        return None

            except aiohttp.ClientError as e:
                logger.warning(f"Network error on CORE request: {e}")
                if attempt < self.config.retry_count - 1:
                    await asyncio.sleep(attempt + 1)
                    continue
                return None

            except Exception as e:
                logger.error(f"Error making CORE request: {e}")
                return None

        return None

    async def get_fulltext_by_doi(self, doi: str) -> Optional[Dict]:
        """
        Get full text or PDF URL by DOI.

        Args:
            doi: Digital Object Identifier

        Returns:
            Dictionary with:
                - downloadUrl: Direct PDF download URL
                - fullText: Full text content (if available)
                - title: Paper title
                - metadata: Additional metadata
        """
        if not doi:
            return None

        # Clean DOI
        doi = doi.replace("https://doi.org/", "").replace("http://doi.org/", "")

        logger.info(f"Searching CORE for DOI: {doi}")

        # Search by DOI
        params = {"q": f'doi:"{doi}"', "limit": 1}

        data = await self._make_request("/works/search", params=params)

        if not data or not data.get("results"):
            logger.debug(f"No results in CORE for DOI: {doi}")
            return None

        # Get first result
        work = data["results"][0]

        result = {
            "id": work.get("id"),
            "title": work.get("title"),
            "downloadUrl": work.get("downloadUrl"),
            "fullText": work.get("fullText"),
            "abstract": work.get("abstract"),
            "authors": work.get("authors", []),
            "publishedDate": work.get("publishedDate"),
            "doi": work.get("doi"),
            "sourceFulltextUrls": work.get("sourceFulltextUrls", []),
            "metadata": {
                "core_id": work.get("id"),
                "language": work.get("language"),
                "publisher": work.get("publisher"),
                "identifiers": work.get("identifiers", []),
            },
        }

        logger.info(f"✓ Found in CORE: {result['title'][:50]}")

        # Log what's available
        has_pdf = bool(result.get("downloadUrl"))
        has_fulltext = bool(result.get("fullText"))
        has_sources = bool(result.get("sourceFulltextUrls"))

        logger.debug(f"CORE result - PDF: {has_pdf}, FullText: {has_fulltext}, Sources: {has_sources}")

        return result

    async def search_by_title(self, title: str, limit: int = 5) -> List[Dict]:
        """
        Search for papers by title.

        Args:
            title: Paper title (fuzzy matching supported)
            limit: Maximum results to return

        Returns:
            List of matching works
        """
        if not title:
            return []

        logger.info(f"Searching CORE by title: {title[:50]}")

        params = {"q": f'title:"{title}"', "limit": limit}

        data = await self._make_request("/works/search", params=params)

        if not data or not data.get("results"):
            logger.debug(f"No results in CORE for title: {title[:50]}")
            return []

        results = []
        for work in data["results"]:
            results.append(
                {
                    "id": work.get("id"),
                    "title": work.get("title"),
                    "downloadUrl": work.get("downloadUrl"),
                    "fullText": work.get("fullText"),
                    "doi": work.get("doi"),
                    "abstract": work.get("abstract"),
                }
            )

        logger.info(f"Found {len(results)} results in CORE")
        return results

    async def download_pdf(self, download_url: str, output_path: Path) -> bool:
        """
        Download PDF from CORE.

        Args:
            download_url: PDF download URL from CORE
            output_path: Path to save PDF

        Returns:
            True if successful, False otherwise
        """
        if not download_url:
            return False

        logger.info(f"Downloading PDF from CORE: {download_url}")

        if not self.session:
            connector = aiohttp.TCPConnector(ssl=self.ssl_context)
            self.session = aiohttp.ClientSession(connector=connector)

        try:
            # Add API key to URL
            params = {"apiKey": self.config.api_key}

            async with self.session.get(download_url, params=params, timeout=self.config.timeout) as response:
                if response.status == 200:
                    # Verify it's a PDF
                    content_type = response.headers.get("Content-Type", "")
                    content = await response.read()

                    # Check PDF magic number
                    if content[:4] != b"%PDF":
                        logger.warning(f"Not a valid PDF (Content-Type: {content_type})")
                        return False

                    # Save to file
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
            logger.error(f"Error downloading PDF from CORE: {e}")
            return False

    async def fetch_by_id(self, identifier: str) -> Optional[Publication]:
        """
        Fetch a publication by DOI or CORE ID (implements BasePublicationClient interface).

        Args:
            identifier: DOI or CORE ID

        Returns:
            Publication if found, None otherwise
        """
        # Try as DOI first
        result = await self.get_fulltext_by_doi(identifier)
        if result:
            return self._convert_work_to_publication(result)

        # Try as CORE ID
        data = await self._make_request(f"/works/{identifier}")
        if data:
            return self._convert_work_to_publication(data)

        return None

    async def search(self, query: str, max_results: int = 100, **kwargs) -> List[Publication]:
        """
        Search for publications (implements BasePublicationClient interface).

        Args:
            query: Search query
            max_results: Maximum results to return
            **kwargs: Additional filters

        Returns:
            List of publications
        """
        logger.info(f"Searching CORE: {query}")

        params = {"q": query, "limit": min(max_results, 100)}

        data = await self._make_request("/works/search", params=params)

        if not data or not data.get("results"):
            return []

        publications = []
        for work in data["results"]:
            try:
                pub = self._convert_work_to_publication(work)
                publications.append(pub)
            except Exception as e:
                logger.warning(f"Error converting CORE work: {e}")
                continue

        logger.info(f"Found {len(publications)} publications in CORE")
        return publications

    def _convert_work_to_publication(self, work: Dict) -> Publication:
        """
        Convert CORE work to Publication object.

        Args:
            work: CORE work dictionary

        Returns:
            Publication object
        """
        # Extract authors
        authors = []
        for author in work.get("authors", []):
            if isinstance(author, dict):
                name = author.get("name", "")
            else:
                name = str(author)
            if name:
                authors.append(name)

        # Create publication
        pub = Publication(
            title=work.get("title", ""),
            authors=authors,
            abstract=work.get("abstract", ""),
            publication_date=None,  # CORE doesn't always provide this
            journal=work.get("publisher"),
            doi=work.get("doi"),
            source=PublicationSource.OPENALEX,  # Use OPENALEX as closest match
            metadata={
                "core_id": work.get("id"),
                "download_url": work.get("downloadUrl"),
                "full_text_available": bool(work.get("fullText")),
                "source_fulltext_urls": work.get("sourceFulltextUrls", []),
                "language": work.get("language"),
                "year_published": work.get("yearPublished"),
            },
        )

        # Store PDF URL if available
        if work.get("downloadUrl"):
            pub.pdf_url = work["downloadUrl"]

        return pub

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
