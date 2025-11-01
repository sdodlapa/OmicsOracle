#!/usr/bin/env python3
"""
Test script for Phase 9: Quality Validation Integration

Tests the integration of quality validation into the main citation discovery pipeline.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from omics_oracle_v2.lib.pipelines.citation_discovery.geo_discovery import GEOCitationDiscovery
from omics_oracle_v2.lib.pipelines.citation_discovery.quality_validation import QualityConfig, QualityLevel
from omics_oracle_v2.lib.search_engines.geo.client import GEOClient

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def test_default_config():
    """Test with default configuration (quality validation enabled, no filtering)."""
    logger.info("=" * 80)
    logger.info("🧪 Test 1: Default Configuration (No Filtering)")
    logger.info("=" * 80)
    logger.info("")

    # Initialize GEO client
    geo_client = GEOClient()
    geo_metadata = await geo_client.get_metadata("GSE52564", include_sra=False)

    logger.info(f"GEO Dataset: {geo_metadata.title}")
    logger.info(f"Original PMID: {geo_metadata.pubmed_ids[0] if geo_metadata.pubmed_ids else 'None'}")
    logger.info("")

    # Initialize citation discovery with default settings
    discovery = GEOCitationDiscovery(
        enable_cache=True,
        enable_quality_validation=True,  # Quality validation ON
        quality_filter_level=None,  # No filtering
    )

    # Find citing papers
    result = await discovery.find_citing_papers(geo_metadata, max_results=50)

    logger.info("")
    logger.info("📊 Results Summary:")
    logger.info(f"  Papers found: {len(result.citing_papers)}")

    if result.quality_summary:
        logger.info(f"  Quality validation: ENABLED")
        logger.info(f"  Papers assessed: {result.quality_summary['total_assessed']}")
        logger.info(f"  Average quality: {result.quality_summary['average_score']:.3f}")
        logger.info("")
        logger.info("  Quality distribution:")
        for level, count in result.quality_summary["distribution"].items():
            pct = (count / result.quality_summary["total_assessed"]) * 100
            logger.info(f"    {level:12s}: {count:3d} ({pct:5.1f}%)")

    logger.info("")
    return result


async def test_with_filtering():
    """Test with quality filtering enabled."""
    logger.info("\n" + "=" * 80)
    logger.info("🧪 Test 2: Quality Filtering (GOOD+ only)")
    logger.info("=" * 80)
    logger.info("")

    geo_client = GEOClient()
    geo_metadata = await geo_client.get_metadata("GSE52564", include_sra=False)

    # Initialize with GOOD+ filtering
    discovery = GEOCitationDiscovery(
        enable_cache=True,
        enable_quality_validation=True,
        quality_filter_level=QualityLevel.GOOD,  # Filter to GOOD+ only
    )

    result = await discovery.find_citing_papers(geo_metadata, max_results=50)

    logger.info("")
    logger.info("📊 Results Summary:")
    logger.info(f"  Papers found (after filtering): {len(result.citing_papers)}")

    if result.quality_summary:
        logger.info(f"  Quality validation: ENABLED")
        logger.info(f"  Filter level: {result.quality_summary.get('filter_level', 'N/A')}")
        logger.info(f"  Pre-filter count: {result.quality_summary.get('pre_filter_count', 0)}")
        logger.info(f"  Post-filter count: {result.quality_summary.get('post_filter_count', 0)}")
        logger.info(f"  Filtered out: {result.quality_summary.get('filtered_count', 0)}")
        logger.info(
            f"  Filter rate: {(result.quality_summary.get('filtered_count', 0) / result.quality_summary.get('pre_filter_count', 1)) * 100:.1f}%"
        )

    logger.info("")

    # Show top 5 papers
    logger.info("Top 5 Papers (GOOD+ quality):")
    for i, paper in enumerate(result.citing_papers[:5], 1):
        logger.info(f"  {i}. {paper.title[:70]}...")
        logger.info(
            f"     PMID: {paper.pmid or 'N/A'} | Citations: {paper.citations or 0} | "
            f"Year: {paper.publication_date.year if paper.publication_date else 'N/A'}"
        )

    logger.info("")
    return result


async def test_strict_filtering():
    """Test with strict quality filtering (EXCELLENT only)."""
    logger.info("\n" + "=" * 80)
    logger.info("🧪 Test 3: Strict Filtering (EXCELLENT only)")
    logger.info("=" * 80)
    logger.info("")

    geo_client = GEOClient()
    geo_metadata = await geo_client.get_metadata("GSE52564", include_sra=False)

    # Initialize with EXCELLENT-only filtering
    discovery = GEOCitationDiscovery(
        enable_cache=True,
        enable_quality_validation=True,
        quality_filter_level=QualityLevel.EXCELLENT,  # Only EXCELLENT papers
    )

    result = await discovery.find_citing_papers(geo_metadata, max_results=50)

    logger.info("")
    logger.info("📊 Results Summary:")
    logger.info(f"  Papers found (EXCELLENT only): {len(result.citing_papers)}")

    if result.quality_summary:
        logger.info(f"  Pre-filter count: {result.quality_summary.get('pre_filter_count', 0)}")
        logger.info(f"  Post-filter count: {result.quality_summary.get('post_filter_count', 0)}")
        logger.info(f"  Filtered out: {result.quality_summary.get('filtered_count', 0)}")
        logger.info(
            f"  Filter rate: {(result.quality_summary.get('filtered_count', 0) / result.quality_summary.get('pre_filter_count', 1)) * 100:.1f}%"
        )

    logger.info("")
    return result


async def test_custom_config():
    """Test with custom quality configuration."""
    logger.info("\n" + "=" * 80)
    logger.info("🧪 Test 4: Custom Quality Configuration (Strict)")
    logger.info("=" * 80)
    logger.info("")

    geo_client = GEOClient()
    geo_metadata = await geo_client.get_metadata("GSE52564", include_sra=False)

    # Create strict quality config
    strict_config = QualityConfig(
        require_abstract=True,
        require_authors=True,
        min_abstract_length=200,  # Longer abstracts required
        min_citations_recent=10,  # Higher citation bar
        min_citations_older=20,
        check_predatory=True,
        allow_preprints=False,  # No preprints
        min_quality_score=0.5,  # Higher minimum score
    )

    discovery = GEOCitationDiscovery(
        enable_cache=True,
        enable_quality_validation=True,
        quality_config=strict_config,
        quality_filter_level=QualityLevel.ACCEPTABLE,  # Filter with strict config
    )

    result = await discovery.find_citing_papers(geo_metadata, max_results=50)

    logger.info("")
    logger.info("📊 Results Summary (Strict Config):")
    logger.info(f"  Papers found (after strict filtering): {len(result.citing_papers)}")

    if result.quality_summary:
        logger.info(f"  Pre-filter count: {result.quality_summary.get('pre_filter_count', 0)}")
        logger.info(f"  Post-filter count: {result.quality_summary.get('post_filter_count', 0)}")
        logger.info(f"  Filtered out: {result.quality_summary.get('filtered_count', 0)}")
        logger.info(
            f"  Filter rate: {(result.quality_summary.get('filtered_count', 0) / result.quality_summary.get('pre_filter_count', 1)) * 100:.1f}%"
        )

    logger.info("")
    return result


async def test_disabled():
    """Test with quality validation disabled."""
    logger.info("\n" + "=" * 80)
    logger.info("🧪 Test 5: Quality Validation DISABLED")
    logger.info("=" * 80)
    logger.info("")

    geo_client = GEOClient()
    geo_metadata = await geo_client.get_metadata("GSE52564", include_sra=False)

    # Disable quality validation
    discovery = GEOCitationDiscovery(
        enable_cache=True,
        enable_quality_validation=False,  # Quality validation OFF
    )

    result = await discovery.find_citing_papers(geo_metadata, max_results=50)

    logger.info("")
    logger.info("📊 Results Summary:")
    logger.info(f"  Papers found: {len(result.citing_papers)}")
    logger.info(f"  Quality validation: DISABLED")
    logger.info(f"  Quality assessments: {result.quality_assessments is None}")
    logger.info(f"  Quality summary: {result.quality_summary is None}")

    logger.info("")
    return result


async def compare_results():
    """Compare results across different quality configurations."""
    logger.info("\n" + "=" * 80)
    logger.info("📊 Comparison Across Configurations")
    logger.info("=" * 80)
    logger.info("")

    geo_client = GEOClient()
    geo_metadata = await geo_client.get_metadata("GSE52564", include_sra=False)

    configs = [
        ("No filtering", None),
        ("ACCEPTABLE+", QualityLevel.ACCEPTABLE),
        ("GOOD+", QualityLevel.GOOD),
        ("EXCELLENT", QualityLevel.EXCELLENT),
    ]

    results_table = []

    for config_name, filter_level in configs:
        discovery = GEOCitationDiscovery(
            enable_cache=True,
            enable_quality_validation=True,
            quality_filter_level=filter_level,
        )

        result = await discovery.find_citing_papers(geo_metadata, max_results=50)

        pre_count = (
            result.quality_summary.get("pre_filter_count", len(result.citing_papers))
            if result.quality_summary
            else len(result.citing_papers)
        )
        post_count = len(result.citing_papers)
        filtered = pre_count - post_count
        filter_rate = (filtered / pre_count * 100) if pre_count > 0 else 0

        results_table.append(
            {
                "config": config_name,
                "pre_filter": pre_count,
                "post_filter": post_count,
                "filtered": filtered,
                "filter_rate": filter_rate,
            }
        )

    logger.info("Configuration Comparison:")
    logger.info(f"{'Config':<20} {'Pre-Filter':<12} {'Post-Filter':<12} {'Filtered':<10} {'Rate':<10}")
    logger.info("-" * 70)
    for row in results_table:
        logger.info(
            f"{row['config']:<20} {row['pre_filter']:<12} {row['post_filter']:<12} "
            f"{row['filtered']:<10} {row['filter_rate']:>6.1f}%"
        )

    logger.info("")


async def main():
    """Main test function."""
    try:
        # Test 1: Default (no filtering)
        await test_default_config()

        # Test 2: GOOD+ filtering
        await test_with_filtering()

        # Test 3: EXCELLENT only
        await test_strict_filtering()

        # Test 4: Custom config
        await test_custom_config()

        # Test 5: Disabled
        await test_disabled()

        # Comparison
        await compare_results()

        logger.info("=" * 80)
        logger.info("✅ Phase 9 Integration Tests Complete!")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
