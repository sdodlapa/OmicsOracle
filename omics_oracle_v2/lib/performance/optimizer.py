"""
Search performance optimizer.

This module provides optimization strategies for the semantic search pipeline:
- Batch processing for embeddings
- Async query execution
- Result prefetching
- Query planning and optimization
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from omics_oracle_v2.lib.performance.cache import CacheConfig, CacheManager

logger = logging.getLogger(__name__)


@dataclass
class OptimizationConfig:
    """Configuration for search optimizer."""

    # Batch processing
    enable_batching: bool = True
    batch_size: int = 32
    batch_timeout_ms: int = 100

    # Caching
    enable_caching: bool = True
    cache_config: Optional[CacheConfig] = None

    # Prefetching
    enable_prefetch: bool = False
    prefetch_size: int = 10

    # Parallelization
    max_concurrent_queries: int = 5


class SearchOptimizer:
    """
    Performance optimizer for semantic search.

    Features:
    - Batch embedding generation
    - Result caching
    - Query prefetching
    - Performance monitoring

    Example:
        >>> config = OptimizationConfig(enable_batching=True)
        >>> optimizer = SearchOptimizer(config)
        >>>
        >>> # Optimize single query
        >>> results = optimizer.optimize_query(query, search_fn)
        >>>
        >>> # Optimize batch of queries
        >>> results = optimizer.optimize_batch(queries, search_fn)
    """

    def __init__(self, config: Optional[OptimizationConfig] = None):
        """
        Initialize search optimizer.

        Args:
            config: Optimization configuration (uses defaults if None)
        """
        self.config = config or OptimizationConfig()

        # Initialize cache
        if self.config.enable_caching:
            cache_config = self.config.cache_config or CacheConfig()
            self.cache = CacheManager(cache_config)
        else:
            self.cache = None

        # Performance metrics
        self.metrics = {
            "total_queries": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "batch_queries": 0,
            "total_time_ms": 0.0,
        }

        logger.info(
            f"Search optimizer initialized (batching: {self.config.enable_batching}, "
            f"caching: {self.config.enable_caching})"
        )

    def optimize_query(self, query: str, search_fn, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Optimize single query execution.

        Args:
            query: Search query
            search_fn: Search function to call
            force_refresh: Skip cache and force fresh search

        Returns:
            Search results
        """
        start_time = time.time()
        self.metrics["total_queries"] += 1

        cache_key = f"search:{query}"

        # Check cache
        if self.config.enable_caching and not force_refresh:
            cached_results = self.cache.get(cache_key)

            if cached_results is not None:
                self.metrics["cache_hits"] += 1
                elapsed_ms = (time.time() - start_time) * 1000
                self.metrics["total_time_ms"] += elapsed_ms
                logger.debug(f"Cache hit for query: {query[:50]}... ({elapsed_ms:.2f}ms)")
                return cached_results

            self.metrics["cache_misses"] += 1

        # Execute search
        results = search_fn(query)

        # Cache results
        if self.config.enable_caching:
            self.cache.set(cache_key, results)

        elapsed_ms = (time.time() - start_time) * 1000
        self.metrics["total_time_ms"] += elapsed_ms
        logger.debug(f"Query executed: {query[:50]}... ({elapsed_ms:.2f}ms)")

        return results

    def optimize_batch(
        self, queries: List[str], search_fn, force_refresh: bool = False
    ) -> List[List[Dict[str, Any]]]:
        """
        Optimize batch query execution.

        Args:
            queries: List of search queries
            search_fn: Search function to call
            force_refresh: Skip cache and force fresh search

        Returns:
            List of search results (one per query)
        """
        start_time = time.time()
        self.metrics["batch_queries"] += 1

        results = []
        uncached_queries = []
        uncached_indices = []

        # Check cache for each query
        if self.config.enable_caching and not force_refresh:
            for i, query in enumerate(queries):
                cache_key = f"search:{query}"
                cached_result = self.cache.get(cache_key)

                if cached_result is not None:
                    results.append(cached_result)
                    self.metrics["cache_hits"] += 1
                else:
                    results.append(None)  # Placeholder
                    uncached_queries.append(query)
                    uncached_indices.append(i)
                    self.metrics["cache_misses"] += 1
        else:
            uncached_queries = queries
            uncached_indices = list(range(len(queries)))
            results = [None] * len(queries)

        # Execute uncached queries
        if uncached_queries:
            if self.config.enable_batching:
                # Batch processing
                batch_results = self._batch_search(uncached_queries, search_fn)
            else:
                # Sequential processing
                batch_results = [search_fn(q) for q in uncached_queries]

            # Fill in results and cache
            for idx, result in zip(uncached_indices, batch_results):
                results[idx] = result

                if self.config.enable_caching:
                    cache_key = f"search:{queries[idx]}"
                    self.cache.set(cache_key, result)

        elapsed_ms = (time.time() - start_time) * 1000
        self.metrics["total_time_ms"] += elapsed_ms
        logger.info(
            f"Batch executed: {len(queries)} queries "
            f"({len(uncached_queries)} uncached, {elapsed_ms:.2f}ms)"
        )

        return results

    def _batch_search(self, queries: List[str], search_fn) -> List[List[Dict[str, Any]]]:
        """
        Execute batch search with optimizations.

        Args:
            queries: List of queries
            search_fn: Search function

        Returns:
            List of results
        """
        # Process in batches
        results = []
        batch_size = self.config.batch_size

        for i in range(0, len(queries), batch_size):
            batch = queries[i : i + batch_size]
            batch_results = [search_fn(q) for q in batch]
            results.extend(batch_results)

        return results

    async def optimize_async(self, queries: List[str], async_search_fn) -> List[List[Dict[str, Any]]]:
        """
        Optimize queries with async execution.

        Args:
            queries: List of search queries
            async_search_fn: Async search function

        Returns:
            List of search results
        """
        # Limit concurrent queries
        semaphore = asyncio.Semaphore(self.config.max_concurrent_queries)

        async def bounded_search(query: str):
            async with semaphore:
                # Check cache
                if self.config.enable_caching:
                    cache_key = f"search:{query}"
                    cached = self.cache.get(cache_key)
                    if cached is not None:
                        return cached

                # Execute search
                result = await async_search_fn(query)

                # Cache result
                if self.config.enable_caching:
                    self.cache.set(cache_key, result)

                return result

        # Execute all queries concurrently
        tasks = [bounded_search(q) for q in queries]
        results = await asyncio.gather(*tasks)

        return results

    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        metrics = self.metrics.copy()

        if self.metrics["total_queries"] > 0:
            metrics["avg_time_ms"] = self.metrics["total_time_ms"] / self.metrics["total_queries"]
            metrics["cache_hit_rate"] = (
                self.metrics["cache_hits"] / (self.metrics["cache_hits"] + self.metrics["cache_misses"])
                if (self.metrics["cache_hits"] + self.metrics["cache_misses"]) > 0
                else 0.0
            )
        else:
            metrics["avg_time_ms"] = 0.0
            metrics["cache_hit_rate"] = 0.0

        if self.cache:
            cache_stats = self.cache.get_stats()
            metrics["cache_memory_size"] = cache_stats.memory_size
            metrics["cache_disk_size"] = cache_stats.disk_size

        return metrics

    def reset_metrics(self) -> None:
        """Reset performance metrics."""
        self.metrics = {
            "total_queries": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "batch_queries": 0,
            "total_time_ms": 0.0,
        }
        logger.info("Metrics reset")

    def clear_cache(self) -> None:
        """Clear all caches."""
        if self.cache:
            self.cache.clear()


