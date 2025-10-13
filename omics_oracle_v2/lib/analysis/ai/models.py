"""
Data models for AI summarization service.

Provides Pydantic models for summary requests, responses, and configuration
with full type safety and validation.
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SummaryType(str, Enum):
    """Types of summaries that can be generated."""

    BRIEF = "brief"  # 1-2 sentences, quick overview
    COMPREHENSIVE = "comprehensive"  # Full multi-section summary
    TECHNICAL = "technical"  # Focus on methodology and technical details
    SIGNIFICANCE = "significance"  # Research impact and implications


class SummaryRequest(BaseModel):
    """Request for AI summary generation."""

    metadata: Dict[str, Any] = Field(..., description="Dataset metadata to summarize")
    query_context: Optional[str] = Field(None, description="Original user query for context")
    summary_type: SummaryType = Field(
        default=SummaryType.COMPREHENSIVE, description="Type of summary to generate"
    )
    dataset_id: Optional[str] = Field(None, description="Dataset identifier (for caching)")
    overrides: Optional[Dict[str, Any]] = Field(
        None, description="Override default settings (max_tokens, temperature, etc.)"
    )


class SummaryResponse(BaseModel):
    """Response containing generated summary."""

    model_config = {"protected_namespaces": ()}  # Allow model_* field names

    dataset_id: str = Field(..., description="Dataset identifier")
    summary_type: SummaryType = Field(..., description="Type of summary generated")
    overview: Optional[str] = Field(None, description="High-level overview")
    methodology: Optional[str] = Field(None, description="Methodology summary")
    significance: Optional[str] = Field(None, description="Research significance")
    technical_details: Optional[str] = Field(None, description="Technical information")
    brief: Optional[str] = Field(None, description="Brief one-paragraph summary")
    token_usage: Optional[Dict[str, Any]] = Field(None, description="Token usage statistics")
    model_used: Optional[str] = Field(None, description="LLM model used")

    def has_content(self) -> bool:
        """Check if response contains any real summary content."""
        return any(
            [
                self.overview,
                self.methodology,
                self.significance,
                self.technical_details,
                self.brief,
            ]
        )

    def get_primary_summary(self) -> Optional[str]:
        """Get the main summary text based on type."""
        if self.brief:
            return self.brief
        if self.overview:
            return self.overview
        if self.methodology:
            return self.methodology
        return None


class BatchSummaryRequest(BaseModel):
    """Request for batch summarization of multiple datasets."""

    query: str = Field(..., description="Original search query")
    results: List[Dict[str, Any]] = Field(..., description="List of dataset results")
    max_datasets: int = Field(default=10, description="Maximum datasets to summarize")


class BatchSummaryResponse(BaseModel):
    """Response for batch summarization."""

    query: str = Field(..., description="Original query")
    total_datasets: int = Field(..., description="Total number of datasets")
    summarized_count: int = Field(..., description="Number of datasets actually summarized")
    statistics: Dict[str, Dict[str, int]] = Field(
        default_factory=dict, description="Aggregated statistics (organisms, platforms, etc.)"
    )
    overview: Optional[str] = Field(None, description="Batch overview summary")


class PromptTemplate(BaseModel):
    """Template for constructing LLM prompts."""

    system_message: str = Field(..., description="System role message")
    user_template: str = Field(..., description="User message template")
    max_tokens: int = Field(default=500, description="Maximum tokens for response")
    temperature: float = Field(default=0.3, description="Sampling temperature")


class ModelInfo(BaseModel):
    """Information about the LLM model configuration."""

    model_config = {"protected_namespaces": ()}  # Allow model_* field names

    model_name: str = Field(..., description="Model identifier")
    provider: str = Field(default="openai", description="LLM provider")
    max_tokens: int = Field(..., description="Maximum tokens per request")
    temperature: float = Field(..., description="Default temperature")
    available: bool = Field(..., description="Whether model is available")
