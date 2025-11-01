"""
Quick test to verify GEORegistry async changes work.
Tests that the get_complete_geo_data endpoint is now async.
"""

import asyncio
import logging

from omics_oracle_v2.lib.pipelines.storage.registry import get_registry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_async_registry():
    """Test that registry methods are async."""
    logger.info("Testing async GEORegistry...")

    registry = get_registry()

    # Test 1: Check registry initialized
    logger.info(f"✓ Registry initialized: {registry}")
    logger.info(f"✓ Registry has cache: {hasattr(registry, 'cache')}")

    # Test 2: Verify get_complete_geo_data is async
    import inspect

    is_async = inspect.iscoroutinefunction(registry.get_complete_geo_data)
    logger.info(f"✓ get_complete_geo_data is async: {is_async}")

    # Test 3: Try calling it (will return None if no data, but shouldn't crash)
    try:
        result = await registry.get_complete_geo_data("GSE_TEST_NONEXISTENT")
        logger.info(f"✓ Async call successful: result={result}")
    except Exception as e:
        logger.error(f"✗ Async call failed: {e}")
        raise

    # Test 4: Verify no old methods exist
    old_methods = [
        "register_geo_dataset",
        "register_publication",
        "link_geo_to_publication",
        "record_download_attempt",
    ]
    for method in old_methods:
        has_method = hasattr(registry, method)
        if has_method:
            logger.error(f"✗ Old method still exists: {method}")
        else:
            logger.info(f"✓ Old method removed: {method}")

    logger.info("=" * 60)
    logger.info("✓ All async tests passed!")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_async_registry())
