"""
Advanced caching system for search results and embeddings.

This module provides a multi-level caching system with:
- In-memory LRU cache for hot data
- File-based persistent cache
- TTL (Time-To-Live) support
- Cache statistics and monitoring
- Automatic cleanup
"""

import hashlib
import json
import logging
import time
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class CacheConfig:
    """Configuration for cache manager."""

    # Memory cache settings
    memory_cache_size: int = 1000  # Max items in memory
    memory_ttl_seconds: int = 3600  # 1 hour

    # Disk cache settings
    disk_cache_enabled: bool = True
    disk_cache_dir: str = "data/cache/search"
    disk_ttl_seconds: int = 86400  # 24 hours

    # Cleanup settings
    auto_cleanup: bool = True
    cleanup_interval_seconds: int = 3600  # 1 hour


@dataclass
class CacheStats:
    """Cache statistics."""

    memory_size: int = 0
    disk_size: int = 0
    memory_hits: int = 0
    memory_misses: int = 0
    disk_hits: int = 0
    disk_misses: int = 0
    total_requests: int = 0

    @property
    def memory_hit_rate(self) -> float:
        """Calculate memory cache hit rate."""
        total = self.memory_hits + self.memory_misses
        return self.memory_hits / total if total > 0 else 0.0

    @property
    def disk_hit_rate(self) -> float:
        """Calculate disk cache hit rate."""
        total = self.disk_hits + self.disk_misses
        return self.disk_hits / total if total > 0 else 0.0

    @property
    def overall_hit_rate(self) -> float:
        """Calculate overall cache hit rate."""
        hits = self.memory_hits + self.disk_hits
        return hits / self.total_requests if self.total_requests > 0 else 0.0


