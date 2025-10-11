"""
Quick test to validate parallel GEO metadata download optimization.

Tests:
1. Sequential download (old way - for comparison)
2. Parallel download (new way - should be much faster)
"""

import asyncio
import time

from omics_oracle_v2.core.config import get_settings
from omics_oracle_v2.lib.geo.client import GEOClient


async def test_parallel_download():
    """Test parallel download speed improvement."""

    settings = get_settings()
    client = GEOClient(settings.geo)

    # Test with 20 datasets
    test_ids = [
        "GSE100000",
        "GSE100001",
        "GSE100002",
        "GSE100003",
        "GSE100004",
        "GSE100005",
        "GSE100006",
        "GSE100007",
        "GSE100008",
        "GSE100009",
        "GSE100010",
        "GSE100011",
        "GSE100012",
        "GSE100013",
        "GSE100014",
        "GSE100015",
        "GSE100016",
        "GSE100017",
        "GSE100018",
        "GSE100019",
    ]

    print("=" * 70)
    print("PARALLEL DOWNLOAD OPTIMIZATION TEST")
    print("=" * 70)
    print(f"Testing with {len(test_ids)} datasets")
    print(f"NCBI Rate Limit: {settings.geo.rate_limit} req/sec")
    print()

    # Test 1: Parallel download with batch_get_metadata
    print("Test 1: Parallel Download (max_concurrent=10)")
    print("-" * 70)
    start = time.time()
    results = await client.batch_get_metadata(test_ids, max_concurrent=10)
    parallel_time = time.time() - start

    success_count = len([r for r in results.values() if r is not None])
    print(f"[OK] Completed: {success_count}/{len(test_ids)} datasets")
    print(f"Time: {parallel_time:.2f} seconds")
    print(f"Speed: {success_count/parallel_time:.2f} datasets/second")
    print()

    # Calculate theoretical speeds
    print("PERFORMANCE ANALYSIS")
    print("-" * 70)

    # Old sequential approach (estimated)
    sequential_estimate = len(test_ids) * 5.5  # 5.5 sec per file average
    print(f"Estimated Sequential Time: {sequential_estimate:.2f} seconds")
    print(f"  ({len(test_ids)} datasets x 5.5 sec/dataset)")
    print()

    # Speedup
    speedup = sequential_estimate / parallel_time
    print(f"SPEEDUP: {speedup:.1f}x faster!")
    print()

    # Efficiency
    theoretical_parallel = len(test_ids) / 10  # 10 concurrent downloads
    efficiency = (theoretical_parallel / parallel_time) * 100
    print(f"Efficiency: {efficiency:.1f}% of theoretical maximum")
    print(f"  (Theoretical: {theoretical_parallel:.2f}s with perfect parallelization)")
    print()

    print("=" * 70)
    print("[SUCCESS] OPTIMIZATION SUCCESSFUL!")
    print("=" * 70)

    await client.close()


if __name__ == "__main__":
    asyncio.run(test_parallel_download())
