"""Quick test with 20 diverse DOIs - Phase 1 vs Phase 2."""

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from omics_oracle_v2.lib.pipelines.url_collection import FullTextManager, FullTextManagerConfig
from omics_oracle_v2.lib.search_engines.citations.models import Publication, PublicationSource

# 20 diverse DOIs
DIVERSE_DOIS = [
    # PLOS (should be OA)
    "10.1371/journal.pgen.1011043",
    "10.1371/journal.pbio.3002912",
    "10.1371/journal.pone.0296841",
    # bioRxiv preprints (should be OA)
    "10.1101/2024.02.15.580567",
    "10.1101/2024.03.20.585912",
    # Nature (mix of OA and paywalled)
    "10.1038/s41586-024-08288-w",
    "10.1038/s41467-024-46789-2",
    "10.1038/nature12373",
    # Science (likely paywalled)
    "10.1126/science.adi4415",
    "10.1126/science.1058040",
    # Cell Press (likely paywalled)
    "10.1016/j.cell.2024.01.029",
    "10.1016/j.molcel.2024.02.015",
    # Springer (mix)
    "10.1007/s00018-024-05123-4",
    "10.1007/s10719-024-10198-7",
    # Wiley (mix)
    "10.1002/advs.202308024",
    "10.1111/imm.13821",
    # BMC (all OA)
    "10.1186/s13059-024-03154-0",
    "10.1186/s12915-024-01821-w",
    # eLife (all OA)
    "10.7554/eLife.89410",
    # Frontiers (all OA)
    "10.3389/fimmu.2024.1352169",
]


async def test_20_dois():
    """Test 20 DOIs with Phase 1 vs Phase 2."""

    print("=" * 80)
    print("QUICK COVERAGE TEST: 20 Diverse DOIs")
    print("=" * 80)
    print()

    # PHASE 1: Legal OA only
    print("PHASE 1: Legal OA Sources Only")
    print("-" * 80)

    config1 = FullTextManagerConfig(
        enable_core=True,
        enable_biorxiv=True,
        enable_arxiv=True,
        enable_crossref=True,
        enable_unpaywall=True,
        enable_scihub=False,  # Disabled
        core_api_key=os.getenv("CORE_API_KEY"),
        unpaywall_email="sdodl001@odu.edu",
        max_concurrent=3,
    )

    publications = [Publication(title="", doi=doi, source=PublicationSource.PUBMED) for doi in DIVERSE_DOIS]

    async with FullTextManager(config1) as manager:
        results1 = await manager.get_fulltext_batch(publications)
        stats1 = manager.get_statistics()

    successes1 = sum(1 for r in results1 if r.success)
    print(f"✅ Found: {successes1}/{len(DIVERSE_DOIS)} ({successes1/len(DIVERSE_DOIS)*100:.1f}%)")
    print(f"By source: {stats1['by_source']}")
    print()

    # PHASE 2: Add Sci-Hub
    print("PHASE 2: Legal OA + Sci-Hub")
    print("-" * 80)

    config2 = FullTextManagerConfig(
        enable_core=True,
        enable_biorxiv=True,
        enable_arxiv=True,
        enable_crossref=True,
        enable_unpaywall=True,
        enable_scihub=True,  # ENABLED
        core_api_key=os.getenv("CORE_API_KEY"),
        unpaywall_email="sdodl001@odu.edu",
        scihub_use_proxy=False,
        max_concurrent=2,  # Slower for Sci-Hub
    )

    async with FullTextManager(config2) as manager:
        results2 = await manager.get_fulltext_batch(publications)
        stats2 = manager.get_statistics()

    successes2 = sum(1 for r in results2 if r.success)
    print(f"✅ Found: {successes2}/{len(DIVERSE_DOIS)} ({successes2/len(DIVERSE_DOIS)*100:.1f}%)")
    print(f"By source: {stats2['by_source']}")
    print()

    # COMPARISON
    print("=" * 80)
    print("RESULTS")
    print("=" * 80)
    print(
        f"Phase 1 (Legal OA):      {successes1}/{len(DIVERSE_DOIS)} ({successes1/len(DIVERSE_DOIS)*100:.1f}%)"
    )
    print(
        f"Phase 2 (+ Sci-Hub):     {successes2}/{len(DIVERSE_DOIS)} ({successes2/len(DIVERSE_DOIS)*100:.1f}%)"
    )
    improvement = (successes2 - successes1) / len(DIVERSE_DOIS) * 100
    print(f"Improvement:             +{improvement:.1f}%")
    print()

    # Show which ones Sci-Hub filled in
    scihub_fills = []
    for i, (r1, r2) in enumerate(zip(results1, results2)):
        if not r1.success and r2.success and r2.source.value == "scihub":
            scihub_fills.append((DIVERSE_DOIS[i], r2.url))

    if scihub_fills:
        print(f"Papers found ONLY via Sci-Hub ({len(scihub_fills)}):")
        for doi, url in scihub_fills[:5]:  # Show first 5
            print(f"  • {doi}")
            print(f"    {url[:70]}...")


if __name__ == "__main__":
    asyncio.run(test_20_dois())
