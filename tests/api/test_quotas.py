"""
Tests for quota management API endpoints.
"""
# flake8: noqa
# Note: Some tests use fixtures (admin_user, regular_user, app, get_auth_headers,
# create_test_user) that are marked as skip pending implementation.

import pytest  # noqa: F401
from httpx import AsyncClient

from omics_oracle_v2.api.main import create_app
from omics_oracle_v2.cache import memory_clear
from omics_oracle_v2.core import Settings

# Note: create_test_user and get_auth_headers fixtures are imported from conftest.py
# They are automatically discovered by pytest and don't need explicit imports


@pytest.fixture
async def app():
    """Create test FastAPI application."""
    settings = Settings()
    return create_app(settings=settings)


@pytest.fixture
async def regular_user(db_session, create_test_user):
    """Create a regular test user."""
    return await create_test_user(db_session, email="user@test.com", password="testpass", tier="free")


@pytest.fixture
async def admin_user(db_session, create_test_user):
    """Create an admin test user."""
    return await create_test_user(
        db_session,
        email="admin@test.com",
        password="adminpass",
        tier="pro",
        is_admin=True,
    )


@pytest.fixture(autouse=True)
async def clear_quota_cache():
    """Clear quota cache before each test."""
    await memory_clear()
    yield
    await memory_clear()


class TestUserQuotaEndpoints:
    """Tests for user quota endpoints."""

    @pytest.mark.asyncio
    async def test_get_my_quota_success(self, app, regular_user, get_auth_headers):
        """Test getting current user's quota."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            headers = await get_auth_headers(regular_user)

            response = await client.get("/api/v2/quotas/me", headers=headers)

            assert response.status_code == 200
            data = response.json()

            # Check response structure
            assert "user_id" in data
            assert "tier" in data
            assert "hourly_limit" in data
            assert "hourly_used" in data
            assert "hourly_remaining" in data
            assert "hourly_reset_at" in data
            assert "daily_limit" in data
            assert "daily_used" in data
            assert "daily_remaining" in data
            assert "daily_reset_at" in data
            assert "quota_exceeded" in data

            # Check values
            assert data["user_id"] == regular_user.id
            assert data["tier"] == "free"
            assert data["hourly_limit"] == 100  # Free tier hourly limit
            assert data["daily_limit"] == 1000  # Free tier daily limit
            assert not data["quota_exceeded"]

    @pytest.mark.asyncio
    async def test_get_my_quota_unauthorized(self, app):
        """Test getting quota without authentication."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v2/quotas/me")

            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_my_quota_after_usage(self, app, regular_user):
        """Test quota reflects actual usage."""
        from omics_oracle_v2.auth.quota import check_rate_limit

        # Use some quota
        for _ in range(5):
            await check_rate_limit(user_id=regular_user.id, ip_address=None, tier="free", window="hour")

        async with AsyncClient(app=app, base_url="http://test") as client:
            headers = await get_auth_headers(regular_user)

            response = await client.get("/api/v2/quotas/me", headers=headers)

            assert response.status_code == 200
            data = response.json()

            # Should show 5 requests used (+1 for this check)
            assert data["hourly_used"] >= 5
            assert data["hourly_remaining"] <= data["hourly_limit"] - 5

    @pytest.mark.asyncio
    async def test_get_my_usage_history_success(self, app, regular_user):
        """Test getting usage history."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            headers = await get_auth_headers(regular_user)

            response = await client.get("/api/v2/quotas/me/history", headers=headers)

            assert response.status_code == 200
            data = response.json()

            # Check response structure
            assert "user_id" in data
            assert "period_start" in data
            assert "period_end" in data
            assert "total_requests" in data
            assert "average_daily_requests" in data
            assert "peak_daily_requests" in data
            assert "current_tier" in data
            assert "history" in data

            assert data["user_id"] == regular_user.id
            assert data["current_tier"] == "free"

    @pytest.mark.asyncio
    async def test_get_my_usage_history_custom_days(self, app, regular_user):
        """Test getting usage history with custom days parameter."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            headers = await get_auth_headers(regular_user)

            response = await client.get("/api/v2/quotas/me/history?days=7", headers=headers)

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_my_usage_history_invalid_days(self, app, regular_user):
        """Test validation of days parameter."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            headers = await get_auth_headers(regular_user)

            # Too many days
            response = await client.get("/api/v2/quotas/me/history?days=100", headers=headers)
            assert response.status_code == 400

            # Too few days
            response = await client.get("/api/v2/quotas/me/history?days=0", headers=headers)
            assert response.status_code == 400


class TestAdminQuotaEndpoints:
    """Tests for admin quota management endpoints."""

    @pytest.mark.asyncio
    async def test_admin_get_user_quota(self, app, admin_user, regular_user):
        """Test admin getting any user's quota."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            headers = await get_auth_headers(admin_user)

            response = await client.get(f"/api/v2/quotas/{regular_user.id}", headers=headers)

            assert response.status_code == 200
            data = response.json()

            assert data["user_id"] == regular_user.id
            assert data["tier"] == "free"

    @pytest.mark.asyncio
    async def test_admin_get_user_quota_not_found(self, app, admin_user):
        """Test admin getting quota for non-existent user."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            headers = await get_auth_headers(admin_user)

            response = await client.get("/api/v2/quotas/99999", headers=headers)

            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_regular_user_cannot_get_other_quota(self, app, regular_user):
        """Test that regular users cannot get other users' quotas."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            headers = await get_auth_headers(regular_user)

            response = await client.get("/api/v2/quotas/999", headers=headers)

            assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_update_user_tier(self, app, admin_user, regular_user, db_session):
        """Test admin updating user tier."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            headers = await get_auth_headers(admin_user)

            # Update to pro tier
            response = await client.put(
                f"/api/v2/quotas/{regular_user.id}/tier",
                headers=headers,
                json={"tier": "pro"},
            )

            assert response.status_code == 200
            data = response.json()

            assert data["tier"] == "pro"

            # Verify in database
            from omics_oracle_v2.auth import crud

            updated_user = await crud.get_user_by_id(db_session, regular_user.id)
            assert updated_user.tier == "pro"

    @pytest.mark.asyncio
    async def test_admin_update_user_tier_invalid(self, app, admin_user, regular_user):
        """Test admin updating user tier with invalid tier."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            headers = await get_auth_headers(admin_user)

            response = await client.put(
                f"/api/v2/quotas/{regular_user.id}/tier",
                headers=headers,
                json={"tier": "invalid"},
            )

            assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_regular_user_cannot_update_tier(self, app, regular_user):
        """Test that regular users cannot update tiers."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            headers = await get_auth_headers(regular_user)

            response = await client.put(
                f"/api/v2/quotas/{regular_user.id}/tier",
                headers=headers,
                json={"tier": "pro"},
            )

            assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_reset_user_quota(self, app, admin_user, regular_user):
        """Test admin resetting user quota."""
        from omics_oracle_v2.auth.quota import check_rate_limit

        # Use some quota
        for _ in range(10):
            await check_rate_limit(user_id=regular_user.id, ip_address=None, tier="free", window="hour")

        async with AsyncClient(app=app, base_url="http://test") as client:
            headers = await get_auth_headers(admin_user)

            # Reset quota
            response = await client.post(
                f"/api/v2/quotas/{regular_user.id}/reset",
                headers=headers,
                json={"window": "hour"},
            )

            assert response.status_code == 204

            # Verify quota was reset
            result = await check_rate_limit(
                user_id=regular_user.id, ip_address=None, tier="free", window="hour"
            )

            # Should be back to full quota (minus 1 for this check)
            assert result.remaining == result.limit - 1

    @pytest.mark.asyncio
    async def test_admin_reset_all_quotas(self, app, admin_user, regular_user):
        """Test admin resetting all quota windows."""
        from omics_oracle_v2.auth.quota import check_rate_limit

        # Use hourly and daily quota
        for _ in range(5):
            await check_rate_limit(user_id=regular_user.id, ip_address=None, tier="free", window="hour")
            await check_rate_limit(user_id=regular_user.id, ip_address=None, tier="free", window="day")

        async with AsyncClient(app=app, base_url="http://test") as client:
            headers = await get_auth_headers(admin_user)

            # Reset all
            response = await client.post(
                f"/api/v2/quotas/{regular_user.id}/reset",
                headers=headers,
                json={"window": "all"},
            )

            assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_regular_user_cannot_reset_quota(self, app, regular_user):
        """Test that regular users cannot reset quotas."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            headers = await get_auth_headers(regular_user)

            response = await client.post(
                f"/api/v2/quotas/{regular_user.id}/reset",
                headers=headers,
                json={"window": "hour"},
            )

            assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_get_quota_stats(self, app, admin_user):
        """Test admin getting system-wide quota statistics."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            headers = await get_auth_headers(admin_user)

            response = await client.get("/api/v2/quotas/stats/overview", headers=headers)

            assert response.status_code == 200
            data = response.json()

            # Check response has expected fields
            assert "total_users" in data
            assert "active_users_hour" in data
            assert "active_users_day" in data
            assert "requests_hour" in data
            assert "requests_day" in data
            assert "tier_distribution" in data
            assert "quota_exceeded_users" in data

    @pytest.mark.asyncio
    async def test_regular_user_cannot_get_stats(self, app, regular_user):
        """Test that regular users cannot access quota stats."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            headers = await get_auth_headers(regular_user)

            response = await client.get("/api/v2/quotas/stats/overview", headers=headers)

            assert response.status_code == 403


