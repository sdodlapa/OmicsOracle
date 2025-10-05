"""
Tests for health and metrics endpoints.

Based on successful manual tests from manual_api_test.py
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestHealthEndpoints:
    """Test health and metrics endpoints."""

    async def test_health_check(self, client: AsyncClient):
        """Test health check endpoint returns healthy status."""
        response = await client.get("/health/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data

    async def test_metrics_endpoint(self, client: AsyncClient):
        """Test metrics endpoint returns Prometheus format."""
        response = await client.get("/metrics")
        assert response.status_code == 200
        # Prometheus metrics are text/plain
        assert "text/plain" in response.headers.get("content-type", "")

    async def test_root_endpoint(self, client: AsyncClient):
        """Test root endpoint returns API info."""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data or "name" in data or "status" in data
