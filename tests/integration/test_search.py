"""
Test NCBI search with proper email configuration
"""

import asyncio
import logging
import os
import time
from pathlib import Path

# Set environment variable
os.environ["NCBI_EMAIL"] = "omicsoracle@example.com"

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("test_search")

# Add project root to path and import patched Entrez
project_root = Path.cwd()
import entrez_patch


async def test_search(query="dna methylation immune cells"):
    """Test GEO search with the OmicsOracle pipeline."""
    # Add project root to path
    project_root = Path.cwd()
    try:
        # Import OmicsOracle components
        from src.omics_oracle.core.config import Config
        from src.omics_oracle.pipeline.pipeline import OmicsOracle

        # Check Bio.Entrez email
        try:
            from Bio import Entrez

            logger.info(f"Bio.Entrez.email = {Entrez.email}")
        except ImportError:
            logger.warning("Bio.Entrez not available")

        # Create config
        config = Config()
        if hasattr(config, "ncbi") and hasattr(config.ncbi, "email"):
            logger.info(f"Config NCBI email: {config.ncbi.email}")

            # Force set it if not already set
            if not config.ncbi.email:
                config.ncbi.email = os.environ.get("NCBI_EMAIL", "omicsoracle@example.com")
                logger.info(f"Set config.ncbi.email to {config.ncbi.email}")

        # Initialize pipeline
        logger.info("Initializing OmicsOracle pipeline...")
        pipeline = OmicsOracle(config)

        # Check geo_client configuration
        if hasattr(pipeline, "geo_client"):
            geo_client = pipeline.geo_client
            logger.info(f"GEO client info: {geo_client.get_client_info()}")

            # Check NCBI client email
            if hasattr(geo_client, "_client") and hasattr(geo_client._client, "email"):
                logger.info(f"GEO client email: {geo_client._client.email}")

        # Process query
        logger.info(f"Testing search with query: '{query}'")
        start_time = time.time()
        result = await pipeline.process_query(query=query, max_results=5)

        # Log results
        elapsed = time.time() - start_time
        logger.info(f"Search completed in {elapsed:.2f}s")
        logger.info(f"Status: {result.status.value}")
        logger.info(f"GEO IDs found: {len(result.geo_ids)}")
        if result.geo_ids:
            logger.info(f"First 5 GEO IDs: {result.geo_ids[:5]}")

        # Log progress events
        logger.info(f"Progress events: {len(result.progress_events)}")
        for i, event in enumerate(result.progress_events[:10]):  # Show first 10
            logger.info(f"Event {i+1}: {event.stage} - {event.message} ({event.percentage:.1f}%)")

        return result

    except Exception as e:
        logger.error(f"Error during test search: {e}", exc_info=True)
        return None

    finally:
        if "pipeline" in locals():
            await pipeline.close()


if __name__ == "__main__":
    asyncio.run(test_search())
