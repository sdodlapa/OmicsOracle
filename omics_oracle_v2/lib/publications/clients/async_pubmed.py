"""
Async PubMed client for concurrent operations.

Provides async/await versions of PubMed search and fetch operations.
"""

import asyncio
import logging
import os
import ssl
import time
from typing import Any, Dict, List, Optional

import aiohttp
from aiohttp import ClientTimeout, TCPConnector

from omics_oracle_v2.lib.publications.clients.base import APIError, RateLimitError, SearchError
from omics_oracle_v2.lib.publications.config import PubMedConfig
from omics_oracle_v2.lib.publications.models import Publication, PublicationSource

logger = logging.getLogger(__name__)

# SSL bypass for institutional networks (same as sync client)
if os.getenv("PYTHONHTTPSVERIFY", "1") == "0":
    logger.info("SSL verification disabled for async PubMed (PYTHONHTTPSVERIFY=0)")


class AsyncPubMedClient:
    """
    Async PubMed client using NCBI E-utilities API.

    Features:
    - Async HTTP requests with aiohttp
    - Concurrent search and fetch operations
    - Rate limiting (max 10 requests/second with API key, 3/second without)
    - Automatic retries with exponential backoff
    - Batch fetching

    Example:
        >>> client = AsyncPubMedClient(email="user@example.com")
        >>> results = await client.search_async("cancer genomics", max_results=50)
        >>> publications = await client.fetch_batch_async(pmid_list)
    """

    def __init__(
        self,
        email: str,
        api_key: Optional[str] = None,
        requests_per_second: float = 3.0,
        max_retries: int = 3,
    ):
        """
        Initialize async PubMed client.

        Args:
            email: Email for NCBI (required)
            api_key: NCBI API key (increases rate limit to 10 req/s)
            requests_per_second: Max requests per second
            max_retries: Max retry attempts on failure
        """
        self.email = email
        self.api_key = api_key
        self.max_retries = max_retries

        # Rate limiting
        self.requests_per_second = requests_per_second
        self._request_times = []
        self._rate_limit_lock = asyncio.Lock()

        # Base URLs
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        self.esearch_url = f"{self.base_url}/esearch.fcgi"
        self.efetch_url = f"{self.base_url}/efetch.fcgi"
        self.esummary_url = f"{self.base_url}/esummary.fcgi"

        # Session (created on first request)
        self._session = None

        logger.info(f"Async PubMed client initialized (rate={requests_per_second} req/s)")

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            timeout = ClientTimeout(total=30)

            # Create SSL context with verification bypass if needed
            ssl_context = None
            if os.getenv("PYTHONHTTPSVERIFY", "1") == "0":
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE

            # Create connector with SSL context
            connector = TCPConnector(ssl=ssl_context) if ssl_context else None

            self._session = aiohttp.ClientSession(timeout=timeout, connector=connector)
        return self._session

    async def close(self):
        """Close the aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def _wait_for_rate_limit(self):
        """Wait if necessary to respect rate limiting."""
        async with self._rate_limit_lock:
            current_time = time.time()

            # Remove old request times (older than 1 second)
            self._request_times = [t for t in self._request_times if current_time - t < 1.0]

            # Check if we're at the limit
            if len(self._request_times) >= self.requests_per_second:
                # Wait until oldest request is >1 second old
                wait_time = 1.0 - (current_time - self._request_times[0])
                if wait_time > 0:
                    logger.debug(f"Rate limit reached, waiting {wait_time:.2f}s")
                    await asyncio.sleep(wait_time)
                    # Clean up again
                    current_time = time.time()
                    self._request_times = [t for t in self._request_times if current_time - t < 1.0]

            # Record this request
            self._request_times.append(current_time)

    async def _make_request(self, url: str, params: Dict[str, Any]) -> str:
        """
        Make HTTP request with rate limiting and retries.

        Args:
            url: API endpoint URL
            params: Query parameters

        Returns:
            Response text

        Raises:
            APIError: On request failure after retries
        """
        # Add API key if available
        if self.api_key:
            params["api_key"] = self.api_key

        session = await self._get_session()

        for attempt in range(self.max_retries):
            try:
                # Rate limiting
                await self._wait_for_rate_limit()

                # Make request
                async with session.get(url, params=params) as response:
                    if response.status == 429:
                        # Rate limit exceeded
                        wait_time = 2**attempt
                        logger.warning(f"Rate limit exceeded, waiting {wait_time}s")
                        await asyncio.sleep(wait_time)
                        continue

                    response.raise_for_status()
                    return await response.text()

            except aiohttp.ClientError as e:
                if attempt < self.max_retries - 1:
                    wait_time = 2**attempt
                    logger.warning(f"Request failed (attempt {attempt + 1}): {e}. Retrying in {wait_time}s")
                    await asyncio.sleep(wait_time)
                else:
                    raise APIError(f"Request failed after {self.max_retries} attempts: {e}")

    async def search_async(
        self,
        query: str,
        max_results: int = 50,
        sort: str = "relevance",
        date_range: Optional[tuple] = None,
    ) -> List[str]:
        """
        Search PubMed asynchronously.

        Args:
            query: Search query
            max_results: Maximum results to return
            sort: Sort order ('relevance', 'pub_date', 'author')
            date_range: Optional (min_date, max_date) tuple

        Returns:
            List of PMIDs

        Raises:
            SearchError: On search failure
        """
        params = {
            "db": "pubmed",
            "term": query,
            "retmax": max_results,
            "retmode": "json",
            "email": self.email,
            "tool": "OmicsOracle",
        }

        # Add sort parameter
        if sort == "pub_date":
            params["sort"] = "pub+date"
        elif sort == "author":
            params["sort"] = "author"

        # Add date range
        if date_range:
            min_date, max_date = date_range
            params["mindate"] = min_date
            params["maxdate"] = max_date

        try:
            response_text = await self._make_request(self.esearch_url, params)

            # Parse JSON response
            import json

            data = json.loads(response_text)

            if "esearchresult" in data:
                pmids = data["esearchresult"].get("idlist", [])
                count = int(data["esearchresult"].get("count", 0))
                logger.info(f"PubMed search found {count} results, returning {len(pmids)} PMIDs")
                return pmids
            else:
                raise SearchError(f"Unexpected response format: {response_text[:200]}")

        except Exception as e:
            logger.error(f"PubMed search failed: {e}")
            raise SearchError(f"Search failed: {e}")

    async def fetch_async(self, pmid: str) -> Optional[Publication]:
        """
        Fetch single publication by PMID asynchronously.

        Args:
            pmid: PubMed ID

        Returns:
            Publication object or None
        """
        publications = await self.fetch_batch_async([pmid])
        return publications[0] if publications else None

    async def fetch_batch_async(self, pmids: List[str], batch_size: int = 100) -> List[Publication]:
        """
        Fetch multiple publications concurrently.

        Args:
            pmids: List of PMIDs
            batch_size: Number of PMIDs to fetch per request

        Returns:
            List of Publication objects
        """
        if not pmids:
            return []

        all_publications = []

        # Process in batches
        for i in range(0, len(pmids), batch_size):
            batch_pmids = pmids[i : i + batch_size]

            params = {
                "db": "pubmed",
                "id": ",".join(batch_pmids),
                "retmode": "xml",
                "rettype": "abstract",
                "email": self.email,
                "tool": "OmicsOracle",
            }

            try:
                response_text = await self._make_request(self.efetch_url, params)
                publications = self._parse_pubmed_xml(response_text)
                all_publications.extend(publications)

                logger.debug(f"Fetched {len(publications)} publications from batch {i//batch_size + 1}")

            except Exception as e:
                logger.error(f"Failed to fetch batch {i}-{i+batch_size}: {e}")

        return all_publications

    def _parse_pubmed_xml(self, xml_text: str) -> List[Publication]:
        """
        Parse PubMed XML response.

        Args:
            xml_text: XML response from efetch

        Returns:
            List of Publication objects
        """
        import xml.etree.ElementTree as ET

        publications = []

        try:
            root = ET.fromstring(xml_text)

            for article in root.findall(".//PubmedArticle"):
                try:
                    pub = self._parse_article(article)
                    if pub:
                        publications.append(pub)
                except Exception as e:
                    logger.warning(f"Failed to parse article: {e}")

        except ET.ParseError as e:
            logger.error(f"Failed to parse XML: {e}")

        return publications

    def _parse_article(self, article) -> Optional[Publication]:
        """Parse single PubMed article XML."""
        try:
            # PMID
            pmid_elem = article.find(".//PMID")
            pmid = pmid_elem.text if pmid_elem is not None else None

            # Title
            title_elem = article.find(".//ArticleTitle")
            title = title_elem.text if title_elem is not None else "No title"

            # Abstract
            abstract_parts = []
            for abstract_text in article.findall(".//AbstractText"):
                if abstract_text.text:
                    abstract_parts.append(abstract_text.text)
            abstract = " ".join(abstract_parts) if abstract_parts else None

            # Authors
            authors = []
            for author in article.findall(".//Author"):
                last_name = author.findtext("LastName", "")
                fore_name = author.findtext("ForeName", "")
                initials = author.findtext("Initials", "")

                if last_name:
                    author_name = f"{last_name} {initials if initials else fore_name}".strip()
                    authors.append(author_name)

            # Journal
            journal_elem = article.find(".//Journal/Title")
            journal = journal_elem.text if journal_elem is not None else None

            # Publication year
            year_elem = article.find(".//PubDate/Year")
            year = int(year_elem.text) if year_elem is not None and year_elem.text else None

            # DOI
            doi = None
            for article_id in article.findall(".//ArticleId"):
                if article_id.get("IdType") == "doi":
                    doi = article_id.text
                    break

            # Create publication
            return Publication(
                title=title,
                abstract=abstract,
                authors=authors or [],
                journal=journal,
                year=year,
                pmid=pmid,
                doi=doi,
                source=PublicationSource.PUBMED,
                url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else None,
            )

        except Exception as e:
            logger.error(f"Error parsing article: {e}")
            return None

    async def search_and_fetch_async(
        self, query: str, max_results: int = 50, sort: str = "relevance"
    ) -> List[Publication]:
        """
        Search and fetch publications in one operation.

        Args:
            query: Search query
            max_results: Maximum results
            sort: Sort order

        Returns:
            List of Publication objects
        """
        # Search for PMIDs
        pmids = await self.search_async(query, max_results, sort)

        if not pmids:
            logger.info(f"No results found for query: {query}")
            return []

        # Fetch publications
        publications = await self.fetch_batch_async(pmids)

        logger.info(f"Retrieved {len(publications)} publications for query: {query}")
        return publications


# Convenience wrapper for compatibility
class AsyncPubMedWrapper:
    """Wrapper to make async client compatible with sync interface."""

    def __init__(self, config: PubMedConfig):
        self.client = AsyncPubMedClient(
            email=config.email, api_key=config.api_key, requests_per_second=config.requests_per_second
        )

    async def search(self, query: str, max_results: int = 50) -> List[Publication]:
        """Search and fetch publications."""
        return await self.client.search_and_fetch_async(query, max_results)

    async def close(self):
        """Close the client."""
        await self.client.close()
