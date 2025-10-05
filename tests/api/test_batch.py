"""
Tests for batch processing endpoints.

Based on successful manual tests - tests batch job creation and management.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestBatchJobs:
    """Test batch job endpoints."""

    async def test_create_batch_job(self, authenticated_client):
        """Test creating a batch job."""
        client, _ = authenticated_client
        response = await client.post(
            "/api/v1/batch/jobs",
            json={
                "queries": ["cancer", "diabetes", "alzheimer"],
                "workflow_type": "simple_search",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "job_id" in data
        assert data["status"] in ["queued", "pending"]
        assert data["total_queries"] == 3

    async def test_list_batch_jobs(self, authenticated_client):
        """Test listing batch jobs."""
        client, _ = authenticated_client
        response = await client.get("/api/v1/batch/jobs")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_get_batch_job_status(self, authenticated_client):
        """Test getting batch job status."""
        client, _ = authenticated_client

        # Create a job first
        create_response = await client.post(
            "/api/v1/batch/jobs",
            json={
                "queries": ["test1", "test2"],
                "workflow_type": "simple_search",
            },
        )
        assert create_response.status_code == 201
        job_id = create_response.json()["job_id"]

        # Get job status
        response = await client.get(f"/api/v1/batch/jobs/{job_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == job_id
        assert "status" in data
        assert "progress" in data

    async def test_batch_job_without_auth(self, client: AsyncClient):
        """Test creating batch job without authentication fails."""
        response = await client.post(
            "/api/v1/batch/jobs",
            json={
                "queries": ["test"],
                "workflow_type": "simple_search",
            },
        )
        assert response.status_code == 401

    async def test_batch_job_empty_queries(self, authenticated_client):
        """Test creating batch job with empty queries fails."""
        client, _ = authenticated_client
        response = await client.post(
            "/api/v1/batch/jobs",
            json={
                "queries": [],
                "workflow_type": "simple_search",
            },
        )
        assert response.status_code == 422

    async def test_batch_job_invalid_workflow(self, authenticated_client):
        """Test creating batch job with invalid workflow type fails."""
        client, _ = authenticated_client
        response = await client.post(
            "/api/v1/batch/jobs",
            json={
                "queries": ["test"],
                "workflow_type": "invalid_workflow",
            },
        )
        assert response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.slow
class TestBatchJobExecution:
    """Test batch job execution (slower tests)."""

    async def test_batch_job_with_multiple_queries(self, authenticated_client):
        """Test batch job with multiple queries."""
        client, _ = authenticated_client
        response = await client.post(
            "/api/v1/batch/jobs",
            json={
                "queries": ["cancer", "diabetes", "alzheimer", "parkinsons"],
                "workflow_type": "simple_search",
                "max_results": 2,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["total_queries"] == 4

    async def test_batch_job_full_analysis_workflow(self, authenticated_client):
        """Test batch job with full analysis workflow."""
        client, _ = authenticated_client
        response = await client.post(
            "/api/v1/batch/jobs",
            json={
                "queries": ["breast cancer"],
                "workflow_type": "full_analysis",
                "max_results": 3,
            },
        )
        assert response.status_code == 201
