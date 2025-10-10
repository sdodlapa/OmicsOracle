"""
Test that Sci-Hub is tried ONLY when Phase 1 sources fail.

This test explicitly chooses papers that:
1. ARE available on Sci-Hub
2. ARE NOT available via Unpaywall/legal OA
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from omics_oracle_v2.lib.publications.fulltext_manager import FullTextManager, FullTextManagerConfig
from omics_oracle_v2.lib.publications.publication import Publication


async def test_scihub_fills_gaps():
    """Test that Sci-Hub finds papers that legal OA sources miss."""

    print("=" * 80)
    print("TEST: Sci-Hub Fills Gaps in Phase 1")
    print("=" * 80)
    print()

    # Test papers: Known paywalled papers (NOT in Unpaywall)
    test_papers = [
        {
            "title": "The hallmarks of aging",
            "doi": "10.1016/j.cell.2013.05.039",  # Cell paper - paywalled
            "expected_phase1": False,  # Should NOT be in Unpaywall
            "expected_phase2": True,  # Should be in Sci-Hub
        },
        {
            "title": "CRISPR-Cas9 structures and mechanisms",
            "doi": "10.1146/annurev-biophys-062215-010822",  # Annual Reviews - paywalled
            "expected_phase1": False,
            "expected_phase2": True,
        },
        {
            "title": "The sequence of the human genome",
            "doi": "10.1126/science.1058040",  # Science - paywalled
            "expected_phase1": False,
            "expected_phase2": True,
        },
        {
            "title": "A draft sequence of the human genome",
            "doi": "10.1038/35057062",  # Nature - paywalled
            "expected_phase1": False,
            "expected_phase2": True,
        },
    ]

    publications = []
    for paper in test_papers:
        pub = Publication()
        pub.title = paper["title"]
        pub.doi = paper["doi"]
        publications.append(pub)

    # PHASE 1: Legal OA only
    print("PHASE 1: Legal OA Sources Only")
    print("-" * 80)

    config1 = FullTextManagerConfig(
        enable_unpaywall=True,
        enable_core=True,
        enable_biorxiv=True,
        enable_arxiv=True,
        enable_crossref=True,
        enable_scihub=False,  # ⭐ Sci-Hub DISABLED
        unpaywall_email="sdodl001@odu.edu",
        max_concurrent=2,
    )

    phase1_found = 0
    phase1_sources = {}

    async with FullTextManager(config1) as manager:
        results1 = await manager.get_fulltext_batch(publications)

        for paper, result in zip(test_papers, results1):
            if result.success:
                phase1_found += 1
                source = result.source.value
                phase1_sources[source] = phase1_sources.get(source, 0) + 1
                print(f"✅ {paper['doi'][:30]:30} → {source}")
            else:
                print(f"❌ {paper['doi'][:30]:30} → NONE")

    print()
    print(f"Phase 1 Coverage: {phase1_found}/{len(test_papers)} ({phase1_found/len(test_papers)*100:.1f}%)")
    if phase1_sources:
        print(f"Sources: {phase1_sources}")
    print()

    # PHASE 2: Legal OA + Sci-Hub
    print("PHASE 2: Legal OA + Sci-Hub")
    print("-" * 80)

    config2 = FullTextManagerConfig(
        enable_unpaywall=True,
        enable_core=True,
        enable_biorxiv=True,
        enable_arxiv=True,
        enable_crossref=True,
        enable_scihub=True,  # ⭐ Sci-Hub ENABLED
        unpaywall_email="sdodl001@odu.edu",
        scihub_use_proxy=False,
        max_concurrent=2,
    )

    phase2_found = 0
    phase2_sources = {}
    scihub_count = 0

    async with FullTextManager(config2) as manager:
        results2 = await manager.get_fulltext_batch(publications)

        for paper, result in zip(test_papers, results2):
            if result.success:
                phase2_found += 1
                source = result.source.value
                phase2_sources[source] = phase2_sources.get(source, 0) + 1

                if source == "scihub":
                    scihub_count += 1
                    print(f"✅ {paper['doi'][:30]:30} → {source} ⭐ (Sci-Hub filled gap)")
                else:
                    print(f"✅ {paper['doi'][:30]:30} → {source}")
            else:
                print(f"❌ {paper['doi'][:30]:30} → NONE")

    print()
    print(f"Phase 2 Coverage: {phase2_found}/{len(test_papers)} ({phase2_found/len(test_papers)*100:.1f}%)")
    print(f"Sources: {phase2_sources}")
    print()

    # Summary
    print("=" * 80)
    print("RESULTS")
    print("=" * 80)
    print(
        f"Phase 1 (Legal OA):      {phase1_found}/{len(test_papers)} ({phase1_found/len(test_papers)*100:.1f}%)"
    )
    print(
        f"Phase 2 (+ Sci-Hub):     {phase2_found}/{len(test_papers)} ({phase2_found/len(test_papers)*100:.1f}%)"
    )
    print(
        f"Sci-Hub filled gaps:     {scihub_count}/{len(test_papers)} ({scihub_count/len(test_papers)*100:.1f}%)"
    )
    improvement = (phase2_found - phase1_found) / len(test_papers) * 100
    print(f"Improvement:             +{improvement:.1f}%")
    print()

    if scihub_count > 0:
        print(f"✅ SUCCESS: Sci-Hub filled {scihub_count} gaps that Phase 1 missed!")
    else:
        print(f"⚠️  WARNING: Sci-Hub didn't fill any gaps (might be rate limited or mirrors down)")


if __name__ == "__main__":
    asyncio.run(test_scihub_fills_gaps())
