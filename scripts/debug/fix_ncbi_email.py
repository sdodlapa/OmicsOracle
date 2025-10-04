"""
NCBI Email Configuration Fix for GEO Client

This module patches the GEO client to ensure the NCBI email is properly configured.
"""

import logging
import os
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("ncbi_fix")


def main():
    """Apply fixes to ensure NCBI email is properly configured."""
    # Set environment variable
    os.environ["NCBI_EMAIL"] = "omicsoracle@example.com"
    logger.info(f"Set NCBI_EMAIL environment variable to {os.environ['NCBI_EMAIL']}")

    # Create a monkey patch for Bio.Entrez
    patch_file = Path("entrez_patch.py")
    with open(patch_file, "w") as f:
        f.write(
            """
\"\"\"
Monkey patch for Bio.Entrez to force email configuration
\"\"\"

import logging
import os
from importlib import import_module

logger = logging.getLogger("entrez_patch")

# Try to import Bio.Entrez
try:
    from Bio import Entrez

    # Store original email value
    original_email = getattr(Entrez, "email", None)

    # Set email from environment or use default
    ncbi_email = os.environ.get("NCBI_EMAIL", "omicsoracle@example.com")
    Entrez.email = ncbi_email

    logger.info(f"Patched Bio.Entrez.email: {original_email} -> {Entrez.email}")

except ImportError:
    logger.warning("Bio.Entrez not found, skipping patch")

# Add patch to pipeline initialization
def patch_pipeline():
    \"\"\"Patch the OmicsOracle pipeline to ensure NCBI email is set.\"\"\"
    try:
        from src.omics_oracle.pipeline.pipeline import OmicsOracle

        # Store original __init__
        original_init = OmicsOracle.__init__

        # Create patched init
        def patched_init(self, config=None):
            # Call original init
            original_init(self, config)

            # Ensure NCBI email is set in GEO client
            if hasattr(self, "geo_client") and hasattr(self.geo_client, "_client"):
                try:
                    ncbi_email = os.environ.get("NCBI_EMAIL", "omicsoracle@example.com")
                    self.geo_client._client.email = ncbi_email
                    logger.info(f"Patched geo_client email: {self.geo_client._client.email}")
                except AttributeError:
                    logger.warning("Could not patch geo_client email")

        # Apply patch
        OmicsOracle.__init__ = patched_init
        logger.info("Patched OmicsOracle.__init__")

    except ImportError:
        logger.warning("OmicsOracle pipeline not found, skipping patch")

# Run the patch
patch_pipeline()
"""
        )

    logger.info(f"Created Entrez patch file: {patch_file}")
    logger.info("Use the following code in your application startup:")
    logger.info("import entrez_patch  # Apply Bio.Entrez email patch")

    # Create a utility script to run test searches with the correct email
    test_script = Path("test_search.py")
    with open(test_script, "w") as f:
        f.write(
            """
\"\"\"
Test NCBI search with proper email configuration
\"\"\"

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
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("test_search")

# Import patched Entrez
import entrez_patch

async def test_search(query="dna methylation immune cells"):
    \"\"\"Test GEO search with the OmicsOracle pipeline.\"\"\"
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
        if 'pipeline' in locals():
            await pipeline.close()

if __name__ == "__main__":
    asyncio.run(test_search())
"""
        )

    logger.info(f"Created test search script: {test_script}")
    logger.info("Run this script to test NCBI search with correct email configuration:")
    logger.info("python test_search.py")


if __name__ == "__main__":
    main()
