"""
Tests for GEOCache - 2-tier cache (Redis + UnifiedDB).

Tests the GEOCache class for caching complete GEO dataset metadata
with automatic promotion and write-through semantics.
"""

import asyncio
import pytest
from datetime import datetime
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch

from omics_oracle_v2.lib.pipelines.storage.registry.geo_cache import GEOCache, create_geo_cache


# ========== Fixtures ==========

@pytest.fixture
def mock_unified_db():
    """Create a mock UnifiedDatabase for testing."""
    mock_db = MagicMock()
    
    # Mock get_complete_geo_data to return sample data
    mock_db.get_complete_geo_data = MagicMock(return_value={
        "geo": {
            "geo_id": "GSE123456",
            "title": "Test GEO Dataset",
            "organism": "Homo sapiens",
            "platform": "GPL570"
        },
        "papers": {
            "original": [
                {
                    "pmid": "12345678",
                    "title": "Test Paper",
                    "download_history": [{"status": "downloaded"}]
                }
            ],
            "citing": []
        },
        "statistics": {
            "total_papers": 1,
            "successful_downloads": 1,
            "success_rate": 100.0
        }
    })
    
    # Mock update_geo_dataset
    mock_db.update_geo_dataset = MagicMock()
    
    return mock_db


@pytest.fixture
def sample_geo_data():
    """Sample GEO dataset data for testing."""
    return {
        "geo": {
            "geo_id": "GSE123456",
            "title": "Test GEO Dataset",
            "summary": "This is a test dataset",
            "organism": "Homo sapiens",
            "platform": "GPL570",
            "sample_count": 10
        },
        "papers": {
            "original": [
                {
                    "pmid": "12345678",
                    "doi": "10.1234/test",
                    "title": "Test Paper",
                    "download_history": [
                        {"status": "downloaded", "file_path": "/path/to/file.pdf"}
                    ]
                }
            ],
            "citing": []
        },
        "statistics": {
            "original_papers": 1,
            "citing_papers": 0,
            "total_papers": 1,
            "successful_downloads": 1,
            "failed_downloads": 0,
            "success_rate": 100.0
        }
    }


@pytest.fixture
def cache(mock_unified_db):
    """Create a GEOCache instance for testing."""
    return GEOCache(mock_unified_db)


# ========== Initialization Tests ==========

class TestGEOCacheInit:
    """Test GEOCache initialization."""

    def test_default_initialization(self, mock_unified_db):
        """Test initialization with default parameters."""
        cache = GEOCache(mock_unified_db)
        
        assert cache.unified_db == mock_unified_db
        assert cache.redis_ttl == 7 * 24 * 3600  # 7 days in seconds
        assert cache.enable_fallback is True
        assert cache.redis_cache is not None
        assert isinstance(cache.memory_fallback, dict)
        assert cache.max_memory_entries == 1000

    def test_custom_ttl(self, mock_unified_db):
        """Test initialization with custom TTL."""
        cache = GEOCache(mock_unified_db, redis_ttl_days=14)
        
        assert cache.redis_ttl == 14 * 24 * 3600  # 14 days in seconds

    def test_disable_fallback(self, mock_unified_db):
        """Test initialization with fallback disabled."""
        cache = GEOCache(mock_unified_db, enable_fallback=False)
        
        assert cache.enable_fallback is False

    def test_factory_function(self, mock_unified_db):
        """Test create_geo_cache factory function."""
        cache = create_geo_cache(mock_unified_db, redis_ttl_days=10)
        
        assert isinstance(cache, GEOCache)
        assert cache.redis_ttl == 10 * 24 * 3600


# ========== Cache Hit Tests ==========

