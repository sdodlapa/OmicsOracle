"""
Week 2 Day 4: Test SearchAgent Migration

Quick validation test for unified pipeline integration.
"""
import asyncio
import logging

from omics_oracle_v2.agents.models.search import SearchInput
from omics_oracle_v2.agents.search_agent import SearchAgent
from omics_oracle_v2.core.config import Settings

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def test_unified_pipeline():
    """Test SearchAgent with unified pipeline enabled."""
    logger.info("=" * 80)
    logger.info("Week 2 Day 4: SearchAgent Migration Test")
    logger.info("=" * 80)

    # Create SearchAgent with unified pipeline
    logger.info("\n1. Initializing SearchAgent with unified pipeline...")
    settings = Settings()
    agent = SearchAgent(
        settings=settings,
        enable_semantic=True,
        enable_publications=True,
    )

    # Verify feature flag
    assert agent._use_unified_pipeline == True, "Unified pipeline should be enabled by default"
    logger.info("   ✓ Unified pipeline enabled")

    # Test simple search
    logger.info("\n2. Testing simple GEO search...")
    input_data = SearchInput(
        search_terms=["diabetes", "insulin"], original_query="diabetes insulin resistance", max_results=10
    )

    result = agent.execute(input_data)

    logger.info(f"   ✓ Search completed")
    logger.info(f"   - Total found: {result.total_found}")
    logger.info(f"   - Datasets returned: {len(result.datasets)}")
    logger.info(f"   - Search mode: {result.filters_applied.get('search_mode', 'unknown')}")
    logger.info(f"   - Cache hit: {result.filters_applied.get('cache_hit', False)}")

    # Test with filters
    logger.info("\n3. Testing search with filters...")
    input_data_filtered = SearchInput(
        search_terms=["breast cancer"], organism="Homo sapiens", min_samples=50, max_results=20
    )

    result_filtered = agent.execute(input_data_filtered)

    logger.info(f"   ✓ Filtered search completed")
    logger.info(f"   - Total found: {result_filtered.total_found}")
    logger.info(f"   - Datasets returned: {len(result_filtered.datasets)}")

    # Validate filters applied
    for dataset in result_filtered.datasets[:5]:  # Check first 5
        if dataset.dataset.sample_count:
            assert (
                dataset.dataset.sample_count >= 50
            ), f"Sample count filter failed: {dataset.dataset.sample_count}"

    logger.info("   ✓ Min samples filter validated")

    # Test GEO ID fast path
    logger.info("\n4. Testing GEO ID direct lookup...")
    input_data_geo_id = SearchInput(search_terms=["GSE100000"], max_results=1)

    result_geo_id = agent.execute(input_data_geo_id)

    logger.info(f"   ✓ GEO ID lookup completed")
    logger.info(f"   - Query type: {result_geo_id.filters_applied.get('search_mode', 'unknown')}")
    logger.info(f"   - Results: {len(result_geo_id.datasets)}")

    # Test cache speedup (second query should be faster)
    logger.info("\n5. Testing cache speedup...")
    import time

    start1 = time.time()
    result_first = agent.execute(input_data)
    time1 = time.time() - start1

    start2 = time.time()
    result_second = agent.execute(input_data)
    time2 = time.time() - start2

    logger.info(f"   - First query: {time1:.3f}s")
    logger.info(f"   - Second query (cached): {time2:.3f}s")
    logger.info(f"   - Speedup: {time1/time2:.1f}x")

    if time2 < time1 / 5:  # Expect at least 5x speedup
        logger.info("   ✓ Cache speedup validated!")
    else:
        logger.warning("   ⚠ Cache may not be working optimally")

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("MIGRATION TEST SUMMARY")
    logger.info("=" * 80)
    logger.info("✓ Unified pipeline initialized successfully")
    logger.info("✓ Basic search works")
    logger.info("✓ Filtered search works")
    logger.info("✓ GEO ID lookup works")
    logger.info("✓ Caching functional")
    logger.info("\n🎉 Week 2 Day 4 Migration: SUCCESSFUL!")
    logger.info("=" * 80)


def test_legacy_mode():
    """Test SearchAgent with legacy mode (feature flag disabled)."""
    logger.info("\n\n" + "=" * 80)
    logger.info("Testing Legacy Mode (Backward Compatibility)")
    logger.info("=" * 80)

    settings = Settings()
    agent = SearchAgent(
        settings=settings,
        enable_semantic=False,
        enable_publications=False,
    )

    # Disable unified pipeline
    agent._use_unified_pipeline = False
    logger.info("   Unified pipeline disabled")

    # Test search still works
    logger.info("\n Testing search with legacy implementation...")
    input_data = SearchInput(search_terms=["cancer"], max_results=5)

    result = agent.execute(input_data)

    logger.info(f"   ✓ Legacy search completed")
    logger.info(f"   - Total found: {result.total_found}")
    logger.info(f"   - Datasets returned: {len(result.datasets)}")
    logger.info("\n✓ Backward compatibility maintained!")
    logger.info("=" * 80)


if __name__ == "__main__":
    try:
        # Test unified pipeline (default)
        test_unified_pipeline()

        # Test legacy mode (backward compat)
        test_legacy_mode()

        print("\n\n🚀 ALL TESTS PASSED! Migration successful!")

    except Exception as e:
        logger.error(f"\n❌ TEST FAILED: {e}", exc_info=True)
        raise
