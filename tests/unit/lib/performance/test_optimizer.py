"""
Unit tests for search optimizer.

Tests cover:
- Configuration
- Query optimization
- Batch optimization
- Caching integration
- Performance metrics
"""

import tempfile
import time

import pytest

from omics_oracle_v2.lib.performance.cache import CacheConfig
from omics_oracle_v2.lib.performance.optimizer import OptimizationConfig, SearchOptimizer


class TestOptimizationConfig:
    """Test optimization configuration."""

    def test_default_config(self):
        """Test default configuration values."""
        config = OptimizationConfig()

        assert config.enable_batching is True
        assert config.batch_size == 32
        assert config.enable_caching is True
        assert config.max_concurrent_queries == 5

    def test_custom_config(self):
        """Test custom configuration."""
        config = OptimizationConfig(
            enable_batching=False,
            batch_size=16,
            enable_caching=False,
            max_concurrent_queries=10,
        )

        assert config.enable_batching is False
        assert config.batch_size == 16
        assert config.enable_caching is False
        assert config.max_concurrent_queries == 10


class TestSearchOptimizer:
    """Test search optimizer."""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def mock_search_fn(self):
        """Create mock search function."""

        def search(query: str):
            """Mock search with small delay."""
            time.sleep(0.01)  # 10ms delay
            return [{"id": f"result_{i}", "score": 0.9 - i * 0.1, "query": query} for i in range(3)]

        return search

    def test_initialization(self, temp_cache_dir):
        """Test optimizer initialization."""
        cache_config = CacheConfig(disk_cache_dir=temp_cache_dir)
        config = OptimizationConfig(cache_config=cache_config)

        optimizer = SearchOptimizer(config)

        assert optimizer.config.enable_batching is True
        assert optimizer.config.enable_caching is True
        assert optimizer.cache is not None

    def test_initialization_no_cache(self):
        """Test initialization without caching."""
        config = OptimizationConfig(enable_caching=False)
        optimizer = SearchOptimizer(config)

        assert optimizer.cache is None

    def test_optimize_single_query(self, temp_cache_dir, mock_search_fn):
        """Test optimizing single query."""
        cache_config = CacheConfig(disk_cache_dir=temp_cache_dir)
        config = OptimizationConfig(cache_config=cache_config)
        optimizer = SearchOptimizer(config)

        query = "test query"
        results = optimizer.optimize_query(query, mock_search_fn)

        assert len(results) == 3
        assert results[0]["query"] == query

    def test_cache_hit(self, temp_cache_dir, mock_search_fn):
        """Test cache hit on second query."""
        cache_config = CacheConfig(disk_cache_dir=temp_cache_dir)
        config = OptimizationConfig(cache_config=cache_config)
        optimizer = SearchOptimizer(config)

        query = "test query"

        # First call - cache miss
        start = time.time()
        results1 = optimizer.optimize_query(query, mock_search_fn)
        time1 = time.time() - start

        # Second call - cache hit (should be faster)
        start = time.time()
        results2 = optimizer.optimize_query(query, mock_search_fn)
        time2 = time.time() - start

        assert results1 == results2
        assert time2 < time1  # Cache hit is faster
        assert optimizer.metrics["cache_hits"] == 1
        assert optimizer.metrics["cache_misses"] == 1

    def test_force_refresh(self, temp_cache_dir, mock_search_fn):
        """Test force refresh bypasses cache."""
        cache_config = CacheConfig(disk_cache_dir=temp_cache_dir)
        config = OptimizationConfig(cache_config=cache_config)
        optimizer = SearchOptimizer(config)

        query = "test query"

        # First call
        optimizer.optimize_query(query, mock_search_fn)

        # Second call with force_refresh
        optimizer.optimize_query(query, mock_search_fn, force_refresh=True)

        # force_refresh bypasses cache check, so no cache hit/miss counted for it
        # First call: 1 cache miss, Second call: bypassed
        assert optimizer.metrics["cache_hits"] == 0
        assert optimizer.metrics["cache_misses"] == 1

    def test_optimize_batch(self, temp_cache_dir, mock_search_fn):
        """Test batch query optimization."""
        cache_config = CacheConfig(disk_cache_dir=temp_cache_dir)
        config = OptimizationConfig(cache_config=cache_config)
        optimizer = SearchOptimizer(config)

        queries = ["query 1", "query 2", "query 3"]
        results = optimizer.optimize_batch(queries, mock_search_fn)

        assert len(results) == 3
        assert all(len(r) == 3 for r in results)
        assert results[0][0]["query"] == queries[0]
        assert results[1][0]["query"] == queries[1]
        assert results[2][0]["query"] == queries[2]

    def test_batch_with_cache_hits(self, temp_cache_dir, mock_search_fn):
        """Test batch optimization with some cached results."""
        cache_config = CacheConfig(disk_cache_dir=temp_cache_dir)
        config = OptimizationConfig(cache_config=cache_config)
        optimizer = SearchOptimizer(config)

        # Pre-cache some results
        optimizer.optimize_query("query 1", mock_search_fn)
        optimizer.optimize_query("query 2", mock_search_fn)

        # Reset metrics
        optimizer.reset_metrics()

        # Batch with mix of cached and uncached
        queries = ["query 1", "query 2", "query 3", "query 4"]
        results = optimizer.optimize_batch(queries, mock_search_fn)

        assert len(results) == 4
        # Should have 2 cache hits (query 1 and 2)
        assert optimizer.metrics["cache_hits"] == 2
        # Should have 2 cache misses (query 3 and 4)
        assert optimizer.metrics["cache_misses"] == 2

    def test_batch_with_duplicates(self, temp_cache_dir, mock_search_fn):
        """Test batch optimization with duplicate queries."""
        cache_config = CacheConfig(disk_cache_dir=temp_cache_dir)
        config = OptimizationConfig(cache_config=cache_config)
        optimizer = SearchOptimizer(config)

        queries = ["query 1", "query 2", "query 1"]  # query 1 appears twice
        results = optimizer.optimize_batch(queries, mock_search_fn)

        assert len(results) == 3
        # In batch mode, all queries are checked at once, so duplicates
        # within the same batch won't create cache hits
        assert len(results) == 3
        # The first query 1 will be executed, and both instances will get same result
        assert results[0] == results[2]

    def test_batching_disabled(self, temp_cache_dir, mock_search_fn):
        """Test with batching disabled."""
        cache_config = CacheConfig(disk_cache_dir=temp_cache_dir)
        config = OptimizationConfig(enable_batching=False, cache_config=cache_config)
        optimizer = SearchOptimizer(config)

        queries = ["query 1", "query 2", "query 3"]
        results = optimizer.optimize_batch(queries, mock_search_fn)

        assert len(results) == 3

    def test_caching_disabled(self, mock_search_fn):
        """Test with caching disabled."""
        config = OptimizationConfig(enable_caching=False)
        optimizer = SearchOptimizer(config)

        query = "test query"

        # Multiple calls should all execute search
        optimizer.optimize_query(query, mock_search_fn)
        optimizer.optimize_query(query, mock_search_fn)

        # No cache hits/misses
        assert optimizer.metrics["cache_hits"] == 0
        assert optimizer.metrics["cache_misses"] == 0

    def test_metrics(self, temp_cache_dir, mock_search_fn):
        """Test performance metrics."""
        cache_config = CacheConfig(disk_cache_dir=temp_cache_dir)
        config = OptimizationConfig(cache_config=cache_config)
        optimizer = SearchOptimizer(config)

        # Execute some queries
        optimizer.optimize_query("query 1", mock_search_fn)
        optimizer.optimize_query("query 2", mock_search_fn)
        optimizer.optimize_query("query 1", mock_search_fn)  # Cache hit

        metrics = optimizer.get_metrics()

        assert metrics["total_queries"] == 3
        assert metrics["cache_hits"] == 1
        assert metrics["cache_misses"] == 2
        assert metrics["cache_hit_rate"] == pytest.approx(1 / 3)
        assert metrics["avg_time_ms"] > 0
        assert metrics["total_time_ms"] > 0

    def test_reset_metrics(self, temp_cache_dir, mock_search_fn):
        """Test resetting metrics."""
        cache_config = CacheConfig(disk_cache_dir=temp_cache_dir)
        config = OptimizationConfig(cache_config=cache_config)
        optimizer = SearchOptimizer(config)

        # Generate metrics
        optimizer.optimize_query("query 1", mock_search_fn)
        assert optimizer.metrics["total_queries"] > 0

        # Reset
        optimizer.reset_metrics()

        metrics = optimizer.get_metrics()
        assert metrics["total_queries"] == 0
        assert metrics["cache_hits"] == 0
        assert metrics["cache_misses"] == 0

    def test_clear_cache(self, temp_cache_dir, mock_search_fn):
        """Test clearing cache."""
        cache_config = CacheConfig(disk_cache_dir=temp_cache_dir)
        config = OptimizationConfig(cache_config=cache_config)
        optimizer = SearchOptimizer(config)

        # Add to cache
        optimizer.optimize_query("query 1", mock_search_fn)

        # Clear cache
        optimizer.clear_cache()

        # Should be cache miss now
        optimizer.reset_metrics()
        optimizer.optimize_query("query 1", mock_search_fn)

        assert optimizer.metrics["cache_hits"] == 0
        assert optimizer.metrics["cache_misses"] == 1

    def test_batch_size_respected(self, temp_cache_dir, mock_search_fn):
        """Test that batch size is respected."""
        cache_config = CacheConfig(disk_cache_dir=temp_cache_dir)
        config = OptimizationConfig(batch_size=2, cache_config=cache_config)
        optimizer = SearchOptimizer(config)

        # Create 5 queries (should be processed in batches of 2)
        queries = [f"query {i}" for i in range(5)]
        results = optimizer.optimize_batch(queries, mock_search_fn)

        assert len(results) == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
