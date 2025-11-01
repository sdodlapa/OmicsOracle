#!/usr/bin/env python3
"""
Quick test to verify cache serialization works for GEO results.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from omics_oracle_v2.lib.geo.models import GEOSeriesMetadata
from omics_oracle_v2.lib.pipelines.unified_search_pipeline import SearchResult

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def test_cache_serialization():
    """Test that SearchResult with GEOSeriesMetadata can be cached."""

    # Create a minimal GEOSeriesMetadata object
    geo_metadata = GEOSeriesMetadata(
        geo_id="GSE123456",
        title="Test Dataset",
        summary="Test summary",
        organism="Homo sapiens",
        sample_count=10,
    )

    # Create a SearchResult
    result = SearchResult(
        query="test query",
        optimized_query="test query",
        query_type="dataset",
        geo_datasets=[geo_metadata],
        publications=[],
        total_results=1,
        search_time_ms=100.0,
    )

    # Test to_dict() method
    logger.info("Testing SearchResult.to_dict()...")
    try:
        result_dict = result.to_dict()
        logger.info("[OK] to_dict() successful")

        # Test JSON serialization
        logger.info("Testing JSON serialization...")
        result_json = json.dumps(result_dict)
        logger.info(f"[OK] JSON serialization successful ({len(result_json)} bytes)")

        # Test deserialization
        logger.info("Testing JSON deserialization...")
        result_dict_restored = json.loads(result_json)
        logger.info("[OK] JSON deserialization successful")

        # Verify data integrity
        assert result_dict_restored["query"] == "test query"
        assert result_dict_restored["total_results"] == 1
        assert len(result_dict_restored["geo_datasets"]) == 1
        assert result_dict_restored["geo_datasets"][0]["geo_id"] == "GSE123456"
        logger.info("[OK] Data integrity verified")

        logger.info("\n" + "=" * 60)
        logger.info("SUCCESS! Cache serialization fix is working!")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"[FAIL] {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(test_cache_serialization())
