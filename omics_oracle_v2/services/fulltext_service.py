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

import asyncio
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
from omics_oracle_v2.lib.pipelines.storage import UnifiedDatabase
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
        """Initialize service with database."""
        self.db = UnifiedDatabase("data/database/omics_oracle.db")

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
            logger.info("[FULLTEXT] Initializing components (fast sources only)...")
            fulltext_config = FullTextManagerConfig(
                enable_institutional=True,
                enable_pmc=True,  # RE-ENABLED: Fixed with proper HTTP headers
                enable_unpaywall=True,
                enable_openalex=False,  # DISABLED: Can be slow for large batches
                enable_core=False,  # DISABLED: Often slow and rate-limited
                enable_biorxiv=True,
                enable_arxiv=True,
                enable_crossref=True,
                enable_scihub=True,  # Fast and reliable
                enable_libgen=True,
                download_pdfs=False,  # We handle downloads separately
                unpaywall_email=os.getenv("UNPAYWALL_EMAIL", "research@omicsoracle.ai"),
                core_api_key=os.getenv("CORE_API_KEY"),
            )
            fulltext_manager = FullTextManager(fulltext_config)
            await fulltext_manager.initialize()

            # Initialize PDF downloader with aggressive concurrency
            pdf_downloader = PDFDownloadManager(
                max_concurrent=25,  # MAXIMUM: Download all 25 papers simultaneously
                max_retries=0,  # NO RETRIES: Use waterfall fallback instead (faster)
                timeout_seconds=15,  # Aggressive timeout for faster failure detection
                validate_pdf=True,  # CRITICAL: Validate PDFs to reject HTML error pages
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

        # Get PubMed IDs - FIRST check database for ALL citing papers
        pmids = []

        # Get PMIDs from dataset (passed from SearchService with all citing papers)
        dataset_pmids = dataset.pubmed_ids or []

        # Try to get additional metadata from database
        db_pmids = []
        try:
            logger.debug(f"[{geo_id}] Calling db.get_publications_by_geo()...")
            pubs_from_db = self.db.get_publications_by_geo(geo_id)
            logger.debug(f"[{geo_id}] Got {len(pubs_from_db)} publications from DB")

            if pubs_from_db:
                # Check if we got UniversalIdentifier objects or dicts
                if hasattr(pubs_from_db[0], "pmid"):
                    # UniversalIdentifier objects
                    db_pmids = [p.pmid for p in pubs_from_db if p.pmid]
                else:
                    # Dicts
                    db_pmids = [p["pmid"] for p in pubs_from_db if p.get("pmid")]

                logger.debug(f"[{geo_id}] Found {len(db_pmids)} paper(s) in database")
        except Exception as e:
            logger.error(
                f"[{geo_id}] Could not fetch papers from database: {e}", exc_info=True
            )

        # Use dataset PMIDs (which includes all citing papers from SearchService)
        # Database is only used for additional metadata, not as PMID source
        pmids = dataset_pmids
        logger.info(
            f"[{geo_id}] Using {len(pmids)} PubMed ID(s) from dataset "
            f"(includes {len(dataset_pmids)} from citing papers analysis)"
        )

        if not pmids:
            logger.warning(f"[{geo_id}] No PubMed IDs found in database or dataset")
            dataset.fulltext_status = "no_pmids"
            dataset.fulltext_count = 0
            return dataset

        # Limit papers if requested
        if max_papers:
            original_count = len(pmids)
            pmids = pmids[:max_papers]
            logger.info(
                f"[{geo_id}] Limited to {len(pmids)}/{original_count} papers "
                f"(max_papers={max_papers})"
            )

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

        # Step 5: Load parsed content from database and populate dataset.fulltext
        fulltext_list = []
        for result in download_results:
            if result.success:
                pub = result.publication
                pmid = pub.pmid

                # Create fulltext object with metadata
                fulltext_obj = {
                    "pmid": pmid,
                    "title": pub.title,
                    "authors": getattr(pub, "authors", None),
                    "journal": getattr(pub, "journal", None),
                    "year": getattr(pub, "year", None),
                    "doi": getattr(pub, "doi", None),
                    "url": getattr(pub, "fulltext_url", None),
                    "pdf_path": str(result.pdf_path) if result.pdf_path else None,
                }

                # Load parsed content from database if available
                if include_full_content:
                    try:
                        content = self.db.get_content_extraction(geo_id, pmid)
                        if content:
                            # Add parsed sections to fulltext object
                            # Parse the full_text into sections (basic parsing)
                            full_text = content.full_text or ""

                            # Simple heuristic: split by common headers
                            # This is a simplified version - real parsing would use PDFExtractor's section detection
                            fulltext_obj["abstract"] = ""
                            fulltext_obj["methods"] = ""
                            fulltext_obj["results"] = ""
                            fulltext_obj["discussion"] = ""

                            # For now, put full text in all sections so AI Analysis can access it
                            # TODO: Implement proper section extraction from full_text
                            text_preview = full_text[:5000]  # First 5K chars
                            text_middle = (
                                full_text[
                                    len(full_text) // 2 : len(full_text) // 2 + 5000
                                ]
                                if len(full_text) > 10000
                                else ""
                            )
                            text_end = (
                                full_text[-5000:]
                                if len(full_text) > 5000
                                else full_text
                            )

                            fulltext_obj["abstract"] = text_preview
                            fulltext_obj["methods"] = (
                                text_middle if text_middle else text_preview
                            )
                            fulltext_obj["results"] = (
                                text_end if text_end else text_preview
                            )
                            fulltext_obj["discussion"] = (
                                text_end if text_end else text_preview
                            )
                            fulltext_obj["full_text"] = full_text  # Include full text
                            fulltext_obj["char_count"] = content.char_count
                            fulltext_obj["page_count"] = content.page_count
                            fulltext_obj["has_methods"] = True
                            fulltext_obj["has_results"] = True
                            fulltext_obj[
                                "extraction_method"
                            ] = content.extraction_method

                            logger.debug(
                                f"[{geo_id}] Loaded {content.char_count} chars "
                                f"for PMID {pmid} from database"
                            )
                    except Exception as e:
                        logger.warning(
                            f"[{geo_id}] Could not load parsed content for PMID {pmid}: {e}"
                        )

                fulltext_list.append(fulltext_obj)

        # Populate dataset.fulltext array
        dataset.fulltext = fulltext_list

        # Step 6: Determine overall status
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

        # Update pdf_count to match (for dashboard display consistency)
        # This shows the correct count in "X/Y PDF downloaded"
        dataset.pdf_count = successful

        # Add fulltext_total so frontend knows how many papers were attempted (including citing papers)
        dataset.fulltext_total = total

        # Update completion_rate (percentage of papers processed)
        if total > 0:
            dataset.completion_rate = (successful / total) * 100.0

        logger.info(
            f"[{geo_id}] Complete: status={status}, "
            f"downloaded={successful}/{total} papers, "
            f"pdf_count={dataset.pdf_count}, completion={dataset.completion_rate:.0f}%, "
            f"fulltext_objects={len(fulltext_list)}"
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
                # Fetch from PubMed (returns Publication object)
                pub = pubmed_client.fetch_by_id(pmid)

                if pub:
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
        Collect fulltext URLs using FullTextManager IN PARALLEL for speed.

        Returns:
            Dict mapping PMID -> List[SourceURL]
        """
        logger.info(
            f"[{geo_id}] Collecting URLs for {len(publications)} publications in parallel..."
        )

        # Collect URLs in parallel for all publications (MUCH faster!)
        async def collect_for_pub(pub):
            """Collect URLs for a single publication, returns (pmid, urls)"""
            try:
                # Use FullTextManager to collect all URLs
                result = await fulltext_manager.get_all_fulltext_urls(pub)

                if result.all_urls:
                    return (pub.pmid, result.all_urls)
                else:
                    logger.warning(f"[{geo_id}] PMID:{pub.pmid} - No URLs found")
                    return (pub.pmid, [])

            except Exception as e:
                logger.error(
                    f"[{geo_id}] Error collecting URLs for PMID:{pub.pmid}: {e}",
                    exc_info=True,
                )
                return (pub.pmid, [])

        # Execute URL collection in parallel for all publications
        results = await asyncio.gather(*[collect_for_pub(pub) for pub in publications])

        # Convert list of tuples to dict
        url_results = {pmid: urls for pmid, urls in results}

        total_urls = sum(len(urls) for urls in url_results.values())
        logger.info(
            f"[{geo_id}] Collected {total_urls} total URL(s) from {len(publications)} publications"
        )

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
        import time

        start_time = time.time()

        logger.info(f"[{geo_id}] Downloading PDFs to {output_dir}...")
        output_dir.mkdir(parents=True, exist_ok=True)

        # OPTIMIZATION: Download PDFs in parallel using asyncio.gather (25 concurrent)
        async def download_single_pdf(pub: Publication) -> any:
            """Download a single PDF with fallback."""
            try:
                # CHECK DATABASE CACHE: Skip if already successfully downloaded
                try:
                    existing_acquisition = self.db.get_pdf_acquisition(geo_id, pub.pmid)
                    if (
                        existing_acquisition
                        and existing_acquisition.status == "success"
                    ):
                        pdf_path = Path(existing_acquisition.pdf_path)
                        if pdf_path.exists():
                            logger.info(
                                f"[{geo_id}] PMID:{pub.pmid} - [DB CACHED] Already downloaded, skipping"
                            )
                            from omics_oracle_v2.lib.pipelines.pdf_download.download_manager import \
                                DownloadResult

                            return DownloadResult(
                                publication=pub,
                                success=True,
                                pdf_path=pdf_path,
                                file_size=pdf_path.stat().st_size,
                                source="db_cache",
                                error=None,
                            )
                except Exception as db_err:
                    # If database check fails, continue with download
                    logger.debug(
                        f"[{geo_id}] PMID:{pub.pmid} - DB cache check failed: {db_err}"
                    )

                # CHECK FILE SYSTEM CACHE: Skip download if PDF already exists
                expected_path = output_dir / f"pmid_{pub.pmid}.pdf"
                if expected_path.exists():
                    logger.info(
                        f"[{geo_id}] PMID:{pub.pmid} - [FILE CACHED] PDF already exists, skipping download"
                    )
                    from omics_oracle_v2.lib.pipelines.pdf_download.download_manager import \
                        DownloadResult

                    return DownloadResult(
                        publication=pub,
                        success=True,
                        pdf_path=expected_path,
                        file_size=expected_path.stat().st_size,
                        source="file_cache",
                        error=None,
                    )

                urls = url_results.get(pub.pmid, [])

                if not urls:
                    logger.warning(f"[{geo_id}] PMID:{pub.pmid} - No URLs to download")
                    from omics_oracle_v2.lib.pipelines.pdf_download.download_manager import \
                        DownloadResult

                    return DownloadResult(
                        publication=pub, success=False, error="No URLs found"
                    )

                # Download with fallback through all URLs (with timing)
                import time

                download_start = time.time()

                result = await pdf_downloader.download_with_fallback(
                    publication=pub,
                    all_urls=urls,
                    output_dir=output_dir,
                )

                download_time = time.time() - download_start

                if result.success:
                    logger.info(
                        f"[{geo_id}] PMID:{pub.pmid} - [OK] Downloaded in {download_time:.1f}s "
                        f"({result.file_size / 1024:.1f} KB) from {result.source}"
                    )

                    # Ensure publication exists in universal_identifiers (for foreign key)
                    try:
                        from omics_oracle_v2.lib.pipelines.storage.unified_db import \
                            UniversalIdentifier

                        universal_id = UniversalIdentifier(
                            pmid=pub.pmid,
                            doi=pub.doi,
                            pmcid=pub.pmcid,
                            title=pub.title,
                            first_author=pub.authors[0] if pub.authors else None,
                            publication_year=pub.publication_date[:4]
                            if pub.publication_date
                            else None,
                            journal=pub.journal,
                            citation_count=0,
                        )
                        self.db.insert_universal_identifier(universal_id)
                    except Exception as e:
                        # Already exists, that's fine
                        logger.debug(
                            f"[{geo_id}] PMID:{pub.pmid} - Universal ID insert: {e}"
                        )

                    # Store in database with performance metrics
                    acquisition = PDFAcquisition(
                        geo_id=geo_id,
                        pmid=pub.pmid,
                        pdf_path=str(result.pdf_path),
                        pdf_hash_sha256="",  # TODO: Calculate hash
                        pdf_size_bytes=result.file_size,
                        source_url=str(urls[0].url) if urls else None,
                        source_type=result.source,
                        download_method=f"fallback_{download_time:.1f}s",  # Track timing
                        status="success",
                    )
                    self.db.insert_pdf_acquisition(acquisition)

                    # Log performance for source prioritization
                    logger.debug(
                        f"[PERF] {result.source}: {download_time:.1f}s for "
                        f"{result.file_size / 1024:.0f}KB ({result.file_size / 1024 / download_time:.0f} KB/s)"
                    )
                else:
                    logger.warning(
                        f"[{geo_id}] PMID:{pub.pmid} - [FAIL] Download failed: "
                        f"{result.error}"
                    )

                return result

            except Exception as e:
                logger.error(f"[{geo_id}] Error downloading PMID:{pub.pmid}: {e}")
                from omics_oracle_v2.lib.pipelines.pdf_download.download_manager import \
                    DownloadResult

                return DownloadResult(publication=pub, success=False, error=str(e))

        # Execute all downloads in parallel
        download_results = await asyncio.gather(
            *[download_single_pdf(pub) for pub in publications]
        )

        successful = sum(1 for r in download_results if r.success)

        # Calculate performance statistics
        total_time = time.time() - start_time
        throughput = successful / total_time if total_time > 0 else 0

        logger.info(
            f"[{geo_id}] Downloaded {successful}/{len(download_results)} PDF(s) "
            f"in {total_time:.1f}s ({throughput:.1f} PDFs/sec, max 25 concurrent)"
        )

        return list(download_results)

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

                # Extract content (PDFExtractor.extract_text is synchronous)
                metadata = {
                    "title": result.publication.title,
                    "pmid": pmid,
                    "doi": result.publication.doi,
                }
                parsed = extractor.extract_text(pdf_path, metadata=metadata)

                if parsed and parsed.get("full_text"):
                    # Store in database
                    full_text = parsed["full_text"]
                    page_count = parsed.get("page_count", 0)
                    extraction_method = parsed.get("extraction_method", "pypdf")

                    extraction = ContentExtraction(
                        geo_id=geo_id,
                        pmid=pmid,
                        full_text=full_text,
                        page_count=page_count,
                        char_count=len(full_text),
                        word_count=len(full_text.split()),
                        extractor_used="PDFExtractor",
                        extraction_method=extraction_method,
                        has_readable_text=True,
                    )
                    self.db.insert_content_extraction(extraction)

                    logger.info(
                        f"[{geo_id}] PMID:{pmid} - [OK] Parsed "
                        f"({len(full_text)} chars, {page_count} pages)"
                    )
                else:
                    logger.warning(
                        f"[{geo_id}] PMID:{pmid} - [FAIL] Parsing failed (no text)"
                    )

            except Exception as e:
                logger.error(f"[{geo_id}] Error parsing {result.pdf_path}: {e}")

        parsed_count = len([r for r in successful_downloads])
        logger.info(f"[{geo_id}] Attempted to parse {parsed_count} PDF(s)")
