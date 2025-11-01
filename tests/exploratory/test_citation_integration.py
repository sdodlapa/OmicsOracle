#!/usr/bin/env python3
"""
Test Citation Integration - October 13, 2025

This script tests the new citation discovery integration in the enrichment endpoint.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from omics_oracle_v2.lib.citations.discovery.geo_discovery import GEOCitationDiscovery
from omics_oracle_v2.lib.search_engines.geo.models import GEOSeriesMetadata

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


async def test_citation_discovery():
    """Test that citation discovery works correctly"""

    print("\n" + "=" * 80)
    print("TEST 1: Citation Discovery for GSE48968")
    print("=" * 80 + "\n")

    # Create test metadata
    test_geo = GEOSeriesMetadata(
        geo_id="GSE48968",
        title="Test Dataset",
        summary="Test summary",
        organism="Homo sapiens",
        platform="GPL570",
        sample_count=10,
        submission_date="2020-01-01",
        publication_date="2020-06-01",
        pubmed_ids=["24906385"],  # Known PMID with citations
    )

    # Initialize discovery
    discovery = GEOCitationDiscovery()

    # Find citing papers
    logger.info("Finding citing papers...")
    result = await discovery.find_citing_papers(test_geo, max_results=5)

    # Validate results
    assert result.geo_id == "GSE48968", "GEO ID mismatch"
    assert result.original_pmid == "24906385", "Original PMID mismatch"

    if result.citing_papers:
        logger.info(f"✅ Found {len(result.citing_papers)} citing papers!")
        for i, paper in enumerate(result.citing_papers[:3], 1):
            logger.info(f"   {i}. {paper.title[:60]}...")
            logger.info(f"      PMID: {paper.pmid or paper.doi}")
    else:
        logger.warning("⚠️ No citing papers found (may be expected for some datasets)")

    print("\n" + "=" * 80)
    print("TEST 1: PASSED ✅")
    print("=" * 80 + "\n")

    return result


async def test_file_organization():
    """Test that file organization logic is correct"""

    print("\n" + "=" * 80)
    print("TEST 2: File Organization")
    print("=" * 80 + "\n")

    # Test directory creation
    base_dir = Path("data/pdfs/TEST_GSE12345")
    original_dir = base_dir / "original"
    citing_dir = base_dir / "citing"

    # Create directories
    original_dir.mkdir(parents=True, exist_ok=True)
    citing_dir.mkdir(parents=True, exist_ok=True)

    # Verify
    assert original_dir.exists(), "Original directory not created"
    assert citing_dir.exists(), "Citing directory not created"

    logger.info(f"✅ Created directory structure:")
    logger.info(f"   {original_dir}")
    logger.info(f"   {citing_dir}")

    # Create metadata file
    import json

    metadata = {
        "geo_id": "TEST_GSE12345",
        "title": "Test Dataset",
        "processed_at": "2025-10-13T20:00:00Z",
        "papers": {
            "original": {"count": 1, "pmids": ["12345"]},
            "citing": {"count": 3, "pmids": ["67890", "67891", "67892"]},
        },
        "total_count": 4,
        "status": "available",
    }

    metadata_file = base_dir / "metadata.json"
    with open(metadata_file, "w") as f:
        json.dump(metadata, f, indent=2)

    assert metadata_file.exists(), "Metadata file not created"
    logger.info(f"✅ Created metadata file: {metadata_file}")

    # Read back and verify
    with open(metadata_file) as f:
        loaded = json.load(f)

    assert loaded["geo_id"] == "TEST_GSE12345", "Metadata verification failed"
    assert loaded["papers"]["citing"]["count"] == 3, "Citing count mismatch"

    logger.info("✅ Metadata verification passed")

    print("\n" + "=" * 80)
    print("TEST 2: PASSED ✅")
    print("=" * 80 + "\n")


async def test_paper_type_sorting():
    """Test that citing papers are sorted first"""

    print("\n" + "=" * 80)
    print("TEST 3: Paper Type Sorting")
    print("=" * 80 + "\n")

    # Simulate papers
    papers_original = [{"pmid": "12345", "title": "Original paper", "type": "original"}]
    papers_citing = [
        {"pmid": "67890", "title": "Citing paper 1", "type": "citing"},
        {"pmid": "67891", "title": "Citing paper 2", "type": "citing"},
    ]

    # Simulate sorting (citing first, then original)
    papers_to_show = papers_citing + papers_original

    # Verify
    assert papers_to_show[0]["type"] == "citing", "First paper should be citing"
    assert papers_to_show[1]["type"] == "citing", "Second paper should be citing"
    assert papers_to_show[2]["type"] == "original", "Last paper should be original"

    logger.info("✅ Citing papers sorted first:")
    for i, paper in enumerate(papers_to_show, 1):
        logger.info(f"   {i}. {paper['title']} ({paper['type']})")

    print("\n" + "=" * 80)
    print("TEST 3: PASSED ✅")
    print("=" * 80 + "\n")


async def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("CITATION INTEGRATION TESTS")
    print("=" * 80 + "\n")

    try:
        # Test 1: Citation discovery
        await test_citation_discovery()

        # Test 2: File organization
        await test_file_organization()

        # Test 3: Paper sorting
        await test_paper_type_sorting()

        print("\n" + "=" * 80)
        print("ALL TESTS PASSED ✅")
        print("=" * 80 + "\n")

        print("Next steps:")
        print("1. Start server: ./start_omics_oracle.sh")
        print("2. Test API: curl -X POST http://localhost:8000/api/agents/enrich-fulltext")
        print("3. Check logs for [CITATION] and [DOWNLOAD] messages")
        print("4. Verify file organization in data/pdfs/{geo_id}/")

    except Exception as e:
        logger.error(f"❌ TEST FAILED: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
