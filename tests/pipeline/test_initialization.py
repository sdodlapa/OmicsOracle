#!/usr/bin/env python3
"""
Test the OmicsOracle pipeline initialization process.

This script verifies that:
1. The OmicsOracle pipeline initializes properly
2. NCBI email is configured correctly
3. Required components are initialized
4. Caching is disabled as expected
"""

import asyncio
import logging
import os
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
from src.omics_oracle.pipeline.pipeline import OmicsOracle


@pytest.fixture
def config():
    """Create a test configuration object."""
    config = Config()

    # Ensure NCBI email is set in config
    if hasattr(config, "ncbi"):
        if not hasattr(config.ncbi, "email") or not config.ncbi.email:
            logger.info("Setting NCBI email in config object for testing")
            setattr(config.ncbi, "email", "omicsoracle@example.com")

    return config


async def test_pipeline_initialization(config):
    """Test that the OmicsOracle pipeline initializes successfully."""
    logger.info("Testing pipeline initialization...")

    # Initialize pipeline with caching explicitly disabled
    try:
        pipeline = OmicsOracle(config, disable_cache=True)
        assert pipeline is not None, "Pipeline should not be None"

        # Check if critical components are initialized
        assert hasattr(pipeline, "geo_client"), "Pipeline should have geo_client"
        assert pipeline.geo_client is not None, "geo_client should not be None"

        assert hasattr(pipeline, "summarizer"), "Pipeline should have summarizer"
        assert pipeline.summarizer is not None, "summarizer should not be None"

        # Verify cache is disabled
        assert pipeline.disable_cache is True, "Cache should be disabled"

        # Verify NCBI email is set correctly
        assert Entrez.email == "omicsoracle@example.com", "Entrez.email should be set"

        if hasattr(pipeline.config, "ncbi") and hasattr(pipeline.config.ncbi, "email"):
            assert pipeline.config.ncbi.email == "omicsoracle@example.com", "Config NCBI email should be set"

        logger.info("Pipeline initialization test successful!")
        return True
    except Exception as e:
        logger.error(f"Pipeline initialization failed: {e}")
        raise


async def test_basic_query(config):
    """Test a basic query with the pipeline."""
    logger.info("Testing basic query functionality...")

    try:
        # Initialize pipeline
        pipeline = OmicsOracle(config, disable_cache=True)

        # Simple test query
        query = "cancer microarray"
        max_results = 3

        # Process query
        query_result = await pipeline.process_query(query, max_results=max_results)

        # Verify results
        assert query_result is not None, "Query result should not be None"
        assert hasattr(query_result, "geo_ids"), "Query result should have geo_ids"
        assert query_result.geo_ids is not None, "geo_ids should not be None"

        # We may not always get results, but the query should execute without errors
        if query_result.geo_ids:
            logger.info(f"Found {len(query_result.geo_ids)} GEO IDs")

            # Check that we don't get more results than requested
            assert (
                len(query_result.geo_ids) <= max_results
            ), f"Should not return more than {max_results} results"

            # Verify we have metadata for each GEO ID
            if query_result.metadata:
                assert len(query_result.metadata) <= len(
                    query_result.geo_ids
                ), "Should not have more metadata than GEO IDs"
        else:
            logger.warning("No GEO IDs found for query, but query executed without errors")

        logger.info("Basic query test successful!")
        return True
    except Exception as e:
        logger.error(f"Basic query test failed: {e}")
        raise


@pytest.mark.asyncio
async def test_pipeline_components():
    """Test all pipeline components in sequence."""
    config_obj = config()

    # Test initialization
    init_success = await test_pipeline_initialization(config_obj)
    assert init_success, "Pipeline initialization should succeed"

    # Only proceed with query test if initialization succeeded
    if init_success:
        query_success = await test_basic_query(config_obj)
        assert query_success, "Basic query should succeed"


if __name__ == "__main__":
    # Run the tests
    asyncio.run(test_pipeline_components())
