"""Orchestrator models for multi-agent workflows."""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class WorkflowType(str, Enum):
    """Type of workflow to execute."""

    SIMPLE_SEARCH = "simple_search"  # Query -> Search -> Report
    FULL_ANALYSIS = "full_analysis"  # Query -> Search -> Data -> Report
    QUICK_REPORT = "quick_report"  # Search -> Report (direct dataset IDs)
    DATA_VALIDATION = "data_validation"  # Data -> Report (validate existing datasets)


class WorkflowStage(str, Enum):
    """Current stage in workflow execution."""

    INITIALIZED = "initialized"
    QUERY_PROCESSING = "query_processing"
    DATASET_SEARCH = "dataset_search"
    DATA_VALIDATION = "data_validation"
    REPORT_GENERATION = "report_generation"
    COMPLETED = "completed"
    FAILED = "failed"


class OrchestratorInput(BaseModel):
    """Input for orchestrator workflow execution."""

    query: str = Field(..., min_length=1, description="User's research query")
    workflow_type: WorkflowType = Field(
        default=WorkflowType.FULL_ANALYSIS, description="Type of workflow to execute"
    )
    max_results: int = Field(default=50, ge=1, le=200, description="Maximum datasets to return")
    report_type: str = Field(default="comprehensive", description="Type of report to generate")
    report_format: str = Field(default="markdown", description="Format for final report")
    include_quality_analysis: bool = Field(default=True, description="Include quality analysis in report")
    include_recommendations: bool = Field(default=True, description="Include recommendations in report")
    # Optional filters
    organisms: Optional[List[str]] = Field(default=None, description="Filter by specific organisms")
    min_samples: Optional[int] = Field(default=None, ge=1, description="Minimum sample count")
    study_types: Optional[List[str]] = Field(default=None, description="Filter by study types")


class WorkflowResult(BaseModel):
    """Result from a single workflow stage."""

    stage: WorkflowStage
    success: bool
    agent_name: str
    output: Optional[Any] = None
    error: Optional[str] = None
    execution_time_ms: float = Field(default=0.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class OrchestratorOutput(BaseModel):
    """Output from orchestrator workflow execution."""

    workflow_type: WorkflowType
    query: str
    final_stage: WorkflowStage
    success: bool

    # Stage results
    stage_results: List[WorkflowResult] = Field(default_factory=list)

    # Final outputs
    final_report: Optional[str] = None
    report_title: Optional[str] = None

    # Summary statistics
    total_datasets_found: int = Field(default=0)
    total_datasets_analyzed: int = Field(default=0)
    high_quality_datasets: int = Field(default=0)

    # Execution metadata
    total_execution_time_ms: float = Field(default=0.0)
    stages_completed: int = Field(default=0)
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def get_stage_result(self, stage: WorkflowStage) -> Optional[WorkflowResult]:
        """Get result for a specific stage."""
        for result in self.stage_results:
            if result.stage == stage:
                return result
        return None

    def get_failed_stages(self) -> List[WorkflowResult]:
        """Get all failed stages."""
        return [r for r in self.stage_results if not r.success]

    def get_execution_summary(self) -> str:
        """Generate execution summary."""
        lines = [
            f"Workflow: {self.workflow_type.value}",
            f"Query: {self.query}",
            f"Status: {'SUCCESS' if self.success else 'FAILED'}",
            f"Stages Completed: {self.stages_completed}",
            f"Total Time: {self.total_execution_time_ms:.2f}ms",
        ]

        if self.success:
            lines.extend(
                [
                    "",
                    "Results:",
                    f"- Datasets Found: {self.total_datasets_found}",
                    f"- Datasets Analyzed: {self.total_datasets_analyzed}",
                    f"- High Quality: {self.high_quality_datasets}",
                ]
            )
        else:
            lines.extend(
                [
                    "",
                    f"Error: {self.error_message}",
                    f"Failed at stage: {self.final_stage.value}",
                ]
            )

        return "\n".join(lines)
