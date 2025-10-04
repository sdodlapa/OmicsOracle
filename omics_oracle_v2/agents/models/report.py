"""
Report models for Report Agent.

Defines input/output data structures for AI-powered report generation,
multi-dataset synthesis, and insight extraction.
"""

from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from .data import ProcessedDataset


class ReportType(str, Enum):
    """Types of reports that can be generated."""

    BRIEF = "brief"  # Short summary (1-2 paragraphs)
    COMPREHENSIVE = "comprehensive"  # Detailed analysis (multiple sections)
    TECHNICAL = "technical"  # Technical details for researchers
    EXECUTIVE = "executive"  # High-level summary for decision makers


class ReportFormat(str, Enum):
    """Output formats for generated reports."""

    MARKDOWN = "markdown"
    JSON = "json"
    HTML = "html"
    TEXT = "text"


class ReportInput(BaseModel):
    """Input for report generation operations."""

    datasets: List[ProcessedDataset] = Field(
        ..., description="Processed datasets to include in report", min_length=1
    )
    query_context: Optional[str] = Field(None, description="Original user query for context")
    report_type: ReportType = Field(
        default=ReportType.COMPREHENSIVE, description="Type of report to generate"
    )
    report_format: ReportFormat = Field(default=ReportFormat.MARKDOWN, description="Output format for report")
    max_datasets: int = Field(default=10, description="Maximum datasets to include in detail", ge=1, le=50)
    include_quality_analysis: bool = Field(default=True, description="Include quality analysis section")
    include_recommendations: bool = Field(default=True, description="Include recommendations section")

    @field_validator("datasets")
    @classmethod
    def validate_datasets(cls, v: List[ProcessedDataset]) -> List[ProcessedDataset]:
        """Validate datasets list is not empty."""
        if not v:
            raise ValueError("datasets cannot be empty")
        return v


class ReportSection(BaseModel):
    """A section within a generated report."""

    title: str = Field(..., description="Section title")
    content: str = Field(..., description="Section content")
    order: int = Field(..., description="Section order in report", ge=0)


class KeyInsight(BaseModel):
    """A key insight extracted from the datasets."""

    insight: str = Field(..., description="The insight text")
    supporting_datasets: List[str] = Field(
        default_factory=list, description="GEO IDs supporting this insight"
    )
    confidence: float = Field(default=1.0, description="Confidence in this insight (0.0-1.0)", ge=0.0, le=1.0)


class ReportOutput(BaseModel):
    """Output from report generation operations."""

    # Report metadata
    report_type: ReportType = Field(..., description="Type of report generated")
    report_format: ReportFormat = Field(..., description="Format of report")
    generated_at: str = Field(..., description="Timestamp when report was generated")

    # Report content
    title: str = Field(..., description="Report title")
    summary: str = Field(..., description="Executive summary")
    sections: List[ReportSection] = Field(default_factory=list, description="Report sections in order")

    # Analysis results
    key_insights: List[KeyInsight] = Field(default_factory=list, description="Key insights extracted")
    recommendations: List[str] = Field(default_factory=list, description="Actionable recommendations")

    # Statistics
    total_datasets_analyzed: int = Field(..., description="Number of datasets analyzed", ge=0)
    datasets_included: List[str] = Field(default_factory=list, description="GEO IDs of datasets included")
    quality_summary: Dict[str, int] = Field(
        default_factory=dict, description="Summary of dataset quality levels"
    )

    # Full report text
    full_report: str = Field(..., description="Complete formatted report")

    def get_section_by_title(self, title: str) -> Optional[ReportSection]:
        """
        Get a section by its title.

        Args:
            title: Section title to search for

        Returns:
            ReportSection if found, None otherwise
        """
        for section in self.sections:
            if section.title.lower() == title.lower():
                return section
        return None

    def get_high_confidence_insights(self, min_confidence: float = 0.7) -> List[KeyInsight]:
        """
        Get insights with confidence above threshold.

        Args:
            min_confidence: Minimum confidence threshold

        Returns:
            List of high-confidence insights
        """
        return [i for i in self.key_insights if i.confidence >= min_confidence]

    class Config:
        """Pydantic config."""

        arbitrary_types_allowed = True


__all__ = [
    "ReportType",
    "ReportFormat",
    "ReportInput",
    "ReportOutput",
    "ReportSection",
    "KeyInsight",
]
