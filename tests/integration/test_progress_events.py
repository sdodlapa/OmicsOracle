#!/usr/bin/env python
"""
Progress Events Validation Script for OmicsOracle

This script tests the progress event reporting functionality of the OmicsOracle pipeline.
It executes a search query and logs all progress events to validate the real-time progress reporting.
"""

import asyncio
import logging
import os
import sys
import time
from datetime import datetime
from typing import Any, Dict

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("progress_validation.log"),
    ],
)
logger = logging.getLogger("progress_validation")

# Add project root to path
from src.omics_oracle.core.config import Config

# Import OmicsOracle components
from src.omics_oracle.pipeline.pipeline import OmicsOracle, ProgressEvent

# List to store progress events
progress_events = []


async def progress_callback(query_id: str, event: ProgressEvent):
    """Callback function to receive progress events from the pipeline."""
    progress_events.append(
        {
            "query_id": query_id,
            "stage": event.stage,
            "message": event.message,
            "percentage": event.percentage,
            "timestamp": event.timestamp.isoformat(),
            "detail": event.detail,
        }
    )

    # Print progress update
    logger.info(f"Progress [{event.percentage:.1f}%]: {event.stage} - {event.message}")
    if event.detail:
        logger.debug(f"  Details: {event.detail}")


async def test_search_with_progress(query: str):
    """Run a test search and track progress events."""
    start_time = time.time()
    logger.info(f"Starting test search: '{query}'")

    # Load configuration
    config = Config()

    # Log configuration settings
    logger.info(f"NCBI Email: {getattr(config.ncbi, 'email', 'Not configured')}")
    logger.info(f"Config environment: {config.environment}")

    # Initialize pipeline
    pipeline = OmicsOracle(config)

    # Set progress callback
    pipeline.set_progress_callback(progress_callback)

    try:
        # Process query
        result = await pipeline.process_query(query=query, max_results=10, include_sra=False)

        # Log result summary
        logger.info(f"Search completed in {time.time() - start_time:.2f} seconds")
        logger.info(f"Status: {result.status.value}")
        logger.info(f"GEO IDs found: {len(result.geo_ids)}")
        logger.info(f"Metadata entries: {len(result.metadata)}")
        logger.info(f"Progress events: {len(progress_events)}")

        # Check if any GEO IDs were found
        if not result.geo_ids:
            logger.warning("No GEO IDs were found. This might indicate a configuration issue.")

            # Check NCBI client configuration
            if hasattr(pipeline.geo_client, "_client") and hasattr(pipeline.geo_client._client, "email"):
                logger.info(f"NCBI client email: {pipeline.geo_client._client.email}")
            else:
                logger.error("NCBI client email not properly configured!")

        # Write progress events to file
        with open("progress_events.log", "w") as f:
            for i, event in enumerate(progress_events):
                f.write(f"Event {i+1}: {event['stage']} - {event['message']} ({event['percentage']:.1f}%)\n")
                if event["detail"]:
                    f.write(f"  Details: {event['detail']}\n")
                f.write("\n")

        return result

    except Exception as e:
        logger.error(f"Error during search: {str(e)}", exc_info=True)
        raise
    finally:
        # Clean up
        await pipeline.close()


async def analyze_exception_logs():
    """Analyze log files for exceptions and configuration issues."""
    logger.info("Checking for configuration issues and exceptions...")

    # Check for NCBI email configuration
    env_files = [".env", ".env.local", ".env.development"]
    for env_file in env_files:
        if os.path.exists(env_file):
            with open(env_file, "r") as f:
                content = f.read()
                logger.info(f"Found {env_file} file:")
                if "NCBI_EMAIL" in content:
                    logger.info(f"  NCBI_EMAIL is configured in {env_file}")
                else:
                    logger.warning(f"  NCBI_EMAIL not found in {env_file}")

    # Check Python path
    logger.info(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")

    # List of key components to check
    components = [
        "src.omics_oracle.geo_tools.geo_client",
        "src.omics_oracle.services.improved_search",
        "src.omics_oracle.pipeline.pipeline",
    ]

    for component in components:
        try:
            __import__(component)
            logger.info(f"Successfully imported {component}")
        except ImportError as e:
            logger.error(f"Failed to import {component}: {str(e)}")


async def main():
    """Main function to run the validation."""
    logger.info("Starting OmicsOracle Progress Events Validation")
    logger.info(f"Current directory: {os.getcwd()}")

    # First analyze logs and configuration
    await analyze_exception_logs()

    # Test queries
    queries = ["get information about dna methylation of immune cells"]

    for query in queries:
        await test_search_with_progress(query)

    logger.info("Validation completed")


if __name__ == "__main__":
    asyncio.run(main())
