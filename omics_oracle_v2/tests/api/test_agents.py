"""
Tests for Agent Execution Endpoints (Task 2)

Tests for the individual agent execution endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from omics_oracle_v2.api.main import create_app
from omics_oracle_v2.core import Settings


@pytest.fixture
def app():
    """Create test FastAPI app."""
    settings = Settings()
    return create_app(settings=settings)


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


class TestQueryAgentEndpoint:
    """Tests for Query Agent endpoint."""

    def test_query_endpoint_exists(self, client):
        """Test that the query endpoint exists."""
        # Send invalid request to check endpoint exists
        response = client.post("/api/v1/agents/query", json={})
        # Should get 422 (validation error) not 404
        assert response.status_code == 422

    def test_query_with_valid_input(self, client):
        """Test query endpoint with valid input."""
        response = client.post(
            "/api/v1/agents/query",
            json={"query": "breast cancer RNA-seq studies"},
        )

        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert data["success"] is True
        assert "execution_time_ms" in data
        assert "timestamp" in data
        assert data["original_query"] == "breast cancer RNA-seq studies"
        assert "intent" in data
        assert "confidence" in data
        assert "entities" in data
        assert "search_terms" in data
        assert "entity_counts" in data

    def test_query_with_empty_string(self, client):
        """Test query endpoint with empty string."""
        response = client.post("/api/v1/agents/query", json={"query": ""})
        assert response.status_code == 422  # Validation error

    def test_query_with_long_text(self, client):
        """Test query endpoint with very long text."""
        long_query = "test " * 200  # Very long query
        response = client.post("/api/v1/agents/query", json={"query": long_query})

        # Should fail with 422 (Pydantic validation error - query too long)
        assert response.status_code == 422

    def test_query_entities_structure(self, client):
        """Test that entities have correct structure."""
        response = client.post(
            "/api/v1/agents/query",
            json={"query": "TP53 mutations in lung cancer"},
        )

        assert response.status_code == 200
        data = response.json()

        # Check entities structure
        if data["entities"]:
            entity = data["entities"][0]
            assert "text" in entity
            assert "entity_type" in entity
            assert "confidence" in entity


class TestSearchAgentEndpoint:
    """
    Tests for Search Agent endpoint.

    NOTE: These tests require NCBI_EMAIL environment variable to be set.
    Without it, the SearchAgent will fail to initialize and tests will fail with 500 errors.
    These are integration tests that require real NCBI API access.
    """

    def test_search_endpoint_exists(self, client):
        """Test that the search endpoint exists."""
        response = client.post("/api/v1/agents/search", json={})
        assert response.status_code == 422  # Validation error

    def test_search_with_valid_input(self, client):
        """Test search endpoint with valid input."""
        response = client.post(
            "/api/v1/agents/search",
            json={"search_terms": ["breast cancer", "RNA-seq"], "max_results": 5},
        )

        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert data["success"] is True
        assert "execution_time_ms" in data
        assert "timestamp" in data
        assert "total_found" in data
        assert "datasets" in data
        assert "search_terms_used" in data
        assert "filters_applied" in data

    def test_search_with_filters(self, client):
        """Test search with filters."""
        response = client.post(
            "/api/v1/agents/search",
            json={
                "search_terms": ["cancer"],
                "filters": {"organism": "Homo sapiens"},
                "max_results": 10,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "Homo sapiens" in str(data["filters_applied"])

    def test_search_max_results_validation(self, client):
        """Test that max_results is validated."""
        # Test with value exceeding limit (>100)
        response = client.post(
            "/api/v1/agents/search",
            json={"search_terms": ["cancer"], "max_results": 1000},
        )

        assert response.status_code == 422  # Validation error

    def test_search_dataset_structure(self, client):
        """Test that datasets have correct structure."""
        response = client.post(
            "/api/v1/agents/search",
            json={"search_terms": ["cancer"], "max_results": 3},
        )

        assert response.status_code == 200
        data = response.json()

        # Check dataset structure if any found
        if data["datasets"]:
            dataset = data["datasets"][0]
            assert "geo_id" in dataset
            assert "title" in dataset
            assert "sample_count" in dataset
            assert "relevance_score" in dataset
            assert "match_reasons" in dataset


class TestDataAgentEndpoint:
    """Tests for Data Agent endpoint."""

    def test_validate_endpoint_exists(self, client):
        """Test that the validate endpoint exists."""
        response = client.post("/api/v1/agents/validate", json={})
        assert response.status_code == 422  # Validation error

    def test_validate_with_valid_input(self, client):
        """Test validation endpoint with valid input."""
        response = client.post(
            "/api/v1/agents/validate",
            json={"dataset_ids": ["GSE12345", "GSE67890"]},
        )

        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert data["success"] is True
        assert "execution_time_ms" in data
        assert "timestamp" in data
        assert "total_processed" in data
        assert "validated_datasets" in data
        assert "quality_stats" in data

    def test_validate_with_quality_threshold(self, client):
        """Test validation with quality score threshold."""
        response = client.post(
            "/api/v1/agents/validate",
            json={"dataset_ids": ["GSE12345"], "min_quality_score": 0.7},
        )

        assert response.status_code == 200

    def test_validate_dataset_structure(self, client):
        """Test that validated datasets have correct structure."""
        response = client.post(
            "/api/v1/agents/validate",
            json={"dataset_ids": ["GSE12345"]},
        )

        assert response.status_code == 200
        data = response.json()

        # Check validated dataset structure
        if data["validated_datasets"]:
            dataset = data["validated_datasets"][0]
            assert "geo_id" in dataset
            assert "quality_metrics" in dataset

            metrics = dataset["quality_metrics"]
            assert "quality_score" in metrics
            assert "quality_level" in metrics
            assert "has_publication" in metrics
            assert "has_sra_data" in metrics


class TestReportAgentEndpoint:
    """Tests for Report Agent endpoint."""

    def test_report_endpoint_exists(self, client):
        """Test that the report endpoint exists."""
        response = client.post("/api/v1/agents/report", json={})
        assert response.status_code == 422  # Validation error

    def test_report_with_valid_input(self, client):
        """Test report endpoint with valid input."""
        response = client.post(
            "/api/v1/agents/report",
            json={"dataset_ids": ["GSE12345", "GSE67890"]},
        )

        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert data["success"] is True
        assert "execution_time_ms" in data
        assert "timestamp" in data
        assert "report_type" in data
        assert "report_format" in data
        assert "full_report" in data
        assert "key_findings" in data
        assert "datasets_analyzed" in data

    def test_report_with_options(self, client):
        """Test report with custom options."""
        response = client.post(
            "/api/v1/agents/report",
            json={
                "dataset_ids": ["GSE12345"],
                "report_type": "comprehensive",
                "report_format": "markdown",
                "include_recommendations": True,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["report_type"] == "comprehensive"
        assert data["report_format"] == "markdown"
        assert "recommendations" in data

    def test_report_without_recommendations(self, client):
        """Test report without recommendations."""
        response = client.post(
            "/api/v1/agents/report",
            json={"dataset_ids": ["GSE12345"], "include_recommendations": False},
        )

        assert response.status_code == 200
        data = response.json()
        # Recommendations should be None when not requested
        assert data["recommendations"] is None


class TestAgentEndpointErrors:
    """Tests for error handling in agent endpoints."""

    def test_query_missing_field(self, client):
        """Test query endpoint with missing required field."""
        response = client.post("/api/v1/agents/query", json={})
        assert response.status_code == 422

    def test_search_missing_field(self, client):
        """Test search endpoint with missing required field."""
        response = client.post("/api/v1/agents/search", json={"max_results": 10})
        assert response.status_code == 422

    def test_validate_missing_field(self, client):
        """Test validate endpoint with missing required field."""
        response = client.post("/api/v1/agents/validate", json={})
        assert response.status_code == 422

    def test_report_missing_field(self, client):
        """Test report endpoint with missing required field."""
        response = client.post("/api/v1/agents/report", json={})
        assert response.status_code == 422


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
