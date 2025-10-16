"""
API Request Models

Pydantic models for API requests.
"""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from omics_oracle_v2.api.models.agent_schemas import ReportFormat, ReportType


class QueryRequest(BaseModel):
    """Request model for Query Agent."""

    query: str = Field(
        ...,
        description="Natural language research query",
        min_length=1,
        max_length=500,
        examples=["breast cancer RNA-seq studies"],
    )


class SearchRequest(BaseModel):
    """Request model for Search Agent."""

    search_terms: List[str] = Field(
        ...,
        description="List of search terms",
        min_length=1,
        examples=[["breast cancer", "RNA-seq"]],
    )
    filters: Optional[Dict[str, str]] = Field(
        default=None,
        description="Optional filters (organism, study_type, etc.)",
        examples=[{"organism": "Homo sapiens", "min_samples": "10"}],
    )
    max_results: int = Field(
        default=20,
        description="Maximum number of results to return",
        ge=1,
        le=1000,  # Increased from 100 to support pagination
    )
    enable_semantic: bool = Field(
        default=False,
        description="Enable semantic search using AI-powered query expansion and hybrid search",
    )


class DataValidationRequest(BaseModel):
    """Request model for Data Agent."""

    dataset_ids: List[str] = Field(
        ...,
        description="List of GEO dataset IDs to validate",
        min_length=1,
        examples=[["GSE12345", "GSE67890"]],
    )
    min_quality_score: Optional[float] = Field(
        default=None,
        description="Minimum quality score threshold (0-1)",
        ge=0.0,
        le=1.0,
    )


class ReportRequest(BaseModel):
    """Request model for Report Agent."""

    dataset_ids: List[str] = Field(
        ...,
        description="List of GEO dataset IDs to include in report",
        min_length=1,
        examples=[["GSE12345", "GSE67890"]],
    )
    report_type: ReportType = Field(
        default=ReportType.BRIEF,
        description="Type of report to generate",
    )
    report_format: ReportFormat = Field(
        default=ReportFormat.MARKDOWN,
        description="Output format for the report",
    )
    include_recommendations: bool = Field(
        default=True,
        description="Include actionable recommendations",
    )
