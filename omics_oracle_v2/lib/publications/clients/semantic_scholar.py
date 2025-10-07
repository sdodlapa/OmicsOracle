"""
Semantic Scholar client for citation data enrichment.

This client provides citation counts and metrics from Semantic Scholar's API,
which is free and doesn't require authentication for basic use.

API Documentation: https://api.semanticscholar.org/
Rate Limits: 100 requests per 5 minutes (free tier)

Example:
    >>> from omics_oracle_v2.lib.publications.clients.semantic_scholar import SemanticScholarClient
    >>> from omics_oracle_v2.lib.publications.config import SemanticScholarConfig
    >>>
    >>> config = SemanticScholarConfig()
    >>> client = SemanticScholarClient(config)
    >>>
    >>> # Enrich publication with citations
    >>> pub = Publication(doi="10.1038/nature12345", ...)
    >>> enriched_pub = client.enrich_publication(pub)
    >>> print(f"Citations: {enriched_pub.citations}")
"""

import logging
import time
from typing import Dict, List, Optional

import requests

from omics_oracle_v2.lib.publications.clients.base import BasePublicationClient
from omics_oracle_v2.lib.publications.models import Publication

logger = logging.getLogger(__name__)


class SemanticScholarConfig:
    """
    Configuration for Semantic Scholar API.

    Attributes:
        enable: Enable Semantic Scholar enrichment
        api_url: Base API URL
        timeout: Request timeout in seconds
        retry_count: Number of retries on failure
        rate_limit_per_minute: API rate limit (free tier: 100 req/5min = 20/min)
    """

    def __init__(
        self,
        enable: bool = True,
        api_url: str = "https://api.semanticscholar.org/graph/v1",
        timeout: int = 10,
        retry_count: int = 3,
        rate_limit_per_minute: int = 20,
    ):
        self.enable = enable
        self.api_url = api_url
        self.timeout = timeout
        self.retry_count = retry_count
        self.rate_limit_per_minute = rate_limit_per_minute
        self.min_request_interval = 60.0 / rate_limit_per_minute  # seconds between requests


