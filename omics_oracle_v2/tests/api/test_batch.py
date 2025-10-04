"""
Tests for batch processing endpoints.

Tests batch job submission, status tracking, result retrieval,
and job management.
"""

import pytest
from fastapi.testclient import TestClient

from omics_oracle_v2.api.batch import JobStatus, batch_manager
from omics_oracle_v2.api.main import create_app


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def cleanup_jobs():
    """Clean up batch jobs after each test."""
    yield
    # Clear all jobs
    batch_manager.jobs.clear()
    batch_manager.running_tasks.clear()


class TestBatchJobSubmission:
    """Tests for batch job submission."""

    def test_submit_batch_job(self, client, cleanup_jobs):
        """Test submitting a batch job with multiple workflows."""
        response = client.post(
            "/api/v1/batch/jobs",
            json={
                "workflows": [
                    {
                        "workflow_type": "quick_report",
                        "query": "cancer genomics",
                    },
                    {
                        "workflow_type": "quick_report",
                        "query": "diabetes research",
                    },
                ],
                "metadata": {"user": "test_user", "priority": "high"},
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "pending"
        assert data["total_workflows"] == 2
        assert "submitted" in data["message"].lower()

    def test_submit_empty_batch_job(self, client, cleanup_jobs):
        """Test submitting a batch job with no workflows."""
        response = client.post("/api/v1/batch/jobs", json={"workflows": []})

        assert response.status_code == 400
        assert "no workflows" in response.json()["detail"].lower()

    def test_submit_batch_with_metadata(self, client, cleanup_jobs):
        """Test submitting a batch job with metadata."""
        metadata = {"experiment": "test_123", "timestamp": "2025-10-04"}

        response = client.post(
            "/api/v1/batch/jobs",
            json={
                "workflows": [{"workflow_type": "quick_report", "query": "test query"}],
                "metadata": metadata,
            },
        )

        assert response.status_code == 200
        data = response.json()
        job_id = data["job_id"]

        # Verify metadata is stored
        job = batch_manager.get_job(job_id)
        assert job.metadata == metadata


class TestBatchJobStatus:
    """Tests for batch job status endpoints."""

    @pytest.mark.asyncio
    async def test_get_job_status(self, client, cleanup_jobs):
        """Test getting status of a batch job."""
        # Create a job
        job_id = await batch_manager.create_job(workflow_count=3, metadata={"test": "status"})

        response = client.get(f"/api/v1/batch/jobs/{job_id}/status")

        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == job_id
        assert data["status"] == "pending"
        assert data["total_workflows"] == 3
        assert data["completed_workflows"] == 0
        assert data["failed_workflows"] == 0
        assert data["progress_percentage"] == 0.0
        assert "created_at" in data

    def test_get_nonexistent_job_status(self, client, cleanup_jobs):
        """Test getting status of a non-existent job."""
        response = client.get("/api/v1/batch/jobs/nonexistent-id/status")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_job_status_with_progress(self, client, cleanup_jobs):
        """Test job status shows correct progress."""
        # Create job and add some results
        job_id = await batch_manager.create_job(workflow_count=4)
        await batch_manager.start_job(job_id)

        # Complete 2 workflows
        await batch_manager.add_workflow_result(job_id, "wf1", JobStatus.COMPLETED, result={"data": "test1"})
        await batch_manager.add_workflow_result(job_id, "wf2", JobStatus.COMPLETED, result={"data": "test2"})

        response = client.get(f"/api/v1/batch/jobs/{job_id}/status")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
        assert data["completed_workflows"] == 2
        assert data["progress_percentage"] == 50.0  # 2/4 = 50%


class TestBatchJobResults:
    """Tests for batch job results endpoints."""

    @pytest.mark.asyncio
    async def test_get_job_results(self, client, cleanup_jobs):
        """Test getting results of a completed batch job."""
        # Create and complete a job
        job_id = await batch_manager.create_job(workflow_count=2)
        await batch_manager.start_job(job_id)

        await batch_manager.add_workflow_result(
            job_id,
            "wf1",
            JobStatus.COMPLETED,
            result={"report": "result 1"},
        )
        await batch_manager.add_workflow_result(
            job_id,
            "wf2",
            JobStatus.COMPLETED,
            result={"report": "result 2"},
        )

        response = client.get(f"/api/v1/batch/jobs/{job_id}/results")

        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == job_id
        assert data["status"] == "completed"
        assert len(data["workflows"]) == 2
        assert data["workflows"][0]["status"] == "completed"
        assert data["workflows"][0]["result"]["report"] == "result 1"

    def test_get_nonexistent_job_results(self, client, cleanup_jobs):
        """Test getting results of a non-existent job."""
        response = client.get("/api/v1/batch/jobs/nonexistent-id/results")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_results_with_failures(self, client, cleanup_jobs):
        """Test getting results when some workflows failed."""
        job_id = await batch_manager.create_job(workflow_count=3)
        await batch_manager.start_job(job_id)

        await batch_manager.add_workflow_result(job_id, "wf1", JobStatus.COMPLETED, result={"data": "ok"})
        await batch_manager.add_workflow_result(job_id, "wf2", JobStatus.FAILED, error="Test error")
        await batch_manager.add_workflow_result(job_id, "wf3", JobStatus.COMPLETED, result={"data": "ok"})

        response = client.get(f"/api/v1/batch/jobs/{job_id}/results")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"  # Overall status
        assert data["completed_workflows"] == 2
        assert data["failed_workflows"] == 1

        # Check failed workflow has error
        failed_wf = next(wf for wf in data["workflows"] if wf["status"] == "failed")
        assert failed_wf["error"] == "Test error"
        assert failed_wf["result"] is None


class TestBatchJobCancellation:
    """Tests for batch job cancellation."""

    @pytest.mark.asyncio
    async def test_cancel_running_job(self, client, cleanup_jobs):
        """Test cancelling a running batch job."""
        # Create and start a job
        job_id = await batch_manager.create_job(workflow_count=5)
        await batch_manager.start_job(job_id)

        response = client.delete(f"/api/v1/batch/jobs/{job_id}")

        assert response.status_code == 200
        assert "cancelled" in response.json()["message"].lower()

        # Verify job is cancelled
        job = batch_manager.get_job(job_id)
        assert job.status == JobStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_cancel_completed_job(self, client, cleanup_jobs):
        """Test cancelling a completed job fails."""
        # Create and complete a job
        job_id = await batch_manager.create_job(workflow_count=1)
        await batch_manager.start_job(job_id)
        await batch_manager.add_workflow_result(job_id, "wf1", JobStatus.COMPLETED, result={})

        response = client.delete(f"/api/v1/batch/jobs/{job_id}")

        assert response.status_code == 400
        assert "cannot cancel" in response.json()["detail"].lower()

    def test_cancel_nonexistent_job(self, client, cleanup_jobs):
        """Test cancelling a non-existent job."""
        response = client.delete("/api/v1/batch/jobs/nonexistent-id")
        assert response.status_code == 404


class TestBatchJobListing:
    """Tests for batch job listing endpoints."""

    @pytest.mark.asyncio
    async def test_list_all_jobs(self, client, cleanup_jobs):
        """Test listing all batch jobs."""
        # Create multiple jobs
        _job1 = await batch_manager.create_job(workflow_count=1)
        await batch_manager.create_job(workflow_count=2)
        _job3 = await batch_manager.create_job(workflow_count=3)

        response = client.get("/api/v1/batch/jobs")

        assert response.status_code == 200
        data = response.json()
        assert "jobs" in data
        assert "total" in data
        assert data["total"] == 3
        assert len(data["jobs"]) == 3

        # Jobs should be sorted by creation time (newest first)
        job_ids = [job["job_id"] for job in data["jobs"]]
        assert job_ids[0] == _job3  # Most recent
        assert job_ids[2] == _job1  # Oldest

    @pytest.mark.asyncio
    async def test_list_jobs_by_status(self, client, cleanup_jobs):
        """Test listing jobs filtered by status."""
        # Create jobs with different statuses
        await batch_manager.create_job(workflow_count=1)  # pending
        job2 = await batch_manager.create_job(workflow_count=1)
        job3 = await batch_manager.create_job(workflow_count=1)

        await batch_manager.start_job(job2)
        await batch_manager.add_workflow_result(job3, "wf1", JobStatus.COMPLETED, result={})

        # List pending jobs
        response = client.get("/api/v1/batch/jobs?status=pending")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["jobs"][0]["status"] == "pending"

        # List running jobs
        response = client.get("/api/v1/batch/jobs?status=running")
        data = response.json()
        assert data["total"] == 1
        assert data["jobs"][0]["status"] == "running"

        # List completed jobs
        response = client.get("/api/v1/batch/jobs?status=completed")
        data = response.json()
        assert data["total"] == 1
        assert data["jobs"][0]["status"] == "completed"

    @pytest.mark.asyncio
    async def test_list_jobs_with_limit(self, client, cleanup_jobs):
        """Test listing jobs with limit parameter."""
        # Create multiple jobs
        for _ in range(10):
            await batch_manager.create_job(workflow_count=1)

        response = client.get("/api/v1/batch/jobs?limit=5")

        assert response.status_code == 200
        data = response.json()
        assert len(data["jobs"]) == 5
        assert data["total"] == 10


class TestBatchManager:
    """Tests for BatchJobManager functionality."""

    @pytest.mark.asyncio
    async def test_create_job(self, cleanup_jobs):
        """Test creating a batch job."""
        job_id = await batch_manager.create_job(workflow_count=5, metadata={"test": "data"})

        assert job_id is not None
        job = batch_manager.get_job(job_id)
        assert job is not None
        assert job.total_workflows == 5
        assert job.status == JobStatus.PENDING
        assert job.metadata["test"] == "data"

    @pytest.mark.asyncio
    async def test_job_completion(self, cleanup_jobs):
        """Test automatic job completion when all workflows finish."""
        job_id = await batch_manager.create_job(workflow_count=2)
        await batch_manager.start_job(job_id)

        # Add first result - job should still be running
        await batch_manager.add_workflow_result(job_id, "wf1", JobStatus.COMPLETED, result={})
        job = batch_manager.get_job(job_id)
        assert job.status == JobStatus.RUNNING

        # Add second result - job should complete
        await batch_manager.add_workflow_result(job_id, "wf2", JobStatus.COMPLETED, result={})
        job = batch_manager.get_job(job_id)
        assert job.status == JobStatus.COMPLETED
        assert job.completed_at is not None

    @pytest.mark.asyncio
    async def test_cleanup_old_jobs(self, cleanup_jobs):
        """Test cleaning up old completed jobs."""
        # Create many completed jobs
        for i in range(15):
            job_id = await batch_manager.create_job(workflow_count=1)
            await batch_manager.start_job(job_id)
            await batch_manager.add_workflow_result(job_id, "wf1", JobStatus.COMPLETED, result={})

        assert batch_manager.get_job_count() == 15

        # Cleanup keeping only 10
        removed = batch_manager.cleanup_old_jobs(max_jobs=10)

        assert removed == 5
        assert batch_manager.get_job_count() == 10
