"""
OpenAlex API client for citation data and paper discovery.

OpenAlex is a free, open-source alternative to Google Scholar with:
- Official REST API (no scraping needed)
- Generous rate limits (10,000 requests/day, no authentication)
- Comprehensive coverage (250M+ works)
- Citation data including citing papers
- Open access status and metadata

API Documentation: https://docs.openalex.org/
Rate Limits: 10 req/second for polite pool (with email), 1 req/second otherwise

Example:
    >>> from omics_oracle_v2.lib.publications.clients.openalex import OpenAlexClient
    >>> 
    >>> client = OpenAlexClient(email="researcher@university.edu")
    >>> 
    >>> # Find citing papers
    >>> citing_papers = client.get_citing_papers(doi="10.1038/nature12345")
    >>> print(f"Found {len(citing_papers)} citing papers")
    >>> 
    >>> # Search for papers
    >>> papers = client.search("CRISPR gene editing", max_results=20)
"""

import logging
import time
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import quote

import requests

from omics_oracle_v2.lib.publications.clients.base import BasePublicationClient
from omics_oracle_v2.lib.publications.models import Publication, PublicationSource

logger = logging.getLogger(__name__)


class OpenAlexConfig:
    """
    Configuration for OpenAlex API.

    Attributes:
        enable: Enable OpenAlex client
        api_url: Base API URL
        email: Email for polite pool (10x faster rate limits)
        timeout: Request timeout in seconds
        retry_count: Number of retries on failure
        rate_limit_per_second: Requests per second (10 with email, 1 without)
        user_agent: Custom user agent string
    """

    def __init__(
        self,
        enable: bool = True,
        api_url: str = "https://api.openalex.org",
        email: Optional[str] = None,
        timeout: int = 30,
        retry_count: int = 3,
        rate_limit_per_second: Optional[int] = None,
        user_agent: str = "OmicsOracle/1.0 (Academic Research Tool)",
    ):
        self.enable = enable
        self.api_url = api_url
        self.email = email
        self.timeout = timeout
        self.retry_count = retry_count
        self.user_agent = user_agent
        
        # Auto-configure rate limit based on email
        if rate_limit_per_second is None:
            self.rate_limit_per_second = 10 if email else 1
        else:
            self.rate_limit_per_second = rate_limit_per_second
        
        self.min_request_interval = 1.0 / self.rate_limit_per_second