class TestQuotaTierBehavior:
    """Tests for tier-specific quota behavior."""

    @pytest.mark.asyncio
    async def test_free_tier_limits(self, app, db_session):
        """Test free tier quota limits."""
        user = await create_test_user(db_session, email="free@test.com", password="test", tier="free")

        async with AsyncClient(app=app, base_url="http://test") as client:
            headers = await get_auth_headers(user)

            response = await client.get("/api/v2/quotas/me", headers=headers)

            data = response.json()
            assert data["hourly_limit"] == 100
            assert data["daily_limit"] == 1000

    @pytest.mark.asyncio
    async def test_pro_tier_limits(self, app, db_session):
        """Test pro tier quota limits."""
        user = await create_test_user(db_session, email="pro@test.com", password="test", tier="pro")

        async with AsyncClient(app=app, base_url="http://test") as client:
            headers = await get_auth_headers(user)

            response = await client.get("/api/v2/quotas/me", headers=headers)

            data = response.json()
            assert data["hourly_limit"] == 1000
            assert data["daily_limit"] == 20000

    @pytest.mark.asyncio
    async def test_enterprise_tier_limits(self, app, db_session):
        """Test enterprise tier quota limits."""
        user = await create_test_user(
            db_session, email="enterprise@test.com", password="test", tier="enterprise"
        )

        async with AsyncClient(app=app, base_url="http://test") as client:
            headers = await get_auth_headers(user)

            response = await client.get("/api/v2/quotas/me", headers=headers)

            data = response.json()
            assert data["hourly_limit"] == 10000
            assert data["daily_limit"] == 200000
