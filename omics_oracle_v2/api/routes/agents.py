"""
Agent Execution Routes

REST endpoints for executing search and analysis operations.

Note: Individual agent endpoints (query, validate, report) have been removed.
      All agents archived to extras/agents/. Main functionality:
      - /search: SearchOrchestrator for dataset/publication search
      - /enrich-fulltext: FullTextManager for PDF download
      - /analyze: SummarizationClient for AI analysis
"""

import logging
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from omics_oracle_v2.api.models.requests import SearchRequest
from omics_oracle_v2.api.models.responses import (DatasetResponse,
                                                  SearchResponse)
from omics_oracle_v2.lib.pipelines.citation_discovery.geo_discovery import \
    GEOCitationDiscovery
from omics_oracle_v2.services.search_service import SearchService

# TODO: DatabaseQueries deleted - use UnifiedDatabase directly if needed
# from omics_oracle_v2.lib.pipelines.storage.queries import DatabaseQueries

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Agents"])


# Agent Execution Endpoints


@router.post(
    "/search", response_model=SearchResponse, summary="Search Datasets and Publications"
)
async def execute_search(
    request: SearchRequest,
):
    """
    Search for datasets and publications using the SearchOrchestrator.

    This endpoint searches across multiple sources:
    - NCBI GEO database for omics datasets
    - PubMed for biomedical publications
    - OpenAlex for open access articles

    Features:
    - **Intelligent query analysis**: Auto-detects query type (GEO ID, keyword, etc.)
    - **Query optimization**: NER + SapBERT semantic expansion
    - **Hybrid search**: Searches both datasets and publications in parallel
    - **Redis caching**: 1000x speedup for cached queries
    - **Cross-source linking**: Finds datasets mentioned in publications

    **Note:** This endpoint is public for demo purposes. No authentication required.

    Args:
        request: Search request with terms, filters, result limit, and semantic flag

    Returns:
        SearchResponse: Ranked dataset and publication results with relevance scores
    """
    try:
        service = SearchService()
        return await service.execute_search(request)
    except Exception as e:
        logger.error(f"Search execution failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search error: {str(e)}",
        )


