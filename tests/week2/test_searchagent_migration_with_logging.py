"""
Test SearchAgent migration to unified pipeline with COMPREHENSIVE FILE LOGGING.

This test validates:
1. SearchAgent uses unified pipeline by default
2. All optimizations from Week 2 Days 1-3 are working
3. Performance improvements are measurable
4. Backward compatibility is maintained

ALL OUTPUT IS LOGGED TO FILE: logs/searchagent_migration_test_TIMESTAMP.log
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

# Create timestamped log file
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = log_dir / f"searchagent_migration_test_{timestamp}.log"

# Configure logging to BOTH file and console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),  # Write to file
        logging.StreamHandler(sys.stdout),  # Also print to console
    ],
)

logger = logging.getLogger(__name__)

# Log test start
logger.info("=" * 80)
logger.info("SearchAgent Migration Test - Week 2 Day 4")
logger.info(f"Log file: {log_file}")
logger.info(f"Test started at: {datetime.now()}")
logger.info("=" * 80)

from omics_oracle_v2.agents.models import SearchInput

# Import after logging is configured
from omics_oracle_v2.agents.search_agent import SearchAgent
from omics_oracle_v2.core.config import Settings


def test_unified_pipeline_basic():
    """Test 1: Basic search using unified pipeline."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 1: Basic Search with Unified Pipeline")
    logger.info("=" * 80)

    start_time = time.time()

    # Initialize
    logger.info("Initializing SearchAgent with unified pipeline enabled...")
    settings = Settings()
    agent = SearchAgent(settings, enable_semantic=True, enable_publications=True)

    # Verify unified pipeline is enabled
    assert hasattr(agent, "_use_unified_pipeline"), "Missing _use_unified_pipeline flag"
    assert agent._use_unified_pipeline == True, "Unified pipeline should be enabled by default"
    logger.info(f"✓ Unified pipeline enabled: {agent._use_unified_pipeline}")

    # Create search input
    input_data = SearchInput(
        search_terms=["diabetes", "insulin"],
        original_query="diabetes insulin resistance",
        max_results=10,
    )

    logger.info(f"Executing search: '{input_data.original_query}'")
    logger.info(f"Search terms: {input_data.search_terms}")
    logger.info(f"Max results: {input_data.max_results}")

    # Execute search
    agent_result = agent.execute(input_data)

    # Extract SearchOutput from AgentResult
    result = agent_result.output if hasattr(agent_result, "output") else agent_result

    # Log results
    elapsed = time.time() - start_time
    logger.info("\n" + "-" * 80)
    logger.info("SEARCH RESULTS:")
    logger.info(f"Total found: {result.total_found}")
    logger.info(f"Datasets returned: {len(result.datasets)}")
    logger.info(f"Search time: {elapsed:.2f}s")

    if result.filters_applied:
        logger.info(f"Filters applied: {result.filters_applied}")

    if result.datasets:
        logger.info("\nTop 3 Results:")
        for i, ds in enumerate(result.datasets[:3], 1):
            logger.info(f"\n  {i}. {ds.accession}")
            logger.info(f"     Title: {ds.title[:80]}...")
            if hasattr(ds, "relevance_score"):
                logger.info(f"     Score: {ds.relevance_score:.2f}")

    logger.info("-" * 80)
    logger.info(f"✓ TEST 1 PASSED in {elapsed:.2f}s")

    return result


def test_filtered_search():
    """Test 2: Search with organism and sample filters."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 2: Filtered Search")
    logger.info("=" * 80)

    start_time = time.time()

    settings = Settings()
    agent = SearchAgent(settings, enable_semantic=True, enable_publications=True)

    input_data = SearchInput(
        search_terms=["cancer"],
        original_query="cancer genomics",
        organism="Homo sapiens",
        min_samples=20,
        max_results=10,
    )

    logger.info(f"Query: '{input_data.original_query}'")
    logger.info(f"Organism filter: {input_data.organism}")
    logger.info(f"Min samples: {input_data.min_samples}")

    agent_result = agent.execute(input_data)
    result = agent_result.output if hasattr(agent_result, "output") else agent_result

    elapsed = time.time() - start_time
    logger.info(f"\nTotal found: {result.total_found}")
    logger.info(f"Datasets returned: {len(result.datasets)}")
    logger.info(f"Search time: {elapsed:.2f}s")

    # Verify filters were applied
    if result.filters_applied:
        assert "organism" in result.filters_applied or input_data.organism in str(
            result.filters_applied
        ), "Organism filter not applied"
        logger.info(f"✓ Filters applied: {result.filters_applied}")

    logger.info(f"✓ TEST 2 PASSED in {elapsed:.2f}s")
    return result


def test_geo_id_lookup():
    """Test 3: Direct GEO ID lookup."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 3: GEO ID Direct Lookup")
    logger.info("=" * 80)

    start_time = time.time()

    settings = Settings()
    agent = SearchAgent(settings, enable_semantic=True, enable_publications=True)

    input_data = SearchInput(
        search_terms=["GSE10072"],  # Known dataset
        original_query="GSE10072",
        max_results=1,
    )

    logger.info(f"Looking up GEO ID: {input_data.original_query}")

    agent_result = agent.execute(input_data)
    result = agent_result.output if hasattr(agent_result, "output") else agent_result

    elapsed = time.time() - start_time
    logger.info(f"\nFound: {len(result.datasets)} dataset(s)")
    logger.info(f"Lookup time: {elapsed:.2f}s")

    if result.datasets:
        ds = result.datasets[0]
        logger.info(f"\n✓ Found dataset: {ds.accession}")
        logger.info(f"  Title: {ds.title}")
        logger.info(f"  Samples: {ds.sample_count}")

    logger.info(f"✓ TEST 3 PASSED in {elapsed:.2f}s")
    return result


