"""Full-text enrichment service for OmicsOracle.

IMPLEMENTATION HISTORY:
- Oct 15, 2025: Service created during refactoring (stub only)
- Oct 16, 2025: Complete implementation added to fix PDF download failures

This service implements the core business logic for the /enrich-fulltext endpoint.
Uses existing validated components:
- FullTextManager: URL collection with waterfall optimization
- PDFDownloadManager: Download with fallback through multiple URLs
- PDFExtractor: PDF parsing and content extraction
- UnifiedDatabase: Persistent storage

TODO (v3.0.0): Refactor to use PipelineCoordinator for better architecture.
See: docs/ENRICH_FULLTEXT_REFACTORING_PLAN.md
"""

import logging
import os
import time
from pathlib import Path
from typing import Dict, List, Optional

from omics_oracle_v2.api.models import DatasetResponse
from omics_oracle_v2.lib.pipelines.citation_discovery.clients.config import \
    PubMedConfig
from omics_oracle_v2.lib.pipelines.citation_discovery.clients.pubmed import \
    PubMedClient
from omics_oracle_v2.lib.pipelines.pdf_download import PDFDownloadManager
from omics_oracle_v2.lib.pipelines.storage import get_registry
from omics_oracle_v2.lib.pipelines.storage.models import (ContentExtraction,
                                                          PDFAcquisition)
from omics_oracle_v2.lib.pipelines.text_enrichment import PDFExtractor
from omics_oracle_v2.lib.pipelines.url_collection import (
    FullTextManager, FullTextManagerConfig)
from omics_oracle_v2.lib.search_engines.citations.models import Publication

logger = logging.getLogger(__name__)