class SemanticScholarClient(BasePublicationClient):
    """
    Client for Semantic Scholar API to get citation data.

    Free tier: 100 requests per 5 minutes
    No API key required for basic usage
    """

    def __init__(self, config: Optional[SemanticScholarConfig] = None):
        """Initialize Semantic Scholar client."""
        self.config = config or SemanticScholarConfig()
        super().__init__(self.config)  # Call parent __init__
        self.last_request_time = 0.0
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "OmicsOracle/1.0 (Academic Research Tool)",
                "Accept": "application/json",
            }
        )

    @property
    def source_name(self) -> str:
        """Get the name of this publication source."""
        return "semantic_scholar"

    def _rate_limit(self):
        """Enforce rate limiting."""
        if not self.config.enable:
            return

        elapsed = time.time() - self.last_request_time
        if elapsed < self.config.min_request_interval:
            sleep_time = self.config.min_request_interval - elapsed
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def get_paper_by_doi(self, doi: str) -> Optional[Dict]:
        """
        Get paper data from Semantic Scholar by DOI.

        Args:
            doi: Digital Object Identifier

        Returns:
            Paper data dictionary or None if not found
        """
        if not self.config.enable or not doi:
            return None

        self._rate_limit()

        url = f"{self.config.api_url}/paper/DOI:{doi}"
        params = {"fields": "title,year,citationCount,influentialCitationCount,authors,venue"}

        for attempt in range(self.config.retry_count):
            try:
                response = self.session.get(url, params=params, timeout=self.config.timeout)

                if response.status_code == 200:
                    data = response.json()
                    logger.debug(f"Retrieved Semantic Scholar data for DOI: {doi}")
                    return data

                elif response.status_code == 404:
                    logger.debug(f"Paper not found in Semantic Scholar: {doi}")
                    return None

                elif response.status_code == 429:
                    # Rate limited - wait longer
                    wait_time = (attempt + 1) * 5
                    logger.warning(f"Rate limited by Semantic Scholar, waiting {wait_time}s")
                    time.sleep(wait_time)
                    continue

                else:
                    logger.warning(f"Semantic Scholar API error {response.status_code} for {doi}")
                    return None

            except requests.exceptions.Timeout:
                logger.warning(f"Timeout fetching Semantic Scholar data for {doi}")
                if attempt < self.config.retry_count - 1:
                    time.sleep(attempt + 1)
                    continue
                return None

            except Exception as e:
                logger.error(f"Error fetching Semantic Scholar data: {e}")
                return None

        return None

    def get_paper_by_title(self, title: str) -> Optional[Dict]:
        """
        Search for paper by title in Semantic Scholar.

        Args:
            title: Paper title

        Returns:
            Paper data dictionary or None if not found
        """
        if not self.config.enable or not title:
            return None

        self._rate_limit()

        url = f"{self.config.api_url}/paper/search"
        params = {
            "query": title,
            "fields": "title,year,citationCount,influentialCitationCount,authors",
            "limit": 1,
        }

        try:
            response = self.session.get(url, params=params, timeout=self.config.timeout)

            if response.status_code == 200:
                data = response.json()
                if data.get("data") and len(data["data"]) > 0:
                    paper = data["data"][0]
                    logger.debug(f"Found paper in Semantic Scholar: {title[:50]}")
                    return paper
                else:
                    logger.debug(f"Paper not found in Semantic Scholar: {title[:50]}")
                    return None

            else:
                logger.warning(f"Semantic Scholar search error: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Error searching Semantic Scholar: {e}")
            return None

    def enrich_publication(self, publication: Publication) -> Publication:
        """
        Enrich a publication with citation data from Semantic Scholar.

        Tries DOI first, falls back to title search.

        Args:
            publication: Publication to enrich

        Returns:
            Publication with updated citation count
        """
        if not self.config.enable:
            return publication

        # Try DOI first (most accurate)
        paper_data = None
        if publication.doi:
            paper_data = self.get_paper_by_doi(publication.doi)

        # Fall back to title search if DOI fails
        if not paper_data and publication.title:
            paper_data = self.get_paper_by_title(publication.title)

        # Update citation count if found
        if paper_data:
            citation_count = paper_data.get("citationCount", 0)
            influential_citations = paper_data.get("influentialCitationCount", 0)

            # Update publication
            publication.citations = citation_count

            # Store influential citations in metadata
            if not publication.metadata:
                publication.metadata = {}
            publication.metadata["influential_citations"] = influential_citations
            publication.metadata["semantic_scholar_enriched"] = True

            logger.info(
                f"Enriched '{publication.title[:50]}...' with {citation_count} citations "
                f"({influential_citations} influential)"
            )

        return publication

    def enrich_publications(self, publications: List[Publication]) -> List[Publication]:
        """
        Enrich multiple publications with citation data.

        Args:
            publications: List of publications to enrich

        Returns:
            List of enriched publications
        """
        if not self.config.enable:
            return publications

        logger.info(f"Enriching {len(publications)} publications with Semantic Scholar data...")

        enriched = []
        for i, pub in enumerate(publications):
            try:
                enriched_pub = self.enrich_publication(pub)
                enriched.append(enriched_pub)

                if (i + 1) % 10 == 0:
                    logger.info(f"Enriched {i + 1}/{len(publications)} publications")

            except Exception as e:
                logger.error(f"Error enriching publication: {e}")
                enriched.append(pub)  # Add original if enrichment fails

        logger.info(
            f"Enrichment complete: {sum(1 for p in enriched if p.citations and p.citations > 0)}"
            f"/{len(enriched)} publications have citations"
        )

        return enriched

    def search(self, query: str, max_results: int = 100, **kwargs) -> List[Publication]:
        """
        Search for publications (not primary use case for Semantic Scholar).

        Note: Semantic Scholar is primarily used for enrichment, not search.
        This method is implemented to satisfy the BasePublicationClient interface.

        Args:
            query: Search query string
            max_results: Maximum number of results
            **kwargs: Additional parameters

        Returns:
            Empty list (use PubMed or Google Scholar for search)
        """
        logger.warning(
            "Semantic Scholar client is designed for enrichment, not search. "
            "Use PubMed or Google Scholar for publication search."
        )
        return []

    def fetch_by_id(self, identifier: str) -> Optional[Publication]:
        """
        Fetch a publication by DOI.

        Args:
            identifier: DOI of the publication

        Returns:
            Publication if found, None otherwise
        """
        if not identifier:
            return None

        # Assume identifier is DOI
        paper_data = self.get_paper_by_doi(identifier)

        if not paper_data:
            return None

        # Create minimal Publication object from Semantic Scholar data
        from omics_oracle_v2.lib.publications.models import PublicationSource

        pub = Publication(
            title=paper_data.get("title", ""),
            abstract=paper_data.get("abstract", ""),
            authors=[author.get("name", "") for author in paper_data.get("authors", [])],
            publication_date=None,  # Would need parsing
            doi=identifier,
            citations=paper_data.get("citationCount", 0),
            source=PublicationSource.SEMANTIC_SCHOLAR,
            metadata={
                "influential_citations": paper_data.get("influentialCitationCount", 0),
                "semantic_scholar_id": paper_data.get("paperId"),
            },
        )

        return pub