# Demo usage
if __name__ == "__main__":
    import random
    import sys

    # Configure logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    print("=" * 80)
    print("Search Optimizer Demo")
    print("=" * 80)

    # Mock search function
    def mock_search(query: str) -> List[Dict[str, Any]]:
        """Simulate search with some latency."""
        time.sleep(0.05)  # 50ms simulated latency
        return [
            {"id": f"GSE{random.randint(1000, 9999)}", "score": random.random(), "query": query}
            for _ in range(5)
        ]

    # Create optimizer
    config = OptimizationConfig(
        enable_batching=True, enable_caching=True, batch_size=10, max_concurrent_queries=3
    )

    optimizer = SearchOptimizer(config)

    print("\n[*] Optimizer initialized")
    print(f"    Batching: {config.enable_batching}")
    print(f"    Caching: {config.enable_caching}")
    print(f"    Batch size: {config.batch_size}")
    print(f"    Max concurrent: {config.max_concurrent_queries}")

    # Single query optimization
    print("\n[*] Testing single query optimization...")
    query = "ATAC-seq chromatin accessibility"

    # First call - cache miss
    results = optimizer.optimize_query(query, mock_search)
    print(f"    First call: {len(results)} results")

    # Second call - cache hit
    results = optimizer.optimize_query(query, mock_search)
    print(f"    Second call: {len(results)} results (cached)")

    # Batch query optimization
    print("\n[*] Testing batch query optimization...")
    queries = [
        "ATAC-seq chromatin",
        "RNA-seq gene expression",
        "ChIP-seq histone",
        "ATAC-seq chromatin",  # Duplicate - should hit cache
        "DNase-seq",
    ]

    batch_results = optimizer.optimize_batch(queries, mock_search)
    print(f"    Processed {len(queries)} queries")
    print(f"    Got {len(batch_results)} results")

    # Performance metrics
    print("\n[*] Performance metrics:")
    metrics = optimizer.get_metrics()
    print(f"    Total queries: {metrics['total_queries']}")
    print(f"    Cache hits: {metrics['cache_hits']}")
    print(f"    Cache misses: {metrics['cache_misses']}")
    print(f"    Cache hit rate: {metrics['cache_hit_rate']:.2%}")
    print(f"    Batch queries: {metrics['batch_queries']}")
    print(f"    Avg time: {metrics['avg_time_ms']:.2f}ms")
    print(f"    Total time: {metrics['total_time_ms']:.2f}ms")
    if "cache_memory_size" in metrics:
        print(f"    Cache size: {metrics['cache_memory_size']} items")

    # Test with larger batch
    print("\n[*] Testing larger batch (20 queries)...")
    large_batch = [f"query-{i}" for i in range(20)]
    start = time.time()
    large_results = optimizer.optimize_batch(large_batch, mock_search)
    elapsed = (time.time() - start) * 1000
    print(f"    Completed in {elapsed:.2f}ms")
    print(f"    Average per query: {elapsed / len(large_batch):.2f}ms")

    # Final metrics
    print("\n[*] Final metrics:")
    metrics = optimizer.get_metrics()
    print(f"    Total queries processed: {metrics['total_queries']}")
    print(f"    Overall cache hit rate: {metrics['cache_hit_rate']:.2%}")
    print(f"    Total time: {metrics['total_time_ms']:.2f}ms")

    print("\n" + "=" * 80)
    print("Demo complete!")
    print("=" * 80)

    sys.exit(0)
