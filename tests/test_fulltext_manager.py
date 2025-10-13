"""Test for FullTextManager."""

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from omics_oracle_v2.lib.enrichment.fulltext.manager import FullTextManager, FullTextManagerConfig
from omics_oracle_v2.lib.search_engines.citations.models import Publication, PublicationSource


async def test_fulltext_manager():
    """Test FullTextManager with real publications."""
    print("Testing FullTextManager...")
    print()

    # Get CORE API key from environment
    core_api_key = os.getenv("CORE_API_KEY")
    if not core_api_key:
        print("WARNING: CORE_API_KEY not set, CORE client will be disabled")
        print()

    # Configure manager
    config = FullTextManagerConfig(
        enable_institutional=False,  # Skip for testing
        enable_pmc=False,  # Skip for testing
        enable_unpaywall=False,  # Skip for testing
        enable_openalex=True,
        enable_core=bool(core_api_key),
        enable_biorxiv=True,
        enable_arxiv=True,
        enable_crossref=True,
        core_api_key=core_api_key,
        download_pdfs=False,  # Just get URLs for testing
        max_concurrent=3,
    )

    async with FullTextManager(config) as manager:
        print("FullTextManager initialized")
        print()

        # Test 1: bioRxiv preprint (should find in bioRxiv)
        print("1. Testing bioRxiv preprint...")
        biorxiv_pub = Publication(
            title="SARS-CoV-2 Omicron variant replication in human cells",
            doi="10.1101/2021.12.31.474653",  # Real bioRxiv DOI
            source=PublicationSource.PUBMED,
        )

        result = await manager.get_fulltext(biorxiv_pub)
        if result.success:
            print(f"   [SUCCESS] Found via {result.source}")
            print(f"   URL: {result.url}")
        else:
            print(f"   [FAILED] {result.error}")
        print()

        # Test 2: arXiv preprint (should find in arXiv)
        print("2. Testing arXiv preprint...")
        arxiv_pub = Publication(
            title="Quantum Computing",
            doi="2301.12345",  # arXiv ID
            source=PublicationSource.PUBMED,
        )

        result = await manager.get_fulltext(arxiv_pub)
        if result.success:
            print(f"   [SUCCESS] Found via {result.source}")
            print(f"   URL: {result.url}")
        else:
            print(f"   [FAILED] {result.error}")
        print()

        # Test 3: PLoS ONE paper (should find in CORE or Crossref)
        print("3. Testing PLoS ONE paper (Open Access)...")
        plos_pub = Publication(
            title="Ecological Guild Evolution and the Discovery of the World's Smallest Vertebrate",
            doi="10.1371/journal.pone.0029797",
            source=PublicationSource.PUBMED,
        )

        result = await manager.get_fulltext(plos_pub)
        if result.success:
            print(f"   [SUCCESS] Found via {result.source}")
            print(f"   URL: {result.url}")
        else:
            print(f"   [FAILED] {result.error}")
        print()

        # Test 4: Publication with OpenAlex OA URL
        print("4. Testing publication with OA URL in metadata...")
        oa_pub = Publication(
            title="CRISPR gene editing",
            doi="10.1038/nature12345",
            source=PublicationSource.OPENALEX,
            metadata={"oa_url": "https://europepmc.org/articles/PMC1234567"},
        )

        result = await manager.get_fulltext(oa_pub)
        if result.success:
            print(f"   [SUCCESS] Found via {result.source}")
            print(f"   URL: {result.url}")
        else:
            print(f"   [FAILED] {result.error}")
        print()

        # Test 5: Batch processing
        print("5. Testing batch processing (3 papers)...")
        batch_pubs = [biorxiv_pub, arxiv_pub, plos_pub]

        results = await manager.get_fulltext_batch(batch_pubs, max_concurrent=2)

        success_count = sum(1 for r in results if r.success)
        print(f"   Batch results: {success_count}/{len(results)} succeeded")
        for i, result in enumerate(results, 1):
            if result.success:
                print(f"   [{i}] SUCCESS via {result.source}")
            else:
                print(f"   [{i}] FAILED: {result.error}")
        print()

        # Show statistics
        print("6. Manager Statistics:")
        stats = manager.get_statistics()
        print(f"   Total attempts: {stats['total_attempts']}")
        print(f"   Successes: {stats['successes']}")
        print(f"   Failures: {stats['failures']}")
        print(f"   Success rate: {stats['success_rate']}")
        print(f"   By source: {stats['by_source']}")
        print()

    print("FullTextManager test complete!")


if __name__ == "__main__":
    asyncio.run(test_fulltext_manager())
