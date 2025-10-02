#!/usr/bin/env python3
"""
Test script to debug NCBI email configuration issues.

This script checks all the places where the NCBI email should be set
and ensures they are properly configured.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set NCBI email environment variable FIRST
os.environ["NCBI_EMAIL"] = "omicsoracle@example.com"
logger.info(f"Set NCBI_EMAIL environment variable to: {os.environ['NCBI_EMAIL']}")

# Add project root to path
# Try to import Bio.Entrez directly and set email
try:
    from Bio import Entrez

    Entrez.email = os.environ["NCBI_EMAIL"]
    logger.info(f"Successfully set Bio.Entrez.email to: {Entrez.email}")
except ImportError:
    logger.error("Bio.Entrez not available - install biopython")
    sys.exit(1)

# Import the OmicsOracle config
try:
    from omics_oracle.core.config import Config

    config = Config()
    logger.info("Successfully loaded Config")

    # Check if the config has a ncbi attribute
    if hasattr(config, "ncbi"):
        logger.info("Config has ncbi attribute")

        # Check if the ncbi attribute has an email property
        if hasattr(config.ncbi, "email"):
            logger.info(f"Config has ncbi.email: {config.ncbi.email}")

            # Set it to our email just to be sure
            config.ncbi.email = os.environ["NCBI_EMAIL"]
            logger.info(f"Updated config.ncbi.email to: {config.ncbi.email}")
        else:
            logger.warning("Config has no ncbi.email property - creating it")
            setattr(config.ncbi, "email", os.environ["NCBI_EMAIL"])
            logger.info(f"Created config.ncbi.email: {config.ncbi.email}")
    else:
        logger.warning("Config has no ncbi attribute")
except ImportError:
    logger.error("Failed to import Config")
    sys.exit(1)

# Try to initialize the NCBI client directly
try:
    from omics_oracle.geo_tools.geo_client import NCBIDirectClient

    # Create client with our email
    ncbi_client = NCBIDirectClient(email=os.environ["NCBI_EMAIL"], verify_ssl=False)
    logger.info(f"Successfully created NCBIDirectClient with email: {ncbi_client.email}")

    # Test a simple search function
    async def test_ncbi_search():
        try:
            # Search for a simple term
            ids = await ncbi_client.esearch(
                db="gds",  # GEO DataSets database
                term="cancer RNA-seq human",
                retmax=5,
            )
            logger.info(f"NCBI search successful! Found {len(ids)} results")
            logger.info(f"First 5 IDs: {ids[:5]}")
            return ids
        except Exception as e:
            logger.error(f"NCBI search failed: {e}")
            return []
        finally:
            await ncbi_client.close()

    # Run the test
    results = asyncio.run(test_ncbi_search())

    # Check if we got results
    if results:
        logger.info("✅ NCBI client is working correctly!")
    else:
        logger.error("❌ NCBI client failed to return results")

except ImportError:
    logger.error("Failed to import NCBIDirectClient")
except Exception as e:
    logger.error(f"Error initializing NCBIDirectClient: {e}")

# Now try to initialize the UnifiedGEOClient
try:
    from omics_oracle.geo_tools.geo_client import UnifiedGEOClient

    # Create client with our config
    geo_client = UnifiedGEOClient(config)

    # Check if the NCBI client was initialized
    if hasattr(geo_client, "ncbi_client") and geo_client.ncbi_client:
        logger.info(f"UnifiedGEOClient initialized with NCBI client, email: {geo_client.ncbi_client.email}")
    else:
        logger.error("UnifiedGEOClient failed to initialize NCBI client")

    # Test a simple search function
    async def test_geo_search():
        try:
            # Search for GEO IDs
            geo_ids = await geo_client.search_geo_datasets("cancer RNA-seq human", max_results=5)
            logger.info(f"GEO search successful! Found {len(geo_ids)} results")
            logger.info(f"GEO IDs: {geo_ids}")
            return geo_ids
        except Exception as e:
            logger.error(f"GEO search failed: {e}")
            return []
        finally:
            await geo_client.close()

    # Run the test
    geo_results = asyncio.run(test_geo_search())

    # Check if we got results
    if geo_results:
        logger.info("✅ UnifiedGEOClient is working correctly!")
    else:
        logger.error("❌ UnifiedGEOClient failed to return results")

except ImportError:
    logger.error("Failed to import UnifiedGEOClient")
except Exception as e:
    logger.error(f"Error initializing UnifiedGEOClient: {e}")

logger.info("NCBI configuration test completed.")
