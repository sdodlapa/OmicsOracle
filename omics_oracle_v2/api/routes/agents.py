"""
Agent Execution Routes

REST endpoints for executing individual agents.
"""

import logging
import time
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from omics_oracle_v2.agents import DataAgent, QueryAgent, ReportAgent
from omics_oracle_v2.agents.models import QueryInput
from omics_oracle_v2.agents.models.data import DataInput
from omics_oracle_v2.agents.models.report import ReportInput
from omics_oracle_v2.agents.models.search import RankedDataset  # Keep for response building
from omics_oracle_v2.api.dependencies import get_data_agent, get_query_agent, get_report_agent
from omics_oracle_v2.api.models.requests import (
    DataValidationRequest,
    QueryRequest,
    ReportRequest,
    SearchRequest,
)
from omics_oracle_v2.api.models.responses import (
    DatasetResponse,
    DataValidationResponse,
    EntityResponse,
    PublicationResponse,
    QualityMetricsResponse,
    QueryResponse,
    ReportResponse,
    SearchResponse,
    ValidatedDatasetResponse,
)
from omics_oracle_v2.auth.dependencies import get_current_user
from omics_oracle_v2.auth.models import User
from omics_oracle_v2.lib.geo.models import GEOSeriesMetadata
from omics_oracle_v2.lib.pipelines.unified_search_pipeline import OmicsSearchPipeline, UnifiedSearchConfig

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Agents"])


# Agent Information Schemas


class AgentInfo(BaseModel):
    """Information about an available agent."""

    id: str = Field(..., description="Agent identifier")
    name: str = Field(..., description="Human-readable agent name")
    description: str = Field(..., description="Agent description")
    category: str = Field(..., description="Agent category")
    capabilities: List[str] = Field(..., description="List of agent capabilities")
    input_types: List[str] = Field(..., description="Accepted input types")
    output_types: List[str] = Field(..., description="Produced output types")
    endpoint: str = Field(..., description="API endpoint path")


# Agent Listing


@router.get("/", response_model=List[AgentInfo], summary="List Available Agents")
async def list_agents(current_user: User = Depends(get_current_user)):
    """
    List all available agents with their metadata.

    Requires authentication.

    Returns comprehensive information about each agent including
    capabilities, input/output types, and API endpoints.

    Returns:
        List of agent information objects
    """
    return [
        AgentInfo(
            id="query",
            name="Query Agent",
            description="Extract biomedical entities and intent from natural language queries",
            category="NLP",
            capabilities=[
                "Named Entity Recognition (NER)",
                "Intent Detection",
                "Entity Extraction (genes, diseases, chemicals, etc.)",
                "Search Term Generation",
            ],
            input_types=["text/plain"],
            output_types=["application/json"],
            endpoint="/api/v1/agents/query",
        ),
        AgentInfo(
            id="search",
            name="Search Agent",
            description="Search and rank GEO datasets based on relevance",
            category="Data Discovery",
            capabilities=[
                "GEO Database Search",
                "Relevance Ranking",
                "Dataset Filtering",
                "Metadata Extraction",
            ],
            input_types=["application/json"],
            output_types=["application/json"],
            endpoint="/api/v1/agents/search",
        ),
        AgentInfo(
            id="data",
            name="Data Agent",
            description="Validate, integrate, and process biomedical datasets",
            category="Data Processing",
            capabilities=[
                "Data Validation",
                "Quality Assessment",
                "Data Integration",
                "Format Conversion",
            ],
            input_types=["application/json", "text/csv"],
            output_types=["application/json"],
            endpoint="/api/v1/agents/data",
        ),
        AgentInfo(
            id="report",
            name="Report Agent",
            description="Generate comprehensive analysis reports",
            category="Reporting",
            capabilities=[
                "Report Generation",
                "Data Summarization",
                "Visualization",
                "Export to Multiple Formats",
            ],
            input_types=["application/json"],
            output_types=["application/json", "text/html", "application/pdf"],
            endpoint="/api/v1/agents/report",
        ),
    ]


# Agent Execution Endpoints


