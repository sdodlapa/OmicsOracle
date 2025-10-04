"""
Workflow API Models

Request/response models for workflow orchestration endpoints.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from omics_oracle_v2.agents.models.orchestrator import WorkflowType


class WorkflowRequest(BaseModel):
    """Request model for workflow execution."""

    query: str = Field(
        ...,
        description="Natural language research query",
        min_length=1,
        max_length=500,
        examples=["Find breast cancer RNA-seq studies"],
    )
    workflow_type: WorkflowType = Field(
        default=WorkflowType.FULL_ANALYSIS,
        description="Type of workflow to execute",
    )
    max_results: int = Field(
        default=50,
        description="Maximum number of datasets to return",
        ge=1,
        le=200,
    )
    report_type: str = Field(
        default="comprehensive",
        description="Type of report (brief, detailed, comprehensive)",
    )
    report_format: str = Field(
        default="markdown",
        description="Report format (markdown, html, json)",
    )
    include_quality_analysis: bool = Field(
        default=True,
        description="Include quality analysis in workflow",
    )
    include_recommendations: bool = Field(
        default=True,
        description="Include recommendations in report",
    )
    # Optional filters
    organisms: Optional[List[str]] = Field(
        default=None,
        description="Filter by specific organisms",
    )
    min_samples: Optional[int] = Field(
        default=None,
        ge=1,
        description="Minimum sample count filter",
    )
    study_types: Optional[List[str]] = Field(
        default=None,
        description="Filter by study types",
    )


class StageResultResponse(BaseModel):
    """Response model for a workflow stage result."""

    stage: str = Field(..., description="Workflow stage name")
    success: bool = Field(..., description="Whether stage succeeded")
    agent_name: str = Field(..., description="Agent that executed the stage")
    execution_time_ms: float = Field(..., description="Stage execution time in ms")
    error: Optional[str] = Field(None, description="Error message if failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Stage metadata")


class WorkflowResponse(BaseModel):
    """Response model for workflow execution."""

    success: bool = Field(..., description="Overall workflow success")
    execution_time_ms: float = Field(..., description="Total execution time in ms")
    timestamp: str = Field(..., description="Completion timestamp")

    # Workflow details
    workflow_type: str = Field(..., description="Type of workflow executed")
    query: str = Field(..., description="Original query")
    final_stage: str = Field(..., description="Final stage reached")

    # Stage results
    stages_completed: int = Field(..., description="Number of stages completed")
    stage_results: List[StageResultResponse] = Field(
        default_factory=list, description="Results from each stage"
    )

    # Final outputs
    final_report: Optional[str] = Field(None, description="Generated report")
    report_title: Optional[str] = Field(None, description="Report title")

    # Summary statistics
    total_datasets_found: int = Field(default=0, description="Total datasets found")
    total_datasets_analyzed: int = Field(default=0, description="Total datasets analyzed")
    high_quality_datasets: int = Field(default=0, description="Number of high-quality datasets")

    # Error information
    error_message: Optional[str] = Field(None, description="Error message if workflow failed")


class WorkflowStatusResponse(BaseModel):
    """Response model for workflow status check."""

    workflow_id: str = Field(..., description="Workflow identifier")
    status: str = Field(..., description="Current status (running, completed, failed)")
    current_stage: str = Field(..., description="Current execution stage")
    progress_percentage: float = Field(..., description="Progress percentage (0-100)")
    started_at: str = Field(..., description="Workflow start timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    estimated_completion: Optional[str] = Field(None, description="Estimated completion time")
