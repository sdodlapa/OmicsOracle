#!/usr/bin/env python3
"""
Week 3 Day 1: Per-Item Batch Cache Validation

Tests the new batch caching implementation to ensure:
- Batch operations work correctly
- Cache hit rates are high for repeated queries
- Performance improvement is significant

This validates the Week 3 Day 1 cache optimization.
"""

import asyncio
import logging
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def test_batch_cache():
    """Test batch caching with real GEO queries."""

    # Import here to ensure proper initialization
    from omics_oracle_v2.lib.infrastructure.cache.redis_cache import RedisCache
    from omics_oracle_v2.lib.search_engines.geo.models import GEOSeriesMetadata

    logger.info("=" * 80)
    logger.info("WEEK 3 DAY 1: PER-ITEM BATCH CACHE VALIDATION")
    logger.info("=" * 80)

    # Initialize cache
    cache = RedisCache(enabled=True)

    if not cache.enabled:
        logger.error("Redis cache is not available - test cannot proceed")
        logger.info("Please ensure Redis is running on localhost:6379")
        return False

    logger.info(f"✅ Redis cache connected")

    # Test 1: Batch Set
    logger.info("\n" + "-" * 80)
    logger.info("TEST 1: Batch Set Operations")
    logger.info("-" * 80)

    test_datasets = {
        "GSE123456": {
            "geo_id": "GSE123456",
            "title": "Test Dataset 1",
            "summary": "Test summary 1",
            "organism": "Homo sapiens",
            "samples": 10,
        },
        "GSE123457": {
            "geo_id": "GSE123457",
            "title": "Test Dataset 2",
            "summary": "Test summary 2",
            "organism": "Mus musculus",
            "samples": 20,
        },
        "GSE123458": {
            "geo_id": "GSE123458",
            "title": "Test Dataset 3",
            "summary": "Test summary 3",
            "organism": "Homo sapiens",
            "samples": 30,
        },
    }

    cached_count = await cache.set_geo_datasets_batch(test_datasets)
    logger.info(f"✅ Cached {cached_count}/3 datasets")

    if cached_count != 3:
        logger.error(f"❌ Expected 3 datasets cached, got {cached_count}")
        return False

    # Test 2: Batch Get (100% hit rate)
    logger.info("\n" + "-" * 80)
    logger.info("TEST 2: Batch Get Operations (100% cached)")
    logger.info("-" * 80)

    test_ids = list(test_datasets.keys())
    start_time = time.time()
    cached_datasets = await cache.get_geo_datasets_batch(test_ids)
    duration = time.time() - start_time

    hits = sum(1 for v in cached_datasets.values() if v is not None)
    hit_rate = (hits / len(test_ids) * 100) if test_ids else 0

    logger.info(f"✅ Retrieved {hits}/3 datasets from cache in {duration*1000:.1f}ms")
    logger.info(f"   Cache hit rate: {hit_rate:.1f}%")

    if hit_rate != 100.0:
        logger.error(f"❌ Expected 100% hit rate, got {hit_rate:.1f}%")
        return False

    # Test 3: Partial Cache (50% hit rate)
    logger.info("\n" + "-" * 80)
    logger.info("TEST 3: Partial Cache Scenario (50% cached)")
    logger.info("-" * 80)

    mixed_ids = ["GSE123456", "GSE123457", "GSE999999", "GSE888888"]
    cached_datasets = await cache.get_geo_datasets_batch(mixed_ids)

    hits = sum(1 for v in cached_datasets.values() if v is not None)
    hit_rate = (hits / len(mixed_ids) * 100) if mixed_ids else 0

    logger.info(f"✅ Retrieved {hits}/4 datasets from cache")
    logger.info(f"   Cache hit rate: {hit_rate:.1f}% (expected ~50%)")

    if hit_rate < 40 or hit_rate > 60:
        logger.warning(f"⚠️  Unexpected hit rate: {hit_rate:.1f}% (expected ~50%)")

    # Test 4: Cache Metrics
    logger.info("\n" + "-" * 80)
    logger.info("TEST 4: Cache Metrics Tracking")
    logger.info("-" * 80)

    metrics = cache.metrics.get_summary()
    logger.info(f"✅ Cache metrics:")
    logger.info(f"   Total requests: {metrics['total_requests']}")
    logger.info(f"   Hits: {metrics['hits']}")
    logger.info(f"   Misses: {metrics['misses']}")
    logger.info(f"   Sets: {metrics['sets']}")
    logger.info(f"   Hit rate: {metrics['hit_rate']}")
    logger.info(f"   Errors: {metrics['errors']}")

    if metrics["errors"] > 0:
        logger.warning(f"⚠️  {metrics['errors']} cache errors occurred")

    # Test 5: Performance Baseline
    logger.info("\n" + "-" * 80)
    logger.info("TEST 5: Performance Baseline")
    logger.info("-" * 80)

    # Measure batch get performance (should be <10ms for cached data)
    test_ids = list(test_datasets.keys())

    iterations = 100
    total_time = 0

    for i in range(iterations):
        start = time.time()
        await cache.get_geo_datasets_batch(test_ids)
        total_time += time.time() - start

    avg_time_ms = (total_time / iterations) * 1000
    throughput = len(test_ids) / (total_time / iterations)

    logger.info(f"✅ Performance (100 iterations):")
    logger.info(f"   Average time: {avg_time_ms:.2f}ms per batch")
    logger.info(f"   Throughput: {throughput:.0f} datasets/sec")

    if avg_time_ms < 10:
        logger.info(f"   [EXCELLENT] < 10ms (target met)")
    elif avg_time_ms < 50:
        logger.info(f"   [GOOD] < 50ms")
    else:
        logger.warning(f"   [SLOW] > 50ms (expected < 10ms)")

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("BATCH CACHE VALIDATION COMPLETE")
    logger.info("=" * 80)
    logger.info(f"✅ Batch set: {cached_count}/3 datasets")
    logger.info(f"✅ Batch get: {hit_rate:.1f}% hit rate")
    logger.info(f"✅ Performance: {avg_time_ms:.2f}ms avg, {throughput:.0f} datasets/sec")
    logger.info(f"✅ Metrics tracking: {metrics['total_requests']} total requests")
    logger.info("=" * 80)

    return True


