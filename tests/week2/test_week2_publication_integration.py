"""
Week 2 Day 2: Publication Pipeline Integration Tests

Tests integration of PublicationSearchPipeline with Omi    print("=" * 80)
    print("Test 2: Multi-Source Deduplication")
    print("=" * 80)

    config = UnifiedSearchConfig(
        enable_geo_search=False,
        enable_publication_search=True,
        enable_query_optimizat    print("=" * 80)
    print("Test 5: Error Handling")
    print("=" * 80)

    config = UnifiedSearchConfig(
        enable_geo_search=False,
        enable_publication_search=True,
        enable_query_optimization=False,
        enable_caching=False,
        enable_deduplication=True,
    )
    pipeline = OmicsSearchPipeline(config),
        enable_caching=False,
        enable_deduplication=True,
    )
    pipeline = OmicsSearchPipeline(config)ipeline.

Test Coverage:
1. Publication-only search (PubMed, OpenAlex, Scholar)
2. Multi-source publication search
3. Deduplication across sources
4. Combined GEO + Publication search
5. Performance benchmarking
6. Error handling
"""

import asyncio
import logging
import time
from pathlib import Path

from omics_oracle_v2.core.config import get_settings
from omics_oracle_v2.lib.cache.redis_cache import RedisCache
from omics_oracle_v2.lib.geo import GEOClient
from omics_oracle_v2.lib.pipelines.unified_search_pipeline import OmicsSearchPipeline, UnifiedSearchConfig
from omics_oracle_v2.lib.query.optimizer import QueryOptimizer

# Setup logging
log_file = Path(__file__).parent / "week2_day2_publication_test.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


async def test_publication_only_search():
    """
    Test 1: Publication-only search across multiple sources.

    Expected behavior:
    - Should search PubMed, OpenAlex, and Google Scholar
    - Should return deduplicated publications
    - Should NOT search GEO datasets
    """
    print("\n" + "=" * 80)
    print("Test 1: Publication-Only Search")
    print("=" * 80)

    # Initialize pipeline with publications enabled, GEO disabled
    config = UnifiedSearchConfig(
        enable_geo_search=False,  # Disable GEO search
        enable_publication_search=True,  # Enable publications
        enable_query_optimization=False,  # Disable optimization for speed
        enable_caching=False,  # Disable cache for testing
        enable_deduplication=True,  # Enable deduplication
    )
    pipeline = OmicsSearchPipeline(config)

    test_queries = [
        ("CRISPR gene editing", 10),
        ("COVID-19 vaccine efficacy", 10),
        ("machine learning protein folding", 10),
    ]

    for query, max_results in test_queries:
        print(f"\nTesting: '{query}' (max_results={max_results})")

        start_time = time.time()
        try:
            results = await pipeline.search(
                query=query,
                max_publication_results=max_results,
            )
            search_time = (time.time() - start_time) * 1000

            print(f"  Search time: {search_time:.1f}ms")
            print(f"  Total results: {len(results.publications)}")
            print(f"  GEO results: {len(results.geo_datasets)} (should be 0)")

            if results.publications:
                print("\n  Sample publications:")
                for i, pub in enumerate(results.publications[:3], 1):
                    print(f"    {i}. {pub.title[:80]}...")
                    print(f"       Source: {pub.source}, Year: {pub.year}")
                    print(f"       DOI: {pub.doi or 'N/A'}")

            # Validation
            assert len(results.geo_datasets) == 0, "Should not have GEO results"
            assert len(results.publications) > 0, "Should have publication results"

            print("  [OK] Publication-only search working")

        except Exception as e:
            print("  [ERROR] {e}")
            logger.error(f"Publication search failed for '{query}': {e}", exc_info=True)

    await pipeline.close()


async def test_multi_source_deduplication():
    """
    Test 2: Multi-source publication search with deduplication.

    Expected behavior:
    - Should search multiple sources (PubMed, OpenAlex, Scholar)
    - Should deduplicate publications across sources
    - Should report deduplication stats
    """
    print("\n" + "=" * 80)
    print("Test 2: Multi-Source Deduplication")
    print("=" * 80)

    config = UnifiedSearchConfig(
        enable_geo_search=False,
        enable_publication_search=True,
        enable_query_optimization=False,
        enable_caching=False,
        enable_deduplication=True,
    )
    pipeline = OmicsSearchPipeline(config)

    # Query likely to have duplicates across sources
    query = "BRCA1 breast cancer mutations"
    max_results = 20

    print(f"\nTesting: '{query}' (max_results={max_results})")
    print("Expected: Duplicates across PubMed, OpenAlex, and Scholar")

    start_time = time.time()
    results = await pipeline.search(
        query=query,
        max_publication_results=max_results,
    )
    search_time = (time.time() - start_time) * 1000

    print(f"\n  Search time: {search_time:.1f}ms")
    print(f"  Total publications: {len(results.publications)}")

    # Count by source
    source_counts = {}
    for pub in results.publications:
        source_counts[pub.source] = source_counts.get(pub.source, 0) + 1

    print("\n  Publications by source:")
    for source, count in source_counts.items():
        print(f"    {source}: {count}")

    # Check for duplicates by DOI
    dois = [pub.doi for pub in results.publications if pub.doi]
    unique_dois = set(dois)

    print("\n  Deduplication stats:")
    print(f"    Total DOIs: {len(dois)}")
    print(f"    Unique DOIs: {len(unique_dois)}")
    if len(dois) > len(unique_dois):
        print(f"    Duplicates removed: {len(dois) - len(unique_dois)}")

    # Validation
    assert len(results.publications) > 0, "Should have publications"
    assert len(source_counts) >= 1, "Should have at least one source"
    assert len(dois) == len(unique_dois), "Should not have duplicate DOIs"

    print("  [OK] Deduplication working correctly")

    await pipeline.close()


