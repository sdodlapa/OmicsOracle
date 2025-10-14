"""
LibGen (Library Genesis) client for accessing scientific papers.

⚠️ IMPORTANT LEGAL NOTICE ⚠️
LibGen provides access to copyrighted scientific papers without publisher permission.
Use of this client may violate copyright laws in your jurisdiction.

This implementation is provided for:
- Research and educational purposes
- Jurisdictions where such use is legal
- Use with proper institutional approval

Users are responsible for ensuring compliance with applicable laws.

LibGen mirrors change frequently. This client includes:
- Multiple mirror fallback
- Automatic mirror selection
- Rate limiting to avoid abuse
- DOI and MD5 hash-based lookup
"""

import asyncio
import logging
import os
import random
import re
import ssl
from typing import Dict, List, Optional

import aiohttp
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# SSL context
SSL_CONTEXT = ssl.create_default_context()
if os.getenv("PYTHONHTTPSVERIFY", "1") == "0":
    SSL_CONTEXT.check_hostname = False
    SSL_CONTEXT.verify_mode = ssl.CERT_NONE


class LibGenConfig(BaseModel):
    """Configuration for LibGen client."""

    # Mirrors (updated as of Oct 2025 - these change frequently)
    mirrors: List[str] = Field(
        default_factory=lambda: [
            "https://libgen.is",
            "https://libgen.rs",
            "https://libgen.st",
        ],
        description="List of LibGen mirrors",
    )

    # Download mirrors (for actual PDF download)
    download_mirrors: List[str] = Field(
        default_factory=lambda: [
            "https://download.library.lol/main",
            "https://cloudflare-ipfs.com/ipfs",
        ],
        description="Download mirror URLs",
    )

    timeout: int = Field(15, ge=5, le=60, description="Request timeout in seconds")
    retry_count: int = Field(2, ge=1, le=5, description="Retries per mirror")
    rate_limit_delay: float = Field(2.0, ge=1.0, le=10.0, description="Delay between requests (seconds)")
    max_concurrent: int = Field(1, ge=1, le=3, description="Max concurrent requests (keep low)")


