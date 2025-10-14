"""
OpenCitations API client for citation discovery.

OpenCitations is a free, open infrastructure that provides citation data
harvested from scholarly publishers and open repositories.

Features:
- Free and open access (no API key required)
- Direct citations endpoint (papers citing a DOI)
- Data from Crossref, PubMed, and other sources
- Simple REST API with JSON responses

Coverage:
- 1.5B+ citation links
- Data from multiple sources (Crossref, NIH OCC, etc.)
- Regular updates

Rate Limits:
- Reasonable use: ~1 request per second recommended
- No hard limits for non-commercial use

API Documentation: https://opencitations.net/index/coci/api/v1
"""

import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests

from omics_oracle_v2.lib.pipelines.citation_discovery.clients.config import OpenCitationsConfig
from omics_oracle_v2.lib.search_engines.citations.models import Publication, PublicationSource

logger = logging.getLogger(__name__)


class OpenCitationsClient:
    """
    Client for OpenCitations API.

    OpenCitations provides:
    - 1.5B+ citation links
    - Free and open access
    - Data from Crossref and other sources
    - Direct citations endpoint

    Features:
    - Citation discovery (papers citing a DOI)
    - Metadata for citations
    - No API key required
    - Simple REST API

    Architecture:
    - COCI API (/index/coci/api/v1): Citation links
    - Meta API (/meta/api/v1): Metadata with batch support
    """

    # OpenCitations API endpoints
    COCI_BASE_URL = "https://opencitations.net/index/coci/api/v1"  # Citations
    META_BASE_URL = "https://opencitations.net/meta/api/v1"  # Metadata (batch support!)

    def __init__(self, config: Optional[OpenCitationsConfig] = None):
        """
        Initialize OpenCitations client.

        Args:
            config: Configuration object (uses defaults if None)
        """
        self.config = config or OpenCitationsConfig()

        # Setup session
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "OmicsOracle/1.0 (https://github.com/sdodlapati3/OmicsOracle)"}
        )

        # CRITICAL: Disable SSL verification for institutional VPN
        self.session.verify = False

        # Suppress SSL warnings
        import urllib3

        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        # Rate limiting
        self._last_request_time = 0
        self._min_interval = 1.0 / self.config.requests_per_second

        logger.info(f"✓ OpenCitations client initialized " f"(rate: {self.config.requests_per_second} req/s)")

    def get_citing_papers(
        self, doi: Optional[str] = None, pmid: Optional[str] = None, limit: int = 100
    ) -> List[Publication]:
        """
        Find papers citing a given publication.

        OpenCitations provides direct citation data from Crossref and other sources.
        The API returns citing DOIs which we then need to resolve to full metadata.

        Args:
            doi: DOI of the paper to find citations for
            pmid: PubMed ID (will try to convert to DOI first)
            limit: Maximum number of citing papers to return

        Returns:
            List of Publication objects citing the given paper
        """
        if not doi and not pmid:
            raise ValueError("Either doi or pmid must be provided")

        # If we have PMID, try to convert to DOI
        target_doi = doi
        if not target_doi and pmid:
            # For now, skip PMID->DOI conversion (could use PubMed or Crossref)
            logger.warning(f"OpenCitations requires DOI, cannot convert PMID {pmid}")
            return []

        if not target_doi:
            return []

        # Clean DOI (remove prefix if present)
        clean_doi = target_doi.replace("https://doi.org/", "").replace("http://dx.doi.org/", "")

        try:
            # Query OpenCitations for papers citing this DOI
            # Endpoint: /citations/{doi}
            # Returns: List of citation metadata including citing DOIs

            url = f"{self.COCI_BASE_URL}/citations/{clean_doi}"
            data = self._make_request(url)

            if not data:
                logger.info(f"No citations found for DOI {clean_doi}")
                return []

            # Extract all citing DOIs
            citing_dois = []
            for citation in data[:limit]:
                citing_doi = citation.get("citing")
                if citing_doi:
                    citing_dois.append(citing_doi)

            if not citing_dois:
                return []

            # BATCH FETCH metadata for all citing DOIs at once (much faster!)
            metadata_map = self.get_metadata_batch(citing_dois)

            # Parse citations with metadata
            papers = []
            for citation in data[:limit]:
                pub = self._parse_citation(citation, metadata_map)
                if pub:
                    papers.append(pub)

            logger.info(f"✓ OpenCitations: found {len(papers)} citing papers for {clean_doi}")
            return papers

        except Exception as e:
            logger.warning(f"OpenCitations request failed for DOI {clean_doi}: {e}")
            return []

    def get_metadata_batch(self, dois: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Get metadata for multiple DOIs in a single batch request.

        OpenCitations Meta API supports batch requests with DOIs separated by '__'
        This is MUCH faster than individual requests.

        Args:
            dois: List of DOIs to fetch metadata for

        Returns:
            Dictionary mapping DOI to metadata dict
        """
        if not dois:
            return {}

        try:
            # Clean DOIs and add 'doi:' prefix for Meta API
            clean_dois = []
            for doi in dois:
                clean = doi.replace("https://doi.org/", "").replace("http://dx.doi.org/", "")
                clean_dois.append(f"doi:{clean}")

            # OpenCitations Meta API batch format: doi:DOI1__doi:DOI2__doi:DOI3
            # Limit: Small batches to avoid URL length issues (400 Bad Request)
            batch_size = 10  # Conservative batch size
            all_metadata = {}

            for i in range(0, len(clean_dois), batch_size):
                batch = clean_dois[i : i + batch_size]
                batch_doi_string = "__".join(batch)

                # Use Meta API for metadata (not COCI API!)
                url = f"{self.META_BASE_URL}/metadata/{batch_doi_string}"
                data = self._make_request(url)

                if data:
                    # API returns list of metadata objects
                    for item in data:
                        # Meta API returns 'id' field with format: "doi:10.xxx/xxx ..."
                        item_id = item.get("id", "")
                        # Extract just the DOI part
                        doi_part = item_id.split()[0].replace("doi:", "") if item_id else ""
                        if doi_part:
                            all_metadata[doi_part] = item

            logger.info(f"✓ Fetched metadata for {len(all_metadata)}/{len(dois)} DOIs in batch")
            return all_metadata

        except Exception as e:
            logger.warning(f"Batch metadata request failed: {e}")
            return {}

    def get_metadata(self, doi: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a specific DOI from OpenCitations Meta API.

        Args:
            doi: DOI to look up

        Returns:
            Metadata dictionary or None if not found
        """
        try:
            clean_doi = doi.replace("https://doi.org/", "").replace("http://dx.doi.org/", "")
            # Use Meta API with doi: prefix
            url = f"{self.META_BASE_URL}/metadata/doi:{clean_doi}"
            data = self._make_request(url)

            if data and len(data) > 0:
                return data[0]  # API returns a list with one item
            return None

        except Exception as e:
            logger.warning(f"Error fetching metadata for DOI {doi}: {e}")
            return None

    def _parse_citation(
        self, citation: Dict[str, Any], metadata_map: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> Optional[Publication]:
        """
        Parse OpenCitations citation data into Publication object.

        Args:
            citation: Citation data from OpenCitations API
            metadata_map: Optional pre-fetched metadata map (for batch mode)

        Returns:
            Publication object or None if parsing fails
        """
        try:
            # OpenCitations citation format:
            # {
            #   "citing": "10.1234/citing-doi",
            #   "cited": "10.1234/cited-doi",
            #   "creation": "2021-01-15",
            #   "timespan": "P2Y",
            #   "journal_sc": "no",
            #   "author_sc": "no"
            # }

            citing_doi = citation.get("citing")
            if not citing_doi:
                return None

            # Get metadata from map (batch mode) or fetch individually
            metadata = None
            if metadata_map:
                metadata = metadata_map.get(citing_doi)
            else:
                metadata = self.get_metadata(citing_doi)

            if not metadata:
                # Create minimal publication from citation data
                return Publication(
                    title=f"Publication {citing_doi}",  # Minimal info
                    authors=[],
                    doi=citing_doi,
                    url=f"https://doi.org/{citing_doi}",
                    source=PublicationSource.CROSSREF,  # Data from Crossref via OpenCitations
                    metadata={"citation_created": citation.get("creation"), "from_opencitations": True},
                )

            # Parse full metadata
            # OpenCitations Meta API format:
            # {
            #   "id": "doi:10.1234/example openalex:W123 pmid:123456 omid:br/...",
            #   "title": "Paper Title",
            #   "author": "Last1, First1 [orcid:...]; Last2, First2",
            #   "pub_date": "2021-06-15",
            #   "venue": "Journal Name [issn:1234-5678 openalex:S123]",
            #   "volume": "42",
            #   "issue": "3",
            #   "page": "123-145",
            #   "type": "journal article",
            #   "publisher": "Publisher Name [crossref:123]",
            #   "editor": ""
            # }

            title = metadata.get("title", "")
            if not title:
                return None

            # Parse authors (format: "Last1, First1 [orcid:...]; Last2, First2")
            authors = []
            author_str = metadata.get("author", "")
            if author_str:
                for author in author_str.split(";"):
                    author = author.strip()
                    if author:
                        # Remove ORCID/OMID identifiers in brackets
                        author_clean = author.split("[")[0].strip()
                        # Convert "Last, First" to "First Last"
                        parts = author_clean.split(",")
                        if len(parts) == 2:
                            authors.append(f"{parts[1].strip()} {parts[0].strip()}")
                        else:
                            authors.append(author_clean)

            # Parse publication date
            pub_date = None
            pub_date_str = metadata.get("pub_date", "")
            if pub_date_str:
                try:
                    # Format: "2021-06-15" or "2021-06" or "2021"
                    parts = pub_date_str.split("-")
                    if len(parts) == 3:
                        pub_date = datetime(int(parts[0]), int(parts[1]), int(parts[2]))
                    elif len(parts) == 2:
                        pub_date = datetime(int(parts[0]), int(parts[1]), 1)
                    elif len(parts) == 1:
                        pub_date = datetime(int(parts[0]), 1, 1)
                except (ValueError, TypeError):
                    pass

            # Get journal (venue format: "Journal Name [issn:... openalex:...]")
            journal = None
            venue_str = metadata.get("venue", "")
            if venue_str:
                journal = venue_str.split("[")[0].strip()

            volume = metadata.get("volume")
            issue = metadata.get("issue")
            pages = metadata.get("page")
            publisher = (
                metadata.get("publisher", "").split("[")[0].strip() if metadata.get("publisher") else None
            )

            # Meta API doesn't have citation_count, use 0
            citations = 0

            # Build URL
            url = f"https://doi.org/{citing_doi}"

            return Publication(
                title=title,
                authors=authors,
                journal=journal,
                publication_date=pub_date,
                doi=citing_doi,
                url=url,
                source=PublicationSource.CROSSREF,  # Data from Crossref via OpenCitations
                citations=citations,
                metadata={
                    "volume": volume,
                    "issue": issue,
                    "pages": pages,
                    "publisher": publisher,
                    "citation_created": citation.get("creation"),
                    "from_opencitations": True,
                    "pub_type": metadata.get("type"),
                },
            )

        except Exception as e:
            logger.warning(f"Error parsing OpenCitations citation: {e}")
            return None

    def _make_request(
        self, url: str, params: Optional[Dict[str, Any]] = None, max_retries: int = 3
    ) -> Optional[Any]:
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

                # Make request (allow redirects)
                response = self.session.get(url, params=params, timeout=30, allow_redirects=True)

                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 5))
                    logger.warning(f"Rate limited, waiting {retry_after}s...")
                    time.sleep(retry_after)
                    continue

                response.raise_for_status()

                return response.json()

            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    wait_time = (2**attempt) * 1.0  # Exponential backoff
                    logger.warning(
                        f"OpenCitations request failed (attempt {attempt + 1}/{max_retries}), "
                        f"retrying in {wait_time}s: {e}"
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(f"OpenCitations request failed after {max_retries} attempts: {e}")
                    return None

        return None
