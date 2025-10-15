"""
Legacy Agent Schemas

These models were originally part of the multi-agent system (now archived to extras/agents/).
They are kept here as API schemas for backward compatibility with existing endpoints.

Models extracted from:
- agents/models/search.py: RankedDataset
- agents/models/orchestrator.py: WorkflowType
- agents/models/report.py: ReportType, ReportFormat
"""

from enum import Enum
from typing import List

from pydantic import BaseModel, Field

from omics_oracle_v2.lib.search_engines.geo.models import GEOSeriesMetadata


# From agents/models/search.py
class RankedDataset(BaseModel):
    """Dataset with relevance ranking."""

    dataset: GEOSeriesMetadata = Field(..., description="GEO dataset")
    relevance_score: float = Field(
        ..., description="Relevance score (0.0-1.0)", ge=0.0, le=1.0
    )
    match_reasons: List[str] = Field(
        default_factory=list, description="Reasons for relevance"
    )

    class Config:
        """Pydantic config."""

        arbitrary_types_allowed = True


# From agents/models/orchestrator.py
class WorkflowType(str, Enum):
    """Type of workflow to execute."""

    SIMPLE_SEARCH = "simple_search"  # Query -> Search -> Report
    FULL_ANALYSIS = "full_analysis"  # Query -> Search -> Data -> Report
    QUICK_REPORT = "quick_report"  # Search -> Report (direct dataset IDs)
    DATA_VALIDATION = "data_validation"  # Data -> Report (validate existing datasets)


# From agents/models/report.py
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


__all__ = [
    "RankedDataset",
    "WorkflowType",
    "ReportType",
    "ReportFormat",
]
