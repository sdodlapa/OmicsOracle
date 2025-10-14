"""
arXiv preprint repository client for full-text access.

arXiv is a free distribution service and open-access archive for scholarly articles
in physics, mathematics, computer science, quantitative biology, and more.

Coverage: 2M+ preprints (primarily physics, CS, math, some biology)
API: http://export.arxiv.org/api/query
Rate Limits: 1 request per 3 seconds (polite policy)
PDF Access: Direct PDF URLs available for all papers

API Documentation: https://info.arxiv.org/help/api/index.html

Example:
    >>> from omics_oracle_v2.lib.enrichment.fulltext.sources.oa_sources.arxiv_client import ArXivClient
    >>>
    >>> async with ArXivClient() as client:
    >>>     # Search by arXiv ID
    >>>     paper = await client.get_by_arxiv_id("2301.12345")
    >>>
    >>>     # Search by title
    >>>     papers = await client.search_by_title("quantum computing")
    >>>
    >>>     # Download PDF
    >>>     await client.download_pdf(paper['pdf_url'], Path("paper.pdf"))
"""

import asyncio
import logging
import re
import ssl
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional

import aiohttp
from pydantic import BaseModel, Field

from omics_oracle_v2.lib.search_engines.citations.base import BasePublicationClient
from omics_oracle_v2.lib.search_engines.citations.models import Publication, PublicationSource

logger = logging.getLogger(__name__)


class ArXivConfig(BaseModel):
    """
    Configuration for arXiv API.

    Attributes:
        enable: Enable arXiv client
        api_url: Base API URL
        timeout: Request timeout in seconds
        retry_count: Number of retries on failure
        rate_limit_delay: Delay between requests (3 seconds per arXiv policy)
        max_results_per_query: Maximum results per search query
        user_agent: Custom user agent string
    """

    enable: bool = Field(default=True, description="Enable arXiv client")
    api_url: str = Field(default="http://export.arxiv.org/api/query", description="Base API URL for arXiv")
    timeout: int = Field(default=30, description="Request timeout in seconds", ge=1)
    retry_count: int = Field(default=3, description="Number of retries on failure", ge=0)
    rate_limit_delay: float = Field(
        default=3.0, description="Delay between requests (3 seconds per arXiv policy)", ge=0.1
    )
    max_results_per_query: int = Field(
        default=100, description="Maximum results per search query", ge=1, le=1000
    )
    user_agent: str = Field(
        default="OmicsOracle/1.0 (Academic Research Tool; mailto:research@university.edu)",
        description="Custom user agent string",
    )


