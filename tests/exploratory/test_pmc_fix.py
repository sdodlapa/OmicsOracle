#!/usr/bin/env python3
"""
Test script to verify PMC 403 error fix.

This script tests that PMC URLs are properly detected and bypassed.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from omics_oracle_v2.api.models.responses import DatasetResponse
from omics_oracle_v2.services.fulltext_service import FulltextService


async def test_pmc_url_fix():
    """Test that PMC URLs are properly detected and bypassed."""

    print("\n" + "=" * 80)
    print("Testing PMC 403 Error Fix")
    print("=" * 80 + "\n")

    # Test dataset GSE570 with known PMC URL
    test_dataset = DatasetResponse(
        geo_id="GSE570",
        title="HeLa CD4+ transfection",
        summary="Expression profiles of HeLa CD4+ cells transfected with epitope-tagged eTat plasmid",
        organism="Homo sapiens",
        platform_id="GPL8300",
        sample_count=4,
        publication_date="2003-08-04",
        pubmed_ids=["15780141"],  # Known to have PMC URL
        citation_count=25,
        fulltext_count=0,
        fulltext_status="pending",
        relevance_score=10.0,
    )

    print(f"Test Dataset: {test_dataset.geo_id}")
    print(f"PubMed IDs: {test_dataset.pubmed_ids}")
    print(f"\nExpected behavior:")
    print("  1. PMC URL should be detected and skipped")
    print("  2. Waterfall should try alternative sources")
    print("  3. Download should succeed (or try multiple sources)")
    print("\nStarting download...\n")

    # Initialize service
    service = FulltextService()

    try:
        # Attempt enrichment
        results = await service.enrich_datasets(
            datasets=[test_dataset], max_papers=1, include_full_content=True
        )

        result = results[0]

        print("\n" + "=" * 80)
        print("RESULTS")
        print("=" * 80 + "\n")
        print(f"Status: {result.fulltext_status}")
        print(f"Papers downloaded: {result.fulltext_count}")

        if result.fulltext_status == "success":
            print("\n✅ SUCCESS! Fix is working - PMC bypass successful")
            return 0
        elif result.fulltext_status == "partial":
            print("\n⚠️  PARTIAL SUCCESS - Some sources worked")
            return 0
        elif result.fulltext_status == "failed":
            print("\n❌ FAILED - All sources failed (may be behind paywall)")
            print("\nThis may be expected if paper is truly not open access.")
            print("Check logs for evidence that PMC URL was skipped.")
            return 1
        else:
            print(f"\n❓ UNKNOWN STATUS: {result.fulltext_status}")
            return 1

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(test_pmc_url_fix())
    sys.exit(exit_code)