@router.post(
    "/enrich-fulltext",
    response_model=List[DatasetResponse],
    summary="Enrich Datasets with Full-Text Content",
)
async def enrich_fulltext(
    datasets: List[DatasetResponse],
    max_papers: int = Query(
        default=None,
        description="Maximum papers to download per dataset. None = download ALL papers.",
    ),
    include_full_content: bool = Query(
        default=False,
        description="Include full parsed text (abstract, methods, results, etc.). "
        "Set to False to reduce response size and avoid HTTP/2 errors.",
    ),
    include_citing_papers: bool = Query(
        default=True,
        description="Download papers that CITED this dataset (not just original paper). "
        "This shows how the dataset was USED in research.",
    ),
    max_citing_papers: int = Query(
        default=10,
        description="Maximum citing papers to download per dataset (default=10).",
    ),
    download_original: bool = Query(
        default=True,
        description="Also download the original paper that generated the dataset (stored separately).",
    ),
):
    """
    Enrich datasets with full-text content from linked publications.

    Uses FullTextManager directly (same approach as PublicationSearchPipeline).

    This endpoint:
    1. Takes datasets with PubMed IDs
    2. Fetches full publication metadata from PubMed (DOI, PMC ID)
    3. Downloads PDFs using FullTextManager.get_fulltext_batch() (concurrent!)
    4. Returns datasets with fulltext URLs

    **Note:** This is a public endpoint for demo purposes (async background task).

    Args:
        datasets: List of datasets to enrich (must have pubmed_ids)
        max_papers: Maximum papers to download per dataset (1-10)

    Returns:
        List of datasets with full-text URLs attached
    """
    import os
    from pathlib import Path

    from omics_oracle_v2.lib.pipelines.citation_discovery.clients.config import \
        PubMedConfig
    from omics_oracle_v2.lib.pipelines.citation_discovery.clients.pubmed import \
        PubMedClient
    from omics_oracle_v2.lib.pipelines.pdf_download import PDFDownloadManager
    from omics_oracle_v2.lib.pipelines.storage import get_registry
    from omics_oracle_v2.lib.pipelines.url_collection import (
        FullTextManager, FullTextManagerConfig)

    start_time = time.time()

    try:
        # Initialize FullTextManager (for getting PDF URLs from various sources)
        logger.info("Initializing FullTextManager with all sources...")
        fulltext_config = FullTextManagerConfig(
            enable_institutional=True,
            enable_pmc=True,
            enable_unpaywall=True,
            enable_openalex=True,
            enable_core=True,
            enable_biorxiv=True,
            enable_arxiv=True,
            enable_crossref=True,
            enable_scihub=True,  # User requested
            enable_libgen=True,  # User requested
            download_pdfs=False,  # [WARNING] CRITICAL: DO NOT download here, we use PDFDownloadManager instead
            unpaywall_email=os.getenv("UNPAYWALL_EMAIL", "research@omicsoracle.ai"),
            core_api_key=os.getenv("CORE_API_KEY"),
        )
        fulltext_manager = FullTextManager(fulltext_config)

        # Initialize PDFDownloadManager (for actually downloading and validating PDFs)
        pdf_downloader = PDFDownloadManager(
            max_concurrent=3, max_retries=2, timeout_seconds=30, validate_pdf=True
        )

        # Initialize PubMed client for metadata fetching
        pubmed_client = PubMedClient(
            PubMedConfig(email=os.getenv("NCBI_EMAIL", "research@omicsoracle.ai"))
        )

        # Initialize manager
        if not fulltext_manager.initialized:
            await fulltext_manager.initialize()

        enriched_datasets = []

        # Initialize citation discovery if needed
        citation_discovery = None
        if include_citing_papers:
            logger.info("[CITATION] Initializing citation discovery...")
            citation_discovery = GEOCitationDiscovery()

        for dataset in datasets:
            logger.info(f"\n{'=' * 80}")
            logger.info(f"Processing {dataset.geo_id}: {dataset.title[:60]}...")
            logger.info(f"{'=' * 80}\n")

            if not dataset.pubmed_ids:
                logger.warning(f"Dataset {dataset.geo_id} has no PubMed IDs")
                enriched_datasets.append(dataset)
                continue

            # STEP 0: Decide what papers to download based on user preferences
            original_pmids = (
                dataset.pubmed_ids[:max_papers]
                if max_papers is not None
                else dataset.pubmed_ids
            )

            # Track what we'll download
            papers_to_download = {
                "original": [],  # Original paper(s) that generated the dataset
                "citing": [],  # Papers that cited/used the dataset
            }

            # STEP 1: Handle ORIGINAL papers (if requested)
            if download_original and original_pmids:
                logger.info(
                    f"[{dataset.geo_id}] [ORIGINAL] Fetching metadata for {len(original_pmids)} original paper(s)..."
                )
                for pmid in original_pmids:
                    try:
                        pub = pubmed_client.fetch_by_id(pmid)
                        if pub:
                            papers_to_download["original"].append(pub)
                            logger.info(
                                f"  [{dataset.geo_id}] [OK] PMID {pmid}: DOI={pub.doi}, PMC={pub.pmcid}"
                            )
                    except Exception as e:
                        logger.error(f"  [{dataset.geo_id}] [ERROR] PMID {pmid}: {e}")

            # STEP 2: Discover CITING papers (if requested)
            citation_result = None  # Initialize for metadata storage
            if include_citing_papers and citation_discovery:
                logger.info(
                    f"[{dataset.geo_id}] [CITATION] Discovering papers that cited {dataset.geo_id}..."
                )

                # Convert DatasetResponse to GEOSeriesMetadata for citation discovery
                geo_metadata = GEOSeriesMetadata(
                    geo_id=dataset.geo_id,
                    title=dataset.title,
                    summary=dataset.summary or "",
                    organism=dataset.organism or "",
                    platform=dataset.platform or "",
                    sample_count=dataset.sample_count,
                    submission_date=dataset.submission_date or "",
                    publication_date=dataset.publication_date or "",
                    pubmed_ids=dataset.pubmed_ids,
                )

                try:
                    citation_result = await citation_discovery.find_citing_papers(
                        geo_metadata, max_results=max_citing_papers
                    )

                    if citation_result.citing_papers:
                        logger.info(
                            f"  [{dataset.geo_id}] [OK] Found {len(citation_result.citing_papers)} citing papers"
                        )
                        papers_to_download["citing"] = citation_result.citing_papers[
                            :max_citing_papers
                        ]
                    else:
                        logger.warning(
                            f"  [{dataset.geo_id}] [WARNING] No citing papers found"
                        )

                except Exception as e:
                    logger.error(
                        f"  [ERROR] Citation discovery failed: {e}", exc_info=True
                    )

            # STEP 3: If no papers to download, skip
            total_papers = len(papers_to_download["original"]) + len(
                papers_to_download["citing"]
            )
            if total_papers == 0:
                logger.warning(f"[SKIP] No papers to download for {dataset.geo_id}")
                enriched_datasets.append(dataset)
                continue

            logger.info(
                f"[DOWNLOAD] Total papers to download: {total_papers} "
                f"(original={len(papers_to_download['original'])}, "
                f"citing={len(papers_to_download['citing'])})"
            )

            # Combine all publications for URL collection
            publications = papers_to_download["original"] + papers_to_download["citing"]

            # STEP 1: Get URLs from all sources (same as pipeline)
            logger.info(
                f" Finding full-text URLs for {len(publications)} publications from all sources..."
            )
            fulltext_results = await fulltext_manager.get_fulltext_batch(publications)

            # DEBUG: Log all fulltext results
            logger.warning(
                f"[DATA] FULLTEXT RESULTS: Received {len(fulltext_results)} results"
            )
            for idx, (pub, result) in enumerate(zip(publications, fulltext_results)):
                logger.warning(
                    f"   [{idx+1}] PMID {pub.pmid}: success={result.success}, source={result.source.value if result.success else 'NONE'}, has_url={bool(result.url)}"
                )

            # STEP 2: Set fulltext_url on publications for PDFDownloadManager
            logger.warning(
                "[LINK] STEP 2: Setting fulltext URLs on publication objects..."
            )
            urls_set = 0
            for pub, result in zip(publications, fulltext_results):
                if result.success and result.url:
                    pub.fulltext_url = result.url
                    pub.fulltext_source = result.source.value
                    urls_set += 1
                    logger.warning(
                        f"   [OK] PMID {pub.pmid}: URL set from {result.source.value}"
                    )
                else:
                    logger.warning(
                        f"   [ERROR] PMID {pub.pmid}: NO URL (success={result.success}, url={bool(result.url)})"
                    )
            logger.warning(
                f"[DATA] STEP 2 COMPLETE: Set URLs on {urls_set}/{len(publications)} publications"
            )

            # STEP 3: Download PDFs with automatic waterfall fallback (organized by paper type)
            logger.info(
                "[DOWNLOAD] STEP 3: Downloading PDFs with automatic waterfall fallback..."
            )

            # Create organized directory structure: data/pdfs/{geo_id}/{original|citing}/
            base_pdf_dir = Path("data/pdfs") / dataset.geo_id
            original_dir = base_pdf_dir / "original"
            citing_dir = base_pdf_dir / "citing"
            original_dir.mkdir(parents=True, exist_ok=True)
            citing_dir.mkdir(parents=True, exist_ok=True)

            download_results = {"original": [], "citing": []}
            successful_downloads = {"original": 0, "citing": 0}

            # Download ORIGINAL papers
            if papers_to_download["original"]:
                logger.info(
                    f"  [ORIGINAL] Downloading {len(papers_to_download['original'])} original paper(s)..."
                )
                for pub in papers_to_download["original"]:
                    url_result = await fulltext_manager.get_all_fulltext_urls(pub)

                    # Store ALL collected URLs on publication for metadata.json
                    pub._all_collected_urls = url_result.all_urls

                    if not url_result.all_urls:
                        logger.warning(f"    [SKIP] PMID {pub.pmid}: No URLs found")
                        continue

                    logger.info(
                        f"    [DOWNLOAD] PMID {pub.pmid}: Trying {len(url_result.all_urls)} sources "
                        f"({', '.join([u.source.value for u in url_result.all_urls])})"
                    )

                    result = await pdf_downloader.download_with_fallback(
                        publication=pub,
                        all_urls=url_result.all_urls,
                        output_dir=original_dir,
                    )

                    download_results["original"].append(result)

                    if result.success and result.pdf_path:
                        successful_downloads["original"] += 1
                        pub.pdf_path = result.pdf_path
                        pub.fulltext_source = result.source
                        pub.paper_type = "original"  # Mark as original paper
                        logger.info(
                            f"    [OK] PMID {pub.pmid}: Downloaded from {result.source} "
                            f"({result.file_size / 1024:.1f} KB) -> original/{result.pdf_path.name}"
                        )
                    else:
                        logger.warning(
                            f"    [FAIL] PMID {pub.pmid}: All sources failed. Error: {result.error}"
                        )

            # Download CITING papers
            if papers_to_download["citing"]:
                logger.info(
                    f"  [CITING] Downloading {len(papers_to_download['citing'])} citing paper(s)..."
                )
                for pub in papers_to_download["citing"]:
                    url_result = await fulltext_manager.get_all_fulltext_urls(pub)

                    # Store ALL collected URLs on publication for metadata.json
                    pub._all_collected_urls = url_result.all_urls

                    if not url_result.all_urls:
                        logger.warning(
                            f"    [SKIP] PMID {pub.pmid or pub.doi}: No URLs found"
                        )
                        continue

                    logger.info(
                        f"    [DOWNLOAD] PMID {pub.pmid or pub.doi}: Trying {len(url_result.all_urls)} sources "
                        f"({', '.join([u.source.value for u in url_result.all_urls])})"
                    )

                    result = await pdf_downloader.download_with_fallback(
                        publication=pub,
                        all_urls=url_result.all_urls,
                        output_dir=citing_dir,
                    )

                    download_results["citing"].append(result)

                    if result.success and result.pdf_path:
                        successful_downloads["citing"] += 1
                        pub.pdf_path = result.pdf_path
                        pub.fulltext_source = result.source
                        pub.paper_type = "citing"  # Mark as citing paper
                        logger.info(
                            f"    [OK] PMID {pub.pmid or pub.doi}: Downloaded from {result.source} "
                            f"({result.file_size / 1024:.1f} KB) -> citing/{result.pdf_path.name}"
                        )
                    else:
                        logger.warning(
                            f"    [FAIL] PMID {pub.pmid or pub.doi}: All sources failed. Error: {result.error}"
                        )

            # Log summary
            total_success = (
                successful_downloads["original"] + successful_downloads["citing"]
            )
            total_attempted = len(papers_to_download["original"]) + len(
                papers_to_download["citing"]
            )
            logger.warning(
                f"[OK] STEP 3 COMPLETE: Downloaded {total_success}/{total_attempted} PDFs "
                f"(original={successful_downloads['original']}/{len(papers_to_download['original'])}, "
                f"citing={successful_downloads['citing']}/{len(papers_to_download['citing'])})"
            )

            # STEP 4: Parse PDFs and attach to dataset
            logger.info("[PARSE] STEP 4: Parsing PDFs and building fulltext data...")
            dataset.fulltext = []
            added_count = 0
            skipped_no_url = 0
            skipped_no_pdf = 0

            # IMPORTANT: If citing papers were requested, add them FIRST to fulltext list
            # This ensures frontend "Download Papers" button shows citing papers by default
            papers_to_parse = []
            if include_citing_papers and papers_to_download["citing"]:
                papers_to_parse.extend(papers_to_download["citing"])
                logger.info(
                    f"  [PRIORITY] Will show {len(papers_to_download['citing'])} citing papers first"
                )
            if download_original and papers_to_download["original"]:
                papers_to_parse.extend(papers_to_download["original"])
                logger.info(
                    f"  [SECONDARY] Will include {len(papers_to_download['original'])} original papers"
                )

            for pub in papers_to_parse:
                # Skip if no URL found
                if not hasattr(pub, "fulltext_url") or not pub.fulltext_url:
                    logger.debug(f"   Skipping PMID {pub.pmid}: no fulltext_url")
                    skipped_no_url += 1
                    continue

                # Try to get parsed content if PDF was downloaded
                parsed_content = None
                has_pdf = (
                    hasattr(pub, "pdf_path")
                    and pub.pdf_path
                    and Path(pub.pdf_path).exists()
                )

                if has_pdf:
                    logger.info(
                        f"[DOC] Parsing PDF for PMID {pub.pmid} from {pub.pdf_path}..."
                    )
                    try:
                        # FIX: Use ParsedCache directly instead of deprecated get_parsed_content()
                        from omics_oracle_v2.lib.pipelines.text_enrichment import (
                            PDFExtractor, get_parsed_cache)

                        # Check cache first
                        cache = get_parsed_cache()
                        cached_content = await cache.get(pub.pmid)

                        if cached_content:
                            parsed_content = cached_content.get("content", {})
                            logger.info(
                                f"   [CACHE] Using cached parsed content for {pub.pmid}"
                            )
                        else:
                            # Parse the downloaded PDF
                            extractor = PDFExtractor(enable_enrichment=True)
                            parsed_content = extractor.extract_text(
                                Path(pub.pdf_path),
                                metadata={"pmid": pub.pmid, "title": pub.title},
                            )

                            # Cache it for future use
                            await cache.save(
                                publication_id=pub.pmid,
                                content=parsed_content,
                                source_file=str(pub.pdf_path),
                                source_type="pdf",
                            )
                            logger.info(
                                f"   [CACHE] Saved parsed content for {pub.pmid}"
                            )

                        logger.info(
                            f"   [OK] Parsed {Path(pub.pdf_path).stat().st_size // 1024} KB PDF: "
                            f"abstract={len(parsed_content.get('abstract', ''))} chars, "
                            f"methods={len(parsed_content.get('methods', ''))} chars"
                        )
                    except Exception as e:
                        logger.error(
                            f"   [ERROR] Failed to parse PDF for {pub.pmid}: {e}"
                        )
                        import traceback

                        logger.error(f"   [TRACE] {traceback.format_exc()}")
                else:
                    logger.warning(
                        f"[WARNING]  PMID {pub.pmid}: No PDF file (pdf_path={getattr(pub, 'pdf_path', 'NOT SET')})"
                    )
                    skipped_no_pdf += 1
                    # CRITICAL FIX: Skip this publication - don't add URL-only entries!
                    logger.warning(
                        f"   [ERROR] SKIPPING PMID {pub.pmid}: No PDF downloaded, not counting as success"
                    )
                    continue

                # Build fulltext info - ONLY if we have parsed content
                fulltext_info = {
                    "pmid": pub.pmid if hasattr(pub, "pmid") else None,
                    "doi": pub.doi if hasattr(pub, "doi") else None,
                    "title": pub.title
                    or (parsed_content.get("title") if parsed_content else pub.title),
                    "url": pub.fulltext_url,
                    "source": pub.fulltext_source
                    if hasattr(pub, "fulltext_source")
                    else "unknown",
                    "pdf_path": str(pub.pdf_path)
                    if hasattr(pub, "pdf_path") and pub.pdf_path
                    else None,
                    "paper_type": pub.paper_type
                    if hasattr(pub, "paper_type")
                    else "unknown",  # "original" or "citing"
                }

                # Add parsed sections if available
                # FIXED (Oct 15, 2025): Always include full content when we have it!
                # If we took the time to download and parse the PDF, the content should be used.
                # The "include_full_content" param is now only for backwards compatibility.
                if parsed_content:
                    # Always include full parsed text when available
                    fulltext_info.update(
                        {
                            "abstract": parsed_content.get("abstract", ""),
                            "methods": parsed_content.get("methods", ""),
                            "results": parsed_content.get("results", ""),
                            "discussion": parsed_content.get("discussion", ""),
                            "introduction": parsed_content.get("introduction", ""),
                            "conclusion": parsed_content.get("conclusion", ""),
                            # Also include metadata for backwards compatibility
                            "has_abstract": bool(parsed_content.get("abstract")),
                            "has_methods": bool(parsed_content.get("methods")),
                            "has_results": bool(parsed_content.get("results")),
                            "has_discussion": bool(parsed_content.get("discussion")),
                            "content_length": len(parsed_content.get("methods", ""))
                            + len(parsed_content.get("results", ""))
                            + len(parsed_content.get("discussion", "")),
                        }
                    )
                    logger.info(
                        f"   [OK] Added PMID {pub.pmid} with FULL CONTENT "
                        f"(abstract={len(parsed_content.get('abstract', ''))} chars, "
                        f"methods={len(parsed_content.get('methods', ''))} chars, "
                        f"results={len(parsed_content.get('results', ''))} chars)"
                    )

                    dataset.fulltext.append(fulltext_info)
                    added_count += 1
                else:
                    logger.warning(
                        f"   [ERROR] SKIPPING PMID {pub.pmid}: PDF parsing failed, not adding to fulltext"
                    )

            # Count papers by type
            citing_papers_count = sum(
                1 for f in dataset.fulltext if f.get("paper_type") == "citing"
            )
            original_papers_count = sum(
                1 for f in dataset.fulltext if f.get("paper_type") == "original"
            )

            logger.warning(
                f"[DATA] STEP 4 COMPLETE: Added {added_count} entries to fulltext "
                f"(citing={citing_papers_count}, original={original_papers_count}, "
                f"skipped {skipped_no_url} without URL, {skipped_no_pdf} without PDF)"
            )
            dataset.fulltext_count = len(dataset.fulltext)

            # More accurate status based on actual PDFs downloaded and parsed
            if dataset.fulltext_count == 0:
                # Differentiate between download failure and parse failure
                if total_successful > 0:
                    dataset.fulltext_status = (
                        "parse_failed"  # Downloaded but couldn't parse
                    )
                    logger.error(
                        f"[STATUS] Parse failed: {total_successful} PDFs downloaded but none could be parsed"
                    )
                else:
                    dataset.fulltext_status = "download_failed"  # Couldn't download
                    logger.error(
                        f"[STATUS] Download failed: No PDFs could be downloaded from any source"
                    )
            elif dataset.fulltext_count < total_papers:
                dataset.fulltext_status = "partial"
                logger.warning(
                    f"[STATUS] Partial: {dataset.fulltext_count}/{total_papers} papers processed"
                )
            else:
                dataset.fulltext_status = "available"
                logger.info(
                    f"[STATUS] Success: All {dataset.fulltext_count} papers processed"
                )

            logger.warning(
                f"[DATA] FINAL STATUS: fulltext_count={dataset.fulltext_count}/{total_papers}, "
                f"fulltext_status={dataset.fulltext_status}, "
                f"citing_papers={citing_papers_count}, original_papers={original_papers_count}"
            )

            # Store COMPREHENSIVE metadata about paper organization and URLs
            # This ensures frontend has ALL information needed for robust downloads/retries
            metadata_file = base_pdf_dir / "metadata.json"
            import json

            # Build detailed paper information with URLs
            def build_paper_metadata(papers, paper_type):
                """Extract comprehensive metadata for each paper"""
                paper_list = []
                for pub in papers:
                    paper_info = {
                        "pmid": pub.pmid if hasattr(pub, "pmid") else None,
                        "doi": pub.doi if hasattr(pub, "doi") else None,
                        "pmc_id": pub.pmcid if hasattr(pub, "pmcid") else None,
                        "title": pub.title if hasattr(pub, "title") else None,
                        "authors": pub.authors if hasattr(pub, "authors") else [],
                        "journal": pub.journal if hasattr(pub, "journal") else None,
                        "year": pub.year if hasattr(pub, "year") else None,
                        "paper_type": paper_type,
                        "pdf_path": str(pub.pdf_path)
                        if hasattr(pub, "pdf_path") and pub.pdf_path
                        else None,
                        "fulltext_source": pub.fulltext_source
                        if hasattr(pub, "fulltext_source")
                        else None,
                        "fulltext_url": pub.fulltext_url
                        if hasattr(pub, "fulltext_url")
                        else None,
                        # Store ALL collected URLs for retry capability
                        "all_urls": [],
                    }

                    # Get all URLs that were collected (for retry capability)
                    if hasattr(pub, "_all_collected_urls"):
                        paper_info["all_urls"] = [
                            {
                                "url": u.url,
                                "source": u.source.value,
                                "priority": u.priority,
                                "url_type": u.url_type.value
                                if u.url_type
                                else "unknown",  # NEW: Store URL type
                                "confidence": u.confidence,
                                "requires_auth": u.requires_auth,
                                "metadata": u.metadata or {},
                            }
                            for u in pub._all_collected_urls
                        ]

                    paper_list.append(paper_info)
                return paper_list

            # Build comprehensive metadata
            metadata = {
                # GEO Dataset Information
                "geo": {
                    "geo_id": dataset.geo_id,
                    "title": dataset.title,
                    "summary": dataset.summary,
                    "organism": dataset.organism,
                    "platform": dataset.platform,
                    "sample_count": dataset.sample_count,
                    "submission_date": dataset.submission_date,
                    "publication_date": dataset.publication_date,
                    "pubmed_ids": dataset.pubmed_ids,
                    "relevance_score": dataset.relevance_score,
                    "match_reasons": dataset.match_reasons,
                },
                # Processing Information
                "processing": {
                    "processed_at": datetime.now(timezone.utc).isoformat(),
                    "include_citing_papers": include_citing_papers,
                    "max_citing_papers": max_citing_papers,
                    "download_original": download_original,
                    "include_full_content": include_full_content,
                },
                # Papers with FULL metadata and URLs
                "papers": {
                    "original": {
                        "count": len(papers_to_download["original"]),
                        "downloaded": successful_downloads["original"],
                        "papers": build_paper_metadata(
                            papers_to_download["original"], "original"
                        ),
                    },
                    "citing": {
                        "count": len(papers_to_download["citing"]),
                        "downloaded": successful_downloads["citing"],
                        "papers": build_paper_metadata(
                            papers_to_download["citing"], "citing"
                        ),
                    },
                },
                # Download Statistics
                "statistics": {
                    "total_attempted": total_papers,
                    "total_successful": total_success,
                    "success_rate": round(total_success / total_papers * 100, 1)
                    if total_papers > 0
                    else 0,
                    "citing_papers_in_response": citing_papers_count,
                    "original_papers_in_response": original_papers_count,
                },
                # Status
                "status": {
                    "fulltext_status": dataset.fulltext_status,
                    "fulltext_count": dataset.fulltext_count,
                    "needs_retry": total_success
                    < total_papers,  # Flag if downloads failed
                },
            }

            # Store citation strategy breakdown if available
            if (
                hasattr(citation_result, "strategy_breakdown")
                if include_citing_papers and citation_discovery
                else False
            ):
                metadata["citation_discovery"] = {
                    "original_pmid": citation_result.original_pmid,
                    "strategy_a_count": len(
                        citation_result.strategy_breakdown.get("strategy_a", [])
                    ),
                    "strategy_b_count": len(
                        citation_result.strategy_breakdown.get("strategy_b", [])
                    ),
                    "total_found": len(citation_result.citing_papers),
                }

            with open(metadata_file, "w") as f:
                json.dump(metadata, f, indent=2)
            logger.info(f"[METADATA] Saved comprehensive metadata to {metadata_file}")
            logger.info(
                f"[METADATA] Frontend can use this file for robust downloads/retries"
            )

            # STEP 5: Store in centralized registry for O(1) frontend access
            logger.info("[REGISTRY] STEP 5: Storing data in centralized registry...")
            try:
                registry = get_registry()

                # Register GEO dataset
                registry.register_geo_dataset(dataset.geo_id, metadata["geo"])
                logger.info(f"  [OK] Registered GEO dataset: {dataset.geo_id}")

                # Register publications with ALL URLs
                for paper_type in ["original", "citing"]:
                    for paper in metadata["papers"][paper_type]["papers"]:
                        if paper["pmid"]:  # Only register if has PMID
                            # Store publication with URLs
                            registry.register_publication(
                                pmid=paper["pmid"],
                                metadata={
                                    "title": paper["title"],
                                    "authors": paper["authors"],
                                    "journal": paper["journal"],
                                    "year": paper["year"],
                                    "doi": paper["doi"],
                                    "pmc_id": paper["pmc_id"],
                                },
                                urls=paper["all_urls"],
                                doi=paper["doi"],
                            )

                            # Link to GEO dataset
                            citation_strategy = (
                                citation_result.strategy_breakdown.get(paper["pmid"])
                                if citation_result
                                and hasattr(citation_result, "strategy_breakdown")
                                else None
                            )
                            registry.link_geo_to_publication(
                                dataset.geo_id,
                                paper["pmid"],
                                relationship_type=paper_type,
                                citation_strategy=citation_strategy,
                            )

                            # Record download attempt
                            if paper["pdf_path"] and paper["fulltext_source"]:
                                # Success
                                registry.record_download_attempt(
                                    pmid=paper["pmid"],
                                    url=paper["fulltext_url"],
                                    source=paper["fulltext_source"],
                                    status="success",
                                    file_path=paper["pdf_path"],
                                    file_size=Path(paper["pdf_path"]).stat().st_size
                                    if Path(paper["pdf_path"]).exists()
                                    else None,
                                )
                            elif paper["all_urls"]:
                                # Failed - record all attempted URLs
                                for url_info in paper["all_urls"]:
                                    registry.record_download_attempt(
                                        pmid=paper["pmid"],
                                        url=url_info["url"],
                                        source=url_info["source"],
                                        status="failed",
                                        error_message="Download failed",
                                    )

                            logger.debug(
                                f"    [OK] Registered {paper_type} paper: PMID {paper['pmid']}"
                            )

                logger.info(
                    f"  [OK] Registry updated with complete data for {dataset.geo_id}"
                )

            except Exception as reg_error:
                logger.error(
                    f"  [ERROR] Failed to update registry: {reg_error}", exc_info=True
                )
                # Don't fail the whole enrichment if registry fails

            # STEP 6: Update dataset metrics for frontend display (Oct 15, 2025)
            # After enrichment, update citation_count, pdf_count, completion_rate
            # so the frontend card displays accurate "X/Y PDFs downloaded, Z% processed"
            logger.info("[METRICS] STEP 6: Updating dataset metrics for frontend...")
            try:
                # Count TOTAL papers (original + citing) from metadata
                original_count = len(metadata["papers"]["original"]["papers"])
                citing_count = len(metadata["papers"]["citing"]["papers"])
                total_papers = original_count + citing_count

                # Count how many have PDFs (from fulltext array)
                pdfs_downloaded = (
                    len([ft for ft in dataset.fulltext if ft.get("pdf_path")])
                    if dataset.fulltext
                    else 0
                )

                # Calculate completion rate (if we have full content, it's processed)
                completion = (
                    (pdfs_downloaded / total_papers * 100) if total_papers > 0 else 0.0
                )

                # Update dataset metrics (total citations = original + citing papers)
                dataset.citation_count = total_papers
                dataset.pdf_count = pdfs_downloaded
                dataset.completion_rate = completion
                dataset.fulltext_count = pdfs_downloaded  # Ensure this is also set

                logger.info(
                    f"  [OK] Metrics updated: {pdfs_downloaded}/{total_papers} PDFs, "
                    f"{completion:.0f}% complete "
                    f"(original={original_count}, citing={citing_count})"
                )

            except Exception as metrics_error:
                logger.warning(f"  [WARNING] Could not update metrics: {metrics_error}")

            enriched_datasets.append(dataset)

            # Log statistics (same as pipeline)
            stats = fulltext_manager.get_statistics()
            logger.info(f"Sources used: {stats.get('by_source', {})}")

        execution_time_ms = (time.time() - start_time) * 1000
        logger.info(
            f"Enriched {len(enriched_datasets)} datasets in {execution_time_ms:.2f}ms"
        )

        return enriched_datasets

    except Exception as e:
        logger.error(f"Full-text enrichment failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Enrichment error: {str(e)}",
        )
    finally:
        # Clean up aiohttp sessions to prevent resource leaks
        try:
            if fulltext_manager:
                await fulltext_manager.cleanup()
                logger.debug("Cleaned up fulltext_manager resources")
        except Exception as cleanup_error:
            logger.warning(f"Error during cleanup: {cleanup_error}")


