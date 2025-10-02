#!/usr/bin/env python3
"""
Diagnostic script to test OmicsOracle pipeline initialization.
This script will help identify why the pipeline is not initializing properly in the FastAPI app.
"""

import logging
import os
from pathlib import Path

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("diagnostics")

# Add project root to path
# Set NCBI email in environment
os.environ["NCBI_EMAIL"] = "omicsoracle@example.com"
logger.info(f"Set NCBI_EMAIL environment variable to {os.environ['NCBI_EMAIL']}")

# Try to import Bio.Entrez and set email
try:
    from Bio import Entrez

    Entrez.email = "omicsoracle@example.com"
    logger.info(f"Set Bio.Entrez.email to {Entrez.email}")
except ImportError as e:
    logger.error(f"Failed to import Bio.Entrez: {e}")
    logger.info("Checking if biopython is installed...")
    try:
        import pkg_resources

        biopython_version = pkg_resources.get_distribution("biopython").version
        logger.info(f"Biopython version: {biopython_version}")
    except Exception as e:
        logger.error(f"Error checking biopython: {e}")

# Now try to import and initialize the OmicsOracle components
try:
    logger.info("Importing Config...")
    from src.omics_oracle.core.config import Config

    logger.info("Config imported successfully")

    logger.info("Importing OmicsOracle...")
    from src.omics_oracle.pipeline.pipeline import OmicsOracle

    logger.info("OmicsOracle imported successfully")

    # Create configuration
    logger.info("Creating Config object...")
    config = Config()
    logger.info("Config object created")

    # Check NCBI email configuration
    if hasattr(config, "ncbi"):
        if hasattr(config.ncbi, "email"):
            logger.info(f"NCBI email in config: {config.ncbi.email}")
            if not config.ncbi.email:
                logger.info("Setting NCBI email in config object...")
                setattr(config.ncbi, "email", "omicsoracle@example.com")
                logger.info(f"NCBI email set to: {config.ncbi.email}")
        else:
            logger.warning("Config.ncbi does not have email attribute")
    else:
        logger.warning("Config object does not have ncbi attribute")

    # Try to initialize the pipeline
    logger.info("Initializing OmicsOracle pipeline...")
    try:
        pipeline = OmicsOracle(config, disable_cache=True)
        logger.info("Pipeline initialized successfully")

        # Check pipeline components
        if hasattr(pipeline, "geo_client"):
            logger.info(f"GEO client initialized: {pipeline.geo_client is not None}")
            if hasattr(pipeline.geo_client, "ncbi_client"):
                logger.info(f"NCBI client initialized: {pipeline.geo_client.ncbi_client is not None}")
            else:
                logger.warning("GEO client does not have ncbi_client attribute")
        else:
            logger.warning("Pipeline does not have geo_client attribute")

        if hasattr(pipeline, "summarizer"):
            logger.info(f"Summarizer initialized: {pipeline.summarizer is not None}")
            if hasattr(pipeline.summarizer, "client"):
                logger.info(f"OpenAI client initialized: {pipeline.summarizer.client is not None}")
            else:
                logger.warning("Summarizer does not have client attribute")
        else:
            logger.warning("Pipeline does not have summarizer attribute")

    except Exception as e:
        logger.error(f"Failed to initialize pipeline: {e}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")

except Exception as e:
    logger.error(f"Error during setup: {e}")
    import traceback

    logger.error(f"Traceback: {traceback.format_exc()}")

logger.info("Diagnostic script completed")
