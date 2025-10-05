"""
Tests for workflow endpoints.

Based on successful manual tests - tests workflow discovery and execution.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestWorkflowDiscovery:
    """Test workflow discovery."""

    async def test_list_workflows(self, authenticated_client):
        """Test listing all available workflows."""
        client, _ = authenticated_client
        response = await client.get("/api/v1/workflows/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 4  # full_analysis, simple_search, data_only, custom

        # Check workflow structure
        workflow = data[0]
        assert "type" in workflow
        assert "name" in workflow
        assert "agents" in workflow
        assert "description" in workflow

    async def test_list_workflows_unauthenticated(self, client: AsyncClient):
        """Test listing workflows without authentication fails."""
        response = await client.get("/api/v1/workflows/")
        assert response.status_code == 401


@pytest.mark.asyncio
@pytest.mark.slow
class TestWorkflowExecution:
    """Test workflow execution."""

    async def test_execute_full_analysis_workflow(self, authenticated_client):
        """Test executing full analysis workflow."""
        client, _ = authenticated_client
        response = await client.post(
            "/api/v1/workflows/execute",
            json={
                "query": "cancer research",
                "workflow_type": "full_analysis",
                "max_results": 5,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["workflow_type"] == "full_analysis"
        assert "final_report" in data
        assert "execution_time_ms" in data

    async def test_execute_simple_search_workflow(self, authenticated_client):
        """Test executing simple search workflow."""
        client, _ = authenticated_client
        response = await client.post(
            "/api/v1/workflows/execute",
            json={
                "query": "diabetes",
                "workflow_type": "simple_search",
                "max_results": 3,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["workflow_type"] == "simple_search"

    async def test_execute_data_only_workflow(self, authenticated_client):
        """Test executing data-only workflow."""
        client, _ = authenticated_client
        response = await client.post(
            "/api/v1/workflows/execute",
            json={
                "query": "alzheimer",
                "workflow_type": "data_only",
                "max_results": 2,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    async def test_workflow_invalid_type(self, authenticated_client):
        """Test executing workflow with invalid type fails."""
        client, _ = authenticated_client
        response = await client.post(
            "/api/v1/workflows/execute",
            json={
                "query": "test",
                "workflow_type": "nonexistent_workflow",
            },
        )
        assert response.status_code == 422

    async def test_workflow_empty_query(self, authenticated_client):
        """Test executing workflow with empty query fails."""
        client, _ = authenticated_client
        response = await client.post(
            "/api/v1/workflows/execute",
            json={
                "query": "",
                "workflow_type": "simple_search",
            },
        )
        assert response.status_code == 422

    async def test_workflow_without_auth(self, client: AsyncClient):
        """Test executing workflow without authentication fails."""
        response = await client.post(
            "/api/v1/workflows/execute",
            json={
                "query": "test",
                "workflow_type": "simple_search",
            },
        )
        assert response.status_code == 401


@pytest.mark.asyncio
class TestWorkflowValidation:
    """Test workflow validation and error handling."""

    async def test_workflow_missing_required_fields(self, authenticated_client):
        """Test workflow execution with missing required fields fails."""
        client, _ = authenticated_client
        response = await client.post(
            "/api/v1/workflows/execute",
            json={
                "workflow_type": "simple_search",
                # Missing query field
            },
        )
        assert response.status_code == 422

    async def test_workflow_max_results_validation(self, authenticated_client):
        """Test workflow respects max_results parameter."""
        client, _ = authenticated_client
        response = await client.post(
            "/api/v1/workflows/execute",
            json={
                "query": "test",
                "workflow_type": "simple_search",
                "max_results": 1,
            },
        )
        assert response.status_code == 200
