"""
Unit tests for hybrid search engine.

Tests search configuration, indexing, and result fusion.
"""

from unittest.mock import MagicMock

import numpy as np
import pytest

from omics_oracle_v2.lib.search.hybrid import HybridSearchEngine, SearchConfig, SearchResult


class TestSearchConfig:
    """Test search configuration."""

    def test_default_config(self):
        """Test default configuration values."""
        config = SearchConfig()
        assert config.keyword_weight == 0.4
        assert config.semantic_weight == 0.6
        assert config.max_results == 100
        assert config.keyword_k == 50
        assert config.semantic_k == 50

    def test_custom_config(self):
        """Test custom configuration."""
        config = SearchConfig(
            keyword_weight=0.7,
            semantic_weight=0.3,
            max_results=20,
            min_combined_score=0.5,
        )
        assert config.keyword_weight == 0.7
        assert config.semantic_weight == 0.3
        assert config.max_results == 20
        assert config.min_combined_score == 0.5

    def test_weights_must_sum_to_one(self):
        """Test that weights must sum to 1.0."""
        with pytest.raises(ValueError, match="must equal 1.0"):
            SearchConfig(keyword_weight=0.5, semantic_weight=0.6)

    def test_negative_weight(self):
        """Test that negative weights are rejected."""
        with pytest.raises(ValueError, match="must be non-negative"):
            SearchConfig(keyword_weight=-0.1, semantic_weight=1.1)

    def test_zero_max_results(self):
        """Test that max_results must be positive."""
        with pytest.raises(ValueError, match="must be positive"):
            SearchConfig(max_results=0)

    def test_zero_k_values(self):
        """Test that k values must be positive."""
        with pytest.raises(ValueError, match="must be positive"):
            SearchConfig(keyword_k=0)

        with pytest.raises(ValueError, match="must be positive"):
            SearchConfig(semantic_k=0)


class TestSearchResult:
    """Test search result."""

    def test_create_result(self):
        """Test creating search result."""
        result = SearchResult(
            id="doc1",
            keyword_score=0.8,
            semantic_score=0.6,
            combined_score=0.7,
            metadata={"title": "Test"},
        )
        assert result.id == "doc1"
        assert result.keyword_score == 0.8
        assert result.semantic_score == 0.6
        assert result.combined_score == 0.7
        assert result.metadata == {"title": "Test"}

    def test_result_comparison(self):
        """Test result comparison (for sorting)."""
        result1 = SearchResult(id="doc1", combined_score=0.8)
        result2 = SearchResult(id="doc2", combined_score=0.6)

        # Higher score should be "less than" for sorting in descending order
        assert result1 < result2
        assert not result2 < result1


class TestHybridSearchEngineInit:
    """Test hybrid search engine initialization."""

    @pytest.fixture
    def mock_embedding_service(self):
        """Create mock embedding service."""
        service = MagicMock()
        service.embed_text.return_value = np.random.rand(128).tolist()
        service.embed_batch.return_value = [np.random.rand(128).tolist() for _ in range(3)]
        return service

    @pytest.fixture
    def mock_vector_db(self):
        """Create mock vector database."""
        db = MagicMock()
        db.size.return_value = 0
        db.search.return_value = []
        return db

    def test_init_default_config(self, mock_embedding_service, mock_vector_db):
        """Test initialization with default config."""
        engine = HybridSearchEngine(mock_embedding_service, mock_vector_db)
        assert engine.config.keyword_weight == 0.4
        assert engine.config.semantic_weight == 0.6

    def test_init_custom_config(self, mock_embedding_service, mock_vector_db):
        """Test initialization with custom config."""
        config = SearchConfig(keyword_weight=0.7, semantic_weight=0.3)
        engine = HybridSearchEngine(mock_embedding_service, mock_vector_db, config)
        assert engine.config.keyword_weight == 0.7


