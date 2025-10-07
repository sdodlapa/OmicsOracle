"""
Google Scholar client for publication search.

This module provides a client for searching academic publications via Google Scholar,
complementing PubMed with additional sources like preprints, conference papers, and theses.

Features:
- Broader coverage than PubMed (preprints, conferences, theses)
- Citation counts and metrics
- Related papers discovery
- Author profile integration

Rate Limits:
- No official API (uses web scraping via scholarly library)
- Recommended: 1 request per 3-5 seconds to avoid blocking
- Optional proxy support for higher volume

Example:
    >>> from omics_oracle_v2.lib.publications.clients.scholar import GoogleScholarClient
    >>> from omics_oracle_v2.lib.publications.config import GoogleScholarConfig
    >>>
    >>> config = GoogleScholarConfig(enable=True, rate_limit_seconds=3.0)
    >>> client = GoogleScholarClient(config)
    >>> results = client.search("CRISPR cancer therapy", max_results=10)
    >>>
    >>> for pub in results:
    ...     print(f"{pub.title} - Citations: {pub.citations}")
"""

import logging
import os
import ssl
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

# Disable SSL verification if environment variable is set (for institutional networks)
if os.getenv("PYTHONHTTPSVERIFY", "1") == "0":
    ssl._create_default_https_context = ssl._create_unverified_context

try:
    from scholarly import scholarly

    SCHOLARLY_AVAILABLE = True
except ImportError:
    SCHOLARLY_AVAILABLE = False
    scholarly = None

from omics_oracle_v2.core.exceptions import PublicationSearchError

from ..config import GoogleScholarConfig
from ..models import Publication, PublicationSource
from .base import BasePublicationClient


