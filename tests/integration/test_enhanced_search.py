#!/usr/bin/env python3
"""
Test the enhanced search functionality for complex queries

This script tests the new enhanced query handler with complex biomedical queries
that were previously returning no results.
"""

import asyncio
import logging
import os
import sys
import time
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add project root to path
# Set NCBI email environment variable
os.environ["NCBI_EMAIL"] = "omicsoracle@example.com"

# Import required modules
try:
    from omics_oracle.core.config import Config
    from omics_oracle.pipeline.pipeline import OmicsOracle
    from omics_oracle.search.enhanced_query_handler import QueryParser, perform_multi_strategy_search
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    sys.exit(1)


async def test_search_with_enhanced_handler():
    """Test the enhanced search functionality with complex queries."""
    logger.info("Testing enhanced search handler with complex queries")

    # Initialize pipeline
    config = Config()
    pipeline = OmicsOracle(config)

    # Test queries that were failing before
    test_queries = [
        "gene expression data for liver cancer of human species",
        "breast cancer single-cell RNA-seq human",
        "diabetes microarray data from pancreatic tissue",
        "covid-19 lung transcriptome data",
        "neurodegenerative disease brain expression profiles",
    ]

    results = {}

    try:
        for query in test_queries:
            logger.info(f"Testing query: '{query}'")

            # Parse query components
            parser = QueryParser()
            components = parser.parse_query(query)
            logger.info(f"Query components: {components}")

            # Generate alternative queries
            alt_queries = parser.generate_alternative_queries(components)
            logger.info(f"Alternative queries: {alt_queries}")

            # Test search with both approaches for comparison
            start_time = time.time()

            try:
                # Standard approach
                standard_result = await pipeline.process_query(query, max_results=5)
                standard_count = len(standard_result.geo_ids) if hasattr(standard_result, "geo_ids") else 0
                logger.info(f"Standard search results: {standard_count} GEO IDs")
            except Exception as e:
                logger.error(f"Standard search failed: {e}")
                standard_count = 0

            try:
                # Enhanced approach
                geo_ids, metadata = await perform_multi_strategy_search(pipeline, query, max_results=5)
                enhanced_count = len(geo_ids)
                logger.info(f"Enhanced search results: {enhanced_count} GEO IDs")
                logger.info(f"Search strategy: {metadata.get('search_strategy')}")
                logger.info(f"Query used: {metadata.get('query_used')}")
            except Exception as e:
                logger.error(f"Enhanced search failed: {e}")
                enhanced_count = 0

            elapsed = time.time() - start_time

            # Store results
            results[query] = {
                "standard_count": standard_count,
                "enhanced_count": enhanced_count,
                "elapsed_time": elapsed,
                "components": components,
                "search_strategy": metadata.get("search_strategy") if "metadata" in locals() else None,
                "query_used": metadata.get("query_used") if "metadata" in locals() else None,
            }

            logger.info(f"Query '{query}' processed in {elapsed:.2f}s")
            logger.info("---")
    except Exception as e:
        logger.error(f"Test failed with error: {e}")

    # Print summary
    logger.info("\n=== SUMMARY ===")
    for query, result in results.items():
        improvement = result["enhanced_count"] - result["standard_count"]

        if improvement > 0:
            status = f"✅ Improved (+{improvement} results)"
        elif improvement == 0 and result["enhanced_count"] > 0:
            status = "✓ Same results"
        elif improvement == 0 and result["enhanced_count"] == 0:
            status = "❌ No results in both methods"
        else:
            status = f"❌ Worse (-{abs(improvement)} results)"

        logger.info(f"Query: '{query}'")
        logger.info(f"  Standard: {result['standard_count']} results")
        logger.info(f"  Enhanced: {result['enhanced_count']} results")
        logger.info(f"  Strategy: {result.get('search_strategy', 'N/A')}")
        logger.info(f"  Query used: {result.get('query_used', 'N/A')}")
        logger.info(f"  Status: {status}")
        logger.info("")

    return pipeline


async def main():
    """Run the enhanced search test and properly close resources."""
    pipeline = None
    try:
        # Run the test
        pipeline = await test_search_with_enhanced_handler()
    finally:
        # Close the pipeline to clean up resources
        if pipeline:
            logger.info("Cleaning up resources...")
            # Close the pipeline
            if hasattr(pipeline, "close"):
                await pipeline.close()

            # Explicitly close any other potential sessions
            if hasattr(pipeline, "geo_client"):
                if hasattr(pipeline.geo_client, "session") and not pipeline.geo_client.session.closed:
                    await pipeline.geo_client.session.close()
                # Also close unified client if it exists
                if hasattr(pipeline.geo_client, "unified_client") and hasattr(
                    pipeline.geo_client.unified_client, "session"
                ):
                    if not pipeline.geo_client.unified_client.session.closed:
                        await pipeline.geo_client.unified_client.session.close()
                # Close direct client if it exists
                if hasattr(pipeline.geo_client, "direct_client") and hasattr(
                    pipeline.geo_client.direct_client, "session"
                ):
                    if not pipeline.geo_client.direct_client.session.closed:
                        await pipeline.geo_client.direct_client.session.close()

            # Close any sessions in http clients
            if hasattr(pipeline, "http_client") and hasattr(pipeline.http_client, "session"):
                if not pipeline.http_client.session.closed:
                    await pipeline.http_client.session.close()

            # Close any aiohttp sessions
            import asyncio

            for task in asyncio.all_tasks():
                if "aiohttp" in task.get_name() and not task.done():
                    logger.info(f"Cancelling aiohttp task: {task.get_name()}")
                    task.cancel()

            logger.info("Resources cleaned up successfully")


if __name__ == "__main__":
    asyncio.run(main())