class LibGenClient:
    """
    Client for LibGen paper access.

    ⚠️ WARNING: Use responsibly and in compliance with local laws.

    Features:
    - Multiple mirror fallback
    - DOI-based lookup
    - Title-based search
    - MD5 hash-based direct download
    - Rate limiting

    Example:
        >>> config = LibGenConfig()
        >>> async with LibGenClient(config) as client:
        ...     pdf_url = await client.get_pdf_url("10.1038/nature12373")
        ...     if pdf_url:
        ...         print(f"PDF: {pdf_url}")
    """

    def __init__(self, config: LibGenConfig):
        """
        Initialize LibGen client.

        Args:
            config: LibGen configuration
        """
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.ssl_context = SSL_CONTEXT
        self._last_request_time = 0.0
        self._working_mirrors: List[str] = []
        self._failed_mirrors: set = set()

        logger.info(f"LibGen client initialized with {len(config.mirrors)} mirrors")

    async def __aenter__(self):
        """Async context manager entry."""
        # Browser-like headers to avoid bot detection
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

        connector = aiohttp.TCPConnector(ssl=self.ssl_context)
        self.session = aiohttp.ClientSession(headers=headers, connector=connector)

        # Initialize working mirrors list
        self._working_mirrors = self.config.mirrors.copy()
        random.shuffle(self._working_mirrors)  # Randomize to distribute load

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def close(self) -> None:
        """Close the aiohttp session.

        Week 3 Day 3: Added explicit close() method for proper resource cleanup.
        """
        if self.session:
            await self.session.close()
            self.session = None

    async def _rate_limit(self):
        """Apply rate limiting."""
        import time

        elapsed = time.time() - self._last_request_time
        if elapsed < self.config.rate_limit_delay:
            await asyncio.sleep(self.config.rate_limit_delay - elapsed)
        self._last_request_time = time.time()

    async def _search_by_doi(self, mirror: str, doi: str) -> Optional[Dict]:
        """
        Search LibGen by DOI.

        Args:
            mirror: LibGen mirror URL
            doi: DOI to search for

        Returns:
            Paper metadata dict or None
        """
        if not self.session:
            raise RuntimeError("Client not initialized.")

        # LibGen search API
        search_url = f"{mirror}/scimag/"
        params = {"q": doi}

        try:
            await self._rate_limit()

            async with self.session.get(
                search_url, params=params, timeout=self.config.timeout, ssl=self.ssl_context
            ) as response:
                if response.status not in [200, 301, 302]:
                    logger.debug(f"LibGen mirror {mirror} returned {response.status}")
                    return None

                html = await response.text()

                # Extract paper info from HTML
                # LibGen shows results in a table with MD5 hash in the first column
                metadata = self._parse_search_results(html)

                if metadata:
                    logger.debug(f"Found paper in LibGen via {mirror}")
                    return metadata
                else:
                    logger.debug(f"No results in LibGen from {mirror}")
                    return None

        except asyncio.TimeoutError:
            logger.debug(f"Timeout for LibGen mirror: {mirror}")
            return None
        except aiohttp.ClientError as e:
            logger.debug(f"Network error for LibGen mirror {mirror}: {e}")
            return None
        except Exception as e:
            logger.debug(f"Error accessing LibGen mirror {mirror}: {e}")
            return None

    def _parse_search_results(self, html: str) -> Optional[Dict]:
        """
        Parse LibGen search results HTML to extract paper metadata.

        Args:
            html: HTML content from search results

        Returns:
            Dict with md5, title, doi, or None
        """
        # Look for MD5 hash in the results table
        # LibGen format: <a href="http://library.lol/main/HASH">link</a>
        # or newer format: data-md5="HASH"

        # Pattern 1: Direct download link with MD5
        download_match = re.search(r"library\.lol/main/([a-f0-9]{32})", html, re.IGNORECASE)
        if download_match:
            md5_hash = download_match.group(1)
            return {"md5": md5_hash.lower()}

        # Pattern 2: IPFS link with MD5
        ipfs_match = re.search(r"cloudflare-ipfs\.com/ipfs/([a-zA-Z0-9]+)", html)
        if ipfs_match:
            ipfs_hash = ipfs_match.group(1)
            return {"ipfs": ipfs_hash}

        # Pattern 3: data-md5 attribute
        data_md5_match = re.search(r'data-md5="([a-f0-9]{32})"', html, re.IGNORECASE)
        if data_md5_match:
            md5_hash = data_md5_match.group(1)
            return {"md5": md5_hash.lower()}

        # Pattern 4: Look for any MD5-like hash in download URLs
        md5_pattern_match = re.search(r"/([a-f0-9]{32})", html, re.IGNORECASE)
        if md5_pattern_match:
            md5_hash = md5_pattern_match.group(1)
            return {"md5": md5_hash.lower()}

        return None

    def _construct_download_url(self, metadata: Dict) -> Optional[str]:
        """
        Construct download URL from metadata.

        Args:
            metadata: Paper metadata with md5 or ipfs hash

        Returns:
            Download URL or None
        """
        # Try MD5-based download first
        if "md5" in metadata:
            md5_hash = metadata["md5"]
            # Use library.lol as primary download mirror
            return f"https://download.library.lol/main/{md5_hash}"

        # Try IPFS-based download
        if "ipfs" in metadata:
            ipfs_hash = metadata["ipfs"]
            return f"https://cloudflare-ipfs.com/ipfs/{ipfs_hash}"

        return None

    async def _try_mirror(self, mirror: str, doi: str) -> Optional[str]:
        """
        Try to get PDF URL from a specific mirror.

        Args:
            mirror: LibGen mirror URL
            doi: DOI to search for

        Returns:
            PDF URL or None
        """
        # Search by DOI
        metadata = await self._search_by_doi(mirror, doi)

        if not metadata:
            return None

        # Construct download URL
        pdf_url = self._construct_download_url(metadata)

        if pdf_url:
            logger.info(f"✓ Found PDF via LibGen mirror: {mirror}")
            return pdf_url

        return None

    async def get_pdf_url(self, doi: str) -> Optional[str]:
        """
        Get PDF URL for a paper by DOI.

        Args:
            doi: DOI of the paper

        Returns:
            PDF URL or None

        Example:
            >>> url = await client.get_pdf_url("10.1038/nature12373")
        """
        await self._rate_limit()

        # Try mirrors in order
        for mirror in self._working_mirrors:
            if mirror in self._failed_mirrors:
                continue

            logger.debug(f"Trying LibGen mirror: {mirror}")

            for attempt in range(self.config.retry_count):
                pdf_url = await self._try_mirror(mirror, doi)

                if pdf_url:
                    return pdf_url

                if attempt < self.config.retry_count - 1:
                    await asyncio.sleep(1)

            # Mark mirror as failed for this session
            self._failed_mirrors.add(mirror)

        logger.debug(f"No working LibGen mirror found for: {doi}")
        return None

    async def batch_get_pdf_urls(self, dois: List[str]) -> List[Optional[str]]:
        """
        Get PDF URLs for multiple papers.

        Args:
            dois: List of DOIs

        Returns:
            List of PDF URLs (None for not found)

        Note: This is rate-limited to avoid overloading LibGen.
        """
        semaphore = asyncio.Semaphore(self.config.max_concurrent)

        async def get_with_semaphore(doi: str) -> Optional[str]:
            async with semaphore:
                return await self.get_pdf_url(doi)

        results = []
        for doi in dois:
            result = await get_with_semaphore(doi)
            results.append(result)
            # Small delay between batches
            await asyncio.sleep(self.config.rate_limit_delay)

        return results

    async def check_mirrors(self) -> List[str]:
        """
        Check which mirrors are currently accessible.

        Returns:
            List of working mirror URLs
        """
        working = []

        for mirror in self.config.mirrors:
            try:
                if not self.session:
                    raise RuntimeError("Client not initialized.")

                async with self.session.get(
                    mirror, timeout=5, ssl=self.ssl_context, allow_redirects=True
                ) as response:
                    if response.status in [200, 301, 302]:
                        working.append(mirror)
                        logger.info(f"✓ LibGen mirror accessible: {mirror}")
                    else:
                        logger.debug(f"✗ Mirror returned {response.status}: {mirror}")
            except Exception as e:
                logger.debug(f"✗ LibGen mirror not accessible: {mirror} ({e})")

        return working


# Convenience function
async def get_libgen_pdf(doi: str) -> Optional[str]:
    """
    Quick helper to get PDF URL from LibGen.

    Args:
        doi: DOI of the paper

    Returns:
        PDF URL or None

    Example:
        >>> url = await get_libgen_pdf("10.1038/nature12373")
        >>> if url:
        ...     print(f"PDF: {url}")
    """
    config = LibGenConfig()
    async with LibGenClient(config) as client:
        return await client.get_pdf_url(doi)
