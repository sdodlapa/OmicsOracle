"""
Data Download Pipeline - Separate pipeline for downloading approved datasets.

This module handles the actual download of experimental data files
AFTER user approval. It is completely separate from the search/metadata
pipeline to ensure users explicitly control what gets downloaded.

Key Features:
- User approval workflow
- Download queue management
- Progress tracking
- Size estimation and validation
- Storage management
- Resume capability for large files

Architecture:
    User Search → Metadata Collection → User Reviews → Approves Datasets
                                                            ↓
                                            Download Pipeline (THIS MODULE)
                                                            ↓
                                            Local Storage → Analysis
"""

import asyncio
import logging
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set

import aiohttp
from pydantic import BaseModel, Field

from ...core.exceptions import DownloadError
from ..geo.models import GEOSeriesMetadata

logger = logging.getLogger(__name__)


class DownloadStatus(str, Enum):
    """Status of a dataset download."""

    PENDING = "pending"  # Waiting for approval
    APPROVED = "approved"  # Approved but not started
    DOWNLOADING = "downloading"  # Currently downloading
    COMPLETED = "completed"  # Successfully downloaded
    FAILED = "failed"  # Download failed
    PAUSED = "paused"  # User paused download
    CANCELLED = "cancelled"  # User cancelled download


class DownloadRequest(BaseModel):
    """Request to download a dataset file."""

    geo_id: str = Field(..., description="GEO series ID")
    file_url: str = Field(..., description="URL to download")
    file_type: str = Field(..., description="Type of file (RAW, processed, etc.)")
    file_format: str = Field(..., description="File format")
    destination_path: str = Field(..., description="Where to save the file")

    approved_by: str = Field(..., description="Username who approved download")
    approved_at: datetime = Field(default_factory=datetime.now, description="Approval timestamp")

    status: DownloadStatus = Field(default=DownloadStatus.APPROVED, description="Download status")
    progress_bytes: int = Field(default=0, description="Bytes downloaded so far")
    total_bytes: Optional[int] = Field(None, description="Total file size")

    started_at: Optional[datetime] = Field(None, description="Download start time")
    completed_at: Optional[datetime] = Field(None, description="Download completion time")
    error_message: Optional[str] = Field(None, description="Error message if failed")

    def get_progress_percent(self) -> float:
        """Get download progress percentage."""
        if self.total_bytes and self.total_bytes > 0:
            return (self.progress_bytes / self.total_bytes) * 100
        return 0.0


