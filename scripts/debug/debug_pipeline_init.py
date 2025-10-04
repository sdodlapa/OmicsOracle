#!/usr/bin/env python
"""
OmicsOracle Pipeline Initialization Debugger

This script systematically tests and debugs the OmicsOracle pipeline initialization
process, identifying issues that may prevent proper startup.
"""

import importlib.util
import logging
import os
import time
import traceback
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("pipeline_init_debug.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("pipeline_debug")

# Add project root to path
script_path = Path(__file__).resolve()
project_root = script_path.parent
logger.info(f"Project root: {project_root}")


def test_imports():
    """Test importing key modules"""
    logger.info("Testing imports...")

    imports_to_test = [
        "src.omics_oracle.core.config",
        "src.omics_oracle.pipeline.pipeline",
        "src.omics_oracle.services.summarizer",
        "src.omics_oracle.geo_tools.geo_client",
        "Bio.Entrez",
    ]

    success_count = 0
    for module_name in imports_to_test:
        try:
            module = __import__(module_name, fromlist=[""])
            logger.info(f"✓ Successfully imported {module_name}")
            success_count += 1
        except ImportError as e:
            logger.error(f"✗ Failed to import {module_name}: {e}")

    logger.info(f"Import test results: {success_count}/{len(imports_to_test)} successful")
    return success_count == len(imports_to_test)


def test_ncbi_email_config():
    """Test NCBI email configuration"""
    logger.info("Testing NCBI email configuration...")

    # Check environment variable
    ncbi_email_env = os.environ.get("NCBI_EMAIL")
    if ncbi_email_env:
        logger.info(f"✓ NCBI_EMAIL environment variable is set: {ncbi_email_env}")
    else:
        logger.warning("✗ NCBI_EMAIL environment variable is not set")
        # Set it for further tests
        os.environ["NCBI_EMAIL"] = "omicsoracle@example.com"
        logger.info("Set NCBI_EMAIL to omicsoracle@example.com for testing")

    # Check Bio.Entrez email setting
    try:
        from Bio import Entrez

        if hasattr(Entrez, "email") and Entrez.email:
            logger.info(f"✓ Bio.Entrez.email is set: {Entrez.email}")
        else:
            logger.warning("✗ Bio.Entrez.email is not set")
            # Set it for further tests
            Entrez.email = os.environ.get("NCBI_EMAIL", "omicsoracle@example.com")
            logger.info(f"Set Bio.Entrez.email to {Entrez.email}")
    except ImportError:
        logger.error("✗ Failed to import Bio.Entrez")
        return False

    return True


def test_config_loading():
    """Test loading the configuration"""
    logger.info("Testing configuration loading...")

    try:
        from src.omics_oracle.core.config import Config

        config = Config()
        logger.info("✓ Successfully created Config object")

        # Check NCBI configuration
        if hasattr(config, "ncbi"):
            logger.info("✓ Config has ncbi attribute")
            if hasattr(config.ncbi, "email"):
                logger.info(f"✓ Config.ncbi.email is set: {config.ncbi.email}")
            else:
                logger.warning("✗ Config.ncbi.email is not set")
                setattr(
                    config.ncbi,
                    "email",
                    os.environ.get("NCBI_EMAIL", "omicsoracle@example.com"),
                )
                logger.info(f"Set config.ncbi.email to {config.ncbi.email}")
        else:
            logger.error("✗ Config does not have ncbi attribute")
            return False

        return True
    except Exception as e:
        logger.error(f"✗ Failed to load configuration: {e}")
        logger.error(traceback.format_exc())
        return False


def test_geo_client():
    """Test GEO client initialization"""
    logger.info("Testing GEO client initialization...")

    try:
        from src.omics_oracle.core.config import Config
        from src.omics_oracle.geo_tools.geo_client import GEOClient

        config = Config()
        if hasattr(config, "ncbi") and not hasattr(config.ncbi, "email"):
            setattr(
                config.ncbi,
                "email",
                os.environ.get("NCBI_EMAIL", "omicsoracle@example.com"),
            )

        geo_client = GEOClient(config, disable_cache=True)
        logger.info("✓ Successfully initialized GEO client")

        return True
    except Exception as e:
        logger.error(f"✗ Failed to initialize GEO client: {e}")
        logger.error(traceback.format_exc())
        return False


def test_summarizer():
    """Test summarizer initialization"""
    logger.info("Testing summarizer initialization...")

    try:
        from src.omics_oracle.core.config import Config
        from src.omics_oracle.services.summarizer import Summarizer

        config = Config()
        summarizer = Summarizer(config, disable_cache=True)
        logger.info("✓ Successfully initialized Summarizer")

        return True
    except Exception as e:
        logger.error(f"✗ Failed to initialize Summarizer: {e}")
        logger.error(traceback.format_exc())
        return False


def test_pipeline_init():
    """Test pipeline initialization"""
    logger.info("Testing pipeline initialization...")

    try:
        from src.omics_oracle.core.config import Config
        from src.omics_oracle.pipeline.pipeline import OmicsOracle

        # Ensure NCBI email is set in environment
        if "NCBI_EMAIL" not in os.environ:
            os.environ["NCBI_EMAIL"] = "omicsoracle@example.com"
            logger.info("Set NCBI_EMAIL environment variable for testing")

        # Ensure Bio.Entrez.email is set
        try:
            from Bio import Entrez

            if not hasattr(Entrez, "email") or not Entrez.email:
                Entrez.email = os.environ["NCBI_EMAIL"]
                logger.info(f"Set Bio.Entrez.email to {Entrez.email}")
        except ImportError:
            pass

        config = Config()

        # Ensure config.ncbi.email is set
        if hasattr(config, "ncbi") and not hasattr(config.ncbi, "email"):
            setattr(config.ncbi, "email", os.environ["NCBI_EMAIL"])
            logger.info(f"Set config.ncbi.email to {config.ncbi.email}")

        # Log all environment variables for debugging
        logger.debug("Environment variables:")
        for key, value in os.environ.items():
            if "EMAIL" in key or "NCBI" in key or "PATH" in key:
                logger.debug(f"  {key}={value}")

        start_time = time.time()
        logger.info("Creating OmicsOracle pipeline instance...")
        pipeline = OmicsOracle(config, disable_cache=True)
        end_time = time.time()

        if pipeline:
            logger.info(f"✓ Successfully initialized OmicsOracle pipeline in {end_time - start_time:.2f}s")

            # Check critical components
            if hasattr(pipeline, "geo_client") and pipeline.geo_client:
                logger.info("✓ Pipeline has initialized geo_client")
            else:
                logger.warning("✗ Pipeline does not have geo_client initialized")

            if hasattr(pipeline, "summarizer") and pipeline.summarizer:
                logger.info("✓ Pipeline has initialized summarizer")
            else:
                logger.warning("✗ Pipeline does not have summarizer initialized")

            return True
        else:
            logger.error("✗ Pipeline initialization returned None")
            return False

    except Exception as e:
        logger.error(f"✗ Failed to initialize pipeline: {e}")
        logger.error(traceback.format_exc())
        return False


def test_simple_query():
    """Test a simple query to verify pipeline functionality"""
    logger.info("Testing simple query...")

    try:
        import asyncio

        from src.omics_oracle.core.config import Config
        from src.omics_oracle.pipeline.pipeline import OmicsOracle

        config = Config()
        pipeline = OmicsOracle(config, disable_cache=True)

        # Test with a simple query
        test_query = "cancer RNA-seq"
        logger.info(f"Running test query: '{test_query}'")

        # Create an event loop for async execution
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Run the query with a timeout
        try:
            result = loop.run_until_complete(
                asyncio.wait_for(
                    pipeline.process_query(test_query, max_results=2),
                    timeout=30,
                )
            )

            if result and hasattr(result, "geo_ids") and result.geo_ids:
                logger.info(f"✓ Successfully retrieved {len(result.geo_ids)} GEO IDs")
                logger.info(f"  First few GEO IDs: {result.geo_ids[:3]}")
                return True
            else:
                logger.warning("✗ Query returned no results")
                return False

        except asyncio.TimeoutError:
            logger.error("✗ Query timed out after 30 seconds")
            return False
        finally:
            loop.close()

    except Exception as e:
        logger.error(f"✗ Failed to run simple query: {e}")
        logger.error(traceback.format_exc())
        return False


def run_all_tests():
    """Run all tests and provide a summary"""
    logger.info("=" * 50)
    logger.info("OMICSORACLE PIPELINE INITIALIZATION TESTS")
    logger.info("=" * 50)

    tests = [
        ("Import Test", test_imports),
        ("NCBI Email Configuration", test_ncbi_email_config),
        ("Configuration Loading", test_config_loading),
        ("GEO Client Initialization", test_geo_client),
        ("Summarizer Initialization", test_summarizer),
        ("Pipeline Initialization", test_pipeline_init),
        ("Simple Query Test", test_simple_query),
    ]

    results = []
    for name, test_func in tests:
        logger.info("\n" + "=" * 30)
        logger.info(f"Running: {name}")
        logger.info("=" * 30)

        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            logger.error(f"Test '{name}' failed with unhandled exception: {e}")
            logger.error(traceback.format_exc())
            results.append((name, False))

    # Print summary
    logger.info("\n\n" + "=" * 50)
    logger.info("TEST SUMMARY")
    logger.info("=" * 50)

    success_count = 0
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{status}: {name}")
        if result:
            success_count += 1

    logger.info(f"\nOverall: {success_count}/{len(results)} tests passed")

    # Provide recommendations
    logger.info("\n" + "=" * 50)
    logger.info("RECOMMENDATIONS")
    logger.info("=" * 50)

    if all(result for _, result in results):
        logger.info("All tests passed! The pipeline should be working correctly.")
        logger.info("If you're still experiencing issues, check the following:")
        logger.info("1. Network connectivity to NCBI servers")
        logger.info("2. Frontend-backend integration")
        logger.info("3. WebSocket connection stability")
    else:
        logger.info("Some tests failed. Recommendations:")

        test_dict = dict(results)

        if not test_dict.get("Import Test", True):
            logger.info("- Check your Python path and make sure all required packages are installed")
            logger.info("  Run: pip install -r requirements.txt")

        if not test_dict.get("NCBI Email Configuration", True):
            logger.info("- Set the NCBI_EMAIL environment variable")
            logger.info("  Example: export NCBI_EMAIL=your.email@example.com")

        if not test_dict.get("Configuration Loading", True):
            logger.info("- Check your configuration files for errors")
            logger.info("- Ensure the configuration directory exists and is readable")

        if not test_dict.get("GEO Client Initialization", True):
            logger.info("- Verify Bio.Entrez is installed correctly")
            logger.info("- Check network connectivity to NCBI servers")

        if not test_dict.get("Pipeline Initialization", True):
            logger.info("- Check all the dependencies needed for the pipeline")
            logger.info("- Look for detailed error messages in the log")
            logger.info("- Try running with increased logging verbosity")

        if not test_dict.get("Simple Query Test", True):
            logger.info("- Test your network connection to NCBI")
            logger.info("- Verify the NCBI API is not rate-limiting your requests")
            logger.info("- Check if the pipeline components are working individually")


if __name__ == "__main__":
    run_all_tests()
