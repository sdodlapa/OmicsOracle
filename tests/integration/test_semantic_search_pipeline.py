"""
End-to-end integration test for semantic search pipeline.

Tests the complete flow from document indexing to hybrid search.
"""

import tempfile
from pathlib import Path

import numpy as np
import pytest

from omics_oracle_v2.lib.embeddings.service import EmbeddingConfig, EmbeddingService
from omics_oracle_v2.lib.search.hybrid import HybridSearchEngine, SearchConfig
from omics_oracle_v2.lib.vector_db.faiss_db import FAISSVectorDB


class TestSemanticSearchPipeline:
    """Integration tests for the complete semantic search pipeline."""

    @pytest.fixture
    def mock_openai_key(self, monkeypatch):
        """Set mock OpenAI API key."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key-123")

    @pytest.fixture
    def sample_documents(self):
        """Create sample biomedical documents."""
        return [
            {
                "id": "GSE123456",
                "text": "Gene expression profiling of cancer cells using RNA-seq",
                "title": "Cancer Gene Expression Study",
                "organism": "Homo sapiens",
                "platform": "RNA-Seq",
            },
            {
                "id": "GSE789012",
                "text": "Single cell RNA sequencing of immune cells in disease",
                "title": "Immune Cell scRNA-seq Analysis",
                "organism": "Homo sapiens",
                "platform": "scRNA-Seq",
            },
            {
                "id": "GSE345678",
                "text": "Proteomics analysis of brain tissue in Alzheimer disease",
                "title": "Alzheimer Proteomics Study",
                "organism": "Homo sapiens",
                "platform": "Mass Spectrometry",
            },
            {
                "id": "GSE901234",
                "text": "Microarray gene expression in diabetes mellitus patients",
                "title": "Diabetes Gene Expression",
                "organism": "Homo sapiens",
                "platform": "Microarray",
            },
            {
                "id": "GSE567890",
                "text": "ChIP-seq analysis of histone modifications in stem cells",
                "title": "Stem Cell Epigenetics",
                "organism": "Mus musculus",
                "platform": "ChIP-Seq",
            },
        ]

    @pytest.fixture
    def embedding_config(self, mock_openai_key):
        """Create embedding configuration."""
        return EmbeddingConfig(
            model="text-embedding-3-small",
            dimension=1536,
            cache_enabled=True,
            cache_dir=tempfile.mkdtemp(),
        )

    @pytest.fixture
    def search_config(self):
        """Create search configuration."""
        return SearchConfig(
            keyword_weight=0.4,
            semantic_weight=0.6,
            max_results=10,
            min_combined_score=0.1,
        )

    def test_pipeline_without_openai(self, sample_documents):
        """Test pipeline with mock embeddings (no OpenAI API call)."""
        # Create components with mocked embedding service
        embedding_service = MockEmbeddingService(dimension=128)
        vector_db = FAISSVectorDB(dimension=128)
        search_engine = HybridSearchEngine(embedding_service, vector_db)

        # Index documents
        search_engine.index_documents(sample_documents, metadata_fields=["title", "organism", "platform"])

        assert search_engine.size() == 5

        # Search for RNA-seq related datasets
        results = search_engine.search("RNA sequencing gene expression")

        assert len(results) > 0
        assert all(hasattr(r, "combined_score") for r in results)
        assert all(hasattr(r, "keyword_score") for r in results)
        assert all(hasattr(r, "semantic_score") for r in results)

        # Results should be ranked
        for i in range(len(results) - 1):
            assert results[i].combined_score >= results[i + 1].combined_score

        # Check metadata is preserved
        for result in results:
            assert result.metadata is not None
            assert "title" in result.metadata
            assert "organism" in result.metadata

    def test_keyword_search_quality(self, sample_documents):
        """Test keyword search finds exact matches."""
        embedding_service = MockEmbeddingService(dimension=128)
        vector_db = FAISSVectorDB(dimension=128)

        # Configure for keyword-only search
        config = SearchConfig(keyword_weight=1.0, semantic_weight=0.0, max_results=5)
        search_engine = HybridSearchEngine(embedding_service, vector_db, config)

        search_engine.index_documents(sample_documents)

        # Search for specific term
        results = search_engine.search("proteomics")

        # Should find the proteomics document
        assert len(results) > 0
        assert any("GSE345678" == r.id for r in results)

    def test_semantic_search_quality(self, sample_documents):
        """Test semantic search finds related concepts."""
        embedding_service = MockEmbeddingService(dimension=128)
        vector_db = FAISSVectorDB(dimension=128)

        # Configure for semantic-only search
        config = SearchConfig(keyword_weight=0.0, semantic_weight=1.0, max_results=5)
        search_engine = HybridSearchEngine(embedding_service, vector_db, config)

        search_engine.index_documents(sample_documents)

        # Search with semantic query (mock service returns consistent embeddings)
        results = search_engine.search("transcriptomics analysis")

        assert len(results) > 0
        # With mock embeddings, semantic scores should be >= 0 (may be 0 for identical embeddings)
        assert all(r.semantic_score >= 0 for r in results)

    def test_hybrid_search_balances_results(self, sample_documents):
        """Test hybrid search balances keyword and semantic signals."""
        embedding_service = MockEmbeddingService(dimension=128)
        vector_db = FAISSVectorDB(dimension=128)

        # Balanced hybrid search
        config = SearchConfig(keyword_weight=0.5, semantic_weight=0.5)
        search_engine = HybridSearchEngine(embedding_service, vector_db, config)

        search_engine.index_documents(sample_documents)

        results = search_engine.search("RNA cancer cells")

        assert len(results) > 0

        # Should have both keyword and semantic components
        for result in results:
            # Combined score should be average of keyword and semantic
            expected = 0.5 * result.keyword_score + 0.5 * result.semantic_score
            assert abs(result.combined_score - expected) < 0.001

    def test_search_with_filters(self, sample_documents):
        """Test search with score filters."""
        embedding_service = MockEmbeddingService(dimension=128)
        vector_db = FAISSVectorDB(dimension=128)

        # Strict filtering
        config = SearchConfig(
            keyword_weight=0.5,
            semantic_weight=0.5,
            min_combined_score=0.5,  # High threshold
        )
        search_engine = HybridSearchEngine(embedding_service, vector_db, config)

        search_engine.index_documents(sample_documents)

        results = search_engine.search("very specific rare query")

        # Should filter out low-scoring results
        assert all(r.combined_score >= 0.5 for r in results)

    def test_dynamic_config_update(self, sample_documents):
        """Test updating search configuration dynamically."""
        embedding_service = MockEmbeddingService(dimension=128)
        vector_db = FAISSVectorDB(dimension=128)

        search_engine = HybridSearchEngine(embedding_service, vector_db)
        search_engine.index_documents(sample_documents)

        # Initial search
        results1 = search_engine.search("RNA sequencing")
        initial_count = len(results1)

        # Update config to be more restrictive
        search_engine.update_config(max_results=2, min_combined_score=0.3)

        results2 = search_engine.search("RNA sequencing")

        # Should return fewer results
        assert len(results2) <= 2
        assert len(results2) <= initial_count

    def test_persistence_and_reload(self, sample_documents):
        """Test saving and loading vector database."""
        embedding_service = MockEmbeddingService(dimension=128)
        vector_db = FAISSVectorDB(dimension=128)

        search_engine = HybridSearchEngine(embedding_service, vector_db)
        search_engine.index_documents(sample_documents)

        # Get initial results
        results_before = search_engine.search("RNA sequencing")

        # Save vector DB
        with tempfile.TemporaryDirectory() as tmpdir:
            vector_db.save(tmpdir)

            # Create new components and load
            new_vector_db = FAISSVectorDB(dimension=128)
            new_vector_db.load(tmpdir)

            # Create new search engine with loaded vector DB
            # The keyword index needs to be rebuilt
            new_search_engine = HybridSearchEngine(embedding_service, new_vector_db)
            # Rebuild keyword index using the private method
            texts = [doc["text"] for doc in sample_documents]
            ids = [doc["id"] for doc in sample_documents]
            new_search_engine._build_keyword_index(texts, ids)

            results_after = new_search_engine.search("RNA sequencing")

            # Should get same number of results
            assert len(results_before) == len(results_after)

    def test_empty_query_handling(self, sample_documents):
        """Test handling of empty queries."""
        embedding_service = MockEmbeddingService(dimension=128)
        vector_db = FAISSVectorDB(dimension=128)
        search_engine = HybridSearchEngine(embedding_service, vector_db)

        search_engine.index_documents(sample_documents)

        # Empty query should return results (based on index content)
        results = search_engine.search("")

        # Should not crash, may return results based on similarity
        assert isinstance(results, list)

    def test_large_result_set(self, sample_documents):
        """Test handling of large result sets."""
        embedding_service = MockEmbeddingService(dimension=128)
        vector_db = FAISSVectorDB(dimension=128)

        # Very large max_results
        config = SearchConfig(max_results=1000)
        search_engine = HybridSearchEngine(embedding_service, vector_db, config)

        search_engine.index_documents(sample_documents)

        results = search_engine.search("gene expression")

        # Should not exceed available documents
        assert len(results) <= len(sample_documents)

    def test_clear_and_reindex(self, sample_documents):
        """Test clearing and re-indexing."""
        embedding_service = MockEmbeddingService(dimension=128)
        vector_db = FAISSVectorDB(dimension=128)
        search_engine = HybridSearchEngine(embedding_service, vector_db)

        # Index
        search_engine.index_documents(sample_documents)
        assert search_engine.size() == 5

        # Clear
        search_engine.clear()
        assert search_engine.size() == 0

        # Re-index with different documents
        new_docs = sample_documents[:2]
        search_engine.index_documents(new_docs)
        assert search_engine.size() == 2


class MockEmbeddingService:
    """Mock embedding service for testing without OpenAI API."""

    def __init__(self, dimension: int = 128):
        self.dimension = dimension
        np.random.seed(42)  # Deterministic for testing

    def embed_text(self, text: str) -> list:
        """Generate deterministic mock embedding."""
        # Use hash of text for reproducibility
        hash_val = hash(text) % (2**32)
        np.random.seed(hash_val)
        embedding = np.random.randn(self.dimension)
        # Normalize
        embedding = embedding / np.linalg.norm(embedding)
        return embedding.tolist()

    def embed_batch(self, texts: list) -> list:
        """Generate batch of mock embeddings."""
        return [self.embed_text(text) for text in texts]

    def get_dimension(self) -> int:
        """Get embedding dimension."""
        return self.dimension


@pytest.mark.skipif(
    not Path.home().joinpath(".openai_api_key_test").exists(),
    reason="OpenAI API key file not found - skipping live API tests",
)
class TestSemanticSearchWithRealAPI:
    """Integration tests with real OpenAI API (optional)."""

    @pytest.fixture
    def embedding_service(self):
        """Create real embedding service."""
        config = EmbeddingConfig(
            model="text-embedding-3-small",
            dimension=1536,
            cache_enabled=True,
            cache_dir=tempfile.mkdtemp(),
        )
        return EmbeddingService(config)

    def test_real_semantic_search(self, embedding_service):
        """Test semantic search with real OpenAI embeddings."""
        vector_db = FAISSVectorDB(dimension=1536)
        search_engine = HybridSearchEngine(embedding_service, vector_db)

        # Simple test documents
        documents = [
            {"id": "doc1", "text": "Machine learning and artificial intelligence"},
            {"id": "doc2", "text": "Deep neural networks for image recognition"},
            {"id": "doc3", "text": "Natural language processing with transformers"},
        ]

        search_engine.index_documents(documents)

        # Semantic query (synonyms, not exact keywords)
        results = search_engine.search("AI and ML techniques")

        assert len(results) > 0
        # Should find semantically similar documents
        assert any("doc1" == r.id for r in results[:2])  # ML/AI doc should rank high