class ArXivClient(BasePublicationClient):
    """
    Client for arXiv preprint repository.

    arXiv provides free access to 2M+ preprints primarily in:
    - Physics
    - Mathematics
    - Computer Science
    - Quantitative Biology
    - Quantitative Finance
    - Statistics
    - Electrical Engineering
    - Economics

    All papers have freely available PDFs.
    """

    # arXiv ID patterns
    # Old format: math/0703324 (subject/YYMMNNN)
    # New format: 2301.12345 (YYMM.NNNNN)
    ARXIV_ID_PATTERN = re.compile(r"(?:arxiv:)?(\d{4}\.\d{4,5}|[a-z\-]+/\d{7})", re.IGNORECASE)

    # Atom namespace for parsing XML responses
    ATOM_NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}

    def __init__(self, config: Optional[ArXivConfig] = None):
        """
        Initialize arXiv client.

        Args:
            config: arXiv configuration
        """
        self.config = config or ArXivConfig()
        self.session: Optional[aiohttp.ClientSession] = None
        self.last_request_time: float = 0

        # Create SSL context that bypasses certificate verification
        # (needed for some institutional VPN environments like Georgia Tech)
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE

        logger.info(f"Initialized arXiv client (rate limit: 1 req/{self.config.rate_limit_delay}s)")

    @property
    def source_name(self) -> str:
        """Return the name of this source."""
        return "arXiv"

    async def __aenter__(self):
        """Async context manager entry."""
        connector = aiohttp.TCPConnector(ssl=self.ssl_context)
        self.session = aiohttp.ClientSession(
            connector=connector,
            headers={"User-Agent": self.config.user_agent},
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
        """Enforce rate limiting (3 seconds between requests per arXiv policy)."""
        current_time = asyncio.get_event_loop().time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.config.rate_limit_delay:
            delay = self.config.rate_limit_delay - time_since_last
            logger.debug(f"Rate limiting: sleeping {delay:.2f}s")
            await asyncio.sleep(delay)

        self.last_request_time = asyncio.get_event_loop().time()

    async def _make_request(self, params: Dict) -> Optional[str]:
        """
        Make request to arXiv API with retry logic.

        Args:
            params: Query parameters

        Returns:
            XML response as string, or None on failure
        """
        if not self.session:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")

        await self._rate_limit()

        for attempt in range(self.config.retry_count):
            try:
                async with self.session.get(self.config.api_url, params=params) as response:
                    if response.status == 200:
                        return await response.text()
                    else:
                        logger.warning(f"arXiv API returned status {response.status} (attempt {attempt + 1})")

            except asyncio.TimeoutError:
                logger.warning(f"arXiv API timeout (attempt {attempt + 1})")
            except Exception as e:
                logger.warning(f"arXiv API error: {e} (attempt {attempt + 1})")

            if attempt < self.config.retry_count - 1:
                await asyncio.sleep(2**attempt)  # Exponential backoff

        return None

    def _extract_arxiv_id(self, text: str) -> Optional[str]:
        """
        Extract arXiv ID from text (DOI, URL, or plain ID).

        Args:
            text: Text potentially containing arXiv ID

        Returns:
            Normalized arXiv ID, or None
        """
        match = self.ARXIV_ID_PATTERN.search(text)
        if match:
            return match.group(1)
        return None

    def _parse_entry(self, entry: ET.Element) -> Optional[Dict]:
        """
        Parse an arXiv entry from XML.

        Args:
            entry: XML entry element

        Returns:
            Paper metadata dict, or None on error
        """
        try:
            # Extract arXiv ID from entry ID
            entry_id_elem = entry.find("atom:id", self.ATOM_NS)
            if entry_id_elem is None or not entry_id_elem.text:
                logger.debug("Missing entry ID in arXiv response")
                return None

            entry_id = entry_id_elem.text
            arxiv_id = entry_id.split("/abs/")[-1].replace("v1", "").replace("v2", "").replace("v3", "")

            # Title
            title_elem = entry.find("atom:title", self.ATOM_NS)
            title = title_elem.text.strip() if title_elem is not None and title_elem.text else None

            # Summary (abstract)
            summary_elem = entry.find("atom:summary", self.ATOM_NS)
            abstract = summary_elem.text.strip() if summary_elem is not None and summary_elem.text else None

            # Authors
            authors = []
            for author in entry.findall("atom:author", self.ATOM_NS):
                name_elem = author.find("atom:name", self.ATOM_NS)
                if name_elem is not None:
                    authors.append(name_elem.text)

            # Published date
            published_elem = entry.find("atom:published", self.ATOM_NS)
            published = published_elem.text if published_elem is not None else None

            # Updated date
            updated_elem = entry.find("atom:updated", self.ATOM_NS)
            updated = updated_elem.text if updated_elem is not None else None

            # Categories
            categories = []
            for category in entry.findall("atom:category", self.ATOM_NS):
                term = category.get("term")
                if term:
                    categories.append(term)

            # DOI (if available)
            doi = None
            for link in entry.findall("atom:link", self.ATOM_NS):
                if link.get("title") == "doi":
                    doi_url = link.get("href", "")
                    if "doi.org/" in doi_url:
                        doi = doi_url.split("doi.org/")[-1]

            # Construct PDF URL
            pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

            # Journal reference (if published)
            journal_ref = None
            journal_elem = entry.find("arxiv:journal_ref", self.ATOM_NS)
            if journal_elem is not None:
                journal_ref = journal_elem.text

            return {
                "arxiv_id": arxiv_id,
                "title": title,
                "abstract": abstract,
                "authors": authors,
                "published": published,
                "updated": updated,
                "categories": categories,
                "doi": doi,
                "pdf_url": pdf_url,
                "abstract_url": f"https://arxiv.org/abs/{arxiv_id}",
                "journal_ref": journal_ref,
            }

        except Exception as e:
            logger.error(f"Error parsing arXiv entry: {e}")
            return None

    async def get_by_arxiv_id(self, arxiv_id: str) -> Optional[Dict]:
        """
        Get paper by arXiv ID.

        Args:
            arxiv_id: arXiv identifier (e.g., "2301.12345" or "math/0703324")

        Returns:
            Paper metadata dict, or None if not found
        """
        # Clean arXiv ID
        clean_id = self._extract_arxiv_id(arxiv_id)
        if not clean_id:
            logger.debug(f"Invalid arXiv ID: {arxiv_id}")  # Changed from warning to debug
            return None

        params = {"id_list": clean_id}

        xml_response = await self._make_request(params)
        if not xml_response:
            return None

        try:
            root = ET.fromstring(xml_response)
            entry = root.find("atom:entry", self.ATOM_NS)

            if entry is None:
                logger.info(f"No entry found for arXiv ID: {arxiv_id}")
                return None

            return self._parse_entry(entry)

        except Exception as e:
            logger.error(f"Error parsing arXiv response: {e}")
            return None

    async def search_by_title(self, title: str, max_results: int = 10) -> List[Dict]:
        """
        Search for papers by title.

        Args:
            title: Paper title to search for
            max_results: Maximum number of results to return

        Returns:
            List of paper metadata dicts
        """
        # Construct search query
        query = f'ti:"{title}"'

        params = {
            "search_query": query,
            "max_results": min(max_results, self.config.max_results_per_query),
            "sortBy": "relevance",
            "sortOrder": "descending",
        }

        xml_response = await self._make_request(params)
        if not xml_response:
            return []

        try:
            root = ET.fromstring(xml_response)
            entries = root.findall("atom:entry", self.ATOM_NS)

            results = []
            for entry in entries:
                paper = self._parse_entry(entry)
                if paper:
                    results.append(paper)

            logger.info(f"Found {len(results)} papers for title: {title}")
            return results

        except Exception as e:
            logger.error(f"Error parsing arXiv search response: {e}")
            return []

    async def search(
        self,
        query: str,
        max_results: int = 10,
        sort_by: str = "relevance",
        categories: Optional[List[str]] = None,
    ) -> List[Dict]:
        """
        General search for papers.

        Args:
            query: Search query (can use arXiv query syntax)
            max_results: Maximum number of results
            sort_by: Sort order ("relevance", "lastUpdatedDate", "submittedDate")
            categories: Filter by categories (e.g., ["cs.AI", "cs.LG"])

        Returns:
            List of paper metadata dicts
        """
        # Add category filter if specified
        if categories:
            cat_query = " OR ".join([f"cat:{cat}" for cat in categories])
            query = f"({query}) AND ({cat_query})"

        params = {
            "search_query": query,
            "max_results": min(max_results, self.config.max_results_per_query),
            "sortBy": sort_by,
            "sortOrder": "descending",
        }

        xml_response = await self._make_request(params)
        if not xml_response:
            return []

        try:
            root = ET.fromstring(xml_response)
            entries = root.findall("atom:entry", self.ATOM_NS)

            results = []
            for entry in entries:
                paper = self._parse_entry(entry)
                if paper:
                    results.append(paper)

            logger.info(f"Found {len(results)} papers for query: {query}")
            return results

        except Exception as e:
            logger.error(f"Error parsing arXiv search response: {e}")
            return []

    # NOTE: download_pdf() method REMOVED (redundant with PDFDownloadManager)
    # arXiv client now returns URLs only - PDFDownloadManager handles all downloads
    # This eliminates duplicate download logic and inconsistent validation

    async def fetch_by_id(self, identifier: str) -> Optional[Publication]:
        """
        Fetch publication by identifier (implements BasePublicationClient).

        Args:
            identifier: arXiv ID or DOI

        Returns:
            Publication object, or None if not found
        """
        # Try to extract arXiv ID
        arxiv_id = self._extract_arxiv_id(identifier)
        if not arxiv_id:
            logger.warning(f"Could not extract arXiv ID from: {identifier}")
            return None

        paper = await self.get_by_arxiv_id(arxiv_id)
        if not paper:
            return None

        return self._convert_to_publication(paper)

    def _convert_to_publication(self, paper: Dict) -> Publication:
        """
        Convert arXiv paper dict to Publication object.

        Args:
            paper: Paper metadata from arXiv API

        Returns:
            Publication object
        """
        return Publication(
            title=paper.get("title"),
            authors=", ".join(paper.get("authors", [])),
            journal=paper.get("journal_ref") or "arXiv preprint",
            year=paper.get("published", "")[:4] if paper.get("published") else None,
            doi=paper.get("doi"),
            pmid=None,
            pmcid=None,
            abstract=paper.get("abstract"),
            url=paper.get("abstract_url"),
            source=PublicationSource.ARXIV,
            metadata={
                "arxiv_id": paper.get("arxiv_id"),
                "pdf_url": paper.get("pdf_url"),
                "categories": paper.get("categories", []),
                "published": paper.get("published"),
                "updated": paper.get("updated"),
                "is_open_access": True,  # All arXiv papers are OA
            },
        )


# Convenience functions for backwards compatibility
async def search_arxiv(query: str, max_results: int = 10) -> List[Dict]:
    """
    Search arXiv for papers (convenience function).

    Args:
        query: Search query
        max_results: Maximum results

    Returns:
        List of paper metadata dicts
    """
    async with ArXivClient() as client:
        return await client.search(query, max_results)


async def get_arxiv_pdf(arxiv_id: str, output_path: Path) -> bool:
    """
    Download arXiv PDF (convenience function).

    Args:
        arxiv_id: arXiv identifier
        output_path: Local path to save PDF

    Returns:
        True if successful
    """
    async with ArXivClient() as client:
        paper = await client.get_by_arxiv_id(arxiv_id)
        if paper and paper.get("pdf_url"):
            return await client.download_pdf(paper["pdf_url"], output_path)
        return False