class FulltextService:
    """Service for full-text enrichment of GEO datasets.

    Minimal working implementation (Oct 16, 2025).
    Provides PDF download functionality using existing pipeline components.
    """

    def __init__(self):
        """Initialize service with database registry."""
        self.db = get_registry()

    async def enrich_datasets(
        self,
        datasets: List[DatasetResponse],
        max_papers: Optional[int] = None,
        include_citing_papers: bool = True,
        max_citing_papers: int = 5,
        download_original: bool = True,
        include_full_content: bool = True,
    ) -> List[DatasetResponse]:
        """
        Enrich datasets with full-text PDFs and extracted content.

        Pipeline:
        1. Fetch publication metadata from PubMed
        2. Collect URLs using FullTextManager (waterfall with skip optimization)
        3. Download PDFs using PDFDownloadManager (with fallback)
        4. Parse PDFs using PDFExtractor (optional)
        5. Store in database
        6. Return enriched datasets

        Args:
            datasets: List of datasets to enrich (must have pubmed_ids)
            max_papers: Maximum papers to download per dataset
            include_citing_papers: Download citing papers (NOT IMPLEMENTED YET)
            max_citing_papers: Max citing papers per dataset (NOT IMPLEMENTED YET)
            download_original: Download original papers (always True for now)
            include_full_content: Include parsed text sections

        Returns:
            List of datasets with fulltext status and counts
        """
        start_time = time.time()

        logger.info(f"[FULLTEXT] Starting enrichment for {len(datasets)} dataset(s)...")

        # Initialize components
        fulltext_manager = None
        pdf_downloader = None
        pubmed_client = None

        try:
            # Initialize FullTextManager
            logger.info("[FULLTEXT] Initializing FullTextManager with all sources...")
            fulltext_config = FullTextManagerConfig(
                enable_institutional=True,
                enable_pmc=True,
                enable_unpaywall=True,
                enable_openalex=True,
                enable_core=True,
                enable_biorxiv=True,
                enable_arxiv=True,
                enable_crossref=True,
                enable_scihub=True,
                enable_libgen=True,
                download_pdfs=False,  # We handle downloads separately
                unpaywall_email=os.getenv("UNPAYWALL_EMAIL", "research@omicsoracle.ai"),
                core_api_key=os.getenv("CORE_API_KEY"),
            )
            fulltext_manager = FullTextManager(fulltext_config)
            await fulltext_manager.initialize()

            # Initialize PDF downloader
            pdf_downloader = PDFDownloadManager(
                max_concurrent=3, max_retries=2, timeout_seconds=30, validate_pdf=True
            )

            # Initialize PubMed client
            pubmed_client = PubMedClient(
                PubMedConfig(email=os.getenv("NCBI_EMAIL", "research@omicsoracle.ai"))
            )

            # Process each dataset
            enriched_datasets = []

            for dataset in datasets:
                try:
                    enriched = await self._process_dataset(
                        dataset=dataset,
                        pubmed_client=pubmed_client,
                        fulltext_manager=fulltext_manager,
                        pdf_downloader=pdf_downloader,
                        max_papers=max_papers,
                        include_full_content=include_full_content,
                    )
                    enriched_datasets.append(enriched)

                except Exception as e:
                    logger.error(
                        f"[ERROR] Failed to process {dataset.geo_id}: {e}",
                        exc_info=True,
                    )
                    # Return dataset with error status
                    dataset.fulltext_status = "error"
                    dataset.fulltext_count = 0
                    enriched_datasets.append(dataset)

            elapsed = time.time() - start_time
            logger.info(f"[FULLTEXT] Enrichment complete in {elapsed:.1f}s")

            return enriched_datasets

        finally:
            # Cleanup resources
            if fulltext_manager:
                try:
                    await fulltext_manager.cleanup()
                    logger.debug("[FULLTEXT] Cleaned up FullTextManager")
                except Exception as e:
                    logger.warning(f"[FULLTEXT] Cleanup error: {e}")

    async def _process_dataset(
        self,
        dataset: DatasetResponse,
        pubmed_client: PubMedClient,
        fulltext_manager: FullTextManager,
        pdf_downloader: PDFDownloadManager,
        max_papers: Optional[int],
        include_full_content: bool,
    ) -> DatasetResponse:
        """
        Process a single dataset through the enrichment pipeline.

        Returns:
            Enriched dataset with fulltext_status and fulltext_count
        """
        geo_id = dataset.geo_id
        logger.info(f"[{geo_id}] Starting enrichment...")

        # Get PubMed IDs
        pmids = dataset.pubmed_ids or []
        if not pmids:
            logger.warning(f"[{geo_id}] No PubMed IDs found")
            dataset.fulltext_status = "no_pmids"
            dataset.fulltext_count = 0
            return dataset

        # Limit papers if requested
        if max_papers:
            pmids = pmids[:max_papers]

        logger.info(f"[{geo_id}] Processing {len(pmids)} publication(s)...")

        # Step 1: Fetch publication metadata from PubMed
        publications = await self._fetch_publications(geo_id, pmids, pubmed_client)
        if not publications:
            logger.warning(f"[{geo_id}] Failed to fetch any publications from PubMed")
            dataset.fulltext_status = "fetch_failed"
            dataset.fulltext_count = 0
            return dataset

        # Step 2: Collect URLs using FullTextManager
        url_results = await self._collect_urls(geo_id, publications, fulltext_manager)

        # Step 3: Download PDFs with fallback
        output_dir = Path("data/pdfs") / geo_id
        download_results = await self._download_pdfs(
            geo_id, publications, url_results, pdf_downloader, output_dir
        )

        # Step 4: Parse PDFs if requested
        if include_full_content:
            await self._parse_pdfs(geo_id, download_results)

        # Step 5: Determine overall status
        total = len(download_results)
        successful = sum(1 for r in download_results if r.success)

        if successful == 0:
            status = "failed"
        elif successful == total:
            status = "success"
        else:
            status = "partial"

        dataset.fulltext_status = status
        dataset.fulltext_count = successful

        logger.info(
            f"[{geo_id}] Complete: status={status}, "
            f"downloaded={successful}/{total} papers"
        )

        return dataset

    async def _fetch_publications(
        self,
        geo_id: str,
        pmids: List[str],
        pubmed_client: PubMedClient,
    ) -> List[Publication]:
        """
        Fetch publication metadata from PubMed.

        Returns:
            List of Publication objects
        """
        logger.info(f"[{geo_id}] Fetching metadata for {len(pmids)} PMID(s)...")

        publications = []

        for pmid in pmids:
            try:
                # Fetch from PubMed
                pub_data = await pubmed_client.fetch_publication(pmid)

                if pub_data:
                    # Convert to Publication object
                    pub = Publication(
                        pmid=pmid,
                        doi=pub_data.get("doi"),
                        title=pub_data.get("title", "Unknown Title"),
                        abstract=pub_data.get("abstract"),
                        authors=pub_data.get("authors", []),
                        journal=pub_data.get("journal"),
                        publication_date=pub_data.get("publication_date"),
                        source="pubmed",
                    )
                    publications.append(pub)
                    logger.debug(
                        f"[{geo_id}] Fetched PMID:{pmid} - {pub.title[:50]}..."
                    )
                else:
                    logger.warning(f"[{geo_id}] No data for PMID:{pmid}")

            except Exception as e:
                logger.error(f"[{geo_id}] Error fetching PMID:{pmid}: {e}")
                continue

        logger.info(f"[{geo_id}] Fetched {len(publications)}/{len(pmids)} publications")
        return publications

    async def _collect_urls(
        self,
        geo_id: str,
        publications: List[Publication],
        fulltext_manager: FullTextManager,
    ) -> Dict[str, List]:
        """
        Collect fulltext URLs using FullTextManager.

        Returns:
            Dict mapping PMID -> List[SourceURL]
        """
        logger.info(
            f"[{geo_id}] Collecting URLs for {len(publications)} publications..."
        )

        url_results = {}

        for pub in publications:
            try:
                # Use FullTextManager to collect all URLs (with waterfall skip optimization)
                result = await fulltext_manager.get_all_fulltext_urls(pub)

                if result.all_urls:
                    url_results[pub.pmid] = result.all_urls
                    logger.debug(
                        f"[{geo_id}] PMID:{pub.pmid} - Found {len(result.all_urls)} URL(s) "
                        f"from {len(result.sources_queried)} source(s)"
                    )
                else:
                    logger.warning(f"[{geo_id}] PMID:{pub.pmid} - No URLs found")
                    url_results[pub.pmid] = []

            except Exception as e:
                logger.error(
                    f"[{geo_id}] Error collecting URLs for PMID:{pub.pmid}: {e}"
                )
                url_results[pub.pmid] = []

        total_urls = sum(len(urls) for urls in url_results.values())
        logger.info(f"[{geo_id}] Collected {total_urls} total URL(s)")

        return url_results

    async def _download_pdfs(
        self,
        geo_id: str,
        publications: List[Publication],
        url_results: Dict[str, List],
        pdf_downloader: PDFDownloadManager,
        output_dir: Path,
    ) -> List:
        """
        Download PDFs with fallback through multiple URLs.

        Returns:
            List of DownloadResult objects
        """
        logger.info(f"[{geo_id}] Downloading PDFs to {output_dir}...")
        output_dir.mkdir(parents=True, exist_ok=True)

        download_results = []

        for pub in publications:
            try:
                urls = url_results.get(pub.pmid, [])

                if not urls:
                    logger.warning(f"[{geo_id}] PMID:{pub.pmid} - No URLs to download")
                    from omics_oracle_v2.lib.pipelines.pdf_download.download_manager import \
                        DownloadResult

                    download_results.append(
                        DownloadResult(
                            publication=pub, success=False, error="No URLs found"
                        )
                    )
                    continue

                # Download with fallback through all URLs
                result = await pdf_downloader.download_with_fallback(
                    publication=pub,
                    all_urls=urls,
                    output_dir=output_dir,
                )

                download_results.append(result)

                if result.success:
                    logger.info(
                        f"[{geo_id}] PMID:{pub.pmid} - [OK] Downloaded "
                        f"({result.file_size / 1024:.1f} KB) from {result.source}"
                    )

                    # Store in database
                    acquisition = PDFAcquisition(
                        geo_id=geo_id,
                        pmid=pub.pmid,
                        pdf_path=str(result.pdf_path),
                        pdf_hash_sha256="",  # TODO: Calculate hash
                        pdf_size_bytes=result.file_size,
                        source_url=str(urls[0].url) if urls else None,
                        source_type=result.source,
                        download_method="fallback",
                        status="success",
                    )
                    self.db.insert_pdf_acquisition(acquisition)
                else:
                    logger.warning(
                        f"[{geo_id}] PMID:{pub.pmid} - [FAIL] Download failed: "
                        f"{result.error}"
                    )

            except Exception as e:
                logger.error(f"[{geo_id}] Error downloading PMID:{pub.pmid}: {e}")
                from omics_oracle_v2.lib.pipelines.pdf_download.download_manager import \
                    DownloadResult

                download_results.append(
                    DownloadResult(publication=pub, success=False, error=str(e))
                )

        successful = sum(1 for r in download_results if r.success)
        logger.info(
            f"[{geo_id}] Downloaded {successful}/{len(download_results)} PDF(s)"
        )

        return download_results

    async def _parse_pdfs(
        self,
        geo_id: str,
        download_results: List,
    ) -> None:
        """
        Parse downloaded PDFs and extract content.

        Stores results in database.
        """
        logger.info(f"[{geo_id}] Parsing downloaded PDFs...")

        extractor = PDFExtractor()
        successful_downloads = [r for r in download_results if r.success and r.pdf_path]

        for result in successful_downloads:
            try:
                pmid = result.publication.pmid
                pdf_path = result.pdf_path

                logger.debug(f"[{geo_id}] Parsing {pdf_path.name}...")

                # Extract content
                parsed = await extractor.extract(pdf_path)

                if parsed and parsed.full_text:
                    # Store in database
                    extraction = ContentExtraction(
                        geo_id=geo_id,
                        pmid=pmid,
                        full_text=parsed.full_text,
                        page_count=parsed.page_count,
                        char_count=len(parsed.full_text),
                        word_count=len(parsed.full_text.split()),
                        extractor_used="PDFExtractor",
                        extraction_method=parsed.extraction_method,
                        has_readable_text=True,
                    )
                    self.db.insert_content_extraction(extraction)

                    logger.info(
                        f"[{geo_id}] PMID:{pmid} - [OK] Parsed "
                        f"({len(parsed.full_text)} chars, {parsed.page_count} pages)"
                    )
                else:
                    logger.warning(
                        f"[{geo_id}] PMID:{pmid} - [FAIL] Parsing failed (no text)"
                    )

            except Exception as e:
                logger.error(f"[{geo_id}] Error parsing {result.pdf_path}: {e}")

        parsed_count = len([r for r in successful_downloads])
        logger.info(f"[{geo_id}] Attempted to parse {parsed_count} PDF(s)")
