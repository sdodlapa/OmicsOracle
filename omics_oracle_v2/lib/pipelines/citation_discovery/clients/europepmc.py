"""
Europe PMC API Client

Europe PMC is a comprehensive life sciences literature database providing
access to 42+ million abstracts and 7+ million full-text articles.

API Features:
- Free and open access (no API key required)
- Rich citation data with context
- Full-text search capabilities
- Open Access content
- RESTful API with JSON responses

Rate Limits:
- No strict rate limits for reasonable use
- Recommended: ~3 requests/second

Official API Docs: https://europepmc.org/RestfulWebService
"""

import logging
import ssl
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

import requests

from omics_oracle_v2.lib.search_engines.citations.models import (
    Publication,
    PublicationSource,
)

logger = logging.getLogger(__name__)


@dataclass
class EuropePMCConfig:
    """Configuration for Europe PMC API"""

    rate_limit: int = 3  # requests per second (conservative)
    timeout: int = 15  # seconds
    max_retries: int = 3
    retry_delay: float = 1.0  # seconds
    email: Optional[str] = None  # Optional - for polite usage


class EuropePMCClient:
    """
    Client for Europe PMC API

    Features:
    - Find papers citing a given publication (by PMID, DOI, or PMC ID)
    - Search papers by text query
    - Get full-text content for Open Access articles
    - Rich metadata (abstract, citations, references, etc.)

    Examples:
        # Find papers citing a specific paper
        client = EuropePMCClient()
        citations = client.get_citing_papers(pmid="12345678")

        # Search for papers about a topic
        papers = client.search("GEO dataset GSE12345")
    """

    BASE_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest"

    def __init__(self, config: Optional[EuropePMCConfig] = None):
        """
        Initialize Europe PMC client

        Args:
            config: Optional configuration
        """
        self.config = config or EuropePMCConfig()
        self.session = requests.Session()

        # Add email to User-Agent if provided (polite usage)
        if self.config.email:
            self.session.headers["User-Agent"] = f"OmicsOracle/2.0 ({self.config.email})"

        # Create SSL context that bypasses verification (for institutional VPN/proxies)
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # Mount adapter with SSL context
        from requests.adapters import HTTPAdapter
        
        class SSLAdapter(HTTPAdapter):
            def init_poolmanager(self, *args, **kwargs):
                kwargs['ssl_context'] = ssl_context
                return super().init_poolmanager(*args, **kwargs)
        
        self.session.mount('https://', SSLAdapter())

        # Rate limiting state
        self._last_request_time = 0.0
        self._min_interval = 1.0 / self.config.rate_limit

        logger.info(f"Europe PMC client initialized (rate: {self.config.rate_limit} req/s)")

    def _rate_limit(self):
        """Enforce rate limiting"""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_request_time = time.time()

    def _make_request(
        self, endpoint: str, params: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        Make API request with retry logic

        Args:
            endpoint: API endpoint (e.g., "search")
            params: Query parameters

        Returns:
            Response data or None if failed
        """
        url = f"{self.BASE_URL}/{endpoint}"
        
        # Always request JSON format
        if params is None:
            params = {}
        params["format"] = "json"

        for attempt in range(self.config.max_retries):
            try:
                self._rate_limit()
                response = self.session.get(url, params=params, timeout=self.config.timeout)

                # Handle rate limiting (429)
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", self.config.retry_delay * 2))
                    logger.warning(f"Rate limited. Waiting {retry_after}s...")
                    time.sleep(retry_after)
                    continue

                # Handle errors
                if response.status_code != 200:
                    logger.error(f"API error {response.status_code}: {response.text[:200]}")
                    return None

                return response.json()

            except requests.exceptions.Timeout:
                logger.warning(f"Request timeout (attempt {attempt + 1}/{self.config.max_retries})")
                if attempt < self.config.max_retries - 1:
                    time.sleep(self.config.retry_delay * (attempt + 1))
            except Exception as e:
                logger.error(f"Request failed: {e}")
                return None

        return None

    def get_citing_papers(
        self,
        pmid: Optional[str] = None,
        doi: Optional[str] = None,
        pmc_id: Optional[str] = None,
        max_results: int = 100,
    ) -> List[Publication]:
        """
        Get papers citing a given publication

        Args:
            pmid: PubMed ID (e.g., "12345678")
            doi: DOI (e.g., "10.1234/example")
            pmc_id: PubMed Central ID (e.g., "PMC123456")
            max_results: Maximum results to return

        Returns:
            List of citing publications
        """
        # Build query for citations
        if pmid:
            query = f"CITES:{pmid}_MED"
        elif pmc_id:
            query = f"CITES:{pmc_id}_PMC"
        elif doi:
            query = f'CITES:"{doi}"'
        else:
            logger.error("Must provide PMID, DOI, or PMC ID")
            return []

        logger.info(f"Finding papers citing via Europe PMC: {query}")

        # Search for citing papers
        params = {
            "query": query,
            "pageSize": min(max_results, 1000),  # Europe PMC max is 1000
            "cursorMark": "*",  # Start from beginning
        }

        response = self._make_request("search", params)
        if not response:
            return []

        # Parse results
        result_list = response.get("resultList", {})
        results = result_list.get("result", [])

        logger.info(f"Found {len(results)} citing papers for {query}")

        # Convert to Publication objects
        publications = []
        for result in results:
            try:
                pub = self._parse_result(result)
                if pub:
                    publications.append(pub)
            except Exception as e:
                logger.debug(f"Failed to parse result: {e}")
                continue

        return publications

    def search(self, query: str, max_results: int = 100) -> List[Publication]:
        """
        Search for papers by text query

        Args:
            query: Search query
            max_results: Maximum results to return

        Returns:
            List of publications matching query
        """
        logger.info(f"Searching Europe PMC: {query}")

        params = {
            "query": query,
            "pageSize": min(max_results, 1000),
            "cursorMark": "*",
        }

        response = self._make_request("search", params)
        if not response:
            return []

        # Parse results
        result_list = response.get("resultList", {})
        results = result_list.get("result", [])

        logger.info(f"Found {len(results)} results")

        # Convert to Publication objects
        publications = []
        for result in results:
            try:
                pub = self._parse_result(result)
                if pub:
                    publications.append(pub)
            except Exception as e:
                logger.debug(f"Failed to parse result: {e}")
                continue

        return publications

    def _parse_result(self, result: Dict) -> Optional[Publication]:
        """
        Parse Europe PMC result into Publication object

        Args:
            result: Raw result from API

        Returns:
            Publication object or None if parsing fails
        """
        try:
            # Extract IDs
            pmid = result.get("pmid")
            doi = result.get("doi")
            pmc_id = result.get("pmcid")

            # Title and abstract
            title = result.get("title", "").strip()
            abstract = result.get("abstractText", "").strip()

            if not title:
                return None

            # Authors
            author_list = result.get("authorList", {}).get("author", [])
            authors = []
            for author in author_list:
                # Handle different author formats
                if isinstance(author, dict):
                    full_name = author.get("fullName", "")
                    if not full_name:
                        # Build from parts
                        first = author.get("firstName", "")
                        last = author.get("lastName", "")
                        full_name = f"{first} {last}".strip()
                    if full_name:
                        authors.append(full_name)
                elif isinstance(author, str):
                    authors.append(author)

            # Publication date
            pub_date = None
            pub_year = result.get("pubYear")
            if pub_year:
                try:
                    pub_date = datetime(int(pub_year), 1, 1)
                except (ValueError, TypeError):
                    pass

            # Journal
            journal = result.get("journalTitle") or result.get("journalInfo", {}).get("journal", {}).get("title")

            # Citation count
            citation_count = result.get("citedByCount", 0)

            # URL
            url = None
            if doi:
                url = f"https://doi.org/{doi}"
            elif pmid:
                url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}"
            elif pmc_id:
                url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc_id}"

            return Publication(
                pmid=pmid,
                doi=doi,
                title=title,
                abstract=abstract,
                authors=authors,
                publication_date=pub_date,
                journal=journal,
                url=url,
                citations=citation_count,
                source=PublicationSource.EUROPEPMC,
            )

        except Exception as e:
            logger.debug(f"Failed to parse Europe PMC result: {e}")
            return None
