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
from typing import List, Optional, Dict, Any
from datetime import datetime
import requests

from omics_oracle_v2.lib.search_engines.citations.models import Publication, PublicationSource
from omics_oracle_v2.lib.pipelines.citation_discovery.clients.config import OpenCitationsConfig

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
    """
    
    # OpenCitations API v1 (v2 doesn't exist yet)
    BASE_URL = "https://opencitations.net/index/coci/api/v1"
    
    def __init__(self, config: Optional[OpenCitationsConfig] = None):
        """
        Initialize OpenCitations client.
        
        Args:
            config: Configuration object (uses defaults if None)
        """
        self.config = config or OpenCitationsConfig()
        
        # Setup session
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'OmicsOracle/1.0 (https://github.com/sdodlapati3/OmicsOracle)'
        })
        
        # CRITICAL: Disable SSL verification for institutional VPN
        self.session.verify = False
        
        # Suppress SSL warnings
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # Rate limiting
        self._last_request_time = 0
        self._min_interval = 1.0 / self.config.requests_per_second
        
        logger.info(
            f"✓ OpenCitations client initialized "
            f"(rate: {self.config.requests_per_second} req/s)"
        )
    
    def get_citing_papers(
        self,
        doi: Optional[str] = None,
        pmid: Optional[str] = None,
        limit: int = 100
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
        clean_doi = target_doi.replace('https://doi.org/', '').replace('http://dx.doi.org/', '')
        
        try:
            # Query OpenCitations for papers citing this DOI
            # Endpoint: /citations/{doi}
            # Returns: List of citation metadata including citing DOIs
            
            url = f"{self.BASE_URL}/citations/{clean_doi}"
            data = self._make_request(url)
            
            if not data:
                logger.info(f"No citations found for DOI {clean_doi}")
                return []
            
            # Parse the citations
            papers = []
            for citation in data[:limit]:
                pub = self._parse_citation(citation)
                if pub:
                    papers.append(pub)
            
            logger.info(f"✓ OpenCitations: found {len(papers)} citing papers for {clean_doi}")
            return papers
            
        except Exception as e:
            logger.warning(f"OpenCitations request failed for DOI {clean_doi}: {e}")
            return []
    
    def get_metadata(self, doi: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a specific DOI from OpenCitations.
        
        Args:
            doi: DOI to look up
        
        Returns:
            Metadata dictionary or None if not found
        """
        try:
            clean_doi = doi.replace('https://doi.org/', '').replace('http://dx.doi.org/', '')
            url = f"{self.BASE_URL}/metadata/{clean_doi}"
            data = self._make_request(url)
            
            if data and len(data) > 0:
                return data[0]  # API returns a list with one item
            return None
            
        except Exception as e:
            logger.warning(f"Error fetching metadata for DOI {doi}: {e}")
            return None
    
    def _parse_citation(self, citation: Dict[str, Any]) -> Optional[Publication]:
        """
        Parse OpenCitations citation data into Publication object.
        
        Args:
            citation: Citation data from OpenCitations API
        
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
            
            citing_doi = citation.get('citing')
            if not citing_doi:
                return None
            
            # Get full metadata for the citing paper
            metadata = self.get_metadata(citing_doi)
            if not metadata:
                # Create minimal publication from citation data
                return Publication(
                    title=f"Publication {citing_doi}",  # Minimal info
                    authors=[],
                    doi=citing_doi,
                    url=f"https://doi.org/{citing_doi}",
                    source=PublicationSource.CROSSREF,  # Data from Crossref via OpenCitations
                    metadata={
                        'citation_created': citation.get('creation'),
                        'from_opencitations': True
                    }
                )
            
            # Parse full metadata
            # OpenCitations metadata format:
            # {
            #   "author": "Smith, John; Doe, Jane",
            #   "year": "2021",
            #   "title": "Paper Title",
            #   "source_title": "Journal Name",
            #   "volume": "42",
            #   "issue": "3",
            #   "page": "123-145",
            #   "doi": "10.1234/example",
            #   "reference": "...",
            #   "citation_count": "5",
            #   "citation": "...",
            #   "oa_link": "https://..."
            # }
            
            title = metadata.get('title', '')
            if not title:
                return None
            
            # Parse authors (format: "Last, First; Last2, First2")
            authors = []
            author_str = metadata.get('author', '')
            if author_str:
                for author in author_str.split(';'):
                    author = author.strip()
                    if author:
                        # Convert "Last, First" to "First Last"
                        parts = author.split(',')
                        if len(parts) == 2:
                            authors.append(f"{parts[1].strip()} {parts[0].strip()}")
                        else:
                            authors.append(author)
            
            # Parse year
            pub_date = None
            year_str = metadata.get('year', '')
            if year_str:
                try:
                    pub_date = datetime(int(year_str), 1, 1)
                except (ValueError, TypeError):
                    pass
            
            # Get journal and other metadata
            journal = metadata.get('source_title')
            volume = metadata.get('volume')
            issue = metadata.get('issue')
            pages = metadata.get('page')
            
            # Get citation count
            citations = 0
            citation_count_str = metadata.get('citation_count', '0')
            try:
                citations = int(citation_count_str)
            except (ValueError, TypeError):
                pass
            
            # Get OA link if available
            oa_link = metadata.get('oa_link')
            url = oa_link if oa_link else f"https://doi.org/{citing_doi}"
            
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
                    'volume': volume,
                    'issue': issue,
                    'pages': pages,
                    'citation_created': citation.get('creation'),
                    'from_opencitations': True,
                    'oa_link': oa_link
                }
            )
            
        except Exception as e:
            logger.warning(f"Error parsing OpenCitations citation: {e}")
            return None
    
    def _make_request(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        max_retries: int = 3
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
                
                # Make request
                response = self.session.get(url, params=params, timeout=30)
                
                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 5))
                    logger.warning(f"Rate limited, waiting {retry_after}s...")
                    time.sleep(retry_after)
                    continue
                
                response.raise_for_status()
                
                return response.json()
                
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 1.0  # Exponential backoff
                    logger.warning(
                        f"OpenCitations request failed (attempt {attempt + 1}/{max_retries}), "
                        f"retrying in {wait_time}s: {e}"
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(f"OpenCitations request failed after {max_retries} attempts: {e}")
                    return None
        
        return None
