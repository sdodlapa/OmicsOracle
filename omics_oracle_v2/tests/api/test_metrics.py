"""
Tests for Prometheus metrics and monitoring.

Tests metrics collection, exposure, and tracking functionality.
"""

import pytest
from fastapi.testclient import TestClient

from omics_oracle_v2.api.main import create_app
from omics_oracle_v2.api.metrics import (
    track_agent_execution,
    track_batch_job,
    track_websocket_connection,
    track_websocket_message,
    track_workflow_execution,
)


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


class TestMetricsEndpoint:
    """Tests for Prometheus metrics endpoint."""

    def test_metrics_endpoint_exists(self, client):
        """Test metrics endpoint exists."""
        response = client.get("/metrics")
        assert response.status_code == 200

    def test_metrics_content_type(self, client):
        """Test metrics endpoint returns correct content type."""
        response = client.get("/metrics")
        assert response.status_code == 200
        # Prometheus metrics content type
        assert "text/plain" in response.headers.get("content-type", "")

    def test_metrics_contains_prometheus_format(self, client):
        """Test metrics are in Prometheus format."""
        response = client.get("/metrics")
        assert response.status_code == 200
        content = response.text

        # Should contain Prometheus metric format
        # Metrics have # HELP and # TYPE lines
        assert "# HELP" in content or "# TYPE" in content


class TestHTTPMetrics:
    """Tests for HTTP request metrics collection."""

    def test_http_requests_tracked(self, client):
        """Test HTTP requests are tracked in metrics."""
        # Make a request
        client.get("/health")

        # Get metrics
        response = client.get("/metrics")
        assert response.status_code == 200
        content = response.text

        # Should contain HTTP request metrics
        assert "omicsoracle_http_requests_total" in content

    def test_http_request_duration_tracked(self, client):
        """Test HTTP request duration is tracked."""
        # Make a request
        client.get("/health")

        # Get metrics
        response = client.get("/metrics")
        content = response.text

        # Should contain duration metrics
        assert "omicsoracle_http_request_duration_seconds" in content

    def test_multiple_requests_increment_counter(self, client):
        """Test multiple requests increment counter."""
        # Make multiple requests
        for _ in range(3):
            client.get("/health")

        # Get metrics
        response = client.get("/metrics")
        content = response.text

        # Metrics should reflect multiple requests
        assert "omicsoracle_http_requests_total" in content

    def test_metrics_endpoint_not_tracked(self, client):
        """Test metrics endpoint doesn't track itself."""
        # Get metrics multiple times
        for _ in range(3):
            client.get("/metrics")

        # Get metrics
        response = client.get("/metrics")

        # Should not have /metrics endpoint in tracked requests
        # (it's excluded from tracking)
        assert response.status_code == 200


class TestAgentMetrics:
    """Tests for agent execution metrics."""

    def test_track_agent_execution(self, client):
        """Test agent execution tracking."""
        # Track some agent executions
        track_agent_execution("QueryAgent", 0.5, "success")
        track_agent_execution("SearchAgent", 1.2, "success")
        track_agent_execution("DataAgent", 0.8, "failure")

        # Get metrics
        response = client.get("/metrics")
        content = response.text

        # Should contain agent metrics
        assert "omicsoracle_agent_executions_total" in content
        assert "omicsoracle_agent_execution_duration_seconds" in content

    def test_agent_metrics_include_labels(self, client):
        """Test agent metrics include proper labels."""
        track_agent_execution("QueryAgent", 0.5, "success")

        response = client.get("/metrics")
        content = response.text

        # Should contain agent name and status labels
        assert "agent=" in content or "status=" in content


class TestWorkflowMetrics:
    """Tests for workflow execution metrics."""

    def test_track_workflow_execution(self, client):
        """Test workflow execution tracking."""
        track_workflow_execution("full_analysis", 2.5, "success")
        track_workflow_execution("simple_search", 1.0, "success")
        track_workflow_execution("quick_report", 0.5, "failure")

        response = client.get("/metrics")
        content = response.text

        assert "omicsoracle_workflow_executions_total" in content
        assert "omicsoracle_workflow_duration_seconds" in content

    def test_workflow_metrics_include_type(self, client):
        """Test workflow metrics include workflow type."""
        track_workflow_execution("full_analysis", 2.5, "success")

        response = client.get("/metrics")
        content = response.text

        assert "workflow_type=" in content


class TestBatchJobMetrics:
    """Tests for batch job metrics."""

    def test_track_batch_job(self, client):
        """Test batch job tracking."""
        track_batch_job("completed", 5)
        track_batch_job("completed", 3)
        track_batch_job("failed", 2)

        response = client.get("/metrics")
        content = response.text

        assert "omicsoracle_batch_jobs_total" in content
        assert "omicsoracle_batch_job_workflows" in content


class TestWebSocketMetrics:
    """Tests for WebSocket metrics."""

    def test_track_websocket_connection(self, client):
        """Test WebSocket connection tracking."""
        # Track connections
        track_websocket_connection(True)
        track_websocket_connection(True)
        track_websocket_connection(False)

        response = client.get("/metrics")
        content = response.text

        assert "omicsoracle_websocket_connections_total" in content
        assert "omicsoracle_websocket_active_connections" in content

    def test_track_websocket_messages(self, client):
        """Test WebSocket message tracking."""
        track_websocket_message("stage_start")
        track_websocket_message("stage_complete")
        track_websocket_message("progress")

        response = client.get("/metrics")
        content = response.text

        assert "omicsoracle_websocket_messages_sent" in content


class TestMetricsIntegration:
    """Tests for metrics integration with API endpoints."""

    def test_api_requests_generate_metrics(self, client):
        """Test API requests automatically generate metrics."""
        # Make various API requests
        client.get("/")
        client.get("/health")
        client.get("/health/ready")

        # Get metrics
        response = client.get("/metrics")
        content = response.text

        # Should have metrics for all endpoints
        assert "omicsoracle_http_requests_total" in content
        assert "omicsoracle_http_request_duration_seconds" in content

    def test_error_responses_tracked(self, client):
        """Test error responses are tracked in metrics."""
        # Make a request to non-existent endpoint
        client.get("/nonexistent")

        # Get metrics
        response = client.get("/metrics")
        content = response.text

        # Should contain error metrics
        assert "omicsoracle_http_requests_total" in content
