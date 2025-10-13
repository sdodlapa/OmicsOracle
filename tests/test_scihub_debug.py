"""Debug test to see exactly what happens with Sci-Hub."""

import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from omics_oracle_v2.lib.fulltext.manager import FullTextManager, FullTextManagerConfig
from omics_oracle_v2.lib.search_engines.citations.models import Publication, PublicationSource

# Enable detailed logging
logging.basicConfig(level=logging.DEBUG, format="%(levelname)s - %(name)s - %(message)s")


async def test_scihub_waterfall():
    """Test that waterfall reaches Sci-Hub for failed papers."""

    print("=" * 80)
    print("DEBUG TEST: Sci-Hub Waterfall Behavior")
    print("=" * 80)
    print()

    # Use papers that should NOT be in legal OA sources
    test_dois = [
        "10.1126/science.1058040",  # Science - paywalled
        "10.1016/j.cell.2013.05.039",  # Cell - paywalled
    ]

    publications = [Publication(title="Paper", doi=doi, source=PublicationSource.PUBMED) for doi in test_dois]

    # Test with Sci-Hub ENABLED
    print("Configuration:")
    print("  - Unpaywall: ENABLED")
    print("  - Sci-Hub: ENABLED")
    print("  - Papers: 2 paywalled papers (should fail Phase 1)")
    print()

    config = FullTextManagerConfig(
        enable_core=False,  # Disable to make test faster
        enable_biorxiv=False,
        enable_arxiv=False,
        enable_crossref=False,
        enable_unpaywall=True,
        enable_scihub=True,  # ⭐ ENABLED
        unpaywall_email="sdodl001@odu.edu",
        scihub_use_proxy=False,
        max_concurrent=1,
    )

    print("Starting test...")
    print()

    async with FullTextManager(config) as manager:
        # Test papers one by one to see detailed logs
        for i, pub in enumerate(publications, 1):
            print(f"\n{'='*60}")
            print(f"Testing Paper {i}: {pub.doi}")
            print(f"{'='*60}")

            result = await manager.get_fulltext(pub)

            print(f"\nResult:")
            print(f"  Success: {result.success}")
            if result.success:
                print(f"  Source: {result.source.value}")
                print(f"  URL: {result.url[:80]}...")
            else:
                print(f"  Error: {result.error}")

    print("\n" + "=" * 80)
    print("FINAL STATISTICS")
    print("=" * 80)
    stats = manager.get_statistics()
    print(f"Total attempts: {stats['total_attempts']}")
    print(f"Successes: {stats['successes']}")
    print(f"Failures: {stats['failures']}")
    print(f"Success rate: {stats['success_rate']:.1f}%")
    print(f"By source: {stats['by_source']}")
    print()

    if "scihub" in stats["by_source"]:
        print(f"✅ SUCCESS: Sci-Hub found {stats['by_source']['scihub']} papers!")
    else:
        print("❌ PROBLEM: Sci-Hub was not used at all!")
        print("\nPossible reasons:")
        print("  1. Sci-Hub client not initialized")
        print("  2. Sci-Hub method returning success=False incorrectly")
        print("  3. Error in waterfall logic")
        print("  4. Sci-Hub mirrors all down")


if __name__ == "__main__":
    asyncio.run(test_scihub_waterfall())
