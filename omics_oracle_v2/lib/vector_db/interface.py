"""
Abstract interface for vector databases.

Defines the contract for vector storage and similarity search.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


class VectorDB(ABC):
    """
    Abstract base class for vector databases.

    Provides vector storage and k-nearest neighbor search.
    """

    @abstractmethod
    def add_vectors(
        self,
        vectors: np.ndarray,
        ids: Optional[List[str]] = None,
        metadata: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """
        Add vectors to the database.

        Args:
            vectors: Array of shape (n_vectors, dimension)
            ids: Optional list of unique identifiers for each vector
            metadata: Optional list of metadata dicts for each vector

        Raises:
            ValueError: If vectors shape is invalid or IDs are not unique
        """

    @abstractmethod
    def search(self, query_vector: np.ndarray, k: int = 10) -> List[Tuple[str, float]]:
        """
        Find k nearest neighbors to query vector.

        Args:
            query_vector: Query vector of shape (dimension,)
            k: Number of nearest neighbors to return

        Returns:
            List of (id, distance) tuples, sorted by distance (closest first)

        Raises:
            ValueError: If query vector dimension doesn't match database
        """

    @abstractmethod
    def search_batch(self, query_vectors: np.ndarray, k: int = 10) -> List[List[Tuple[str, float]]]:
        """
        Batch search for multiple query vectors.

        Args:
            query_vectors: Array of shape (n_queries, dimension)
            k: Number of nearest neighbors per query

        Returns:
            List of results for each query (list of (id, distance) tuples)
        """

    @abstractmethod
    def get_metadata(self, id: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a vector by ID.

        Args:
            id: Vector identifier

        Returns:
            Metadata dict or None if ID not found
        """

    @abstractmethod
    def remove(self, ids: List[str]) -> int:
        """
        Remove vectors by ID.

        Args:
            ids: List of vector IDs to remove

        Returns:
            Number of vectors actually removed
        """

    @abstractmethod
    def clear(self) -> None:
        """Remove all vectors from the database."""

    @abstractmethod
    def save(self, path: str) -> None:
        """
        Save index to disk.

        Args:
            path: Directory path to save index and metadata
        """

    @abstractmethod
    def load(self, path: str) -> None:
        """
        Load index from disk.

        Args:
            path: Directory path to load index and metadata from

        Raises:
            FileNotFoundError: If index files don't exist
        """

    @abstractmethod
    def size(self) -> int:
        """
        Get number of vectors in database.

        Returns:
            Number of vectors
        """

    @abstractmethod
    def dimension(self) -> int:
        """
        Get vector dimension.

        Returns:
            Dimension of vectors in database
        """
