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

from omics_oracle_v2.agents import DataAgent, QueryAgent, ReportAgent, SearchAgent
from omics_oracle_v2.agents.models import QueryInput
from omics_oracle_v2.agents.models.data import DataInput
from omics_oracle_v2.agents.models.report import ReportInput
from omics_oracle_v2.agents.models.search import RankedDataset, SearchInput
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


@router.post("/search", response_model=SearchResponse, summary="Execute Search Agent")
async def execute_search_agent(
    request: SearchRequest,
):
    """
    Execute the Search Agent to find datasets in GEO database.

    This endpoint searches the NCBI GEO database using provided search terms
    and filters, returning ranked results.

    Supports two search modes:
    - **Keyword Search (default)**: Traditional GEO search with keyword matching
    - **Semantic Search**: AI-powered search with query expansion, hybrid ranking,
      and cross-encoder reranking (requires FAISS index)

    **Note:** This endpoint is public for demo purposes. No authentication required.

    Args:
        request: Search request with terms, filters, result limit, and semantic flag

    Returns:
        SearchResponse: Ranked dataset results with relevance scores
    """
    start_time = time.time()

    # Collect search logs for frontend display
    search_logs = []

    try:
        # Import here to avoid circular dependency
        from omics_oracle_v2.api.dependencies import get_settings

        settings = get_settings()
        agent = SearchAgent(settings=settings, enable_semantic=request.enable_semantic)

        # Log original query
        original_query = " ".join(request.search_terms)
        search_logs.append(f"🔍 Original query: '{original_query}'")
        logger.info(f"Search request: '{original_query}' (semantic={request.enable_semantic})")

        # Log semantic search status
        if request.enable_semantic:
            if agent.is_semantic_search_available():
                search_logs.append("✨ Using semantic search with AI-powered query expansion")
                logger.info("Using semantic search with query expansion and hybrid ranking")
            else:
                search_logs.append("⚠️ Semantic search unavailable, using keyword search")
                logger.warning(
                    "Semantic search requested but index unavailable, falling back to keyword search"
                )
        else:
            search_logs.append("📝 Using unified pipeline with query preprocessing")

        # Execute agent
        search_input = SearchInput(
            search_terms=request.search_terms,
            filters=request.filters or {},
            max_results=request.max_results,
        )
        result = agent.execute(search_input)

        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Search failed: {result.error}",
            )

        output = result.output

        # Extract search information from agent result metadata
        metadata = result.metadata if result.metadata else {}

        # Add detailed logging for debugging
        if "raw_geo_count" in metadata:
            search_logs.append(f"📦 Raw GEO datasets fetched: {metadata['raw_geo_count']}")

        if "filtered_count" in metadata:
            search_logs.append(f"🔍 After filtering: {metadata['filtered_count']}")

        if "ranked_count" in metadata:
            search_logs.append(f"📊 After ranking: {metadata['ranked_count']}")

        # Add query optimization logs from metadata
        if "query_type" in metadata:
            query_type = metadata["query_type"]
            if query_type == "hybrid":
                search_logs.append("🔄 Query type: HYBRID (GEO + Publications)")
            else:
                search_logs.append(f"📊 Query type: {query_type}")

        # Add hybrid search stats
        if "hybrid_mode" in metadata and metadata["hybrid_mode"]:
            geo_from_pubs = metadata.get("geo_from_publications_count", 0)
            geo_direct = metadata.get("geo_direct_count", 0)
            search_logs.append(f"🔗 Hybrid search: {geo_direct} direct + {geo_from_pubs} from publications")

        if "optimized_query" in metadata:
            optimized = metadata["optimized_query"]
            if optimized != original_query:
                search_logs.append(f"🔧 Optimized query: '{optimized}'")
            else:
                search_logs.append("ℹ️ Query used as-is (no optimization needed)")

        if "cache_hit" in metadata:
            if metadata["cache_hit"]:
                search_logs.append("⚡ Cache hit - results returned from cache")
            else:
                search_logs.append("🔄 Fresh search - results fetched from GEO")

        if "search_time_ms" in metadata:
            search_time = metadata["search_time_ms"]
            search_logs.append(f"⏱️ Search time: {search_time:.2f}ms")

        # Add result counts
        search_logs.append(f"✅ Found {output.total_found} datasets total")
        if output.publications_count > 0:
            search_logs.append(f"📄 Found {output.publications_count} related publications")
        if output.filters_applied:
            filter_str = ", ".join([f"{k}={v}" for k, v in output.filters_applied.items()])
            search_logs.append(f"🎯 Filters applied: {filter_str}")

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
                publication_date=ranked.dataset.publication_date,  # When dataset was made public
                submission_date=ranked.dataset.submission_date,  # When dataset was submitted
                pubmed_ids=ranked.dataset.pubmed_ids,  # Include PMIDs for full-text enrichment
            )
            for ranked in output.datasets
        ]

        # Convert publications to response format
        publications = []
        if output.publications:
            for pub in output.publications:
                # Extract GEO IDs from abstract/full text
                import re

                geo_ids = []
                if hasattr(pub, "abstract") and pub.abstract:
                    geo_ids.extend(re.findall(r"\bGSE\d{5,}\b", pub.abstract))
                if hasattr(pub, "full_text") and pub.full_text:
                    geo_ids.extend(re.findall(r"\bGSE\d{5,}\b", pub.full_text))

                publications.append(
                    PublicationResponse(
                        pmid=getattr(pub, "pmid", None),
                        pmc_id=getattr(pub, "pmc_id", None),
                        doi=getattr(pub, "doi", None),
                        title=getattr(pub, "title", ""),
                        abstract=getattr(pub, "abstract", None),
                        authors=getattr(pub, "authors", []),
                        journal=getattr(pub, "journal", None),
                        publication_date=getattr(pub, "publication_date", None),
                        geo_ids_mentioned=list(set(geo_ids)),  # Deduplicate
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
            total_found=output.total_found,
            datasets=datasets,
            search_terms_used=output.search_terms_used,
            filters_applied=output.filters_applied,
            search_logs=search_logs,
            publications=publications,
            publications_count=len(publications),
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

    from omics_oracle_v2.lib.fulltext.manager import FullTextManager, FullTextManagerConfig
    from omics_oracle_v2.lib.publications.clients.pubmed import PubMedClient, PubMedConfig

    start_time = time.time()

    try:
        # Initialize FullTextManager (same config as PublicationSearchPipeline)
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
            download_pdfs=True,  # Download PDFs for parsing
            unpaywall_email=os.getenv("UNPAYWALL_EMAIL", "research@omicsoracle.ai"),
            core_api_key=os.getenv("CORE_API_KEY"),
        )
        fulltext_manager = FullTextManager(fulltext_config)

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

            # BATCH DOWNLOAD (same as PublicationSearchPipeline - WORKING CODE!)
            logger.info(f"🚀 Batch downloading full-text for {len(publications)} publications...")
            fulltext_results = await fulltext_manager.get_fulltext_batch(publications)

            # Attach results to dataset metadata
            dataset.fulltext = []
            for pub, result in zip(publications, fulltext_results):
                if result.success:
                    fulltext_info = {
                        "pmid": pub.pmid,
                        "title": pub.title,
                        "url": result.url,
                        "source": result.source.value,
                        "pdf_path": result.pdf_path if result.pdf_path else None,
                    }
                    dataset.fulltext.append(fulltext_info)
                    logger.info(f"✅ Got full-text for {pub.pmid} from {result.source.value}")

            dataset.fulltext_count = len(dataset.fulltext)
            dataset.fulltext_status = "available" if dataset.fulltext else "failed"
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
