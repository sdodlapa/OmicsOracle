#!/usr/bin/env python3
"""
Debug script to test OmicsOracle pipeline initialization.
This will help diagnose issues with the pipeline initialization process.
"""

import logging
import os
import traceback
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("debug")

# Add project root to path
# Set NCBI email
os.environ["NCBI_EMAIL"] = "omicsoracle@example.com"
logger.info(f"Set NCBI_EMAIL environment variable to {os.environ['NCBI_EMAIL']}")

# Try to set Bio.Entrez email
try:
    from Bio import Entrez

    Entrez.email = "omicsoracle@example.com"
    logger.info(f"Set Bio.Entrez.email to {Entrez.email}")
except ImportError:
    logger.error("Bio.Entrez not available - this may be causing issues")
    logger.error("Try installing biopython: pip install biopython")

try:
    logger.info("Importing OmicsOracle dependencies...")
    from src.omics_oracle.core.config import Config
    from src.omics_oracle.pipeline.pipeline import OmicsOracle

    logger.info("Creating Config object...")
    config = Config()

    # Check NCBI email configuration
    if hasattr(config, "ncbi"):
        if not hasattr(config.ncbi, "email") or not config.ncbi.email:
            logger.info("Setting NCBI email in config object")
            setattr(config.ncbi, "email", "omicsoracle@example.com")
        logger.info(f"NCBI email in config: {config.ncbi.email}")
    else:
        logger.error("Config object does not have ncbi attribute - this is a problem")

    logger.info("Creating OmicsOracle pipeline instance with disable_cache=True...")
    pipeline = OmicsOracle(config, disable_cache=True)

    if pipeline is None:
        logger.error("Pipeline initialization returned None")
    else:
        logger.info("Pipeline created successfully!")

        # Check critical components
        logger.info("Checking pipeline components...")
        if hasattr(pipeline, "geo_client"):
            logger.info(f"GEO client initialized: {pipeline.geo_client is not None}")
        else:
            logger.error("Pipeline missing geo_client attribute")

        if hasattr(pipeline, "summarizer"):
            logger.info(f"Summarizer initialized: {pipeline.summarizer is not None}")
        else:
            logger.error("Pipeline missing summarizer attribute")

        # Test a simple search query
        try:
            logger.info("Testing a basic query (this will be async)...")
            import asyncio

            async def test_query():
                try:
                    logger.info("Running search query: 'test cancer'")
                    result = await pipeline.process_query("test cancer", max_results=2)
                    logger.info(f"Query successful! Found {len(result.geo_ids)} GEO IDs")
                    return result
                except Exception as e:
                    logger.error(f"Query failed: {e}")
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    return None

            # Run the async function
            result = asyncio.run(test_query())

            if result and result.geo_ids:
                logger.info(f"Search successful! Found IDs: {result.geo_ids}")
            else:
                logger.error("Search returned no results or failed")

        except Exception as e:
            logger.error(f"Error running test query: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")

except Exception as e:
    logger.error(f"Error initializing pipeline: {e}")
    logger.error(f"Traceback: {traceback.format_exc()}")

logger.info("Diagnostic script complete")
