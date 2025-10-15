"""
⚠️⚠️⚠️ DEPRECATED - DO NOT USE THIS FILE! ⚠️⚠️⚠️

This file has been DEPRECATED and replaced by PDFDownloadManager.

❌ OLD (BROKEN): omics_oracle_v2/lib/fulltext/download_utils.py
✅ NEW (WORKING): omics_oracle_v2/lib/storage/pdf/download_manager.py

REASON FOR DEPRECATION:
----------------------
1. Simple wrapper with no validation
2. Downloads HTML pages for DOI redirects (broken for institutional access)
3. No retry logic
4. No proper error handling
5. Redundant with PDFDownloadManager

MIGRATION:
---------
Instead of:
    from omics_oracle_v2.lib.enrichment.fulltext.download_utils import download_and_save_pdf
    saved_path = await download_and_save_pdf(url, publication, source)

Use:
    from omics_oracle_v2.lib.enrichment.fulltext.download_manager import PDFDownloadManager

    pdf_downloader = PDFDownloadManager(validate_pdf=True)
    download_report = await pdf_downloader.download_batch(
        publications=[publication],
        output_dir=Path("data/pdfs"),
        url_field="fulltext_url"
    )

DEPRECATED: October 12, 2025
ARCHIVED TO: omics_oracle_v2/lib/archive/deprecated_20251012/
REPLACED BY: PDFDownloadManager
SEE: docs/analysis/PDF_DOWNLOAD_REDUNDANCY_AUDIT.md

⚠️⚠️⚠️ DO NOT USE THIS FILE! ⚠️⚠️⚠️
"""

# Original implementation below (for historical reference only)
# -----------------------------------------------------------------

"""
Utility functions for downloading and saving full-text files.

This module provides helper functions to download PDFs/XMLs from URLs
and save them to appropriate source-specific directories using SmartCache.

Author: OmicsOracle Team
Date: October 11, 2025
"""

import logging
import os
import ssl
from pathlib import Path
from typing import Optional

import aiohttp

from omics_oracle_v2.lib.enrichment.fulltext.smart_cache import SmartCache

logger = logging.getLogger(__name__)


async def download_file(url: str, timeout: int = 30) -> Optional[bytes]:
    """
    Download file from URL with SSL bypass support for institutional networks.

    Args:
        url: URL to download from
        timeout: Timeout in seconds

    Returns:
        File content as bytes, or None if download failed

    Example:
        >>> content = await download_file("https://arxiv.org/pdf/2301.12345.pdf")
        >>> if content:
        >>>     print(f"Downloaded {len(content)} bytes")
    """
    try:
        # Create SSL context that bypasses verification if needed (institutional networks)
        ssl_context = None
        if os.getenv("PYTHONHTTPSVERIFY", "1") == "0":
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            logger.debug("SSL verification disabled for download")

        connector = aiohttp.TCPConnector(ssl=ssl_context) if ssl_context else None
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(
                url, timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                if response.status == 200:
                    content = await response.read()
                    logger.debug(f"Downloaded {len(content)} bytes from {url}")
                    return content
                else:
                    logger.warning(
                        f"Download failed: HTTP {response.status} from {url}"
                    )
                    return None
    except aiohttp.ClientError as e:
        logger.warning(f"Download error from {url}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error downloading from {url}: {e}")
        return None


async def download_and_save_pdf(
    url: str,
    publication,
    source: str,
    cache: Optional[SmartCache] = None,
    timeout: int = 30,
) -> Optional[Path]:
    """
    Download PDF from URL and save to source-specific directory.

    This is a convenience function that combines downloading and saving
    in one operation. It uses SmartCache to determine the appropriate
    storage location based on the source.

    Args:
        url: URL to download PDF from
        publication: Publication object with identifiers
        source: Source identifier ('arxiv', 'pmc', 'institutional', 'scihub', etc.)
        cache: SmartCache instance (creates new one if not provided)
        timeout: Download timeout in seconds

    Returns:
        Path where PDF was saved, or None if download failed

    Example:
        >>> pdf_path = await download_and_save_pdf(
        ...     url="https://arxiv.org/pdf/2301.12345.pdf",
        ...     publication=publication,
        ...     source='arxiv'
        ... )
        >>> if pdf_path:
        ...     print(f"Saved to: {pdf_path}")
    """
    # Download file
    content = await download_file(url, timeout=timeout)

    if not content:
        logger.warning(f"Failed to download PDF from {url}")
        return None

    # Validate it's a PDF (simple check)
    if not content.startswith(b"%PDF"):
        logger.warning(f"Downloaded content from {url} doesn't appear to be a PDF")
        # Still save it, might be useful for debugging

    # Save to cache
    if cache is None:
        cache = SmartCache()

    try:
        saved_path = cache.save_file(
            content=content, publication=publication, source=source, file_type="pdf"
        )

        logger.info(
            f"✓ Downloaded and saved PDF: {source}/{saved_path.name} ({len(content) // 1024} KB)"
        )
        return saved_path

    except Exception as e:
        logger.error(f"Error saving PDF from {url}: {e}")
        return None


async def download_and_save_xml(
    url: str,
    publication,
    source: str,
    cache: Optional[SmartCache] = None,
    timeout: int = 30,
) -> Optional[Path]:
    """
    Download XML from URL and save to source-specific directory.

    Similar to download_and_save_pdf but for XML/NXML files.

    Args:
        url: URL to download XML from
        publication: Publication object with identifiers
        source: Source identifier (e.g., 'pmc', 'biorxiv')
        cache: SmartCache instance (creates new one if not provided)
        timeout: Download timeout in seconds

    Returns:
        Path where XML was saved, or None if download failed

    Example:
        >>> xml_path = await download_and_save_xml(
        ...     url="https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9876543/xml/",
        ...     publication=publication,
        ...     source='pmc'
        ... )
    """
    # Download file
    content = await download_file(url, timeout=timeout)

    if not content:
        logger.warning(f"Failed to download XML from {url}")
        return None

    # Validate it's XML (simple check)
    if not (content.startswith(b"<?xml") or content.startswith(b"<article")):
        logger.warning(f"Downloaded content from {url} doesn't appear to be XML")
        # Still save it, might be useful for debugging

    # Determine file extension
    file_type = "nxml" if source == "pmc" else "xml"

    # Save to cache
    if cache is None:
        cache = SmartCache()

    try:
        saved_path = cache.save_file(
            content=content, publication=publication, source=source, file_type=file_type
        )

        logger.info(
            f"✓ Downloaded and saved XML: {source}/{saved_path.name} ({len(content) // 1024} KB)"
        )
        return saved_path

    except Exception as e:
        logger.error(f"Error saving XML from {url}: {e}")
        return None


def get_cache_instance() -> SmartCache:
    """
    Get a SmartCache instance.

    This is a convenience function to avoid importing SmartCache
    directly in every source method.

    Returns:
        SmartCache instance
    """
    return SmartCache()
