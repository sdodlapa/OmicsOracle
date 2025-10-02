#!/usr/bin/env python3
"""
Enhanced CLI test for OmicsOracle with LLM integration.

This script provides a comprehensive test of the AI-powered summarization feature.
"""

import asyncio
import sys
import time
from pathlib import Path

# Add the src directory to the Python path
from omics_oracle.pipeline.pipeline import OmicsOracle, ResultFormat


def print_separator(title: str, char: str = "="):
    """Print a formatted separator."""
    print(f"\n{char * 60}")
    print(f" {title}")
    print(f"{char * 60}")


async def test_cli_integration():
    """Test the CLI integration with various queries."""
    print_separator("🚀 OmicsOracle AI-Powered CLI Test Suite", "=")

    # Test queries of different complexity
    test_queries = [
        {
            "query": "breast cancer tumor microenvironment",
            "description": "Complex cancer research query",
            "max_results": 3,
        },
        {
            "query": "CRISPR gene editing",
            "description": "Gene editing technology query",
            "max_results": 2,
        },
        {
            "query": "single cell RNA sequencing heart development",
            "description": "Developmental biology query",
            "max_results": 2,
        },
    ]

    oracle = OmicsOracle()
    results = []

    try:
        for i, test_case in enumerate(test_queries, 1):
            print_separator(f"Test {i}: {test_case['description']}", "-")
            print(f"🔍 Query: '{test_case['query']}'")
            print(f"📊 Max Results: {test_case['max_results']}")

            start_time = time.time()

            try:
                # Process the query
                result = await oracle.process_query(
                    query=test_case["query"],
                    max_results=test_case["max_results"],
                    result_format=ResultFormat.JSON,
                )

                end_time = time.time()
                processing_time = end_time - start_time

                # Store results
                test_result = {
                    "query": test_case["query"],
                    "status": result.status.value,
                    "processing_time": processing_time,
                    "geo_ids": len(result.geo_ids),
                    "datasets": len(result.metadata),
                    "ai_summaries": bool(result.ai_summaries),
                    "success": result.is_completed,
                }
                results.append(test_result)

                # Display results
                print(f"\n✅ Status: {result.status.value}")
                print(f"⏱️  Processing Time: {processing_time:.2f}s")
                print(f"📈 GEO IDs Found: {len(result.geo_ids)}")
                print(f"📚 Datasets Retrieved: {len(result.metadata)}")

                if result.geo_ids:
                    print("\n🆔 Sample GEO IDs:")
                    for j, geo_id in enumerate(result.geo_ids[:3], 1):
                        print(f"   {j}. {geo_id}")

                # Display AI summaries
                if result.ai_summaries:
                    print("\n🤖 AI Summaries Generated: ✅")

                    if "batch_summary" in result.ai_summaries:
                        batch = result.ai_summaries["batch_summary"]
                        print(
                            f"   📋 Batch Overview: {batch.get('total_datasets', 0)} datasets, {batch.get('total_samples', 0)} samples"
                        )

                    if "individual_summaries" in result.ai_summaries:
                        individual_count = len(result.ai_summaries["individual_summaries"])
                        print(f"   🔬 Individual Summaries: {individual_count} datasets")

                        # Show a sample summary
                        if individual_count > 0:
                            sample = result.ai_summaries["individual_summaries"][0]
                            sample_summary = sample.get("summary", {})
                            if "overview" in sample_summary:
                                overview = sample_summary["overview"]
                                print(f"   💡 Sample Overview: {overview[:150]}...")
                else:
                    print("\n🤖 AI Summaries Generated: ❌")

                print(f"\n{'✅ SUCCESS' if result.is_completed else '❌ FAILED'}")

            except Exception as e:
                print(f"\n❌ Error: {e}")
                test_result = {
                    "query": test_case["query"],
                    "status": "failed",
                    "error": str(e),
                    "success": False,
                }
                results.append(test_result)

            # Add delay between queries to respect API limits
            if i < len(test_queries):
                print("\n⏳ Waiting 30 seconds before next query to respect API limits...")
                await asyncio.sleep(30)

    finally:
        await oracle.close()

    # Summary report
    print_separator("📊 TEST RESULTS SUMMARY", "=")

    successful_tests = sum(1 for r in results if r.get("success", False))
    total_tests = len(results)

    print(
        f"📈 Overall Success Rate: {successful_tests}/{total_tests} ({successful_tests / total_tests * 100:.1f}%)"
    )

    for i, result in enumerate(results, 1):
        status_icon = "✅" if result.get("success", False) else "❌"
        print(f"\n{status_icon} Test {i}: {result['query'][:50]}...")
        print(f"   Status: {result.get('status', 'unknown')}")
        if result.get("success", False):
            print(f"   Time: {result.get('processing_time', 0):.2f}s")
            print(f"   Datasets: {result.get('datasets', 0)}")
            print(f"   AI Summaries: {'Yes' if result.get('ai_summaries', False) else 'No'}")
        else:
            print(f"   Error: {result.get('error', 'Unknown error')}")

    # Recommendations
    print_separator("💡 RECOMMENDATIONS", "=")

    if successful_tests == total_tests:
        print("🎉 All tests passed! Your OmicsOracle AI integration is working perfectly.")
        print("\n🚀 Ready for production use:")
        print("   • Web interface integration")
        print("   • CLI deployment")
        print("   • Batch processing workflows")
    else:
        print("⚠️  Some tests failed. Consider:")
        print("   • Checking OpenAI API key and credits")
        print("   • Verifying internet connectivity")
        print("   • Testing with simpler queries first")

    print("\n💰 Cost Management:")
    print("   • Using gpt-4o-mini model for cost efficiency")
    print("   • Implement caching for repeated queries")
    print("   • Set usage limits based on your budget")

    return successful_tests == total_tests


async def main():
    """Run the enhanced CLI test."""
    try:
        success = await test_cli_integration()
        if success:
            print("\n🎊 All tests completed successfully!")
            sys.exit(0)
        else:
            print("\n⚠️  Some tests failed. Check the output above for details.")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
