"""
Base client interface for publication sources.

All publication clients (PubMed, Scholar, etc.) inherit from this base class
to ensure consistent interface and error handling.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from omics_oracle_v2.lib.search_engines.citations.models import Publication


class BasePublicationClient(ABC):
    """
    Abstract base class for all publication clients.

    All clients must implement:
    - search(): Search for publications by query
    - fetch_by_id(): Fetch publication by identifier
    - get_citations(): Get citation count (if supported)
    """

    def __init__(self, config):
        """
        Initialize the client with configuration.

        Args:
            config: Client-specific configuration object
        """
        self.config = config
        self._initialized = False

    @abstractmethod
    def search(self, query: str, max_results: int = 100, **kwargs) -> List[Publication]:
        """
        Search for publications matching the query.

        Args:
            query: Search query string
            max_results: Maximum number of results to return
            **kwargs: Additional search parameters

        Returns:
            List of Publication objects

        Raises:
            NotImplementedError: Must be implemented by subclass
        """
        raise NotImplementedError

    @abstractmethod
    def fetch_by_id(self, identifier: str) -> Optional[Publication]:
        """
        Fetch a single publication by its identifier.

        Args:
            identifier: Publication identifier (PMID, DOI, etc.)

        Returns:
            Publication object if found, None otherwise

        Raises:
            NotImplementedError: Must be implemented by subclass
        """
        raise NotImplementedError

    def get_citations(self, publication: Publication) -> int:
        """
        Get citation count for a publication (if supported).

        Args:
            publication: Publication to get citations for

        Returns:
            Citation count (0 if not supported)
        """
        return 0  # Default: not supported

    def initialize(self) -> None:
        """
        Initialize client resources (connections, caches, etc.).

        Override if client needs initialization.
        """
        self._initialized = True

    def cleanup(self) -> None:
        """
        Clean up client resources.

        Override if client needs cleanup.
        """
        self._initialized = False

    def __enter__(self):
        """Context manager entry."""
        self.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()
        return False

    @property
    def is_initialized(self) -> bool:
        """Check if client is initialized."""
        return self._initialized

    @property
    @abstractmethod
    def source_name(self) -> str:
        """
        Get the name of this publication source.

        Returns:
            Source name (e.g., "pubmed", "google_scholar")
        """
        raise NotImplementedError


class PublicationClientError(Exception):
    """Base exception for publication client errors."""


class SearchError(PublicationClientError):
    """Error during publication search."""


class FetchError(PublicationClientError):
    """Error fetching publication by ID."""


class RateLimitError(PublicationClientError):
    """Rate limit exceeded."""


class APIError(PublicationClientError):
    """API error response."""
