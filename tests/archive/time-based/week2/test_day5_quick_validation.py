"""
Quick validation test for Week 2 Day 5 improvements.

Validates in ~2 minutes:
1. Session cleanup (no unclosed warnings)
2. Phase logging clarity (Phase 1 vs Phase 2)
3. Cache metrics visible (hit rate, misses, sets)

Run: python tests/week2/test_day5_quick_validation.py
"""

import asyncio
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

# Create logs directory
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Setup file logging
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = log_dir / f"day5_validation_{timestamp}.log"

# Configure logging to BOTH file and console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)

# Suppress verbose libraries
logging.getLogger("GEOparse").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("aiohttp").setLevel(logging.WARNING)

from omics_oracle_v2.agents.models import SearchInput
from omics_oracle_v2.agents.search_agent import SearchAgent
from omics_oracle_v2.core.config import Settings


def test_quick_validation():
    """Quick test with minimal results to validate improvements."""
    logger.info("\n" + "=" * 80)
    logger.info("QUICK VALIDATION TEST - Week 2 Day 5 Improvements")
    logger.info("=" * 80)

    start_time = time.time()

    # Create agent
    settings = Settings()
    agent = SearchAgent(settings, enable_semantic=True, enable_publications=True)

    # Test 1: Basic search (minimal results)
    logger.info("\nTest 1: Basic search with 2 results...")
    input_data = SearchInput(
        search_terms=["cancer"],
        original_query="cancer",
        max_results=2,  # MINIMAL for speed
    )

    result1 = agent.execute(input_data).output
    logger.info(f"Found {len(result1.datasets)} datasets in {time.time() - start_time:.1f}s")

    # Test 2: Cache hit (should be instant)
    logger.info("\nTest 2: Same query (cache hit)...")
    cache_start = time.time()
    agent.execute(input_data).output  # noqa: F841
    cache_time = time.time() - cache_start
    logger.info(f"Cache retrieval in {cache_time:.3f}s")

    # Test 3: GEO ID lookup (fast path)
    logger.info("\nTest 3: GEO ID direct lookup...")
    geo_start = time.time()
    input_geo = SearchInput(
        search_terms=["GSE123456"],
        original_query="GSE123456",
        max_results=1,
    )
    agent.execute(input_geo).output  # noqa: F841
    geo_time = time.time() - geo_start
    logger.info(f"GEO lookup in {geo_time:.1f}s")

    total_time = time.time() - start_time

    # Cleanup properly
    logger.info("\n" + "=" * 80)
    logger.info("Closing pipeline resources...")
    logger.info("=" * 80)

    if hasattr(agent, "_unified_pipeline") and agent._unified_pipeline:
        asyncio.run(agent._unified_pipeline.close())
        logger.info("Pipeline closed successfully")

    logger.info("\n" + "=" * 80)
    logger.info("VALIDATION COMPLETE!")
    logger.info(f"Total time: {total_time:.2f}s")
    logger.info(f"Log file: {log_file}")
    logger.info("=" * 80)

    # Check for expected outputs
    logger.info("\n" + "=" * 80)
    logger.info("VALIDATION CHECKLIST:")
    logger.info("=" * 80)
    logger.info("1. Check log for 'Phase 1: Adding institutional access URLs'")
    logger.info("2. Check log for 'Phase 2: Verified full-text access'")
    logger.info("3. Check log for 'Cache Metrics:' with hit rate")
    logger.info("4. Check for NO 'Unclosed client session' warnings")
    logger.info(f"\nReview: {log_file}")

    return result1


if __name__ == "__main__":
    logger.info("Week 2 Day 5 - Quick Validation Test")
    logger.info(f"Log file: {log_file}")
    logger.info("")

    try:
        test_quick_validation()
        sys.exit(0)
    except KeyboardInterrupt:
        logger.warning("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\nTEST FAILED: {e}", exc_info=True)
        sys.exit(1)