# AI Analysis Endpoint


class QueryProcessingContext(BaseModel):
    """Context from query processing pipeline."""

    extracted_entities: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Entities extracted by entity type (GENE, DISEASE, ORGANISM, etc.)",
    )
    expanded_terms: List[str] = Field(
        default_factory=list, description="Expanded search terms and synonyms"
    )
    geo_search_terms: List[str] = Field(
        default_factory=list, description="Actual search terms used in GEO query"
    )
    search_intent: Optional[str] = Field(None, description="Detected search intent")
    query_type: Optional[str] = Field(
        None, description="Query type (gene-focused, disease-focused, etc.)"
    )


class MatchExplanation(BaseModel):
    """Explanation of why a dataset matched the query."""

    matched_terms: List[str] = Field(
        default_factory=list, description="Terms that matched in this dataset"
    )
    relevance_score: float = Field(..., description="Relevance score (0-1)")
    match_type: str = Field(
        default="unknown",
        description="Type of match (exact, synonym, expanded, semantic)",
    )
    confidence: float = Field(default=0.0, description="Confidence in the match (0-1)")


class AIAnalysisRequest(BaseModel):
    """Request for AI analysis of datasets."""

    datasets: List[DatasetResponse] = Field(..., description="Datasets to analyze")
    query: str = Field(..., description="Original search query for context")
    max_datasets: int = Field(
        default=5, ge=1, le=10, description="Max datasets to analyze"
    )
    # RAG Phase 1: Enhanced context
    query_processing: Optional[QueryProcessingContext] = Field(
        None, description="Query processing context (entities, synonyms, search terms)"
    )
    match_explanations: Optional[Dict[str, MatchExplanation]] = Field(
        None, description="Explanation of why each dataset matched (keyed by geo_id)"
    )


