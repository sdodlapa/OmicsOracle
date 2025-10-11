"""
Content fetcher for retrieving full-text articles from various sources.

This module handles the actual fetching of XML/HTML/PDF content from external APIs
and repositories, with proper rate limiting and error handling.
"""

import asyncio
import logging
import ssl
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import aiofiles
import aiohttp

from lib.fulltext.models import ContentType, SourceType

logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple rate limiter for API requests."""

    def __init__(self, requests_per_second: float = 3.0):
        """
        Initialize rate limiter.

        Args:
            requests_per_second: Maximum requests allowed per second
        """
        self.requests_per_second = requests_per_second
        self.min_interval = 1.0 / requests_per_second
        self.last_request_time: Optional[datetime] = None

    async def wait(self):
        """Wait if necessary to respect rate limit."""
        if self.last_request_time:
            elapsed = (datetime.now() - self.last_request_time).total_seconds()
            if elapsed < self.min_interval:
                await asyncio.sleep(self.min_interval - elapsed)
        self.last_request_time = datetime.now()


class ContentFetcher:
    """
    Fetches full-text content from various sources.

    Handles:
    - PMC XML via NCBI E-utilities
    - PDF downloads from various sources
    - Rate limiting
    - Retry logic with exponential backoff
    - Disk caching
    """

    def __init__(
        self,
        cache_dir: Path,
        api_key: Optional[str] = None,
        requests_per_second: float = 3.0,
        max_retries: int = 3,
    ):
        """
        Initialize content fetcher.

        Args:
            cache_dir: Directory to cache downloaded content
            api_key: NCBI API key (allows 10 req/sec instead of 3)
            requests_per_second: Rate limit (3 without key, 10 with key)
            max_retries: Maximum retry attempts for failed requests
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.api_key = api_key
        self.max_retries = max_retries

        # NCBI E-utilities base URLs
        self.efetch_base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

        # Rate limiter (10 req/sec with API key, 3 without)
        rate = 10.0 if api_key else requests_per_second
        self.rate_limiter = RateLimiter(rate)

        logger.info(f"ContentFetcher initialized (rate: {rate} req/sec, cache: {cache_dir})")

    async def fetch_xml(
        self, source: SourceType, identifier: str, use_cache: bool = True
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Fetch XML content from a source.

        Args:
            source: Source type (e.g., PMC)
            identifier: Article identifier (e.g., PMC ID)
            use_cache: Whether to use cached version if available

        Returns:
            Tuple of (success, xml_content, error_message)
        """
        if source == SourceType.PMC:
            return await self._fetch_pmc_xml(identifier, use_cache)
        else:
            return False, None, f"Unsupported XML source: {source}"

    async def _fetch_pmc_xml(
        self, pmc_id: str, use_cache: bool = True
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Fetch XML from PubMed Central using E-utilities.

        Args:
            pmc_id: PMC ID (with or without 'PMC' prefix)
            use_cache: Whether to use cached version

        Returns:
            Tuple of (success, xml_content, error_message)
        """
        # Normalize PMC ID (remove 'PMC' prefix if present)
        clean_id = pmc_id.replace("PMC", "")

        # Check cache first
        cache_file = self.cache_dir / "xml" / "pmc" / f"{clean_id}.nxml"
        if use_cache and cache_file.exists():
            try:
                async with aiofiles.open(cache_file, "r", encoding="utf-8") as f:
                    content = await f.read()
                logger.info(f"PMC{clean_id}: Loaded from cache")
                return True, content, None
            except Exception as e:
                logger.warning(f"PMC{clean_id}: Cache read error: {e}")

        # Fetch from NCBI
        params = {"db": "pmc", "id": clean_id, "retmode": "xml", "rettype": "full"}
        if self.api_key:
            params["api_key"] = self.api_key

        for attempt in range(self.max_retries):
            try:
                await self.rate_limiter.wait()

                # Create SSL context that doesn't verify certificates (for demo)
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE

                async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context)) as session:
                    async with session.get(self.efetch_base, params=params) as response:
                        if response.status == 200:
                            content = await response.text()

                            # Check if response contains error message
                            if "<ERROR>" in content or len(content) < 100:
                                error_msg = "Invalid response from NCBI"
                                logger.warning(f"PMC{clean_id}: {error_msg}")
                                return False, None, error_msg

                            # Save to cache
                            cache_file.parent.mkdir(parents=True, exist_ok=True)
                            async with aiofiles.open(cache_file, "w", encoding="utf-8") as f:
                                await f.write(content)

                            logger.info(f"PMC{clean_id}: Fetched successfully ({len(content)} bytes)")
                            return True, content, None

                        elif response.status == 429:  # Too many requests
                            wait_time = 2**attempt
                            logger.warning(f"PMC{clean_id}: Rate limited, waiting {wait_time}s")
                            await asyncio.sleep(wait_time)
                            continue

                        else:
                            error_msg = f"HTTP {response.status}"
                            logger.warning(f"PMC{clean_id}: {error_msg}")
                            if attempt < self.max_retries - 1:
                                await asyncio.sleep(2**attempt)
                                continue
                            return False, None, error_msg

            except aiohttp.ClientError as e:
                logger.warning(f"PMC{clean_id}: Network error (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2**attempt)
                    continue
                return False, None, f"Network error: {e}"

            except Exception as e:
                logger.error(f"PMC{clean_id}: Unexpected error: {e}")
                return False, None, f"Unexpected error: {e}"

        return False, None, "Max retries exceeded"

    async def fetch_pdf(
        self, url: str, source: SourceType, identifier: str, use_cache: bool = True
    ) -> Tuple[bool, Optional[Path], Optional[str]]:
        """
        Download PDF from a URL.

        Args:
            url: PDF download URL
            source: Source type
            identifier: Article identifier for cache filename
            use_cache: Whether to use cached version

        Returns:
            Tuple of (success, pdf_path, error_message)
        """
        # Check cache
        cache_subdir = self.cache_dir / "pdf" / source.value
        cache_file = cache_subdir / f"{identifier}.pdf"

        if use_cache and cache_file.exists():
            logger.info(f"{identifier}: PDF loaded from cache")
            return True, cache_file, None

        # Download PDF
        for attempt in range(self.max_retries):
            try:
                await self.rate_limiter.wait()

                # Create SSL context that doesn't verify certificates (for demo)
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE

                async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context)) as session:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as response:
                        if response.status == 200:
                            content = await response.read()

                            # Verify it's a PDF
                            if not content.startswith(b"%PDF"):
                                error_msg = "Response is not a valid PDF"
                                logger.warning(f"{identifier}: {error_msg}")
                                return False, None, error_msg

                            # Save to cache
                            cache_subdir.mkdir(parents=True, exist_ok=True)
                            async with aiofiles.open(cache_file, "wb") as f:
                                await f.write(content)

                            logger.info(f"{identifier}: PDF downloaded ({len(content)} bytes)")
                            return True, cache_file, None

                        else:
                            error_msg = f"HTTP {response.status}"
                            logger.warning(f"{identifier}: {error_msg}")
                            if attempt < self.max_retries - 1:
                                await asyncio.sleep(2**attempt)
                                continue
                            return False, None, error_msg

            except asyncio.TimeoutError:
                logger.warning(f"{identifier}: Download timeout (attempt {attempt + 1})")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2**attempt)
                    continue
                return False, None, "Download timeout"

            except Exception as e:
                logger.error(f"{identifier}: Download error: {e}")
                return False, None, f"Download error: {e}"

        return False, None, "Max retries exceeded"

    def get_cache_path(self, content_type: ContentType, source: SourceType, identifier: str) -> Path:
        """
        Get the cache path for a specific article.

        Args:
            content_type: Type of content (XML, PDF, etc.)
            source: Source of content
            identifier: Article identifier

        Returns:
            Path to cached file
        """
        if content_type == ContentType.XML:
            return self.cache_dir / "xml" / source.value / f"{identifier}.nxml"
        elif content_type == ContentType.PDF:
            return self.cache_dir / "pdf" / source.value / f"{identifier}.pdf"
        elif content_type == ContentType.HTML:
            return self.cache_dir / "html" / source.value / f"{identifier}.html"
        else:
            return self.cache_dir / "text" / source.value / f"{identifier}.txt"
