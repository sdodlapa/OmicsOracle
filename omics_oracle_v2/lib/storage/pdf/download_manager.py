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

from omics_oracle_v2.lib.publications.models import Publication

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
        Download PDFs for a batch of publications.

        Args:
            publications: List of publications with PDF URLs
            output_dir: Directory to save PDFs
            url_field: Which publication attribute contains the PDF URL

        Returns:
            DownloadReport with results
        """
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
        """Generate unique filename for PDF"""
        if publication.pmid:
            return f"PMID_{publication.pmid}.pdf"
        elif publication.doi:
            # Clean DOI for filename
            clean_doi = publication.doi.replace("/", "_").replace("\\", "_")
            return f"DOI_{clean_doi}.pdf"
        else:
            # Fallback to hash of title
            import hashlib

            title_hash = hashlib.md5(publication.title.encode()).hexdigest()[:12]
            return f"paper_{title_hash}.pdf"

    def _is_valid_pdf(self, content: bytes) -> bool:
        """Validate PDF using magic bytes"""
        return content.startswith(self.PDF_MAGIC_BYTES)
