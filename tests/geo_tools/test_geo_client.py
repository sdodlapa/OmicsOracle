#!/usr/bin/env python3
"""
Test the GEO client functionality of OmicsOracle.

This script verifies that:
1. The GEO client connects properly to NCBI
2. Search queries return expected results
3. Metadata retrieval works correctly
4. Error handling functions as expected
5. Caching is properly disabled
"""

import asyncio
import logging
import os
import time
from pathlib import Path

import pytest

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add project root to path
# Set NCBI email for testing
os.environ["NCBI_EMAIL"] = "omicsoracle@example.com"

from Bio import Entrez

from src.omics_oracle.core.config import Config
from src.omics_oracle.geo_tools.geo_client import GEOClient


@pytest.fixture
def geo_client():
    """Create a test GEO client."""
    # Ensure NCBI email is set
    Entrez.email = "omicsoracle@example.com"

    # Create config
    config = Config()
    if hasattr(config, "ncbi"):
        setattr(config.ncbi, "email", "omicsoracle@example.com")

    # Create GEO client with caching disabled
    return GEOClient(config, disable_cache=True)


async def test_geo_search(geo_client):
    """Test GEO search functionality."""
    logger.info("Testing GEO search...")

    try:
        # Simple search query
        query = "cancer microarray"
        max_results = 5

        # Perform search
        search_start = time.time()
        geo_ids = await geo_client.search(query, max_results=max_results)
        search_duration = time.time() - search_start

        # Verify results
        assert geo_ids is not None, "GEO IDs should not be None"
        logger.info(f"Found {len(geo_ids)} GEO IDs in {search_duration:.2f}s")

        # We might not always get results, but the function should execute without errors
        if geo_ids:
            # Check that we don't get more results than requested
            assert len(geo_ids) <= max_results, f"Should not return more than {max_results} results"

            # Check that results follow GEO ID format (GSE*)
            for geo_id in geo_ids:
                assert geo_id.startswith("GSE"), f"GEO ID {geo_id} should start with GSE"

        logger.info("GEO search test successful!")
        return geo_ids
    except Exception as e:
        logger.error(f"GEO search test failed: {e}")
        raise


async def test_metadata_retrieval(geo_client, geo_ids):
    """Test metadata retrieval functionality."""
    if not geo_ids or len(geo_ids) == 0:
        logger.warning("No GEO IDs available for metadata test")
        return True

    logger.info(f"Testing metadata retrieval for {len(geo_ids)} GEO IDs...")

    try:
        # Get metadata for the first GEO ID
        geo_id = geo_ids[0]

        metadata_start = time.time()
        metadata = await geo_client.get_metadata(geo_id)
        metadata_duration = time.time() - metadata_start

        # Verify metadata
        assert metadata is not None, "Metadata should not be None"
        logger.info(f"Retrieved metadata for {geo_id} in {metadata_duration:.2f}s")

        # Check essential metadata fields
        assert "title" in metadata, "Metadata should have a title"
        assert "summary" in metadata, "Metadata should have a summary"

        logger.info(f"Metadata keys: {', '.join(metadata.keys())}")
        logger.info("Metadata retrieval test successful!")
        return True
    except Exception as e:
        logger.error(f"Metadata retrieval test failed: {e}")
        raise


async def test_error_handling(geo_client):
    """Test error handling in GEO client."""
    logger.info("Testing error handling...")

    try:
        # Test with invalid GEO ID
        invalid_geo_id = "INVALID_ID"

        # Should not raise exception but return None or empty result
        metadata = await geo_client.get_metadata(invalid_geo_id)

        # Verify result
        assert metadata is None or len(metadata) == 0, "Invalid GEO ID should return None or empty metadata"

        logger.info("Error handling test successful!")
        return True
    except Exception as e:
        logger.error(f"Error handling test failed: {e}")
        raise


async def test_cache_disabled(geo_client):
    """Test that caching is properly disabled."""
    logger.info("Testing cache disabled functionality...")

    try:
        # Verify cache is disabled
        assert geo_client.disable_cache is True, "Cache should be disabled"

        # Run the same query twice and measure time
        query = "breast cancer"
        max_results = 3

        # First run
        start1 = time.time()
        geo_ids1 = await geo_client.search(query, max_results=max_results)
        duration1 = time.time() - start1

        # Short delay
        await asyncio.sleep(1)

        # Second run - should take similar time if cache is disabled
        start2 = time.time()
        geo_ids2 = await geo_client.search(query, max_results=max_results)
        duration2 = time.time() - start2

        logger.info(f"First search: {duration1:.2f}s, Second search: {duration2:.2f}s")

        # If cache was enabled, second run would be much faster
        # With cache disabled, times should be comparable
        # Note: This is not a perfect test as network conditions can vary
        # but significant differences would suggest caching is happening

        # Check results consistency
        assert len(geo_ids1) == len(geo_ids2), "Result counts should be consistent"

        logger.info("Cache disabled test successful!")
        return True
    except Exception as e:
        logger.error(f"Cache disabled test failed: {e}")
        raise


@pytest.mark.asyncio
async def test_geo_client_components():
    """Test all GEO client components in sequence."""
    client = geo_client()

    # Test search
    geo_ids = await test_geo_search(client)

    # Test metadata retrieval if we have GEO IDs
    if geo_ids and len(geo_ids) > 0:
        metadata_success = await test_metadata_retrieval(client, geo_ids)
        assert metadata_success, "Metadata retrieval should succeed"

    # Test error handling
    error_success = await test_error_handling(client)
    assert error_success, "Error handling should succeed"

    # Test cache disabled
    cache_success = await test_cache_disabled(client)
    assert cache_success, "Cache disabled test should succeed"


if __name__ == "__main__":
    # Run the tests
    asyncio.run(test_geo_client_components())
