"""
Batch Text Enrichment Processor

Processes multiple PDFs in parallel with progress tracking and error handling.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from omics_oracle_v2.lib.pipelines.text_enrichment.pdf_parser import PDFExtractor

logger = logging.getLogger(__name__)


@dataclass
class BatchResult:
    """Result of batch processing."""

    total_pdfs: int = 0
    successful: int = 0
    failed: int = 0
    results: List[Dict] = field(default_factory=list)
    errors: Dict[str, str] = field(default_factory=dict)  # pdf_path -> error message
    processing_time: float = 0.0

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_pdfs == 0:
            return 0.0
        return (self.successful / self.total_pdfs) * 100


class BatchProcessor:
    """Batch process PDFs for text enrichment."""

    def __init__(
        self,
        max_concurrent: int = 10,
        enable_enrichment: bool = True,
        timeout_seconds: int = 120,
    ):
        """
        Initialize batch processor.

        Args:
            max_concurrent: Maximum concurrent PDF processing
            enable_enrichment: Whether to run enrichers
            timeout_seconds: Timeout per PDF
        """
        self.max_concurrent = max_concurrent
        self.enable_enrichment = enable_enrichment
        self.timeout_seconds = timeout_seconds
        self.extractor = PDFExtractor(enable_enrichment=enable_enrichment)

    async def process_batch(
        self,
        pdf_paths: List[Path],
        metadata_list: Optional[List[Dict]] = None,
        output_dir: Optional[Path] = None,
    ) -> BatchResult:
        """
        Process batch of PDFs.

        Args:
            pdf_paths: List of PDF paths to process
            metadata_list: Optional list of metadata dicts (one per PDF)
            output_dir: Optional directory to save enriched JSON files

        Returns:
            BatchResult with summary and individual results
        """
        import time

        start_time = time.time()

        result = BatchResult(total_pdfs=len(pdf_paths))

        # Create output directory if specified
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)

        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(self.max_concurrent)

        # Process PDFs concurrently
        tasks = []
        for i, pdf_path in enumerate(pdf_paths):
            metadata = metadata_list[i] if metadata_list and i < len(metadata_list) else None
            task = self._process_single_pdf(pdf_path, metadata, output_dir, semaphore)
            tasks.append(task)

        # Wait for all tasks
        individual_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Collect results
        for i, pdf_result in enumerate(individual_results):
            pdf_path = pdf_paths[i]

            if isinstance(pdf_result, Exception):
                result.failed += 1
                result.errors[str(pdf_path)] = str(pdf_result)
                logger.error(f"Failed to process {pdf_path}: {pdf_result}")
            elif pdf_result is None:
                result.failed += 1
                result.errors[str(pdf_path)] = "Extraction returned None"
            else:
                result.successful += 1
                result.results.append(
                    {
                        "pdf_path": str(pdf_path),
                        "enrichment": pdf_result,
                    }
                )

        result.processing_time = time.time() - start_time

        logger.info(
            f"Batch processing complete: {result.successful}/{result.total_pdfs} successful "
            f"({result.success_rate:.1f}%) in {result.processing_time:.1f}s"
        )

        return result

    async def _process_single_pdf(
        self,
        pdf_path: Path,
        metadata: Optional[Dict],
        output_dir: Optional[Path],
        semaphore: asyncio.Semaphore,
    ) -> Optional[Dict]:
        """Process a single PDF with timeout and error handling."""
        async with semaphore:
            try:
                # Run extraction with timeout
                enriched = await asyncio.wait_for(
                    self._extract_async(pdf_path, metadata),
                    timeout=self.timeout_seconds,
                )

                # Save to output directory if specified
                if output_dir and enriched:
                    output_file = output_dir / f"{pdf_path.stem}_enriched.json"
                    self._save_enriched_json(enriched, output_file)

                return enriched

            except asyncio.TimeoutError:
                logger.error(f"Timeout processing {pdf_path} (>{self.timeout_seconds}s)")
                raise
            except Exception as e:
                logger.error(f"Error processing {pdf_path}: {e}")
                raise

    async def _extract_async(self, pdf_path: Path, metadata: Optional[Dict]) -> Optional[Dict]:
        """
        Async wrapper for PDF extraction.

        Note: PDFExtractor is currently synchronous, so we run in executor.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.extractor.extract_text,
            pdf_path,
            metadata,
            None,  # context
        )

    def _save_enriched_json(self, enriched: Dict, output_file: Path):
        """Save enriched content to JSON file."""
        import json

        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(enriched, f, indent=2, ensure_ascii=False, default=str)
            logger.debug(f"Saved enriched content to {output_file}")
        except Exception as e:
            logger.error(f"Failed to save enriched JSON to {output_file}: {e}")


# Convenience function for quick batch processing
async def process_pdfs_batch(
    pdf_paths: List[Path],
    metadata_list: Optional[List[Dict]] = None,
    output_dir: Optional[Path] = None,
    max_concurrent: int = 10,
    enable_enrichment: bool = True,
) -> BatchResult:
    """
    Convenience function for batch PDF processing.

    Usage:
        >>> import asyncio
        >>> from pathlib import Path
        >>> pdfs = list(Path("data/pdfs").glob("*.pdf"))
        >>> result = asyncio.run(process_pdfs_batch(pdfs, max_concurrent=5))
        >>> print(f"Success rate: {result.success_rate:.1f}%")
    """
    processor = BatchProcessor(max_concurrent=max_concurrent, enable_enrichment=enable_enrichment)
    return await processor.process_batch(pdf_paths, metadata_list, output_dir)
