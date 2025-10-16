"""
API Response Models

Pydantic models for API responses.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class BaseResponse(BaseModel):
    """Base response model with common fields."""

    success: bool = Field(..., description="Whether the request was successful")
    execution_time_ms: float = Field(..., description="Execution time in milliseconds")
    timestamp: datetime = Field(..., description="Response timestamp")


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")


class EntityResponse(BaseModel):
    """Entity extracted from query."""

    text: str = Field(..., description="Entity text")
    entity_type: str = Field(..., description="Entity type")
    confidence: float = Field(..., description="Confidence score")


class QueryResponse(BaseResponse):
    """Response model for Query Agent."""

    original_query: str = Field(..., description="Original query text")
    intent: str = Field(..., description="Detected intent")
    confidence: float = Field(..., description="Overall confidence score")
    entities: List[EntityResponse] = Field(..., description="Extracted entities")
    search_terms: List[str] = Field(..., description="Generated search terms")
    entity_counts: Dict[str, int] = Field(..., description="Count by entity type")


class FullTextContent(BaseModel):
    """Parsed and normalized full-text content from a publication."""

    pmid: str = Field(..., description="PubMed ID")
    title: str = Field(..., description="Publication title")
    url: Optional[str] = Field(default="", description="Full-text URL")
    source: Optional[str] = Field(
        default="", description="Source (institutional, pmc, etc.)"
    )
    pdf_path: Optional[str] = Field(default=None, description="Local PDF file path")
    abstract: str = Field(default="", description="Abstract text")
    methods: str = Field(default="", description="Methods section")
    results: str = Field(default="", description="Results section")
    discussion: str = Field(default="", description="Discussion section")
    introduction: Optional[str] = Field(default="", description="Introduction section")
    conclusion: Optional[str] = Field(default="", description="Conclusion section")
    references: List[str] = Field(
        default_factory=list, description="Reference citations"
    )
    figures_captions: List[str] = Field(
        default_factory=list, description="Figure captions"
    )
    tables_captions: List[str] = Field(
        default_factory=list, description="Table captions"
    )
    format: str = Field(default="unknown", description="Source format (jats/pdf/latex)")
    parse_date: str = Field(default="", description="When the content was parsed")


class DatasetResponse(BaseModel):
    """Dataset metadata response."""

    geo_id: str = Field(..., description="GEO dataset ID")
    title: str = Field(..., description="Dataset title")
    summary: Optional[str] = Field(None, description="Dataset summary")
    organism: Optional[str] = Field(None, description="Organism")
    sample_count: int = Field(..., description="Number of samples")
    platform: Optional[str] = Field(None, description="Platform technology")
    relevance_score: float = Field(..., description="Relevance score")
    match_reasons: List[str] = Field(..., description="Reasons for match")

    # Publication and citation info
    publication_date: Optional[str] = Field(None, description="Public release date")
    submission_date: Optional[str] = Field(None, description="Submission date")
    pubmed_ids: List[str] = Field(
        default_factory=list, description="Associated PubMed IDs"
    )

    # Database metrics (accurate counts from UnifiedDatabase)
    citation_count: int = Field(
        default=0, description="Total papers in database for this GEO dataset"
    )
    pdf_count: int = Field(
        default=0, description="Number of papers with downloaded PDFs"
    )
    processed_count: int = Field(
        default=0, description="Number of papers with extracted content"
    )
    completion_rate: float = Field(
        default=0.0, description="Processing completion percentage"
    )

    # Full-text content fields
    fulltext: List[FullTextContent] = Field(
        default_factory=list, description="Full-text content from publications"
    )
    fulltext_status: str = Field(
        default="not_downloaded",
        description="Status: not_downloaded/downloading/available/failed/partial",
    )
    fulltext_count: int = Field(
        default=0, description="Number of full-text papers available"
    )
    fulltext_total: int = Field(
        default=0, description="Total papers attempted (including citing papers)"
    )


class PublicationResponse(BaseModel):
    """Publication metadata response."""

    pmid: Optional[str] = Field(None, description="PubMed ID")
    pmc_id: Optional[str] = Field(None, description="PubMed Central ID")
    doi: Optional[str] = Field(None, description="DOI")
    title: str = Field(..., description="Publication title")
    abstract: Optional[str] = Field(None, description="Abstract")
    authors: List[str] = Field(default_factory=list, description="Authors")
    journal: Optional[str] = Field(None, description="Journal name")
    publication_date: Optional[str] = Field(None, description="Publication date")
    geo_ids_mentioned: List[str] = Field(
        default_factory=list, description="GEO IDs mentioned in the paper"
    )
    fulltext_available: bool = Field(
        default=False, description="Whether full text is available"
    )
    pdf_path: Optional[str] = Field(None, description="Path to downloaded PDF")


class QueryProcessingResponse(BaseModel):
    """Query processing context from QueryOptimizer."""

    extracted_entities: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Extracted entities by type (GENE, DISEASE, etc.)",
    )
    expanded_terms: List[str] = Field(
        default_factory=list, description="Synonym-expanded search terms"
    )
    geo_search_terms: List[str] = Field(
        default_factory=list, description="GEO-specific search terms used"
    )
    search_intent: Optional[str] = Field(None, description="Detected search intent")
    query_type: Optional[str] = Field(None, description="Query type classification")


class SearchResponse(BaseResponse):
    """Response model for Search Agent."""

    total_found: int = Field(..., description="Total datasets found")
    datasets: List[DatasetResponse] = Field(..., description="Ranked dataset results")
    search_terms_used: List[str] = Field(..., description="Search terms used")
    filters_applied: Dict[str, Any] = Field(..., description="Filters applied")
    search_logs: List[str] = Field(
        default=[], description="Search process logs for debugging"
    )
    publications: List[PublicationResponse] = Field(
        default_factory=list, description="Related publications"
    )
    publications_count: int = Field(
        default=0, description="Number of related publications found"
    )
    query_processing: Optional[QueryProcessingResponse] = Field(
        None, description="Query processing context for RAG enhancement"
    )


class QualityMetricsResponse(BaseModel):
    """Quality metrics for a dataset."""

    quality_score: float = Field(..., description="Overall quality score (0-1)")
    quality_level: str = Field(
        ..., description="Quality level (excellent/good/fair/poor)"
    )
    has_publication: bool = Field(..., description="Has associated publication")
    has_sra_data: bool = Field(..., description="Has SRA data available")
    age_years: float = Field(..., description="Dataset age in years")


class ValidatedDatasetResponse(DatasetResponse):
    """Dataset with quality validation."""

    quality_metrics: QualityMetricsResponse = Field(..., description="Quality metrics")


class DataValidationResponse(BaseResponse):
    """Response model for Data Agent."""

    total_processed: int = Field(..., description="Total datasets processed")
    validated_datasets: List[ValidatedDatasetResponse] = Field(
        ..., description="Validated datasets"
    )
    quality_stats: Dict[str, Any] = Field(..., description="Quality statistics")


class ReportResponse(BaseResponse):
    """Response model for Report Agent."""

    report_type: str = Field(..., description="Report type")
    report_format: str = Field(..., description="Report format")
    full_report: str = Field(..., description="Complete report text")
    key_findings: List[str] = Field(..., description="Key findings summary")
    recommendations: Optional[List[str]] = Field(None, description="Recommendations")
    datasets_analyzed: int = Field(..., description="Number of datasets analyzed")