class TestGEOCacheHit:
    """Test cache hit scenarios (Redis hot-tier)."""

    @pytest.mark.asyncio
    async def test_redis_cache_hit(self, cache, sample_geo_data):
        """Test cache hit from Redis (hot tier)"""
        with patch.object(cache.redis_cache, 'get_geo_metadata', new_callable=AsyncMock) as mock_redis_get:
            mock_redis_get.return_value = sample_geo_data
            
            result = await cache.get("GSE123456")
            
            assert result == sample_geo_data
            mock_redis_get.assert_called_once_with("GSE123456")
            assert cache.stats["cache_hits"] == 1
            assert cache.stats["cache_misses"] == 0

    @pytest.mark.asyncio
    async def test_memory_fallback_hit(self, mock_unified_db, sample_geo_data):
        """Test cache hit from in-memory fallback."""
        cache = GEOCache(mock_unified_db)
        
        # Populate memory fallback
        cache.memory_fallback["GSE123456"] = sample_geo_data
        
        # Mock Redis to fail
        with patch.object(cache.redis_cache, 'get_geo_metadata', new_callable=AsyncMock) as mock_redis_get:
            mock_redis_get.return_value = None
            
            result = await cache.get("GSE123456")
            
            # Should return data from memory
            assert result == sample_geo_data
            
            # Should check Redis first
            mock_redis_get.assert_called_once()
            
            # Should NOT query UnifiedDB
            mock_unified_db.get_complete_geo_data.assert_not_called()
            
            # Should increment cache hits
            assert cache.stats["cache_hits"] == 1


# ========== Cache Miss Tests ==========

class TestGEOCacheMiss:
    """Test cache miss scenarios (queries UnifiedDB warm-tier)."""

    @pytest.mark.asyncio
    async def test_cache_miss_with_promotion(self, mock_unified_db, sample_geo_data):
        """Test cache miss triggers UnifiedDB query and promotes to Redis."""
        cache = GEOCache(mock_unified_db)
        
        # Mock Redis cache miss
        with patch.object(cache.redis_cache, 'get_geo_metadata', new_callable=AsyncMock) as mock_redis_get, \
             patch.object(cache.redis_cache, 'set_geo_metadata', new_callable=AsyncMock) as mock_redis_set:
            
            mock_redis_get.return_value = None
            mock_unified_db.get_complete_geo_data.return_value = sample_geo_data
            
            result = await cache.get("GSE123456")
            
            # Should return data from UnifiedDB
            assert result == sample_geo_data
            
            # Should check Redis
            mock_redis_get.assert_called_once()
            
            # Should query UnifiedDB
            mock_unified_db.get_complete_geo_data.assert_called_once_with("GSE123456")
            
            # Should promote to Redis
            mock_redis_set.assert_called_once()
            
            # Should increment stats
            assert cache.stats["cache_misses"] == 1
            assert cache.stats["db_queries"] == 1
            assert cache.stats["promotions"] == 1

    @pytest.mark.asyncio
    async def test_cache_miss_not_found(self, mock_unified_db):
        """Test cache miss when GEO not found in UnifiedDB."""
        cache = GEOCache(mock_unified_db)
        
        # Mock Redis cache miss
        with patch.object(cache.redis_cache, 'get_geo_metadata', new_callable=AsyncMock) as mock_redis_get:
            mock_redis_get.return_value = None
            mock_unified_db.get_complete_geo_data.return_value = None
            
            result = await cache.get("GSE_NONEXISTENT")
            
            # Should return None
            assert result is None
            
            # Should query UnifiedDB
            mock_unified_db.get_complete_geo_data.assert_called_once()
            
            # Should increment cache misses
            assert cache.stats["cache_misses"] == 1
            assert cache.stats["db_queries"] == 1


# ========== Write-Through Tests ==========

