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


class SearchResponse(BaseResponse):
    """Response model for Search Agent."""

    total_found: int = Field(..., description="Total datasets found")
    datasets: List[DatasetResponse] = Field(..., description="Ranked dataset results")
    search_terms_used: List[str] = Field(..., description="Search terms used")
    filters_applied: Dict[str, Any] = Field(..., description="Filters applied")


class QualityMetricsResponse(BaseModel):
    """Quality metrics for a dataset."""

    quality_score: float = Field(..., description="Overall quality score (0-1)")
    quality_level: str = Field(..., description="Quality level (excellent/good/fair/poor)")
    has_publication: bool = Field(..., description="Has associated publication")
    has_sra_data: bool = Field(..., description="Has SRA data available")
    age_years: float = Field(..., description="Dataset age in years")


class ValidatedDatasetResponse(DatasetResponse):
    """Dataset with quality validation."""

    quality_metrics: QualityMetricsResponse = Field(..., description="Quality metrics")


class DataValidationResponse(BaseResponse):
    """Response model for Data Agent."""

    total_processed: int = Field(..., description="Total datasets processed")
    validated_datasets: List[ValidatedDatasetResponse] = Field(..., description="Validated datasets")
    quality_stats: Dict[str, Any] = Field(..., description="Quality statistics")


class ReportResponse(BaseResponse):
    """Response model for Report Agent."""

    report_type: str = Field(..., description="Report type")
    report_format: str = Field(..., description="Report format")
    full_report: str = Field(..., description="Complete report text")
    key_findings: List[str] = Field(..., description="Key findings summary")
    recommendations: Optional[List[str]] = Field(None, description="Recommendations")
    datasets_analyzed: int = Field(..., description="Number of datasets analyzed")
