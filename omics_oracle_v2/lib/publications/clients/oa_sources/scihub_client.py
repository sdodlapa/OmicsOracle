"""
Sci-Hub client for accessing scientific papers.

⚠️ IMPORTANT LEGAL NOTICE ⚠️
Sci-Hub provides access to copyrighted scientific papers without publisher permission.
Use of this client may violate copyright laws in your jurisdiction.

This implementation is provided for:
- Research and educational purposes
- Jurisdictions where such use is legal
- Use with proper institutional approval

Users are responsible for ensuring compliance with applicable laws.

Sci-Hub mirrors change frequently. This client includes:
- Multiple mirror fallback
- Automatic mirror selection
- Rate limiting to avoid abuse
- Optional Tor/proxy support (for privacy)
"""

import asyncio
import logging
import os
import random
import re
import ssl
from typing import Dict, List, Optional
from urllib.parse import quote

import aiohttp
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# SSL context
SSL_CONTEXT = ssl.create_default_context()
if os.getenv("PYTHONHTTPSVERIFY", "1") == "0":
    SSL_CONTEXT.check_hostname = False
    SSL_CONTEXT.verify_mode = ssl.CERT_NONE


class SciHubConfig(BaseModel):
    """Configuration for Sci-Hub client."""

    # Mirrors (updated as of Oct 2025 - these change frequently)
    mirrors: List[str] = Field(
        default_factory=lambda: [
            "https://sci-hub.se",
            "https://sci-hub.st",
            "https://sci-hub.ru",
            "https://sci-hub.ren",
            "https://sci-hub.si",
        ],
        description="List of Sci-Hub mirrors",
    )

    timeout: int = Field(15, ge=5, le=60, description="Request timeout in seconds")
    retry_count: int = Field(2, ge=1, le=5, description="Retries per mirror")
    rate_limit_delay: float = Field(2.0, ge=1.0, le=10.0, description="Delay between requests (seconds)")
    use_proxy: bool = Field(False, description="Use proxy/Tor for requests")
    proxy_url: Optional[str] = Field(None, description="Proxy URL (e.g., socks5://localhost:9050 for Tor)")
    max_concurrent: int = Field(1, ge=1, le=3, description="Max concurrent requests (keep low)")