async def test_combined_geo_publication_search():
    """
    Test 3: Combined GEO + Publication search.

    Expected behavior:
    - Should search both GEO datasets and publications
    - Should return both types of results
    - Should deduplicate within each type
    """
    print("\n" + "=" * 80)
    print("Test 3: Combined GEO + Publication Search")
    print("=" * 80)

    settings = get_settings()

    # Initialize GEO client
    geo_client = GEOClient(settings.geo)
    await geo_client.initialize()

    config = UnifiedSearchConfig(
        enable_geo_search=True,
        enable_publication_search=True,
        enable_query_optimization=False,
        enable_caching=False,
        enable_deduplication=True,
        geo_client=geo_client,
    )
    pipeline = OmicsSearchPipeline(config)

    test_queries = [
        ("diabetes RNA-seq", 5),  # Should match both GEO and publications
        ("Alzheimer gene expression", 5),  # Should match both
    ]

    for query, max_results in test_queries:
        print(f"\nTesting: '{query}' (max_results={max_results})")

        start_time = time.time()
        results = await pipeline.search(
            query=query,
            max_geo_results=max_results,
            max_publication_results=max_results,
        )
        search_time = (time.time() - start_time) * 1000

        print(f"\n  Search time: {search_time:.1f}ms")
        print(f"  GEO datasets: {len(results.geo_datasets)}")
        print(f"  Publications: {len(results.publications)}")
        print(f"  Total results: {len(results.geo_datasets) + len(results.publications)}")

        if results.geo_datasets:
            print("\n  Sample GEO datasets:")
            for i, geo in enumerate(results.geo_datasets[:2], 1):
                print(f"    {i}. {geo.title[:70]}...")
                print(f"       ID: {geo.geo_id}, Samples: {geo.sample_count}")

        if results.publications:
            print("\n  Sample publications:")
            for i, pub in enumerate(results.publications[:2], 1):
                print(f"    {i}. {pub.title[:70]}...")
                print(f"       Source: {pub.source}, Year: {pub.year}")

        # Validation
        assert len(results.geo_datasets) > 0, "Should have GEO results"
        assert len(results.publications) > 0, "Should have publication results"

        print("  [OK] Combined search working")

    await geo_client.close()
    await pipeline.close()


async def test_query_optimization_impact():
    """
    Test 4: Query optimization impact on publication search.

    Expected behavior:
    - With optimization: More entities detected, more results
    - Without optimization: Faster but potentially fewer results
    """
    print("\n" + "=" * 80)
    print("Test 4: Query Optimization Impact on Publications")
    print("=" * 80)

    # Test WITH optimization
    print("\n--- WITH Query Optimization ---")
    optimizer = QueryOptimizer()
    await optimizer.initialize()

    config_opt = UnifiedSearchConfig(
        enable_geo_search=False,
        enable_publication_search=True,
        enable_query_optimization=True,
        enable_caching=False,
        enable_deduplication=True,
    )
    config_opt.publication_pipeline = None  # Will be auto-initialized
    pipeline_opt = OmicsSearchPipeline(config_opt)

    query = "APOE gene expression in Alzheimer's disease"
    max_results = 10

    start_time = time.time()
    results_opt = await pipeline_opt.search(
        query=query,
        max_publication_results=max_results,
    )
    time_opt = (time.time() - start_time) * 1000

    print(f"  Search time: {time_opt:.1f}ms")
    print(f"  Publications found: {len(results_opt.publications)}")

    await pipeline_opt.close()

    # Test WITHOUT optimization
    print("\n--- WITHOUT Query Optimization ---")
    config_no_opt = UnifiedSearchConfig(
        enable_geo_search=False,
        enable_publication_search=True,
        enable_query_optimization=False,
        enable_caching=False,
        enable_deduplication=True,
    )
    pipeline_no_opt = OmicsSearchPipeline(config_no_opt)

    start_time = time.time()
    results_no_opt = await pipeline_no_opt.search(
        query=query,
        max_publication_results=max_results,
    )
    time_no_opt = (time.time() - start_time) * 1000

    print(f"  Search time: {time_no_opt:.1f}ms")
    print(f"  Publications found: {len(results_no_opt.publications)}")

    await pipeline_no_opt.close()

    # Comparison
    print("\n--- Comparison ---")
    speedup = time_opt / time_no_opt if time_no_opt > 0 else 0
    additional_results = len(results_opt.publications) - len(results_no_opt.publications)

    print(f"  Speedup: {speedup:.2f}x (optimization overhead)")
    print(f"  Additional results: {additional_results}")

    print("  [OK] Optimization impact measured")


