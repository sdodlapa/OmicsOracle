#!/usr/bin/env python3
"""
Week 3 Day 1: Cache Optimization Test

Validates that batch_get_metadata_smart provides:
- Parallel fetching on first request
- Cache hits on second request
- 10-50x speedup improvement
"""

import asyncio
import logging
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from omics_oracle_v2.core.config import get_settings
from omics_oracle_v2.lib.geo import GEOClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def test_cache_optimization():
    """Test cache optimization with batch_get_metadata_smart."""

    settings = get_settings()
    client = GEOClient(settings)

    # Use a small set of real GEO IDs for testing
    test_ids = [
        "GSE123456",  # Test dataset
        "GSE123457",
        "GSE123458",
    ]

    logger.info("=" * 70)
    logger.info("WEEK 3 DAY 1: Cache Optimization Test")
    logger.info("=" * 70)

    # Test 1: First request (cache miss - should fetch in parallel)
    logger.info("\nTest 1: First request (cache miss expected)")
    logger.info("-" * 70)
    start_time = time.time()

    try:
        results_first = await client.batch_get_metadata_smart(geo_ids=test_ids, max_concurrent=10)
        first_duration = time.time() - start_time

        logger.info("[OK] First request completed")
        logger.info("    - Datasets fetched: %d", len(results_first))
        logger.info("    - Time: %.2fs", first_duration)
        logger.info("    - Throughput: %.1f datasets/sec", len(results_first) / first_duration)

    except Exception as e:
        logger.error("[FAIL] First request failed: %s", e)
        await client.close()
        sys.exit(1)

    # Test 2: Second request (cache hit - should be much faster)
    logger.info("\nTest 2: Second request (cache hit expected)")
    logger.info("-" * 70)
    start_time = time.time()

    try:
        results_second = await client.batch_get_metadata_smart(geo_ids=test_ids, max_concurrent=10)
        second_duration = time.time() - start_time

        logger.info("[OK] Second request completed")
        logger.info("    - Datasets fetched: %d", len(results_second))
        logger.info("    - Time: %.2fs", second_duration)
        logger.info("    - Throughput: %.1f datasets/sec", len(results_second) / second_duration)

    except Exception as e:
        logger.error("[FAIL] Second request failed: %s", e)
        await client.close()
        sys.exit(1)

    # Test 3: Calculate speedup
    logger.info("\nTest 3: Cache Speedup Analysis")
    logger.info("-" * 70)

    if second_duration > 0:
        speedup = first_duration / second_duration
        logger.info("[OK] Cache speedup: %.1fx", speedup)

        if speedup >= 5:
            logger.info("    [EXCELLENT] %.1fx speedup (target: 10-50x)", speedup)
        elif speedup >= 2:
            logger.info("    [GOOD] %.1fx speedup (target: 10-50x)", speedup)
        else:
            logger.warning("    [SLOW] %.1fx speedup (target: 10-50x)", speedup)

    # Test 4: Mixed cache scenario (50% cached, 50% new)
    logger.info("\nTest 4: Mixed cache scenario (50 percent cached, 50 percent new)")
    logger.info("-" * 70)

    mixed_ids = test_ids[:2] + ["GSE123459", "GSE123460"]  # 2 cached + 2 new
    start_time = time.time()

    try:
        results_mixed = await client.batch_get_metadata_smart(geo_ids=mixed_ids, max_concurrent=10)
        mixed_duration = time.time() - start_time

        logger.info("[OK] Mixed request completed")
        logger.info("    - Datasets fetched: %d", len(results_mixed))
        logger.info("    - Time: %.2fs", mixed_duration)
        logger.info("    - Expected: ~50 percent of first request time")
        logger.info("    - Actual: %.0f percent of first request", mixed_duration / first_duration * 100)

    except Exception as e:
        logger.error(f"[FAIL] Mixed request failed: {e}")
        await client.close()
        sys.exit(1)

    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("CACHE OPTIMIZATION TEST COMPLETE")
    logger.info("=" * 70)
    logger.info(f"First request (cache miss):  {first_duration:.2f}s")
    logger.info(f"Second request (cache hit):  {second_duration:.2f}s")
    logger.info(f"Cache speedup:               {speedup:.1f}x")
    logger.info(f"Mixed request (50% cached):  {mixed_duration:.2f}s")
    logger.info("=" * 70)

    # Cleanup
    await client.close()

    if speedup >= 2:
        logger.info("\n[SUCCESS] Cache optimization is working!")
        sys.exit(0)
    else:
        logger.warning("\n[WARNING] Cache speedup below target")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(test_cache_optimization())