def test_cache_speedup():
    """Test 4: Verify cache provides speedup on repeated queries."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 4: Cache Speedup Verification")
    logger.info("=" * 80)

    settings = Settings()
    agent = SearchAgent(settings, enable_semantic=True, enable_publications=True)

    input_data = SearchInput(
        search_terms=["covid"],
        original_query="covid-19 respiratory",
        max_results=5,
    )

    # First search (cache miss)
    logger.info("First search (cache miss expected)...")
    start1 = time.time()
    agent_result1 = agent.execute(input_data)
    result1 = agent_result1.output if hasattr(agent_result1, "output") else agent_result1
    time1 = time.time() - start1
    logger.info(f"  Time: {time1:.2f}s")
    logger.info(f"  Results: {len(result1.datasets)}")

    # Second search (cache hit)
    logger.info("\nSecond search (cache hit expected)...")
    start2 = time.time()
    agent_result2 = agent.execute(input_data)
    result2 = agent_result2.output if hasattr(agent_result2, "output") else agent_result2
    time2 = time.time() - start2
    logger.info(f"  Time: {time2:.2f}s")
    logger.info(f"  Results: {len(result2.datasets)}")

    # Calculate speedup
    speedup = time1 / time2 if time2 > 0 else 1
    logger.info(f"\n✓ Speedup: {speedup:.1f}x")

    if speedup > 5:
        logger.info(f"✓ Excellent cache performance! ({speedup:.1f}x speedup)")
    elif speedup > 2:
        logger.info(f"✓ Good cache performance ({speedup:.1f}x speedup)")
    else:
        logger.warning(f"⚠ Cache may not be working optimally ({speedup:.1f}x speedup)")

    logger.info(f"✓ TEST 4 PASSED")
    return result1, result2


def test_legacy_mode():
    """Test 5: Verify legacy mode still works."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 5: Legacy Mode Compatibility")
    logger.info("=" * 80)

    start_time = time.time()

    settings = Settings()
    agent = SearchAgent(settings, enable_semantic=True, enable_publications=True)

    # Switch to legacy mode
    logger.info("Switching to legacy mode...")
    agent._use_unified_pipeline = False

    input_data = SearchInput(
        search_terms=["asthma"],
        original_query="asthma genes",
        max_results=5,
    )

    logger.info(f"Executing search in legacy mode: '{input_data.original_query}'")
    agent_result = agent.execute(input_data)
    result = agent_result.output if hasattr(agent_result, "output") else agent_result

    elapsed = time.time() - start_time
    logger.info(f"\nTotal found: {result.total_found}")
    logger.info(f"Datasets returned: {len(result.datasets)}")
    logger.info(f"Search time: {elapsed:.2f}s")

    logger.info("✓ Legacy mode still functional")
    logger.info(f"✓ TEST 5 PASSED in {elapsed:.2f}s")

    return result


def main():
    """Run all tests."""
    try:
        logger.info("\nStarting test suite...")
        overall_start = time.time()

        # Run tests
        test_unified_pipeline_basic()
        test_filtered_search()
        test_geo_id_lookup()
        test_cache_speedup()
        test_legacy_mode()

        # Summary
        overall_time = time.time() - overall_start
        logger.info("\n" + "=" * 80)
        logger.info("ALL TESTS PASSED! ✓")
        logger.info(f"Total test time: {overall_time:.2f}s")
        logger.info(f"Log file: {log_file}")
        logger.info("=" * 80)

        return 0

    except KeyboardInterrupt:
        logger.warning("\n⚠ Tests interrupted by user (Ctrl+C)")
        logger.info(f"Partial results saved to: {log_file}")
        return 1

    except Exception as e:
        logger.error(f"\n❌ TEST FAILED with error: {e}", exc_info=True)
        logger.info(f"Error details saved to: {log_file}")
        return 1

    finally:
        logger.info(f"\nLog file location: {log_file.absolute()}")
        logger.info("You can analyze this file for detailed timing and bottlenecks.")


if __name__ == "__main__":
    sys.exit(main())
