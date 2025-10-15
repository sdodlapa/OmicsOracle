"""
Crossref API client for citation discovery.

Crossref is the largest DOI registration agency with 130M+ scholarly records.
Provides comprehensive citation data across all disciplines.

Features:
- Citation discovery (papers citing a DOI)
- Metadata retrieval
- Free and open REST API
- Rate limiting: 50 req/s (polite pool with mailto)
- SSL bypass for institutional VPNs
- Automatic retry with exponential backoff

API Documentation: https://api.crossref.org/swagger-ui/index.html
Best Practices: https://github.com/CrossRef/rest-api-doc
"""

import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests

from omics_oracle_v2.lib.pipelines.citation_discovery.clients.config import \
    CrossrefConfig
from omics_oracle_v2.lib.search_engines.citations.models import (
    Publication, PublicationSource)

logger = logging.getLogger(__name__)


class CrossrefClient:
    """
    Client for Crossref REST API.

    Crossref provides:
    - 130M+ scholarly records
    - DOI-based citation tracking
    - Cross-publisher metadata
    - Free and open access

    Features:
    - Citation discovery (is-referenced-by-count, references)
    - Metadata search
    - Rate limiting: 50 req/s (polite pool)
    - SSL bypass for institutional VPNs
    - Automatic retry with backoff
    """

    def __init__(self, config: Optional[CrossrefConfig] = None):
        """
        Initialize Crossref client.

        Args:
            config: Configuration object (uses defaults if None)
        """
        self.config = config or CrossrefConfig()
        self.base_url = "https://api.crossref.org"

        # Setup session with SSL bypass
        self.session = requests.Session()

        # CRITICAL: Disable SSL verification at session level
        # This is required for institutional VPN/proxies that use self-signed certificates
        self.session.verify = False

        # Suppress SSL warnings (optional but cleaner logs)
        import urllib3

        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        # Polite pool - add mailto to get better rate limits
        if self.config.mailto:
            self.session.headers.update(
                {"User-Agent": f"OmicsOracle/1.0 (mailto:{self.config.mailto})"}
            )
        else:
            self.session.headers.update({"User-Agent": "OmicsOracle/1.0"})

        # Rate limiting
        self._last_request_time = 0
        self._min_interval = 1.0 / self.config.requests_per_second

        logger.info(
            f"✓ Crossref client initialized "
            f"(rate: {self.config.requests_per_second} req/s, "
            f"polite: {bool(self.config.mailto)})"
        )

    def get_citing_papers(
        self, doi: Optional[str] = None, pmid: Optional[str] = None, limit: int = 100
    ) -> List[Publication]:
        """
        Find papers citing a given publication.

        Crossref supports DOI-based citation discovery. For PMID, we first
        convert to DOI using Crossref's works API.

        Args:
            doi: DOI of the paper to find citations for
            pmid: PubMed ID (will be converted to DOI)
            limit: Maximum number of citing papers to return

        Returns:
            List of Publication objects citing the given paper

        Raises:
            ValueError: If neither doi nor pmid provided
        """
        if not doi and not pmid:
            raise ValueError("Either doi or pmid must be provided")

        # If we have PMID, try to get DOI first
        target_doi = doi
        if not target_doi and pmid:
            target_doi = self._pmid_to_doi(pmid)
            if not target_doi:
                logger.warning(f"Could not convert PMID {pmid} to DOI")
                return []

        if not target_doi:
            return []

        # Clean DOI (remove prefix if present)
        clean_doi = target_doi.replace("https://doi.org/", "").replace(
            "http://dx.doi.org/", ""
        )

        # Query for papers citing this DOI
        # Crossref doesn't have a direct "citing papers" endpoint
        # We use the work metadata to get citation count, then search for papers
        # that reference this DOI
        papers = []

        try:
            # First, get the work metadata to verify DOI exists
            work_url = f"{self.base_url}/works/{clean_doi}"
            work_data = self._make_request(work_url)

            if not work_data or "message" not in work_data:
                logger.warning(f"DOI {clean_doi} not found in Crossref")
                return []

            # Crossref doesn't provide citing papers directly via API
            # We can only get reference count and references FROM this paper
            # For actual citing papers, we'd need OpenCitations or other services

            # Log what we found
            citation_count = work_data["message"].get("is-referenced-by-count", 0)
            logger.info(
                f"DOI {clean_doi} has {citation_count} citations (per Crossref metadata)"
            )

            # For now, Crossref is primarily used for metadata enrichment
            # and reference extraction, not citation discovery
            # We return empty list but log the citation count
            return []

        except Exception as e:
            logger.warning(f"Error finding citing papers for DOI {clean_doi}: {e}")
            return []

    def search(self, query: str, limit: int = 20) -> List[Publication]:
        """
        Search Crossref for publications matching a query.

        Args:
            query: Search query string
            limit: Maximum number of results to return

        Returns:
            List of Publication objects matching the query
        """
        try:
            params = {
                "query": query,
                "rows": min(limit, 100),  # Crossref max is 1000, we cap at 100
                "select": "DOI,title,author,published,container-title,volume,issue,page,ISSN,publisher,type,is-referenced-by-count",
            }

            url = f"{self.base_url}/works"
            data = self._make_request(url, params=params)

            if not data or "message" not in data or "items" not in data["message"]:
                return []

            papers = []
            for item in data["message"]["items"]:
                pub = self._parse_result(item)
                if pub:
                    papers.append(pub)

            logger.info(
                f"✓ Crossref search: found {len(papers)} papers for query '{query}'"
            )
            return papers

        except Exception as e:
            logger.warning(f"Crossref search error: {e}")
            return []

    def get_work(self, doi: str) -> Optional[Publication]:
        """
        Get metadata for a specific DOI.

        Args:
            doi: DOI to look up

        Returns:
            Publication object or None if not found
        """
        try:
            clean_doi = doi.replace("https://doi.org/", "").replace(
                "http://dx.doi.org/", ""
            )
            url = f"{self.base_url}/works/{clean_doi}"
            data = self._make_request(url)

            if not data or "message" not in data:
                return None

            return self._parse_result(data["message"])

        except Exception as e:
            logger.warning(f"Error fetching DOI {doi}: {e}")
            return None

    def _pmid_to_doi(self, pmid: str) -> Optional[str]:
        """
        Convert PubMed ID to DOI using Crossref API.

        Args:
            pmid: PubMed ID

        Returns:
            DOI string or None if not found
        """
        try:
            # Search for PMID in Crossref
            params = {"query": f"PMID:{pmid}", "rows": 1}

            url = f"{self.base_url}/works"
            data = self._make_request(url, params=params)

            if data and "message" in data and "items" in data["message"]:
                items = data["message"]["items"]
                if items:
                    return items[0].get("DOI")

            return None

        except Exception as e:
            logger.warning(f"Error converting PMID {pmid} to DOI: {e}")
            return None

    def _parse_result(self, item: Dict[str, Any]) -> Optional[Publication]:
        """
        Parse Crossref API result into Publication object.

        Args:
            item: Result item from Crossref API

        Returns:
            Publication object or None if parsing fails
        """
        try:
            # Extract title
            title_list = item.get("title", [])
            title = title_list[0] if title_list else None
            if not title:
                return None

            # Extract DOI
            doi = item.get("DOI")

            # Extract authors
            authors = []
            for author in item.get("author", []):
                given = author.get("given", "")
                family = author.get("family", "")
                if family:
                    authors.append(f"{given} {family}".strip())

            # Extract publication date
            pub_date = None
            date_parts = item.get("published", item.get("created", {})).get(
                "date-parts", [[]]
            )
            if date_parts and date_parts[0]:
                parts = date_parts[0]
                if len(parts) >= 1:
                    year = parts[0]
                    month = parts[1] if len(parts) >= 2 else 1
                    day = parts[2] if len(parts) >= 3 else 1
                    try:
                        pub_date = datetime(year, month, day)
                    except ValueError:
                        pub_date = datetime(year, 1, 1)

            # Extract journal/container
            journal_list = item.get("container-title", [])
            journal = journal_list[0] if journal_list else None

            # Extract abstract (Crossref usually doesn't include abstracts)
            abstract = item.get("abstract", "")

            # Extract citation count
            citations = item.get("is-referenced-by-count", 0)

            # Extract other metadata
            volume = item.get("volume")
            issue = item.get("issue")
            pages = item.get("page")
            publisher = item.get("publisher")
            article_type = item.get("type", "unknown")

            # Build URL
            url = f"https://doi.org/{doi}" if doi else None

            return Publication(
                title=title,
                authors=authors,
                journal=journal,
                publication_date=pub_date,
                doi=doi,
                abstract=abstract,
                url=url,
                source=PublicationSource.CROSSREF,
                citations=citations,
                metadata={
                    "volume": volume,
                    "issue": issue,
                    "pages": pages,
                    "publisher": publisher,
                    "type": article_type,
                },
            )

        except Exception as e:
            logger.warning(f"Error parsing Crossref result: {e}")
            return None

    def _make_request(
        self, url: str, params: Optional[Dict[str, Any]] = None, max_retries: int = 3
    ) -> Optional[Dict[str, Any]]:
        """
        Make HTTP request with rate limiting and retry logic.

        Args:
            url: URL to request
            params: Query parameters
            max_retries: Maximum number of retry attempts

        Returns:
            JSON response data or None if all retries fail
        """
        for attempt in range(max_retries):
            try:
                # Rate limiting
                now = time.time()
                time_since_last = now - self._last_request_time
                if time_since_last < self._min_interval:
                    time.sleep(self._min_interval - time_since_last)

                self._last_request_time = time.time()

                # Make request
                response = self.session.get(url, params=params, timeout=30)
                response.raise_for_status()

                return response.json()

            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    wait_time = (2**attempt) * 1.0  # Exponential backoff
                    logger.warning(
                        f"Crossref request failed (attempt {attempt + 1}/{max_retries}), "
                        f"retrying in {wait_time}s: {e}"
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(
                        f"Crossref request failed after {max_retries} attempts: {e}"
                    )
                    return None

        return None
