"""Test Unpaywall client."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from omics_oracle_v2.lib.search_engines.citations.oa_sources.unpaywall_client import (
    UnpaywallClient,
    UnpaywallConfig,
)


async def test_unpaywall():
    """Test Unpaywall with known OA papers."""

    test_dois = [
        "10.1371/journal.pgen.1011043",  # PLOS (should be OA)
        "10.1038/s41467-024-46789-2",  # Nature Communications (often OA)
        "10.1101/2024.02.15.580567",  # bioRxiv (should be OA)
        "10.1056/NEJMoa2312345",  # NEJM (likely paywalled)
    ]

    config = UnpaywallConfig(email="sdodl001@odu.edu")

    async with UnpaywallClient(config) as client:
        print("Testing Unpaywall API...")
        print("=" * 80)
        print()

        for doi in test_dois:
            print(f"DOI: {doi}")
            result = await client.get_oa_location(doi)

            if result:
                print(f"  ✅ IS OPEN ACCESS")
                best_oa = result.get("best_oa_location", {})
                print(f"  Title: {result.get('title', 'N/A')[:60]}...")
                print(f"  Version: {best_oa.get('version', 'N/A')}")
                print(f"  License: {best_oa.get('license', 'N/A')}")
                pdf_url = await client.get_pdf_url(doi)
                if pdf_url:
                    print(f"  PDF URL: {pdf_url[:80]}...")
                else:
                    print(f"  PDF URL: Not available")
            else:
                print(f"  ❌ NOT OPEN ACCESS (or not found)")

            print()


if __name__ == "__main__":
    asyncio.run(test_unpaywall())
