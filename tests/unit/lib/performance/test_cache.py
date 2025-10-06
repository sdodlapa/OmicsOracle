"""
Unit tests for cache manager.

Tests cover:
- Configuration
- Memory caching (LRU)
- Disk caching
- TTL expiration
- Statistics
- Cleanup
"""

import tempfile
import time

import pytest

from omics_oracle_v2.lib.performance.cache import CacheConfig, CacheManager, CacheStats


class TestCacheConfig:
    """Test cache configuration."""

    def test_default_config(self):
        """Test default configuration values."""
        config = CacheConfig()

        assert config.memory_cache_size == 1000
        assert config.memory_ttl_seconds == 3600
        assert config.disk_cache_enabled is True
        assert config.auto_cleanup is True

    def test_custom_config(self):
        """Test custom configuration."""
        config = CacheConfig(
            memory_cache_size=500,
            memory_ttl_seconds=1800,
            disk_cache_enabled=False,
            auto_cleanup=False,
        )

        assert config.memory_cache_size == 500
        assert config.memory_ttl_seconds == 1800
        assert config.disk_cache_enabled is False
        assert config.auto_cleanup is False


class TestCacheStats:
    """Test cache statistics."""

    def test_stats_creation(self):
        """Test creating statistics."""
        stats = CacheStats(
            memory_size=10,
            memory_hits=7,
            memory_misses=3,
            total_requests=10,
        )

        assert stats.memory_size == 10
        assert stats.memory_hits == 7
        assert stats.memory_misses == 3
        assert stats.total_requests == 10

    def test_memory_hit_rate(self):
        """Test memory hit rate calculation."""
        stats = CacheStats(memory_hits=7, memory_misses=3)

        assert stats.memory_hit_rate == 0.7

    def test_disk_hit_rate(self):
        """Test disk hit rate calculation."""
        stats = CacheStats(disk_hits=5, disk_misses=5)

        assert stats.disk_hit_rate == 0.5

    def test_overall_hit_rate(self):
        """Test overall hit rate calculation."""
        stats = CacheStats(memory_hits=7, memory_misses=3, disk_hits=2, disk_misses=8, total_requests=20)

        # 7 memory hits + 2 disk hits = 9 total hits out of 20 requests
        assert stats.overall_hit_rate == 0.45

    def test_zero_division(self):
        """Test hit rate with zero requests."""
        stats = CacheStats()

        assert stats.memory_hit_rate == 0.0
        assert stats.disk_hit_rate == 0.0
        assert stats.overall_hit_rate == 0.0


