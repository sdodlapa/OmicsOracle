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

from fastapi import APIRouter, Body, HTTPException, Query, status
from pydantic import BaseModel, Field

from omics_oracle_v2.api.models.requests import SearchRequest
from omics_oracle_v2.api.models.responses import (DatasetResponse,
                                                  SearchResponse)
from omics_oracle_v2.lib.search_engines.geo.models import GEOSeriesMetadata
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
async def enrich_with_fulltext(
    datasets: List[DatasetResponse] = Body(
        ..., description="Datasets with PubMed IDs to enrich with full-text"
    ),
    max_papers: Optional[int] = Query(
        default=None, ge=1, le=10, description="Max papers to download per dataset"
    ),
    include_full_content: bool = Query(
        default=True,
        description="Include full parsed text (abstract, methods, results, etc.)",
    ),
    include_citing_papers: bool = Query(
        default=True,
        description="Download papers that CITED this dataset (not just original paper).",
    ),
    max_citing_papers: int = Query(
        default=10,
        description="Maximum citing papers to download per dataset (default=10).",
    ),
    download_original: bool = Query(
        default=True,
        description="Also download the original paper that generated the dataset.",
    ),
):
    """
    Enrich datasets with full-text content from linked publications.
    
    Refactored Oct 15, 2025 to use FulltextService.
    
    This endpoint:
    1. Takes datasets with PubMed IDs
    2. Fetches full publication metadata from PubMed
    3. Downloads PDFs using FullTextManager (concurrent)
    4. Parses PDFs and extracts sections
    5. Stores data in UnifiedDB automatically
    6. Returns datasets with fulltext URLs
    
    Args:
        datasets: List of datasets to enrich (must have pubmed_ids)
        max_papers: Maximum papers to download per dataset
        include_citing_papers: Download citing papers (default: True)
        max_citing_papers: Max citing papers per dataset (default: 10)
        download_original: Download original papers (default: True)
        include_full_content: Include parsed text sections (default: True)
    
    Returns:
        List of datasets with full-text URLs attached
    """
    try:
        from omics_oracle_v2.services.fulltext_service import FulltextService

        service = FulltextService()
        
        return await service.enrich_datasets(
            datasets=datasets,
            max_papers=max_papers,
            include_citing_papers=include_citing_papers,
            max_citing_papers=max_citing_papers,
            download_original=download_original,
            include_full_content=include_full_content,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Full-text enrichment failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Enrichment error: {str(e)}",
        )


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


@router.post(
    "/datasets/{geo_id}/discover-citations",
    summary="Discover Citations for a GEO Dataset"
)
async def discover_citations(geo_id: str):
    """
    Discover and populate citations for a GEO dataset.
    
    This endpoint:
    1. Searches PubMed for papers citing this GEO dataset
    2. Retrieves metadata for found papers
    3. Stores citations in the UnifiedDatabase
    
    Args:
        geo_id: GEO accession ID (e.g., GSE189158)
        
    Returns:
        Discovery results with citation count
    """
    try:
        logger.info(f"Starting citation discovery for {geo_id}")
        
        # Initialize discovery service
        discovery = GEOCitationDiscovery()
        
        # Create minimal metadata (will be enriched during discovery)
        metadata = GEOSeriesMetadata(
            geo_id=geo_id,
            title="",
            summary="",
            organism="",
            submission_date="2024-01-01",
            pubmed_ids=[],
            samples=[],
            platforms=[],
            sample_count=0
        )
        
        # Run discovery (async)
        result = await discovery.find_citing_papers(metadata, max_results=100)
        
        # Get count from result
        citations_found = len(result.citing_papers) if hasattr(result, 'citing_papers') else 0
        
        logger.info(f"Discovery complete for {geo_id}: {citations_found} citations")
        
        return {
            "geo_id": geo_id,
            "citations_found": citations_found,
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Citation discovery failed for {geo_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Discovery error: {str(e)}",
        )