@router.post("/query", response_model=QueryResponse, summary="Execute Query Agent")
async def execute_query_agent(
    request: QueryRequest,
    current_user: User = Depends(get_current_user),
    agent: QueryAgent = Depends(get_query_agent),
):
    """
    Execute the Query Agent to extract entities and generate search terms.

    This endpoint processes a natural language query to:
    - Extract biomedical entities (genes, diseases, chemicals, etc.)
    - Detect research intent
    - Generate optimized search terms

    Args:
        request: Query request containing the natural language query

    Returns:
        QueryResponse: Extracted entities, intent, and search terms
    """
    start_time = time.time()

    try:
        # Execute agent
        query_input = QueryInput(query=request.query)
        result = agent.execute(query_input)

        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Query processing failed: {result.error}",
            )

        output = result.output

        # Convert entities to response format
        entities = [
            EntityResponse(
                text=entity.text,
                entity_type=entity.entity_type.value,
                confidence=entity.confidence,
            )
            for entity in output.entities
        ]

        execution_time_ms = (time.time() - start_time) * 1000

        return QueryResponse(
            success=True,
            execution_time_ms=execution_time_ms,
            timestamp=datetime.now(timezone.utc),
            original_query=output.original_query,
            intent=output.intent,
            confidence=output.confidence,
            entities=entities,
            search_terms=output.search_terms,
            entity_counts=output.entity_counts,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Query agent execution failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query processing error: {str(e)}",
        )


