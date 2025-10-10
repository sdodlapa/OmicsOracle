"""
PDF Download Manager

Async PDF downloader with validation, retry logic, and progress tracking.
Supports parallel downloads with rate limiting.
"""

import asyncio
import logging
from pathlib import Path
from typing import List, Optional, Dict
from dataclasses import dataclass, field
import aiohttp
import aiofiles

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
    PDF_MAGIC_BYTES = b'%PDF-'
    
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
        url_field: str = "fulltext_url"  # Which field has the PDF URL
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
            total_size_mb=total_bytes / (1024 * 1024)
        )
        
        logger.info(f"✓ Download complete: {successful}/{len(publications)} successful")
        logger.info(f"  Total size: {report.total_size_mb:.2f} MB")
        
        return report
    
    async def _download_with_retry(
        self,
        publication: Publication,
        url: str,
        output_dir: Path
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
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        # All retries failed
        return DownloadResult(
            publication=publication,
            success=False,
            error=f"Failed after {self.max_retries} attempts"
        )
    
    async def _download_single(
        self,
        publication: Publication,
        url: str,
        output_dir: Path
    ) -> DownloadResult:
        """Download a single PDF"""
        async with self.semaphore:  # Rate limiting
            try:
                # Generate filename
                filename = self._generate_filename(publication)
                pdf_path = output_dir / filename
                
                # Download
                timeout = aiohttp.ClientTimeout(total=self.timeout_seconds)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(url) as response:
                        if response.status != 200:
                            return DownloadResult(
                                publication=publication,
                                success=False,
                                error=f"HTTP {response.status}"
                            )
                        
                        content = await response.read()
                
                # Validate PDF
                if self.validate_pdf and not self._is_valid_pdf(content):
                    return DownloadResult(
                        publication=publication,
                        success=False,
                        error="Invalid PDF (magic bytes check failed)"
                    )
                
                # Save to disk
                async with aiofiles.open(pdf_path, 'wb') as f:
                    await f.write(content)
                
                logger.info(f"✓ Downloaded: {filename} ({len(content) / 1024:.1f} KB)")
                
                return DownloadResult(
                    publication=publication,
                    success=True,
                    pdf_path=pdf_path,
                    source=url,
                    file_size=len(content)
                )
                
            except asyncio.TimeoutError:
                return DownloadResult(
                    publication=publication,
                    success=False,
                    error="Timeout"
                )
            except Exception as e:
                return DownloadResult(
                    publication=publication,
                    success=False,
                    error=str(e)
                )
    
    def _generate_filename(self, publication: Publication) -> str:
        """Generate unique filename for PDF"""
        if publication.pmid:
            return f"PMID_{publication.pmid}.pdf"
        elif publication.doi:
            # Clean DOI for filename
            clean_doi = publication.doi.replace('/', '_').replace('\\', '_')
            return f"DOI_{clean_doi}.pdf"
        else:
            # Fallback to hash of title
            import hashlib
            title_hash = hashlib.md5(publication.title.encode()).hexdigest()[:12]
            return f"paper_{title_hash}.pdf"
    
    def _is_valid_pdf(self, content: bytes) -> bool:
        """Validate PDF using magic bytes"""
        return content.startswith(self.PDF_MAGIC_BYTES)
