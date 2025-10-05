"""
Unit tests for FAISS vector database.

Tests vector storage, search, persistence, and metadata management.
"""

import tempfile
from pathlib import Path

import numpy as np
import pytest

from omics_oracle_v2.lib.vector_db.faiss_db import FAISSVectorDB


class TestFAISSVectorDBInit:
    """Test database initialization."""

    def test_init_valid_dimension(self):
        """Test initialization with valid dimension."""
        db = FAISSVectorDB(dimension=128)
        assert db.dimension() == 128
        assert db.size() == 0

    def test_init_invalid_dimension(self):
        """Test initialization with invalid dimension."""
        with pytest.raises(ValueError, match="Dimension must be positive"):
            FAISSVectorDB(dimension=0)

        with pytest.raises(ValueError, match="Dimension must be positive"):
            FAISSVectorDB(dimension=-1)


class TestFAISSVectorDBAddVectors:
    """Test adding vectors."""

    @pytest.fixture
    def db(self):
        """Create a test database."""
        return FAISSVectorDB(dimension=4)

    def test_add_vectors_basic(self, db):
        """Test basic vector addition."""
        vectors = np.array([[1, 2, 3, 4], [5, 6, 7, 8]], dtype=np.float32)
        ids = ["v1", "v2"]

        db.add_vectors(vectors, ids)

        assert db.size() == 2
        assert db.get_metadata("v1") is None

    def test_add_vectors_auto_ids(self, db):
        """Test auto-generated IDs."""
        vectors = np.array([[1, 2, 3, 4]], dtype=np.float32)

        db.add_vectors(vectors)

        assert db.size() == 1

    def test_add_vectors_with_metadata(self, db):
        """Test adding vectors with metadata."""
        vectors = np.array([[1, 2, 3, 4]], dtype=np.float32)
        ids = ["v1"]
        metadata = [{"type": "dataset", "name": "test"}]

        db.add_vectors(vectors, ids, metadata)

        assert db.size() == 1
        assert db.get_metadata("v1") == {"type": "dataset", "name": "test"}

    def test_add_vectors_wrong_dimension(self, db):
        """Test adding vectors with wrong dimension."""
        vectors = np.array([[1, 2, 3]], dtype=np.float32)  # Dimension 3, not 4

        with pytest.raises(ValueError, match="doesn't match database dimension"):
            db.add_vectors(vectors)

    def test_add_vectors_wrong_shape(self, db):
        """Test adding vectors with wrong shape."""
        vectors = np.array([1, 2, 3, 4], dtype=np.float32)  # 1D, not 2D

        with pytest.raises(ValueError, match="must be 2D array"):
            db.add_vectors(vectors)

    def test_add_vectors_duplicate_ids(self, db):
        """Test adding vectors with duplicate IDs."""
        vectors = np.array([[1, 2, 3, 4]], dtype=np.float32)
        db.add_vectors(vectors, ids=["v1"])

        # Try to add again with same ID
        with pytest.raises(ValueError, match="Duplicate IDs"):
            db.add_vectors(vectors, ids=["v1"])

    def test_add_vectors_id_count_mismatch(self, db):
        """Test ID count mismatch."""
        vectors = np.array([[1, 2, 3, 4], [5, 6, 7, 8]], dtype=np.float32)
        ids = ["v1"]  # Only 1 ID for 2 vectors

        with pytest.raises(ValueError, match="doesn't match number of vectors"):
            db.add_vectors(vectors, ids)


