"""
Batch processing endpoints for OmicsOracle API.

Provides REST endpoints for submitting batch jobs, checking status,
and retrieving results.
"""

import asyncio
import logging
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from pydantic import BaseModel, Field

from omics_oracle_v2.api.batch import JobStatus, batch_manager
from omics_oracle_v2.api.dependencies import (
    get_data_agent,
    get_query_agent,
    get_report_agent,
    get_search_agent,
)
from omics_oracle_v2.api.routes.workflows import WorkflowRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/batch", tags=["batch"])


class BatchWorkflowRequest(BaseModel):
    """Request to submit multiple workflows as a batch job."""

    workflows: List[WorkflowRequest] = Field(..., description="List of workflows to execute")
    metadata: Optional[dict] = Field(None, description="Optional metadata for the batch job")


class BatchJobResponse(BaseModel):
    """Response for batch job submission."""

    job_id: str = Field(..., description="Unique job identifier")
    status: JobStatus = Field(..., description="Current job status")
    total_workflows: int = Field(..., description="Total number of workflows")
    message: str = Field(..., description="Status message")


class BatchJobStatusResponse(BaseModel):
    """Response for batch job status query."""

    job_id: str
    status: JobStatus
    total_workflows: int
    completed_workflows: int
    failed_workflows: int
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    progress_percentage: float = Field(..., description="Completion percentage (0-100)")


class BatchJobResultResponse(BaseModel):
    """Response for batch job results."""

    job_id: str
    status: JobStatus
    total_workflows: int
    completed_workflows: int
    failed_workflows: int
    workflows: List[dict]
    metadata: dict


class BatchJobListResponse(BaseModel):
    """Response for listing batch jobs."""

    jobs: List[BatchJobStatusResponse]
    total: int


async def execute_batch_workflows(job_id: str, workflows: List[WorkflowRequest]) -> None:
    """
    Execute workflows in a batch job.

    Args:
        job_id: Batch job ID
        workflows: List of workflow requests to execute
    """
    try:
        # Start the job
        await batch_manager.start_job(job_id)

        # Get agent instances
        query_agent = get_query_agent()
        search_agent = get_search_agent()
        data_agent = get_data_agent()
        report_agent = get_report_agent()

        # Execute each workflow
        for i, workflow_req in enumerate(workflows):
            workflow_id = f"{job_id}-workflow-{i}"

            try:
                logger.info(f"Executing workflow {i+1}/{len(workflows)} " f"in job {job_id}")

                # Execute workflow based on type
                if workflow_req.workflow_type == "full_analysis":
                    # Full pipeline: Query -> Search -> Data -> Report
                    query_result = await query_agent.execute(workflow_req.query)
                    search_result = await search_agent.execute(query_result["query"])
                    data_result = await data_agent.execute(search_result.get("dataset_ids", []))
                    report_result = await report_agent.execute(
                        {
                            "query": query_result,
                            "search": search_result,
                            "data": data_result,
                        }
                    )
                    result = {
                        "query": query_result,
                        "search": search_result,
                        "data": data_result,
                        "report": report_result,
                    }

                elif workflow_req.workflow_type == "simple_search":
                    # Simple: Query -> Search -> Report
                    query_result = await query_agent.execute(workflow_req.query)
                    search_result = await search_agent.execute(query_result["query"])
                    report_result = await report_agent.execute(
                        {"query": query_result, "search": search_result}
                    )
                    result = {
                        "query": query_result,
                        "search": search_result,
                        "report": report_result,
                    }

                elif workflow_req.workflow_type == "quick_report":
                    # Quick: Search -> Report
                    search_result = await search_agent.execute(workflow_req.query)
                    report_result = await report_agent.execute({"search": search_result})
                    result = {"search": search_result, "report": report_result}

                else:  # data_validation
                    # Data validation: Data -> Report
                    data_result = await data_agent.execute(workflow_req.dataset_ids or [])
                    report_result = await report_agent.execute({"data": data_result})
                    result = {"data": data_result, "report": report_result}

                # Add successful result
                await batch_manager.add_workflow_result(
                    job_id=job_id,
                    workflow_id=workflow_id,
                    status=JobStatus.COMPLETED,
                    result=result,
                )

            except Exception as e:
                logger.error(f"Workflow {workflow_id} failed in job {job_id}: {str(e)}")
                await batch_manager.add_workflow_result(
                    job_id=job_id,
                    workflow_id=workflow_id,
                    status=JobStatus.FAILED,
                    error=str(e),
                )

    except Exception as e:
        logger.error(f"Batch job {job_id} failed: {str(e)}")
        # Mark remaining workflows as failed
        job = batch_manager.get_job(job_id)
        if job:
            remaining = job.total_workflows - len(job.workflows)
            for i in range(remaining):
                workflow_id = f"{job_id}-workflow-{len(job.workflows) + i}"
                await batch_manager.add_workflow_result(
                    job_id=job_id,
                    workflow_id=workflow_id,
                    status=JobStatus.FAILED,
                    error="Batch job execution failed",
                )


