"""
Unpaywall client for finding open access full-text papers.

Unpaywall (https://unpaywall.org) is a legal, free API that indexes
20M+ open access papers from publishers, repositories, and preprint servers.

API Documentation: https://unpaywall.org/products/api
No API key required (just an email for identification)
"""

import asyncio
import logging
import os
import ssl
from typing import Dict, List, Optional

import aiohttp
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# SSL context for institutional networks
SSL_CONTEXT = ssl.create_default_context()
if os.getenv("PYTHONHTTPSVERIFY", "1") == "0":
    SSL_CONTEXT.check_hostname = False
    SSL_CONTEXT.verify_mode = ssl.CERT_NONE


class UnpaywallConfig(BaseModel):
    """Configuration for Unpaywall API."""

    email: str = Field(..., description="Email for API identification (required)")
    api_url: str = Field("https://api.unpaywall.org/v2", description="API base URL")
    timeout: int = Field(10, ge=1, le=60, description="Request timeout in seconds")
    retry_count: int = Field(3, ge=1, le=5, description="Number of retries")


class UnpaywallClient:
    """
    Client for Unpaywall API.

    Features:
    - Get OA status and full-text URLs by DOI
    - No API key required (just email)
    - Covers 20M+ open access papers
    - Legal and sustainable

    Example:
        >>> config = UnpaywallConfig(email="researcher@university.edu")
        >>> async with UnpaywallClient(config) as client:
        ...     result = await client.get_oa_location("10.1038/nature12373")
        ...     if result:
        ...         print(result['best_oa_location']['url'])
    """

    def __init__(self, config: UnpaywallConfig):
        """
        Initialize Unpaywall client.

        Args:
            config: Unpaywall configuration
        """
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.ssl_context = SSL_CONTEXT

        logger.info(f"Unpaywall client initialized (email={config.email})")

    async def __aenter__(self):
        """Async context manager entry."""
        connector = aiohttp.TCPConnector(ssl=self.ssl_context)
        self.session = aiohttp.ClientSession(connector=connector)
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

    async def get_oa_location(self, doi: str) -> Optional[Dict]:
        """
        Get open access location for a DOI.

        Args:
            doi: Digital Object Identifier

        Returns:
            Dict with OA information, or None if not found

            Example response:
            {
                'doi': '10.1038/nature12373',
                'is_oa': True,
                'best_oa_location': {
                    'url': 'https://www.nature.com/articles/nature12373.pdf',
                    'url_for_pdf': 'https://www.nature.com/articles/nature12373.pdf',
                    'url_for_landing_page': 'https://doi.org/10.1038/nature12373',
                    'version': 'publishedVersion',
                    'license': 'cc-by'
                },
                'oa_locations': [...],  # All OA locations
                'title': 'Paper title',
                'journal_name': 'Nature',
                'publisher': 'Springer Nature',
                'year': 2013
            }
        """
        if not doi:
            return None

        # Clean DOI
        doi = doi.replace("https://doi.org/", "").replace("http://doi.org/", "").strip()

        if not self.session:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")

        url = f"{self.config.api_url}/{doi}"
        params = {"email": self.config.email}

        for attempt in range(self.config.retry_count):
            try:
                async with self.session.get(
                    url, params=params, timeout=self.config.timeout, ssl=self.ssl_context
                ) as response:
                    if response.status == 200:
                        data = await response.json()

                        # Check if it's OA
                        if not data.get("is_oa"):
                            logger.debug(f"Not OA in Unpaywall: {doi}")
                            return None

                        logger.info(f"✓ Found OA in Unpaywall: {doi}")
                        return data

                    elif response.status == 404:
                        logger.debug(f"DOI not found in Unpaywall: {doi}")
                        return None

                    elif response.status == 429:
                        # Rate limited (should not happen with polite use)
                        wait_time = (attempt + 1) * 2
                        logger.warning(f"Rate limited by Unpaywall, waiting {wait_time}s")
                        await asyncio.sleep(wait_time)
                        continue

                    else:
                        logger.warning(f"Unpaywall API error {response.status} for DOI: {doi}")
                        return None

            except asyncio.TimeoutError:
                logger.debug(f"Unpaywall timeout for DOI: {doi}")
                if attempt < self.config.retry_count - 1:
                    await asyncio.sleep(1)
                    continue
                return None

            except aiohttp.ClientError as e:
                logger.debug(f"Network error on Unpaywall request: {e}")
                if attempt < self.config.retry_count - 1:
                    await asyncio.sleep(attempt + 1)
                    continue
                return None

            except Exception as e:
                logger.warning(f"Unexpected error in Unpaywall request: {e}")
                return None

        return None

    async def get_pdf_url(self, doi: str) -> Optional[str]:
        """
        Get best PDF URL for a DOI.

        Args:
            doi: Digital Object Identifier

        Returns:
            PDF URL or None
        """
        result = await self.get_oa_location(doi)

        if not result:
            return None

        # Try best_oa_location first
        best_oa = result.get("best_oa_location")
        if best_oa:
            # Prefer direct PDF URL
            pdf_url = best_oa.get("url_for_pdf")
            if pdf_url:
                return pdf_url

            # Fall back to regular URL if it's a PDF
            url = best_oa.get("url")
            if url and url.lower().endswith(".pdf"):
                return url

        # Try other OA locations
        for location in result.get("oa_locations", []):
            pdf_url = location.get("url_for_pdf")
            if pdf_url:
                return pdf_url

            url = location.get("url")
            if url and url.lower().endswith(".pdf"):
                return url

        return None

    async def batch_get_oa(self, dois: List[str], max_concurrent: int = 5) -> List[Optional[Dict]]:
        """
        Get OA information for multiple DOIs concurrently.

        Args:
            dois: List of DOIs
            max_concurrent: Maximum concurrent requests

        Returns:
            List of OA information dicts (None for not found)
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def get_with_semaphore(doi: str) -> Optional[Dict]:
            async with semaphore:
                return await self.get_oa_location(doi)

        tasks = [get_with_semaphore(doi) for doi in dois]
        return await asyncio.gather(*tasks)


# Convenience function
async def get_unpaywall_pdf(doi: str, email: str) -> Optional[str]:
    """
    Quick helper to get PDF URL from Unpaywall.

    Args:
        doi: Digital Object Identifier
        email: Email for API identification

    Returns:
        PDF URL or None

    Example:
        >>> url = await get_unpaywall_pdf("10.1038/nature12373", "user@example.com")
        >>> if url:
        ...     print(f"PDF available at: {url}")
    """
    config = UnpaywallConfig(email=email)
    async with UnpaywallClient(config) as client:
        return await client.get_pdf_url(doi)
