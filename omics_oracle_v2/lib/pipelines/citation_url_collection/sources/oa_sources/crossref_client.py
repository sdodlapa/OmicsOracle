"""
Crossref API client for publisher full-text links and metadata.

Crossref is a DOI registration agency providing metadata for scholarly content
from publishers. Many publishers provide full-text links through Crossref.

Coverage: 130M+ DOIs from academic publishers
API: https://api.crossref.org/works/{DOI}
Rate Limits: 50 req/second with Crossref-Plus (free with email)
Full-Text Access: Publisher-provided links (varies by publisher/agreement)

API Documentation: https://github.com/CrossRef/rest-api-doc

Example:
    >>> from omics_oracle_v2.lib.enrichment.fulltext.sources.oa_sources.crossref_client import CrossrefClient
    >>>
    >>> async with CrossrefClient(email="researcher@university.edu") as client:
    >>>     # Get metadata by DOI
    >>>     paper = await client.get_by_doi("10.1371/journal.pone.0123456")
    >>>
    >>>     # Check for full-text links
    >>>     if paper and paper.get('fulltext_urls'):
    >>>         print(f"Full-text URLs: {paper['fulltext_urls']}")
"""

import asyncio
import logging
import ssl
from typing import Dict, List, Optional
from urllib.parse import quote

import aiohttp

from omics_oracle_v2.lib.search_engines.citations.base import BasePublicationClient
from omics_oracle_v2.lib.search_engines.citations.models import Publication, PublicationSource

logger = logging.getLogger(__name__)


class CrossrefConfig:
    """
    Configuration for Crossref API.

    Attributes:
        enable: Enable Crossref client
        api_url: Base API URL
        email: Email for polite pool (Crossref-Plus, faster rate limits)
        timeout: Request timeout in seconds
        retry_count: Number of retries on failure
        rate_limit_per_second: Requests per second (50 with email in polite pool)
        user_agent: Custom user agent string
    """

    def __init__(
        self,
        enable: bool = True,
        api_url: str = "https://api.crossref.org",
        email: Optional[str] = None,
        timeout: int = 30,
        retry_count: int = 3,
        rate_limit_per_second: int = 50,  # Polite pool with email
        user_agent: str = "OmicsOracle/1.0 (Academic Research Tool)",
    ):
        self.enable = enable
        self.api_url = api_url
        self.email = email
        self.timeout = timeout
        self.retry_count = retry_count
        self.rate_limit_per_second = rate_limit_per_second
        self.user_agent = user_agent
        self.min_request_interval = 1.0 / rate_limit_per_second


