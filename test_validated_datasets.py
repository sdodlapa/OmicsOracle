#!/usr/bin/env python3
"""
Test with datasets that should have database records.
Search for datasets we validated in Phase 5.
"""

import asyncio
import logging

import httpx

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def test_with_validated_dataset():
    """Test with a dataset from our Phase 5 validation."""

    logger.info("=" * 80)
    logger.info("Testing with datasets from Phase 5 validation")
    logger.info("=" * 80)

    # These GEO IDs were used in Phase 5 validation
    test_geo_ids = [
        "GSE68849",  # Breast cancer - used in validation
        "GSE75688",  # Another validated dataset
        "GSE89116",  # Phase E dataset
    ]

    async with httpx.AsyncClient(timeout=60.0) as client:
        for geo_id in test_geo_ids:
            logger.info(f"\n🔍 Searching for: {geo_id}")
            logger.info("-" * 80)

            # Search for specific GEO ID
            response = await client.post(
                "http://localhost:8000/api/agents/search",
                json={
                    "search_terms": [geo_id],
                    "max_results": 5,
                    "enable_semantic": False,
                },
            )

            if response.status_code != 200:
                logger.error(f"❌ Search failed: {response.status_code}")
                continue

            data = response.json()
            datasets = data.get("datasets", [])

            if not datasets:
                logger.warning(f"   No results found")
                continue

            # Check first result
            dataset = datasets[0]
            logger.info(f"\n✅ Found: {dataset.get('geo_id')}")
            logger.info(f"   Title: {dataset.get('title', '')[:60]}...")
            logger.info(f"   ")
            logger.info(f"   📊 DATABASE METRICS:")
            logger.info(f"      Citations in DB: {dataset.get('citation_count', 0)}")
            logger.info(f"      PDFs downloaded: {dataset.get('pdf_count', 0)}")
            logger.info(f"      Papers processed: {dataset.get('processed_count', 0)}")
            logger.info(f"      Completion rate: {dataset.get('completion_rate', 0):.1f}%")
            logger.info(f"   ")
            logger.info(f"   🔗 SEARCH RESULT DATA:")
            logger.info(f"      PubMed IDs: {len(dataset.get('pubmed_ids', []))}")
            logger.info(f"      Fulltext count: {dataset.get('fulltext_count', 0)}")
            logger.info(f"      Fulltext status: {dataset.get('fulltext_status', 'unknown')}")

            # Button state analysis
            citation_count = dataset.get("citation_count", 0)
            fulltext_count = dataset.get("fulltext_count", 0)

            logger.info(f"   ")
            logger.info(f"   🎛️  BUTTON STATES:")

            if citation_count > 0:
                if fulltext_count > 0:
                    logger.info(f"      ✅ Download Papers: SUCCESS (already downloaded)")
                    logger.info(f"      🟢 AI Analysis: ENABLED ({fulltext_count} PDFs)")
                else:
                    logger.info(f"      🔵 Download Papers: ENABLED ({citation_count} in DB)")
                    logger.info(f"      ⚪ AI Analysis: DISABLED (needs PDFs)")
            else:
                logger.info(f"      ⚪ Download Papers: DISABLED (no citations)")
                logger.info(f"      ⚪ AI Analysis: DISABLED (no citations)")

            # Check consistency
            logger.info(f"   ")
            logger.info(f"   ✓ DATA CONSISTENCY CHECK:")

            pubmed_count = len(dataset.get("pubmed_ids", []))
            if citation_count == pubmed_count and citation_count > 0:
                logger.warning(
                    f"      ⚠️  citation_count ({citation_count}) == pubmed_ids.length ({pubmed_count})"
                )
                logger.warning(f"         This might indicate data is from search, not database!")
            elif citation_count > 0:
                logger.info(
                    f"      ✅ citation_count ({citation_count}) != pubmed_ids.length ({pubmed_count})"
                )
                logger.info(f"         Good! Data is from database, not search results")
            else:
                logger.info(f"      ℹ️  No citations in database yet (expected for new datasets)")


async def check_database_directly():
    """Check database directly to see what we have."""
    from omics_oracle_v2.lib.storage.queries import DatabaseQueries

    logger.info("\n" + "=" * 80)
    logger.info("Direct Database Check")
    logger.info("=" * 80)

    db = DatabaseQueries(db_path="data/database/search_data.db")

    # Get overall stats
    stats = db.get_processing_statistics()

    logger.info(f"\n📊 DATABASE STATISTICS:")
    logger.info(f"   Total GEO datasets: {stats.get('total_geo_datasets', 0)}")
    logger.info(f"   Total publications: {stats.get('total_publications', 0)}")
    logger.info(f"   Publications with PDFs: {stats.get('publications_with_pdf', 0)}")
    logger.info(f"   Publications with extraction: {stats.get('publications_with_extraction', 0)}")
    logger.info(f"   Database size: {stats.get('database_size_mb', 0):.2f} MB")

    # Try to get specific GEO stats
    test_ids = ["GSE68849", "GSE75688", "GSE89116"]

    logger.info(f"\n📋 CHECKING SPECIFIC GEO DATASETS:")
    for geo_id in test_ids:
        try:
            geo_stats = db.get_geo_statistics(geo_id)
            pub_counts = geo_stats.get("publication_counts", {})

            if pub_counts.get("total", 0) > 0:
                logger.info(f"\n   ✅ {geo_id}:")
                logger.info(f"      Total papers: {pub_counts.get('total', 0)}")
                logger.info(f"      With PDFs: {pub_counts.get('with_pdf', 0)}")
                logger.info(f"      With extraction: {pub_counts.get('with_extraction', 0)}")
                logger.info(f"      Completion: {geo_stats.get('completion_rate', 0):.1f}%")
            else:
                logger.info(f"   ⚪ {geo_id}: No data in database")
        except Exception as e:
            logger.info(f"   ❌ {geo_id}: Error - {e}")


async def main():
    """Run all tests."""
    # First check database
    await check_database_directly()

    # Then test API with those datasets
    await test_with_validated_dataset()

    logger.info("\n" + "=" * 80)
    logger.info("✅ Testing Complete")
    logger.info("=" * 80)
    logger.info("\n💡 OBSERVATIONS:")
    logger.info("   1. If citation_count = 0: Dataset not in database yet (NEW)")
    logger.info("   2. If citation_count > 0: Database integration working!")
    logger.info("   3. If citation_count = pubmed_ids.length: Might be from search (investigate)")
    logger.info("   4. If citation_count != pubmed_ids.length: Correctly using database!")
    logger.info("\n")


if __name__ == "__main__":
    asyncio.run(main())
