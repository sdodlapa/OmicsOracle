"""
Development Workflow Routes (No Authentication)

SECURITY WARNING: This module bypasses authentication for development testing only.
DO NOT use in production. Delete this file before deploying.

This is a temporary solution to test the frontend without setting up authentication.
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
from omics_oracle_v2.api.models.workflow import WorkflowRequest

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Workflows (Dev)"], prefix="/dev")


# Mock User for Development
class MockUser(BaseModel):
    """Mock user for development testing."""

    id: int = 1
    email: str = "dev@test.com"
    tier: str = "enterprise"
    is_active: bool = True


# Workflow Information Schema
class WorkflowInfo(BaseModel):
    """Information about an available workflow."""

    type: str = Field(..., description="Workflow type identifier")
    name: str = Field(..., description="Human-readable workflow name")
    description: str = Field(..., description="Workflow description")
    agents: List[str] = Field(..., description="Agents used in this workflow")
    use_case: str = Field(..., description="When to use this workflow")


@router.get("/", response_model=List[WorkflowInfo], summary="List Available Workflows (Dev)")
async def list_workflows():
    """
    List all available workflows with their metadata.

    DEV MODE: No authentication required.
    """
    workflows = [
        WorkflowInfo(
            type="simple_search",
            name="Simple Search Workflow",
            description="Quick search and basic report generation (Query -> Search -> Report)",
            agents=["Query Agent", "Search Agent", "Report Agent"],
            use_case="When you need to quickly find datasets matching specific criteria",
        ),
        WorkflowInfo(
            type="full_analysis",
            name="Full Analysis Workflow",
            description="Complete analysis pipeline with data retrieval (Query -> Search -> Data -> Report)",
            agents=["Query Agent", "Search Agent", "Data Agent", "Report Agent"],
            use_case="When you need comprehensive analysis with detailed reports",
        ),
        WorkflowInfo(
            type="quick_report",
            name="Quick Report Workflow",
            description="Generate report from known dataset IDs (Search -> Report)",
            agents=["Search Agent", "Report Agent"],
            use_case="When you already have specific GEO dataset IDs",
        ),
        WorkflowInfo(
            type="data_validation",
            name="Data Validation Workflow",
            description="Validate and report on existing datasets (Data -> Report)",
            agents=["Data Agent", "Report Agent"],
            use_case="When validating quality and completeness of known datasets",
        ),
    ]
    return workflows


@router.post("/execute", summary="Execute Workflow (Dev)")
async def execute_workflow(request: WorkflowRequest, orchestrator: Orchestrator = Depends(get_orchestrator)):
    """
    Execute a multi-agent workflow.

    DEV MODE: No authentication required.
    Uses enterprise tier mock user.

    **Available Workflow Types:**
    - simple_search: Quick search with basic report
    - full_analysis: Complete analysis with detailed report (default)
    - quick_report: Generate report from known dataset IDs
    - data_validation: Validate existing datasets
    """
    logger.info(f"[DEV MODE] Executing {request.workflow_type} workflow: {request.query}")

    # Mock user with enterprise tier (used for orchestrator input)
    # Removed unused variable to pass flake8

    try:
        # Create orchestrator input from request fields
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

        # Execute workflow (NOT async!)
        start_time = time.time()
        result = orchestrator.execute(orchestrator_input)
        execution_time = time.time() - start_time

        if not result.success:
            logger.error(f"[DEV MODE] Workflow failed: {result.error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Workflow execution failed: {result.error}",
            )

        output = result.output

        # Build simplified response matching OrchestratorOutput structure
        response = {
            "success": output.success,
            "execution_time_ms": execution_time * 1000,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "workflow_type": output.workflow_type.value,
            "query": output.query,
            "final_stage": output.final_stage.value,
            "stages_completed": len(output.stage_results),
            "stage_results": [
                {
                    "stage": stage.stage.value,
                    "agent": stage.agent_name,
                    "success": stage.success,
                    "error_message": stage.error,
                    "execution_time_ms": stage.execution_time_ms,
                }
                for stage in output.stage_results
            ],
            "final_report": output.final_report,
            "report_title": output.report_title,
            "total_datasets_found": output.total_datasets_found,
            "total_datasets_analyzed": output.total_datasets_analyzed,
            "high_quality_datasets": output.high_quality_datasets,
            "error_message": output.error_message,
        }

        logger.info(f"[DEV MODE] Workflow completed successfully in {execution_time:.2f}s")

        return response

    except Exception as e:
        logger.exception(f"[DEV MODE] Workflow execution failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Workflow execution failed: {str(e)}"
        )


@router.get("/status", summary="Dev Mode Status")
async def dev_status():
    """
    Get development mode status.

    SECURITY WARNING: This endpoint confirms authentication bypass is active.
    """
    return {
        "mode": "development",
        "authentication": "disabled",
        "mock_user": {"email": "dev@test.com", "tier": "enterprise"},
        "warning": "DO NOT USE IN PRODUCTION - Authentication is bypassed!",
    }
