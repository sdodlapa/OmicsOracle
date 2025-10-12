#!/usr/bin/env python3
"""
Chrome Cookie Integration for Institutional Access

This module extracts cookies from your Chrome browser session and uses them
to download PDFs from institutional/publisher sites where you're logged in.

REQUIREMENTS:
1. You must be logged into the publisher site in Chrome
2. Chrome must not be running (or use a different profile)
3. Install: pip install browser-cookie3 pycryptodome

USAGE:
    from chrome_cookies import download_with_chrome_cookies

    success = await download_with_chrome_cookies(
        url="https://academic.oup.com/nar/article/...",
        output_path=Path("paper.pdf")
    )
"""

import asyncio
import logging
import ssl
from pathlib import Path
from typing import Optional

import aiohttp

logger = logging.getLogger(__name__)


def get_chrome_cookies_for_domain(domain: str) -> dict:
    """
    Extract cookies from Chrome for a specific domain.

    Args:
        domain: Domain name (e.g., "academic.oup.com")

    Returns:
        Dictionary of cookies {name: value}
    """
    try:
        import browser_cookie3

        # Get Chrome cookies
        cookies = browser_cookie3.chrome(domain_name=domain)

        cookie_dict = {}
        for cookie in cookies:
            cookie_dict[cookie.name] = cookie.value

        logger.info(f"Extracted {len(cookie_dict)} cookies from Chrome for {domain}")
        return cookie_dict

    except ImportError:
        logger.error("browser-cookie3 not installed. Run: pip install browser-cookie3 pycryptodome")
        return {}
    except Exception as e:
        logger.warning(f"Could not extract Chrome cookies: {e}")
        logger.info("Make sure Chrome is closed or use a different profile")
        return {}


async def download_with_chrome_cookies(url: str, output_path: Path, timeout: int = 30) -> bool:
    """
    Download a file using cookies from Chrome browser.

    This allows downloading from sites where you're logged in via Chrome.

    Args:
        url: URL to download
        output_path: Where to save the file
        timeout: Request timeout in seconds

    Returns:
        True if download successful, False otherwise
    """
    from urllib.parse import urlparse

    # Extract domain from URL
    parsed = urlparse(url)
    domain = parsed.netloc

    # Get cookies from Chrome
    cookies = get_chrome_cookies_for_domain(domain)

    if not cookies:
        logger.warning(f"No cookies found for {domain}. Direct download may fail.")
    else:
        logger.info(f"Using {len(cookies)} cookies from Chrome session")

    # Create SSL context
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    try:
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        async with aiohttp.ClientSession(connector=connector, cookies=cookies) as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as response:
                if response.status == 200:
                    content = await response.read()

                    # Validate PDF
                    if content[:4] != b"%PDF":
                        logger.error(f"Downloaded file is not a PDF: {url}")
                        return False

                    # Save file
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    output_path.write_bytes(content)

                    logger.info(f"✅ Downloaded {len(content) // 1024} KB to {output_path}")
                    return True

                else:
                    logger.error(f"Download failed: HTTP {response.status} from {url}")
                    return False

    except Exception as e:
        logger.error(f"Error downloading with Chrome cookies: {e}")
        return False


async def test_chrome_cookie_download():
    """Test downloading with Chrome cookies."""

    # Example: Download from Oxford University Press (if logged in)
    url = "https://academic.oup.com/nar/article-pdf/53/4/gkaf101/62165164/gkaf101.pdf"
    output_path = Path("data/test_pdfs/chrome_cookie_test.pdf")

    print("\n" + "=" * 70)
    print("TESTING CHROME COOKIE DOWNLOAD")
    print("=" * 70)
    print(f"\nURL: {url}")
    print(f"Output: {output_path}")
    print("\nNote: You must be logged into academic.oup.com in Chrome")
    print("Make sure Chrome is closed or use a different profile\n")

    success = await download_with_chrome_cookies(url, output_path)

    if success:
        print("\n✅ SUCCESS! Downloaded using Chrome session cookies")
        print(f"File saved: {output_path}")
        print(f"Size: {output_path.stat().st_size // 1024} KB")
    else:
        print("\n❌ FAILED - You may not be logged in or cookies unavailable")
        print("Try:")
        print("1. Log into academic.oup.com in Chrome")
        print("2. Close Chrome completely")
        print("3. Run this script again")

    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(test_chrome_cookie_download())
