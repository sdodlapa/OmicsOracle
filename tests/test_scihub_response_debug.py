"""Debug Sci-Hub to see what's actually being returned."""

import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from omics_oracle_v2.lib.enrichment.fulltext.sources.scihub_client import SciHubClient, SciHubConfig

logging.basicConfig(level=logging.DEBUG, format="%(levelname)s - %(message)s")


async def debug_scihub_response():
    """Check what Sci-Hub is actually returning."""

    # Use a paper that definitely worked before
    test_doi = "10.1126/science.1058040"

    print("=" * 80)
    print("DEBUG: Sci-Hub Response Analysis")
    print("=" * 80)
    print(f"Testing DOI: {test_doi}")
    print()

    config = SciHubConfig(
        rate_limit_delay=2.0,
        timeout=30,  # Longer timeout
    )

    async with SciHubClient(config) as client:
        # Access the internal method to get full response
        import os
        import ssl
        from urllib.parse import quote

        import aiohttp

        ssl_context = ssl.create_default_context()
        if os.getenv("PYTHONHTTPSVERIFY", "1") == "0":
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

        mirrors_to_test = [
            "https://sci-hub.se",
            "https://sci-hub.st",
        ]

        for mirror in mirrors_to_test:
            print(f"\nTesting mirror: {mirror}")
            print("-" * 60)

            url = f"{mirror}/{quote(test_doi)}"
            print(f"URL: {url}")

            try:
                async with client.session.get(url, timeout=30, ssl=ssl_context) as response:
                    print(f"Status: {response.status}")
                    print(f"Headers: {dict(response.headers)}")

                    html = await response.text()
                    print(f"Response length: {len(html)} bytes")

                    # Check if it's HTML or a redirect
                    if "html" in response.headers.get("content-type", "").lower():
                        print("Content-Type: HTML")

                        # Look for common patterns
                        if "captcha" in html.lower():
                            print("⚠️  CAPTCHA detected!")
                        if "blocked" in html.lower():
                            print("⚠️  Blocking detected!")
                        if "cloudflare" in html.lower():
                            print("⚠️  Cloudflare protection detected!")
                        if "iframe" in html.lower():
                            print("✓ iframe found (normal)")
                        if ".pdf" in html.lower():
                            print("✓ PDF reference found")

                        # Show first 500 chars
                        print(f"\nFirst 500 chars of HTML:")
                        print("-" * 60)
                        print(html[:500])
                        print("-" * 60)
                    else:
                        print(f"Content-Type: {response.headers.get('content-type')}")

            except asyncio.TimeoutError:
                print("❌ Timeout")
            except Exception as e:
                print(f"❌ Error: {e}")

            await asyncio.sleep(3)

    print("\n" + "=" * 80)
    print("DIAGNOSIS")
    print("=" * 80)
    print("Based on the response analysis above, we can determine:")
    print("  - If CAPTCHA: Sci-Hub is blocking automated requests")
    print("  - If Cloudflare: Need to add headers/user-agent")
    print("  - If PDF found: Extraction pattern needs fixing")
    print("  - If timeout: Mirrors might be down or slow")


if __name__ == "__main__":
    asyncio.run(debug_scihub_response())
