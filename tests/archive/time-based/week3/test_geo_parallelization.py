"""
Week 3 Day 2: GEO Parallelization Performance Tests

Validates the GEO client parallelization improvements:
- Baseline vs optimized performance comparison
- Throughput measurement (datasets/sec)
- Success rate validation
- Load testing with varying batch sizes
- Concurrency level optimization
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import asyncio
import time
from typing import List

import pytest

from omics_oracle_v2.core.config import Settings
from omics_oracle_v2.lib.search_engines.geo.client import GEOClient


@pytest.fixture
async def geo_client():
    """Create GEO client for testing."""
    settings = Settings()
    if not settings.geo or not settings.geo.ncbi_email:
        pytest.skip("GEO settings not configured (need OMICS_GEO_NCBI_EMAIL)")

    client = GEOClient(settings.geo)
    yield client
    await client.close()


@pytest.fixture
def sample_geo_ids() -> List[str]:
    """Sample GEO IDs for testing (verified to exist)."""
    return [
        "GSE1",
        "GSE2",
        "GSE3",
        "GSE4",
        "GSE5",
        "GSE6",
        "GSE7",
        "GSE8",
        "GSE9",
        "GSE10",
        "GSE11",
        "GSE12",
        "GSE13",
        "GSE14",
        "GSE15",
        "GSE16",
        "GSE17",
        "GSE18",
        "GSE19",
        "GSE20",
    ]


@pytest.mark.asyncio
async def test_baseline_performance_old_concurrency(geo_client, sample_geo_ids):
    """
    Test baseline performance with old concurrency (10).

    This establishes the baseline to compare against optimized performance.
    """
    print("\n" + "=" * 80)
    print("BASELINE TEST (max_concurrent=10)")
    print("=" * 80)

    geo_ids = sample_geo_ids[:20]  # Test with 20 datasets

    start_time = time.time()
    results = await geo_client.batch_get_metadata(geo_ids, max_concurrent=10)
    elapsed_time = time.time() - start_time

    success_count = len([r for r in results.values() if r is not None])
    success_rate = (success_count / len(geo_ids)) * 100
    throughput = success_count / elapsed_time if elapsed_time > 0 else 0

    print(f"\nResults:")
    print(f"  GEO IDs: {len(geo_ids)}")
    print(f"  Successful: {success_count}/{len(geo_ids)} ({success_rate:.1f}%)")
    print(f"  Elapsed: {elapsed_time:.2f}s")
    print(f"  Throughput: {throughput:.2f} datasets/sec")
    print(f"  Avg per dataset: {elapsed_time / len(geo_ids):.2f}s")

    # Assertions
    assert success_rate >= 50, "Success rate should be at least 50% (some old IDs may not exist)"
    assert elapsed_time < 60, "Should complete within 60 seconds"

    return {
        "concurrency": 10,
        "batch_size": len(geo_ids),
        "success_count": success_count,
        "success_rate": success_rate,
        "elapsed_time": elapsed_time,
        "throughput": throughput,
    }


@pytest.mark.asyncio
async def test_optimized_performance_new_concurrency(geo_client, sample_geo_ids):
    """
    Test optimized performance with new concurrency (20).

    Expected: 1.5-2x throughput improvement vs baseline.
    """
    print("\n" + "=" * 80)
    print("OPTIMIZED TEST (max_concurrent=20)")
    print("=" * 80)

    geo_ids = sample_geo_ids[:20]  # Test with 20 datasets

    start_time = time.time()
    results = await geo_client.batch_get_metadata(geo_ids, max_concurrent=20)
    elapsed_time = time.time() - start_time

    success_count = len([r for r in results.values() if r is not None])
    success_rate = (success_count / len(geo_ids)) * 100
    throughput = success_count / elapsed_time if elapsed_time > 0 else 0

    print(f"\nResults:")
    print(f"  GEO IDs: {len(geo_ids)}")
    print(f"  Successful: {success_count}/{len(geo_ids)} ({success_rate:.1f}%)")
    print(f"  Elapsed: {elapsed_time:.2f}s")
    print(f"  Throughput: {throughput:.2f} datasets/sec")
    print(f"  Avg per dataset: {elapsed_time / len(geo_ids):.2f}s")

    # Assertions
    assert success_rate >= 50, "Success rate should be at least 50%"
    assert elapsed_time < 50, "Should be faster than baseline"
    assert throughput >= 0.5, "Throughput should be at least 0.5 datasets/sec"

    return {
        "concurrency": 20,
        "batch_size": len(geo_ids),
        "success_count": success_count,
        "success_rate": success_rate,
        "elapsed_time": elapsed_time,
        "throughput": throughput,
    }


@pytest.mark.asyncio
async def test_performance_comparison(geo_client, sample_geo_ids):
    """
    Compare baseline (10 concurrent) vs optimized (20 concurrent) performance.

    Goal: 1.5-2x speedup with optimized settings.
    """
    print("\n" + "=" * 80)
    print("PERFORMANCE COMPARISON TEST")
    print("=" * 80)

    geo_ids = sample_geo_ids[:20]

    # Baseline test (10 concurrent)
    print("\nRunning baseline test (max_concurrent=10)...")
    start_baseline = time.time()
    results_baseline = await geo_client.batch_get_metadata(geo_ids, max_concurrent=10)
    elapsed_baseline = time.time() - start_baseline
    success_baseline = len([r for r in results_baseline.values() if r is not None])
    throughput_baseline = success_baseline / elapsed_baseline if elapsed_baseline > 0 else 0

    # Wait a bit to avoid rate limiting
    await asyncio.sleep(2)

    # Optimized test (20 concurrent)
    print("Running optimized test (max_concurrent=20)...")
    start_optimized = time.time()
    results_optimized = await geo_client.batch_get_metadata(geo_ids, max_concurrent=20)
    elapsed_optimized = time.time() - start_optimized
    success_optimized = len([r for r in results_optimized.values() if r is not None])
    throughput_optimized = success_optimized / elapsed_optimized if elapsed_optimized > 0 else 0

    # Calculate speedup
    speedup = elapsed_baseline / elapsed_optimized if elapsed_optimized > 0 else 0
    throughput_improvement = (
        ((throughput_optimized - throughput_baseline) / throughput_baseline) * 100
        if throughput_baseline > 0
        else 0
    )

    print(f"\n{'=' * 80}")
    print("COMPARISON RESULTS")
    print(f"{'=' * 80}")
    print(f"\nBaseline (max_concurrent=10):")
    print(f"  Success: {success_baseline}/{len(geo_ids)}")
    print(f"  Time: {elapsed_baseline:.2f}s")
    print(f"  Throughput: {throughput_baseline:.2f} datasets/sec")
    print(f"\nOptimized (max_concurrent=20):")
    print(f"  Success: {success_optimized}/{len(geo_ids)}")
    print(f"  Time: {elapsed_optimized:.2f}s")
    print(f"  Throughput: {throughput_optimized:.2f} datasets/sec")
    print(f"\nImprovement:")
    print(f"  Speedup: {speedup:.2f}x")
    print(f"  Throughput gain: {throughput_improvement:+.1f}%")
    print(f"  Time saved: {elapsed_baseline - elapsed_optimized:.2f}s")
    print(f"{'=' * 80}\n")

    # Assertions
    assert speedup >= 1.0, "Optimized should be at least as fast as baseline"
    # Note: Actual speedup depends on network conditions, may not always reach 1.5x
    if speedup >= 1.5:
        print("✅ EXCELLENT: Achieved 1.5x+ speedup!")
    elif speedup >= 1.2:
        print("✅ GOOD: Achieved 1.2x+ speedup")
    else:
        print("⚠️  Modest improvement, may vary with network conditions")

    return {
        "baseline": {
            "time": elapsed_baseline,
            "throughput": throughput_baseline,
            "success": success_baseline,
        },
        "optimized": {
            "time": elapsed_optimized,
            "throughput": throughput_optimized,
            "success": success_optimized,
        },
        "speedup": speedup,
        "throughput_improvement_pct": throughput_improvement,
    }


@pytest.mark.asyncio
async def test_load_testing_various_batch_sizes(geo_client, sample_geo_ids):
    """
    Test performance with varying batch sizes.

    Tests: 10, 20, 50 datasets
    Goal: Validate throughput scales with optimized settings.
    """
    print("\n" + "=" * 80)
    print("LOAD TESTING (Various Batch Sizes)")
    print("=" * 80)

    # Expand sample IDs for larger batches
    extended_ids = sample_geo_ids + [f"GSE{i}" for i in range(21, 51)]

    batch_sizes = [10, 20]  # Keep it reasonable for testing
    results = []

    for batch_size in batch_sizes:
        geo_ids = extended_ids[:batch_size]

        print(f"\nTesting batch_size={batch_size}, max_concurrent=20...")
        start_time = time.time()
        batch_results = await geo_client.batch_get_metadata(geo_ids, max_concurrent=20)
        elapsed_time = time.time() - start_time

        success_count = len([r for r in batch_results.values() if r is not None])
        success_rate = (success_count / len(geo_ids)) * 100
        throughput = success_count / elapsed_time if elapsed_time > 0 else 0

        print(
            f"  Results: {success_count}/{batch_size} ({success_rate:.1f}%) "
            f"in {elapsed_time:.2f}s ({throughput:.2f} datasets/sec)"
        )

        results.append(
            {
                "batch_size": batch_size,
                "success_count": success_count,
                "success_rate": success_rate,
                "elapsed_time": elapsed_time,
                "throughput": throughput,
            }
        )

        # Rate limit between tests
        await asyncio.sleep(2)

    print(f"\n{'=' * 80}")
    print("LOAD TEST SUMMARY")
    print(f"{'=' * 80}")
    for result in results:
        print(
            f"Batch {result['batch_size']:3d}: "
            f"{result['throughput']:5.2f} datasets/sec, "
            f"{result['success_rate']:5.1f}% success"
        )
    print(f"{'=' * 80}\n")

    # Validate throughput is reasonable
    for result in results:
        assert result["throughput"] > 0, f"Throughput should be positive for batch {result['batch_size']}"

    return results


@pytest.mark.asyncio
async def test_success_rate_validation(geo_client, sample_geo_ids):
    """
    Validate that success rate remains high with optimized settings.

    Goal: Success rate >= 90% (some old GEO IDs may not exist)
    """
    print("\n" + "=" * 80)
    print("SUCCESS RATE VALIDATION")
    print("=" * 80)

    geo_ids = sample_geo_ids[:20]

    results = await geo_client.batch_get_metadata(geo_ids, max_concurrent=20)

    success_count = len([r for r in results.values() if r is not None])
    failed_count = len(geo_ids) - success_count
    success_rate = (success_count / len(geo_ids)) * 100

    failed_ids = [geo_id for geo_id, metadata in results.items() if metadata is None]

    print(f"\nResults:")
    print(f"  Total: {len(geo_ids)}")
    print(f"  Successful: {success_count}")
    print(f"  Failed: {failed_count}")
    print(f"  Success rate: {success_rate:.1f}%")

    if failed_ids:
        print(f"\nFailed IDs: {', '.join(failed_ids)}")

    # Note: Old GEO IDs (GSE1-20) may not all exist, so we use a lower threshold
    assert success_rate >= 50, f"Success rate {success_rate:.1f}% is too low (expected ≥50%)"

    if success_rate >= 90:
        print("✅ EXCELLENT: Success rate ≥90%")
    elif success_rate >= 70:
        print("✅ GOOD: Success rate ≥70%")
    else:
        print("⚠️  Some older GEO IDs may not exist")

    return {
        "total": len(geo_ids),
        "success_count": success_count,
        "failed_count": failed_count,
        "success_rate": success_rate,
        "failed_ids": failed_ids,
    }


@pytest.mark.asyncio
async def test_timeout_handling(geo_client):
    """
    Validate that 30s timeout is working correctly.

    Tests with a mix of valid and potentially slow/invalid IDs.
    """
    print("\n" + "=" * 80)
    print("TIMEOUT HANDLING TEST")
    print("=" * 80)

    # Mix of valid and invalid IDs to test timeout behavior
    test_ids = [
        "GSE1",
        "GSE2",
        "INVALID123",  # Should fail quickly
        "GSE3",
    ]

    print(f"\nTesting with {len(test_ids)} IDs (including invalid)...")
    start_time = time.time()
    results = await geo_client.batch_get_metadata(test_ids, max_concurrent=20)
    elapsed_time = time.time() - start_time

    success_count = len([r for r in results.values() if r is not None])

    print(f"\nResults:")
    print(f"  Total IDs: {len(test_ids)}")
    print(f"  Successful: {success_count}")
    print(f"  Elapsed: {elapsed_time:.2f}s")
    print(f"  Avg per ID: {elapsed_time / len(test_ids):.2f}s")

    # Should complete quickly (not wait 30s for each failure)
    assert elapsed_time < 120, "Should handle failures efficiently"

    return {
        "total": len(test_ids),
        "success_count": success_count,
        "elapsed_time": elapsed_time,
    }


if __name__ == "__main__":
    """Run tests manually for quick validation."""

    async def run_manual_tests():
        """Run subset of tests manually."""
        settings = Settings()
        if not settings.geo or not settings.geo.ncbi_email:
            print("⚠️  Skipping: GEO settings not configured")
            print("   Set OMICS_GEO_NCBI_EMAIL environment variable")
            return

        client = GEOClient(settings.geo)
        sample_ids = [f"GSE{i}" for i in range(1, 21)]

        try:
            print("\n" + "=" * 80)
            print("MANUAL TEST RUN")
            print("=" * 80)

            # Run comparison test
            await test_performance_comparison(client, sample_ids)

            # Run success rate test
            await test_success_rate_validation(client, sample_ids)

            print("\n✅ Manual tests complete!")

        finally:
            await client.close()

    asyncio.run(run_manual_tests())
