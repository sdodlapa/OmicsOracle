"""
Workflow Orchestration Routes

REST endpoints for executing multi-agent workflows.
"""

import logging
import time
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from omics_oracle_v2.agents import Orchestrator
from omics_oracle_v2.agents.models.orchestrator import OrchestratorInput
from omics_oracle_v2.api.dependencies import get_orchestrator
from omics_oracle_v2.api.models.workflow import StageResultResponse, WorkflowRequest, WorkflowResponse
from omics_oracle_v2.auth.dependencies import get_current_user
from omics_oracle_v2.auth.models import User

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Workflows"])


# Workflow Information Schema


class WorkflowInfo(BaseModel):
    """Information about an available workflow."""

    type: str = Field(..., description="Workflow type identifier")
    name: str = Field(..., description="Human-readable workflow name")
    description: str = Field(..., description="Workflow description")
    agents: List[str] = Field(..., description="Agents used in this workflow")
    use_case: str = Field(..., description="When to use this workflow")


# Workflow Listing


@router.get("/", response_model=List[WorkflowInfo], summary="List Available Workflows")
async def list_workflows(current_user: User = Depends(get_current_user)):
    """
    List all available workflows with their metadata.

    Requires authentication.

    Returns comprehensive information about each workflow including
    the agents involved and recommended use cases.

    Returns:
        List of workflow information objects
    """
    from omics_oracle_v2.agents.models.orchestrator import WorkflowType

    return [
        WorkflowInfo(
            type=WorkflowType.FULL_ANALYSIS.value,
            name="Full Analysis",
            description="Complete analysis: Query -> Search -> Data Validation -> Report",
            agents=["QueryAgent", "SearchAgent", "DataAgent", "ReportAgent"],
            use_case="Comprehensive dataset analysis with quality validation",
        ),
        WorkflowInfo(
            type=WorkflowType.SIMPLE_SEARCH.value,
            name="Simple Search",
            description="Quick search: Query -> Search -> Report",
            agents=["QueryAgent", "SearchAgent", "ReportAgent"],
            use_case="Fast dataset discovery without quality validation",
        ),
        WorkflowInfo(
            type=WorkflowType.QUICK_REPORT.value,
            name="Quick Report",
            description="Direct report: Search -> Report (with dataset IDs)",
            agents=["SearchAgent", "ReportAgent"],
            use_case="Generate report for known dataset IDs",
        ),
        WorkflowInfo(
            type=WorkflowType.DATA_VALIDATION.value,
            name="Data Validation",
            description="Validate and report: Data Validation -> Report",
            agents=["DataAgent", "ReportAgent"],
            use_case="Quality analysis of existing datasets",
        ),
    ]


# Workflow Execution


@router.post("/execute", response_model=WorkflowResponse, summary="Execute Complete Workflow")
async def execute_workflow(
    request: WorkflowRequest,
    current_user: User = Depends(get_current_user),
    orchestrator: Orchestrator = Depends(get_orchestrator),
):
    """
    Execute a complete multi-agent workflow.

    This endpoint orchestrates multiple agents to process a research query
    end-to-end, from query understanding to final report generation.

    Supported workflow types:
    - **full_analysis**: Query -> Search -> Data Validation -> Report (comprehensive)
    - **simple_search**: Query -> Search -> Report (faster, no validation)
    - **quick_report**: Search -> Report (direct dataset IDs)
    - **data_validation**: Data Validation -> Report (existing datasets)

    Args:
        request: Workflow request with query and preferences

    Returns:
        WorkflowResponse: Complete workflow results with report
    """
    start_time = time.time()

    try:
        logger.info(f"Starting workflow: {request.workflow_type.value} for query: {request.query}")

        # Build orchestrator input
        orchestrator_input = OrchestratorInput(
            query=request.query,
            workflow_type=request.workflow_type,
            max_results=request.max_results,
            report_type=request.report_type,
            report_format=request.report_format,
            include_quality_analysis=request.include_quality_analysis,
            include_recommendations=request.include_recommendations,
            organisms=request.organisms,
            min_samples=request.min_samples,
            study_types=request.study_types,
        )

        # Execute workflow
        result = orchestrator.execute(orchestrator_input)

        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Workflow execution failed: {result.error}",
            )

        output = result.output

        # Convert stage results
        stage_results = []
        for stage_result in output.stage_results:
            stage_results.append(
                StageResultResponse(
                    stage=stage_result.stage.value,
                    success=stage_result.success,
                    agent_name=stage_result.agent_name,
                    execution_time_ms=stage_result.execution_time_ms,
                    error=stage_result.error,
                    metadata=stage_result.metadata,
                )
            )

        execution_time_ms = (time.time() - start_time) * 1000

        return WorkflowResponse(
            success=output.success,
            execution_time_ms=execution_time_ms,
            timestamp=datetime.now(timezone.utc).isoformat(),
            workflow_type=output.workflow_type.value,
            query=output.query,
            final_stage=output.final_stage.value,
            stages_completed=output.stages_completed,
            stage_results=stage_results,
            final_report=output.final_report,
            report_title=output.report_title,
            total_datasets_found=output.total_datasets_found,
            total_datasets_analyzed=output.total_datasets_analyzed,
            high_quality_datasets=output.high_quality_datasets,
            error_message=output.error_message,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Workflow execution error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow execution error: {str(e)}",
        )


@router.get("/types", summary="List Available Workflow Types")
async def list_workflow_types():
    """
    List all available workflow types with descriptions.

    Returns:
        Dict of workflow types and their descriptions
    """
    from omics_oracle_v2.agents.models.orchestrator import WorkflowType

    return {
        "workflow_types": [
            {
                "type": WorkflowType.FULL_ANALYSIS.value,
                "name": "Full Analysis",
                "description": "Complete analysis: Query -> Search -> Data Validation -> Report",
                "agents": ["QueryAgent", "SearchAgent", "DataAgent", "ReportAgent"],
                "use_case": "Comprehensive dataset analysis with quality validation",
            },
            {
                "type": WorkflowType.SIMPLE_SEARCH.value,
                "name": "Simple Search",
                "description": "Quick search: Query -> Search -> Report",
                "agents": ["QueryAgent", "SearchAgent", "ReportAgent"],
                "use_case": "Fast dataset discovery without quality validation",
            },
            {
                "type": WorkflowType.QUICK_REPORT.value,
                "name": "Quick Report",
                "description": "Direct report: Search -> Report (with dataset IDs)",
                "agents": ["SearchAgent", "ReportAgent"],
                "use_case": "Generate report for known dataset IDs",
            },
            {
                "type": WorkflowType.DATA_VALIDATION.value,
                "name": "Data Validation",
                "description": "Validate and report: Data Validation -> Report",
                "agents": ["DataAgent", "ReportAgent"],
                "use_case": "Quality analysis of existing datasets",
            },
        ]
    }
