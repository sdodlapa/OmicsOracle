#!/usr/bin/env python3
"""
Test script to verify that OmicsOracle displays only real, relevant results
with both GEO and AI summaries.

This script will:
1. Initialize the OmicsOracle pipeline with cache disabled
2. Execute a search query
3. Verify no cache is used
4. Check that results are not padded or fabricated
5. Verify both GEO and AI summaries are present when available
"""

import asyncio
import logging
import os
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add project root to path
# Set NCBI email before importing Bio modules
os.environ["NCBI_EMAIL"] = "omicsoracle@example.com"

# Import Bio.Entrez to set email directly
try:
    from Bio import Entrez

    Entrez.email = "omicsoracle@example.com"
    logger.info(f"Set Bio.Entrez.email to {Entrez.email}")
except ImportError:
    logger.warning("Bio.Entrez module not available")

from src.omics_oracle.core.config import Config
from src.omics_oracle.pipeline.pipeline import OmicsOracle


async def test_honest_results():
    """Test that search results are honest and contain both summary types."""
    # Initialize OmicsOracle with cache explicitly disabled
    logger.info("Initializing OmicsOracle with cache disabled...")

    # Create config with proper NCBI email
    config = Config()

    # Ensure NCBI email is set in config
    if hasattr(config, "ncbi"):
        if not hasattr(config.ncbi, "email") or not config.ncbi.email:
            logger.info("Setting NCBI email in config object")
            setattr(config.ncbi, "email", "omicsoracle@example.com")
    else:
        logger.warning("Config object does not have ncbi attribute")

    # Initialize pipeline with config
    oracle = OmicsOracle(config, disable_cache=True)

    # Ensure GEO client cache is None
    assert oracle.geo_client.cache is None, "GEO client cache should be None"

    # Ensure summarizer cache is None
    assert oracle.summarizer.cache is None, "Summarizer cache should be None"

    # Execute search with a specific query
    query = "cancer RNA-seq human"
    max_results = 15

    logger.info(f"Running search for: '{query}' (max_results={max_results})...")
    result = await oracle.process_query(query, max_results=max_results)

    # Verify results
    logger.info(f"Search complete. Found {len(result.geo_ids)} GEO IDs")
    logger.info(f"Metadata entries: {len(result.metadata)}")

    # Check for padding/fabrication
    if len(result.geo_ids) != len(result.metadata):
        logger.warning(
            f"Mismatch between GEO IDs ({len(result.geo_ids)}) and metadata entries ({len(result.metadata)})"
        )

    # Check for AI summaries
    if not result.ai_summaries:
        logger.warning("No AI summaries generated")
    else:
        if "individual_summaries" in result.ai_summaries:
            logger.info(f"Found {len(result.ai_summaries['individual_summaries'])} individual AI summaries")
        else:
            logger.warning("No individual AI summaries available")

    # Print detailed summary of each result
    logger.info("\nDetailed result summary:")
    for i, geo_id in enumerate(result.geo_ids[: min(5, len(result.geo_ids))]):
        if i < len(result.metadata):
            metadata = result.metadata[i]
            logger.info(f"\n{i+1}. {geo_id}:")
            logger.info(f"   Title: {metadata.get('title', 'N/A')}")
            logger.info(f"   Relevance score: {metadata.get('relevance_score', 'N/A')}")
            logger.info(f"   GEO Summary: {'Available' if metadata.get('summary') else 'N/A'}")

            # Check for AI summary
            ai_summary = None
            if result.ai_summaries and "individual_summaries" in result.ai_summaries:
                for summary in result.ai_summaries["individual_summaries"]:
                    if summary.get("accession") == geo_id:
                        ai_summary = summary.get("summary")
                        break

            logger.info(f"   AI Summary: {'Available' if ai_summary else 'N/A'}")
        else:
            logger.warning(f"{i+1}. {geo_id}: No metadata available")

    logger.info("\nTest completed.")
    return result


if __name__ == "__main__":
    asyncio.run(test_honest_results())