@router.post("/search", response_model=SearchResponse, summary="Search Datasets and Publications")
async def execute_search(
    request: SearchRequest,
):
    """
    Search for datasets and publications using the unified OmicsSearchPipeline.

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
        # Initialize unified pipeline
        search_logs.append("📝 Using unified search pipeline with query optimization")
        logger.info("Initializing OmicsSearchPipeline")

        # Build search config
        config = UnifiedSearchConfig(
            enable_geo_search=True,
            enable_publication_search=True,
            max_geo_results=request.max_results,
            max_publication_results=50,
            enable_caching=True,
            enable_query_optimization=not request.enable_semantic,  # Use optimization unless semantic mode
        )

        pipeline = OmicsSearchPipeline(config)

        # Build query from search terms
        original_query = " ".join(request.search_terms)
        search_logs.append(f"🔍 Original query: '{original_query}'")
        logger.info(f"Search request: '{original_query}' (semantic={request.enable_semantic})")

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
            search_logs.append(f"🎯 Query with filters: '{query}'")

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
            search_logs.append("🔄 Query type: HYBRID (GEO + Publications)")
        else:
            search_logs.append(f"📊 Query type: {query_type}")

        if search_result.optimized_query and search_result.optimized_query != original_query:
            search_logs.append(f"🔧 Optimized query: '{search_result.optimized_query}'")
        else:
            search_logs.append("ℹ️ Query used as-is (no optimization needed)")

        if search_result.cache_hit:
            search_logs.append("⚡ Cache hit - results returned from cache")
        else:
            search_logs.append("🔄 Fresh search - results fetched from sources")

        search_logs.append(f"⏱️ Pipeline search time: {search_result.search_time_ms:.2f}ms")

        # Extract GEO datasets
        geo_datasets = search_result.geo_datasets
        search_logs.append(f"📦 Raw GEO datasets fetched: {len(geo_datasets)}")

        # Apply min_samples filter if specified
        min_samples = request.filters.get("min_samples") if request.filters else None
        if min_samples:
            min_samples_int = int(min_samples)
            geo_datasets = [d for d in geo_datasets if d.sample_count and d.sample_count >= min_samples_int]
            filters_applied["min_samples"] = str(min_samples_int)
            search_logs.append(f"� After min_samples={min_samples_int} filter: {len(geo_datasets)}")
            logger.info(f"Filtered by min_samples={min_samples_int}: {len(geo_datasets)} remain")

        # Simple ranking by keyword relevance
        ranked_datasets = []
        search_terms_lower = {term.lower() for term in request.search_terms}

        for dataset in geo_datasets:
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
            summary_matches = sum(1 for term in search_terms_lower if term in summary_lower)
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
                RankedDataset(dataset=dataset, relevance_score=score, match_reasons=reasons)
            )

        # Sort by relevance (highest first)
        ranked_datasets.sort(key=lambda d: d.relevance_score, reverse=True)
        search_logs.append(f"📊 After ranking: {len(ranked_datasets)} datasets")

        # Extract publications
        publications = search_result.publications
        search_logs.append(f"📄 Found {len(publications)} related publications")

        # Add search mode to filters
        filters_applied["search_mode"] = search_result.query_type
        filters_applied["cache_hit"] = str(search_result.cache_hit)
        filters_applied["optimized"] = str(search_result.optimized_query != original_query)

        # Add result counts
        search_logs.append(
            f"✅ Total results: {len(ranked_datasets)} datasets, {len(publications)} publications"
        )

        # Convert datasets to response format
        datasets = [
            DatasetResponse(
                geo_id=ranked.dataset.geo_id,
                title=ranked.dataset.title,
                summary=ranked.dataset.summary,
                organism=ranked.dataset.organism,
                sample_count=ranked.dataset.sample_count,
                platform=ranked.dataset.platforms[0] if ranked.dataset.platforms else None,
                relevance_score=ranked.relevance_score,
                match_reasons=ranked.match_reasons,
                publication_date=ranked.dataset.publication_date,
                submission_date=ranked.dataset.submission_date,
                pubmed_ids=ranked.dataset.pubmed_ids,
            )
            for ranked in ranked_datasets
        ]

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
                        fulltext_available=hasattr(pub, "full_text") and pub.full_text is not None,
                        pdf_path=getattr(pub, "pdf_path", None),
                    )
                )

        execution_time_ms = (time.time() - start_time) * 1000
        search_logs.append(f"⏰ Total execution time: {execution_time_ms:.2f}ms")

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
    max_papers: int = 3,
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

    from omics_oracle_v2.lib.fulltext.manager import FullTextManager, FullTextManagerConfig
    from omics_oracle_v2.lib.publications.clients.pubmed import PubMedClient, PubMedConfig
    from omics_oracle_v2.lib.storage.pdf.download_manager import PDFDownloadManager

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
            download_pdfs=False,  # ⚠️ CRITICAL: DO NOT download here, we use PDFDownloadManager instead
            unpaywall_email=os.getenv("UNPAYWALL_EMAIL", "research@omicsoracle.ai"),
            core_api_key=os.getenv("CORE_API_KEY"),
        )
        fulltext_manager = FullTextManager(fulltext_config)

        # Initialize PDFDownloadManager (for actually downloading and validating PDFs)
        pdf_downloader = PDFDownloadManager(
            max_concurrent=3, max_retries=2, timeout_seconds=30, validate_pdf=True
        )

        # Initialize PubMed client for metadata fetching
        pubmed_client = PubMedClient(PubMedConfig(email=os.getenv("NCBI_EMAIL", "research@omicsoracle.ai")))

        # Initialize manager
        if not fulltext_manager.initialized:
            await fulltext_manager.initialize()

        enriched_datasets = []

        for dataset in datasets:
            if not dataset.pubmed_ids:
                logger.warning(f"Dataset {dataset.geo_id} has no PubMed IDs")
                enriched_datasets.append(dataset)
                continue

            # Limit to max_papers
            pmids_to_fetch = dataset.pubmed_ids[:max_papers]
            logger.info(f"Enriching {dataset.geo_id} with {len(pmids_to_fetch)} PMIDs...")

            # Fetch full metadata from PubMed (gets DOI, PMC ID, etc.)
            publications = []
            for pmid in pmids_to_fetch:
                try:
                    pub = pubmed_client.fetch_by_id(pmid)
                    if pub:
                        publications.append(pub)
                        logger.info(f"✅ Fetched metadata for PMID {pmid}: DOI={pub.doi}, PMC={pub.pmcid}")
                except Exception as e:
                    logger.error(f"Error fetching metadata for PMID {pmid}: {e}")

            if not publications:
                logger.warning(f"No publications fetched for {dataset.geo_id}")
                enriched_datasets.append(dataset)
                continue

            # STEP 1: Get URLs from all sources (same as pipeline)
            logger.info(f"� Finding full-text URLs for {len(publications)} publications from all sources...")
            fulltext_results = await fulltext_manager.get_fulltext_batch(publications)

            # DEBUG: Log all fulltext results
            logger.warning(f"📊 FULLTEXT RESULTS: Received {len(fulltext_results)} results")
            for idx, (pub, result) in enumerate(zip(publications, fulltext_results)):
                logger.warning(
                    f"   [{idx+1}] PMID {pub.pmid}: success={result.success}, source={result.source.value if result.success else 'NONE'}, has_url={bool(result.url)}"
                )

            # STEP 2: Set fulltext_url on publications for PDFDownloadManager
            logger.warning(f"🔗 STEP 2: Setting fulltext URLs on publication objects...")
            urls_set = 0
            for pub, result in zip(publications, fulltext_results):
                if result.success and result.url:
                    pub.fulltext_url = result.url
                    pub.fulltext_source = result.source.value
                    urls_set += 1
                    logger.warning(f"   ✅ PMID {pub.pmid}: URL set from {result.source.value}")
                else:
                    logger.warning(
                        f"   ❌ PMID {pub.pmid}: NO URL (success={result.success}, url={bool(result.url)})"
                    )
            logger.warning(f"📊 STEP 2 COMPLETE: Set URLs on {urls_set}/{len(publications)} publications")

            # STEP 3: Download PDFs with waterfall retry on failure
            logger.info(f"🔍 STEP 3: Preparing to download PDFs with waterfall fallback...")
            publications_with_urls = [
                p for p in publications if hasattr(p, "fulltext_url") and p.fulltext_url
            ]
            logger.info(f"   Found {len(publications_with_urls)} publications with URLs")

            if publications_with_urls:
                logger.info(f"⬇️  Downloading {len(publications_with_urls)} PDFs using PDFDownloadManager...")
                pdf_dir = Path("data/fulltext/pdfs")
                pdf_dir.mkdir(parents=True, exist_ok=True)

                # First attempt with initial URLs
                download_report = await pdf_downloader.download_batch(
                    publications=publications_with_urls, output_dir=pdf_dir, url_field="fulltext_url"
                )
                logger.warning(
                    f"📊 STEP 3A: First attempt - Downloaded {download_report.successful}/{download_report.total} PDFs"
                )

                # STEP 3B: WATERFALL RETRY - For failed downloads, try next sources
                failed_pubs = []
                for result in download_report.results:
                    if not result.success:
                        failed_pubs.append(result.publication)
                        logger.warning(
                            f"   � PMID {result.publication.pmid}: Will retry with next source (failed: {result.error})"
                        )

                if failed_pubs:
                    logger.warning(
                        f"🔄 STEP 3B: TIERED WATERFALL RETRY for {len(failed_pubs)} failed downloads..."
                    )
                    logger.warning(f"   Strategy: Keep trying ALL remaining sources until success")

                    # For each failed publication, try ALL remaining sources in waterfall
                    retry_successes = 0
                    for pub in failed_pubs:
                        tried_sources = [pub.fulltext_source] if hasattr(pub, "fulltext_source") else []
                        logger.warning(
                            f"   🔄 PMID {pub.pmid}: Starting waterfall retry (already tried: {', '.join(tried_sources)})"
                        )

                        # Keep trying until we get a successful download or run out of sources
                        max_attempts = 10  # Safety limit (we have 11 sources total)
                        attempt = 0
                        download_succeeded = False

                        while not download_succeeded and attempt < max_attempts:
                            attempt += 1

                            # Get next URL from waterfall, skipping all tried sources
                            retry_result = await fulltext_manager.get_fulltext(
                                pub, skip_sources=tried_sources
                            )

                            if not retry_result.success or not retry_result.url:
                                logger.warning(
                                    f"      ❌ Attempt {attempt}: No more sources available in waterfall"
                                )
                                break

                            # Found alternative - try downloading
                            current_source = retry_result.source.value
                            tried_sources.append(current_source)
                            pub.fulltext_url = retry_result.url
                            pub.fulltext_source = current_source
                            logger.warning(f"      🆕 Attempt {attempt}: Trying {current_source}")

                            # Try to download this single PDF
                            single_result = await pdf_downloader._download_single(
                                pub, retry_result.url, pdf_dir
                            )

                            if single_result.success and single_result.pdf_path:
                                pub.pdf_path = str(single_result.pdf_path)
                                retry_successes += 1
                                download_succeeded = True
                                logger.warning(
                                    f"      ✅ SUCCESS via {current_source}! Size: {single_result.file_size / 1024:.1f} KB"
                                )
                                # Add to results
                                download_report.results.append(single_result)
                            else:
                                logger.warning(
                                    f"      ⚠️  {current_source} failed: {single_result.error} - trying next source..."
                                )

                        if not download_succeeded:
                            logger.warning(
                                f"      ❌ EXHAUSTED: Tried {len(tried_sources)} sources, none succeeded"
                            )

                    if retry_successes > 0:
                        download_report.successful += retry_successes
                        download_report.failed -= retry_successes
                        logger.warning(
                            f"📊 RETRY COMPLETE: {retry_successes} additional PDFs downloaded from alternative sources"
                        )

                logger.warning(
                    f"✅ STEP 3 COMPLETE: Downloaded {download_report.successful}/{download_report.total} PDFs (including retries)"
                )

                # STEP 3C: Set pdf_path on publications from all download results
                logger.warning(f"🔍 STEP 3C: Setting pdf_path on publications from download results...")
                paths_set = 0
                for result in download_report.results:
                    if result.success and result.pdf_path:
                        result.publication.pdf_path = str(result.pdf_path)
                        paths_set += 1
                        logger.warning(
                            f"   ✅ PMID {result.publication.pmid}: pdf_path={result.pdf_path.name}, size={result.pdf_path.stat().st_size} bytes"
                        )
                    else:
                        logger.warning(
                            f"   ❌ PMID {result.publication.pmid}: Download FAILED after retry - {result.error}"
                        )
                logger.warning(
                    f"📊 STEP 3C COMPLETE: Set pdf_path on {paths_set}/{len(publications_with_urls)} publications"
                )
            else:
                logger.warning("❌ STEP 3 SKIPPED: No publications with URLs found")

            # STEP 4: Parse PDFs and attach to dataset
            logger.info(f"🔍 STEP 4: Parsing PDFs and building fulltext data...")
            dataset.fulltext = []
            added_count = 0
            skipped_no_url = 0
            skipped_no_pdf = 0

            for pub in publications:
                # Skip if no URL found
                if not hasattr(pub, "fulltext_url") or not pub.fulltext_url:
                    logger.debug(f"   Skipping PMID {pub.pmid}: no fulltext_url")
                    skipped_no_url += 1
                    continue

                # Try to get parsed content if PDF was downloaded
                parsed_content = None
                has_pdf = hasattr(pub, "pdf_path") and pub.pdf_path and Path(pub.pdf_path).exists()

                if has_pdf:
                    logger.info(f"📄 Parsing PDF for PMID {pub.pmid} from {pub.pdf_path}...")
                    try:
                        parsed_content = await fulltext_manager.get_parsed_content(pub)
                        logger.info(
                            f"   ✅ Parsed {Path(pub.pdf_path).stat().st_size // 1024} KB PDF: "
                            f"abstract={len(parsed_content.get('abstract', ''))} chars, "
                            f"methods={len(parsed_content.get('methods', ''))} chars"
                        )
                    except Exception as e:
                        logger.error(f"   ❌ Failed to parse PDF for {pub.pmid}: {e}")
                else:
                    logger.warning(
                        f"⚠️  PMID {pub.pmid}: No PDF file (pdf_path={getattr(pub, 'pdf_path', 'NOT SET')})"
                    )
                    skipped_no_pdf += 1
                    # CRITICAL FIX: Skip this publication - don't add URL-only entries!
                    logger.warning(
                        f"   ❌ SKIPPING PMID {pub.pmid}: No PDF downloaded, not counting as success"
                    )
                    continue

                # Build fulltext info - ONLY if we have parsed content
                fulltext_info = {
                    "pmid": pub.pmid,
                    "title": pub.title or (parsed_content.get("title") if parsed_content else pub.title),
                    "url": pub.fulltext_url,
                    "source": pub.fulltext_source if hasattr(pub, "fulltext_source") else "unknown",
                    "pdf_path": str(pub.pdf_path) if hasattr(pub, "pdf_path") and pub.pdf_path else None,
                }

                # Add parsed sections if available
                if parsed_content:
                    fulltext_info.update(
                        {
                            "abstract": parsed_content.get("abstract", ""),
                            "methods": parsed_content.get("methods", ""),
                            "results": parsed_content.get("results", ""),
                            "discussion": parsed_content.get("discussion", ""),
                            "introduction": parsed_content.get("introduction", ""),
                            "conclusion": parsed_content.get("conclusion", ""),
                        }
                    )
                    logger.warning(
                        f"   ✅ Added PMID {pub.pmid} with {len(parsed_content.get('abstract', ''))} char abstract"
                    )
                    dataset.fulltext.append(fulltext_info)
                    added_count += 1
                else:
                    logger.warning(
                        f"   ❌ SKIPPING PMID {pub.pmid}: PDF parsing failed, not adding to fulltext"
                    )

            logger.warning(
                f"📊 STEP 4 COMPLETE: Added {added_count} entries to fulltext (skipped {skipped_no_url} without URL, {skipped_no_pdf} without PDF)"
            )
            dataset.fulltext_count = len(dataset.fulltext)

            # More accurate status based on actual PDFs downloaded
            if dataset.fulltext_count == 0:
                dataset.fulltext_status = "failed"
            elif dataset.fulltext_count < len(publications):
                dataset.fulltext_status = "partial"
            else:
                dataset.fulltext_status = "available"

            logger.warning(
                f"📊 FINAL STATUS: fulltext_count={dataset.fulltext_count}/{len(publications)}, fulltext_status={dataset.fulltext_status}"
            )
            enriched_datasets.append(dataset)

            # Log statistics (same as pipeline)
            stats = fulltext_manager.get_statistics()
            logger.info(f"Sources used: {stats.get('by_source', {})}")

        execution_time_ms = (time.time() - start_time) * 1000
        logger.info(f"Enriched {len(enriched_datasets)} datasets in {execution_time_ms:.2f}ms")

        return enriched_datasets

    except Exception as e:
        logger.error(f"Full-text enrichment failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Enrichment error: {str(e)}",
        )


@router.post(
    "/validate",
    response_model=DataValidationResponse,
    summary="Execute Data Agent",
)
async def execute_data_agent(
    request: DataValidationRequest,
    current_user: User = Depends(get_current_user),
    agent: DataAgent = Depends(get_data_agent),
):
    """
    Execute the Data Agent to validate dataset quality.

    This endpoint validates GEO datasets by checking:
    - Data quality metrics
    - Publication availability
    - SRA data presence
    - Dataset age

    Args:
        request: Validation request with dataset IDs

    Returns:
        DataValidationResponse: Validated datasets with quality scores
    """
    start_time = time.time()

    try:
        # First need to fetch the datasets
        # For now, create minimal RankedDataset objects with just IDs
        # In production, you'd fetch full metadata first
        from omics_oracle_v2.agents.models.search import GEOSeriesMetadata

        ranked_datasets = []
        for geo_id in request.dataset_ids:
            metadata = GEOSeriesMetadata(
                geo_id=geo_id,
                title=f"Dataset {geo_id}",
                summary="",
                organism="",
                sample_count=0,
                submission_date="",
                pubmed_ids=[],
            )
            ranked_datasets.append(
                RankedDataset(
                    dataset=metadata,
                    relevance_score=1.0,
                    match_reasons=["Direct ID match"],
                )
            )

        # Execute agent
        data_input = DataInput(datasets=ranked_datasets)
        result = agent.execute(data_input)

        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Data validation failed: {result.error}",
            )

        output = result.output

        # Convert to response format
        validated = []
        for processed in output.processed_datasets:
            # Convert age_days to age_years
            age_years = processed.age_days / 365.25 if processed.age_days else 0.0

            quality_metrics = QualityMetricsResponse(
                quality_score=processed.quality_score,
                quality_level=processed.quality_level,
                has_publication=processed.has_publication,
                has_sra_data=processed.has_sra_data,
                age_years=age_years,
            )

            validated.append(
                ValidatedDatasetResponse(
                    geo_id=processed.geo_id,
                    title=processed.title,
                    summary=processed.summary,
                    organism=processed.organism,
                    sample_count=processed.sample_count,
                    platform="",  # ProcessedDataset doesn't have platform field
                    relevance_score=processed.relevance_score,
                    match_reasons=[],  # Not available in ProcessedDataset
                    quality_metrics=quality_metrics,
                )
            )

        execution_time_ms = (time.time() - start_time) * 1000

        # Create quality stats dict from DataOutput fields
        quality_stats = {
            "total_processed": output.total_processed,
            "total_passed_quality": output.total_passed_quality,
            "average_quality_score": output.average_quality_score,
            "quality_distribution": output.quality_distribution,
        }

        return DataValidationResponse(
            success=True,
            execution_time_ms=execution_time_ms,
            timestamp=datetime.now(timezone.utc),
            total_processed=output.total_processed,
            validated_datasets=validated,
            quality_stats=quality_stats,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Data agent execution failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Data validation error: {str(e)}",
        )


@router.post("/report", response_model=ReportResponse, summary="Execute Report Agent")
async def execute_report_agent(
    request: ReportRequest,
    current_user: User = Depends(get_current_user),
    agent: ReportAgent = Depends(get_report_agent),
):
    """
    Execute the Report Agent to generate analysis reports.

    This endpoint generates AI-powered reports analyzing datasets,
    including key findings and recommendations.

    Args:
        request: Report request with dataset IDs and preferences

    Returns:
        ReportResponse: Generated report with findings and recommendations
    """
    start_time = time.time()

    try:
        # Create minimal dataset objects for report generation
        from omics_oracle_v2.agents.models.data import ProcessedDataset

        processed_datasets = []
        for geo_id in request.dataset_ids:
            # Create minimal ProcessedDataset for report generation
            processed_datasets.append(
                ProcessedDataset(
                    geo_id=geo_id,
                    title=f"Dataset {geo_id}",
                    summary="",
                    organism="",
                    sample_count=0,
                    platform_count=1,
                    submission_date="",
                    publication_date="",
                    age_days=730,  # ~2 years
                    pubmed_ids=[],
                    has_publication=True,
                    has_sra_data=True,
                    sra_run_count=0,
                    quality_score=0.8,
                    quality_level="good",
                    quality_issues=[],
                    quality_strengths=[],
                    relevance_score=1.0,
                    metadata_completeness=0.7,
                )
            )

        # Execute agent
        report_input = ReportInput(
            datasets=processed_datasets,
            report_type=request.report_type,
            output_format=request.report_format,
            include_recommendations=request.include_recommendations,
        )
        result = agent.execute(report_input)

        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Report generation failed: {result.error}",
            )

        output = result.output

        execution_time_ms = (time.time() - start_time) * 1000

        return ReportResponse(
            success=True,
            execution_time_ms=execution_time_ms,
            timestamp=datetime.now(timezone.utc),
            report_type=output.report_type.value,
            report_format=output.report_format.value,
            full_report=output.full_report,
            key_findings=[insight.insight for insight in output.key_insights],
            recommendations=output.recommendations if request.include_recommendations else None,
            datasets_analyzed=output.total_datasets_analyzed,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Report agent execution failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Report generation error: {str(e)}",
        )


# AI Analysis Endpoint


class AIAnalysisRequest(BaseModel):
    """Request for AI analysis of datasets."""

    datasets: List[DatasetResponse] = Field(..., description="Datasets to analyze")
    query: str = Field(..., description="Original search query for context")
    max_datasets: int = Field(default=5, ge=1, le=10, description="Max datasets to analyze")


class AIAnalysisResponse(BaseModel):
    """Response from AI analysis."""

    model_config = {"protected_namespaces": ()}

    success: bool = Field(..., description="Whether analysis succeeded")
    execution_time_ms: float = Field(..., description="Execution time in milliseconds")
    timestamp: datetime = Field(..., description="Response timestamp")
    query: str = Field(..., description="Original query")
    analysis: str = Field(..., description="AI-generated analysis")
    insights: List[str] = Field(default_factory=list, description="Key insights")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations")
    model_used: str = Field(default="", description="LLM model used")


@router.post("/analyze", response_model=AIAnalysisResponse, summary="AI Analysis of Datasets")
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
        from omics_oracle_v2.lib.ai.client import SummarizationClient

        settings = get_settings()

        # Check if OpenAI is configured
        if not settings.ai.openai_api_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI analysis unavailable: OpenAI API key not configured. "
                "Set OPENAI_API_KEY environment variable.",
            )

        # Initialize AI client
        ai_client = SummarizationClient(settings=settings)

        # Limit datasets
        datasets_to_analyze = request.datasets[: request.max_datasets]

        # DEBUG: Log what we received
        for ds in datasets_to_analyze:
            logger.info(f"🔍 Dataset {ds.geo_id}: has {len(ds.fulltext) if ds.fulltext else 0} fulltext items")
            if ds.fulltext and len(ds.fulltext) > 0:
                for ft in ds.fulltext:
                    logger.info(
                        f"   📄 PMID {ft.pmid}: pdf_path={ft.pdf_path}, "
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
                dataset_info.append(
                    f"\n   📄 Full-text content from {len(ds.fulltext)} linked publication(s):"
                )
                total_fulltext_papers += len(ds.fulltext)

                for j, ft in enumerate(ds.fulltext[:2], 1):  # Max 2 papers per dataset to manage tokens
                    dataset_info.extend(
                        [
                            f"\n   Paper {j}: {ft.title[:100]}... (PMID: {ft.pmid})",
                            f"   Abstract: {ft.abstract[:250] if ft.abstract else 'N/A'}...",
                            f"   Methods: {ft.methods[:400] if ft.methods else 'N/A'}...",
                            f"   Results: {ft.results[:400] if ft.results else 'N/A'}...",
                            f"   Discussion: {ft.discussion[:250] if ft.discussion else 'N/A'}...",
                        ]
                    )
            else:
                dataset_info.append("   ⚠️ No full-text available (analyzing GEO summary only)")

            dataset_summaries.append("\n".join(dataset_info))

        # Build analysis prompt with full-text context
        fulltext_note = (
            f"\n\nIMPORTANT: You have access to full-text content from {total_fulltext_papers} scientific papers "
            f"(Methods, Results, Discussion sections). Use these to provide detailed, specific insights "
            f"about experimental design, methodologies, and key findings."
            if total_fulltext_papers > 0
            else "\n\nNote: Analysis based on GEO metadata only (no full-text papers available)."
        )

        analysis_prompt = f"""
