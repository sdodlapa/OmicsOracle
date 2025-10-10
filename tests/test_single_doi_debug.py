"""Debug test for a single DOI to see all log messages."""

import asyncio
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from omics_oracle_v2.lib.fulltext.manager import FullTextManager, FullTextManagerConfig
from omics_oracle_v2.lib.publications.models import Publication, PublicationSource

# Enable debug logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


async def test_single_doi():
    """Test a single DOI with debug logging."""

    # Test a known OA paper with a valid DOI
    test_doi = "10.1371/journal.pgen.1011043"  # PLOS Genetics (should be OA)

    print(f"Testing DOI: {test_doi}")
    print("=" * 80)

    config = FullTextManagerConfig(
        enable_core=True,
        enable_biorxiv=True,
        enable_arxiv=True,
        enable_crossref=True,
        enable_openalex=True,
        core_api_key=os.getenv("CORE_API_KEY"),
        download_pdfs=False,
        max_concurrent=3,
    )

    async with FullTextManager(config) as manager:
        pub = Publication(
            title=f"Test paper {test_doi}",
            doi=test_doi,
            source=PublicationSource.PUBMED,
        )

        result = await manager.get_fulltext(pub)

        print("=" * 80)
        print("RESULT:")
        print(f"  Success: {result.success}")
        if result.success:
            print(f"  Source: {result.source}")
            print(f"  URL: {result.url}")
            print(f"  Metadata: {result.metadata}")
        else:
            print(f"  Error: {result.error}")

        print()
        print("STATISTICS:")
        stats = manager.get_statistics()
        print(f"  Total attempts: {stats['total_attempts']}")
        print(f"  Successes: {stats['successes']}")
        print(f"  By source: {stats['by_source']}")


if __name__ == "__main__":
    asyncio.run(test_single_doi())
