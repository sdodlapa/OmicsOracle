"""
FAISS-based vector database implementation.

Provides fast similarity search using Facebook's FAISS library.
"""

import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import faiss
import numpy as np

from omics_oracle_v2.lib.vector_db.interface import VectorDB


class FAISSVectorDB(VectorDB):
    """
    FAISS-based vector database.

    Uses FAISS IndexFlatL2 for exact nearest neighbor search.
    Stores metadata separately for flexibility.
    """

    def __init__(self, dimension: int):
        """
        Initialize FAISS vector database.

        Args:
            dimension: Vector dimension (must match embedding dimension)

        Raises:
            ValueError: If dimension <= 0
        """
        if dimension <= 0:
            raise ValueError(f"Dimension must be positive, got {dimension}")

        self._dimension = dimension
        self._index = faiss.IndexFlatL2(dimension)
        self._id_to_idx: Dict[str, int] = {}  # Map ID to internal index
        self._idx_to_id: Dict[int, str] = {}  # Map internal index to ID
        self._metadata: Dict[str, Dict[str, Any]] = {}  # ID -> metadata
        self._next_idx = 0  # Next available internal index

    def add_vectors(
        self,
        vectors: np.ndarray,
        ids: Optional[List[str]] = None,
        metadata: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """
        Add vectors to FAISS index.

        Args:
            vectors: Array of shape (n_vectors, dimension)
            ids: Optional list of unique IDs (auto-generated if None)
            metadata: Optional metadata for each vector

        Raises:
            ValueError: If shapes don't match or IDs aren't unique
        """
        if vectors.ndim != 2:
            raise ValueError(f"Vectors must be 2D array, got shape {vectors.shape}")

        if vectors.shape[1] != self._dimension:
            raise ValueError(
                f"Vector dimension {vectors.shape[1]} doesn't match database dimension {self._dimension}"
            )

        n_vectors = vectors.shape[0]

        # Generate IDs if not provided
        if ids is None:
            ids = [f"vec_{self._next_idx + i}" for i in range(n_vectors)]
        elif len(ids) != n_vectors:
            raise ValueError(f"Number of IDs ({len(ids)}) doesn't match number of vectors ({n_vectors})")

        # Check for duplicate IDs
        existing_ids = set(ids) & set(self._id_to_idx.keys())
        if existing_ids:
            raise ValueError(f"Duplicate IDs: {existing_ids}")

        # Ensure vectors are contiguous float32 (FAISS requirement)
        vectors = np.ascontiguousarray(vectors, dtype=np.float32)

        # Add to FAISS index
        self._index.add(vectors)

        # Update mappings
        for i, id in enumerate(ids):
            idx = self._next_idx + i
            self._id_to_idx[id] = idx
            self._idx_to_id[idx] = id

            # Store metadata if provided
            if metadata and i < len(metadata):
                self._metadata[id] = metadata[i]

        self._next_idx += n_vectors

    def search(self, query_vector: np.ndarray, k: int = 10) -> List[Tuple[str, float]]:
        """
        Find k nearest neighbors.

        Args:
            query_vector: Query vector of shape (dimension,) or (1, dimension)
            k: Number of neighbors to return

        Returns:
            List of (id, distance) tuples sorted by distance

        Raises:
            ValueError: If query dimension doesn't match or database is empty
        """
        if self.size() == 0:
            return []

        # Reshape to (1, dimension) if needed
        if query_vector.ndim == 1:
            query_vector = query_vector.reshape(1, -1)

        if query_vector.shape[1] != self._dimension:
            raise ValueError(
                f"Query dimension {query_vector.shape[1]} doesn't match database dimension {self._dimension}"
            )

        # Ensure float32 and contiguous
        query_vector = np.ascontiguousarray(query_vector, dtype=np.float32)

        # Limit k to available vectors
        k = min(k, self.size())

        # Search
        distances, indices = self._index.search(query_vector, k)

        # Convert to (id, distance) tuples
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx in self._idx_to_id:
                id = self._idx_to_id[idx]
                results.append((id, float(dist)))

        return results

    def search_batch(self, query_vectors: np.ndarray, k: int = 10) -> List[List[Tuple[str, float]]]:
        """
        Batch search for multiple queries.

        Args:
            query_vectors: Array of shape (n_queries, dimension)
            k: Number of neighbors per query

        Returns:
            List of results for each query
        """
        if self.size() == 0:
            return [[] for _ in range(query_vectors.shape[0])]

        if query_vectors.ndim != 2:
            raise ValueError(f"Query vectors must be 2D array, got shape {query_vectors.shape}")

        if query_vectors.shape[1] != self._dimension:
            raise ValueError(
                f"Query dimension {query_vectors.shape[1]} doesn't match database dimension {self._dimension}"
            )

        # Ensure float32 and contiguous
        query_vectors = np.ascontiguousarray(query_vectors, dtype=np.float32)

        # Limit k to available vectors
        k = min(k, self.size())

        # Batch search
        distances, indices = self._index.search(query_vectors, k)

        # Convert to list of (id, distance) tuples
        results = []
        for query_distances, query_indices in zip(distances, indices):
            query_results = []
            for dist, idx in zip(query_distances, query_indices):
                if idx in self._idx_to_id:
                    id = self._idx_to_id[idx]
                    query_results.append((id, float(dist)))
            results.append(query_results)

        return results

    def get_metadata(self, id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a vector."""
        return self._metadata.get(id)

    def remove(self, ids: List[str]) -> int:
        """
        Remove vectors by ID.

        Note: FAISS doesn't support efficient removal, so we mark as removed
        in mappings but don't rebuild index. Use rebuild() to compact.

        Args:
            ids: List of IDs to remove

        Returns:
            Number of vectors actually removed
        """
        removed = 0
        for id in ids:
            if id in self._id_to_idx:
                idx = self._id_to_idx[id]
                del self._id_to_idx[id]
                del self._idx_to_id[idx]
                if id in self._metadata:
                    del self._metadata[id]
                removed += 1

        return removed

    def clear(self) -> None:
        """Clear all vectors."""
        self._index.reset()
        self._id_to_idx.clear()
        self._idx_to_id.clear()
        self._metadata.clear()
        self._next_idx = 0

    def save(self, path: str) -> None:
        """
        Save index and metadata to disk.

        Args:
            path: Directory path to save to

        Creates:
            {path}/index.faiss - FAISS index
            {path}/metadata.pkl - ID mappings and metadata
        """
        path_obj = Path(path)
        path_obj.mkdir(parents=True, exist_ok=True)

        # Save FAISS index
        index_file = path_obj / "index.faiss"
        faiss.write_index(self._index, str(index_file))

        # Save metadata and mappings
        metadata_file = path_obj / "metadata.pkl"
        metadata_dict = {
            "dimension": self._dimension,
            "id_to_idx": self._id_to_idx,
            "idx_to_id": self._idx_to_id,
            "metadata": self._metadata,
            "next_idx": self._next_idx,
        }
        with open(metadata_file, "wb") as f:
            pickle.dump(metadata_dict, f)

    def load(self, path: str) -> None:
        """
        Load index and metadata from disk.

        Args:
            path: Directory path to load from

        Raises:
            FileNotFoundError: If index files don't exist
        """
        path_obj = Path(path)

        # Load FAISS index
        index_file = path_obj / "index.faiss"
        if not index_file.exists():
            raise FileNotFoundError(f"FAISS index not found: {index_file}")

        self._index = faiss.read_index(str(index_file))

        # Load metadata and mappings
        metadata_file = path_obj / "metadata.pkl"
        if not metadata_file.exists():
            raise FileNotFoundError(f"Metadata file not found: {metadata_file}")

        with open(metadata_file, "rb") as f:
            metadata_dict = pickle.load(f)

        self._dimension = metadata_dict["dimension"]
        self._id_to_idx = metadata_dict["id_to_idx"]
        self._idx_to_id = metadata_dict["idx_to_id"]
        self._metadata = metadata_dict["metadata"]
        self._next_idx = metadata_dict["next_idx"]

    def size(self) -> int:
        """Get number of vectors (accounting for removed ones)."""
        return len(self._id_to_idx)

    def dimension(self) -> int:
        """Get vector dimension."""
        return self._dimension

    def rebuild(self) -> None:
        """
        Rebuild index to remove deleted vectors.

        This is expensive but reclaims memory from removed vectors.
        """
        if self.size() == 0:
            self.clear()
            return

        # Get all valid vectors
        valid_indices = sorted(self._idx_to_id.keys())
        vectors = np.zeros((len(valid_indices), self._dimension), dtype=np.float32)

        for new_idx, old_idx in enumerate(valid_indices):
            vectors[new_idx] = self._index.reconstruct(int(old_idx))

        # Get IDs and metadata in same order
        ids = [self._idx_to_id[idx] for idx in valid_indices]
        metadata = [self._metadata.get(id) for id in ids]

        # Rebuild
        self.clear()
        self.add_vectors(vectors, ids, metadata)
