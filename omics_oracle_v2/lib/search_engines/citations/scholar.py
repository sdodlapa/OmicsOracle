"""
Enhanced Google Scholar client using scholarly library for citation metrics.

This module provides a robust client for Google Scholar with:
- Citation counts and metrics
- Cited-by paper lists
- Author profile data
- Rate limiting and retry logic
- Proxy support for avoiding blocks

Features:
- Full citation metrics (count, h-index, i10-index)
- Access to cited-by papers list
- Related papers discovery
- Author information and profiles
- Robust error handling and retry logic

Example:
    >>> from omics_oracle_v2.lib.citations.clients.scholar import GoogleScholarClient
    >>> from omics_oracle_v2.lib.search_engines.citations.config import GoogleScholarConfig
    >>>
    >>> config = GoogleScholarConfig(enable=True, rate_limit_seconds=5.0)
    >>> client = GoogleScholarClient(config)
    >>>
    >>> # Search with citation enrichment
    >>> results = client.search("CRISPR cancer therapy", max_results=10)
    >>> for pub in results:
    ...     print(f"{pub.title} - Citations: {pub.citations}")
    >>>
    >>> # Get cited-by papers
    >>> cited_by = client.get_cited_by_papers(results[0], max_papers=20)
    >>> print(f"Papers citing this work: {len(cited_by)}")
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
    from scholarly import ProxyGenerator, scholarly

    SCHOLARLY_AVAILABLE = True
except ImportError:
    SCHOLARLY_AVAILABLE = False
    scholarly = None
    ProxyGenerator = None

from omics_oracle_v2.core.exceptions import PublicationSearchError
from omics_oracle_v2.lib.search_engines.citations.base import BasePublicationClient
from omics_oracle_v2.lib.search_engines.citations.config import GoogleScholarConfig
from omics_oracle_v2.lib.search_engines.citations.models import Publication, PublicationSource


class GoogleScholarClient(BasePublicationClient):
    """
    Enhanced Google Scholar client with citation metrics and cited-by access.

    This client uses the scholarly library to provide:
    - Publication search with citation counts
    - Cited-by paper lists (papers that cite a given work)
    - Author profiles and metrics
    - Rate limiting to avoid blocking
    - Optional proxy support

    Attributes:
        config: Google Scholar configuration
        logger: Logger instance
        retry_count: Number of retries on failure (default: 3)
        retry_delay: Delay between retries in seconds (default: 10)
    """

    def __init__(self, config: GoogleScholarConfig):
        """
        Initialize enhanced Google Scholar client.

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
        self.retry_count = 3
        self.retry_delay = 10  # seconds

        # Configure proxy if provided
        if self.config.use_proxy and self.config.proxy_url:
            self._configure_proxy()

        self.logger.info(
            f"Enhanced GoogleScholarClient initialized "
            f"(rate_limit={config.rate_limit_seconds}s, retries={self.retry_count})"
        )

    @property
    def source_name(self) -> str:
        """Get the name of this publication source."""
        return "google_scholar"

    def _configure_proxy(self):
        """Configure proxy for scholarly library to avoid blocking."""
        try:
            if ProxyGenerator and self.config.proxy_url:
                pg = ProxyGenerator()
                # Set up proxy (free or paid service)
                if "luminati" in self.config.proxy_url or "scraperapi" in self.config.proxy_url:
                    pg.ScraperAPI(self.config.proxy_url)
                else:
                    pg.SingleProxy(http=self.config.proxy_url, https=self.config.proxy_url)

                scholarly.use_proxy(pg)
                self.logger.info(f"Proxy configured: {self.config.proxy_url}")
        except Exception as e:
            self.logger.warning(f"Failed to configure proxy: {e}")

    def _retry_on_block(self, func, *args, **kwargs):
        """
        Retry a function call if it fails due to blocking.

        Args:
            func: Function to call
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Result of func call

        Raises:
            PublicationSearchError: If all retries fail
        """
        for attempt in range(self.retry_count):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_str = str(e).lower()
                if "block" in error_str or "429" in error_str or "captcha" in error_str:
                    if attempt < self.retry_count - 1:
                        wait_time = self.retry_delay * (attempt + 1)  # Exponential backoff
                        self.logger.warning(
                            f"Blocked by Google Scholar (attempt {attempt + 1}/{self.retry_count}). "
                            f"Waiting {wait_time}s before retry..."
                        )
                        time.sleep(wait_time)
                        continue
                    else:
                        raise PublicationSearchError(
                            "Google Scholar blocked requests after multiple retries. "
                            "Try again later or use a proxy."
                        )
                else:
                    raise

    def search(
        self,
        query: str,
        max_results: int = 50,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
    ) -> List[Publication]:
        """
        Search Google Scholar with citation enrichment.

        Args:
            query: Search query string
            max_results: Maximum number of results to return
            year_from: Filter publications from this year onwards
            year_to: Filter publications up to this year

        Returns:
            List of Publication objects with citation counts

        Raises:
            PublicationSearchError: If search fails after retries
        """
        self.logger.info(
            f"Searching Scholar: '{query}', max_results={max_results}, " f"year_range={year_from}-{year_to}"
        )

        try:
            # Perform search with retry logic
            search_generator = self._retry_on_block(
                scholarly.search_pubs,
                query,
                year_low=year_from,
                year_high=year_to,
            )

            publications = []
            for i, result in enumerate(search_generator):
                if i >= max_results:
                    break

                try:
                    # Parse and enrich with citations
                    pub = self._parse_scholar_result(result)
                    publications.append(pub)

                    # Rate limiting
                    if i < max_results - 1:
                        time.sleep(self.config.rate_limit_seconds)

                except Exception as e:
                    self.logger.warning(f"Failed to parse result {i}: {e}")
                    continue

            self.logger.info(
                f"Found {len(publications)} publications from Scholar "
                f"(avg citations: {sum(p.citations for p in publications) / len(publications) if publications else 0:.1f})"
            )
            return publications

        except Exception as e:
            error_msg = f"Google Scholar search failed: {e}"
            self.logger.error(error_msg)
            raise PublicationSearchError(error_msg)

    def get_cited_by_papers(self, publication: Publication, max_papers: int = 50) -> List[Publication]:
        """
        Get list of papers that cite the given publication.

        Args:
            publication: Publication to get citations for
            max_papers: Maximum number of citing papers to return

        Returns:
            List of Publication objects that cite the given work

        Example:
            >>> pub = client.search("CRISPR")[0]
            >>> citing_papers = client.get_cited_by_papers(pub, max_papers=20)
            >>> print(f"{len(citing_papers)} papers cite this work")
        """
        self.logger.info(f"Fetching cited-by papers for: {publication.title[:60]}...")

        try:
            # Get the citedby_url from metadata
            citedby_url = publication.metadata.get("citedby_url")

            if not citedby_url:
                # Search for publication first to get citedby_url
                search_results = self._retry_on_block(
                    scholarly.search_pubs,
                    f'"{publication.title}"',
                )
                result = next(search_results, None)
                if result:
                    citedby_url = result.get("citedby_url")

            if not citedby_url:
                self.logger.warning(f"No citedby_url found for: {publication.title[:60]}")
                return []

            # Fetch citing papers using citedby_url
            citing_pubs = []
            cited_by_generator = self._retry_on_block(
                scholarly.citedby,
                citedby_url,
            )

            for i, result in enumerate(cited_by_generator):
                if i >= max_papers:
                    break

                try:
                    pub = self._parse_scholar_result(result)
                    citing_pubs.append(pub)

                    # Rate limiting
                    if i < max_papers - 1:
                        time.sleep(self.config.rate_limit_seconds)

                except Exception as e:
                    self.logger.warning(f"Failed to parse citing paper {i}: {e}")
                    continue

            self.logger.info(f"Found {len(citing_pubs)} papers citing: {publication.title[:60]}")
            return citing_pubs

        except Exception as e:
            self.logger.error(f"Failed to get cited-by papers: {e}")
            return []

    def enrich_with_citations(self, publication: Publication) -> Publication:
        """
        Enrich a publication with citation metrics from Google Scholar.

        Args:
            publication: Publication to enrich

        Returns:
            Publication with updated citation count and metadata

        Example:
            >>> pub = Publication(title="CRISPR-Cas9", ...)
            >>> enriched = client.enrich_with_citations(pub)
            >>> print(f"Citations: {enriched.citations}")
        """
        try:
            # Search by title to get citation info
            search_query = f'"{publication.title}"'
            search_results = self._retry_on_block(scholarly.search_pubs, search_query)

            result = next(search_results, None)
            if result:
                # Update citation count
                publication.citations = result.get("num_citations", 0)

                # Add Scholar-specific metadata
                publication.metadata.update(
                    {
                        "scholar_id": result.get("scholar_id"),
                        "scholar_url": result.get("pub_url"),
                        "citedby_url": result.get("citedby_url"),
                        "num_versions": result.get("num_versions", 0),
                        "url_related_articles": result.get("url_related_articles"),
                    }
                )

                self.logger.debug(
                    f"Enriched '{publication.title[:50]}...' with {publication.citations} citations"
                )
            else:
                self.logger.warning(f"No Scholar match for: {publication.title[:60]}")

            return publication

        except Exception as e:
            self.logger.warning(f"Failed to enrich with citations: {e}")
            return publication

    def get_author_info(self, author_name: str) -> Optional[Dict[str, Any]]:
        """
        Get author profile information from Google Scholar.

        Args:
            author_name: Name of the author to search for

        Returns:
            Dictionary with author information (h-index, citations, etc.)

        Example:
            >>> info = client.get_author_info("Jennifer Doudna")
            >>> print(f"H-index: {info['hindex']}, Citations: {info['citedby']}")
        """
        try:
            search_query = self._retry_on_block(scholarly.search_author, author_name)
            author = next(search_query, None)

            if author:
                # Fill in author details
                filled_author = self._retry_on_block(scholarly.fill, author)

                return {
                    "name": filled_author.get("name"),
                    "affiliation": filled_author.get("affiliation"),
                    "email": filled_author.get("email"),
                    "interests": filled_author.get("interests", []),
                    "citedby": filled_author.get("citedby", 0),
                    "hindex": filled_author.get("hindex", 0),
                    "i10index": filled_author.get("i10index", 0),
                    "scholar_id": filled_author.get("scholar_id"),
                    "url_picture": filled_author.get("url_picture"),
                }

            return None

        except Exception as e:
            self.logger.error(f"Failed to get author info for '{author_name}': {e}")
            return None

    def fetch_by_id(self, identifier: str) -> Optional[Publication]:
        """
        Fetch a single publication by identifier (DOI or title).

        Args:
            identifier: DOI or publication title

        Returns:
            Publication if found, None otherwise
        """
        if identifier.startswith("10."):
            return self.fetch_by_doi(identifier)
        else:
            # Search by exact title
            results = self.search(f'"{identifier}"', max_results=1)
            return results[0] if results else None

    def fetch_by_doi(self, doi: str) -> Optional[Publication]:
        """
        Fetch a single publication by DOI from Google Scholar.

        Args:
            doi: Digital Object Identifier

        Returns:
            Publication if found, None otherwise
        """
        self.logger.info(f"Fetching Scholar publication by DOI: {doi}")

        try:
            results = self.search(f"doi:{doi}", max_results=1)
            return results[0] if results else None

        except Exception as e:
            self.logger.error(f"Failed to fetch by DOI {doi}: {e}")
            return None

    def _parse_scholar_result(self, result: Dict[str, Any]) -> Publication:
        """
        Convert Google Scholar result to Publication model with full metadata.

        Args:
            result: Raw result dictionary from scholarly library

        Returns:
            Publication object with citation metrics
        """
        bib = result.get("bib", {})

        # Parse authors
        authors = self._parse_authors(bib.get("author", []))

        # Parse publication date
        pub_date = self._parse_date(bib.get("pub_year"))

        # Build publication with full metadata
        return Publication(
            # Core fields
            title=bib.get("title", ""),
            abstract=bib.get("abstract", ""),
            authors=authors,
            journal=bib.get("venue", ""),
            publication_date=pub_date,
            # Identifiers
            doi=result.get("doi"),
            pmid=None,
            pmcid=None,
            # Metrics (KEY FEATURE!)
            citations=result.get("num_citations", 0),
            # Source
            source=PublicationSource.GOOGLE_SCHOLAR,
            # Scholar-specific metadata (for cited-by access)
            metadata={
                "scholar_id": result.get("scholar_id"),
                "scholar_url": result.get("pub_url"),
                "eprint_url": result.get("eprint_url"),
                "pdf_url": result.get("eprint_url"),
                "num_versions": result.get("num_versions", 0),
                "url_related_articles": result.get("url_related_articles"),
                "citedby_url": result.get("citedby_url"),  # KEY for cited-by access!
                "cites_id": result.get("cites_id", []),  # Papers this work cites
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
        self.logger.info("Enhanced GoogleScholarClient cleanup complete")