class OpenAlexClient(BasePublicationClient):
    """
    Client for OpenAlex API.
    
    OpenAlex provides comprehensive scholarly data including:
    - Works (publications)
    - Authors
    - Institutions
    - Venues (journals)
    - Citations (who cites who)
    - Open access status
    
    Free tier with generous rate limits (10,000/day with email).
    """

    def __init__(self, config: Optional[OpenAlexConfig] = None):
        """
        Initialize OpenAlex client.
        
        Args:
            config: OpenAlex configuration
        """
        self.config = config or OpenAlexConfig()
        super().__init__(self.config)
        self.last_request_time = 0.0
        self.session = requests.Session()
        
        # Set up headers
        headers = {
            "User-Agent": self.config.user_agent,
            "Accept": "application/json",
        }
        
        # Add email to user agent for polite pool (faster rate limits)
        if self.config.email:
            headers["User-Agent"] = f"{self.config.user_agent}; mailto:{self.config.email}"
            logger.info(f"OpenAlex client initialized with polite pool ({self.config.rate_limit_per_second} req/s)")
        else:
            logger.info(f"OpenAlex client initialized ({self.config.rate_limit_per_second} req/s)")
            logger.warning("No email provided - consider adding for faster rate limits (10x)")
        
        self.session.headers.update(headers)

    @property
    def source_name(self) -> str:
        """Get the name of this publication source."""
        return "openalex"

    def _rate_limit(self):
        """Enforce rate limiting."""
        if not self.config.enable:
            return

        elapsed = time.time() - self.last_request_time
        if elapsed < self.config.min_request_interval:
            sleep_time = self.config.min_request_interval - elapsed
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def _make_request(self, url: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """
        Make API request with retry logic.
        
        Args:
            url: API endpoint URL
            params: Query parameters
            
        Returns:
            Response JSON or None on failure
        """
        if not self.config.enable:
            return None

        self._rate_limit()

        for attempt in range(self.config.retry_count):
            try:
                response = self.session.get(url, params=params, timeout=self.config.timeout)

                if response.status_code == 200:
                    return response.json()

                elif response.status_code == 404:
                    logger.debug(f"Not found in OpenAlex: {url}")
                    return None

                elif response.status_code == 429:
                    # Rate limited - wait and retry
                    wait_time = (attempt + 1) * 2
                    logger.warning(f"Rate limited by OpenAlex, waiting {wait_time}s")
                    time.sleep(wait_time)
                    continue

                else:
                    logger.warning(f"OpenAlex API error {response.status_code}: {url}")
                    return None

            except requests.exceptions.Timeout:
                logger.warning(f"Timeout on OpenAlex request: {url}")
                if attempt < self.config.retry_count - 1:
                    time.sleep(attempt + 1)
                    continue
                return None

            except Exception as e:
                logger.error(f"Error making OpenAlex request: {e}")
                return None

        return None

    def get_work_by_doi(self, doi: str) -> Optional[Dict]:
        """
        Get work (publication) by DOI.
        
        Args:
            doi: Digital Object Identifier
            
        Returns:
            Work data or None if not found
        """
        if not doi:
            return None

        # Clean DOI (remove https://doi.org/ prefix if present)
        doi = doi.replace("https://doi.org/", "").replace("http://doi.org/", "")
        
        url = f"{self.config.api_url}/works/https://doi.org/{quote(doi)}"
        
        logger.debug(f"Fetching OpenAlex work for DOI: {doi}")
        return self._make_request(url)

    def get_citing_papers(
        self, 
        doi: Optional[str] = None, 
        openalex_id: Optional[str] = None,
        max_results: int = 100
    ) -> List[Publication]:
        """
        Get papers that cite a given work.
        
        Args:
            doi: DOI of the cited work
            openalex_id: OpenAlex ID of the cited work
            max_results: Maximum number of citing papers to return
            
        Returns:
            List of citing publications
        """
        if not doi and not openalex_id:
            logger.warning("Must provide either DOI or OpenAlex ID")
            return []

        # Get the work first if we only have DOI
        if doi and not openalex_id:
            work = self.get_work_by_doi(doi)
            if not work:
                logger.warning(f"Work not found in OpenAlex: {doi}")
                return []
            openalex_id = work["id"]

        # Get citing works
        url = f"{self.config.api_url}/works"
        params = {
            "filter": f"cites:{openalex_id}",
            "per-page": min(max_results, 200),  # API max is 200
            "sort": "cited_by_count:desc",  # Most cited first
        }

        logger.info(f"Finding papers that cite {openalex_id}...")
        data = self._make_request(url, params=params)

        if not data or "results" not in data:
            logger.warning("No citing papers found")
            return []

        # Convert to Publications
        citing_papers = []
        for work in data["results"]:
            try:
                pub = self._convert_work_to_publication(work)
                citing_papers.append(pub)
            except Exception as e:
                logger.warning(f"Error converting work to publication: {e}")
                continue

        logger.info(f"Found {len(citing_papers)} citing papers")
        return citing_papers

    def search(self, query: str, max_results: int = 100, **kwargs) -> List[Publication]:
        """
        Search for publications.
        
        Args:
            query: Search query
            max_results: Maximum results to return
            **kwargs: Additional filters (publication_year, type, etc.)
            
        Returns:
            List of publications matching query
        """
        if not query:
            return []

        url = f"{self.config.api_url}/works"
        params = {
            "search": query,
            "per-page": min(max_results, 200),
            "sort": "cited_by_count:desc",
        }

        # Add additional filters
        filters = []
        if "publication_year" in kwargs:
            filters.append(f"publication_year:{kwargs['publication_year']}")
        if "type" in kwargs:
            filters.append(f"type:{kwargs['type']}")
        
        if filters:
            params["filter"] = ",".join(filters)

        logger.info(f"Searching OpenAlex: {query}")
        data = self._make_request(url, params=params)

        if not data or "results" not in data:
            logger.warning("No results found")
            return []

        # Convert to Publications
        publications = []
        for work in data["results"]:
            try:
                pub = self._convert_work_to_publication(work)
                publications.append(pub)
            except Exception as e:
                logger.warning(f"Error converting work: {e}")
                continue

        logger.info(f"Found {len(publications)} publications")
        return publications

    def fetch_by_id(self, identifier: str) -> Optional[Publication]:
        """
        Fetch a publication by DOI or OpenAlex ID.
        
        Args:
            identifier: DOI or OpenAlex ID (starts with 'W')
            
        Returns:
            Publication if found, None otherwise
        """
        if not identifier:
            return None

        # Check if it's an OpenAlex ID (starts with W) or DOI
        if identifier.startswith("W") or identifier.startswith("https://openalex.org/"):
            url = f"{self.config.api_url}/works/{identifier}"
            work = self._make_request(url)
        else:
            # Assume it's a DOI
            work = self.get_work_by_doi(identifier)

        if not work:
            return None

        return self._convert_work_to_publication(work)

    def _convert_work_to_publication(self, work: Dict) -> Publication:
        """
        Convert OpenAlex work to Publication object.
        
        Args:
            work: OpenAlex work dictionary
            
        Returns:
            Publication object
        """
        # Extract basic metadata
        title = work.get("title", "")
        
        # Extract authors
        authors = []
        for authorship in work.get("authorships", []):
            author = authorship.get("author", {})
            name = author.get("display_name", "")
            if name:
                authors.append(name)
        
        # Extract publication date
        pub_date = None
        pub_date_str = work.get("publication_date")
        if pub_date_str:
            try:
                pub_date = datetime.strptime(pub_date_str, "%Y-%m-%d")
            except:
                pass
        
        # Extract DOI
        doi = work.get("doi")
        if doi and doi.startswith("https://doi.org/"):
            doi = doi.replace("https://doi.org/", "")
        
        # Extract abstract (from abstract_inverted_index)
        abstract = self._extract_abstract(work.get("abstract_inverted_index"))
        
        # Extract journal/venue
        journal = None
        if work.get("primary_location"):
            source = work["primary_location"].get("source")
            if source:
                journal = source.get("display_name")
        
        # Create publication
        pub = Publication(
            title=title,
            authors=authors,
            abstract=abstract,
            publication_date=pub_date,
            journal=journal,
            doi=doi,
            pmid=None,  # OpenAlex doesn't provide PMID directly
            citations=work.get("cited_by_count", 0),
            source=PublicationSource.OPENALEX,
            metadata={
                "openalex_id": work.get("id"),
                "openalex_url": f"https://openalex.org/{work.get('id', '').split('/')[-1]}",
                "type": work.get("type"),
                "is_open_access": work.get("open_access", {}).get("is_oa", False),
                "oa_status": work.get("open_access", {}).get("oa_status"),
                "oa_url": work.get("open_access", {}).get("oa_url"),
                "topics": [t.get("display_name") for t in work.get("topics", [])[:3]],
                "referenced_works_count": work.get("referenced_works_count", 0),
                "concepts": [
                    c.get("display_name") 
                    for c in work.get("concepts", [])[:5]
                ],
            },
        )
        
        return pub

    def _extract_abstract(self, inverted_index: Optional[Dict]) -> str:
        """
        Extract abstract from OpenAlex's inverted index format.
        
        OpenAlex stores abstracts as inverted indexes for efficiency:
        {"word": [position1, position2, ...], ...}
        
        Args:
            inverted_index: Inverted index dictionary
            
        Returns:
            Reconstructed abstract text
        """
        if not inverted_index:
            return ""

        try:
            # Create list of (position, word) pairs
            word_positions = []
            for word, positions in inverted_index.items():
                for pos in positions:
                    word_positions.append((pos, word))
            
            # Sort by position and join
            word_positions.sort(key=lambda x: x[0])
            abstract = " ".join(word for _, word in word_positions)
            
            return abstract
        except Exception as e:
            logger.warning(f"Error extracting abstract from inverted index: {e}")
            return ""

    def enrich_publication(self, publication: Publication) -> Publication:
        """
        Enrich a publication with OpenAlex data.
        
        Args:
            publication: Publication to enrich
            
        Returns:
            Enriched publication
        """
        if not self.config.enable:
            return publication

        # Try to find work by DOI
        work = None
        if publication.doi:
            work = self.get_work_by_doi(publication.doi)

        if not work:
            logger.debug(f"Could not enrich publication: {publication.title[:50]}")
            return publication

        # Update citation count
        if work.get("cited_by_count"):
            publication.citations = work["cited_by_count"]

        # Add OpenAlex metadata
        if not publication.metadata:
            publication.metadata = {}
        
        publication.metadata.update({
            "openalex_id": work.get("id"),
            "openalex_enriched": True,
            "is_open_access": work.get("open_access", {}).get("is_oa", False),
            "oa_url": work.get("open_access", {}).get("oa_url"),
            "referenced_works_count": work.get("referenced_works_count", 0),
        })

        logger.debug(f"Enriched publication with OpenAlex data: {publication.title[:50]}")
        return publication

    def get_citation_contexts(
        self,
        cited_doi: str,
        citing_doi: str
    ) -> List[str]:
        """
        Get citation contexts (where the citation appears).
        
        Note: OpenAlex doesn't provide full citation contexts like Google Scholar snippets.
        This method returns what's available (abstract, title) as a fallback.
        
        Args:
            cited_doi: DOI of cited work
            citing_doi: DOI of citing work
            
        Returns:
            List of context strings (abstract, title)
        """
        contexts = []
        
        # Get citing work
        citing_work = self.get_work_by_doi(citing_doi)
        if not citing_work:
            return contexts
        
        # Use abstract as context if available
        abstract = self._extract_abstract(citing_work.get("abstract_inverted_index"))
        if abstract:
            contexts.append(abstract)
        
        # Fallback to title if no abstract
        if not contexts:
            title = citing_work.get("title", "")
            if title:
                contexts.append(title)
        
        return contexts
