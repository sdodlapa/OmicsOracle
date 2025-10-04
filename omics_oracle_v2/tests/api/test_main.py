"""
Tests for FastAPI Application Setup (Task 1)

Tests for the basic FastAPI application, configuration, middleware, and health checks.
"""

import pytest
from fastapi.testclient import TestClient

from omics_oracle_v2.api.config import APISettings
from omics_oracle_v2.api.main import create_app
from omics_oracle_v2.core import Settings


@pytest.fixture
def test_settings():
    """Create test settings."""
    return Settings()


@pytest.fixture
def test_api_settings():
    """Create test API settings."""
    return APISettings(cors_origins=["http://testserver"])


@pytest.fixture
def app(test_settings, test_api_settings):
    """Create test FastAPI app."""
    return create_app(settings=test_settings, api_settings=test_api_settings)


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


class TestAppCreation:
    """Tests for FastAPI application creation."""

    def test_app_creation(self, app):
        """Test that the app can be created successfully."""
        assert app is not None
        assert app.title == "OmicsOracle Agent API"
        assert app.version == "2.0.0"

    def test_app_has_docs(self, app):
        """Test that OpenAPI documentation is configured."""
        assert app.docs_url == "/docs"
        assert app.redoc_url == "/redoc"
        assert app.openapi_url == "/openapi.json"

    def test_app_has_middleware(self, app):
        """Test that middleware is registered."""
        # Check that middleware is present
        assert len(app.user_middleware) > 0


class TestRootEndpoint:
    """Tests for root endpoint."""

    def test_root_endpoint(self, client):
        """Test root endpoint returns API information."""
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == "OmicsOracle Agent API"
        assert data["version"] == "2.0.0"
        assert "docs" in data
        assert "health" in data


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    def test_health_check(self, client):
        """Test basic health check endpoint."""
        response = client.get("/health/")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert data["version"] == "2.0.0"

    def test_readiness_check(self, client):
        """Test readiness check endpoint."""
        response = client.get("/health/ready")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "ready"
        assert "timestamp" in data

    def test_liveness_check(self, client):
        """Test liveness check endpoint."""
        response = client.get("/health/live")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "alive"
        assert "timestamp" in data

    def test_detailed_health_check(self, client):
        """Test detailed health check endpoint."""
        response = client.get("/health/detailed")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert "components" in data
        assert "uptime_seconds" in data
        assert data["uptime_seconds"] >= 0


class TestOpenAPISchema:
    """Tests for OpenAPI schema generation."""

    def test_openapi_schema_accessible(self, client):
        """Test that OpenAPI schema can be retrieved."""
        response = client.get("/openapi.json")
        assert response.status_code == 200

        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema
        assert schema["info"]["title"] == "OmicsOracle Agent API"

    def test_docs_accessible(self, client):
        """Test that Swagger UI is accessible."""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_redoc_accessible(self, client):
        """Test that ReDoc is accessible."""
        response = client.get("/redoc")
        assert response.status_code == 200


class TestMiddleware:
    """Tests for middleware functionality."""

    def test_cors_headers(self, client):
        """Test that CORS headers are set correctly."""
        response = client.get("/health/", headers={"Origin": "http://testserver"})
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers

    def test_process_time_header(self, client):
        """Test that process time header is added."""
        response = client.get("/health/")
        assert response.status_code == 200
        assert "x-process-time" in response.headers

        # Verify it's a valid float
        process_time = float(response.headers["x-process-time"])
        assert process_time >= 0


class TestErrorHandling:
    """Tests for error handling."""

    def test_404_not_found(self, client):
        """Test 404 error for non-existent endpoints."""
        response = client.get("/nonexistent")
        assert response.status_code == 404


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