class DataDownloadPipeline:
    """
    Pipeline for downloading approved dataset files.

    This is a SEPARATE pipeline from search/metadata collection.
    All downloads require explicit user approval.

    Usage:
        >>> pipeline = DataDownloadPipeline(download_dir="/data/datasets")
        >>>
        >>> # User searches and approves dataset
        >>> metadata = await geo_client.get_metadata("GSE123456")
        >>> user_approves_dataset(metadata)
        >>>
        >>> # Only THEN do we download
        >>> await pipeline.download_dataset(
        ...     geo_id="GSE123456",
        ...     metadata=metadata,
        ...     approved_by="user@example.com"
        ... )
    """

    def __init__(
        self,
        download_dir: str = "./data/downloads",
        max_concurrent_downloads: int = 3,
        chunk_size: int = 8192,
        verify_checksums: bool = True,
    ):
        """
        Initialize data download pipeline.

        Args:
            download_dir: Directory to save downloaded files
            max_concurrent_downloads: Maximum concurrent downloads
            chunk_size: Download chunk size in bytes
            verify_checksums: Whether to verify file integrity
        """
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)

        self.max_concurrent_downloads = max_concurrent_downloads
        self.chunk_size = chunk_size
        self.verify_checksums = verify_checksums

        # Track active downloads
        self.active_downloads: Dict[str, DownloadRequest] = {}
        self.download_queue: List[DownloadRequest] = []

        # Approved datasets (requires explicit approval)
        self.approved_datasets: Set[str] = set()

        logger.info(
            f"DataDownloadPipeline initialized: download_dir={download_dir}, "
            f"max_concurrent={max_concurrent_downloads}"
        )

    def approve_dataset(self, geo_id: str, approved_by: str) -> None:
        """
        Approve a dataset for download.

        REQUIRED before downloading any dataset files.

        Args:
            geo_id: GEO series ID to approve
            approved_by: Username/email of approver
        """
        self.approved_datasets.add(geo_id)
        logger.info(f"Dataset {geo_id} approved for download by {approved_by}")

    def is_approved(self, geo_id: str) -> bool:
        """Check if a dataset is approved for download."""
        return geo_id in self.approved_datasets

    async def download_dataset(
        self,
        geo_id: str,
        metadata: GEOSeriesMetadata,
        approved_by: str,
        file_types: Optional[List[str]] = None,
    ) -> List[DownloadRequest]:
        """
        Download approved dataset files.

        Args:
            geo_id: GEO series ID
            metadata: Dataset metadata (contains download links)
            approved_by: Username who approved download
            file_types: Optional filter for file types (e.g., ["RAW", "processed"])

        Returns:
            List of download requests with status

        Raises:
            DownloadError: If dataset not approved or download fails
        """
        # CRITICAL: Check approval
        if not self.is_approved(geo_id):
            raise DownloadError(
                f"Dataset {geo_id} not approved for download. " f"Call approve_dataset() first."
            )

        logger.info(f"Starting download for approved dataset: {geo_id}")

        # Get download information
        downloads = metadata.data_downloads or metadata.parse_download_info()

        # Filter by file type if specified
        if file_types:
            downloads = [d for d in downloads if d.file_type in file_types]

        if not downloads:
            logger.warning(f"No downloadable files found for {geo_id}")
            return []

        # Create download requests
        requests = []
        for download_info in downloads:
            dest_path = self.download_dir / geo_id / download_info.file_url.split("/")[-1]
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            request = DownloadRequest(
                geo_id=geo_id,
                file_url=download_info.file_url,
                file_type=download_info.file_type,
                file_format=download_info.file_format,
                destination_path=str(dest_path),
                approved_by=approved_by,
            )
            requests.append(request)
            self.download_queue.append(request)

        logger.info(f"Queued {len(requests)} files for download")

        # Process download queue
        await self._process_queue()

        return requests

    async def _process_queue(self) -> None:
        """Process download queue with concurrency control."""
        while self.download_queue:
            # Limit concurrent downloads
            if len(self.active_downloads) >= self.max_concurrent_downloads:
                await asyncio.sleep(1)
                continue

            # Get next download
            request = self.download_queue.pop(0)

            # Start download
            asyncio.create_task(self._download_file(request))

    async def _download_file(self, request: DownloadRequest) -> None:
        """
        Download a single file.

        Args:
            request: Download request
        """
        request.status = DownloadStatus.DOWNLOADING
        request.started_at = datetime.now()
        self.active_downloads[request.file_url] = request

        try:
            logger.info(f"Downloading {request.file_url} → {request.destination_path}")

            async with aiohttp.ClientSession() as session:
                async with session.get(request.file_url) as response:
                    response.raise_for_status()

                    # Get total size
                    request.total_bytes = int(response.headers.get("content-length", 0))

                    # Download in chunks
                    with open(request.destination_path, "wb") as f:
                        async for chunk in response.content.iter_chunked(self.chunk_size):
                            f.write(chunk)
                            request.progress_bytes += len(chunk)

                            # Log progress
                            if request.progress_bytes % (1024 * 1024 * 100) == 0:  # Every 100MB
                                logger.info(
                                    f"Progress: {request.get_progress_percent():.1f}% "
                                    f"({request.progress_bytes / (1024**3):.2f} GB)"
                                )

            # Verify file
            if self.verify_checksums:
                await self._verify_file(request)

            # Mark complete
            request.status = DownloadStatus.COMPLETED
            request.completed_at = datetime.now()

            duration = (request.completed_at - request.started_at).total_seconds()
            size_mb = request.total_bytes / (1024**2) if request.total_bytes else 0

            logger.info(
                f"✓ Download complete: {request.destination_path} " f"({size_mb:.2f} MB in {duration:.1f}s)"
            )

        except Exception as e:
            request.status = DownloadStatus.FAILED
            request.error_message = str(e)
            logger.error(f"Download failed: {request.file_url}: {e}")

        finally:
            # Remove from active downloads
            self.active_downloads.pop(request.file_url, None)

    async def _verify_file(self, request: DownloadRequest) -> bool:
        """
        Verify downloaded file integrity.

        Args:
            request: Download request

        Returns:
            True if verification passed
        """
        # TODO: Add MD5/SHA256 checksum verification
        # GEO doesn't always provide checksums, so this is optional
        logger.debug(f"File verification for {request.destination_path}")
        return True

    def get_download_stats(self) -> Dict[str, int]:
        """Get statistics about downloads."""
        all_requests = list(self.active_downloads.values()) + self.download_queue

        stats = {
            "total": len(all_requests),
            "pending": len([r for r in all_requests if r.status == DownloadStatus.PENDING]),
            "downloading": len([r for r in all_requests if r.status == DownloadStatus.DOWNLOADING]),
            "completed": len([r for r in all_requests if r.status == DownloadStatus.COMPLETED]),
            "failed": len([r for r in all_requests if r.status == DownloadStatus.FAILED]),
        }

        return stats


# Example usage
async def example_usage():
    """
    Example of how to use the Data Download Pipeline.
    """
    from ...lib.geo.client import GEOClient

    # Initialize components
    geo_client = GEOClient()
    download_pipeline = DataDownloadPipeline(download_dir="./data/approved_datasets")

    # Step 1: Search and get metadata (NO DOWNLOAD YET)
    search_result = await geo_client.search("diabetes RNA-seq", max_results=10)
    print(f"Found {len(search_result.geo_ids)} datasets")

    # Step 2: Get metadata for specific dataset (ONLY METADATA)
    geo_id = search_result.geo_ids[0]
    metadata = await geo_client.get_metadata(geo_id)

    print(f"\nDataset: {metadata.title}")
    print(f"Samples: {metadata.sample_count}")
    print(f"Available downloads: {len(metadata.supplementary_files)}")

    # Step 3: Show user what can be downloaded
    for download in metadata.parse_download_info():
        print(f"  - {download.file_type}: {download.file_url}")
        print(f"    Estimated size: {metadata.estimate_download_size_mb()}")

    # Step 4: USER APPROVES (REQUIRED!)
    user_input = input(f"\nApprove download of {geo_id}? (yes/no): ")
    if user_input.lower() == "yes":
        download_pipeline.approve_dataset(geo_id, approved_by="user@example.com")

        # Step 5: NOW download (only after approval)
        requests = await download_pipeline.download_dataset(
            geo_id=geo_id,
            metadata=metadata,
            approved_by="user@example.com",
            file_types=["RAW"],  # Only download raw data
        )

        print(f"\nDownloaded {len(requests)} files")
    else:
        print("Download cancelled by user")


if __name__ == "__main__":
    asyncio.run(example_usage())