class TestHybridSearchEngineIndexing:
    """Test document indexing."""

    @pytest.fixture
    def mock_embedding_service(self):
        """Create mock embedding service."""
        service = MagicMock()
        service.embed_batch.return_value = [
            np.random.rand(128).tolist(),
            np.random.rand(128).tolist(),
            np.random.rand(128).tolist(),
        ]
        return service

    @pytest.fixture
    def mock_vector_db(self):
        """Create mock vector database."""
        db = MagicMock()
        db.size.return_value = 0
        return db

    @pytest.fixture
    def engine(self, mock_embedding_service, mock_vector_db):
        """Create search engine."""
        return HybridSearchEngine(mock_embedding_service, mock_vector_db)

    def test_index_documents(self, engine, mock_embedding_service, mock_vector_db):
        """Test basic document indexing."""
        documents = [
            {"id": "doc1", "text": "machine learning", "title": "ML Doc"},
            {"id": "doc2", "text": "deep learning neural networks", "title": "DL Doc"},
            {"id": "doc3", "text": "data science", "title": "DS Doc"},
        ]

        engine.index_documents(documents)

        # Should generate embeddings for all documents
        assert mock_embedding_service.embed_batch.called
        call_args = mock_embedding_service.embed_batch.call_args[0][0]
        assert len(call_args) == 3

        # Should add vectors to DB
        assert mock_vector_db.add_vectors.called

        # Should build keyword index
        assert len(engine._keyword_index) > 0
        assert engine.size() == 3

    def test_index_empty_documents(self, engine):
        """Test indexing empty list."""
        engine.index_documents([])
        assert engine.size() == 0

    def test_index_missing_text_field(self, engine):
        """Test error when text field is missing."""
        documents = [{"id": "doc1", "title": "Test"}]

        with pytest.raises(ValueError, match="missing 'text' field"):
            engine.index_documents(documents)

    def test_index_missing_id_field(self, engine):
        """Test error when ID field is missing."""
        documents = [{"text": "test content"}]

        with pytest.raises(ValueError, match="missing 'id' field"):
            engine.index_documents(documents)

    def test_index_custom_fields(self, engine, mock_embedding_service, mock_vector_db):
        """Test indexing with custom field names."""
        documents = [
            {"doc_id": "d1", "content": "test", "meta": "data"},
        ]

        engine.index_documents(documents, text_field="content", id_field="doc_id")

        # Should use custom fields
        call_args = mock_embedding_service.embed_batch.call_args[0][0]
        assert call_args == ["test"]

    def test_index_metadata_extraction(self, engine, mock_embedding_service, mock_vector_db):
        """Test metadata extraction."""
        documents = [
            {"id": "doc1", "text": "test", "title": "Test Doc", "author": "Alice"},
        ]

        engine.index_documents(documents, metadata_fields=["title", "author"])

        # Check metadata was passed to vector DB
        _, kwargs = mock_vector_db.add_vectors.call_args
        metadata = kwargs["metadata"]
        assert len(metadata) == 1
        assert metadata[0]["title"] == "Test Doc"
        assert metadata[0]["author"] == "Alice"


class TestHybridSearchEngineSearch:
    """Test search functionality."""

    @pytest.fixture
    def mock_embedding_service(self):
        """Create mock embedding service."""
        service = MagicMock()
        # Return consistent embeddings for testing
        service.embed_text.return_value = np.zeros(128).tolist()
        service.embed_batch.return_value = [
            np.ones(128).tolist(),
            np.ones(128).tolist(),
        ]
        return service

    @pytest.fixture
    def mock_vector_db(self):
        """Create mock vector database."""
        db = MagicMock()
        db.size.return_value = 2
        db.search.return_value = [
            ("doc1", 0.1),  # Low distance = high similarity
            ("doc2", 1.0),
        ]
        db.get_metadata.return_value = {"title": "Test"}
        return db

    @pytest.fixture
    def engine(self, mock_embedding_service, mock_vector_db):
        """Create search engine with indexed documents."""
        engine = HybridSearchEngine(mock_embedding_service, mock_vector_db)

        # Index some documents
        documents = [
            {"id": "doc1", "text": "machine learning algorithms"},
            {"id": "doc2", "text": "deep neural networks"},
        ]
        engine.index_documents(documents)

        return engine

    def test_search_basic(self, engine):
        """Test basic search."""
        results = engine.search("machine learning")

        assert len(results) > 0
        assert all(isinstance(r, SearchResult) for r in results)
        # Results should have combined scores (can be 0 if no match)
        assert all(r.combined_score >= 0 for r in results)

    def test_search_result_ordering(self, engine):
        """Test that results are ordered by combined score."""
        results = engine.search("machine learning")

        # Results should be in descending order of combined score
        for i in range(len(results) - 1):
            assert results[i].combined_score >= results[i + 1].combined_score

    def test_search_result_ranks(self, engine):
        """Test that results have sequential ranks."""
        results = engine.search("machine learning")

        for i, result in enumerate(results, 1):
            assert result.rank == i

    def test_search_max_results(self, mock_embedding_service, mock_vector_db):
        """Test max_results limit."""
        config = SearchConfig(max_results=1)
        engine = HybridSearchEngine(mock_embedding_service, mock_vector_db, config)

        # Index documents
        documents = [{"id": f"doc{i}", "text": f"document {i}"} for i in range(10)]
        engine.index_documents(documents)

        results = engine.search("document")
        assert len(results) <= 1

    def test_search_empty_index(self, mock_embedding_service):
        """Test search on empty index."""
        db = MagicMock()
        db.size.return_value = 0
        db.search.return_value = []

        engine = HybridSearchEngine(mock_embedding_service, db)
        results = engine.search("test")

        # Should return empty results, not error
        assert results == []

    def test_search_keyword_only(self, engine):
        """Test search with keyword matches only."""
        # Configure for keyword-only search
        engine.update_config(keyword_weight=1.0, semantic_weight=0.0)

        results = engine.search("machine")

        # Should find keyword matches
        assert len(results) > 0
        # doc1 has "machine" in it
        assert any(r.id == "doc1" for r in results)

    def test_search_semantic_only(self, engine, mock_vector_db):
        """Test search with semantic matches only."""
        # Configure for semantic-only search
        engine.update_config(keyword_weight=0.0, semantic_weight=1.0)

        # Mock vector DB to return specific results
        mock_vector_db.search.return_value = [("doc2", 0.5)]

        results = engine.search("neural")

        # Should find semantic matches
        assert len(results) > 0


