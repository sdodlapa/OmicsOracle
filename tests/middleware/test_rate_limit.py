"""
Tests for rate limiting middleware.
"""

from unittest.mock import patch

import pytest
from fastapi import FastAPI

from omics_oracle_v2.auth.quota import check_rate_limit
from omics_oracle_v2.cache import memory_clear
from omics_oracle_v2.core import Settings
from omics_oracle_v2.middleware import RateLimitMiddleware


@pytest.fixture
def app():
    """Create test FastAPI application."""
    app = FastAPI()

    @app.get("/test")
    async def test_endpoint():
        return {"status": "ok"}

    @app.get("/batch/test")
    async def batch_endpoint():
        return {"status": "ok"}

    @app.get("/health")
    async def health_endpoint():
        return {"status": "healthy"}

    return app


@pytest.fixture
def settings():
    """Create test settings."""
    return Settings()


@pytest.fixture(autouse=True)
async def clear_cache():
    """Clear memory cache before each test."""
    await memory_clear()
    yield
    await memory_clear()


class TestRateLimitMiddleware:
    """Tests for RateLimitMiddleware."""

    @pytest.mark.asyncio
    async def test_middleware_disabled(self, app, settings):
        """Test middleware does nothing when disabled."""
        settings.rate_limit.enabled = False
        app.add_middleware(RateLimitMiddleware, settings=settings)

        # Make multiple requests - should all succeed
        from httpx import AsyncClient

        async with AsyncClient(app=app, base_url="http://test") as client:
            for _ in range(20):
                response = await client.get("/test")
                assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_rate_limit_headers_added(self, app, settings):
        """Test that rate limit headers are added to responses."""
        settings.rate_limit.enabled = True
        app.add_middleware(RateLimitMiddleware, settings=settings)

        from httpx import AsyncClient

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/test")

            # Check headers are present
            assert "X-RateLimit-Limit" in response.headers
            assert "X-RateLimit-Remaining" in response.headers
            assert "X-RateLimit-Reset" in response.headers

            # Verify values make sense
            limit = int(response.headers["X-RateLimit-Limit"])
            remaining = int(response.headers["X-RateLimit-Remaining"])
            reset_at = int(response.headers["X-RateLimit-Reset"])

            assert limit > 0
            assert remaining >= 0
            assert remaining <= limit
            assert reset_at > 0

    @pytest.mark.asyncio
    async def test_rate_limit_enforced(self, app, settings):
        """Test that rate limits are enforced."""
        settings.rate_limit.enabled = True
        # Set very low limit for anonymous users
        settings.rate_limit.anonymous_limit_hour = 3
        app.add_middleware(RateLimitMiddleware, settings=settings)

        from httpx import AsyncClient

        async with AsyncClient(app=app, base_url="http://test") as client:
            # First 3 requests should succeed
            for i in range(3):
                response = await client.get("/test")
                assert response.status_code == 200, f"Request {i+1} failed"

            # 4th request should be rate limited
            response = await client.get("/test")
            assert response.status_code == 429
            assert "Retry-After" in response.headers

    @pytest.mark.asyncio
    async def test_free_endpoints_not_counted(self, app, settings):
        """Test that free endpoints (cost=0) are not counted."""
        settings.rate_limit.enabled = True
        settings.rate_limit.anonymous_limit_hour = 3
        app.add_middleware(RateLimitMiddleware, settings=settings)

        from httpx import AsyncClient

        async with AsyncClient(app=app, base_url="http://test") as client:
            # Make many requests to health endpoint (cost=0)
            for _ in range(10):
                response = await client.get("/health")
                assert response.status_code == 200

            # Regular endpoint should still work (quota not affected)
            response = await client.get("/test")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_endpoint_cost_multiplier(self, app, settings):
        """Test that endpoint costs are applied correctly."""
        settings.rate_limit.enabled = True
        settings.rate_limit.anonymous_limit_hour = 10
        app.add_middleware(RateLimitMiddleware, settings=settings)

        from httpx import AsyncClient

        async with AsyncClient(app=app, base_url="http://test") as client:
            # Make 2 batch requests (cost=5 each = 10 total)
            response1 = await client.get("/batch/test")
            assert response1.status_code == 200

            response2 = await client.get("/batch/test")
            assert response2.status_code == 200

            # Quota should be exhausted (10 used)
            response3 = await client.get("/test")
            assert response3.status_code == 429

    @pytest.mark.asyncio
    async def test_429_response_format(self, app, settings):
        """Test that 429 responses have correct format."""
        settings.rate_limit.enabled = True
        settings.rate_limit.anonymous_limit_hour = 1
        app.add_middleware(RateLimitMiddleware, settings=settings)

        from httpx import AsyncClient

        async with AsyncClient(app=app, base_url="http://test") as client:
            # Use up quota
            await client.get("/test")

            # Get 429 response
            response = await client.get("/test")
            assert response.status_code == 429

            # Check response body
            data = response.json()
            assert "error" in data
            assert data["error"] == "rate_limit_exceeded"
            assert "message" in data

            # Check headers
            assert "Retry-After" in response.headers
            retry_after = int(response.headers["Retry-After"])
            assert retry_after > 0


