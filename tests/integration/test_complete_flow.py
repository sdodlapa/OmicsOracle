"""
Integration tests for complete user flows.

Tests end-to-end scenarios from registration to results.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.asyncio
class TestCompleteUserJourney:
    """Test complete user journey from registration to results."""

    async def test_new_user_complete_flow(self, client: AsyncClient):
        """Test complete flow: register -> login -> execute -> results."""
        # 1. Register new user
        register_response = await client.post(
            "/api/v2/auth/register",
            json={
                "email": "journey@example.com",
                "password": "Journey123!",
                "username": "journeyuser",
            },
        )
        assert register_response.status_code == 201
        user_data = register_response.json()
        assert user_data["email"] == "journey@example.com"

        # 2. Login with new user
        login_response = await client.post(
            "/api/v2/auth/login",
            json={
                "email": "journey@example.com",
                "password": "Journey123!",
            },
        )
        assert login_response.status_code == 200
        login_data = login_response.json()
        token = login_data["access_token"]
        client.headers["Authorization"] = f"Bearer {token}"

        # 3. Get current user info
        me_response = await client.get("/api/v2/users/me")
        assert me_response.status_code == 200
        me_data = me_response.json()
        assert me_data["email"] == "journey@example.com"

        # 4. List available agents
        agents_response = await client.get("/api/v1/agents")
        assert agents_response.status_code == 200
        agents = agents_response.json()
        assert len(agents) == 4

        # 5. List available workflows
        workflows_response = await client.get("/api/v1/workflows")
        assert workflows_response.status_code == 200
        workflows = workflows_response.json()
        assert len(workflows) == 4

        # 6. Execute a simple workflow
        workflow_response = await client.post(
            "/api/v1/workflows/execute",
            json={
                "query": "test query",
                "workflow_type": "simple_search",
                "max_results": 2,
            },
        )
        assert workflow_response.status_code == 200
        workflow_data = workflow_response.json()
        assert workflow_data["success"] is True

        # 7. Check quota usage
        quota_response = await client.get("/api/v2/quotas/usage")
        assert quota_response.status_code == 200
        quota_data = quota_response.json()
        assert quota_data["requests_used"] >= 1


@pytest.mark.integration
@pytest.mark.asyncio
class TestAuthenticationFlow:
    """Test authentication flow integration."""

    async def test_registration_login_access_flow(self, client: AsyncClient):
        """Test full authentication flow."""
        # Register
        register_response = await client.post(
            "/api/v2/auth/register",
            json={
                "email": "authflow@example.com",
                "password": "AuthFlow123!",
                "username": "authflowuser",
            },
        )
        assert register_response.status_code == 201

        # Login
        login_response = await client.post(
            "/api/v2/auth/login",
            json={
                "email": "authflow@example.com",
                "password": "AuthFlow123!",
            },
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        # Access protected resource
        client.headers["Authorization"] = f"Bearer {token}"
        me_response = await client.get("/api/v2/users/me")
        assert me_response.status_code == 200


@pytest.mark.integration
@pytest.mark.asyncio
class TestWorkflowIntegration:
    """Test workflow integration scenarios."""

    async def test_agent_to_workflow_flow(self, authenticated_client):
        """Test using individual agents before running workflow."""
        client, _ = authenticated_client

        # 1. Query agent
        query_response = await client.post(
            "/api/v1/agents/query",
            json={
                "query": "cancer research",
            },
        )
        assert query_response.status_code == 200

        # 2. Search agent
        search_response = await client.post(
            "/api/v1/agents/search",
            json={
                "query": "cancer",
                "max_results": 3,
            },
        )
        assert search_response.status_code == 200

        # 3. Full workflow (combines agents)
        workflow_response = await client.post(
            "/api/v1/workflows/execute",
            json={
                "query": "cancer research",
                "workflow_type": "full_analysis",
                "max_results": 3,
            },
        )
        assert workflow_response.status_code == 200

    async def test_batch_job_workflow_integration(self, authenticated_client):
        """Test batch job creation and monitoring."""
        client, _ = authenticated_client

        # Create batch job
        create_response = await client.post(
            "/api/v1/batch/jobs",
            json={
                "queries": ["query1", "query2"],
                "workflow_type": "simple_search",
            },
        )
        assert create_response.status_code == 201
        job_id = create_response.json()["job_id"]

        # Check job status
        status_response = await client.get(f"/api/v1/batch/jobs/{job_id}")
        assert status_response.status_code == 200

        # List all jobs
        list_response = await client.get("/api/v1/batch/jobs")
        assert list_response.status_code == 200
        jobs = list_response.json()
        assert any(job["job_id"] == job_id for job in jobs)


@pytest.mark.integration
@pytest.mark.asyncio
class TestQuotaEnforcement:
    """Test quota enforcement across different operations."""

    async def test_quota_tracking_across_operations(self, authenticated_client):
        """Test that quota is tracked across multiple operations."""
        client, _ = authenticated_client

        # Get initial quota
        quota_response = await client.get("/api/v2/quotas/usage")
        assert quota_response.status_code == 200
        initial_quota = quota_response.json()
        initial_requests = initial_quota["requests_used"]

        # Perform some operations
        await client.post("/api/v1/agents/query", json={"query": "test"})
        await client.post("/api/v1/agents/search", json={"query": "test", "max_results": 2})

        # Check quota increased
        quota_response = await client.get("/api/v2/quotas/usage")
        assert quota_response.status_code == 200
        final_quota = quota_response.json()
        final_requests = final_quota["requests_used"]

        assert final_requests > initial_requests


@pytest.mark.integration
@pytest.mark.asyncio
class TestErrorHandling:
    """Test error handling across the system."""

    async def test_cascading_error_handling(self, authenticated_client):
        """Test that errors are properly handled throughout the system."""
        client, _ = authenticated_client

        # Invalid agent request
        response = await client.post(
            "/api/v1/agents/query",
            json={
                "query": "",  # Empty query should fail
            },
        )
        assert response.status_code == 422
        assert "detail" in response.json()

        # Invalid workflow request
        response = await client.post(
            "/api/v1/workflows/execute",
            json={
                "query": "test",
                "workflow_type": "nonexistent",
            },
        )
        assert response.status_code == 422

        # Invalid batch request
        response = await client.post(
            "/api/v1/batch/jobs",
            json={
                "queries": [],  # Empty queries should fail
                "workflow_type": "simple_search",
            },
        )
        assert response.status_code == 422
