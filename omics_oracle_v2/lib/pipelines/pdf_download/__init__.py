"""
PDF Download Pipeline

This pipeline is responsible for downloading PDFs from URLs and validating them.
It implements a waterfall strategy with multiple fallback URLs.

Features:
- Concurrent batch downloads
- Waterfall retry with multiple URLs per publication
- Smart cache checking (avoid re-downloading)
- PDF validation (magic bytes, size, corruption)
- Landing page parsing (extract PDF links from HTML)

Integration Contract:
- Input: Publication with fulltext_url or list of SourceURLs
- Output: DownloadResult with path to validated PDF

Usage:
    >>> from omics_oracle_v2.lib.pipelines.pdf_download import PDFDownloadManager
    >>>
    >>> downloader = PDFDownloadManager()
    >>> result = await downloader.download_with_fallback(publication, urls)
    >>> if result.success:
    >>>     print(f"Downloaded: {result.file_path}")

Author: OmicsOracle Team
Created: October 14, 2025 (Pipeline Separation)
"""

from omics_oracle_v2.cache.smart_cache import LocalFileResult, SmartCache
from omics_oracle_v2.lib.pipelines.pdf_download.download_manager import (
    DownloadReport, DownloadResult, PDFDownloadManager)
from omics_oracle_v2.lib.pipelines.pdf_download.landing_page_parser import \
    LandingPageParser
from omics_oracle_v2.lib.pipelines.pdf_download.utils import \
    validate_pdf_content

__all__ = [
    "PDFDownloadManager",
    "DownloadResult",
    "DownloadReport",
    "LandingPageParser",
    "SmartCache",
    "LocalFileResult",
    "validate_pdf_content",
]
