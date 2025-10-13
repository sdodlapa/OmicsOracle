"""
PDF downloader for retrieving full-text PDFs from various sources.

This module handles downloading PDFs from:
- Unpaywall (best_oa_location.url_for_pdf)
- CORE API (downloadUrl)
- arXiv (pdf_url)
- bioRxiv (pdf_url)
- Publisher websites (when available)

PDFs are validated and cached to disk for future use.
NO PARSING - just download and store for later processing.
"""

import asyncio
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple

import aiofiles
import aiohttp

from lib.fulltext.models import SourceType

logger = logging.getLogger(__name__)


class PDFDownloader:
    """
    Downloads PDFs from various open access sources.

    Features:
    - Multi-source support (Unpaywall, CORE, arXiv, bioRxiv)
    - PDF validation (signature check, size check)
    - Disk caching with metadata
    - Rate limiting per source
    - Retry logic with exponential backoff
    """

    def __init__(
        self,
        cache_dir: Path = Path("data/fulltext/pdf"),
        timeout: int = 60,
        max_retries: int = 3,
        min_pdf_size: int = 10240,  # 10KB minimum
        max_pdf_size: int = 104857600,  # 100MB maximum
    ):
        """
        Initialize PDF downloader.

        Args:
            cache_dir: Base directory for PDF cache
            timeout: Download timeout in seconds
            max_retries: Maximum retry attempts
            min_pdf_size: Minimum valid PDF size in bytes
            max_pdf_size: Maximum PDF size to download
        """
        self.cache_dir = Path(cache_dir)
        self.timeout = timeout
        self.max_retries = max_retries
        self.min_pdf_size = min_pdf_size
        self.max_pdf_size = max_pdf_size

        # Create cache directories
        for source in ["unpaywall", "core", "arxiv", "biorxiv", "publisher"]:
            (self.cache_dir / source).mkdir(parents=True, exist_ok=True)

        logger.info(
            f"PDFDownloader initialized (cache: {cache_dir}, "
            f"timeout: {timeout}s, max_size: {max_pdf_size/1024/1024:.0f}MB)"
        )

    def _get_cache_path(self, source: SourceType, identifier: str) -> Tuple[Path, Path]:
        """
        Get cache file paths for PDF and metadata.

        Args:
            source: Source type
            identifier: Identifier (DOI, arXiv ID, etc.)

        Returns:
            Tuple of (pdf_path, metadata_path)
        """
        # Create safe filename from identifier
        safe_id = hashlib.md5(identifier.encode()).hexdigest()

        source_dir = self.cache_dir / source.value
        pdf_path = source_dir / f"{safe_id}.pdf"
        metadata_path = source_dir / f"{safe_id}.json"

        return pdf_path, metadata_path

    async def _validate_pdf(self, content: bytes) -> Tuple[bool, Optional[str]]:
        """
        Validate PDF content.

        Args:
            content: PDF file bytes

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check size
        if len(content) < self.min_pdf_size:
            return False, f"File too small: {len(content)} bytes"

        if len(content) > self.max_pdf_size:
            return False, f"File too large: {len(content)} bytes"

        # Check PDF signature
        if not content.startswith(b"%PDF"):
            return False, "Not a valid PDF file (missing %PDF header)"

        # Check for truncated PDF
        if b"%%EOF" not in content[-1024:]:
            return False, "PDF appears truncated (missing %%EOF marker)"

        return True, None

    async def download_pdf(
        self,
        url: str,
        source: SourceType,
        identifier: str,
        use_cache: bool = True,
        metadata: Optional[Dict] = None,
    ) -> Tuple[bool, Optional[Path], Optional[str]]:
        """
        Download PDF from URL.

        Args:
            url: PDF download URL
            source: Source type (for cache organization)
            identifier: Article identifier (DOI, arXiv ID, etc.)
            use_cache: Whether to use cached version if available
            metadata: Optional metadata to store with PDF

        Returns:
            Tuple of (success, pdf_path, error_message)
        """
        pdf_path, metadata_path = self._get_cache_path(source, identifier)

        # Check cache
        if use_cache and pdf_path.exists():
            logger.info(f"{identifier}: PDF loaded from cache ({source.value})")
            return True, pdf_path, None

        logger.info(f"{identifier}: Downloading PDF from {source.value}")

        # Download PDF
        for attempt in range(self.max_retries):
            try:
                # Create SSL context (handle self-signed certificates)
                import ssl

                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE

                connector = aiohttp.TCPConnector(ssl=ssl_context)
                timeout_config = aiohttp.ClientTimeout(total=self.timeout)

                async with aiohttp.ClientSession(connector=connector, timeout=timeout_config) as session:
                    async with session.get(url) as response:
                        if response.status == 200:
                            content = await response.read()

                            # Validate PDF
                            is_valid, error = await self._validate_pdf(content)
                            if not is_valid:
                                logger.warning(f"{identifier}: Invalid PDF - {error}")
                                return False, None, f"Invalid PDF: {error}"

                            # Save PDF to cache
                            async with aiofiles.open(pdf_path, "wb") as f:
                                await f.write(content)

                            # Save metadata
                            if metadata is None:
                                metadata = {}

                            metadata.update(
                                {
                                    "identifier": identifier,
                                    "source": source.value,
                                    "url": url,
                                    "download_date": datetime.now().isoformat(),
                                    "file_size": len(content),
                                    "sha256": hashlib.sha256(content).hexdigest(),
                                }
                            )

                            import json

                            async with aiofiles.open(metadata_path, "w", encoding="utf-8") as f:
                                await f.write(json.dumps(metadata, indent=2))

                            logger.info(
                                f"{identifier}: PDF downloaded successfully "
                                f"({len(content)/1024:.0f}KB from {source.value})"
                            )
                            return True, pdf_path, None

                        elif response.status == 404:
                            error_msg = "PDF not found (404)"
                            logger.warning(f"{identifier}: {error_msg}")
                            return False, None, error_msg

                        elif response.status == 403:
                            error_msg = "Access forbidden (403)"
                            logger.warning(f"{identifier}: {error_msg}")
                            return False, None, error_msg

                        elif response.status == 429:  # Rate limited
                            wait_time = 2**attempt
                            logger.warning(f"{identifier}: Rate limited, waiting {wait_time}s")
                            await asyncio.sleep(wait_time)
                            continue

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

            except aiohttp.ClientError as e:
                logger.warning(f"{identifier}: Network error (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2**attempt)
                    continue
                return False, None, f"Network error: {e}"

            except Exception as e:
                logger.error(f"{identifier}: Unexpected error: {e}", exc_info=True)
                return False, None, f"Unexpected error: {e}"

        return False, None, "Max retries exceeded"

    async def download_from_unpaywall(
        self, doi: str, oa_location: Dict, use_cache: bool = True
    ) -> Tuple[bool, Optional[Path], Optional[str]]:
        """
        Download PDF from Unpaywall oa_location.

        Args:
            doi: DOI of the article
            oa_location: Unpaywall oa_location dict with url_for_pdf
            use_cache: Whether to use cached version

        Returns:
            Tuple of (success, pdf_path, error_message)
        """
        pdf_url = oa_location.get("url_for_pdf")
        if not pdf_url:
            return False, None, "No PDF URL in oa_location"

        metadata = {
            "doi": doi,
            "oa_status": oa_location.get("oa_status"),
            "host_type": oa_location.get("host_type"),
            "version": oa_location.get("version"),
            "license": oa_location.get("license"),
        }

        return await self.download_pdf(
            url=pdf_url,
            source=SourceType.UNPAYWALL,
            identifier=doi,
            use_cache=use_cache,
            metadata=metadata,
        )

    async def download_from_core(
        self, core_id: str, download_url: str, use_cache: bool = True
    ) -> Tuple[bool, Optional[Path], Optional[str]]:
        """
        Download PDF from CORE.

        Args:
            core_id: CORE article ID
            download_url: CORE download URL
            use_cache: Whether to use cached version

        Returns:
            Tuple of (success, pdf_path, error_message)
        """
        metadata = {
            "core_id": core_id,
        }

        return await self.download_pdf(
            url=download_url,
            source=SourceType.CORE,
            identifier=core_id,
            use_cache=use_cache,
            metadata=metadata,
        )

    async def download_from_arxiv(
        self, arxiv_id: str, use_cache: bool = True
    ) -> Tuple[bool, Optional[Path], Optional[str]]:
        """
        Download PDF from arXiv.

        Args:
            arxiv_id: arXiv ID (e.g., "2301.12345")
            use_cache: Whether to use cached version

        Returns:
            Tuple of (success, pdf_path, error_message)
        """
        # arXiv PDF URL format
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

        metadata = {
            "arxiv_id": arxiv_id,
        }

        return await self.download_pdf(
            url=pdf_url,
            source=SourceType.ARXIV,
            identifier=arxiv_id,
            use_cache=use_cache,
            metadata=metadata,
        )

    async def download_from_biorxiv(
        self, doi: str, use_cache: bool = True
    ) -> Tuple[bool, Optional[Path], Optional[str]]:
        """
        Download PDF from bioRxiv/medRxiv.

        Args:
            doi: bioRxiv/medRxiv DOI (e.g., "10.1101/2024.01.12.575432")
            use_cache: Whether to use cached version

        Returns:
            Tuple of (success, pdf_path, error_message)
        """
        # bioRxiv PDF URL format
        # Example: https://www.biorxiv.org/content/10.1101/2024.01.12.575432v1.full.pdf
        pdf_url = f"https://www.biorxiv.org/content/{doi}.full.pdf"

        metadata = {
            "doi": doi,
        }

        return await self.download_pdf(
            url=pdf_url,
            source=SourceType.BIORXIV,
            identifier=doi,
            use_cache=use_cache,
            metadata=metadata,
        )

    async def get_cached_pdf(self, source: SourceType, identifier: str) -> Optional[Path]:
        """
        Get cached PDF path if it exists.

        Args:
            source: Source type
            identifier: Article identifier

        Returns:
            Path to cached PDF or None
        """
        pdf_path, _ = self._get_cache_path(source, identifier)
        return pdf_path if pdf_path.exists() else None

    async def get_pdf_metadata(self, source: SourceType, identifier: str) -> Optional[Dict]:
        """
        Get metadata for cached PDF.

        Args:
            source: Source type
            identifier: Article identifier

        Returns:
            Metadata dict or None
        """
        _, metadata_path = self._get_cache_path(source, identifier)

        if not metadata_path.exists():
            return None

        import json

        async with aiofiles.open(metadata_path, "r", encoding="utf-8") as f:
            content = await f.read()
            return json.loads(content)


# Convenience functions for common use cases


async def download_pdf_from_doi(
    doi: str,
    unpaywall_client=None,
    core_client=None,
    cache_dir: Path = Path("data/fulltext/pdf"),
) -> Tuple[bool, Optional[Path], Optional[str], Optional[SourceType]]:
    """
    Try to download PDF from multiple sources given a DOI.

    Tries sources in order:
    1. Unpaywall (if client provided)
    2. CORE (if client provided)
    3. bioRxiv (if DOI starts with 10.1101)

    Args:
        doi: Article DOI
        unpaywall_client: Optional UnpaywallClient instance
        core_client: Optional COREClient instance
        cache_dir: Cache directory

    Returns:
        Tuple of (success, pdf_path, error_message, source)
    """
    downloader = PDFDownloader(cache_dir=cache_dir)

    # Try Unpaywall
    if unpaywall_client:
        try:
            oa_info = await unpaywall_client.get_oa_location(doi)
            if oa_info and oa_info.get("best_oa_location"):
                success, pdf_path, error = await downloader.download_from_unpaywall(
                    doi, oa_info["best_oa_location"]
                )
                if success:
                    return True, pdf_path, None, SourceType.UNPAYWALL
        except Exception as e:
            logger.debug(f"Unpaywall failed for {doi}: {e}")

    # Try CORE
    if core_client:
        try:
            results = await core_client.search_by_doi(doi)
            if results and len(results) > 0:
                article = results[0]
                if "downloadUrl" in article:
                    success, pdf_path, error = await downloader.download_from_core(
                        article.get("id", doi), article["downloadUrl"]
                    )
                    if success:
                        return True, pdf_path, None, SourceType.CORE
        except Exception as e:
            logger.debug(f"CORE failed for {doi}: {e}")

    # Try bioRxiv (if applicable)
    if doi.startswith("10.1101/"):
        success, pdf_path, error = await downloader.download_from_biorxiv(doi)
        if success:
            return True, pdf_path, None, SourceType.BIORXIV

    return False, None, "No PDF available from any source", None