class TestGEOCacheUpdate:
    """Test write-through update semantics."""

    @pytest.mark.asyncio
    async def test_update_write_through(self, mock_unified_db, sample_geo_data):
        """Test update writes to both UnifiedDB and Redis."""
        cache = GEOCache(mock_unified_db)
        
        with patch.object(cache.redis_cache, 'set_geo_metadata', new_callable=AsyncMock) as mock_redis_set:
            result = await cache.update("GSE123456", sample_geo_data)
            
            # Should succeed
            assert result is True
            
            # Should write to UnifiedDB
            mock_unified_db.update_geo_dataset.assert_called_once_with("GSE123456", sample_geo_data)
            
            # Should write to Redis
            mock_redis_set.assert_called_once()
            
            # Verify Redis call included TTL
            call_args = mock_redis_set.call_args
            assert call_args[1]['ttl'] == cache.redis_ttl

    @pytest.mark.asyncio
    async def test_update_invalid_params(self, mock_unified_db):
        """Test update with invalid parameters."""
        cache = GEOCache(mock_unified_db)
        
        # Empty geo_id
        result = await cache.update("", {"data": "value"})
        assert result is False
        
        # Empty data
        result = await cache.update("GSE123456", {})
        assert result is False
        assert result is False

    @pytest.mark.asyncio
    async def test_update_redis_failure_fallback(self, mock_unified_db, sample_geo_data):
        """Test update fallback to memory if Redis fails."""
        cache = GEOCache(mock_unified_db)
        
        with patch.object(cache.redis_cache, 'set_geo_metadata', new_callable=AsyncMock) as mock_redis_set:
            # Mock Redis failure
            mock_redis_set.side_effect = Exception("Redis connection failed")
            
            result = await cache.update("GSE123456", sample_geo_data)
            
            # Should still succeed (UnifiedDB write succeeded)
            assert result is True
            
            # Should write to UnifiedDB
            mock_unified_db.update_geo_dataset.assert_called_once()
            
            # Should increment Redis errors
            assert cache.stats["redis_errors"] >= 1


# ========== Invalidation Tests ==========

class TestGEOCacheInvalidate:
    """Test cache invalidation."""

    @pytest.mark.asyncio
    async def test_invalidate_redis(self, mock_unified_db):
        """Test invalidating cache entry in Redis."""
        cache = GEOCache(mock_unified_db)
        
        with patch.object(cache.redis_cache, 'invalidate_pattern') as mock_redis_delete:
            mock_redis_delete.return_value = 1  # 1 key deleted
            result = await cache.invalidate("GSE123456")
            
            # Should succeed
            assert result is True
            
            # Should delete from Redis with correct pattern
            mock_redis_delete.assert_called_once_with("geo:GSE123456*")

    @pytest.mark.asyncio
    async def test_invalidate_memory(self, mock_unified_db, sample_geo_data):
        """Test invalidating cache entry in memory fallback."""
        cache = GEOCache(mock_unified_db)
        
        # Populate memory fallback
        cache.memory_fallback["GSE123456"] = sample_geo_data
        
        result = await cache.invalidate("GSE123456")
        
        # Should succeed
        assert result is True
        
        # Should remove from memory
        assert "GSE123456" not in cache.memory_fallback

    @pytest.mark.asyncio
    async def test_invalidate_batch(self, mock_unified_db):
        """Test batch invalidation."""
        cache = GEOCache(mock_unified_db)
        
        geo_ids = ["GSE1", "GSE2", "GSE3", "GSE4", "GSE5"]
        
        with patch.object(cache.redis_cache, 'invalidate_pattern') as mock_redis_delete:
            mock_redis_delete.return_value = 1  # Each call deletes 1 key
            count = await cache.invalidate_batch(geo_ids)
            
            # Should invalidate all
            assert count == 5
            
            # Should call invalidate_pattern for each
            assert mock_redis_delete.call_count == 5


# ========== Statistics Tests ==========

class TestGEOCacheStats:
    """Test cache statistics tracking."""

    @pytest.mark.asyncio
    async def test_get_stats_initial(self, mock_unified_db):
        """Test stats when cache is empty."""
        cache = GEOCache(mock_unified_db)
        
        stats = await cache.get_stats()
        
        assert stats["cache_hits"] == 0
        assert stats["cache_misses"] == 0
        assert stats["hit_rate"] == 0.0
        assert stats["total_requests"] == 0
        assert stats["db_queries"] == 0
        assert stats["memory_entries"] == 0

    @pytest.mark.asyncio
    async def test_get_stats_with_activity(self, mock_unified_db, sample_geo_data):
        """Test stats after cache activity."""
        cache = GEOCache(mock_unified_db)
        
        # Simulate 8 hits and 2 misses
        cache.stats["cache_hits"] = 8
        cache.stats["cache_misses"] = 2
        cache.stats["db_queries"] = 2
        cache.stats["promotions"] = 2
        cache.memory_fallback["GSE1"] = sample_geo_data
        cache.memory_fallback["GSE2"] = sample_geo_data
        
        stats = await cache.get_stats()
        
        assert stats["cache_hits"] == 8
        assert stats["cache_misses"] == 2
        assert stats["hit_rate"] == 80.0  # 8 / (8 + 2) * 100
        assert stats["total_requests"] == 10
        assert stats["db_queries"] == 2
        assert stats["promotions"] == 2
        assert stats["memory_entries"] == 2