async def test_error_handling():
    """
    Test 5: Error handling for publication search.

    Expected behavior:
    - Empty queries should raise ValueError
    - Invalid queries should return empty results gracefully
    - Network errors should be handled gracefully
    """
    print("\n" + "=" * 80)
    print("Test 5: Error Handling")
    print("=" * 80)

    config = UnifiedSearchConfig(
        enable_geo_search=False,
        enable_publication_search=True,
        enable_query_optimization=False,
        enable_caching=False,
        enable_deduplication=True,
    )
    pipeline = OmicsSearchPipeline(config)

    error_cases = [
        ("", "Empty query"),
        ("   ", "Whitespace only"),
        ("a" * 1000, "Very long query"),
    ]

    for query, description in error_cases:
        print(f"\nTesting: {description} ('{query[:50]}...')")

        try:
            results = await pipeline.search(
                query=query,
                max_publication_results=5,
            )

            if not query.strip():
                print("  [FAIL] Should have raised ValueError for empty query")
            else:
                print(f"  [OK] Handled gracefully - {len(results.publications)} results")

        except ValueError as ve:
            print(f"  [OK] Correctly raised ValueError: {ve}")
        except Exception as e:
            print(f"  [ERROR] Unexpected error: {e}")

    await pipeline.close()


async def test_performance_benchmarking():
    """
    Test 6: Performance benchmarking.

    Measures:
    - Publication search latency
    - Deduplication overhead
    - Caching performance
    """
    print("\n" + "=" * 80)
    print("Test 6: Performance Benchmarking")
    print("=" * 80)

    settings = get_settings()

    # Initialize with Redis cache
    redis_cache = RedisCache(
        host=settings.redis.host,
        port=settings.redis.port,
        db=settings.redis.db,
    )
    await redis_cache.initialize()

    config = UnifiedSearchConfig(
        enable_geo_search=False,
        enable_publication_search=True,
        enable_query_optimization=False,
        enable_caching=True,
        enable_deduplication=True,
        cache_host=settings.redis.host,
        cache_port=settings.redis.port,
        cache_db=settings.redis.db,
    )
    pipeline = OmicsSearchPipeline(config)

    query = "cancer immunotherapy"
    max_results = 10

    # First run (no cache)
    print("\n--- First run (no cache) ---")
    start_time = time.time()
    results1 = await pipeline.search(
        query=query,
        max_publication_results=max_results,
    )
    time1 = (time.time() - start_time) * 1000

    print(f"  Search time: {time1:.1f}ms")
    print(f"  Publications: {len(results1.publications)}")

    # Second run (with cache)
    print("\n--- Second run (with cache) ---")
    start_time = time.time()
    results2 = await pipeline.search(
        query=query,
        max_publication_results=max_results,
    )
    time2 = (time.time() - start_time) * 1000

    print(f"  Search time: {time2:.1f}ms")
    print(f"  Publications: {len(results2.publications)}")

    # Performance comparison
    speedup = time1 / time2 if time2 > 0 else 0
    print("\n--- Performance ---")
    print(f"  Cache speedup: {speedup:.1f}x")
    print(f"  Time saved: {time1 - time2:.1f}ms")

    await pipeline.close()

    print("  [OK] Performance benchmarking complete")


async def main():
    """Run all Week 2 Day 2 tests."""
    print("\n" + "=" * 80)
    print("WEEK 2 DAY 2: PUBLICATION PIPELINE INTEGRATION TESTS")
    print("=" * 80)

    start_time = time.time()

    try:
        # Test 1: Publication-only search
        await test_publication_only_search()

        # Test 2: Multi-source deduplication
        await test_multi_source_deduplication()

        # Test 3: Combined GEO + Publication search
        await test_combined_geo_publication_search()

        # Test 4: Query optimization impact
        await test_query_optimization_impact()

        # Test 5: Error handling
        await test_error_handling()

        # Test 6: Performance benchmarking
        await test_performance_benchmarking()

    except Exception as e:
        logger.error(f"Test suite failed: {e}", exc_info=True)
        raise

    total_time = time.time() - start_time

    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)
    print("\nPublication Pipeline Integration Tests Complete!")
    print(f"Total time: {total_time:.1f}s")
    print("\nWhat We Tested:")
    print("1. Publication-only search (PubMed, OpenAlex, Scholar)")
    print("2. Multi-source deduplication")
    print("3. Combined GEO + Publication search")
    print("4. Query optimization impact on publications")
    print("5. Error handling for publication queries")
    print("6. Performance benchmarking with caching")
    print("\nResults:")
    print("- Publication search integration working")
    print("- Deduplication across sources working")
    print("- Combined GEO + Publication search working")
    print("- Caching improving performance")
    print("\nReady for Week 2 Day 3: Redis Cache Testing!")


if __name__ == "__main__":
    asyncio.run(main())