class TestFAISSVectorDBSearch:
    """Test vector search."""

    @pytest.fixture
    def db(self):
        """Create database with test vectors."""
        db = FAISSVectorDB(dimension=4)
        vectors = np.array(
            [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1], [1, 1, 0, 0]], dtype=np.float32
        )
        ids = ["v1", "v2", "v3", "v4", "v5"]
        metadata = [{"index": i} for i in range(5)]

        db.add_vectors(vectors, ids, metadata)
        return db

    def test_search_basic(self, db):
        """Test basic nearest neighbor search."""
        query = np.array([1, 0, 0, 0], dtype=np.float32)
        results = db.search(query, k=3)

        assert len(results) == 3
        # First result should be v1 (exact match)
        assert results[0][0] == "v1"
        assert results[0][1] < 0.01  # Distance near 0

    def test_search_2d_query(self, db):
        """Test search with 2D query vector."""
        query = np.array([[1, 0, 0, 0]], dtype=np.float32)
        results = db.search(query, k=2)

        assert len(results) == 2
        assert results[0][0] == "v1"

    def test_search_empty_db(self):
        """Test search on empty database."""
        db = FAISSVectorDB(dimension=4)
        query = np.array([1, 0, 0, 0], dtype=np.float32)

        results = db.search(query, k=5)

        assert results == []

    def test_search_k_larger_than_size(self, db):
        """Test search with k larger than database size."""
        query = np.array([1, 0, 0, 0], dtype=np.float32)
        results = db.search(query, k=100)

        # Should return all 5 vectors
        assert len(results) == 5

    def test_search_wrong_dimension(self, db):
        """Test search with wrong dimension."""
        query = np.array([1, 0, 0], dtype=np.float32)  # Dimension 3, not 4

        with pytest.raises(ValueError, match="doesn't match database dimension"):
            db.search(query, k=5)


class TestFAISSVectorDBSearchBatch:
    """Test batch search."""

    @pytest.fixture
    def db(self):
        """Create database with test vectors."""
        db = FAISSVectorDB(dimension=4)
        vectors = np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0]], dtype=np.float32)
        ids = ["v1", "v2", "v3"]
        db.add_vectors(vectors, ids)
        return db

    def test_search_batch_basic(self, db):
        """Test batch search."""
        queries = np.array([[1, 0, 0, 0], [0, 1, 0, 0]], dtype=np.float32)
        results = db.search_batch(queries, k=2)

        assert len(results) == 2
        # First query should match v1 best
        assert results[0][0][0] == "v1"
        # Second query should match v2 best
        assert results[1][0][0] == "v2"

    def test_search_batch_empty_db(self):
        """Test batch search on empty database."""
        db = FAISSVectorDB(dimension=4)
        queries = np.array([[1, 0, 0, 0], [0, 1, 0, 0]], dtype=np.float32)

        results = db.search_batch(queries, k=2)

        assert len(results) == 2
        assert results[0] == []
        assert results[1] == []

    def test_search_batch_wrong_dimension(self, db):
        """Test batch search with wrong dimension."""
        queries = np.array([[1, 0, 0]], dtype=np.float32)  # Dimension 3, not 4

        with pytest.raises(ValueError, match="doesn't match database dimension"):
            db.search_batch(queries, k=2)

    def test_search_batch_wrong_shape(self, db):
        """Test batch search with wrong shape."""
        queries = np.array([1, 0, 0, 0], dtype=np.float32)  # 1D, not 2D

        with pytest.raises(ValueError, match="must be 2D array"):
            db.search_batch(queries, k=2)


class TestFAISSVectorDBMetadata:
    """Test metadata operations."""

    @pytest.fixture
    def db(self):
        """Create database with metadata."""
        db = FAISSVectorDB(dimension=4)
        vectors = np.array([[1, 0, 0, 0], [0, 1, 0, 0]], dtype=np.float32)
        ids = ["v1", "v2"]
        metadata = [{"name": "first", "score": 1.0}, {"name": "second", "score": 2.0}]
        db.add_vectors(vectors, ids, metadata)
        return db

    def test_get_metadata_exists(self, db):
        """Test getting metadata for existing ID."""
        meta = db.get_metadata("v1")
        assert meta == {"name": "first", "score": 1.0}

    def test_get_metadata_not_exists(self, db):
        """Test getting metadata for non-existent ID."""
        meta = db.get_metadata("v999")
        assert meta is None

    def test_get_metadata_no_metadata(self):
        """Test getting metadata when none was stored."""
        db = FAISSVectorDB(dimension=4)
        vectors = np.array([[1, 0, 0, 0]], dtype=np.float32)
        db.add_vectors(vectors, ids=["v1"])

        meta = db.get_metadata("v1")
        assert meta is None


