"""
Tests for Cross-Encoder Reranker

Tests cross-encoder reranking functionality.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from omics_oracle_v2.lib.ranking.cross_encoder import CrossEncoderReranker, RerankedResult, RerankingConfig


class TestRerankingConfig:
    """Test RerankingConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        config = RerankingConfig()

        assert config.enabled is True
        assert "ms-marco" in config.model
        assert config.batch_size == 32
        assert config.top_k == 20
        assert config.cache_enabled is True
        assert config.device == "cpu"

    def test_custom_config(self):
        """Test custom configuration."""
        config = RerankingConfig(
            enabled=False,
            model="custom-model",
            batch_size=16,
            top_k=10,
            cache_enabled=False,
        )

        assert config.enabled is False
        assert config.model == "custom-model"
        assert config.batch_size == 16
        assert config.top_k == 10
        assert config.cache_enabled is False


class TestRerankedResult:
    """Test RerankedResult dataclass."""

    def test_reranked_result_creation(self):
        """Test creating RerankedResult."""
        result = RerankedResult(
            id="test123",
            text="Test document",
            metadata={"title": "Test"},
            original_score=0.8,
            rerank_score=0.9,
            combined_score=0.85,
            rank=1,
        )

        assert result.id == "test123"
        assert result.text == "Test document"
        assert result.metadata["title"] == "Test"
        assert result.original_score == 0.8
        assert result.rerank_score == 0.9
        assert result.combined_score == 0.85
        assert result.rank == 1