class AIAnalysisResponse(BaseModel):
    """Response from AI analysis."""

    model_config = {"protected_namespaces": ()}

    success: bool = Field(..., description="Whether analysis succeeded")
    execution_time_ms: float = Field(..., description="Execution time in milliseconds")
    timestamp: datetime = Field(..., description="Response timestamp")
    query: str = Field(..., description="Original query")
    analysis: str = Field(..., description="AI-generated analysis")
    insights: List[str] = Field(default_factory=list, description="Key insights")
    recommendations: List[str] = Field(
        default_factory=list, description="Recommendations"
    )
    model_used: str = Field(default="", description="LLM model used")


@router.post(
    "/analyze", response_model=AIAnalysisResponse, summary="AI Analysis of Datasets"
)
async def analyze_datasets(
    request: AIAnalysisRequest,
):
    """
    Use AI to analyze and provide insights on search results.

    This endpoint uses GPT-4 or other LLMs to:
    - Explain which datasets are most relevant
    - Compare datasets and their methodologies
    - Provide scientific context and insights
    - Recommend which datasets to use for specific research goals

    **Note:** Requires OpenAI API key to be configured (OPENAI_API_KEY)

    Args:
        request: Analysis request with datasets and query context

    Returns:
        AIAnalysisResponse: AI-generated analysis and insights
    """
    try:
        from omics_oracle_v2.api.dependencies import get_settings
        from omics_oracle_v2.services.analysis_service import AnalysisService

        settings = get_settings()
        service = AnalysisService()

        return await service.analyze_datasets(request, settings)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI analysis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis error: {str(e)}",
        )


