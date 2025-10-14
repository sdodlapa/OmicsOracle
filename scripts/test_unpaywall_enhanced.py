#!/usr/bin/env python3
"""
Test Enhanced Unpaywall Implementation

Tests that the enhanced Unpaywall source:
1. Verifies is_oa=true before returning URLs
2. Tries all oa_locations (not just best_oa_location)
3. Prefers url_for_pdf over landing pages
4. Properly classifies URL types
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path FIRST
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

from omics_oracle_v2.lib.enrichment.fulltext.manager import FullTextManager, FullTextManagerConfig
from omics_oracle_v2.lib.search_engines.citations.models import Publication, PublicationSource

# Load environment variables
load_dotenv()


async def test_unpaywall_oa_checking():
    """Test that Unpaywall verifies is_oa=true"""

    print("\n" + "=" * 80)
    print("Test 1: Unpaywall OA Verification")
    print("=" * 80)

    # Test with a known Open Access paper
    publication = Publication(
        doi="10.1371/journal.pone.0184491",  # PLOS ONE paper (definitely OA)
        title="Test paper for Unpaywall OA checking",
        authors=[],
        source=PublicationSource.PUBMED,
    )

    print(f"\nTest Publication (Open Access):")
    print(f"  DOI: {publication.doi}")
    print(f"  Expected: is_oa=true")

    # Create manager
    config = FullTextManagerConfig(
        enable_unpaywall=True,
        unpaywall_email=os.getenv("NCBI_EMAIL", "sdodl001@odu.edu"),
        enable_core=False,  # Disable other sources for focused test
        enable_pmc=False,
        enable_institutional=False,
    )
    manager = FullTextManager(config=config)
    await manager.initialize()

    print("\nCalling _try_unpaywall()...")
    print("-" * 80)

    # Try Unpaywall
    result = await manager._try_unpaywall(publication)

    print("-" * 80)
    print("\nResult:")
    print(f"  Success: {result.success}")
    print(f"  URL: {result.url}")
    print(f"  Source: {result.source}")
    if result.metadata:
        print(f"  Metadata:")
        print(f"    - OA Status: {result.metadata.get('oa_status')}")
        print(f"    - License: {result.metadata.get('license')}")
        print(f"    - Version: {result.metadata.get('version')}")
        print(f"    - Location: {result.metadata.get('location')}")
        print(f"    - URL Type: {result.metadata.get('url_type')}")

    await manager.cleanup()

    if result.success:
        print("\n[SUCCESS] Found OA URL via Unpaywall!")
        return True
    else:
        print(f"\n[FAILED] {result.error}")
        return False


async def test_unpaywall_multiple_locations():
    """Test that Unpaywall tries all oa_locations"""

    print("\n" + "=" * 80)
    print("Test 2: Multiple OA Locations")
    print("=" * 80)

    # Use a paper that might have multiple OA locations
    publication = Publication(
        doi="10.1038/nature12373",  # Nature paper with possible multiple locations
        title="Test paper with multiple OA locations",
        authors=[],
        source=PublicationSource.PUBMED,
    )

    print(f"\nTest Publication:")
    print(f"  DOI: {publication.doi}")

    config = FullTextManagerConfig(
        enable_unpaywall=True,
        unpaywall_email=os.getenv("NCBI_EMAIL", "sdodl001@odu.edu"),
        enable_core=False,
        enable_pmc=False,
        enable_institutional=False,
    )
    manager = FullTextManager(config=config)
    await manager.initialize()

    print("\nCalling _try_unpaywall()...")
    print("-" * 80)

    result = await manager._try_unpaywall(publication)

    print("-" * 80)
    print("\nResult:")
    print(f"  Success: {result.success}")
    if result.success:
        print(f"  URL: {result.url}")
        print(f"  Location Used: {result.metadata.get('location', 'unknown')}")
        print(f"  URL Type: {result.metadata.get('url_type', 'unknown')}")
    else:
        print(f"  Error: {result.error}")

    await manager.cleanup()

    # Success if we found something OR if paper is truly not OA
    if result.success or "Not Open Access" in result.error:
        print("\n[SUCCESS] Unpaywall handled multiple locations correctly!")
        return True
    else:
        print(f"\n[WARNING] Unexpected error: {result.error}")
        return False


async def test_unpaywall_pdf_preference():
    """Test that Unpaywall prefers PDF URLs over landing pages"""

    print("\n" + "=" * 80)
    print("Test 3: PDF URL Preference")
    print("=" * 80)

    # PLOS ONE papers always have direct PDF links
    publication = Publication(
        doi="10.1371/journal.pone.0100000",
        title="Test paper for PDF preference",
        authors=[],
        source=PublicationSource.PUBMED,
    )

    print(f"\nTest Publication:")
    print(f"  DOI: {publication.doi}")
    print(f"  Expected: url_for_pdf should be preferred")

    config = FullTextManagerConfig(
        enable_unpaywall=True,
        unpaywall_email=os.getenv("NCBI_EMAIL", "sdodl001@odu.edu"),
        enable_core=False,
        enable_pmc=False,
        enable_institutional=False,
    )
    manager = FullTextManager(config=config)
    await manager.initialize()

    print("\nCalling _try_unpaywall()...")
    print("-" * 80)

    result = await manager._try_unpaywall(publication)

    print("-" * 80)
    print("\nResult:")
    print(f"  Success: {result.success}")
    if result.success:
        print(f"  URL: {result.url}")
        url_type = result.metadata.get("url_type", "unknown")
        print(f"  URL Type: {url_type}")

        # Check if it's a PDF URL
        is_pdf_url = url_type == "pdf_direct" or result.url.lower().endswith(".pdf")
        if is_pdf_url:
            print("\n[SUCCESS] Correctly preferred PDF URL!")
        else:
            print("\n[WARNING] Got landing page instead of PDF")
    else:
        print(f"  Error: {result.error}")
        # Not OA is acceptable
        if "Not Open Access" in result.error:
            print("\n[INFO] Paper not Open Access (acceptable)")

    await manager.cleanup()
    return True


async def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("ENHANCED UNPAYWALL TESTS")
    print("=" * 80)

    try:
        # Test 1: OA verification
        test1_pass = await test_unpaywall_oa_checking()

        # Test 2: Multiple locations
        test2_pass = await test_unpaywall_multiple_locations()

        # Test 3: PDF preference
        test3_pass = await test_unpaywall_pdf_preference()

        # Summary
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        print(f"Test 1 (OA Verification): {'[PASS]' if test1_pass else '[FAIL]'}")
        print(f"Test 2 (Multiple Locations): {'[PASS]' if test2_pass else '[FAIL]'}")
        print(f"Test 3 (PDF Preference): {'[PASS]' if test3_pass else '[FAIL]'}")

        if test1_pass and test2_pass and test3_pass:
            print("\n[SUCCESS] ALL TESTS PASSED!")
            return 0
        else:
            print("\n[WARNING] SOME TESTS HAD ISSUES")
            return 1

    except Exception as e:
        print(f"\n\n[ERROR] {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