class TestCrossEncoderReranker:
    """Test CrossEncoderReranker class."""

    @pytest.fixture
    def mock_model(self):
        """Mock CrossEncoder model."""
        with patch("omics_oracle_v2.lib.ranking.cross_encoder.CrossEncoder") as mock:
            model = MagicMock()
            # Return predictable scores
            model.predict.return_value = np.array([0.9, 0.7, 0.8, 0.6, 0.5])
            mock.return_value = model
            yield mock

    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def config(self, temp_cache_dir):
        """Create test configuration."""
        return RerankingConfig(cache_dir=temp_cache_dir, batch_size=32, top_k=5)

    @pytest.fixture
    def sample_results(self):
        """Sample search results for testing."""
        return [
            {
                "id": "doc1",
                "text": "ATAC-seq chromatin accessibility",
                "score": 0.8,
                "metadata": {"title": "Study 1"},
            },
            {
                "id": "doc2",
                "text": "RNA-seq gene expression",
                "score": 0.75,
                "metadata": {"title": "Study 2"},
            },
            {
                "id": "doc3",
                "text": "ChIP-seq histone modification",
                "score": 0.7,
                "metadata": {"title": "Study 3"},
            },
            {
                "id": "doc4",
                "text": "DNase-seq open chromatin",
                "score": 0.65,
                "metadata": {"title": "Study 4"},
            },
            {
                "id": "doc5",
                "text": "Whole genome sequencing",
                "score": 0.6,
                "metadata": {"title": "Study 5"},
            },
        ]

    def test_initialization(self, config, mock_model):
        """Test reranker initialization."""
        reranker = CrossEncoderReranker(config)

        assert reranker.config.enabled is True
        assert reranker.config.top_k == 5

    def test_disabled_reranking(self, temp_cache_dir, sample_results):
        """Test that disabled reranking returns original results."""
        config = RerankingConfig(enabled=False, cache_dir=temp_cache_dir)
        reranker = CrossEncoderReranker(config)

        query = "test query"
        reranked = reranker.rerank(query, sample_results)

        # Should return same order and scores
        assert len(reranked) == len(sample_results)
        assert reranked[0].id == sample_results[0]["id"]
        assert reranked[0].original_score == sample_results[0]["score"]
        assert reranked[0].rank == 1

    def test_rerank_basic(self, config, mock_model, sample_results):
        """Test basic reranking functionality."""
        reranker = CrossEncoderReranker(config)

        query = "chromatin accessibility"
        reranked = reranker.rerank(query, sample_results)

        # Should return results
        assert len(reranked) > 0
        assert len(reranked) <= config.top_k

        # Results should have all fields
        first = reranked[0]
        assert hasattr(first, "id")
        assert hasattr(first, "text")
        assert hasattr(first, "original_score")
        assert hasattr(first, "rerank_score")
        assert hasattr(first, "combined_score")
        assert hasattr(first, "rank")

    def test_rerank_empty_results(self, config, mock_model):
        """Test reranking with empty results."""
        reranker = CrossEncoderReranker(config)

        query = "test query"
        reranked = reranker.rerank(query, [])

        assert len(reranked) == 0

    def test_top_k_limit(self, config, mock_model, sample_results):
        """Test that top_k limits results."""
        reranker = CrossEncoderReranker(config)

        query = "test query"
        reranked = reranker.rerank(query, sample_results, top_k=3)

        assert len(reranked) == 3

    def test_alpha_weighting(self, config, mock_model, sample_results):
        """Test alpha parameter for score weighting."""
        # Disable caching for this test to ensure different alphas give different results
        config.cache_enabled = False
        reranker = CrossEncoderReranker(config)

        query = "test query"

        # Test with different alpha values
        reranked_high_alpha = reranker.rerank(query, sample_results, alpha=0.9)
        reranked_low_alpha = reranker.rerank(query, sample_results, alpha=0.1)

        # Scores should be different (higher alpha = more weight on rerank score)
        # Since original and rerank scores differ, combined scores should differ
        assert abs(reranked_high_alpha[0].combined_score - reranked_low_alpha[0].combined_score) > 0.01

    def test_score_normalization(self, config, mock_model):
        """Test that rerank scores are normalized to 0-1."""
        reranker = CrossEncoderReranker(config)

        # Test with various raw scores
        test_scores = [-10, -5, 0, 5, 10]

        for score in test_scores:
            normalized = reranker._normalize_score(score)
            assert 0 <= normalized <= 1

    def test_ranking_order(self, config, mock_model, sample_results):
        """Test that results are properly ranked."""
        reranker = CrossEncoderReranker(config)

        query = "test query"
        reranked = reranker.rerank(query, sample_results)

        # Ranks should be sequential starting from 1
        for i, result in enumerate(reranked):
            assert result.rank == i + 1

        # Scores should be in descending order
        for i in range(len(reranked) - 1):
            assert reranked[i].combined_score >= reranked[i + 1].combined_score

    def test_cache_functionality(self, config, mock_model, sample_results, temp_cache_dir):
        """Test result caching."""
        reranker = CrossEncoderReranker(config)

        query = "test query"

        # First call - should compute
        reranked1 = reranker.rerank(query, sample_results)

        # Second call - should use cache
        reranked2 = reranker.rerank(query, sample_results)

        # Results should be identical
        assert len(reranked1) == len(reranked2)
        assert reranked1[0].id == reranked2[0].id
        assert reranked1[0].combined_score == reranked2[0].combined_score

        # Cache file should exist
        cache_file = Path(temp_cache_dir) / "rerank_cache.json"
        assert cache_file.exists()

    def test_cache_disabled(self, temp_cache_dir, mock_model, sample_results):
        """Test reranking with cache disabled."""
        config = RerankingConfig(cache_enabled=False, cache_dir=temp_cache_dir)
        reranker = CrossEncoderReranker(config)

        query = "test query"
        reranker.rerank(query, sample_results)

        # Cache file should not exist
        cache_file = Path(temp_cache_dir) / "rerank_cache.json"
        assert not cache_file.exists()

    def test_clear_cache(self, config, mock_model, sample_results):
        """Test cache clearing."""
        reranker = CrossEncoderReranker(config)

        query = "test query"
        reranker.rerank(query, sample_results)

        # Cache should have entries
        assert len(reranker._cache) > 0

        # Clear cache
        reranker.clear_cache()

        # Cache should be empty
        assert len(reranker._cache) == 0

    def test_get_stats(self, config, mock_model):
        """Test statistics retrieval."""
        reranker = CrossEncoderReranker(config)

        stats = reranker.get_stats()

        assert "model" in stats
        assert "cache_size" in stats
        assert "cache_enabled" in stats
        assert "enabled" in stats
        assert "device" in stats

        assert stats["enabled"] is True
        assert stats["cache_enabled"] is True

    def test_batch_processing(self, config, mock_model, sample_results):
        """Test batched scoring."""
        # Create reranker with small batch size
        config.batch_size = 2
        reranker = CrossEncoderReranker(config)

        query = "test query"
        reranked = reranker.rerank(query, sample_results)

        # Should still work with batching
        assert len(reranked) > 0

    def test_metadata_preservation(self, config, mock_model, sample_results):
        """Test that metadata is preserved."""
        reranker = CrossEncoderReranker(config)

        query = "test query"
        reranked = reranker.rerank(query, sample_results)

        # Metadata should be preserved
        for result in reranked:
            assert "title" in result.metadata
            original = next(r for r in sample_results if r["id"] == result.id)
            assert result.metadata["title"] == original["metadata"]["title"]

    def test_different_queries_different_cache(self, config, mock_model, sample_results):
        """Test that different queries use different cache entries."""
        reranker = CrossEncoderReranker(config)

        query1 = "chromatin accessibility"
        query2 = "gene expression"

        reranker.rerank(query1, sample_results)
        reranker.rerank(query2, sample_results)

        # Should have 2 cache entries
        assert len(reranker._cache) == 2


def test_integration_with_real_model():
    """Integration test with real cross-encoder model (slow)."""
    pytest.skip("Skipping slow integration test - requires model download")

    # This test would download and use a real model
    config = RerankingConfig(top_k=3)
    reranker = CrossEncoderReranker(config)

    results = [
        {
            "id": "1",
            "text": "ATAC-seq measures chromatin accessibility",
            "score": 0.8,
            "metadata": {},
        },
        {
            "id": "2",
            "text": "RNA-seq measures gene expression",
            "score": 0.75,
            "metadata": {},
        },
    ]

    query = "chromatin accessibility profiling"
    reranked = reranker.rerank(query, results)

    # First result should be about ATAC-seq (more relevant)
    assert reranked[0].id == "1"
    assert reranked[0].combined_score > reranked[1].combined_score


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
