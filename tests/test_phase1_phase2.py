"""Test FullTextManager with Unpaywall + Sci-Hub (Phase 1 + Phase 2)."""

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from omics_oracle_v2.lib.publications.fulltext_manager import FullTextManager, FullTextManagerConfig
from omics_oracle_v2.lib.publications.models import Publication, PublicationSource


async def test_comprehensive_coverage():
    """Test with all sources enabled (Phase 1 + Phase 2)."""

    print("=" * 80)
    print("COMPREHENSIVE FULL-TEXT COVERAGE TEST")
    print("Phase 1 (Legal OA) + Phase 2 (Sci-Hub)")
    print("=" * 80)
    print()

    # Test DOIs representing different scenarios
    test_papers = [
        {
            "doi": "10.1371/journal.pgen.1011043",
            "title": "PLOS paper (should be in Unpaywall)",
            "expected": "unpaywall or crossref",
        },
        {
            "doi": "10.1038/nature12373",
            "title": "Nature paper (likely paywalled, needs Sci-Hub)",
            "expected": "scihub",
        },
        {
            "doi": "10.1101/2024.02.15.580567",
            "title": "bioRxiv preprint",
            "expected": "biorxiv",
        },
        {
            "doi": "10.1126/science.1058040",
            "title": "Science paper (paywalled, needs Sci-Hub)",
            "expected": "scihub",
        },
    ]

    # Phase 1: Legal OA sources only
    print("PHASE 1: Legal OA Sources Only")
    print("-" * 80)

    config_phase1 = FullTextManagerConfig(
        enable_core=True,
        enable_biorxiv=True,
        enable_arxiv=True,
        enable_crossref=True,
        enable_unpaywall=True,  # NEW
        enable_scihub=False,  # Disabled for Phase 1
        core_api_key=os.getenv("CORE_API_KEY"),
        unpaywall_email="sdodl001@odu.edu",
        max_concurrent=3,
    )

    async with FullTextManager(config_phase1) as manager:
        for paper in test_papers:
            pub = Publication(
                title=paper["title"],
                doi=paper["doi"],
                source=PublicationSource.PUBMED,
            )

            result = await manager.get_fulltext(pub)

            status = "✅" if result.success else "❌"
            source = result.source.value if result.success else "NONE"
            print(f"{status} {paper['doi'][:30]:<30} → {source}")

        stats1 = manager.get_statistics()
        print()
        print(f"Phase 1 Coverage: {stats1['successes']}/{stats1['total_attempts']} ({stats1['success_rate']}")
        print(f"By source: {stats1['by_source']}")

    print()
    print()

    # Phase 2: Add Sci-Hub for comprehensive coverage
    print("PHASE 2: Legal OA + Sci-Hub (Comprehensive)")
    print("-" * 80)

    config_phase2 = FullTextManagerConfig(
        enable_core=True,
        enable_biorxiv=True,
        enable_arxiv=True,
        enable_crossref=True,
        enable_unpaywall=True,
        enable_scihub=True,  # ENABLED for Phase 2
        core_api_key=os.getenv("CORE_API_KEY"),
        unpaywall_email="sdodl001@odu.edu",
        scihub_use_proxy=False,
        max_concurrent=3,
    )

    async with FullTextManager(config_phase2) as manager:
        for paper in test_papers:
            pub = Publication(
                title=paper["title"],
                doi=paper["doi"],
                source=PublicationSource.PUBMED,
            )

            result = await manager.get_fulltext(pub)

            status = "✅" if result.success else "❌"
            source = result.source.value if result.success else "NONE"
            expected = paper["expected"]
            print(f"{status} {paper['doi'][:30]:<30} → {source:<15} (expected: {expected})")

            if result.success and result.url:
                print(f"   URL: {result.url[:70]}...")

        stats2 = manager.get_statistics()
        print()
        print(f"Phase 2 Coverage: {stats2['successes']}/{stats2['total_attempts']} ({stats2['success_rate']}")
        print(f"By source: {stats2['by_source']}")

    print()
    print("=" * 80)
    print("COMPARISON")
    print("=" * 80)
    print(f"Phase 1 (Legal OA only):     {stats1['success_rate']}")
    print(f"Phase 2 (+ Sci-Hub):         {stats2['success_rate']}")
    print(
        f"Improvement:                 +{float(stats2['success_rate'].rstrip('%')) - float(stats1['success_rate'].rstrip('%')):.1f}%"
    )
    print()


if __name__ == "__main__":
    asyncio.run(test_comprehensive_coverage())