class CacheManager:
    """
    Multi-level cache manager for search results.

    Features:
    - Two-level caching (memory + disk)
    - LRU eviction for memory cache
    - TTL-based expiration
    - Automatic cleanup
    - Statistics tracking

    Example:
        >>> config = CacheConfig(memory_cache_size=500)
        >>> cache = CacheManager(config)
        >>>
        >>> # Store search results
        >>> cache.set("query:atac-seq", results, ttl=3600)
        >>>
        >>> # Retrieve results
        >>> results = cache.get("query:atac-seq")
        >>> if results:
        ...     print("Cache hit!")
        >>>
        >>> # Get statistics
        >>> stats = cache.get_stats()
        >>> print(f"Hit rate: {stats.overall_hit_rate:.2%}")
    """

    def __init__(self, config: Optional[CacheConfig] = None):
        """
        Initialize cache manager.

        Args:
            config: Cache configuration (uses defaults if None)
        """
        self.config = config or CacheConfig()
        self.stats = CacheStats()

        # In-memory LRU cache
        self._memory_cache: OrderedDict[str, Tuple[Any, float]] = OrderedDict()

        # Disk cache directory
        if self.config.disk_cache_enabled:
            self.cache_dir = Path(self.config.disk_cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Last cleanup time
        self._last_cleanup = time.time()

        logger.info(
            f"Cache manager initialized (memory: {self.config.memory_cache_size}, "
            f"disk: {self.config.disk_cache_enabled})"
        )

    def _get_cache_key(self, key: str) -> str:
        """Generate cache key hash."""
        return hashlib.md5(key.encode()).hexdigest()

    def _is_expired(self, timestamp: float, ttl: int) -> bool:
        """Check if cache entry is expired."""
        return time.time() - timestamp > ttl

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        self.stats.total_requests += 1

        # Try memory cache first
        if key in self._memory_cache:
            value, timestamp = self._memory_cache[key]

            if not self._is_expired(timestamp, self.config.memory_ttl_seconds):
                # Move to end (most recently used)
                self._memory_cache.move_to_end(key)
                self.stats.memory_hits += 1
                logger.debug(f"Memory cache hit: {key[:32]}...")
                return value
            else:
                # Expired - remove from cache
                del self._memory_cache[key]
                logger.debug(f"Memory cache expired: {key[:32]}...")

        self.stats.memory_misses += 1

        # Try disk cache
        if self.config.disk_cache_enabled:
            cache_key = self._get_cache_key(key)
            cache_file = self.cache_dir / f"{cache_key}.json"

            if cache_file.exists():
                try:
                    with open(cache_file, "r") as f:
                        data = json.load(f)

                    timestamp = data.get("timestamp", 0)

                    if not self._is_expired(timestamp, self.config.disk_ttl_seconds):
                        value = data.get("value")
                        self.stats.disk_hits += 1
                        logger.debug(f"Disk cache hit: {key[:32]}...")

                        # Promote to memory cache
                        self._set_memory(key, value, timestamp)

                        return value
                    else:
                        # Expired - remove file
                        cache_file.unlink()
                        logger.debug(f"Disk cache expired: {key[:32]}...")
                except Exception as e:
                    logger.warning(f"Failed to read disk cache: {e}")

        self.stats.disk_misses += 1
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Store value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses config default if None)
        """
        timestamp = time.time()

        # Store in memory cache
        self._set_memory(key, value, timestamp)

        # Store in disk cache
        if self.config.disk_cache_enabled:
            cache_key = self._get_cache_key(key)
            cache_file = self.cache_dir / f"{cache_key}.json"

            try:
                with open(cache_file, "w") as f:
                    json.dump(
                        {"key": key, "value": value, "timestamp": timestamp},
                        f,
                        indent=2,
                    )
                logger.debug(f"Disk cache set: {key[:32]}...")
            except Exception as e:
                logger.warning(f"Failed to write disk cache: {e}")

        # Auto cleanup if needed
        if self.config.auto_cleanup:
            if time.time() - self._last_cleanup > self.config.cleanup_interval_seconds:
                self.cleanup()

    def _set_memory(self, key: str, value: Any, timestamp: float) -> None:
        """Store value in memory cache with LRU eviction."""
        # Remove oldest if at capacity
        if (
            key not in self._memory_cache
            and len(self._memory_cache) >= self.config.memory_cache_size
        ):
            oldest_key = next(iter(self._memory_cache))
            del self._memory_cache[oldest_key]
            logger.debug(f"LRU evicted: {oldest_key[:32]}...")

        self._memory_cache[key] = (value, timestamp)
        self._memory_cache.move_to_end(key)
        logger.debug(f"Memory cache set: {key[:32]}...")

    def delete(self, key: str) -> None:
        """Delete value from cache."""
        # Remove from memory
        if key in self._memory_cache:
            del self._memory_cache[key]

        # Remove from disk
        if self.config.disk_cache_enabled:
            cache_key = self._get_cache_key(key)
            cache_file = self.cache_dir / f"{cache_key}.json"
            if cache_file.exists():
                cache_file.unlink()

        logger.debug(f"Cache deleted: {key[:32]}...")

    def clear(self) -> None:
        """Clear all caches."""
        # Clear memory
        self._memory_cache.clear()

        # Clear disk
        if self.config.disk_cache_enabled:
            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    cache_file.unlink()
                except Exception as e:
                    logger.warning(f"Failed to delete {cache_file}: {e}")

        logger.info("Cache cleared")

    def cleanup(self) -> int:
        """
        Remove expired entries.

        Returns:
            Number of entries removed
        """
        removed = 0
        now = time.time()

        # Cleanup memory cache
        expired_keys = []
        for key, (value, timestamp) in self._memory_cache.items():
            if self._is_expired(timestamp, self.config.memory_ttl_seconds):
                expired_keys.append(key)

        for key in expired_keys:
            del self._memory_cache[key]
            removed += 1

        # Cleanup disk cache
        if self.config.disk_cache_enabled:
            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    with open(cache_file, "r") as f:
                        data = json.load(f)
                    timestamp = data.get("timestamp", 0)

                    if self._is_expired(timestamp, self.config.disk_ttl_seconds):
                        cache_file.unlink()
                        removed += 1
                except Exception as e:
                    logger.warning(f"Failed to check {cache_file}: {e}")

        self._last_cleanup = now
        logger.info(f"Cache cleanup: {removed} entries removed")
        return removed

    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        self.stats.memory_size = len(self._memory_cache)

        if self.config.disk_cache_enabled:
            self.stats.disk_size = len(list(self.cache_dir.glob("*.json")))
        else:
            self.stats.disk_size = 0

        return self.stats

    def reset_stats(self) -> None:
        """Reset statistics counters."""
        self.stats = CacheStats()
        logger.info("Cache stats reset")


# Demo usage
if __name__ == "__main__":
    import sys

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    print("=" * 80)
    print("Cache Manager Demo")
    print("=" * 80)

    # Create cache manager
    config = CacheConfig(
        memory_cache_size=100, memory_ttl_seconds=60, disk_ttl_seconds=300
    )

    cache = CacheManager(config)

    print("\n[*] Cache manager initialized")
    print(f"    Memory size: {config.memory_cache_size}")
    print(f"    Memory TTL: {config.memory_ttl_seconds}s")
    print(f"    Disk enabled: {config.disk_cache_enabled}")

    # Demo data
    test_data = {
        "query:atac-seq": [
            {"id": "GSE123", "score": 0.95, "title": "ATAC-seq study"},
            {"id": "GSE124", "score": 0.88, "title": "Chromatin accessibility"},
        ],
        "query:rna-seq": [
            {"id": "GSE125", "score": 0.92, "title": "RNA-seq analysis"},
            {"id": "GSE126", "score": 0.85, "title": "Gene expression"},
        ],
        "query:chip-seq": [
            {"id": "GSE127", "score": 0.90, "title": "ChIP-seq study"},
            {"id": "GSE128", "score": 0.83, "title": "Histone modifications"},
        ],
    }

    # Store data
    print("\n[*] Storing data in cache...")
    for key, value in test_data.items():
        cache.set(key, value)
        print(f"    Stored: {key}")

    # Retrieve data
    print("\n[*] Retrieving data from cache...")
    for key in test_data.keys():
        result = cache.get(key)
        if result:
            print(f"    Hit: {key} ({len(result)} results)")
        else:
            print(f"    Miss: {key}")

    # Try non-existent key
    print("\n[*] Testing cache miss...")
    result = cache.get("query:nonexistent")
    print(f"    Result: {result}")

    # Get statistics
    print("\n[*] Cache statistics:")
    stats = cache.get_stats()
    print(f"    Memory size: {stats.memory_size}")
    print(f"    Disk size: {stats.disk_size}")
    print(f"    Memory hits: {stats.memory_hits}")
    print(f"    Memory misses: {stats.memory_misses}")
    print(f"    Disk hits: {stats.disk_hits}")
    print(f"    Disk misses: {stats.disk_misses}")
    print(f"    Total requests: {stats.total_requests}")
    print(f"    Memory hit rate: {stats.memory_hit_rate:.2%}")
    print(f"    Overall hit rate: {stats.overall_hit_rate:.2%}")

    # Test LRU eviction
    print("\n[*] Testing LRU eviction...")
    print(f"    Cache size limit: {config.memory_cache_size}")
    print(f"    Adding {config.memory_cache_size + 10} items...")

    for i in range(config.memory_cache_size + 10):
        cache.set(f"query:test-{i}", {"id": f"GSE{i}", "score": 0.9})

    stats = cache.get_stats()
    print(f"    Memory size after: {stats.memory_size}")
    print(f"    LRU eviction working: {stats.memory_size == config.memory_cache_size}")

    # Cleanup
    print("\n[*] Cleaning up cache...")
    cache.clear()
    stats = cache.get_stats()
    print(f"    Memory size: {stats.memory_size}")
    print(f"    Disk size: {stats.disk_size}")

    print("\n" + "=" * 80)
    print("Demo complete!")
    print("=" * 80)

    sys.exit(0)
