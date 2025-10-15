"""Identify which papers failed and why."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from omics_oracle_v2.lib.pipelines.url_collection.manager import (
    FullTextManager, FullTextManagerConfig)
from omics_oracle_v2.lib.search_engines.citations.models import (
    Publication, PublicationSource)

# Same 20 DOIs from the earlier test
DIVERSE_DOIS = [
    "10.1371/journal.pgen.1011043",
    "10.1371/journal.pbio.3002912",
    "10.1371/journal.pone.0296841",
    "10.1101/2024.02.15.580567",
    "10.1101/2024.03.20.585912",
    "10.1038/s41586-024-08288-w",
    "10.1038/s41467-024-46789-2",
    "10.1038/nature12373",
    "10.1126/science.adi4415",
    "10.1126/science.1058040",
    "10.1016/j.cell.2024.01.029",
    "10.1016/j.molcel.2024.02.015",
    "10.1007/s00018-024-05123-4",
    "10.1007/s10719-024-10198-7",
    "10.1002/advs.202308024",
    "10.1111/imm.13821",
    "10.1186/s13059-024-03154-0",
    "10.1186/s12915-024-01821-w",
    "10.7554/eLife.89410",
    "10.3389/fimmu.2024.1352169",
]


async def test_identify_failures():
    """Show which papers failed and investigate why."""

    print("=" * 80)
    print("IDENTIFY FAILURES: Which papers can't be found?")
    print("=" * 80)
    print()

    publications = [
        Publication(title=f"Paper {i}", doi=doi, source=PublicationSource.PUBMED)
        for i, doi in enumerate(DIVERSE_DOIS)
    ]

    # Test with EVERYTHING enabled
    config = FullTextManagerConfig(
        enable_unpaywall=True,
        enable_core=False,  # Skip CORE (it's slow and not working)
        enable_biorxiv=True,  # Enable for bioRxiv papers
        enable_arxiv=True,
        enable_crossref=True,
        enable_scihub=True,  # ⭐ ENABLED
        unpaywall_email="sdodl001@odu.edu",
        scihub_use_proxy=False,
        max_concurrent=2,
    )

    successes = []
    failures = []

    async with FullTextManager(config) as manager:
        results = await manager.get_fulltext_batch(publications)

        print("RESULTS:")
        print("-" * 80)

        for doi, pub, result in zip(DIVERSE_DOIS, publications, results):
            if result.success:
                status = "✅"
                source = result.source.value
                successes.append((doi, source))
                print(f"{status} {doi[:45]:45} → {source:12}")
            else:
                status = "❌"
                failures.append((doi, result.error))
                error = result.error[:40] if result.error else "Unknown"
                print(f"{status} {doi[:45]:45} → FAILED ({error})")

        stats = manager.get_statistics()

    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total: {len(DIVERSE_DOIS)}")
    print(
        f"✅ Successes: {len(successes)} ({len(successes)/len(DIVERSE_DOIS)*100:.1f}%)"
    )
    print(f"❌ Failures: {len(failures)} ({len(failures)/len(DIVERSE_DOIS)*100:.1f}%)")
    print()
    print(f"By source: {stats['by_source']}")
    print()

    if "scihub" in stats["by_source"]:
        print(f"⭐ Sci-Hub found: {stats['by_source']['scihub']} papers")
        scihub_papers = [doi for doi, source in successes if source == "scihub"]
        for doi in scihub_papers:
            print(f"   {doi}")
        print()

    if failures:
        print(f"❌ Failed papers ({len(failures)}):")
        for doi, error in failures:
            print(f"   {doi}")
            print(f"      Error: {error}")
        print()
        print("Possible reasons:")
        print("  1. Very new papers (2024) - not yet in Sci-Hub")
        print("  2. DOI format issues")
        print("  3. Sci-Hub mirrors temporarily down")
        print("  4. Rate limiting (try running again)")


if __name__ == "__main__":
    asyncio.run(test_identify_failures())