class TestCacheManager:
    """Test cache manager."""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    def test_initialization(self, temp_cache_dir):
        """Test cache manager initialization."""
        config = CacheConfig(disk_cache_dir=temp_cache_dir)
        cache = CacheManager(config)

        assert cache.config.memory_cache_size == 1000
        assert len(cache._memory_cache) == 0

    def test_set_and_get_memory(self, temp_cache_dir):
        """Test setting and getting from memory cache."""
        config = CacheConfig(disk_cache_dir=temp_cache_dir)
        cache = CacheManager(config)

        # Set value
        test_data = {"id": "GSE123", "score": 0.95}
        cache.set("test_key", test_data)

        # Get value
        result = cache.get("test_key")
        assert result == test_data

    def test_cache_miss(self, temp_cache_dir):
        """Test cache miss."""
        config = CacheConfig(disk_cache_dir=temp_cache_dir)
        cache = CacheManager(config)

        result = cache.get("nonexistent_key")
        assert result is None

    def test_lru_eviction(self, temp_cache_dir):
        """Test LRU eviction policy."""
        config = CacheConfig(memory_cache_size=3, disk_cache_dir=temp_cache_dir)
        cache = CacheManager(config)

        # Fill cache
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        # Add one more (should evict key1)
        cache.set("key4", "value4")

        # key1 should be evicted from memory
        assert "key1" not in cache._memory_cache
        assert "key2" in cache._memory_cache
        assert "key3" in cache._memory_cache
        assert "key4" in cache._memory_cache

    def test_lru_ordering(self, temp_cache_dir):
        """Test LRU ordering with access."""
        config = CacheConfig(memory_cache_size=3, disk_cache_dir=temp_cache_dir)
        cache = CacheManager(config)

        # Fill cache
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        # Access key1 (makes it most recent)
        cache.get("key1")

        # Add key4 (should evict key2, not key1)
        cache.set("key4", "value4")

        assert "key1" in cache._memory_cache  # Recently accessed
        assert "key2" not in cache._memory_cache  # Oldest
        assert "key3" in cache._memory_cache
        assert "key4" in cache._memory_cache

    def test_ttl_expiration_memory(self, temp_cache_dir):
        """Test TTL expiration in memory cache."""
        config = CacheConfig(
            memory_ttl_seconds=1,  # 1 second TTL
            disk_ttl_seconds=1,  # Also expire on disk
            disk_cache_dir=temp_cache_dir,
        )
        cache = CacheManager(config)

        # Set value
        cache.set("test_key", "test_value")

        # Should be available immediately
        assert cache.get("test_key") == "test_value"

        # Wait for expiration
        time.sleep(1.1)

        # Should be expired (from both memory and disk)
        assert cache.get("test_key") is None

    def test_disk_cache(self, temp_cache_dir):
        """Test disk caching."""
        config = CacheConfig(
            memory_cache_size=1,  # Small memory cache
            disk_cache_dir=temp_cache_dir,
        )
        cache = CacheManager(config)

        # Set value
        cache.set("key1", {"data": "value1"})

        # Evict from memory by adding more items
        cache.set("key2", {"data": "value2"})

        # key1 should be evicted from memory but available on disk
        assert "key1" not in cache._memory_cache

        # Should still be retrievable from disk
        result = cache.get("key1")
        assert result == {"data": "value1"}

        # Should be promoted back to memory
        assert "key1" in cache._memory_cache

    def test_disk_cache_disabled(self, temp_cache_dir):
        """Test with disk cache disabled."""
        config = CacheConfig(memory_cache_size=1, disk_cache_enabled=False, disk_cache_dir=temp_cache_dir)
        cache = CacheManager(config)

        # Set value
        cache.set("key1", "value1")

        # Evict from memory
        cache.set("key2", "value2")

        # Should not be retrievable (no disk cache)
        result = cache.get("key1")
        assert result is None

    def test_delete(self, temp_cache_dir):
        """Test deleting cache entries."""
        config = CacheConfig(disk_cache_dir=temp_cache_dir)
        cache = CacheManager(config)

        # Set value
        cache.set("test_key", "test_value")
        assert cache.get("test_key") == "test_value"

        # Delete
        cache.delete("test_key")
        assert cache.get("test_key") is None

    def test_clear(self, temp_cache_dir):
        """Test clearing all caches."""
        config = CacheConfig(disk_cache_dir=temp_cache_dir)
        cache = CacheManager(config)

        # Add multiple values
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        # Clear
        cache.clear()

        # All should be gone
        assert cache.get("key1") is None
        assert cache.get("key2") is None
        assert cache.get("key3") is None
        assert len(cache._memory_cache) == 0

    def test_cleanup_expired(self, temp_cache_dir):
        """Test cleanup of expired entries."""
        config = CacheConfig(memory_ttl_seconds=1, disk_ttl_seconds=1, disk_cache_dir=temp_cache_dir)
        cache = CacheManager(config)

        # Add values
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        # Wait for expiration
        time.sleep(1.1)

        # Cleanup
        removed = cache.cleanup()

        # Both entries should be removed (from memory and disk = 4 total)
        assert removed >= 2  # At least 2 removed
        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_statistics(self, temp_cache_dir):
        """Test cache statistics."""
        config = CacheConfig(disk_cache_dir=temp_cache_dir)
        cache = CacheManager(config)

        # Add some data
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        # Access with hits and misses
        cache.get("key1")  # Hit
        cache.get("key2")  # Hit
        cache.get("key3")  # Miss

        stats = cache.get_stats()

        assert stats.memory_size == 2
        assert stats.memory_hits == 2
        assert stats.memory_misses == 1
        assert stats.total_requests == 3
        assert stats.memory_hit_rate == pytest.approx(2 / 3)

    def test_reset_stats(self, temp_cache_dir):
        """Test resetting statistics."""
        config = CacheConfig(disk_cache_dir=temp_cache_dir)
        cache = CacheManager(config)

        # Generate some stats
        cache.set("key1", "value1")
        cache.get("key1")
        cache.get("key2")

        # Reset
        cache.reset_stats()

        stats = cache.get_stats()
        assert stats.memory_hits == 0
        assert stats.memory_misses == 0
        assert stats.total_requests == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