class SciHubClient:
    """
    Client for Sci-Hub paper access.

    ⚠️ WARNING: Use responsibly and in compliance with local laws.

    Features:
    - Multiple mirror fallback
    - DOI and PMID lookup
    - PDF download links
    - Rate limiting
    - Optional proxy/Tor support

    Example:
        >>> config = SciHubConfig()
        >>> async with SciHubClient(config) as client:
        ...     pdf_url = await client.get_pdf_url("10.1038/nature12373")
        ...     if pdf_url:
        ...         print(f"PDF: {pdf_url}")
    """

    def __init__(self, config: SciHubConfig):
        """
        Initialize Sci-Hub client.

        Args:
            config: Sci-Hub configuration
        """
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.ssl_context = SSL_CONTEXT
        self._last_request_time = 0.0
        self._working_mirrors: List[str] = []
        self._failed_mirrors: set = set()

        logger.info(f"Sci-Hub client initialized with {len(config.mirrors)} mirrors")
        if config.use_proxy:
            logger.info(f"Using proxy: {config.proxy_url}")

    async def __aenter__(self):
        """Async context manager entry."""
        connector_kwargs = {"ssl": self.ssl_context}

        if self.config.use_proxy and self.config.proxy_url:
            connector_kwargs["proxy"] = self.config.proxy_url

        connector = aiohttp.TCPConnector(**connector_kwargs)
        self.session = aiohttp.ClientSession(connector=connector)

        # Initialize working mirrors list
        self._working_mirrors = self.config.mirrors.copy()
        random.shuffle(self._working_mirrors)  # Randomize to distribute load

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def _rate_limit(self):
        """Apply rate limiting."""
        import time

        elapsed = time.time() - self._last_request_time
        if elapsed < self.config.rate_limit_delay:
            await asyncio.sleep(self.config.rate_limit_delay - elapsed)
        self._last_request_time = time.time()

    async def _try_mirror(self, mirror: str, identifier: str) -> Optional[str]:
        """
        Try to get PDF URL from a specific mirror.

        Args:
            mirror: Sci-Hub mirror URL
            identifier: DOI, PMID, or other identifier

        Returns:
            PDF URL or None
        """
        if not self.session:
            raise RuntimeError("Client not initialized.")

        # Construct Sci-Hub URL
        # Sci-Hub accepts: /DOI or /PMID or /URL
        search_url = f"{mirror}/{quote(identifier)}"

        try:
            async with self.session.get(
                search_url, timeout=self.config.timeout, ssl=self.ssl_context
            ) as response:
                if response.status != 200:
                    logger.debug(f"Mirror {mirror} returned {response.status}")
                    return None

                html = await response.text()

                # Extract PDF URL from HTML
                # Sci-Hub shows PDF in an iframe or embed tag
                pdf_url = self._extract_pdf_url(html, mirror)

                if pdf_url:
                    logger.info(f"✓ Found PDF via Sci-Hub mirror: {mirror}")
                    return pdf_url
                else:
                    logger.debug(f"No PDF found in Sci-Hub response from {mirror}")
                    return None

        except asyncio.TimeoutError:
            logger.debug(f"Timeout for mirror: {mirror}")
            return None
        except aiohttp.ClientError as e:
            logger.debug(f"Network error for mirror {mirror}: {e}")
            return None
        except Exception as e:
            logger.debug(f"Error accessing mirror {mirror}: {e}")
            return None

    def _extract_pdf_url(self, html: str, mirror: str) -> Optional[str]:
        """
        Extract PDF URL from Sci-Hub HTML response.

        Args:
            html: HTML content
            mirror: Base mirror URL

        Returns:
            PDF URL or None
        """
        # Pattern 1: embed tag (most common - try first)
        # Matches both <embed src="//domain/path.pdf"> and type="application/pdf"
        embed_match = re.search(r'<embed[^>]+src="([^"]+)"', html, re.IGNORECASE)
        if embed_match:
            url = embed_match.group(1)
            # Verify it's a PDF (either has .pdf or type="application/pdf")
            if (
                ".pdf" in url.lower()
                or 'type="application/pdf"'
                in html[max(0, embed_match.start() - 100) : embed_match.end() + 50]
            ):
                return self._normalize_url(url, mirror)

        # Pattern 2: iframe with PDF
        iframe_match = re.search(r'<iframe[^>]+src="([^"]+)"', html, re.IGNORECASE)
        if iframe_match:
            url = iframe_match.group(1)
            if ".pdf" in url.lower():
                return self._normalize_url(url, mirror)

        # Pattern 3: Direct link button
        button_match = re.search(r'<button[^>]+onclick="location\.href=\'([^\']+)\'', html)
        if button_match:
            url = button_match.group(1)
            if ".pdf" in url.lower():
                return self._normalize_url(url, mirror)

        # Pattern 4: Meta tag redirect
        meta_match = re.search(r'<meta[^>]+content="0;url=([^"]+)"', html, re.IGNORECASE)
        if meta_match:
            url = meta_match.group(1)
            if ".pdf" in url.lower():
                return self._normalize_url(url, mirror)

        # Pattern 5: Any link to PDF (protocol-relative or absolute)
        pdf_link_match = re.search(r'(?:https?:)?//[^"\s]+\.pdf[^"\s]*', html)
        if pdf_link_match:
            return self._normalize_url(pdf_link_match.group(0), mirror)

        return None

    def _normalize_url(self, url: str, mirror: str) -> str:
        """
        Normalize relative URLs to absolute.

        Args:
            url: URL (possibly relative)
            mirror: Base mirror URL

        Returns:
            Absolute URL
        """
        if url.startswith("http://") or url.startswith("https://"):
            return url
        elif url.startswith("//"):
            return "https:" + url
        elif url.startswith("/"):
            return mirror + url
        else:
            return mirror + "/" + url

    async def get_pdf_url(self, identifier: str) -> Optional[str]:
        """
        Get PDF URL for a paper by DOI, PMID, or URL.

        Args:
            identifier: DOI, PMID, or paper URL

        Returns:
            PDF URL or None

        Example:
            >>> url = await client.get_pdf_url("10.1038/nature12373")
            >>> url = await client.get_pdf_url("23222524")  # PMID
        """
        await self._rate_limit()

        # Try mirrors in order
        for mirror in self._working_mirrors:
            if mirror in self._failed_mirrors:
                continue

            logger.debug(f"Trying Sci-Hub mirror: {mirror}")

            for attempt in range(self.config.retry_count):
                pdf_url = await self._try_mirror(mirror, identifier)

                if pdf_url:
                    return pdf_url

                if attempt < self.config.retry_count - 1:
                    await asyncio.sleep(1)

            # Mark mirror as failed for this session
            self._failed_mirrors.add(mirror)

        logger.debug(f"No working Sci-Hub mirror found for: {identifier}")
        return None

    async def batch_get_pdf_urls(self, identifiers: List[str]) -> List[Optional[str]]:
        """
        Get PDF URLs for multiple papers.

        Args:
            identifiers: List of DOIs, PMIDs, or URLs

        Returns:
            List of PDF URLs (None for not found)

        Note: This is rate-limited to avoid overloading Sci-Hub.
        """
        semaphore = asyncio.Semaphore(self.config.max_concurrent)

        async def get_with_semaphore(identifier: str) -> Optional[str]:
            async with semaphore:
                return await self.get_pdf_url(identifier)

        results = []
        for identifier in identifiers:
            result = await get_with_semaphore(identifier)
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
                    if response.status == 200:
                        working.append(mirror)
                        logger.info(f"✓ Mirror accessible: {mirror}")
                    else:
                        logger.debug(f"✗ Mirror returned {response.status}: {mirror}")
            except Exception as e:
                logger.debug(f"✗ Mirror not accessible: {mirror} ({e})")

        return working


# Convenience function
async def get_scihub_pdf(identifier: str, use_proxy: bool = False) -> Optional[str]:
    """
    Quick helper to get PDF URL from Sci-Hub.

    Args:
        identifier: DOI, PMID, or paper URL
        use_proxy: Whether to use Tor/proxy

    Returns:
        PDF URL or None

    Example:
        >>> url = await get_scihub_pdf("10.1038/nature12373")
        >>> if url:
        ...     print(f"PDF: {url}")
    """
    config = SciHubConfig(use_proxy=use_proxy)
    async with SciHubClient(config) as client:
        return await client.get_pdf_url(identifier)
