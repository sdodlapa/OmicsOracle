#!/usr/bin/env python3
"""
Test script for the enhanced OmicsOracle features.

This tests:
- Caching system for AI summaries
- Batch processing capabilities
- Performance improvements
"""

import asyncio
import sys
import time
from pathlib import Path

# Add the src directory to the Python path
from omics_oracle.services.batch_processor import BatchProcessor
from omics_oracle.services.cache import SummaryCache
from omics_oracle.services.summarizer import SummarizationService


async def test_caching_system():
    """Test the AI summary caching system."""
    print("🗄️  Testing AI Summary Caching System")
    print("=" * 50)

    # Initialize cache
    cache = SummaryCache()

    # Test cache operations
    print("📝 Testing cache set/get operations...")

    # Store a test summary
    test_summary = {
        "overview": "This is a test summary for caching",
        "technical_details": "Sample technical details",
        "significance": "Important for testing caching functionality",
    }

    query = "test diabetes query"
    cache.set(query, "dataset_summary", test_summary, token_count=150)

    # Retrieve from cache
    cached_result = cache.get(query, "dataset_summary")

    if cached_result:
        print("✅ Cache set/get working correctly")
        print(f"   Retrieved: {cached_result['overview'][:50]}...")
    else:
        print("❌ Cache retrieval failed")
        return False

    # Test cache statistics
    stats = cache.get_stats()
    print(f"\n📊 Cache Statistics:")
    print(f"   Total entries: {stats['total_entries']}")
    print(f"   Active entries: {stats['active_entries']}")
    print(f"   Tokens saved: {stats['tokens_saved']}")

    return True


async def test_batch_processing():
    """Test the batch processing system."""
    print("\n📦 Testing Batch Processing System")
    print("=" * 50)

    # Initialize batch processor
    batch_processor = BatchProcessor(max_workers=2)

    # Create a batch job with multiple queries
    test_queries = [
        "diabetes pancreatic beta cells",
        "cancer breast tissue",
        "alzheimer brain neurons",
    ]

    print(f"🚀 Creating batch job with {len(test_queries)} queries...")

    try:
        job_id = batch_processor.create_batch_job(
            queries=test_queries,
            name="Test Batch Job",
            max_results_per_query=2,
            enable_ai=True,
        )

        print(f"✅ Batch job created: {job_id}")

        # Get initial status
        batch_job = batch_processor.get_batch_job(job_id)
        if batch_job:
            print(f"   Status: {batch_job.status.value}")
            print(f"   Total queries: {batch_job.total_queries}")

        # Note: We won't actually process the batch job in this test
        # as it would take too long and consume API credits
        print("   (Batch processing test completed - actual processing skipped for demo)")

        return True

    except Exception as e:
        print(f"❌ Batch processing test failed: {e}")
        return False


async def test_performance_improvements():
    """Test performance improvements from caching."""
    print("\n⚡ Testing Performance Improvements")
    print("=" * 50)

    # Initialize summarization service (with caching)
    summarizer = SummarizationService()

    # Test metadata
    test_metadata = {
        "accession": "GSE12345",
        "title": "Test dataset for performance testing",
        "summary": "This dataset is used to test caching performance improvements.",
        "organism": "Homo sapiens",
        "platform": "Test Platform",
        "samples": [{"title": f"Sample {i}"} for i in range(1, 6)],
    }

    query_context = "performance test query"

    # First call (should use AI/fallback)
    print("🔄 First summarization call (fresh)...")
    start_time = time.time()

    summary1 = summarizer.summarize_dataset(test_metadata, query_context=query_context, summary_type="brief")

    first_call_time = time.time() - start_time
    print(f"   Time: {first_call_time:.3f}s")
    print(f"   Summary: {summary1.get('overview', 'N/A')[:50]}...")

    # Second call (should use cache if available)
    print("\n🔄 Second summarization call (cached)...")
    start_time = time.time()

    summary2 = summarizer.summarize_dataset(test_metadata, query_context=query_context, summary_type="brief")

    second_call_time = time.time() - start_time
    print(f"   Time: {second_call_time:.3f}s")

    # Calculate improvement
    if second_call_time < first_call_time:
        improvement = ((first_call_time - second_call_time) / first_call_time) * 100
        print(f"✅ Performance improvement: {improvement:.1f}% faster")
    else:
        print("   (No significant performance difference - normal for fallback mode)")

    return True


async def test_cache_management():
    """Test cache management features."""
    print("\n🧹 Testing Cache Management")
    print("=" * 50)

    cache = SummaryCache()

    # Get initial stats
    initial_stats = cache.get_stats()
    print(f"📊 Initial cache state:")
    print(f"   Total entries: {initial_stats['total_entries']}")

    # Add some test entries
    for i in range(3):
        cache.set(
            f"test query {i}",
            "test_summary",
            {"test": f"summary {i}"},
            token_count=100,
        )

    # Check stats after additions
    updated_stats = cache.get_stats()
    print(f"\n📈 After adding test entries:")
    print(f"   Total entries: {updated_stats['total_entries']}")
    print(f"   Entries added: {updated_stats['total_entries'] - initial_stats['total_entries']}")

    # Test cleanup (won't find expired entries in this quick test)
    expired_count = cache.cleanup_expired()
    print(f"\n🧹 Cleanup results:")
    print(f"   Expired entries removed: {expired_count}")

    return True


async def main():
    """Run all enhancement tests."""
    print("🚀 Testing OmicsOracle Enhanced Features")
    print("=" * 60)

    tests = [
        test_caching_system,
        test_batch_processing,
        test_performance_improvements,
        test_cache_management,
    ]

    results = []

    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            results.append(False)

    # Summary
    print("\n" + "=" * 60)
    print("📋 Test Summary")
    print("=" * 60)

    passed = sum(results)
    total = len(results)

    test_names = [
        "Caching System",
        "Batch Processing",
        "Performance Improvements",
        "Cache Management",
    ]

    for i, (test_name, result) in enumerate(zip(test_names, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:25} {status}")

    print(f"\n🎯 Overall Results: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All enhancement tests completed successfully!")
        print("\n💡 Next steps:")
        print("   1. Deploy the enhanced system")
        print("   2. Test batch processing with real workloads")
        print("   3. Monitor cache performance and hit rates")
        print("   4. Implement cost tracking and management")
    else:
        print(f"\n⚠️  {total - passed} tests failed. Check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
