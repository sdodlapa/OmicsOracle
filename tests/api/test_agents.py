"""
Tests for agent endpoints.

Based on successful manual tests - tests agent discovery and execution.
Covers: Query Agent, Search Agent, Data Agent, Report Agent
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestAgentDiscovery:
    """Test agent discovery endpoints."""

    async def test_list_agents(self, authenticated_client):
        """Test listing all available agents."""
        client, _ = authenticated_client
        response = await client.get("/api/v1/agents/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 4  # Query, Search, Data, Report

        # Check structure of first agent
        agent = data[0]
        assert "id" in agent
        assert "name" in agent
        assert "description" in agent
        assert "capabilities" in agent
        assert "endpoint" in agent

    async def test_list_agents_unauthenticated(self, client: AsyncClient):
        """Test listing agents without authentication fails."""
        response = await client.get("/api/v1/agents/")
        assert response.status_code == 401

    async def test_agent_capabilities_structure(self, authenticated_client):
        """Test that agent capabilities are properly structured."""
        client, _ = authenticated_client
        response = await client.get("/api/v1/agents/")
        assert response.status_code == 200
        agents = response.json()

        for agent in agents:
            assert isinstance(agent["capabilities"], list)
            assert len(agent["capabilities"]) > 0


@pytest.mark.asyncio
class TestQueryAgent:
    """Test Query Agent execution."""

    async def test_execute_query_agent(self, authenticated_client):
        """Test executing Query Agent with valid query."""
        client, _ = authenticated_client
        response = await client.post(
            "/api/v1/agents/query",
            json={
                "query": "breast cancer BRCA1 mutation",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "entities" in data
        assert "execution_time_ms" in data

    async def test_query_agent_empty_query(self, authenticated_client):
        """Test Query Agent with empty query fails."""
        client, _ = authenticated_client
        response = await client.post(
            "/api/v1/agents/query",
            json={
                "query": "",
            },
        )
        assert response.status_code == 422

    async def test_query_agent_complex_biomedical_query(self, authenticated_client):
        """Test Query Agent with complex biomedical query."""
        client, _ = authenticated_client
        response = await client.post(
            "/api/v1/agents/query",
            json={
                "query": "lung cancer adenocarcinoma EGFR mutation treatment response",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "entities" in data
        assert "intent" in data

    async def test_query_agent_without_auth(self, client: AsyncClient):
        """Test Query Agent without authentication fails."""
        response = await client.post(
            "/api/v1/agents/query",
            json={
                "query": "test query",
            },
        )
        assert response.status_code == 401


@pytest.mark.asyncio
class TestSearchAgent:
    """Test Search Agent execution."""

    async def test_execute_search_agent(self, authenticated_client):
        """Test executing Search Agent."""
        client, _ = authenticated_client
        response = await client.post(
            "/api/v1/agents/search",
            json={
                "query": "cancer",
                "max_results": 10,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "datasets" in data["data"]

    async def test_search_agent_with_filters(self, authenticated_client):
        """Test Search Agent with organism filters."""
        client, _ = authenticated_client
        response = await client.post(
            "/api/v1/agents/search",
            json={
                "query": "cancer",
                "max_results": 5,
                "organisms": ["Homo sapiens"],
                "min_samples": 10,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    async def test_search_agent_max_results_limit(self, authenticated_client):
        """Test Search Agent respects max_results parameter."""
        client, _ = authenticated_client
        response = await client.post(
            "/api/v1/agents/search",
            json={
                "query": "cancer",
                "max_results": 3,
            },
        )
        assert response.status_code == 200
        data = response.json()
        # Results should not exceed max_results
        if "datasets" in data["data"]:
            assert len(data["data"]["datasets"]) <= 3


@pytest.mark.asyncio
class TestDataAgent:
    """Test Data Agent execution."""

    async def test_execute_data_agent(self, authenticated_client):
        """Test executing Data Agent."""
        client, _ = authenticated_client
        response = await client.post(
            "/api/v1/agents/data",
            json={
                "dataset_ids": ["GSE12345"],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    async def test_data_agent_multiple_datasets(self, authenticated_client):
        """Test Data Agent with multiple dataset IDs."""
        client, _ = authenticated_client
        response = await client.post(
            "/api/v1/agents/data",
            json={
                "dataset_ids": ["GSE12345", "GSE67890"],
            },
        )
        assert response.status_code == 200


@pytest.mark.asyncio
class TestReportAgent:
    """Test Report Agent execution."""

    async def test_execute_report_agent(self, authenticated_client):
        """Test executing Report Agent."""
        client, _ = authenticated_client
        response = await client.post(
            "/api/v1/agents/report",
            json={
                "data": {"datasets": [], "analysis": {}},
                "report_type": "summary",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "report" in data["data"]

    async def test_report_agent_different_types(self, authenticated_client):
        """Test Report Agent with different report types."""
        client, _ = authenticated_client

        for report_type in ["summary", "detailed", "comparison"]:
            response = await client.post(
                "/api/v1/agents/report",
                json={
                    "data": {"datasets": [], "analysis": {}},
                    "report_type": report_type,
                },
            )
            assert response.status_code == 200
