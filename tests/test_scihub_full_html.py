"""See the FULL HTML response to understand the pattern."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from omics_oracle_v2.lib.publications.clients.oa_sources.scihub_client import SciHubClient, SciHubConfig


async def see_full_html():
    """Get full HTML to see the complete embed tag."""

    test_doi = "10.1126/science.1058040"

    config = SciHubConfig()

    async with SciHubClient(config) as client:
        import os
        import ssl
        from urllib.parse import quote

        ssl_context = ssl.create_default_context()
        if os.getenv("PYTHONHTTPSVERIFY", "1") == "0":
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

        mirror = "https://sci-hub.se"
        url = f"{mirror}/{quote(test_doi)}"

        print(f"Fetching: {url}\n")

        async with client.session.get(url, timeout=30, ssl=ssl_context) as response:
            html = await response.text()

            print("FULL HTML RESPONSE:")
            print("=" * 80)
            print(html)
            print("=" * 80)

            # Test extraction patterns
            print("\nTesting extraction patterns:")
            print("-" * 60)

            import re

            # Current patterns
            patterns = [
                (r'<iframe[^>]+src="([^"]+\.pdf[^"]*)"', "iframe"),
                (r'<embed[^>]+src="([^"]+\.pdf[^"]*)"', "embed"),
                (r'<embed[^>]+src="([^"]+)"', "embed (any)"),
                (r'src="(//[^"]+\.pdf[^"]*)"', "protocol-relative"),
            ]

            for pattern, name in patterns:
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    print(f"✓ {name:20} → {match.group(1)}")
                else:
                    print(f"✗ {name:20} → NOT FOUND")


if __name__ == "__main__":
    asyncio.run(see_full_html())
