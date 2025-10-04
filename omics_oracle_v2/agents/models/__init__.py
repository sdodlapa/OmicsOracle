"""
Agent data models.

Models for representing agent inputs, outputs, and intermediate results.
"""

from enum import Enum
from typing import List

from pydantic import BaseModel, Field

from ...lib.nlp.models import Entity, EntityType


class QueryIntent(str, Enum):
    """Types of user query intents."""

    SEARCH = "search"  # Find datasets
    ANALYZE = "analyze"  # Analyze specific datasets
    SUMMARIZE = "summarize"  # Summarize findings
    COMPARE = "compare"  # Compare datasets
    UNKNOWN = "unknown"  # Cannot determine intent


class QueryInput(BaseModel):
    """
    Input for the Query Agent.

    Represents a natural language query from the user.
    """

    query: str = Field(..., min_length=1, description="Natural language query from user")
    max_entities: int = Field(default=100, ge=1, le=1000, description="Maximum entities to extract")
    include_synonyms: bool = Field(default=True, description="Whether to include entity synonyms")


class QueryOutput(BaseModel):
    """
    Output from the Query Agent.

    Contains extracted entities, search terms, and query analysis.
    """

    original_query: str = Field(..., description="Original user query")
    intent: QueryIntent = Field(..., description="Detected query intent")
    entities: List[Entity] = Field(default_factory=list, description="Extracted biomedical entities")
    search_terms: List[str] = Field(default_factory=list, description="Generated search terms")
    entity_counts: dict = Field(default_factory=dict, description="Count of entities by type")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence in query understanding")
    suggestions: List[str] = Field(default_factory=list, description="Query improvement suggestions")

    def get_entities_by_type(self, entity_type: EntityType) -> List[Entity]:
        """Get all entities of a specific type."""
        return [e for e in self.entities if e.entity_type == entity_type]

    def has_entity_type(self, entity_type: EntityType) -> bool:
        """Check if query contains entities of a specific type."""
        return any(e.entity_type == entity_type for e in self.entities)


__all__ = [
    "QueryIntent",
    "QueryInput",
    "QueryOutput",
]

# Import search models
from .search import RankedDataset, SearchInput, SearchOutput  # noqa: E402

__all__ += ["SearchInput", "SearchOutput", "RankedDataset"]

# Import data models
from .data import DataInput, DataOutput, DataQualityLevel, ProcessedDataset  # noqa: E402

__all__ += ["DataInput", "DataOutput", "DataQualityLevel", "ProcessedDataset"]

# Import report models
from .report import (  # noqa: E402
    KeyInsight,
    ReportFormat,
    ReportInput,
    ReportOutput,
    ReportSection,
    ReportType,
)

__all__ += ["ReportInput", "ReportOutput", "ReportType", "ReportFormat", "ReportSection", "KeyInsight"]

# Import orchestrator models
from .orchestrator import (  # noqa: E402
    OrchestratorInput,
    OrchestratorOutput,
    WorkflowResult,
    WorkflowStage,
    WorkflowType,
)

__all__ += ["OrchestratorInput", "OrchestratorOutput", "WorkflowType", "WorkflowStage", "WorkflowResult"]