User searched for: "{request.query}"

Found {len(datasets_to_analyze)} relevant datasets:

{chr(10).join(dataset_summaries)}{fulltext_note}

Analyze these datasets and provide:

1. **Overview**: Which datasets are most relevant to the user's query and why?
   {f"Reference specific findings from the Methods and Results sections." if total_fulltext_papers > 0 else ""}

2. **Comparison**: How do these datasets differ in methodology and scope?
   {f"Compare experimental approaches described in the Methods sections." if total_fulltext_papers > 0 else ""}

3. **Key Insights**: What are the main scientific findings or approaches?
   {f"Cite specific results and conclusions from the papers." if total_fulltext_papers > 0 else ""}

4. **Recommendations**: Which dataset(s) would you recommend for:
   - Basic understanding of the topic
   - Advanced analysis and replication
   - Method development

Write for a researcher who wants expert guidance on which datasets to use.
Be specific and cite dataset IDs (GSE numbers){f" and PMIDs" if total_fulltext_papers > 0 else ""}.
{f"Ground your analysis in the actual experimental details from the papers." if total_fulltext_papers > 0 else ""}
"""

        # Call LLM
        system_message = (
            "You are an expert bioinformatics advisor helping researchers understand "
            "and select genomics datasets. Provide clear, actionable insights."
        )

        analysis = ai_client._call_llm(prompt=analysis_prompt, system_message=system_message, max_tokens=800)

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
            elif line.strip() and (line.strip()[0].isdigit() or line.strip().startswith("-")):
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
