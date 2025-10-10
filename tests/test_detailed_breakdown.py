"""Detailed test showing EXACTLY which papers were found by which source."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from omics_oracle_v2.lib.publications.fulltext_manager import FullTextManager, FullTextManagerConfig
from omics_oracle_v2.lib.publications.models import Publication, PublicationSource

# Test with known paywalled papers
PAYWALLED_DOIS = [
    "10.1126/science.1058040",  # Science - definitely paywalled
    "10.1016/j.cell.2013.05.039",  # Cell - definitely paywalled
    "10.1038/35057062",  # Nature - old paper, paywalled
]

OPEN_ACCESS_DOIS = [
    "10.1371/journal.pgen.1011043",  # PLOS - definitely OA
    "10.1186/s13059-024-03154-0",  # BMC - definitely OA
]


async def test_detailed_breakdown():
    """Show exactly what each source finds."""

    print("=" * 80)
    print("DETAILED BREAKDOWN: Phase 1 vs Phase 2")
    print("=" * 80)
    print()

    # Combine test sets
    all_dois = OPEN_ACCESS_DOIS + PAYWALLED_DOIS
    labels = ["OA"] * len(OPEN_ACCESS_DOIS) + ["Paywalled"] * len(PAYWALLED_DOIS)

    publications = [
        Publication(title=f"Paper {i}", doi=doi, source=PublicationSource.PUBMED)
        for i, doi in enumerate(all_dois)
    ]

    print(f"Test papers ({len(all_dois)} total):")
    for doi, label in zip(all_dois, labels):
        print(f"  {doi[:35]:35} ({label})")
    print()

    # PHASE 1: Legal OA only
    print("=" * 80)
    print("PHASE 1: Legal OA Sources Only (Sci-Hub DISABLED)")
    print("=" * 80)

    config1 = FullTextManagerConfig(
        enable_unpaywall=True,
        enable_core=False,
        enable_biorxiv=False,
        enable_arxiv=False,
        enable_crossref=False,
        enable_scihub=False,  # ⭐ DISABLED
        unpaywall_email="sdodl001@odu.edu",
        max_concurrent=2,
    )

    phase1_results = []
    async with FullTextManager(config1) as manager:
        results = await manager.get_fulltext_batch(publications)

        for doi, label, result in zip(all_dois, labels, results):
            status = "✅" if result.success else "❌"
            source = result.source.value if result.success else "NONE"
            phase1_results.append((doi, label, result.success, source))
            print(f"{status} {doi[:35]:35} ({label:10}) → {source}")

        stats1 = manager.get_statistics()

    phase1_found = sum(1 for r in results if r.success)
    print(f"\nPhase 1 Total: {phase1_found}/{len(all_dois)} ({phase1_found/len(all_dois)*100:.1f}%)")
    print(f"Sources used: {stats1['by_source']}")
    print()

    # PHASE 2: Add Sci-Hub
    print("=" * 80)
    print("PHASE 2: Legal OA + Sci-Hub (Sci-Hub ENABLED)")
    print("=" * 80)

    config2 = FullTextManagerConfig(
        enable_unpaywall=True,
        enable_core=False,
        enable_biorxiv=False,
        enable_arxiv=False,
        enable_crossref=False,
        enable_scihub=True,  # ⭐ ENABLED
        unpaywall_email="sdodl001@odu.edu",
        scihub_use_proxy=False,
        max_concurrent=2,
    )

    phase2_results = []
    scihub_filled = []

    async with FullTextManager(config2) as manager:
        results = await manager.get_fulltext_batch(publications)

        for i, (doi, label, result) in enumerate(zip(all_dois, labels, results)):
            status = "✅" if result.success else "❌"
            source = result.source.value if result.success else "NONE"
            phase2_results.append((doi, label, result.success, source))

            # Check if Sci-Hub filled a gap
            phase1_success = phase1_results[i][2]
            if not phase1_success and result.success and source == "scihub":
                marker = " ⭐ SCI-HUB FILLED GAP"
                scihub_filled.append(doi)
            else:
                marker = ""

            print(f"{status} {doi[:35]:35} ({label:10}) → {source}{marker}")

        stats2 = manager.get_statistics()

    phase2_found = sum(1 for r in results if r.success)
    print(f"\nPhase 2 Total: {phase2_found}/{len(all_dois)} ({phase2_found/len(all_dois)*100:.1f}%)")
    print(f"Sources used: {stats2['by_source']}")
    print()

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Phase 1 (Legal OA):     {phase1_found}/{len(all_dois)} ({phase1_found/len(all_dois)*100:.1f}%)")
    print(f"Phase 2 (+ Sci-Hub):    {phase2_found}/{len(all_dois)} ({phase2_found/len(all_dois)*100:.1f}%)")
    print(f"Sci-Hub filled gaps:    {len(scihub_filled)}")
    print()

    if scihub_filled:
        print(f"✅ Papers found ONLY via Sci-Hub:")
        for doi in scihub_filled:
            print(f"   {doi}")
    else:
        print("⚠️  Sci-Hub didn't fill any gaps")
        print("\nDiagnostics:")
        print(f"   - Sci-Hub in Phase 2 stats? {'scihub' in stats2['by_source']}")
        print(f"   - Phase 1 failures: {len(all_dois) - phase1_found}")
        print(f"   - Phase 2 failures: {len(all_dois) - phase2_found}")

        if "scihub" not in stats2["by_source"]:
            print("\n❌ PROBLEM: Sci-Hub was NEVER called!")
            print("   This means either:")
            print("   1. All papers were found by legal OA sources")
            print("   2. Papers missing DOIs (Sci-Hub needs DOI/PMID)")
            print("   3. Sci-Hub client initialization failed")
        else:
            print(f"\n✅ Sci-Hub was called {stats2['by_source']['scihub']} times")


if __name__ == "__main__":
    asyncio.run(test_detailed_breakdown())
