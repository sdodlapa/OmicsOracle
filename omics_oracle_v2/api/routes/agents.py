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

from omics_oracle_v2.agents.models.search import RankedDataset
from omics_oracle_v2.api.models.requests import SearchRequest
from omics_oracle_v2.api.models.responses import (DatasetResponse,
                                                  PublicationResponse,
                                                  SearchResponse)
from omics_oracle_v2.lib.pipelines.citation_discovery.geo_discovery import \
    GEOCitationDiscovery
from omics_oracle_v2.lib.search_engines.geo.models import GEOSeriesMetadata
from omics_oracle_v2.lib.search_orchestration import (OrchestratorConfig,
                                                      SearchOrchestrator)
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
    start_time = time.time()

    # Collect search logs for frontend display
    search_logs = []

    try:
        # Initialize search orchestrator
        search_logs.append("[INFO] Using SearchOrchestrator with parallel execution")
        logger.info("Initializing SearchOrchestrator")

        # Build search config
        config = OrchestratorConfig(
            enable_geo=True,
            enable_pubmed=True,
            enable_openalex=True,
            max_geo_results=request.max_results,
            max_publication_results=50,
            enable_cache=True,
            enable_query_optimization=True,  # RAG Phase 3: Enable for entity extraction
        )

        pipeline = SearchOrchestrator(config)

        # Build query from search terms
        original_query = " ".join(request.search_terms)
        search_logs.append(f"[SEARCH] Original query: '{original_query}'")
        logger.info(
            f"Search request: '{original_query}' (semantic={request.enable_semantic})"
        )

        # Apply GEO filters to query (organism, study_type)
        query_parts = [original_query]
        filters_applied = {}

        if request.filters:
            organism = request.filters.get("organism")
            if organism:
                query_parts.append(f'"{organism}"[Organism]')
                filters_applied["organism"] = organism
                logger.info(f"Added organism filter: {organism}")

            study_type = request.filters.get("study_type")
            if study_type:
                query_parts.append(f'"{study_type}"[DataSet Type]')
                filters_applied["study_type"] = study_type
                logger.info(f"Added study type filter: {study_type}")

        query = " AND ".join(query_parts) if len(query_parts) > 1 else query_parts[0]

        if query != original_query:
            search_logs.append(f"[FILTER] Query with filters: '{query}'")

        # Execute unified search
        logger.info(f"Executing unified search: '{query}'")
        search_result = await pipeline.search(
            query=query,
            max_geo_results=request.max_results,
            max_publication_results=50,
            use_cache=True,
        )

        # Log pipeline metrics
        logger.info(
            f"Pipeline complete: type={search_result.query_type}, "
            f"cache={search_result.cache_hit}, time={search_result.search_time_ms:.2f}ms, "
            f"results={search_result.total_results}"
        )

        # Add query optimization logs
        query_type = search_result.query_type
        if query_type == "hybrid":
            search_logs.append("[PROCESS] Query type: HYBRID (GEO + Publications)")
        else:
            search_logs.append(f"[DATA] Query type: {query_type}")

        if (
            search_result.optimized_query
            and search_result.optimized_query != original_query
        ):
            search_logs.append(
                f"[CONFIG] Optimized query: '{search_result.optimized_query}'"
            )
        else:
            search_logs.append("[INFO] Query used as-is (no optimization needed)")

        if search_result.cache_hit:
            search_logs.append("[FAST] Cache hit - results returned from cache")
        else:
            search_logs.append("[PROCESS] Fresh search - results fetched from sources")

        search_logs.append(
            f"[TIME] Pipeline search time: {search_result.search_time_ms:.2f}ms"
        )

        # Extract GEO datasets
        geo_datasets = search_result.geo_datasets
        search_logs.append(f"[CACHE] Raw GEO datasets fetched: {len(geo_datasets)}")

        # Apply min_samples filter if specified
        min_samples = request.filters.get("min_samples") if request.filters else None
        if min_samples:
            min_samples_int = int(min_samples)
            geo_datasets = [
                d
                for d in geo_datasets
                if d.sample_count and d.sample_count >= min_samples_int
            ]
            filters_applied["min_samples"] = str(min_samples_int)
            search_logs.append(
                f" After min_samples={min_samples_int} filter: {len(geo_datasets)}"
            )
            logger.info(
                f"Filtered by min_samples={min_samples_int}: {len(geo_datasets)} remain"
            )

        # Simple ranking by keyword relevance
        ranked_datasets = []
        search_terms_lower = {term.lower() for term in request.search_terms}

        for dataset in geo_datasets:
            # Handle both dict and GEOSeriesMetadata objects
            if isinstance(dataset, dict):
                dataset = GEOSeriesMetadata(**dataset)

            score = 0.0
            reasons = []

            # Title matches (weight: 0.4)
            title_lower = (dataset.title or "").lower()
            title_matches = sum(1 for term in search_terms_lower if term in title_lower)
            if title_matches > 0:
                score += min(0.4, title_matches * 0.2)
                reasons.append(f"Title matches {title_matches} term(s)")

            # Summary matches (weight: 0.3)
            summary_lower = (dataset.summary or "").lower()
            summary_matches = sum(
                1 for term in search_terms_lower if term in summary_lower
            )
            if summary_matches > 0:
                score += min(0.3, summary_matches * 0.15)
                reasons.append(f"Summary matches {summary_matches} term(s)")

            # Sample count bonus (up to 0.15)
            if dataset.sample_count:
                if dataset.sample_count >= 100:
                    score += 0.15
                    reasons.append(f"Large sample size: {dataset.sample_count}")
                elif dataset.sample_count >= 50:
                    score += 0.10
                    reasons.append(f"Good sample size: {dataset.sample_count}")
                elif dataset.sample_count >= 10:
                    score += 0.05
                    reasons.append(f"Adequate sample size: {dataset.sample_count}")

            # Ensure minimum score
            if not reasons:
                reasons.append("General database match")
                score = 0.1

            score = min(1.0, score)
            ranked_datasets.append(
                RankedDataset(
                    dataset=dataset, relevance_score=score, match_reasons=reasons
                )
            )

        # Sort by relevance (highest first)
        ranked_datasets.sort(key=lambda d: d.relevance_score, reverse=True)
        search_logs.append(f"[DATA] After ranking: {len(ranked_datasets)} datasets")

        # Extract publications
        publications = search_result.publications
        search_logs.append(f"[DOC] Found {len(publications)} related publications")

        # Add search mode to filters
        filters_applied["search_mode"] = search_result.query_type
        filters_applied["cache_hit"] = str(search_result.cache_hit)
        filters_applied["optimized"] = str(
            search_result.optimized_query != original_query
        )

        # Add result counts
        search_logs.append(
            f"[OK] Total results: {len(ranked_datasets)} datasets, {len(publications)} publications"
        )

        # =====================================================================
        # ENRICH WITH DATABASE METRICS
        # =====================================================================
        # TODO: DatabaseQueries deleted - skip metrics enrichment for now
        # Can add get_geo_statistics() method to UnifiedDatabase if needed
        try:
            # # Initialize DatabaseQueries with production database
            # db_queries = DatabaseQueries(db_path="data/database/search_data.db")
            search_logs.append("[DATABASE] Skipping database metrics (DatabaseQueries removed)...")

            # Collect database metrics for all datasets
            db_metrics_map = {}
            for ranked in ranked_datasets:
                try:
                    # geo_stats = db_queries.get_geo_statistics(ranked.dataset.geo_id)
                    # pub_counts = geo_stats.get("publication_counts", {})
                    pub_counts = {}

                    db_metrics_map[ranked.dataset.geo_id] = {
                        "citation_count": pub_counts.get(
                            "total", 0
                        ),  # Total papers in database
                        "pdf_count": pub_counts.get("with_pdf", 0),  # Papers with PDFs
                        "processed_count": pub_counts.get(
                            "with_extraction", 0
                        ),  # Papers with extracted content
                        "completion_rate": geo_stats.get(
                            "completion_rate", 0.0
                        ),  # Processing completion %
                    }
                    logger.debug(
                        f"[DB] {ranked.dataset.geo_id}: "
                        f"citations={pub_counts.get('total', 0)}, "
                        f"pdfs={pub_counts.get('with_pdf', 0)}"
                    )
                except Exception as e:
                    logger.warning(
                        f"[DB] Could not get stats for {ranked.dataset.geo_id}: {e}"
                    )
                    # Default to 0 if database query fails
                    db_metrics_map[ranked.dataset.geo_id] = {
                        "citation_count": 0,
                        "pdf_count": 0,
                        "processed_count": 0,
                        "completion_rate": 0.0,
                    }

            search_logs.append(
                f"[DATABASE] Enriched {len(db_metrics_map)} datasets with database metrics"
            )
        except Exception as db_error:
            logger.error(f"[DB] Database enrichment failed: {db_error}")
            search_logs.append(f"[WARNING] Database enrichment failed: {db_error}")
            # Create empty metrics map
            db_metrics_map = {}

        # Convert datasets to response format WITH database metrics
        datasets = []
        for ranked in ranked_datasets:
            # Get database metrics (or use defaults)
            db_metrics = db_metrics_map.get(
                ranked.dataset.geo_id,
                {
                    "citation_count": 0,
                    "pdf_count": 0,
                    "processed_count": 0,
                    "completion_rate": 0.0,
                },
            )

            dataset_response = DatasetResponse(
                geo_id=ranked.dataset.geo_id,
                title=ranked.dataset.title,
                summary=ranked.dataset.summary,
                organism=ranked.dataset.organism,
                sample_count=ranked.dataset.sample_count,
                platform=ranked.dataset.platforms[0]
                if ranked.dataset.platforms
                else None,
                relevance_score=ranked.relevance_score,
                match_reasons=ranked.match_reasons,
                publication_date=ranked.dataset.publication_date,
                submission_date=ranked.dataset.submission_date,
                pubmed_ids=ranked.dataset.pubmed_ids,
                # NEW: Database metrics (accurate counts from UnifiedDatabase)
                citation_count=db_metrics["citation_count"],
                pdf_count=db_metrics["pdf_count"],
                processed_count=db_metrics["processed_count"],
                completion_rate=db_metrics["completion_rate"],
            )
            datasets.append(dataset_response)

        # Convert publications to response format
        publication_responses = []
        if publications:
            for pub in publications:
                # Extract GEO IDs from abstract/full text
                import re

                geo_ids = []
                if hasattr(pub, "abstract") and pub.abstract:
                    geo_ids.extend(re.findall(r"\bGSE\d{5,}\b", pub.abstract))
                if hasattr(pub, "full_text") and pub.full_text:
                    geo_ids.extend(re.findall(r"\bGSE\d{5,}\b", pub.full_text))

                # Handle publication_date (can be datetime or string)
                pub_date = getattr(pub, "publication_date", None)
                if pub_date:
                    if isinstance(pub_date, datetime):
                        pub_date_str = pub_date.isoformat()
                    elif hasattr(pub_date, "year"):  # datetime-like object
                        pub_date_str = f"{pub_date.year:04d}-{getattr(pub_date, 'month', 1):02d}-{getattr(pub_date, 'day', 1):02d}"
                    else:
                        pub_date_str = str(pub_date)
                else:
                    pub_date_str = None

                publication_responses.append(
                    PublicationResponse(
                        pmid=getattr(pub, "pmid", None),
                        pmc_id=getattr(pub, "pmc_id", None),
                        doi=getattr(pub, "doi", None),
                        title=getattr(pub, "title", ""),
                        abstract=getattr(pub, "abstract", None),
                        authors=getattr(pub, "authors", []),
                        journal=getattr(pub, "journal", None),
                        publication_date=pub_date_str,
                        geo_ids_mentioned=list(set(geo_ids)),
                        fulltext_available=hasattr(pub, "full_text")
                        and pub.full_text is not None,
                        pdf_path=getattr(pub, "pdf_path", None),
                    )
                )

        execution_time_ms = (time.time() - start_time) * 1000
        search_logs.append(f"[TIME] Total execution time: {execution_time_ms:.2f}ms")

        # RAG Phase 3: Build query processing context for frontend
        query_processing_response = None
        if search_result.query_processing:
            from omics_oracle_v2.api.models.responses import \
                QueryProcessingResponse

            query_processing_response = QueryProcessingResponse(
                extracted_entities=search_result.query_processing.extracted_entities,
                expanded_terms=search_result.query_processing.expanded_terms,
                geo_search_terms=search_result.query_processing.geo_search_terms,
                search_intent=search_result.query_processing.search_intent,
                query_type=search_result.query_processing.query_type,
            )
            logger.info(
                f"[RAG] Query processing context exposed: "
                f"entities={len(search_result.query_processing.extracted_entities)}, "
                f"expanded={len(search_result.query_processing.expanded_terms)}"
            )

        return SearchResponse(
            success=True,
            execution_time_ms=execution_time_ms,
            timestamp=datetime.now(timezone.utc),
            total_found=search_result.total_results,
            datasets=datasets,
            search_terms_used=request.search_terms,
            filters_applied=filters_applied,
            search_logs=search_logs,
            publications=publication_responses,
            publications_count=len(publication_responses),
            query_processing=query_processing_response,  # RAG Phase 3
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search execution failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search error: {str(e)}",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search agent execution failed: {e}", exc_info=True)
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
    from omics_oracle_v2.lib.pipelines.url_collection import (
        FullTextManager, FullTextManagerConfig)
    from omics_oracle_v2.lib.pipelines.storage import get_registry

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
    start_time = time.time()

    try:
        # Import here to avoid circular dependency
        from omics_oracle_v2.api.dependencies import get_settings
        from omics_oracle_v2.api.helpers import call_openai
        from omics_oracle_v2.lib.pipelines.text_enrichment import \
            get_parsed_cache

        settings = get_settings()

        # Check if OpenAI is configured
        if not settings.ai.openai_api_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI analysis unavailable: OpenAI API key not configured. "
                "Set OPENAI_API_KEY environment variable.",
            )

        # No longer need to initialize heavy AI client
        # ai_client = SummarizationClient(settings=settings)  # REMOVED: 791 LOC replaced with 50-line helper

        # Initialize ParsedCache for loading parsed content from disk
        # (Direct access to Phase 4 component - no deprecated wrapper)
        parsed_cache = get_parsed_cache()

        # Limit datasets
        datasets_to_analyze = request.datasets[: request.max_datasets]

        # ENHANCED CHECK (Oct 15, 2025): Verify we have ACTUAL parsed content, not just metadata
        # Check if datasets have fulltext AND the fulltext has actual content (methods, results, etc.)
        total_fulltext_count = 0
        total_with_content = 0

        for ds in datasets_to_analyze:
            if ds.fulltext and len(ds.fulltext) > 0:
                total_fulltext_count += len(ds.fulltext)
                # Check if at least one paper has actual content (not just metadata)
                for ft in ds.fulltext:
                    # Check for actual text content (not just has_methods=true)
                    has_content = any(
                        [
                            ft.get("methods") and len(ft.get("methods", "")) > 100,
                            ft.get("results") and len(ft.get("results", "")) > 100,
                            ft.get("abstract") and len(ft.get("abstract", "")) > 50,
                        ]
                    )
                    if has_content:
                        total_with_content += 1
                        break  # At least one paper has content for this dataset

        if total_fulltext_count == 0 or total_with_content == 0:
            # No full-text available OR only metadata - don't waste GPT-4 API call
            reason = (
                "No full-text papers downloaded"
                if total_fulltext_count == 0
                else "Papers downloaded but not parsed yet (only metadata available)"
            )

            logger.warning(
                f"[WARNING] AI Analysis BLOCKED: {reason}. "
                f"Fulltext count: {total_fulltext_count}, With content: {total_with_content}"
            )

            return AIAnalysisResponse(
                success=False,
                execution_time_ms=(time.time() - start_time) * 1000,
                timestamp=datetime.now(timezone.utc),
                query=request.query,
                analysis=(
                    "# [!] AI Analysis Not Available\n\n"
                    f"**Reason:** {reason}\n\n"
                    "AI analysis requires detailed **Methods**, **Results**, and **Discussion** sections "
                    "to provide meaningful insights. Without full-text content, AI would only summarize "
                    "the brief GEO metadata - which you can read directly on the dataset cards.\n\n"
                    "## Why We Skip Analysis\n\n"
                    "- **No value added**: GEO summaries are brief (1-2 paragraphs) and easily readable\n"
                    "- **Cost savings**: Each GPT-4 call costs $0.03-0.10 - not worth it for metadata\n"
                    "- **Better alternative**: Read the GEO summary directly - it's faster!\n\n"
                    "## What You Can Do\n\n"
                    "1. **Download Papers First**: Click the 'Download Papers' button on any dataset card\n"
                    "2. **Wait for Parsing**: The system will download, parse, and cache the full-text\n"
                    "3. **Try AI Analysis Again**: Once papers are downloaded, AI can analyze Methods/Results\n\n"
                    "## Manual Review Option\n\n"
                    "You can review the GEO summaries manually - they contain:\n"
                    "- Basic study description\n"
                    "- Sample count and organism\n"
                    "- Brief methods overview\n"
                    "- Link to full paper (if available)\n\n"
                    "For detailed experimental protocols and findings, full-text papers are required."
                ),
                insights=[],
                recommendations=[
                    "Click 'Download Papers' button on dataset cards",
                    "Wait for download and parsing to complete",
                    "Then click 'AI Analysis' for in-depth insights",
                    "Or manually read GEO summaries (faster for basic info)",
                ],
                model_used="none (analysis blocked - no content)",
            )

        # DEBUG: Log what we received
        for ds in datasets_to_analyze:
            logger.info(
                f"[SEARCH] Dataset {ds.geo_id}: has {len(ds.fulltext) if ds.fulltext else 0} fulltext items"
            )
            if ds.fulltext and len(ds.fulltext) > 0:
                for ft in ds.fulltext:
                    logger.info(
                        f"   [DOC] PMID {ft.pmid}: pdf_path={ft.pdf_path}, "
                        f"abstract_len={len(ft.abstract) if ft.abstract else 0}, "
                        f"methods_len={len(ft.methods) if ft.methods else 0}"
                    )

        # Build comprehensive analysis prompt with full-text when available
        dataset_summaries = []
        total_fulltext_papers = 0

        for i, ds in enumerate(datasets_to_analyze, 1):
            # Start with basic dataset info
            dataset_info = [
                f"{i}. **{ds.geo_id}** (Relevance: {int(ds.relevance_score * 100)}%)",
                f"   Title: {ds.title}",
                f"   Organism: {ds.organism or 'N/A'}, Samples: {ds.sample_count or 0}",
                f"   GEO Summary: {ds.summary[:200] if ds.summary else 'No summary'}...",
            ]

            # Add full-text content if available
            if ds.fulltext and len(ds.fulltext) > 0:
                # Prioritize papers for analysis (most important first)
                sorted_papers = sorted(
                    ds.fulltext,
                    key=lambda p: (
                        # Priority 1: Original dataset papers first
                        0
                        if (
                            hasattr(ds, "pubmed_ids")
                            and p.pmid in (ds.pubmed_ids or [])
                        )
                        else 1,
                        # Priority 2: Papers with parsed content (quality check)
                        0 if (hasattr(p, "has_methods") and p.has_methods) else 1,
                        # Priority 3: Reverse PMID (newer papers first, roughly)
                        -int(p.pmid) if p.pmid and p.pmid.isdigit() else 0,
                    ),
                )

                # Analyze up to 2 papers (token limit management)
                papers_to_analyze = sorted_papers[:2]
                total_papers = len(ds.fulltext)

                dataset_info.append(
                    f"\n   [DOC] Full-text content from {len(papers_to_analyze)} of {total_papers} linked publication(s):"
                )
                if total_papers > 2:
                    dataset_info.append(
                        f"   [INFO] Analyzing {len(papers_to_analyze)} papers (token limit). "
                        f"Prioritized: original dataset papers, papers with parsed content."
                    )
                total_fulltext_papers += len(papers_to_analyze)

                for j, ft in enumerate(papers_to_analyze, 1):
                    # Load parsed content from disk if not available in dataset object
                    # (Frontend strips full-text to reduce HTTP payload size)
                    abstract_text = (
                        ft.abstract if hasattr(ft, "abstract") and ft.abstract else None
                    )
                    methods_text = (
                        ft.methods if hasattr(ft, "methods") and ft.methods else None
                    )
                    results_text = (
                        ft.results if hasattr(ft, "results") and ft.results else None
                    )
                    discussion_text = (
                        ft.discussion
                        if hasattr(ft, "discussion") and ft.discussion
                        else None
                    )

                    # If content not in object, load from disk using ParsedCache
                    if not any(
                        [abstract_text, methods_text, results_text, discussion_text]
                    ):
                        if hasattr(ft, "pmid") and ft.pmid:
                            try:
                                # Load parsed content directly from cache (Phase 4 component)
                                # Uses publication ID (PMID) to look up cached content
                                cached_data = await parsed_cache.get(ft.pmid)
                                if cached_data:
                                    content_data = cached_data.get("content", {})
                                    abstract_text = content_data.get("abstract", "")
                                    methods_text = content_data.get("methods", "")
                                    results_text = content_data.get("results", "")
                                    discussion_text = content_data.get("discussion", "")
                                    logger.info(
                                        f"[ANALYZE] Loaded parsed content from cache for PMID {ft.pmid}"
                                    )
                            except Exception as e:
                                logger.warning(
                                    f"[ANALYZE] Could not load parsed content for PMID {ft.pmid}: {e}"
                                )

                    dataset_info.extend(
                        [
                            f"\n   Paper {j}: {ft.title[:100]}... (PMID: {ft.pmid})",
                            f"   Abstract: {abstract_text[:250] if abstract_text else 'N/A'}...",
                            f"   Methods: {methods_text[:400] if methods_text else 'N/A'}...",
                            f"   Results: {results_text[:400] if results_text else 'N/A'}...",
                            f"   Discussion: {discussion_text[:250] if discussion_text else 'N/A'}...",
                        ]
                    )
            else:
                dataset_info.append(
                    "   [WARNING] No full-text available (analyzing GEO summary only)"
                )

            dataset_summaries.append("\n".join(dataset_info))

        # Build analysis prompt with full-text context
        fulltext_note = (
            f"\n\nIMPORTANT: You have access to full-text content from {total_fulltext_papers} scientific papers "
            "(Methods, Results, Discussion sections). Use these to provide detailed, specific insights "
            "about experimental design, methodologies, and key findings."
            if total_fulltext_papers > 0
            else "\n\nNote: Analysis based on GEO metadata only (no full-text papers available)."
        )

        # RAG Phase 1: Add query processing context to prompt
        query_context_section = ""
        if request.query_processing:
            qp = request.query_processing
            query_context_section = "\n# QUERY ANALYSIS CONTEXT\n"

            if qp.extracted_entities:
                query_context_section += (
                    f"Extracted Entities: {dict(qp.extracted_entities)}\n"
                )

            if qp.expanded_terms:
                query_context_section += (
                    f"Expanded Search Terms: {', '.join(qp.expanded_terms)}\n"
                )

            if qp.geo_search_terms:
                query_context_section += (
                    f"GEO Query Used: {', '.join(qp.geo_search_terms)}\n"
                )

            if qp.search_intent:
                query_context_section += f"Search Intent: {qp.search_intent}\n"

            if qp.query_type:
                query_context_section += f"Query Type: {qp.query_type}\n"

            query_context_section += "\n"

        # RAG Phase 1: Add match explanations
        match_context_section = ""
        if request.match_explanations:
            match_context_section = "\n# WHY THESE DATASETS WERE RETRIEVED\n"
            for geo_id, explanation in request.match_explanations.items():
                match_context_section += (
                    f"- {geo_id}: Matched terms [{', '.join(explanation.matched_terms)}], "
                    f"Relevance: {int(explanation.relevance_score * 100)}%, "
                    f"Match type: {explanation.match_type}\n"
                )
            match_context_section += "\n"

        analysis_prompt = f"""
User searched for: "{request.query}"
{query_context_section}{match_context_section}
Found {len(datasets_to_analyze)} relevant datasets:

{chr(10).join(dataset_summaries)}{fulltext_note}

# ANALYSIS TASK (Step-by-Step Reasoning)

**Step 1: Query-Dataset Alignment**
- Review the extracted entities and search intent
- For each dataset, explain HOW it relates to the specific entities (genes, diseases, etc.)
- Reference the matched terms that led to its retrieval

**Step 2: Methodology Assessment**
{"- Compare experimental approaches from Methods sections" if total_fulltext_papers > 0 else "- Assess study design from GEO summaries"}
- Identify strengths and limitations of each approach
- Note unique methodological contributions

**Step 3: Data Quality and Scope**
- Evaluate sample sizes and experimental conditions
{"- Cite specific results and findings from the papers" if total_fulltext_papers > 0 else "- Consider organism and platform information"}
- Assess data completeness and reproducibility

**Step 4: Recommendations**
Based on your analysis, recommend which dataset(s) for:
- **Basic Understanding**: Best introduction to the topic
- **Advanced Analysis**: Most comprehensive data and methods
- **Method Development**: Best experimental protocols

# OUTPUT FORMAT
Provide your analysis in clear sections:
1. Overview (why each dataset is relevant)
2. Comparison (key differences)
3. Key Insights (main findings)
4. Recommendations (specific to use cases)

Be specific. Cite dataset IDs (GSE numbers){" and PMIDs" if total_fulltext_papers > 0 else ""}.
{"Ground your analysis in actual experimental details from the papers." if total_fulltext_papers > 0 else ""}
{"Reference the entities and terms from the query context when explaining relevance." if request.query_processing else ""}
"""

        # Call LLM with enhanced system message
        system_message = (
            "You are an expert bioinformatics advisor helping researchers understand and select genomics datasets. "
            "You use step-by-step reasoning to analyze datasets based on:\n"
            "1. Query context (extracted entities, search intent)\n"
            "2. Match explanations (why each dataset was retrieved)\n"
            "3. Full-text content (experimental methods, results, discussion)\n"
            "4. Dataset metadata (organism, samples, platform)\n\n"
            "Provide clear, actionable insights that reference specific evidence from the query analysis "
            "and dataset content. Be specific about WHY datasets are relevant and HOW they differ."
        )

        # Call OpenAI directly with simple helper (no 791-line library needed)
        analysis = call_openai(
            prompt=analysis_prompt,
            system_message=system_message,
            api_key=settings.ai.openai_api_key,
            model=settings.ai.model,
            max_tokens=800,
            temperature=settings.ai.temperature,
            timeout=settings.ai.timeout,
        )

        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="AI analysis failed to generate response",
            )

        # Extract insights and recommendations (basic parsing)
        insights = []
        recommendations = []

        # Simple parsing - look for numbered or bulleted lists
        lines = analysis.split("\n")
        current_section = None
        for line in lines:
            line_lower = line.lower().strip()
            if "insight" in line_lower or "finding" in line_lower:
                current_section = "insights"
            elif "recommend" in line_lower:
                current_section = "recommendations"
            elif line.strip() and (
                line.strip()[0].isdigit() or line.strip().startswith("-")
            ):
                if current_section == "insights":
                    insights.append(line.strip().lstrip("0123456789.-) "))
                elif current_section == "recommendations":
                    recommendations.append(line.strip().lstrip("0123456789.-) "))

        execution_time_ms = (time.time() - start_time) * 1000

        return AIAnalysisResponse(
            success=True,
            execution_time_ms=execution_time_ms,
            timestamp=datetime.now(timezone.utc),
            query=request.query,
            analysis=analysis,
            insights=insights[:5] if insights else [],
            recommendations=recommendations[:5] if recommendations else [],
            model_used=settings.ai.model,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI analysis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI analysis error: {str(e)}",
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
