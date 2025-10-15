#!/usr/bin/env python3
"""
Test Database Integration
Verifies that API search endpoint returns accurate database metrics.
"""

import asyncio
import logging

import httpx

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_search_with_database_metrics():
    """Test that search endpoint enriches results with database metrics."""

    logger.info("=" * 80)
    logger.info("Testing Database Integration")
    logger.info("=" * 80)

    # Test query
    query = "breast cancer"

    # API endpoint
    url = "http://localhost:8000/api/agents/search"

    logger.info(f"\n1. Sending search request: '{query}'")

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                url,
                json={
                    "search_terms": [query],
                    "max_results": 5,
                    "enable_semantic": False,
                },
            )

            if response.status_code != 200:
                logger.error(f"❌ Request failed: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return False

            data = response.json()

            logger.info(f"\n2. Response received:")
            logger.info(f"   Success: {data.get('success')}")
            logger.info(f"   Datasets found: {len(data.get('datasets', []))}")
            logger.info(f"   Execution time: {data.get('execution_time_ms', 0):.2f}ms")

            # Check database metrics in results
            logger.info(f"\n3. Checking database metrics in results:")

            datasets = data.get("datasets", [])
            if not datasets:
                logger.warning("⚠️  No datasets returned")
                return True

            # Validate each dataset has database metrics
            success = True
            for i, dataset in enumerate(datasets[:3], 1):  # Check first 3
                geo_id = dataset.get("geo_id")
                citation_count = dataset.get("citation_count", -1)
                pdf_count = dataset.get("pdf_count", -1)
                processed_count = dataset.get("processed_count", -1)
                completion_rate = dataset.get("completion_rate", -1.0)

                logger.info(f"\n   Dataset {i}: {geo_id}")
                logger.info(f"   ├─ Citations in DB: {citation_count}")
                logger.info(f"   ├─ PDFs downloaded: {pdf_count}")
                logger.info(f"   ├─ Papers processed: {processed_count}")
                logger.info(f"   └─ Completion rate: {completion_rate:.1f}%")

                # Validate fields exist
                if citation_count == -1:
                    logger.error(f"   ❌ Missing citation_count field")
                    success = False
                if pdf_count == -1:
                    logger.error(f"   ❌ Missing pdf_count field")
                    success = False
                if processed_count == -1:
                    logger.error(f"   ❌ Missing processed_count field")
                    success = False
                if completion_rate == -1.0:
                    logger.error(f"   ❌ Missing completion_rate field")
                    success = False

                # Check if metrics are from database (not just pubmed_ids.length)
                pubmed_ids_count = len(dataset.get("pubmed_ids", []))
                if citation_count == pubmed_ids_count and citation_count > 0:
                    logger.warning(
                        f"   ⚠️  citation_count ({citation_count}) == pubmed_ids.length ({pubmed_ids_count})"
                    )
                    logger.warning(
                        f"       This might be from search results, not database!"
                    )

            logger.info("\n" + "=" * 80)
            if success:
                logger.info("✅ Database Integration Test PASSED")
                logger.info("   All datasets have database metric fields")
            else:
                logger.error("❌ Database Integration Test FAILED")
                logger.error("   Some datasets missing metric fields")
            logger.info("=" * 80)

            return success

    except httpx.ConnectError:
        logger.error("\n❌ Could not connect to API server")
        logger.error("   Make sure the server is running: ./start_omics_oracle.sh")
        return False
    except Exception as e:
        logger.error(f"\n❌ Test failed with error: {e}", exc_info=True)
        return False


async def test_database_queries_directly():
    """Test DatabaseQueries class directly."""
    from omics_oracle_v2.lib.storage.queries import DatabaseQueries

    logger.info("\n" + "=" * 80)
    logger.info("Testing DatabaseQueries Directly")
    logger.info("=" * 80)

    try:
        db_queries = DatabaseQueries(db_path="data/database/search_data.db")

        # Get database statistics
        logger.info("\n1. Checking database statistics:")
        stats = db_queries.get_processing_statistics()

        logger.info(f"   Total GEO datasets: {stats.get('total_geo_datasets', 0)}")
        logger.info(f"   Total publications: {stats.get('total_publications', 0)}")
        logger.info(
            f"   Publications with PDFs: {stats.get('publications_with_pdf', 0)}"
        )
        logger.info(f"   Database size: {stats.get('database_size_mb', 0):.2f} MB")

        # Test get_geo_statistics for a known GEO ID
        logger.info("\n2. Testing get_geo_statistics for GSE68849:")
        geo_stats = db_queries.get_geo_statistics("GSE68849")

        pub_counts = geo_stats.get("publication_counts", {})
        logger.info(f"   Total publications: {pub_counts.get('total', 0)}")
        logger.info(f"   With URLs: {pub_counts.get('with_urls', 0)}")
        logger.info(f"   With PDFs: {pub_counts.get('with_pdf', 0)}")
        logger.info(f"   With extraction: {pub_counts.get('with_extraction', 0)}")
        logger.info(f"   Completion rate: {geo_stats.get('completion_rate', 0):.1f}%")

        logger.info("\n" + "=" * 80)
        logger.info("✅ DatabaseQueries Test PASSED")
        logger.info("=" * 80)

        return True

    except Exception as e:
        logger.error(f"\n❌ DatabaseQueries test failed: {e}", exc_info=True)
        return False


async def main():
    """Run all tests."""
    logger.info("\n🧪 Starting Database Integration Tests\n")

    # Test 1: DatabaseQueries directly
    test1_passed = await test_database_queries_directly()

    # Test 2: API endpoint with database metrics
    test2_passed = await test_search_with_database_metrics()

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("Test Summary")
    logger.info("=" * 80)
    logger.info(
        f"   DatabaseQueries Test: {'✅ PASSED' if test1_passed else '❌ FAILED'}"
    )
    logger.info(
        f"   API Integration Test: {'✅ PASSED' if test2_passed else '❌ FAILED'}"
    )

    if test1_passed and test2_passed:
        logger.info("\n🎉 All tests PASSED!")
        logger.info("\nNext Steps:")
        logger.info("1. Open browser to http://localhost:8000/dashboard")
        logger.info("2. Search for 'breast cancer'")
        logger.info("3. Verify dataset cards show:")
        logger.info("   - '📚 X citations in database'")
        logger.info("   - '📄 X/Y PDFs downloaded'")
        logger.info("   - '📊 X% processed'")
    else:
        logger.error("\n❌ Some tests FAILED")
        logger.error("Check the logs above for details")

    logger.info("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
