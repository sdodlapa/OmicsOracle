#!/usr/bin/env python
"""
NCBI Client Configuration Validator for OmicsOracle

This script validates the NCBI client configuration and tests connectivity
with the NCBI Entrez API.
"""

import asyncio
import logging
import os
import sys

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("ncbi_validator")

# Add project root to path and import modules
from src.omics_oracle.core.config import Config
from src.omics_oracle.geo_tools.geo_client import UnifiedGEOClient


async def test_direct_ncbi_query():
    """Test direct query to NCBI Entrez."""
    try:
        from Bio import Entrez

        # Get email from environment or config
        email = os.environ.get("NCBI_EMAIL")
        if not email:
            config = Config()
            email = getattr(config.ncbi, "email", None)

        if not email:
            logger.error("No NCBI_EMAIL found in environment or config")
            return False

        logger.info(f"Using email: {email}")
        Entrez.email = email

        # Simple test query
        logger.info("Performing test query to NCBI Entrez...")
        handle = Entrez.esearch(db="gds", term="methylation[All Fields]", retmax=5)
        record = Entrez.read(handle)
        handle.close()

        if "IdList" in record and record["IdList"]:
            logger.info(f"Successfully queried NCBI. Found {len(record['IdList'])} results.")
            logger.info(f"First 5 IDs: {record['IdList'][:5]}")
            return True
        else:
            logger.warning("Query successful but no results returned.")
            return False

    except Exception as e:
        logger.error(f"Error during direct NCBI query: {str(e)}", exc_info=True)
        return False


async def validate_geo_client():
    """Validate the GEO client configuration and connectivity."""
    logger.info("Validating GEO client configuration...")

    # Load configuration
    config = Config()

    # Check NCBI configuration
    if hasattr(config, "ncbi") and hasattr(config.ncbi, "email"):
        logger.info(f"NCBI email in config: {config.ncbi.email}")
    else:
        logger.error("NCBI email not found in config!")

    # Check environment variables
    ncbi_email_env = os.environ.get("NCBI_EMAIL")
    logger.info(f"NCBI_EMAIL environment variable: {ncbi_email_env or 'Not set'}")

    # Initialize GEO client
    try:
        geo_client = UnifiedGEOClient(config)
        logger.info("GEO client initialized successfully")

        # Inspect GEO client
        if hasattr(geo_client, "_client") and hasattr(geo_client._client, "email"):
            logger.info(f"GEO client email: {geo_client._client.email}")
        else:
            logger.warning("GEO client doesn't have expected email attribute structure")

        # Test search
        logger.info("Testing GEO search...")
        result = await geo_client.search_geo("methylation", max_results=5)

        logger.info(f"Search results: {len(result) if result else 0} items")
        if result:
            logger.info(f"First result: {result[0]}")
            return True
        else:
            logger.warning("No search results found")
            return False

    except Exception as e:
        logger.error(f"Error validating GEO client: {str(e)}", exc_info=True)
        return False
    finally:
        if "geo_client" in locals():
            await geo_client.close()


async def check_env_files():
    """Check environment files for NCBI configuration."""
    env_files = [".env", ".env.development"]
    found_config = False

    for env_file in env_files:
        if os.path.exists(env_file):
            logger.info(f"Found {env_file}:")
            with open(env_file, "r") as f:
                content = f.read()
                if "NCBI_EMAIL" in content:
                    logger.info(f"  NCBI_EMAIL is configured in {env_file}")
                    found_config = True

                    # Extract the email value
                    for line in content.splitlines():
                        if line.startswith("NCBI_EMAIL="):
                            value = line.split("=", 1)[1].strip()
                            logger.info(f"  Value: {value}")
                else:
                    logger.info(f"  NCBI_EMAIL not found in {env_file}")

    if not found_config:
        logger.warning("NCBI_EMAIL not found in any environment file")

    return found_config


async def create_env_file():
    """Create a .env file with NCBI configuration if it doesn't exist."""
    if not os.path.exists(".env"):
        logger.info("Creating .env file with NCBI configuration...")
        with open(".env", "w") as f:
            f.write("# OmicsOracle environment configuration\n")
            f.write("NCBI_EMAIL=omicsoracle@example.com\n")
            f.write("NCBI_API_KEY=\n")  # Optional
        logger.info(".env file created successfully")
        return True
    else:
        logger.info(".env file already exists")
        return False


async def fix_ncbi_config():
    """Fix NCBI configuration issues."""
    # Set environment variable directly
    os.environ["NCBI_EMAIL"] = "omicsoracle@example.com"
    logger.info("Set NCBI_EMAIL environment variable directly")

    # Create/update .env
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            content = f.read()

        if "NCBI_EMAIL" not in content:
            with open(".env", "a") as f:
                f.write("\nNCBI_EMAIL=omicsoracle@example.com\n")
            logger.info("Added NCBI_EMAIL to existing .env file")
    else:
        await create_env_file()

    return True


async def main():
    """Main function to run the validation."""
    logger.info("Starting NCBI Client Configuration Validation")
    logger.info(f"Current directory: {os.getcwd()}")

    # Check environment files
    env_found = await check_env_files()

    # Try to fix configuration if needed
    if not env_found:
        await fix_ncbi_config()

    # Validate GEO client
    geo_client_valid = await validate_geo_client()

    # Test direct NCBI query
    ncbi_query_valid = await test_direct_ncbi_query()

    # Final validation status
    if geo_client_valid and ncbi_query_valid:
        logger.info("✅ NCBI configuration is valid and working correctly")
    else:
        logger.warning("⚠️ NCBI configuration has issues that need to be resolved")

        # Recommend solutions
        logger.info("\nRecommended solutions:")
        logger.info(
            "1. Ensure a valid email is set in the .env.local file: NCBI_EMAIL=your_email@example.com"
        )
        logger.info("2. Restart the application to load the updated configuration")
        logger.info("3. Check if your IP is blocked by NCBI (too many requests)")
        logger.info("4. Consider using an NCBI API key for higher request limits")

    logger.info("Validation completed")


if __name__ == "__main__":
    asyncio.run(main())
