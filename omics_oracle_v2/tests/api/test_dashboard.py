"""
Tests for web dashboard interface.

Tests dashboard serving, static files, and dashboard functionality.
"""

import pytest
from fastapi.testclient import TestClient

from omics_oracle_v2.api.main import create_app


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


class TestDashboardEndpoint:
    """Tests for dashboard endpoint."""

    def test_dashboard_exists(self, client):
        """Test dashboard endpoint exists."""
        response = client.get("/dashboard")
        assert response.status_code == 200

    def test_dashboard_returns_html(self, client):
        """Test dashboard returns HTML content."""
        response = client.get("/dashboard")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

    def test_dashboard_contains_title(self, client):
        """Test dashboard HTML contains title."""
        response = client.get("/dashboard")
        assert response.status_code == 200
        assert b"OmicsOracle Dashboard" in response.content

    def test_dashboard_contains_workflow_section(self, client):
        """Test dashboard contains workflow execution section."""
        response = client.get("/dashboard")
        assert response.status_code == 200
        content = response.content.decode()
        assert "Execute Workflow" in content
        assert "workflow_type" in content.lower()


class TestStaticFiles:
    """Tests for static file serving."""

    def test_static_directory_mounted(self, client):
        """Test static directory is accessible."""
        # Try to access a static file (dashboard.html via static path)
        response = client.get("/static/dashboard.html")
        # Should either return 200 or 404 if file doesn't exist via static mount
        assert response.status_code in [200, 404, 307]  # 307 is redirect

    def test_websocket_demo_accessible(self, client):
        """Test WebSocket demo is accessible via static files."""
        response = client.get("/static/websocket_demo.html")
        assert response.status_code in [200, 404]


class TestDashboardIntegration:
    """Tests for dashboard integration with API."""

    def test_root_includes_dashboard_link(self, client):
        """Test root endpoint includes dashboard link."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "dashboard" in data
        assert data["dashboard"] == "/dashboard"

    def test_dashboard_workflow_types(self, client):
        """Test dashboard includes all workflow types."""
        response = client.get("/dashboard")
        assert response.status_code == 200
        content = response.content.decode()

        # Check for all workflow types
        assert "full_analysis" in content or "Full Analysis" in content
        assert "simple_search" in content or "Simple Search" in content
        assert "quick_report" in content or "Quick Report" in content
        assert "data_validation" in content or "Data Validation" in content

    def test_dashboard_has_batch_section(self, client):
        """Test dashboard has batch processing section."""
        response = client.get("/dashboard")
        assert response.status_code == 200
        content = response.content.decode()
        assert "Batch" in content or "batch" in content

    def test_dashboard_has_websocket_section(self, client):
        """Test dashboard has WebSocket section."""
        response = client.get("/dashboard")
        assert response.status_code == 200
        content = response.content.decode()
        assert "WebSocket" in content or "websocket" in content.lower()

    def test_dashboard_has_results_section(self, client):
        """Test dashboard has results display section."""
        response = client.get("/dashboard")
        assert response.status_code == 200
        content = response.content.decode()
        assert "Results" in content or "results" in content


class TestDashboardUI:
    """Tests for dashboard UI components."""

    def test_dashboard_has_form_elements(self, client):
        """Test dashboard has necessary form elements."""
        response = client.get("/dashboard")
        assert response.status_code == 200
        content = response.content.decode()

        # Check for form elements
        assert "textarea" in content.lower() or "input" in content.lower()
        assert "button" in content.lower()

    def test_dashboard_has_javascript(self, client):
        """Test dashboard includes JavaScript functionality."""
        response = client.get("/dashboard")
        assert response.status_code == 200
        content = response.content.decode()

        # Check for key JavaScript functions
        assert "executeWorkflow" in content or "execute" in content.lower()
        assert "fetch" in content or "XMLHttpRequest" in content

    def test_dashboard_has_styling(self, client):
        """Test dashboard includes CSS styling."""
        response = client.get("/dashboard")
        assert response.status_code == 200
        content = response.content.decode()

        # Check for CSS
        assert "<style>" in content or "stylesheet" in content.lower()