class TestHybridSearchEngineScoring:
    """Test score normalization and combination."""

    @pytest.fixture
    def engine(self):
        """Create basic engine for testing."""
        service = MagicMock()
        db = MagicMock()
        db.size.return_value = 0
        return HybridSearchEngine(service, db)

    def test_normalize_scores_basic(self, engine):
        """Test basic score normalization."""
        scores = {"doc1": 10.0, "doc2": 5.0, "doc3": 0.0}
        normalized = engine._normalize_scores(scores)

        # Should be in [0, 1] range
        assert all(0.0 <= v <= 1.0 for v in normalized.values())
        # Min should be 0, max should be 1
        assert min(normalized.values()) == 0.0
        assert max(normalized.values()) == 1.0

    def test_normalize_scores_empty(self, engine):
        """Test normalizing empty scores."""
        normalized = engine._normalize_scores({})
        assert normalized == {}

    def test_normalize_scores_all_same(self, engine):
        """Test normalizing when all scores are the same."""
        scores = {"doc1": 5.0, "doc2": 5.0, "doc3": 5.0}
        normalized = engine._normalize_scores(scores)

        # All should be 1.0
        assert all(v == 1.0 for v in normalized.values())

    def test_combine_results(self, engine):
        """Test combining keyword and semantic results."""
        engine.config = SearchConfig(keyword_weight=0.6, semantic_weight=0.4)

        keyword_scores = {"doc1": 1.0, "doc2": 0.5}
        semantic_scores = {"doc1": 0.8, "doc3": 1.0}

        results = engine._combine_results(keyword_scores, semantic_scores)

        # Should have all unique docs
        result_ids = {r.id for r in results}
        assert result_ids == {"doc1", "doc2", "doc3"}

        # doc1 appears in both, should have highest combined score
        doc1_result = next(r for r in results if r.id == "doc1")
        assert doc1_result.keyword_score == 1.0
        assert doc1_result.semantic_score == 0.8
        assert doc1_result.combined_score == 0.6 * 1.0 + 0.4 * 0.8


class TestHybridSearchEngineFiltering:
    """Test result filtering."""

    @pytest.fixture
    def engine(self):
        """Create engine with filtering config."""
        service = MagicMock()
        db = MagicMock()
        db.size.return_value = 0
        config = SearchConfig(
            min_keyword_score=0.3,
            min_semantic_score=0.2,
            min_combined_score=0.5,
        )
        return HybridSearchEngine(service, db, config)

    def test_filter_by_combined_score(self, engine):
        """Test filtering by minimum combined score."""
        results = [
            SearchResult(id="doc1", combined_score=0.8),
            SearchResult(id="doc2", combined_score=0.4),  # Below threshold
            SearchResult(id="doc3", combined_score=0.6),
        ]

        filtered = engine._filter_results(results)

        assert len(filtered) == 2
        assert all(r.combined_score >= 0.5 for r in filtered)


class TestHybridSearchEngineManagement:
    """Test engine management methods."""

    @pytest.fixture
    def engine(self):
        """Create basic engine."""
        service = MagicMock()
        service.embed_batch.return_value = [np.ones(128).tolist()]
        db = MagicMock()
        db.size.return_value = 0
        return HybridSearchEngine(service, db)

    def test_clear(self, engine):
        """Test clearing indexed data."""
        # Index a document
        documents = [{"id": "doc1", "text": "test"}]
        engine.index_documents(documents)

        assert engine.size() > 0

        # Clear
        engine.clear()

        assert engine.size() == 0
        assert len(engine._keyword_index) == 0

    def test_size(self, engine):
        """Test size tracking."""
        assert engine.size() == 0

        documents = [
            {"id": "doc1", "text": "test1"},
            {"id": "doc2", "text": "test2"},
        ]
        engine.index_documents(documents)

        assert engine.size() == 2

    def test_get_config(self, engine):
        """Test getting configuration."""
        config = engine.get_config()
        assert isinstance(config, SearchConfig)
        assert config.keyword_weight == 0.4

    def test_update_config(self, engine):
        """Test updating configuration."""
        engine.update_config(keyword_weight=0.7, semantic_weight=0.3, max_results=50)

        assert engine.config.keyword_weight == 0.7
        assert engine.config.semantic_weight == 0.3
        assert engine.config.max_results == 50

    def test_update_config_validation(self, engine):
        """Test that config update validates values."""
        with pytest.raises(ValueError):
            engine.update_config(keyword_weight=0.6, semantic_weight=0.6)  # Don't sum to 1