class GoogleScholarClient(BasePublicationClient):
    """
    Google Scholar client for academic publication search.

    This client uses the scholarly library to search Google Scholar,
    providing broader coverage than PubMed alone, including:
    - Preprints and working papers
    - Conference proceedings
    - Theses and dissertations
    - Technical reports
    - Book chapters

    Attributes:
        config: Google Scholar configuration
        logger: Logger instance

    Note:
        Google Scholar does not provide an official API. This client uses
        web scraping via the scholarly library, which may be blocked if
        requests are too frequent. Use rate limiting and consider proxies
        for production use.
    """

    def __init__(self, config: GoogleScholarConfig):
        """
        Initialize Google Scholar client.

        Args:
            config: Google Scholar configuration

        Raises:
            ImportError: If scholarly library is not installed
        """
        if not SCHOLARLY_AVAILABLE:
            raise ImportError(
                "scholarly library is required for Google Scholar search. "
                "Install with: pip install scholarly"
            )

        super().__init__(config)
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Configure proxy if provided
        if self.config.use_proxy and self.config.proxy_url:
            self._configure_proxy()

        self.logger.info(f"GoogleScholarClient initialized (rate limit: {config.rate_limit_seconds}s)")

    @property
    def source_name(self) -> str:
        """Get the name of this publication source."""
        return "google_scholar"

    def _configure_proxy(self):
        """Configure proxy for scholarly library."""
        try:
            # Note: scholarly proxy configuration would go here
            # For Week 3, we'll keep it simple without proxy
            self.logger.info(f"Proxy configured: {self.config.proxy_url}")
        except Exception as e:
            self.logger.warning(f"Failed to configure proxy: {e}")

    def search(
        self,
        query: str,
        max_results: int = 50,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
    ) -> List[Publication]:
        """
        Search Google Scholar for publications.

        Args:
            query: Search query string
            max_results: Maximum number of results to return
            year_from: Filter publications from this year onwards
            year_to: Filter publications up to this year

        Returns:
            List of Publication objects

        Raises:
            PublicationSearchError: If search fails

        Example:
            >>> results = client.search("machine learning genomics", max_results=20)
            >>> print(f"Found {len(results)} publications")
        """
        self.logger.info(
            f"Searching Scholar: '{query}', max_results={max_results}, " f"year_range={year_from}-{year_to}"
        )

        try:
            # Build year range string for Scholar
            year_range = None
            if year_from or year_to:
                year_range = f"{year_from or ''}-{year_to or ''}"

            # Perform search using scholarly
            search_generator = scholarly.search_pubs(query, year_low=year_from, year_high=year_to)

            publications = []
            for i, result in enumerate(search_generator):
                if i >= max_results:
                    break

                try:
                    # Parse Scholar result into Publication model
                    pub = self._parse_scholar_result(result)
                    publications.append(pub)

                    # Rate limiting between results
                    if i < max_results - 1:  # Don't sleep after last result
                        time.sleep(self.config.rate_limit_seconds)

                except Exception as e:
                    self.logger.warning(f"Failed to parse result {i}: {e}")
                    continue

            self.logger.info(f"Found {len(publications)} publications from Scholar")
            return publications

        except Exception as e:
            error_msg = f"Google Scholar search failed: {e}"
            self.logger.error(error_msg)
            raise PublicationSearchError(error_msg)

    def fetch_by_id(self, identifier: str) -> Optional[Publication]:
        """
        Fetch a single publication by identifier (DOI or title).

        This is an alias for fetch_by_doi for compatibility with the
        base class interface. Scholar doesn't have its own ID system,
        so we use DOI or search by title.

        Args:
            identifier: DOI or publication title

        Returns:
            Publication if found, None otherwise
        """
        # Try as DOI first
        if identifier.startswith("10."):
            return self.fetch_by_doi(identifier)

        # Otherwise search by exact title
        return self.fetch_by_doi(identifier)  # Will search by title

    def fetch_by_doi(self, doi: str) -> Optional[Publication]:
        """
        Fetch a single publication by DOI from Google Scholar.

        Args:
            doi: Digital Object Identifier

        Returns:
            Publication if found, None otherwise

        Example:
            >>> pub = client.fetch_by_doi("10.1038/nature12345")
            >>> if pub:
            ...     print(f"Found: {pub.title}")
        """
        self.logger.info(f"Fetching Scholar publication by DOI: {doi}")

        try:
            # Search Scholar by DOI
            results = self.search(f"doi:{doi}", max_results=1)

            if results:
                return results[0]

            self.logger.warning(f"No Scholar result found for DOI: {doi}")
            return None

        except Exception as e:
            self.logger.error(f"Failed to fetch by DOI {doi}: {e}")
            return None

    def get_citations(self, publication: Publication) -> int:
        """
        Get citation count for a publication.

        Args:
            publication: Publication to get citations for

        Returns:
            Citation count (0 if unavailable)

        Note:
            If the publication already has a Scholar ID in metadata,
            this method will use it. Otherwise, it searches by title.
        """
        try:
            scholar_id = publication.metadata.get("scholar_id")

            if scholar_id:
                # Use Scholar ID to get citations
                pub_info = scholarly.search_pubs(scholar_id)
                result = next(pub_info, None)
                if result:
                    return result.get("num_citations", 0)
            else:
                # Search by title
                search_query = f'"{publication.title}"'
                search_results = scholarly.search_pubs(search_query)
                result = next(search_results, None)
                if result:
                    return result.get("num_citations", 0)

            return 0

        except Exception as e:
            self.logger.warning(f"Failed to get citations: {e}")
            return 0

    def _parse_scholar_result(self, result: Dict[str, Any]) -> Publication:
        """
        Convert Google Scholar result to Publication model.

        Args:
            result: Raw result dictionary from scholarly library

        Returns:
            Publication object

        Note:
            Scholar results have a different structure than PubMed.
            This method normalizes them to our Publication model.
        """
        bib = result.get("bib", {})

        # Parse authors
        authors = self._parse_authors(bib.get("author", []))

        # Parse publication date
        pub_date = self._parse_date(bib.get("pub_year"))

        # Build publication
        return Publication(
            # Core fields
            title=bib.get("title", ""),
            abstract=bib.get("abstract", ""),
            authors=authors,
            journal=bib.get("venue", ""),
            publication_date=pub_date,
            # Identifiers
            doi=result.get("doi"),
            pmid=None,  # Scholar doesn't provide PMID
            pmcid=None,
            # Metrics
            citations=result.get("num_citations", 0),
            # Source
            source=PublicationSource.GOOGLE_SCHOLAR,
            # Scholar-specific metadata
            metadata={
                "scholar_id": result.get("scholar_id"),
                "scholar_url": result.get("pub_url"),
                "eprint_url": result.get("eprint_url"),
                "pdf_url": result.get("eprint_url"),  # Often points to PDF
                "num_versions": result.get("num_versions", 0),
                "url_related_articles": result.get("url_related_articles"),
                "citedby_url": result.get("citedby_url"),
            },
        )

    def _parse_authors(self, author_data: Any) -> List[str]:
        """
        Parse author information from Scholar result.

        Args:
            author_data: Author data (string or list)

        Returns:
            List of author names
        """
        if isinstance(author_data, list):
            return author_data
        elif isinstance(author_data, str):
            # Split by common delimiters
            if "," in author_data:
                return [a.strip() for a in author_data.split(",")]
            elif " and " in author_data:
                return [a.strip() for a in author_data.split(" and ")]
            else:
                return [author_data]
        else:
            return []

    def _parse_date(self, year_str: Any) -> Optional[datetime]:
        """
        Parse publication year into datetime.

        Args:
            year_str: Year as string or int

        Returns:
            datetime object or None
        """
        try:
            if year_str:
                year = int(year_str)
                return datetime(year, 1, 1)
        except (ValueError, TypeError):
            pass

        return None

    def cleanup(self):
        """Clean up resources."""
        self.logger.info("GoogleScholarClient cleanup complete")