class TestFAISSVectorDBRemove:
    """Test vector removal."""

    @pytest.fixture
    def db(self):
        """Create database with vectors."""
        db = FAISSVectorDB(dimension=4)
        vectors = np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0]], dtype=np.float32)
        ids = ["v1", "v2", "v3"]
        metadata = [{"i": i} for i in range(3)]
        db.add_vectors(vectors, ids, metadata)
        return db

    def test_remove_single(self, db):
        """Test removing single vector."""
        removed = db.remove(["v1"])

        assert removed == 1
        assert db.size() == 2
        assert db.get_metadata("v1") is None
        assert db.get_metadata("v2") is not None

    def test_remove_multiple(self, db):
        """Test removing multiple vectors."""
        removed = db.remove(["v1", "v2"])

        assert removed == 2
        assert db.size() == 1
        assert db.get_metadata("v3") is not None

    def test_remove_non_existent(self, db):
        """Test removing non-existent ID."""
        removed = db.remove(["v999"])

        assert removed == 0
        assert db.size() == 3

    def test_remove_mixed(self, db):
        """Test removing mix of existing and non-existent IDs."""
        removed = db.remove(["v1", "v999", "v2"])

        assert removed == 2
        assert db.size() == 1


class TestFAISSVectorDBClear:
    """Test clearing database."""

    def test_clear(self):
        """Test clearing database."""
        db = FAISSVectorDB(dimension=4)
        vectors = np.array([[1, 0, 0, 0], [0, 1, 0, 0]], dtype=np.float32)
        db.add_vectors(vectors, ids=["v1", "v2"])

        assert db.size() == 2

        db.clear()

        assert db.size() == 0
        assert db.get_metadata("v1") is None


class TestFAISSVectorDBPersistence:
    """Test save and load."""

    @pytest.fixture
    def db(self):
        """Create database with vectors."""
        db = FAISSVectorDB(dimension=4)
        vectors = np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0]], dtype=np.float32)
        ids = ["v1", "v2", "v3"]
        metadata = [{"name": f"vec{i}"} for i in range(3)]
        db.add_vectors(vectors, ids, metadata)
        return db

    def test_save_and_load(self, db):
        """Test saving and loading database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Save
            db.save(tmpdir)

            # Create new database and load
            db2 = FAISSVectorDB(dimension=4)
            db2.load(tmpdir)

            # Verify
            assert db2.size() == 3
            assert db2.dimension() == 4
            assert db2.get_metadata("v1") == {"name": "vec0"}
            assert db2.get_metadata("v2") == {"name": "vec1"}

            # Verify search works
            query = np.array([1, 0, 0, 0], dtype=np.float32)
            results = db2.search(query, k=1)
            assert results[0][0] == "v1"

    def test_save_creates_directory(self, db):
        """Test that save creates directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "nested" / "path"
            db.save(str(path))

            assert path.exists()
            assert (path / "index.faiss").exists()
            assert (path / "metadata.pkl").exists()

    def test_load_missing_index(self):
        """Test loading from non-existent path."""
        db = FAISSVectorDB(dimension=4)

        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(FileNotFoundError, match="FAISS index not found"):
                db.load(tmpdir)

    def test_load_missing_metadata(self):
        """Test loading with missing metadata file."""
        db = FAISSVectorDB(dimension=4)
        vectors = np.array([[1, 0, 0, 0]], dtype=np.float32)
        db.add_vectors(vectors)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Save index file only
            import faiss

            index_file = Path(tmpdir) / "index.faiss"
            faiss.write_index(db._index, str(index_file))

            # Try to load (should fail on missing metadata)
            db2 = FAISSVectorDB(dimension=4)
            with pytest.raises(FileNotFoundError, match="Metadata file not found"):
                db2.load(tmpdir)


class TestFAISSVectorDBRebuild:
    """Test index rebuilding."""

    def test_rebuild_after_removal(self):
        """Test rebuilding index after removals."""
        db = FAISSVectorDB(dimension=4)
        vectors = np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0]], dtype=np.float32)
        ids = ["v1", "v2", "v3"]
        metadata = [{"i": i} for i in range(3)]
        db.add_vectors(vectors, ids, metadata)

        # Remove middle vector
        db.remove(["v2"])

        # Rebuild
        db.rebuild()

        # Verify
        assert db.size() == 2
        assert db.get_metadata("v1") is not None
        assert db.get_metadata("v2") is None
        assert db.get_metadata("v3") is not None

        # Search should still work
        query = np.array([1, 0, 0, 0], dtype=np.float32)
        results = db.search(query, k=2)
        assert len(results) == 2

    def test_rebuild_empty(self):
        """Test rebuilding empty database."""
        db = FAISSVectorDB(dimension=4)
        db.rebuild()

        assert db.size() == 0
