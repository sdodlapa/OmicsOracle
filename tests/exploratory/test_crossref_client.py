"""Quick test for Crossref client."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from omics_oracle_v2.lib.search_engines.citations.oa_sources.crossref_client import CrossrefClient


async def test_crossref_client():
    """Test Crossref client functionality."""
    print("Testing Crossref API client...")
    print()

    async with CrossrefClient(email="research@university.edu") as client:
        # Test 1: Get by DOI (PLoS ONE paper - often has full-text links)
        print("1. Testing with PLoS ONE DOI: 10.1371/journal.pone.0029797")
        paper = await client.get_by_doi("10.1371/journal.pone.0029797")
        if paper:
            print(f"   ✓ Found: {paper['title'][:60]}...")
            print(f"   Authors: {', '.join(paper['authors'][:2])}...")
            print(f"   Journal: {paper['journal']}")
            print(f"   Year: {paper['year']}")
            print(f"   Publisher: {paper['publisher']}")
            print(f"   Open Access: {paper['is_open_access']}")
            if paper.get("fulltext_urls"):
                print(f"   Full-text URLs: {len(paper['fulltext_urls'])} found")
                for url in paper["fulltext_urls"][:2]:
                    print(f"     - {url[:60]}...")
            else:
                print("   Full-text URLs: None")
        else:
            print("   Not found")
        print()

        # Test 2: Get by DOI (Nature paper - may have limited access)
        print("2. Testing with Nature DOI: 10.1038/nature12373")
        paper = await client.get_by_doi("10.1038/nature12373")
        if paper:
            print(f"   ✓ Found: {paper['title'][:60]}...")
            print(f"   Publisher: {paper['publisher']}")
            print(f"   Open Access: {paper['is_open_access']}")
            print(f"   Full-text URLs: {len(paper.get('fulltext_urls', []))} found")
        else:
            print("   Not found")
        print()

        # Test 3: Search
        print("3. Searching: 'CRISPR gene editing'")
        results = await client.search("CRISPR gene editing", max_results=3)
        if results:
            print(f"   ✓ Found {len(results)} papers")
            for i, paper in enumerate(results[:2], 1):
                print(f"   [{i}] {paper['title'][:60]}...")
                print(f"       Journal: {paper.get('journal', 'N/A')}")
                print(
                    f"       OA: {paper.get('is_open_access')}, Links: {len(paper.get('fulltext_urls', []))}"
                )
        else:
            print("   No results found")
        print()

    print("✓ Crossref client working!")


if __name__ == "__main__":
    asyncio.run(test_crossref_client())
