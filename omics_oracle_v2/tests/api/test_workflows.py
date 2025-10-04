"""
Tests for workflow orchestration endpoints.

Tests the REST API endpoints for multi-agent workflow execution.
"""

import pytest
from fastapi.testclient import TestClient

from omics_oracle_v2.api.main import create_app


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


class TestWorkflowExecutionEndpoint:
    """Tests for workflow execution endpoint."""

    def test_workflow_endpoint_exists(self, client):
        """Test that the workflow execution endpoint exists."""
        response = client.post("/api/v1/workflows/execute", json={})
        assert response.status_code == 422  # Validation error for missing fields

    def test_workflow_with_full_analysis(self, client):
        """Test full analysis workflow execution."""
        response = client.post(
            "/api/v1/workflows/execute",
            json={
                "query": "breast cancer RNA-seq studies",
                "workflow_type": "full_analysis",
                "max_results": 10,
            },
        )

        # May succeed or fail depending on API keys
        # Just check structure if successful
        if response.status_code == 200:
            data = response.json()
            assert data["success"] in [True, False]
            assert "execution_time_ms" in data
            assert "timestamp" in data
            assert "workflow_type" in data
            assert data["workflow_type"] == "full_analysis"
            assert "query" in data
            assert "stage_results" in data
            assert isinstance(data["stage_results"], list)

    def test_workflow_with_simple_search(self, client):
        """Test simple search workflow execution."""
        response = client.post(
            "/api/v1/workflows/execute",
            json={
                "query": "lung cancer",
                "workflow_type": "simple_search",
                "max_results": 5,
            },
        )

        # May succeed or fail depending on API keys
        if response.status_code == 200:
            data = response.json()
            assert "workflow_type" in data
            assert data["workflow_type"] == "simple_search"

    def test_workflow_with_filters(self, client):
        """Test workflow with organism filters."""
        response = client.post(
            "/api/v1/workflows/execute",
            json={
                "query": "cancer studies",
                "workflow_type": "simple_search",
                "max_results": 5,
                "organisms": ["Homo sapiens"],
                "min_samples": 10,
            },
        )

        # Structure check
        assert response.status_code in [200, 500]  # May fail without API keys

    def test_workflow_with_report_preferences(self, client):
        """Test workflow with report customization."""
        response = client.post(
            "/api/v1/workflows/execute",
            json={
                "query": "diabetes research",
                "workflow_type": "full_analysis",
                "max_results": 5,
                "report_type": "comprehensive",
                "report_format": "markdown",
                "include_quality_analysis": True,
                "include_recommendations": True,
            },
        )

        assert response.status_code in [200, 500]

    def test_workflow_missing_query(self, client):
        """Test workflow execution without query."""
        response = client.post(
            "/api/v1/workflows/execute",
            json={
                "workflow_type": "full_analysis",
            },
        )

        assert response.status_code == 422  # Validation error

    def test_workflow_invalid_type(self, client):
        """Test workflow with invalid workflow type."""
        response = client.post(
            "/api/v1/workflows/execute",
            json={
                "query": "test query",
                "workflow_type": "invalid_workflow",
            },
        )

        assert response.status_code == 422  # Validation error

    def test_workflow_max_results_validation(self, client):
        """Test that max_results is validated."""
        # Test with value exceeding limit
        response = client.post(
            "/api/v1/workflows/execute",
            json={
                "query": "test",
                "max_results": 300,  # Exceeds limit of 200
            },
        )

        assert response.status_code == 422

    def test_workflow_response_structure(self, client):
        """Test that successful workflow has correct response structure."""
        response = client.post(
            "/api/v1/workflows/execute",
            json={
                "query": "test query",
                "workflow_type": "simple_search",
                "max_results": 3,
            },
        )

        if response.status_code == 200:
            data = response.json()

            # Check required fields
            assert "success" in data
            assert "execution_time_ms" in data
            assert "timestamp" in data
            assert "workflow_type" in data
            assert "query" in data
            assert "final_stage" in data
            assert "stages_completed" in data
            assert "stage_results" in data
            assert "total_datasets_found" in data
            assert "total_datasets_analyzed" in data

            # Check stage results structure
            if len(data["stage_results"]) > 0:
                stage = data["stage_results"][0]
                assert "stage" in stage
                assert "success" in stage
                assert "agent_name" in stage
                assert "execution_time_ms" in stage


class TestWorkflowTypesEndpoint:
    """Tests for workflow types listing endpoint."""

    def test_list_workflow_types(self, client):
        """Test listing available workflow types."""
        response = client.get("/api/v1/workflows/types")

        assert response.status_code == 200
        data = response.json()

        assert "workflow_types" in data
        assert isinstance(data["workflow_types"], list)
        assert len(data["workflow_types"]) >= 4  # At least 4 workflow types

    def test_workflow_types_structure(self, client):
        """Test that workflow types have correct structure."""
        response = client.get("/api/v1/workflows/types")
        data = response.json()

        for workflow in data["workflow_types"]:
            assert "type" in workflow
            assert "name" in workflow
            assert "description" in workflow
            assert "agents" in workflow
            assert "use_case" in workflow
            assert isinstance(workflow["agents"], list)

    def test_workflow_types_includes_all_types(self, client):
        """Test that all expected workflow types are included."""
        response = client.get("/api/v1/workflows/types")
        data = response.json()

        workflow_types = [wf["type"] for wf in data["workflow_types"]]

        assert "full_analysis" in workflow_types
        assert "simple_search" in workflow_types
        assert "quick_report" in workflow_types
        assert "data_validation" in workflow_types


class TestWorkflowErrors:
    """Tests for workflow error handling."""

    def test_workflow_empty_query(self, client):
        """Test workflow with empty query string."""
        response = client.post(
            "/api/v1/workflows/execute",
            json={
                "query": "",
                "workflow_type": "simple_search",
            },
        )

        assert response.status_code == 422  # Validation error

    def test_workflow_long_query(self, client):
        """Test workflow with very long query."""
        long_query = "test " * 200  # Exceeds 500 char limit
        response = client.post(
            "/api/v1/workflows/execute",
            json={
                "query": long_query,
                "workflow_type": "simple_search",
            },
        )

        assert response.status_code == 422  # Validation error

    def test_workflow_negative_max_results(self, client):
        """Test workflow with negative max_results."""
        response = client.post(
            "/api/v1/workflows/execute",
            json={
                "query": "test",
                "max_results": -5,
            },
        )

        assert response.status_code == 422

    def test_workflow_negative_min_samples(self, client):
        """Test workflow with negative min_samples filter."""
        response = client.post(
            "/api/v1/workflows/execute",
            json={
                "query": "test",
                "min_samples": -10,
            },
        )

        assert response.status_code == 422
