#!/usr/bin/env python3
"""
Test PMC Multi-Pattern URL Collection

Tests that the enhanced PMC source tries multiple URL patterns
for PMID 41034176 (the original bug).
"""

import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from omics_oracle_v2.lib.enrichment.fulltext.manager import FullTextManager, FullTextManagerConfig
from omics_oracle_v2.lib.search_engines.citations.models import Publication, PublicationSource

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()


async def test_pmc_patterns():
    """Test PMC with multiple patterns for PMID 41034176"""

    print("\n" + "=" * 80)
    print("Testing PMC Multi-Pattern URL Collection")
    print("=" * 80)

    # Create publication for PMID 41034176
    # This is the original bug - Open Access but couldn't find PMC PDF
    publication = Publication(
        pmid="41034176",
        pmcid="PMC11460852",  # Known PMCID for this paper
        title="Test paper for PMC multi-pattern",
        authors=[],
        source=PublicationSource.PUBMED,
    )

    print("\nTest Publication:")
    print(f"  PMID: {publication.pmid}")
    print(f"  PMCID: {publication.pmcid}")
    print(f"  Title: {publication.title}")

    # Create manager (no config needed for single source test)
    manager = FullTextManager()

    print("\n\nCalling _try_pmc() with multiple patterns...\n")
    print("-" * 80)

    # Try PMC source
    result = await manager._try_pmc(publication)

    print("-" * 80)
    print("\nResult:")
    print(f"  Success: {result.success}")
    print(f"  URL: {result.url}")
    print(f"  Source: {result.source}")
    print(f"  Metadata: {result.metadata}")

    if result.success:
        print("\n[SUCCESS] Found PMC URL!")
        print(f"   Pattern used: {result.metadata.get('pattern', 'unknown')}")
        print(f"   URL type: {result.metadata.get('url_type', 'unknown')}")
        print(f"   PMC ID: {result.metadata.get('pmc_id', 'unknown')}")
    else:
        print(f"\n[FAILED] {result.error}")
        return False

    # Cleanup
    await manager.cleanup()

    print("\n" + "=" * 80)
    print("Test Complete")
    print("=" * 80)

    return True


async def test_full_url_collection():
    """Test full URL collection to see all sources"""

    print("\n" + "=" * 80)
    print("Testing Full URL Collection (All Sources)")
    print("=" * 80)

    publication = Publication(
        pmid="41034176",
        pmcid="PMC11460852",
        doi="10.1128/msphere.00555-24",  # Add DOI
        title="Test paper for PMC multi-pattern",
        authors=[],
        source=PublicationSource.PUBMED,
    )

    print("\nTest Publication:")
    print(f"  PMID: {publication.pmid}")
    print(f"  PMCID: {publication.pmcid}")
    print(f"  DOI: {publication.doi}")

    # Create manager with proper config including API keys
    config = FullTextManagerConfig(
        enable_core=True,
        core_api_key=os.getenv("CORE_API_KEY"),
        enable_unpaywall=True,
        unpaywall_email=os.getenv("NCBI_EMAIL", "sdodl001@odu.edu"),
    )
    manager = FullTextManager(config=config)

    print("\n\nCalling get_all_fulltext_urls()...\n")
    print("-" * 80)

    # Get all URLs
    result = await manager.get_all_fulltext_urls(publication)

    print("-" * 80)
    print("\nResult:")
    print(f"  Success: {result.success}")
    print(f"  Total URLs found: {len(result.all_urls)}")

    if result.all_urls:
        print("\n  All URLs (sorted by priority):")
        for i, source_url in enumerate(result.all_urls, 1):
            print(f"    {i}. {source_url.source.value:15s} " f"(priority={source_url.priority})")
            print(f"       URL: {source_url.url[:80]}...")
            if source_url.url_type:
                print(f"       Type: {source_url.url_type.value}")

        # Check if PMC is in the list
        pmc_urls = [u for u in result.all_urls if u.source.value == "pmc"]
        if pmc_urls:
            print(f"\n[SUCCESS] PMC URLs found: {len(pmc_urls)}")
        else:
            print("\n[WARNING] No PMC URLs found in collection")

    else:
        print("\n[FAILED] No URLs found!")

    # Cleanup
    await manager.cleanup()

    print("\n" + "=" * 80)
    print("Test Complete")
    print("=" * 80)

    return bool(result.all_urls)


async def main():
    """Run all tests"""
    try:
        # Test 1: PMC multi-pattern
        success1 = await test_pmc_patterns()

        # Test 2: Full URL collection
        success2 = await test_full_url_collection()

        if success1 and success2:
            print("\n\n[SUCCESS] ALL TESTS PASSED!")
            return 0
        else:
            print("\n\n[FAILED] SOME TESTS FAILED")
            return 1

    except Exception as e:
        print(f"\n\n[ERROR] {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
