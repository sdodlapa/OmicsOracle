#!/usr/bin/env python
"""
GEO Client Test Script

This script tests the functionality of the GEO client in isolation,
verifying its ability to connect to NCBI and retrieve data.
"""

import asyncio
import logging
import os
import time
import traceback
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("geo_client_test.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("geo_client_test")

# Add project root to path
script_path = Path(__file__).resolve()
project_root = script_path.parent
logger.info(f"Project root: {project_root}")


def setup_ncbi_email():
    """Set up NCBI email configuration"""
    # Set environment variable
    os.environ["NCBI_EMAIL"] = "omicsoracle@example.com"
    logger.info(f"Set NCBI_EMAIL environment variable to {os.environ['NCBI_EMAIL']}")

    # Set Bio.Entrez email directly
    try:
        from Bio import Entrez

        Entrez.email = os.environ["NCBI_EMAIL"]
        logger.info(f"Set Bio.Entrez.email to {Entrez.email}")
        return True
    except ImportError:
        logger.error("Failed to import Bio.Entrez")
        return False


async def test_geo_search(query, max_results=5):
    """Test GEO search functionality"""
    try:
        from omics_oracle.core.config import Config
        from omics_oracle.geo_tools.geo_client import GEOClient

        logger.info(f"Testing GEO search with query: '{query}'")

        # Create config and set NCBI email
        config = Config()
        if hasattr(config, "ncbi"):
            setattr(config.ncbi, "email", os.environ["NCBI_EMAIL"])

        # Initialize GEO client with caching disabled
        geo_client = GEOClient(config, disable_cache=True)
        logger.info("GEO client initialized")

        # Perform search
        start_time = time.time()
        logger.info("Searching for GEO IDs...")
        geo_ids = await geo_client.search_geo_ids(query, max_results=max_results)
        search_time = time.time() - start_time

        if geo_ids:
            logger.info(f"✓ Found {len(geo_ids)} GEO IDs in {search_time:.2f}s")
            logger.info(f"GEO IDs: {geo_ids}")
            return geo_ids
        else:
            logger.warning(f"✗ No GEO IDs found for query: '{query}'")
            return []

    except Exception as e:
        logger.error(f"✗ Error in GEO search: {e}")
        logger.error(traceback.format_exc())
        return []


async def test_fetch_metadata(geo_ids):
    """Test fetching metadata for GEO IDs"""
    if not geo_ids:
        logger.warning("No GEO IDs provided for metadata fetch test")
        return False

    try:
        from omics_oracle.core.config import Config
        from omics_oracle.geo_tools.geo_client import GEOClient

        logger.info(f"Testing metadata fetch for {len(geo_ids)} GEO IDs")

        # Create config and set NCBI email
        config = Config()
        if hasattr(config, "ncbi"):
            setattr(config.ncbi, "email", os.environ["NCBI_EMAIL"])

        # Initialize GEO client with caching disabled
        geo_client = GEOClient(config, disable_cache=True)

        # Fetch metadata for each GEO ID
        for geo_id in geo_ids:
            logger.info(f"Fetching metadata for {geo_id}...")
            start_time = time.time()
            metadata = await geo_client.fetch_geo_metadata(geo_id)
            fetch_time = time.time() - start_time

            if metadata:
                logger.info(f"✓ Successfully fetched metadata for {geo_id} in {fetch_time:.2f}s")
                # Log some metadata fields for verification
                if isinstance(metadata, dict):
                    logger.info(f"  Title: {metadata.get('title', 'N/A')}")
                    logger.info(
                        f"  Summary: {(metadata.get('summary', 'N/A')[:100] + '...') if metadata.get('summary') else 'N/A'}"
                    )
                    logger.info(f"  Platform: {metadata.get('platform', 'N/A')}")
                    logger.info(f"  Organism: {metadata.get('organism', 'N/A')}")
                else:
                    logger.warning(f"  Unexpected metadata type: {type(metadata)}")
            else:
                logger.warning(f"✗ Failed to fetch metadata for {geo_id}")

        return True
    except Exception as e:
        logger.error(f"✗ Error in metadata fetch: {e}")
        logger.error(traceback.format_exc())
        return False


async def test_rate_limiting_and_retries():
    """Test rate limiting and retry mechanism"""
    try:
        from omics_oracle.core.config import Config
        from omics_oracle.geo_tools.geo_client import GEOClient

        logger.info("Testing rate limiting and retry mechanism")

        # Create config and set NCBI email
        config = Config()
        if hasattr(config, "ncbi"):
            setattr(config.ncbi, "email", os.environ["NCBI_EMAIL"])

        # Initialize GEO client with caching disabled
        geo_client = GEOClient(config, disable_cache=True)

        # Perform multiple rapid searches to trigger rate limiting
        queries = [
            "cancer RNA-seq",
            "diabetes microarray",
            "covid-19 transcriptome",
            "heart disease methylation",
            "brain single-cell",
        ]

        results = []
        for query in queries:
            logger.info(f"Searching for: '{query}'")
            geo_ids = await geo_client.search_geo_ids(query, max_results=2)
            results.append((query, len(geo_ids)))
            logger.info(f"Found {len(geo_ids)} results for '{query}'")
            # Don't wait between queries to potentially trigger rate limiting

        # Log results
        logger.info("Rate limiting test results:")
        for query, count in results:
            logger.info(f"  '{query}': {count} results")

        return all(count > 0 for _, count in results)
    except Exception as e:
        logger.error(f"✗ Error in rate limiting test: {e}")
        logger.error(traceback.format_exc())
        return False


async def run_tests():
    """Run all GEO client tests"""
    logger.info("=" * 50)
    logger.info("GEO CLIENT TESTS")
    logger.info("=" * 50)

    # Setup NCBI email
    if not setup_ncbi_email():
        logger.error("Failed to set up NCBI email, aborting tests")
        return

    # Test search functionality
    test_query = "dna methylation of immune cells"
    geo_ids = await test_geo_search(test_query)

    # Test metadata fetch if we got GEO IDs
    if geo_ids:
        await test_fetch_metadata(geo_ids[:2])  # Test with first 2 IDs

    # Test rate limiting and retries
    await test_rate_limiting_and_retries()

    logger.info("\n" + "=" * 50)
    logger.info("GEO CLIENT TEST COMPLETE")
    logger.info("=" * 50)


if __name__ == "__main__":
    # Create and run the async event loop
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(run_tests())
    except Exception as e:
        logger.error(f"Unhandled exception in tests: {e}")
        logger.error(traceback.format_exc())
    finally:
        loop.close()
