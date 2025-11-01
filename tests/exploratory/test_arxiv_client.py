"""Quick test for arXiv client."""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from omics_oracle_v2.lib.search_engines.citations.oa_sources.arxiv_client import ArXivClient


async def test_arxiv_client():
    """Test arXiv client functionality."""
    print("Testing arXiv API client...")
    print()

    async with ArXivClient() as client:
        # Test 1: Get by arXiv ID
        print("1. Testing with arXiv ID: 2301.12345")
        paper = await client.get_by_arxiv_id("2301.12345")
        if paper:
            print(f"   ✓ Found: {paper['title'][:60]}...")
            print(f"   Authors: {', '.join(paper['authors'][:2])}...")
            print(f"   PDF URL: {paper['pdf_url']}")
            print(f"   Categories: {', '.join(paper['categories'][:3])}")
        else:
            print("   Not found (may be invalid ID)")
        print()

        # Test 2: Search by title
        print("2. Searching by title: 'quantum computing'")
        results = await client.search_by_title("quantum computing", max_results=3)
        if results:
            print(f"   ✓ Found {len(results)} papers")
            for i, paper in enumerate(results[:2], 1):
                print(f"   [{i}] {paper['title'][:60]}...")
        else:
            print("   No results found")
        print()

        # Test 3: General search with category filter
        print("3. Searching in cs.AI category: 'machine learning'")
        results = await client.search("machine learning", max_results=3, categories=["cs.AI", "cs.LG"])
        if results:
            print(f"   ✓ Found {len(results)} papers in AI/ML categories")
            for i, paper in enumerate(results[:2], 1):
                print(f"   [{i}] {paper['title'][:60]}...")
                print(f"       Categories: {', '.join(paper['categories'][:3])}")
        else:
            print("   No results found")
        print()

        # Test 4: Old format arXiv ID
        print("4. Testing with old format arXiv ID: math/0703324")
        paper = await client.get_by_arxiv_id("math/0703324")
        if paper:
            print(f"   ✓ Found: {paper['title'][:60]}...")
            print(f"   arXiv ID: {paper['arxiv_id']}")
        else:
            print("   Not found (may be invalid ID)")
        print()

        # Test 5: Extract arXiv ID from DOI
        print("5. Testing arXiv ID extraction from text")
        test_texts = [
            "2301.12345",
            "arxiv:2301.12345",
            "https://arxiv.org/abs/2301.12345",
            "math/0703324",
        ]
        for text in test_texts:
            arxiv_id = client._extract_arxiv_id(text)
            print(f"   '{text}' → '{arxiv_id}'")
        print()

    print("✓ arXiv client working!")


if __name__ == "__main__":
    asyncio.run(test_arxiv_client())