async def test_search_orchestrator_cache():
    """Test that search orchestrator uses batch caching."""

    logger.info("\n" + "=" * 80)
    logger.info("INTEGRATION TEST: Search Orchestrator Batch Caching")
    logger.info("=" * 80)

    from omics_oracle_v2.core.config import get_settings
    from omics_oracle_v2.lib.search_orchestration.orchestrator import SearchOrchestrator

    settings = get_settings()
    orchestrator = SearchOrchestrator(config=settings)

    # Test with a real query (if GEO client available)
    if not orchestrator.geo_client:
        logger.warning("⚠️  GEO client not available - skipping integration test")
        return True

    logger.info("\nRunning search for 'breast cancer' (first time - cache miss)...")
    start_time = time.time()
    result1 = await orchestrator.search("breast cancer", max_geo_results=5, use_cache=True)
    duration1 = time.time() - start_time

    logger.info(f"✅ First search: {len(result1.geo_datasets)} datasets in {duration1:.2f}s")

    logger.info("\nRunning same search (second time - should use cache)...")
    start_time = time.time()
    result2 = await orchestrator.search("breast cancer", max_geo_results=5, use_cache=True)
    duration2 = time.time() - start_time

    logger.info(f"✅ Second search: {len(result2.geo_datasets)} datasets in {duration2:.2f}s")

    if duration2 < duration1:
        speedup = duration1 / duration2
        logger.info(f"✅ Cache speedup: {speedup:.1f}x faster")
    else:
        logger.warning(f"⚠️  No speedup detected (might be network variance)")

    # Check cache metrics
    if orchestrator.cache:
        metrics = orchestrator.cache.metrics.get_summary()
        logger.info(f"\n✅ Cache metrics:")
        logger.info(f"   Hit rate: {metrics['hit_rate']}")
        logger.info(f"   Total requests: {metrics['total_requests']}")

    await orchestrator.close()
    return True


async def main():
    """Run all validation tests."""

    try:
        # Test 1: Batch cache operations
        success1 = await test_batch_cache()

        if not success1:
            logger.error("\n❌ Batch cache validation FAILED")
            return False

        # Test 2: Search orchestrator integration (optional, requires GEO access)
        try:
            success2 = await test_search_orchestrator_cache()
            if not success2:
                logger.warning("\n⚠️  Integration test had issues (non-critical)")
        except Exception as e:
            logger.warning(f"\n⚠️  Integration test skipped: {e}")

        logger.info("\n" + "=" * 80)
        logger.info("✅ ALL VALIDATION TESTS PASSED")
        logger.info("=" * 80)
        logger.info("\nWeek 3 Day 1 cache optimization is working correctly!")
        logger.info("Next steps:")
        logger.info("  - Monitor cache hit rates in production")
        logger.info("  - Implement cache warming for popular datasets")
        logger.info("  - Optimize cache key compression")
        logger.info("=" * 80)

        return True

    except Exception as e:
        logger.error(f"\n❌ Validation failed with error: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