class CrossrefClient(BasePublicationClient):
    """
    Client for Crossref API.

    Crossref provides comprehensive metadata for 130M+ scholarly works including:
    - DOI metadata (title, authors, journal, dates)
    - Publisher information
    - Full-text links (when provided by publisher)
    - References and citations
    - Licensing information
    - Abstract (when available)

    Note: Full-text access depends on publisher policies and institutional access.
    Not all DOIs have full-text links available.
    """

    def __init__(self, config: Optional[CrossrefConfig] = None, email: Optional[str] = None):
        """
        Initialize Crossref client.

        Args:
            config: Crossref configuration
            email: Email for polite pool (can also be set in config)
        """
        self.config = config or CrossrefConfig(email=email)
        self.session: Optional[aiohttp.ClientSession] = None
        self.last_request_time: float = 0

        # Create SSL context that bypasses certificate verification
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE

        logger.info(
            f"Initialized Crossref client "
            f"(rate limit: {self.config.rate_limit_per_second} req/s, "
            f"polite pool: {bool(self.config.email)})"
        )

    @property
    def source_name(self) -> str:
        """Return the name of this source."""
        return "Crossref"

    async def __aenter__(self):
        """Async context manager entry."""
        headers = {"User-Agent": self.config.user_agent}

        # Add email to User-Agent for polite pool (Crossref-Plus)
        if self.config.email:
            headers["User-Agent"] = f"{self.config.user_agent}; mailto:{self.config.email}"

        connector = aiohttp.TCPConnector(ssl=self.ssl_context)
        self.session = aiohttp.ClientSession(
            connector=connector,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=self.config.timeout),
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def close(self) -> None:
        """Close the aiohttp session.

        Week 3 Day 3: Added explicit close() method for proper resource cleanup.
        """
        if self.session:
            await self.session.close()
            self.session = None

    async def _rate_limit(self):
        """Enforce rate limiting."""
        current_time = asyncio.get_event_loop().time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.config.min_request_interval:
            delay = self.config.min_request_interval - time_since_last
            await asyncio.sleep(delay)

        self.last_request_time = asyncio.get_event_loop().time()

    async def _make_request(self, endpoint: str) -> Optional[Dict]:
        """
        Make request to Crossref API with retry logic.

        Args:
            endpoint: API endpoint (relative to base URL)

        Returns:
            JSON response as dict, or None on failure
        """
        if not self.session:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")

        await self._rate_limit()

        url = f"{self.config.api_url}{endpoint}"

        for attempt in range(self.config.retry_count):
            try:
                async with self.session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("message")  # Crossref wraps data in "message"
                    elif response.status == 404:
                        logger.debug(f"Not found in Crossref: {endpoint}")
                        return None
                    else:
                        logger.warning(
                            f"Crossref API returned status {response.status} (attempt {attempt + 1})"
                        )

            except asyncio.TimeoutError:
                logger.warning(f"Crossref API timeout (attempt {attempt + 1})")
            except Exception as e:
                logger.warning(f"Crossref API error: {e} (attempt {attempt + 1})")

            if attempt < self.config.retry_count - 1:
                await asyncio.sleep(2**attempt)  # Exponential backoff

        return None

    async def get_by_doi(self, doi: str) -> Optional[Dict]:
        """
        Get paper metadata by DOI.

        Args:
            doi: DOI (e.g., "10.1371/journal.pone.0123456")

        Returns:
            Paper metadata dict with full-text links if available, or None
        """
        # Clean DOI
        clean_doi = doi.strip()
        if clean_doi.startswith("http"):
            # Extract DOI from URL
            clean_doi = clean_doi.split("doi.org/")[-1]

        endpoint = f"/works/{quote(clean_doi, safe='')}"

        data = await self._make_request(endpoint)
        if not data:
            return None

        return self._parse_work(data)

    def _parse_work(self, work: Dict) -> Dict:
        """
        Parse Crossref work metadata.

        Args:
            work: Crossref work object

        Returns:
            Standardized paper metadata dict
        """
        # Extract basic metadata
        doi = work.get("DOI")
        title = work.get("title", [])
        title = title[0] if title else None

        # Authors
        authors = []
        for author in work.get("author", []):
            given = author.get("given", "")
            family = author.get("family", "")
            authors.append(f"{given} {family}".strip())

        # Journal
        container_title = work.get("container-title", [])
        journal = container_title[0] if container_title else None

        # Year
        published = work.get("published-print") or work.get("published-online")
        year = None
        if published and "date-parts" in published:
            year = published["date-parts"][0][0] if published["date-parts"][0] else None

        # Abstract (if available)
        abstract = work.get("abstract")

        # Full-text links
        fulltext_urls = []
        for link in work.get("link", []):
            if link.get("intended-application") == "text-mining":
                fulltext_urls.append(link.get("URL"))
            elif link.get("content-type") in ["application/pdf", "text/html"]:
                fulltext_urls.append(link.get("URL"))

        # Publisher
        publisher = work.get("publisher")

        # License (indicates OA status)
        licenses = work.get("license", [])
        is_open_access = any(
            "creativecommons.org" in lic.get("URL", "") or "open" in lic.get("URL", "").lower()
            for lic in licenses
        )

        # Volume, issue, pages
        volume = work.get("volume")
        issue = work.get("issue")
        page = work.get("page")

        return {
            "doi": doi,
            "title": title,
            "authors": authors,
            "journal": journal,
            "year": year,
            "abstract": abstract,
            "fulltext_urls": fulltext_urls,
            "publisher": publisher,
            "is_open_access": is_open_access,
            "licenses": licenses,
            "volume": volume,
            "issue": issue,
            "page": page,
            "url": f"https://doi.org/{doi}" if doi else None,
        }

    async def search(self, query: str, max_results: int = 10) -> List[Dict]:
        """
        Search for papers.

        Args:
            query: Search query
            max_results: Maximum number of results

        Returns:
            List of paper metadata dicts
        """
        endpoint = f"/works?query={quote(query)}&rows={max_results}"

        data = await self._make_request(endpoint)
        if not data or "items" not in data:
            return []

        results = []
        for work in data["items"]:
            try:
                parsed = self._parse_work(work)
                results.append(parsed)
            except Exception as e:
                logger.warning(f"Error parsing Crossref work: {e}")
                continue

        logger.info(f"Found {len(results)} papers for query: {query}")
        return results

    async def fetch_by_id(self, identifier: str) -> Optional[Publication]:
        """
        Fetch publication by identifier (implements BasePublicationClient).

        Args:
            identifier: DOI

        Returns:
            Publication object, or None if not found
        """
        paper = await self.get_by_doi(identifier)
        if not paper:
            return None

        return self._convert_to_publication(paper)

    def _convert_to_publication(self, paper: Dict) -> Publication:
        """
        Convert Crossref paper dict to Publication object.

        Args:
            paper: Paper metadata from Crossref API

        Returns:
            Publication object
        """
        return Publication(
            title=paper.get("title"),
            authors=", ".join(paper.get("authors", [])),
            journal=paper.get("journal"),
            year=str(paper.get("year")) if paper.get("year") else None,
            doi=paper.get("doi"),
            pmid=None,
            pmcid=None,
            abstract=paper.get("abstract"),
            url=paper.get("url"),
            source=PublicationSource.OTHER,  # Crossref is metadata source
            metadata={
                "fulltext_urls": paper.get("fulltext_urls", []),
                "publisher": paper.get("publisher"),
                "is_open_access": paper.get("is_open_access", False),
                "licenses": paper.get("licenses", []),
                "volume": paper.get("volume"),
                "issue": paper.get("issue"),
                "page": paper.get("page"),
            },
        )


# Convenience functions
async def get_fulltext_links(doi: str) -> List[str]:
    """
    Get full-text links for a DOI (convenience function).

    Args:
        doi: DOI

    Returns:
        List of full-text URLs
    """
    async with CrossrefClient() as client:
        paper = await client.get_by_doi(doi)
        if paper:
            return paper.get("fulltext_urls", [])
        return []
