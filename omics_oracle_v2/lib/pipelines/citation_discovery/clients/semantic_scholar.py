"""
Semantic Scholar API Client

Semantic Scholar is a free academic search engine with 200M+ papers and
powerful citation graph capabilities. Perfect for citation discovery.

API Features:
- 100 requests/second (no API key needed for basic use)
- Rich citation data with context
- Paper recommendations based on citation patterns
- Free and open access

Rate Limits:
- Anonymous: 100 req/sec
- With API key: Higher limits + priority queue

Official API Docs: https://api.semanticscholar.org/api-docs/
"""

import logging
import ssl
import time
from dataclasses import dataclass
from typing import Dict, List, Optional

import requests

from omics_oracle_v2.lib.search_engines.citations.models import (
    Publication,
    PublicationSource,
)

logger = logging.getLogger(__name__)


@dataclass
class SemanticScholarConfig:
    """Configuration for Semantic Scholar API"""

    api_key: Optional[str] = None  # Optional - increases rate limits
    rate_limit: int = 100  # requests per second
    timeout: int = 10  # seconds
    max_retries: int = 3
    retry_delay: float = 1.0  # seconds


class SemanticScholarClient:
    """
    Client for Semantic Scholar API

    Features:
    - Get papers citing a given paper (by DOI, PMID, or S2 Paper ID)
    - Search papers by text query
    - Get paper recommendations based on citation patterns
    - Rich metadata (abstract, citations, references, etc.)

    Examples:
        # Find papers citing a specific paper
        client = SemanticScholarClient()
        citations = client.get_citing_papers(pmid="12345678")

        # Search for papers about a topic
        papers = client.search("GEO dataset GSE12345")

        # Get recommended papers based on citation patterns
        recommendations = client.get_recommendations(pmid="12345678")
    """

    BASE_URL = "https://api.semanticscholar.org/graph/v1"

    def __init__(self, config: Optional[SemanticScholarConfig] = None):
        """
        Initialize Semantic Scholar client

        Args:
            config: Optional configuration (defaults to anonymous access)
        """
        self.config = config or SemanticScholarConfig()
        self.session = requests.Session()

        # Set API key header if provided
        if self.config.api_key:
            self.session.headers["x-api-key"] = self.config.api_key

        # CRITICAL: Disable SSL verification at session level
        # This is required for institutional VPN/proxies that use self-signed certificates
        self.session.verify = False
        
        # Suppress SSL warnings (optional but cleaner logs)
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        # Rate limiting state
        self._last_request_time = 0.0
        self._min_interval = 1.0 / self.config.rate_limit

    def _rate_limit(self):
        """Enforce rate limiting"""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_request_time = time.time()

    def _make_request(
        self, endpoint: str, params: Optional[Dict] = None, method: str = "GET"
    ) -> Optional[Dict]:
        """
        Make API request with retry logic

        Args:
            endpoint: API endpoint (e.g., "/paper/PMID:12345678")
            params: Query parameters
            method: HTTP method

        Returns:
            Response data or None if failed
        """
        url = f"{self.BASE_URL}{endpoint}"

        for attempt in range(self.config.max_retries):
            try:
                self._rate_limit()

                if method == "GET":
                    response = self.session.get(url, params=params, timeout=self.config.timeout)
                else:
                    response = self.session.post(url, json=params, timeout=self.config.timeout)

                # Handle rate limiting (429)
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", self.config.retry_delay))
                    logger.warning(f"Rate limited. Waiting {retry_after}s...")
                    time.sleep(retry_after)
                    continue

                # Handle errors
                if response.status_code != 200:
                    logger.error(f"API error {response.status_code}: {response.text}")
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
        s2_paper_id: Optional[str] = None,
        limit: int = 1000,
        fields: Optional[List[str]] = None,
    ) -> List[Publication]:
        """
        Get papers that cite a given paper

        Args:
            pmid: PubMed ID (e.g., "12345678")
            doi: DOI (e.g., "10.1038/nature12345")
            s2_paper_id: Semantic Scholar paper ID
            limit: Maximum number of citations to return
            fields: Fields to retrieve (default: title, authors, year, doi, pmid)

        Returns:
            List of Publication objects
        """
        # Determine paper identifier
        if pmid:
            paper_id = f"PMID:{pmid}"
        elif doi:
            paper_id = f"DOI:{doi}"
        elif s2_paper_id:
            paper_id = s2_paper_id
        else:
            raise ValueError("Must provide pmid, doi, or s2_paper_id")

        # Default fields (note: 'doi' is NOT a valid field - use externalIds instead)
        if fields is None:
            fields = [
                "title",
                "authors",
                "year",
                "publicationDate",
                "externalIds",
                "abstract",
                "citationCount",
                "url",
            ]

        # Get citations in batches (API limit is 1000 per request)
        all_citations = []
        offset = 0
        batch_size = 1000

        while len(all_citations) < limit:
            endpoint = f"/paper/{paper_id}/citations"
            params = {"fields": ",".join(fields), "limit": min(batch_size, limit - len(all_citations)), "offset": offset}

            data = self._make_request(endpoint, params)
            if not data or "data" not in data:
                break

            # Convert to Publication objects
            for item in data["data"]:
                citing_paper = item.get("citingPaper", {})
                pub = self._convert_to_publication(citing_paper)
                if pub:
                    all_citations.append(pub)

            # Check if more results available
            if len(data["data"]) < batch_size:
                break

            offset += batch_size

        logger.info(f"Found {len(all_citations)} citing papers for {paper_id}")
        return all_citations

    def search(
        self, query: str, limit: int = 100, year_range: Optional[tuple] = None, fields: Optional[List[str]] = None
    ) -> List[Publication]:
        """
        Search for papers by text query

        Args:
            query: Search query (e.g., "GEO dataset GSE12345")
            limit: Maximum number of results
            year_range: Optional (min_year, max_year) tuple
            fields: Fields to retrieve

        Returns:
            List of Publication objects
        """
        if fields is None:
            fields = [
                "title",
                "authors",
                "year",
                "publicationDate",
                "externalIds",
                "abstract",
                "citationCount",
                "url",
            ]

        endpoint = "/paper/search"
        params = {"query": query, "fields": ",".join(fields), "limit": min(limit, 100)}  # API max is 100 per request

        if year_range:
            params["year"] = f"{year_range[0]}-{year_range[1]}"

        data = self._make_request(endpoint, params)
        if not data or "data" not in data:
            return []

        publications = []
        for item in data["data"]:
            pub = self._convert_to_publication(item)
            if pub:
                publications.append(pub)

        logger.info(f"Found {len(publications)} papers for query: {query}")
        return publications

    def get_recommendations(
        self, pmid: Optional[str] = None, doi: Optional[str] = None, limit: int = 100
    ) -> List[Publication]:
        """
        Get recommended papers based on citation patterns

        Args:
            pmid: PubMed ID
            doi: DOI
            limit: Maximum number of recommendations

        Returns:
            List of Publication objects
        """
        if pmid:
            paper_id = f"PMID:{pmid}"
        elif doi:
            paper_id = f"DOI:{doi}"
        else:
            raise ValueError("Must provide pmid or doi")

        endpoint = f"/paper/{paper_id}/recommendations"
        params = {"limit": min(limit, 100)}

        data = self._make_request(endpoint, params)
        if not data or "recommendedPapers" not in data:
            return []

        publications = []
        for item in data["recommendedPapers"]:
            pub = self._convert_to_publication(item)
            if pub:
                publications.append(pub)

        logger.info(f"Found {len(publications)} recommended papers for {paper_id}")
        return publications

    def _convert_to_publication(self, data: Dict) -> Optional[Publication]:
        """
        Convert Semantic Scholar response to Publication object

        Args:
            data: Paper data from Semantic Scholar API

        Returns:
            Publication object or None if invalid
        """
        if not data or "title" not in data:
            return None

        # Extract external IDs
        external_ids = data.get("externalIds", {})
        pmid = external_ids.get("PubMed")
        doi = data.get("doi") or external_ids.get("DOI")

        # Extract authors
        authors = []
        for author in data.get("authors", []):
            name = author.get("name", "")
            if name:
                authors.append(name)

        # Convert year to publication_date if publicationDate not provided
        publication_date = data.get("publicationDate")
        if not publication_date and data.get("year"):
            publication_date = f"{data['year']}-01-01"

        # Create Publication object
        return Publication(
            title=data.get("title", ""),
            authors=authors,
            pmid=pmid,
            doi=doi,
            abstract=data.get("abstract"),
            publication_date=publication_date,
            journal=None,  # Not provided by Semantic Scholar
            citations=data.get("citationCount"),
            url=data.get("url"),
            source=PublicationSource.SEMANTIC_SCHOLAR,
        )


# Convenience function for quick testing
def test_semantic_scholar():
    """Test Semantic Scholar client"""
    client = SemanticScholarClient()

    # Test 1: Get citing papers for a known paper
    print("\n=== Test 1: Get citing papers ===")
    citations = client.get_citing_papers(pmid="20944583", limit=5)
    print(f"Found {len(citations)} citations")
    for i, pub in enumerate(citations[:3], 1):
        print(f"{i}. {pub.title[:80]}...")
        print(f"   Authors: {', '.join(pub.authors[:3])}")
        print(f"   Date: {pub.publication_date}, PMID: {pub.pmid}, DOI: {pub.doi}")

    # Test 2: Search for papers
    print("\n=== Test 2: Search papers ===")
    papers = client.search("gene expression omnibus GEO", limit=5)
    print(f"Found {len(papers)} papers")
    for i, pub in enumerate(papers[:3], 1):
        print(f"{i}. {pub.title[:80]}...")
        print(f"   Date: {pub.publication_date}, Citations: {pub.citations}")


if __name__ == "__main__":
    test_semantic_scholar()
