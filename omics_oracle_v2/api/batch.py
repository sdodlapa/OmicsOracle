"""
Batch job management for OmicsOracle API.

Manages background processing of multiple workflows with job tracking,
status monitoring, and result retrieval.
"""

import asyncio
import logging
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    """Status of a batch job."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowResult(BaseModel):
    """Result of a single workflow execution in a batch job."""

    workflow_id: str
    status: JobStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class BatchJob(BaseModel):
    """Batch job tracking multiple workflow executions."""

    job_id: str
    status: JobStatus
    total_workflows: int
    completed_workflows: int
    failed_workflows: int
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    workflows: List[WorkflowResult] = []
    metadata: Dict[str, Any] = {}


class BatchJobManager:
    """
    Manages batch jobs for asynchronous workflow processing.

    Stores job state in memory and provides methods for job submission,
    status tracking, and result retrieval.
    """

    def __init__(self):
        """Initialize the batch job manager."""
        self.jobs: Dict[str, BatchJob] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}
        logger.info("BatchJobManager initialized")

    async def create_job(self, workflow_count: int, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a new batch job.

        Args:
            workflow_count: Number of workflows in the batch
            metadata: Optional metadata for the job

        Returns:
            Job ID for tracking
        """
        job_id = str(uuid.uuid4())
        job = BatchJob(
            job_id=job_id,
            status=JobStatus.PENDING,
            total_workflows=workflow_count,
            completed_workflows=0,
            failed_workflows=0,
            created_at=datetime.now(),
            metadata=metadata or {},
        )
        self.jobs[job_id] = job
        logger.info(f"Created batch job {job_id} with {workflow_count} workflows")
        return job_id

    async def start_job(self, job_id: str) -> None:
        """
        Mark a job as started.

        Args:
            job_id: Job ID to start
        """
        if job_id not in self.jobs:
            raise ValueError(f"Job {job_id} not found")

        job = self.jobs[job_id]
        job.status = JobStatus.RUNNING
        job.started_at = datetime.now()
        logger.info(f"Started batch job {job_id}")

    async def add_workflow_result(
        self,
        job_id: str,
        workflow_id: str,
        status: JobStatus,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> None:
        """
        Add a workflow result to a batch job.

        Args:
            job_id: Job ID
            workflow_id: Workflow ID
            status: Workflow execution status
            result: Optional workflow result data
            error: Optional error message if failed
        """
        if job_id not in self.jobs:
            raise ValueError(f"Job {job_id} not found")

        job = self.jobs[job_id]

        # Create workflow result
        workflow_result = WorkflowResult(
            workflow_id=workflow_id,
            status=status,
            completed_at=datetime.now(),
            result=result,
            error=error,
        )

        # Update existing workflow or add new one
        existing = False
        for i, wf in enumerate(job.workflows):
            if wf.workflow_id == workflow_id:
                job.workflows[i] = workflow_result
                existing = True
                break

        if not existing:
            job.workflows.append(workflow_result)

        # Update job counters
        if status == JobStatus.COMPLETED:
            job.completed_workflows += 1
        elif status == JobStatus.FAILED:
            job.failed_workflows += 1

        # Check if job is complete
        total_finished = job.completed_workflows + job.failed_workflows
        if total_finished >= job.total_workflows:
            await self.complete_job(job_id)

        logger.info(f"Added workflow {workflow_id} result to job {job_id}: {status}")

    async def complete_job(self, job_id: str) -> None:
        """
        Mark a job as completed.

        Args:
            job_id: Job ID to complete
        """
        if job_id not in self.jobs:
            raise ValueError(f"Job {job_id} not found")

        job = self.jobs[job_id]

        # Determine final status based on workflow results
        if job.failed_workflows == 0:
            job.status = JobStatus.COMPLETED
        elif job.completed_workflows == 0:
            job.status = JobStatus.FAILED
        else:
            # Some succeeded, some failed - mark as completed with mixed results
            job.status = JobStatus.COMPLETED

        job.completed_at = datetime.now()

        # Clean up running task if exists
        if job_id in self.running_tasks:
            del self.running_tasks[job_id]

        logger.info(
            f"Completed batch job {job_id}: " f"{job.completed_workflows}/{job.total_workflows} successful"
        )

    async def cancel_job(self, job_id: str) -> None:
        """
        Cancel a running job.

        Args:
            job_id: Job ID to cancel
        """
        if job_id not in self.jobs:
            raise ValueError(f"Job {job_id} not found")

        job = self.jobs[job_id]

        # Cancel the running task if exists
        if job_id in self.running_tasks:
            task = self.running_tasks[job_id]
            task.cancel()
            del self.running_tasks[job_id]

        job.status = JobStatus.CANCELLED
        job.completed_at = datetime.now()
        logger.info(f"Cancelled batch job {job_id}")

    def get_job(self, job_id: str) -> Optional[BatchJob]:
        """
        Get a job by ID.

        Args:
            job_id: Job ID to retrieve

        Returns:
            Batch job or None if not found
        """
        return self.jobs.get(job_id)

    def list_jobs(self, status: Optional[JobStatus] = None, limit: int = 100) -> List[BatchJob]:
        """
        List batch jobs, optionally filtered by status.

        Args:
            status: Optional status filter
            limit: Maximum number of jobs to return

        Returns:
            List of batch jobs
        """
        jobs = list(self.jobs.values())

        # Filter by status if provided
        if status:
            jobs = [job for job in jobs if job.status == status]

        # Sort by creation time (newest first)
        jobs.sort(key=lambda j: j.created_at, reverse=True)

        return jobs[:limit]

    def get_job_count(self, status: Optional[JobStatus] = None) -> int:
        """
        Get count of jobs, optionally filtered by status.

        Args:
            status: Optional status filter

        Returns:
            Number of jobs
        """
        if status:
            return sum(1 for job in self.jobs.values() if job.status == status)
        return len(self.jobs)

    async def register_task(self, job_id: str, task: asyncio.Task) -> None:
        """
        Register a background task for a job.

        Args:
            job_id: Job ID
            task: Asyncio task to register
        """
        self.running_tasks[job_id] = task
        logger.info(f"Registered background task for job {job_id}")

    def cleanup_old_jobs(self, max_jobs: int = 1000) -> int:
        """
        Clean up old completed jobs to prevent memory growth.

        Args:
            max_jobs: Maximum number of jobs to keep

        Returns:
            Number of jobs cleaned up
        """
        if len(self.jobs) <= max_jobs:
            return 0

        # Get completed/failed/cancelled jobs sorted by completion time
        completed_jobs = [
            (job.job_id, job.completed_at or job.created_at)
            for job in self.jobs.values()
            if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]
        ]
        completed_jobs.sort(key=lambda x: x[1])

        # Remove oldest jobs
        to_remove = len(self.jobs) - max_jobs
        removed = 0
        for job_id, _ in completed_jobs[:to_remove]:
            if job_id in self.jobs:
                del self.jobs[job_id]
                removed += 1

        if removed > 0:
            logger.info(f"Cleaned up {removed} old batch jobs")

        return removed


# Global batch job manager instance
batch_manager = BatchJobManager()
