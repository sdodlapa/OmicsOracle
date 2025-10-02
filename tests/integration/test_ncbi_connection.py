#!/usr/bin/env python3
"""
Test script to verify NCBI connection is working properly.

This script focuses specifically on setting up Bio.Entrez and
ensuring GEO connectivity works correctly.
"""

import logging
import os
import sys
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add project root to path
# Set NCBI email
os.environ["NCBI_EMAIL"] = "omicsoracle@example.com"

# Import Bio.Entrez and set email
try:
    from Bio import Entrez

    Entrez.email = "omicsoracle@example.com"
    logger.info(f"Set Bio.Entrez.email to {Entrez.email}")
except ImportError:
    logger.warning("Bio.Entrez not available")

# Import our GEO client
from omics_oracle.geo_tools.geo_client import NCBIDirectClient


def test_ncbi_connection():
    """Test direct connection to NCBI E-utilities."""
    logger.info("Testing NCBI direct connection...")

    client = NCBIDirectClient(email="omicsoracle@example.com", verify_ssl=False)

    # Test search
    try:
        logger.info("Searching GEO for 'cancer RNA-seq'...")
        search_results = client.search_geo("cancer RNA-seq", retmax=5)
        logger.info(f"Search successful! Found {len(search_results)} results")

        if search_results:
            for i, result in enumerate(search_results[:3]):
                logger.info(f"Result {i+1}: {result}")

        return True
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return False


if __name__ == "__main__":
    if test_ncbi_connection():
        logger.info("NCBI connection test successful!")
        sys.exit(0)
    else:
        logger.error("NCBI connection test failed!")
        sys.exit(1)