class TestQuotaLogic:
    """Tests for quota checking logic."""

    @pytest.mark.asyncio
    async def test_check_rate_limit_basic(self):
        """Test basic rate limit checking."""
        await memory_clear()

        # First check should succeed
        result = await check_rate_limit(user_id=123, ip_address="192.168.1.1", tier="free", window="hour")

        assert not result.quota_exceeded
        assert result.remaining > 0
        assert result.limit > 0
        assert result.reset_at > 0

    @pytest.mark.asyncio
    async def test_quota_decrements(self):
        """Test that quota decrements with each request."""
        await memory_clear()

        # First request
        result1 = await check_rate_limit(user_id=123, ip_address="192.168.1.1", tier="free", window="hour")

        # Second request
        result2 = await check_rate_limit(user_id=123, ip_address="192.168.1.1", tier="free", window="hour")

        # Remaining should decrease
        assert result2.remaining < result1.remaining
        assert result2.remaining == result1.remaining - 1

    @pytest.mark.asyncio
    async def test_different_tiers_different_limits(self):
        """Test that different tiers have different limits."""
        await memory_clear()

        # Check free tier
        free_result = await check_rate_limit(user_id=1, ip_address=None, tier="free", window="hour")

        # Check pro tier
        pro_result = await check_rate_limit(user_id=2, ip_address=None, tier="pro", window="hour")

        # Check enterprise tier
        enterprise_result = await check_rate_limit(
            user_id=3, ip_address=None, tier="enterprise", window="hour"
        )

        # Limits should increase with tier
        assert free_result.limit < pro_result.limit
        assert pro_result.limit < enterprise_result.limit

    @pytest.mark.asyncio
    async def test_different_windows(self):
        """Test that hourly and daily windows are tracked separately."""
        await memory_clear()

        # Check hourly
        hour_result = await check_rate_limit(user_id=123, ip_address=None, tier="free", window="hour")

        # Check daily
        day_result = await check_rate_limit(user_id=123, ip_address=None, tier="free", window="day")

        # Daily limit should be higher
        assert day_result.limit > hour_result.limit

    @pytest.mark.asyncio
    async def test_quota_exceeded(self):
        """Test quota exceeded detection."""
        await memory_clear()

        # Make requests until quota exhausted
        user_id = 999
        tier = "free"

        result = None
        for i in range(150):  # Free tier is 100/hour
            result = await check_rate_limit(user_id=user_id, ip_address=None, tier=tier, window="hour")
            if result.quota_exceeded:
                break

        # Should have hit quota
        assert result is not None
        assert result.quota_exceeded
        assert result.remaining == 0
        assert result.retry_after > 0

    @pytest.mark.asyncio
    async def test_concurrent_requests_different_users(self):
        """Test that different users have independent quotas."""
        await memory_clear()

        # Make requests for user 1
        for _ in range(10):
            await check_rate_limit(user_id=1, ip_address=None, tier="free", window="hour")

        # Check user 2's quota is unaffected
        result = await check_rate_limit(user_id=2, ip_address=None, tier="free", window="hour")

        # User 2 should have full quota
        assert result.remaining == result.limit - 1  # -1 for this check


@pytest.mark.asyncio
async def test_memory_cache_fallback():
    """Test that system falls back to memory cache when Redis unavailable."""
    await memory_clear()

    # Mock Redis to fail
    with patch("omics_oracle_v2.auth.quota.redis_incr", return_value=None):
        # Should fall back to memory cache
        result = await check_rate_limit(user_id=123, ip_address=None, tier="free", window="hour")

        # Should still work
        assert not result.quota_exceeded
        assert result.remaining > 0


@pytest.mark.asyncio
async def test_ip_based_rate_limiting():
    """Test IP-based rate limiting for anonymous users."""
    await memory_clear()

    # Check with IP address
    result = await check_rate_limit(user_id=None, ip_address="192.168.1.100", tier="anonymous", window="hour")

    assert not result.quota_exceeded
    assert result.remaining > 0

    # Different IP should have separate quota
    result2 = await check_rate_limit(
        user_id=None, ip_address="192.168.1.101", tier="anonymous", window="hour"
    )

    assert result2.remaining == result.remaining  # Both at max - 1
