"""
Data models for the integration layer.

These Pydantic models define the contract between backend and frontend,
ensuring type safety and validation across all implementations.
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, HttpUrl

# ============================================================================
# SEARCH MODELS
# ============================================================================


class SearchRequest(BaseModel):
    """Request model for search operations."""

    query: str = Field(..., description="Search query string")
    databases: List[str] = Field(default=["pubmed", "google_scholar"], description="Databases to search")
    max_results: int = Field(default=100, ge=1, le=1000, description="Maximum results")
    search_mode: Literal["keyword", "semantic", "hybrid"] = Field(
        default="hybrid", description="Search algorithm to use"
    )
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Additional search filters")
    enable_enrichment: bool = Field(default=True, description="Enable citation/quality/biomarker enrichment")


class CitationMetrics(BaseModel):
    """Citation analysis for a publication."""

    count: int = Field(default=0, description="Total citations")
    recent_count: int = Field(default=0, description="Citations in last 2 years")
    h_index: Optional[int] = Field(None, description="H-index of primary author")
    velocity: Optional[float] = Field(None, description="Citations per year")
    predicted_5yr: Optional[int] = Field(None, description="ML prediction for 5 years")


class QualityScore(BaseModel):
    """Quality assessment of a publication."""

    overall: float = Field(..., ge=0, le=1, description="Overall quality (0-1)")
    methodology: float = Field(..., ge=0, le=1, description="Methodology score")
    impact: float = Field(..., ge=0, le=1, description="Impact score")
    recency: float = Field(..., ge=0, le=1, description="Recency score")
    explanation: str = Field(..., description="Human-readable explanation")


class Biomarker(BaseModel):
    """Extracted biomarker/gene/protein."""

    name: str = Field(..., description="Biomarker name")
    type: Literal["gene", "protein", "metabolite", "pathway", "other"] = Field(
        ..., description="Biomarker type"
    )
    confidence: float = Field(..., ge=0, le=1, description="Extraction confidence")
    context: str = Field(..., description="Surrounding text context")


class AccessInfo(BaseModel):
    """Access information for a publication."""

    has_pdf: bool = Field(default=False, description="PDF available")
    pdf_url: Optional[HttpUrl] = Field(None, description="Direct PDF URL")
    has_fulltext: bool = Field(default=False, description="Full text available")
    institutional_access: bool = Field(default=False, description="Institutional access")
    open_access: bool = Field(default=False, description="Open access")


class Publication(BaseModel):
    """A single publication with enriched metadata."""

    # Core metadata
    id: str = Field(..., description="Unique identifier")
    title: str = Field(..., description="Publication title")
    authors: List[str] = Field(..., description="Author names")
    year: Optional[int] = Field(None, description="Publication year")
    journal: Optional[str] = Field(None, description="Journal name")
    doi: Optional[str] = Field(None, description="DOI")
    pmid: Optional[str] = Field(None, description="PubMed ID")
    abstract: Optional[str] = Field(None, description="Abstract text")

    # URLs
    pubmed_url: Optional[HttpUrl] = Field(None, description="PubMed URL")
    scholar_url: Optional[HttpUrl] = Field(None, description="Google Scholar URL")

    # Enrichment data
    citation_metrics: Optional[CitationMetrics] = Field(None, description="Citation analysis")
    quality_score: Optional[QualityScore] = Field(None, description="Quality assessment")
    biomarkers: List[Biomarker] = Field(default_factory=list, description="Extracted biomarkers")
    access_info: Optional[AccessInfo] = Field(None, description="Access information")

    # Search relevance
    relevance_score: float = Field(default=0.0, ge=0, le=1, description="Search relevance (0-1)")
    semantic_similarity: Optional[float] = Field(None, description="Semantic similarity to query")
    match_explanation: Optional[str] = Field(None, description="Why this result matched")


class SearchMetadata(BaseModel):
    """Metadata about search execution."""

    total_results: int = Field(..., description="Total results found")
    query_time: Optional[float] = Field(None, description="Query execution time (seconds)")
    databases_searched: Optional[List[str]] = Field(None, description="Databases queried")
    search_mode: Optional[str] = Field(None, description="Search mode used")
    cache_hit: bool = Field(default=False, description="Result from cache?")


class SearchResponse(BaseModel):
    """Response from search operation."""

    results: List[Publication] = Field(..., description="Search results")
    metadata: SearchMetadata = Field(..., description="Search metadata")
    aggregated_biomarkers: Dict[str, int] = Field(
        default_factory=dict, description="Biomarker frequency across all results"
    )


# ============================================================================
# ANALYSIS MODELS
# ============================================================================


class AnalysisRequest(BaseModel):
    """Request for LLM analysis."""

    query: str = Field(..., description="Original search query")
    results: List[Publication] = Field(..., max_items=20, description="Publications to analyze")
    analysis_type: Literal["overview", "detailed", "synthesis"] = Field(
        default="overview", description="Type of analysis"
    )


class AnalysisResponse(BaseModel):
    """Response from LLM analysis."""

    overview: str = Field(..., description="High-level overview")
    key_findings: List[str] = Field(..., description="Key findings")
    research_gaps: List[str] = Field(..., description="Identified research gaps")
    recommendations: List[str] = Field(..., description="Research recommendations")
    confidence: float = Field(..., ge=0, le=1, description="Analysis confidence")
    model_used: str = Field(..., description="LLM model used")


class QARequest(BaseModel):
    """Request for Q&A over search results."""

    question: str = Field(..., description="User question")
    context: List[Publication] = Field(..., max_items=10, description="Publications as context")


class QAResponse(BaseModel):
    """Response from Q&A system."""

    answer: str = Field(..., description="Answer to question")
    sources: List[str] = Field(..., description="Source publication IDs")
    confidence: float = Field(..., ge=0, le=1, description="Answer confidence")
    follow_up_questions: List[str] = Field(default_factory=list, description="Suggested follow-up questions")


class TrendPoint(BaseModel):
    """A single point in trend analysis."""

    year: int = Field(..., description="Year")
    count: int = Field(..., description="Publication count")
    citation_avg: float = Field(..., description="Average citations")


class TrendAnalysis(BaseModel):
    """Trend analysis over time."""

    trends: List[TrendPoint] = Field(..., description="Trend data points")
    growth_rate: float = Field(..., description="Annual growth rate")
    prediction_5yr: int = Field(..., description="Predicted publications in 5 years")
    peak_year: int = Field(..., description="Peak publication year")


class NetworkNode(BaseModel):
    """A node in citation network."""

    id: str = Field(..., description="Publication ID")
    title: str = Field(..., description="Publication title")
    year: int = Field(..., description="Publication year")
    citations: int = Field(..., description="Citation count")
    size: float = Field(..., description="Node size (for visualization)")


class NetworkEdge(BaseModel):
    """An edge in citation network."""

    source: str = Field(..., description="Source publication ID")
    target: str = Field(..., description="Target publication ID")
    weight: float = Field(default=1.0, description="Edge weight")


class NetworkGraph(BaseModel):
    """Citation network graph."""

    nodes: List[NetworkNode] = Field(..., description="Network nodes")
    edges: List[NetworkEdge] = Field(..., description="Network edges")
    clusters: Dict[str, List[str]] = Field(default_factory=dict, description="Detected clusters")


# ============================================================================
# ML PREDICTION MODELS
# ============================================================================


class RecommendationRequest(BaseModel):
    """Request for paper recommendations."""

    seed_papers: List[str] = Field(..., min_items=1, description="Publication IDs to base recommendations on")
    count: int = Field(default=10, ge=1, le=50, description="Number of recommendations")


class Recommendation(BaseModel):
    """A single recommendation."""

    publication: Publication = Field(..., description="Recommended publication")
    score: float = Field(..., ge=0, le=1, description="Recommendation score")
    reason: str = Field(..., description="Why recommended")


class RecommendationResponse(BaseModel):
    """Response from recommendation system."""

    recommendations: List[Recommendation] = Field(..., description="Recommendations")
    model_used: str = Field(..., description="ML model used")


# ============================================================================
# UTILITY MODELS
# ============================================================================


class HealthStatus(BaseModel):
    """System health status."""

    status: Literal["healthy", "degraded", "unhealthy"] = Field(..., description="Overall status")
    services: Dict[str, bool] = Field(..., description="Service availability")
    cache_hit_rate: float = Field(..., ge=0, le=1, description="Cache hit rate")
    avg_response_time: float = Field(..., description="Average response time (ms)")


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error time")
