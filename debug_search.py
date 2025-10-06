"""Debug script to test GEO search directly."""

import asyncio
import logging

from omics_oracle_v2.core.config import get_settings
from omics_oracle_v2.lib.geo import GEOClient

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def test_search():
    """Test GEO search with the user's query."""
    settings = get_settings()

    # Initialize GEO client
    client = GEOClient(settings.geo)

    # Test queries
    test_queries = [
        # Original user query (as processed by SearchAgent)
        "(cancer AND genomics AND breast AND tissue)",
        "cancer AND genomics AND breast AND tissue",
        # Simpler variations
        "(cancer OR genomics OR breast OR tissue)",
        "cancer OR genomics OR breast OR tissue",
        # Even simpler
        "breast cancer",
        "breast AND cancer",
        # Very simple
        "breast",
        "cancer",
    ]

    for query in test_queries:
        logger.info(f"\n{'=' * 80}")
        logger.info(f"Testing query: {query}")
        logger.info(f"{'=' * 80}")

        try:
            result = await client.search(query=query, max_results=10)
            logger.info(f"Results: {result.total_found} datasets found")
            if result.geo_ids:
                logger.info(f"First 5 IDs: {result.geo_ids[:5]}")
            else:
                logger.warning("No GEO IDs returned!")

        except Exception as e:
            logger.error(f"Search failed: {e}")

        # Small delay between requests
        await asyncio.sleep(0.5)


if __name__ == "__main__":
    asyncio.run(test_search())
