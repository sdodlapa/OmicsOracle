"""Test Sci-Hub client (use responsibly)."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from omics_oracle_v2.lib.pipelines.url_collection.sources.scihub_client import SciHubClient, SciHubConfig


async def test_scihub():
    """Test Sci-Hub with a small sample (responsible testing)."""

    print("⚠️  Testing Sci-Hub - Use responsibly and legally")
    print("=" * 80)
    print()

    config = SciHubConfig(
        rate_limit_delay=3.0,  # Be polite - slow down requests
        max_concurrent=1,  # One at a time
    )

    async with SciHubClient(config) as client:
        # First, check which mirrors are working
        print("1. Checking Sci-Hub mirrors...")
        working_mirrors = await client.check_mirrors()
        print(f"   Found {len(working_mirrors)} working mirrors")
        for mirror in working_mirrors:
            print(f"   ✓ {mirror}")
        print()

        if not working_mirrors:
            print("❌ No working Sci-Hub mirrors found.")
            print("   Mirrors may be blocked or down.")
            return

        # Test with a few papers (keep it minimal for responsible testing)
        test_dois = [
            "10.1038/nature12373",  # Famous CRISPR paper
            "10.1126/science.1058040",  # Classic science paper
        ]

        print("2. Testing PDF retrieval (2 papers only)...")
        print()

        for doi in test_dois:
            print(f"   DOI: {doi}")
            pdf_url = await client.get_pdf_url(doi)

            if pdf_url:
                print(f"   ✅ PDF found: {pdf_url[:80]}...")
            else:
                print(f"   ❌ PDF not found")

            print()


if __name__ == "__main__":
    asyncio.run(test_scihub())