# ========== Warm-Up Tests ==========

class TestGEOCacheWarmUp:
    """Test cache warm-up functionality."""

    @pytest.mark.asyncio
    async def test_warm_up_success(self, mock_unified_db, sample_geo_data):
        """Test pre-populating cache with GEO IDs."""
        cache = GEOCache(mock_unified_db)
        
        geo_ids = ["GSE1", "GSE2", "GSE3"]
        
        with patch.object(cache, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = sample_geo_data
            
            count = await cache.warm_up(geo_ids)
            
            # Should warm up all
            assert count == 3
            
            # Should call get for each
            assert mock_get.call_count == 3

    @pytest.mark.asyncio
    async def test_warm_up_partial_failure(self, mock_unified_db, sample_geo_data):
        """Test warm-up with some failures."""
        cache = GEOCache(mock_unified_db)
        
        geo_ids = ["GSE1", "GSE2", "GSE3"]
        
        with patch.object(cache, 'get', new_callable=AsyncMock) as mock_get:
            # First succeeds, second fails, third succeeds
            mock_get.side_effect = [sample_geo_data, None, sample_geo_data]
            
            count = await cache.warm_up(geo_ids)
            
            # Should count only successful warm-ups
            assert count == 2


# ========== Fallback Tests ==========

class TestGEOCacheFallback:
    """Test in-memory fallback when Redis unavailable."""

    @pytest.mark.asyncio
    async def test_fallback_on_redis_error(self, mock_unified_db, sample_geo_data):
        """Test fallback to memory when Redis fails."""
        cache = GEOCache(mock_unified_db)
        
        with patch.object(cache.redis_cache, 'get_geo_metadata', new_callable=AsyncMock) as mock_redis_get:
            # Mock Redis error
            mock_redis_get.side_effect = Exception("Redis connection failed")
            mock_unified_db.get_complete_geo_data.return_value = sample_geo_data
            
            result = await cache.get("GSE123456")
            
            # Should still return data (from UnifiedDB)
            assert result == sample_geo_data
            
            # Should increment Redis errors
            assert cache.stats["redis_errors"] >= 1

    @pytest.mark.asyncio
    async def test_memory_lru_eviction(self, mock_unified_db, sample_geo_data):
        """Test LRU eviction when memory cache exceeds max entries."""
        cache = GEOCache(mock_unified_db)
        cache.max_memory_entries = 5  # Small limit for testing
        
        # Fill memory beyond limit
        for i in range(7):
            cache._add_to_memory_fallback(f"GSE{i}", sample_geo_data)
        
        # Should evict oldest entries
        assert len(cache.memory_fallback) == 5
        assert cache.stats["evictions"] == 2
        
        # Latest entries should be present
        assert "GSE6" in cache.memory_fallback
        assert "GSE5" in cache.memory_fallback


# ========== Validation Tests ==========

class TestGEOCacheValidation:
    """Test input validation."""

    @pytest.mark.asyncio
    async def test_get_invalid_geo_id(self, mock_unified_db):
        """Test get with invalid GEO ID format."""
        cache = GEOCache(mock_unified_db)
        
        # Empty string
        result = await cache.get("")
        assert result is None
        
        # Not a GSE ID
        result = await cache.get("INVALID123")
        assert result is None


# ========== Integration Tests ==========

class TestGEOCacheIntegration:
    """Integration tests with real-ish scenarios."""

    @pytest.mark.asyncio
    async def test_full_cache_lifecycle(self, mock_unified_db, sample_geo_data):
        """Test complete cache lifecycle: miss → promote → hit → invalidate → miss."""
        cache = GEOCache(mock_unified_db)
        
        with patch.object(cache.redis_cache, 'get_geo_metadata', new_callable=AsyncMock) as mock_redis_get, \
             patch.object(cache.redis_cache, 'set_geo_metadata', new_callable=AsyncMock) as mock_redis_set, \
             patch.object(cache.redis_cache, 'invalidate_pattern') as mock_redis_delete:
            
            mock_redis_delete.return_value = 1  # 1 key deleted
            
            # 1. First get: cache miss
            mock_redis_get.return_value = None
            mock_unified_db.get_complete_geo_data.return_value = sample_geo_data
            
            result1 = await cache.get("GSE123456")
            assert result1 == sample_geo_data
            assert cache.stats["cache_misses"] == 1
            assert cache.stats["promotions"] == 1
            
            # 2. Second get: cache hit (simulate Redis having data now)
            mock_redis_get.return_value = sample_geo_data
            
            result2 = await cache.get("GSE123456")
            assert result2 == sample_geo_data
            assert cache.stats["cache_hits"] == 1
            
            # 3. Invalidate
            await cache.invalidate("GSE123456")
            mock_redis_delete.assert_called()
            
            # 4. Third get: cache miss again
            mock_redis_get.return_value = None
            
            result3 = await cache.get("GSE123456")
            assert result3 == sample_geo_data
            assert cache.stats["cache_misses"] == 2

    @pytest.mark.asyncio
    async def test_concurrent_access(self, mock_unified_db, sample_geo_data):
        """Test concurrent access to cache."""
        cache = GEOCache(mock_unified_db)
        
        with patch.object(cache.redis_cache, 'get_geo_metadata', new_callable=AsyncMock) as mock_redis_get:
            mock_redis_get.return_value = sample_geo_data
            
            # Simulate 10 concurrent requests
            tasks = [cache.get("GSE123456") for _ in range(10)]
            results = await asyncio.gather(*tasks)
            
            # All should succeed
            assert len(results) == 10
            assert all(r == sample_geo_data for r in results)


# ========== Regression Tests (Old Methods Removed) ==========

class TestGEORegistryCleanup:
    """Test that old GEORegistry methods are completely removed."""

    def test_no_legacy_attributes(self):
        """Test that GEORegistry has no legacy SQLite attributes."""
        from omics_oracle_v2.lib.pipelines.storage.registry import GEORegistry
        
        # Mock the actual modules that are imported inside __init__
        with patch('omics_oracle_v2.lib.pipelines.storage.registry.geo_cache.GEOCache') as mock_cache, \
             patch('omics_oracle_v2.lib.pipelines.storage.unified_db.UnifiedDatabase') as mock_db:
            registry = GEORegistry()
            
            # Should NOT have SQLite connection
            assert not hasattr(registry, 'conn')
            
            # Should NOT have old methods
            assert not hasattr(registry, 'register_geo_dataset')
            assert not hasattr(registry, 'register_publication')
            assert not hasattr(registry, 'link_geo_to_publication')
            assert not hasattr(registry, '_init_schema')
            assert not hasattr(registry, '_legacy_get_complete_geo_data')
            assert not hasattr(registry, '_get_download_history')
            
            # Should ONLY have cache
            assert hasattr(registry, 'cache')

    def test_async_only_api(self):
        """Test that GEORegistry methods are async-only."""
        from omics_oracle_v2.lib.pipelines.storage.registry import GEORegistry
        import inspect
        
        # Check that get_complete_geo_data is async
        assert inspect.iscoroutinefunction(GEORegistry.get_complete_geo_data)
        assert inspect.iscoroutinefunction(GEORegistry.invalidate_cache)
        assert inspect.iscoroutinefunction(GEORegistry.get_stats)
        assert inspect.iscoroutinefunction(GEORegistry.warm_up)
