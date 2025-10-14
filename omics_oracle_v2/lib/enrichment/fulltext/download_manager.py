"""
PDF Download Manager

Async PDF downloader with validation, retry logic, and progress tracking.
Supports parallel downloads with rate limiting.
"""

import asyncio
import logging
import ssl
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import aiofiles
import aiohttp

from omics_oracle_v2.lib.enrichment.identifiers import UniversalIdentifier
from omics_oracle_v2.lib.search_engines.citations.models import Publication

logger = logging.getLogger(__name__)


@dataclass
class DownloadResult:
    """Result of a single PDF download"""

    publication: Publication
    success: bool
    pdf_path: Optional[Path] = None
    error: Optional[str] = None
    source: Optional[str] = None  # Which URL source was used
    file_size: int = 0


@dataclass
class DownloadReport:
    """Summary of batch download operation"""

    total: int
    successful: int
    failed: int
    results: List[DownloadResult] = field(default_factory=list)
    total_size_mb: float = 0.0

    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        return self.successful / self.total if self.total > 0 else 0.0


class PDFDownloadManager:
    """
    Manage async PDF downloads with validation and retry.

    Features:
    - Parallel downloads (configurable concurrency)
    - Rate limiting
    - PDF validation (magic bytes check)
    - Retry logic
    - Progress tracking
    """

    # PDF magic bytes (starts with %PDF-)
    PDF_MAGIC_BYTES = b"%PDF-"

    def __init__(
        self,
        max_concurrent: int = 5,
        max_retries: int = 3,
        timeout_seconds: int = 30,
        validate_pdf: bool = True,
    ):
        self.max_concurrent = max_concurrent
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds
        self.validate_pdf = validate_pdf
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def download_batch(
        self,
        publications: List[Publication],
        output_dir: Path,
        url_field: str = "fulltext_url",  # Which field has the PDF URL
    ) -> DownloadReport:
        """
        DEPRECATED: Use download_with_fallback() instead.

        This method only tries ONE URL per publication (from url_field) and was
        causing 70% of downloads to fail unnecessarily. The correct approach is to:

        1. Collect ALL URLs: result = await fulltext_manager.get_all_fulltext_urls(pub)
        2. Try with fallback: await download_manager.download_with_fallback(pub, result.all_urls, output_dir)

        See: docs/WATERFALL_FIX_COMPLETE.md for details.

        Deprecated: October 13, 2025
        Will be removed in: v3.0.0

        Args:
            publications: List of publications with PDF URLs
            output_dir: Directory to save PDFs
            url_field: Which publication attribute contains the PDF URL

        Returns:
            DownloadReport with results
        """
        import warnings

        warnings.warn(
            "download_batch() is deprecated and only tries ONE URL per publication. "
            "Use get_all_fulltext_urls() + download_with_fallback() for maximum success rate. "
            "See docs/WATERFALL_FIX_COMPLETE.md",
            DeprecationWarning,
            stacklevel=2,
        )
        output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Starting batch download of {len(publications)} PDFs")
        logger.info(f"Max concurrent: {self.max_concurrent}")
        logger.info(f"Output directory: {output_dir}")

        # Create download tasks
        tasks = []
        for pub in publications:
            url = getattr(pub, url_field, None)
            if url:
                tasks.append(self._download_with_retry(pub, url, output_dir))
            else:
                logger.warning(f"No URL for {pub.title[:50]}...")

        # Execute downloads concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        download_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Download task failed: {result}")
                continue
            download_results.append(result)

        # Generate report
        successful = sum(1 for r in download_results if r.success)
        failed = len(download_results) - successful
        total_bytes = sum(r.file_size for r in download_results if r.success)

        report = DownloadReport(
            total=len(publications),
            successful=successful,
            failed=failed,
            results=download_results,
            total_size_mb=total_bytes / (1024 * 1024),
        )

        logger.info(f"✓ Download complete: {successful}/{len(publications)} successful")
        logger.info(f"  Total size: {report.total_size_mb:.2f} MB")

        return report

    async def _download_with_retry(
        self, publication: Publication, url: str, output_dir: Path
    ) -> DownloadResult:
        """Download a single PDF with retry logic"""
        for attempt in range(self.max_retries):
            try:
                result = await self._download_single(publication, url, output_dir)
                if result.success:
                    return result
                logger.warning(f"Attempt {attempt + 1} failed: {result.error}")
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} exception: {e}")

            if attempt < self.max_retries - 1:
                await asyncio.sleep(2**attempt)  # Exponential backoff

        # All retries failed
        return DownloadResult(
            publication=publication, success=False, error=f"Failed after {self.max_retries} attempts"
        )

    async def _download_single(self, publication: Publication, url: str, output_dir: Path) -> DownloadResult:
        """
        Download a single PDF with User-Agent headers and redirect handling.

        CHROME COOKIES INTEGRATION:
        Automatically tries to use Chrome browser cookies for authenticated access.
        This allows downloading from publisher sites where you're logged in.

        Fallback order:
        1. Try with Chrome cookies (if available)
        2. Try without cookies (public access)
        """
        async with self.semaphore:  # Rate limiting
            try:
                # Generate filename
                filename = self._generate_filename(publication)
                pdf_path = output_dir / filename

                # Download with SSL context that doesn't verify certificates
                # (needed for some academic publishers with cert issues)
                timeout = aiohttp.ClientTimeout(total=self.timeout_seconds)
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE

                # User-Agent headers to avoid bot detection
                headers = {
                    "User-Agent": "Mozilla/5.0 (compatible; OmicsOracle/2.0; Academic Research Tool; +https://github.com/omicsoracle/omicsoracle)",
                    "Accept": "application/pdf,*/*",
                }

                # Chrome cookies disabled - causing HTTP 400 errors when sent to wrong domains
                # TODO: Fix cookie domain filtering to enable Shibboleth support
                cookie_jar = None

                connector = aiohttp.TCPConnector(ssl=ssl_context)
                async with aiohttp.ClientSession(
                    timeout=timeout, connector=connector, headers=headers, cookie_jar=cookie_jar
                ) as session:
                    # Follow redirects (important for DOI links)
                    async with session.get(url, allow_redirects=True, max_redirects=10) as response:
                        if response.status != 200:
                            return DownloadResult(
                                publication=publication,
                                success=False,
                                error=f"HTTP {response.status} from {response.url}",
                            )

                        content = await response.read()

                        # Log final URL if redirected
                        final_url = str(response.url)
                        if final_url != url:
                            logger.debug(f"Redirected: {url} -> {final_url}")

                    # Validate PDF (still inside session context!)
                    if self.validate_pdf and not self._is_valid_pdf(content):
                        # If we got HTML instead of PDF, try to extract PDF link from landing page
                        if content.startswith(b"<!DOCTYPE") or content.startswith(b"<html"):
                            logger.info(f"Received HTML landing page, attempting to extract PDF URL...")

                            from .landing_page_parser import get_parser

                            parser = get_parser()

                            try:
                                html = content.decode("utf-8", errors="ignore")
                                pdf_url = parser.extract_pdf_url(html, final_url)

                                if pdf_url:
                                    logger.info(f"Found PDF URL in landing page: {pdf_url}")
                                    # Retry download with the extracted PDF URL (session still open!)
                                    async with session.get(
                                        pdf_url, allow_redirects=True, max_redirects=10
                                    ) as pdf_response:
                                        if pdf_response.status == 200:
                                            content = await pdf_response.read()

                                            # Validate the new content is actually a PDF
                                            if self._is_valid_pdf(content):
                                                logger.info(
                                                    f"✓ Successfully downloaded PDF via landing page extraction"
                                                )
                                            else:
                                                return DownloadResult(
                                                    publication=publication,
                                                    success=False,
                                                    error=f"Extracted URL {pdf_url} also returned invalid PDF",
                                                )
                                        else:
                                            return DownloadResult(
                                                publication=publication,
                                                success=False,
                                                error=f"HTTP {pdf_response.status} from extracted URL {pdf_url}",
                                            )
                                else:
                                    return DownloadResult(
                                        publication=publication,
                                        success=False,
                                        error="Received HTML landing page, no PDF link found",
                                    )
                            except Exception as e:
                                logger.warning(f"Landing page parsing failed: {e}")
                                return DownloadResult(
                                    publication=publication,
                                    success=False,
                                    error=f"Invalid PDF (landing page parsing failed: {e})",
                                )
                        else:
                            return DownloadResult(
                                publication=publication,
                                success=False,
                                error="Invalid PDF (magic bytes check failed)",
                            )
                # Session context ends here - now it's safe to proceed

                # Save to disk
                async with aiofiles.open(pdf_path, "wb") as f:
                    await f.write(content)

                logger.info(f"✓ Downloaded: {filename} ({len(content) / 1024:.1f} KB)")

                return DownloadResult(
                    publication=publication,
                    success=True,
                    pdf_path=pdf_path,
                    source=url,
                    file_size=len(content),
                )

            except asyncio.TimeoutError:
                return DownloadResult(publication=publication, success=False, error="Timeout")
            except Exception as e:
                return DownloadResult(publication=publication, success=False, error=str(e))

    def _generate_filename(self, publication: Publication) -> str:
        """
        Generate unique filename for PDF using UniversalIdentifier.

        NEW (Oct 13, 2025):
        - Uses hierarchical identifier fallback: PMID → DOI → PMC → arXiv → Hash
        - Works for all 11 full-text sources (not just PMID-based ones)
        - Filesystem-safe filenames (DOI slashes converted to underscores)
        - Deterministic (same paper = same filename)

        Returns:
            Filename like "pmid_12345.pdf", "doi_10_1234__abc.pdf", etc.

        Examples:
            >>> pub = Publication(pmid="12345", doi="10.1234/abc")
            >>> filename = self._generate_filename(pub)
            >>> print(filename)  # "pmid_12345.pdf"

            >>> pub = Publication(doi="10.1234/abc")  # No PMID
            >>> filename = self._generate_filename(pub)
            >>> print(filename)  # "doi_10_1234__abc.pdf"
        """
        identifier = UniversalIdentifier(publication)
        return identifier.filename

    def _is_valid_pdf(self, content: bytes) -> bool:
        """Validate PDF using magic bytes"""
        return content.startswith(self.PDF_MAGIC_BYTES)

    async def download_with_fallback(
        self,
        publication: Publication,
        all_urls: List,  # List of SourceURL objects
        output_dir: Path,
    ) -> DownloadResult:
        """
        Download PDF with automatic fallback through multiple URLs.

        NEW (Oct 13, 2025):
        - Tries URLs in priority order (institutional > PMC > Unpaywall...)
        - Stops at first successful download
        - No need to re-query APIs (URLs already collected)
        - Logs which source succeeded

        Args:
            publication: Publication object
            all_urls: List of SourceURL objects from FullTextManager
            output_dir: Directory to save PDF

        Returns:
            DownloadResult with success status

        Example:
            >>> # Get all URLs first
            >>> result = await fulltext_manager.get_all_fulltext_urls(pub)
            >>>
            >>> # Try downloading with fallback
            >>> download_result = await pdf_downloader.download_with_fallback(
            >>>     pub, result.all_urls, output_dir
            >>> )
            >>>
            >>> if download_result.success:
            >>>     print(f"Downloaded from {download_result.source}")
        """
        if not all_urls:
            return DownloadResult(publication=publication, success=False, error="No URLs provided")

        output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Trying {len(all_urls)} URLs for: {publication.title[:50]}...")

        # NEW: Retry configuration
        max_retries_per_url = 2  # Retry each URL up to 2 times
        retry_delay = 1.5  # Seconds to wait between retries

        # Try each URL in priority order
        for i, source_url in enumerate(all_urls):
            source_name = source_url.source.value
            priority = source_url.priority
            url = source_url.url

            logger.info(
                f"  [{i+1}/{len(all_urls)}] Trying {source_name} " f"(priority {priority}): {url[:80]}..."
            )

            # NEW: Retry logic for each URL
            for attempt in range(max_retries_per_url):
                try:
                    # Attempt download
                    result = await self._download_single(publication, url, output_dir)

                    if result.success and result.pdf_path:
                        # SUCCESS! Return immediately
                        result.source = source_name
                        retry_msg = f" (attempt {attempt + 1}/{max_retries_per_url})" if attempt > 0 else ""
                        logger.info(
                            f"  ✅ SUCCESS from {source_name}{retry_msg}! "
                            f"Size: {result.file_size / 1024:.1f} KB, "
                            f"Path: {result.pdf_path.name}"
                        )
                        return result
                    else:
                        # Failed this attempt
                        if attempt < max_retries_per_url - 1:
                            logger.warning(
                                f"  ⚠️  {source_name} attempt {attempt + 1}/{max_retries_per_url} failed: {result.error}"
                            )
                            logger.info(f"     Retrying in {retry_delay}s...")
                            await asyncio.sleep(retry_delay)
                        else:
                            # All retries exhausted for this URL
                            logger.debug(
                                f"  ✗ {source_name} failed after {max_retries_per_url} attempts: {result.error}"
                            )

                except Exception as e:
                    if attempt < max_retries_per_url - 1:
                        logger.warning(
                            f"  ⚠️  {source_name} attempt {attempt + 1}/{max_retries_per_url} exception: {e}"
                        )
                        logger.info(f"     Retrying in {retry_delay}s...")
                        await asyncio.sleep(retry_delay)
                    else:
                        logger.debug(f"  ✗ {source_name} exception after {max_retries_per_url} attempts: {e}")
                    continue

            # All retries exhausted for this URL, try next URL

        # All URLs failed
        logger.warning(f"❌ All {len(all_urls)} URLs failed for: {publication.title[:50]}")

        return DownloadResult(
            publication=publication, success=False, error=f"All {len(all_urls)} sources failed", source="none"
        )