@router.post("/jobs", response_model=BatchJobResponse)
async def submit_batch_job(request: BatchWorkflowRequest, background_tasks: BackgroundTasks):
    """
    Submit a batch job with multiple workflows.

    The workflows will be executed asynchronously in the background.
    Use the returned job_id to check status and retrieve results.
    """
    if not request.workflows:
        raise HTTPException(status_code=400, detail="No workflows provided")

    # Create batch job
    job_id = await batch_manager.create_job(
        workflow_count=len(request.workflows), metadata=request.metadata or {}
    )

    # Schedule background execution
    task = asyncio.create_task(execute_batch_workflows(job_id, request.workflows))
    await batch_manager.register_task(job_id, task)

    logger.info(f"Submitted batch job {job_id} with {len(request.workflows)} workflows")

    return BatchJobResponse(
        job_id=job_id,
        status=JobStatus.PENDING,
        total_workflows=len(request.workflows),
        message=f"Batch job submitted with {len(request.workflows)} workflows",
    )


@router.get("/jobs/{job_id}/status", response_model=BatchJobStatusResponse)
async def get_job_status(job_id: str):
    """Get the status of a batch job."""
    job = batch_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Calculate progress
    total_finished = job.completed_workflows + job.failed_workflows
    progress = (total_finished / job.total_workflows * 100) if job.total_workflows > 0 else 0

    return BatchJobStatusResponse(
        job_id=job.job_id,
        status=job.status,
        total_workflows=job.total_workflows,
        completed_workflows=job.completed_workflows,
        failed_workflows=job.failed_workflows,
        created_at=job.created_at.isoformat(),
        started_at=job.started_at.isoformat() if job.started_at else None,
        completed_at=job.completed_at.isoformat() if job.completed_at else None,
        progress_percentage=progress,
    )


@router.get("/jobs/{job_id}/results", response_model=BatchJobResultResponse)
async def get_job_results(job_id: str):
    """Get the results of a completed batch job."""
    job = batch_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Convert workflow results to dict
    workflows = [
        {
            "workflow_id": wf.workflow_id,
            "status": wf.status,
            "started_at": wf.started_at.isoformat() if wf.started_at else None,
            "completed_at": wf.completed_at.isoformat() if wf.completed_at else None,
            "result": wf.result,
            "error": wf.error,
        }
        for wf in job.workflows
    ]

    return BatchJobResultResponse(
        job_id=job.job_id,
        status=job.status,
        total_workflows=job.total_workflows,
        completed_workflows=job.completed_workflows,
        failed_workflows=job.failed_workflows,
        workflows=workflows,
        metadata=job.metadata,
    )


@router.delete("/jobs/{job_id}")
async def cancel_job(job_id: str):
    """Cancel a running batch job."""
    job = batch_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
        raise HTTPException(status_code=400, detail=f"Cannot cancel job with status {job.status}")

    await batch_manager.cancel_job(job_id)

    return {"message": f"Job {job_id} cancelled successfully"}


@router.get("/jobs", response_model=BatchJobListResponse)
async def list_jobs(
    status: Optional[JobStatus] = Query(None, description="Filter by job status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum jobs to return"),
):
    """List batch jobs, optionally filtered by status."""
    jobs = batch_manager.list_jobs(status=status, limit=limit)

    # Convert to response format
    job_responses = [
        BatchJobStatusResponse(
            job_id=job.job_id,
            status=job.status,
            total_workflows=job.total_workflows,
            completed_workflows=job.completed_workflows,
            failed_workflows=job.failed_workflows,
            created_at=job.created_at.isoformat(),
            started_at=job.started_at.isoformat() if job.started_at else None,
            completed_at=job.completed_at.isoformat() if job.completed_at else None,
            progress_percentage=(
                (job.completed_workflows + job.failed_workflows) / job.total_workflows * 100
                if job.total_workflows > 0
                else 0
            ),
        )
        for job in jobs
    ]

    return BatchJobListResponse(jobs=job_responses, total=batch_manager.get_job_count(status=status))