@router.get(
    "/geo/{geo_id}/complete",
    summary="Get Complete GEO Data",
    description="""
    Get complete data for a GEO dataset including:
    - GEO metadata (title, organism, platform, etc.)
    - All papers (original and citing)
    - All URLs for each paper (for retry capability)
    - Download history and statistics

    This endpoint provides a single source of truth for the frontend
    "Download Papers" button, ensuring robust downloads and retries.

    Data is retrieved from the centralized registry (O(1) lookup).
    """,
)
async def get_complete_geo_data(geo_id: str):
    """
    Get complete GEO data from registry.

    Args:
        geo_id: GEO accession (e.g., GSE12345)

    Returns:
        Complete data including GEO metadata, papers, URLs, and download history
    """
    try:
        logger.info(f"[REGISTRY] Getting complete data for {geo_id}")

        registry = get_registry()
        data = registry.get_complete_geo_data(geo_id)

        if not data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"GEO dataset {geo_id} not found in registry. Have you enriched it yet?",
            )

        logger.info(
            f"[OK] Retrieved data for {geo_id}: "
            f"{data['statistics']['total_papers']} papers, "
            f"{data['statistics']['original_papers']} original, "
            f"{data['statistics']['citing_papers']} citing"
        )

        return data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get complete GEO data: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registry error: {str(e)}",
        )
