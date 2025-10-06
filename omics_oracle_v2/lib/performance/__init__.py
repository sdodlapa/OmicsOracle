"""
Performance optimization module for OmicsOracle.

This module provides performance enhancements for the semantic search pipeline:
- Result caching with TTL
- Batch processing
- Async operations
- Memory optimization
"""

from omics_oracle_v2.lib.performance.cache import CacheConfig, CacheManager, CacheStats
from omics_oracle_v2.lib.performance.optimizer import OptimizationConfig, SearchOptimizer

__all__ = [
    "CacheConfig",
    "CacheManager",
    "CacheStats",
    "OptimizationConfig",
    "SearchOptimizer",
]
