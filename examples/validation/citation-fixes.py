#!/usr/bin/env python3
"""
Test Citation Discovery Fixes

Tests the two bug fixes:
1. CitationFinder.find_citing_papers (was CitationAnalyzer.get_citing_papers)
2. PubMed async handling (removed await from synchronous method)
"""

import asyncio
import os
import sys
from pathlib import Path

# Disable SSL verification for testing
os.environ["SSL_VERIFY"] = "false"

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from omics_oracle_v2.lib.geo.models import GEOSeriesMetadata
from omics_oracle_v2.lib.pipelines.citation_discovery.geo_discovery import GEOCitationDiscovery


async def test_citation_fixes():
    """Test both citation discovery strategies"""

    print("=" * 80)
    print("TESTING CITATION DISCOVERY FIXES")
    print("=" * 80)
    print()

    # Create citation discovery instance
    discovery = GEOCitationDiscovery()

    # Test with a real GEO dataset that has a PMID
    # GSE251935 (PMID: 38376465) - DNMT1 degradation study
    test_metadata = GEOSeriesMetadata(
        geo_id="GSE251935",
        title="Tunable DNMT1 degradation reveals cooperation of DNMT1 and DNMT3B",
        summary="Study of DNA methylation dynamics",
        organism="Homo sapiens",
        submission_date="2024-01-15",
        pubmed_ids=["38376465"],  # Has a PMID!
        samples=[],
        platforms=[],
        sample_count=14,
    )

    print(f"Testing with dataset: {test_metadata.geo_id}")
    print(f"PMID: {test_metadata.pubmed_ids[0]}")
    print()

    try:
        # This should work now (both bugs fixed)
        result = await discovery.find_citing_papers(geo_metadata=test_metadata, max_results=50)

        print("✅ Citation discovery completed successfully!")
        print()
        print(f"Dataset: {result.geo_id}")
        print(f"Original PMID: {result.original_pmid}")
        print(f"Total citing papers found: {len(result.citing_papers)}")
        print()

        # Show strategy breakdown
        print("Strategy Breakdown:")
        print(f"  Strategy A (citation-based): {len(result.strategy_breakdown['strategy_a'])} papers")
        print(f"  Strategy B (mention-based):  {len(result.strategy_breakdown['strategy_b'])} papers")
        print()

        # Show first few citing papers
        if result.citing_papers:
            print("First 5 citing papers:")
            print("-" * 80)
            for i, paper in enumerate(result.citing_papers[:5], 1):
                print(f"{i}. {paper.title[:80]}...")
                print(f"   PMID: {paper.pmid or 'N/A'}, DOI: {paper.doi or 'N/A'}")
                print(f"   Year: {paper.publication_date.year if paper.publication_date else 'N/A'}")
                print()
        else:
            print("⚠️ No citing papers found (dataset may be too recent)")
            print()

        print("=" * 80)
        print("TEST PASSED: Both bugs fixed!")
        print("=" * 80)

        return result

    except AttributeError as e:
        print(f"❌ BUG 1 STILL PRESENT: {e}")
        print("   CitationFinder.find_citing_papers() doesn't exist")
        print("   Method implementation issue")
        return None

    except TypeError as e:
        if "await" in str(e) or "async" in str(e):
            print(f"❌ BUG 2 STILL PRESENT: {e}")
            print("   PubMed client search is not async")
            print("   Should not use 'await' with synchronous method")
        else:
            print(f"❌ UNEXPECTED ERROR: {e}")
        return None

    except Exception as e:
        print(f"❌ ERROR: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()
        return None


async def main():
    """Run all tests"""
    result = await test_citation_fixes()

    if result:
        print()
        print("🎉 SUCCESS: Citation discovery is working!")
        print()
        print("Next steps:")
        print("1. Re-run full pipeline test")
        print("2. Should now find 20-60 citing papers for DNA methylation + HiC query")
        print("3. Collect full-text URLs from citing papers")
        print("4. Download PDFs")
        return 0
    else:
        print()
        print("❌ FAILED: Bugs still present")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
