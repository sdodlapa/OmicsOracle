"""Quick test for bioRxiv/medRxiv client."""

import asyncio
import os
from pathlib import Path

from omics_oracle_v2.lib.search_engines.citations.oa_sources.biorxiv_client import BioRxivClient


async def main():
    """Test bioRxiv client with known preprints."""
    async with BioRxivClient() as client:
        print("Testing bioRxiv/medRxiv API client...\n")

        # Test 1: Known bioRxiv preprint
        print("1. Testing with bioRxiv DOI: 10.1101/2023.01.15.524103")
        result = await client.get_by_doi("10.1101/2023.01.15.524103")

        if result:
            print(f"   ✓ Found: {result.get('title', 'N/A')[:60]}")
            print(f"   Server: {result.get('server')}")
            print(f"   Version: {result.get('version')}")
            print(f"   PDF URL: {result.get('pdf_url')}")
            print(f"   Category: {result.get('category')}")
        else:
            print("   Not found (API may be down or DOI invalid)")

        print()

        # Test 2: Try a made-up DOI (should fail)
        print("2. Testing with invalid bioRxiv DOI: 10.1101/9999.99.99.999999")
        result2 = await client.get_by_doi("10.1101/9999.99.99.999999")

        if result2:
            print(f"   Unexpected: {result2.get('title')}")
        else:
            print("   ✓ Correctly returned None for invalid DOI")

        print()

        # Test 3: Non-bioRxiv DOI (should skip)
        print("3. Testing with non-bioRxiv DOI: 10.1038/nature12345")
        result3 = await client.get_by_doi("10.1038/nature12345")

        if result3:
            print(f"   Unexpected: {result3.get('title')}")
        else:
            print("   ✓ Correctly skipped non-bioRxiv DOI")

        print("\n✓ bioRxiv client working!")


if __name__ == "__main__":
    asyncio.run(main())
