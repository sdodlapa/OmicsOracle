"""
Quota definitions and rate limiting logic.

Defines tier-based quotas and provides utilities for checking
and enforcing rate limits.
"""

import logging
import time
from dataclasses import dataclass
from typing import Literal

from omics_oracle_v2.cache import check_redis_health, memory_incr, memory_ttl, redis_incr, redis_ttl
from omics_oracle_v2.core.config import Settings

logger = logging.getLogger(__name__)

# Tier types
TierType = Literal["free", "pro", "enterprise", "anonymous"]


@dataclass
class QuotaLimits:
    """Quota limits for a specific tier."""

    tier: TierType
    requests_per_hour: int
    requests_per_day: int
    concurrent_requests: int


@dataclass
class RateLimitInfo:
    """Rate limit information for a request."""

    limit: int
    remaining: int
    reset_at: int
    retry_after: int | None = None
    quota_exceeded: bool = False


def get_tier_quota(tier: str, settings: Settings | None = None) -> QuotaLimits:
    """
    Get quota limits for a specific tier.

    Args:
        tier: User tier (free, pro, enterprise, anonymous)
        settings: Application settings (optional, will load if not provided)

    Returns:
        QuotaLimits for the tier

    Example:
        >>> quota = get_tier_quota("pro")
        >>> print(quota.requests_per_hour)
        1000
    """
    if settings is None:
        settings = Settings()

    rate_limit = settings.rate_limit

    tier_map = {
        "free": QuotaLimits(
            tier="free",
            requests_per_hour=rate_limit.free_tier_limit_hour,
            requests_per_day=rate_limit.free_tier_limit_day,
            concurrent_requests=rate_limit.free_tier_concurrent,
        ),
        "pro": QuotaLimits(
            tier="pro",
            requests_per_hour=rate_limit.pro_tier_limit_hour,
            requests_per_day=rate_limit.pro_tier_limit_day,
            concurrent_requests=rate_limit.pro_tier_concurrent,
        ),
        "enterprise": QuotaLimits(
            tier="enterprise",
            requests_per_hour=rate_limit.enterprise_tier_limit_hour,
            requests_per_day=rate_limit.enterprise_tier_limit_day,
            concurrent_requests=rate_limit.enterprise_tier_concurrent,
        ),
        "anonymous": QuotaLimits(
            tier="anonymous",
            requests_per_hour=rate_limit.anonymous_limit_hour,
            requests_per_day=rate_limit.anonymous_limit_hour * 24,  # 24 hours worth
            concurrent_requests=1,
        ),
    }

    return tier_map.get(tier.lower(), tier_map["free"])


async def check_rate_limit(
    user_id: int | None,
    ip_address: str | None,
    tier: str = "free",
    window: str = "hour",
) -> RateLimitInfo:
    """
    Check rate limit for a user or IP address.

    Args:
        user_id: User ID (None for anonymous)
        ip_address: Client IP address (used for anonymous users)
        tier: User tier (free, pro, enterprise)
        window: Time window (hour or day)

    Returns:
        RateLimitInfo with current quota status

    Example:
        >>> info = await check_rate_limit(user_id=123, ip_address="1.2.3.4", tier="pro")
        >>> if info.quota_exceeded:
        >>>     return 429  # Too Many Requests
    """
    settings = Settings()
    quota = get_tier_quota(tier if user_id else "anonymous", settings)

    # Determine limit based on window
    limit = quota.requests_per_hour if window == "hour" else quota.requests_per_day
    window_seconds = 3600 if window == "hour" else 86400

    # Build cache key
    if user_id:
        key = f"ratelimit:user:{user_id}:{window}"
    elif ip_address:
        key = f"ratelimit:ip:{ip_address}:{window}"
    else:
        # Shouldn't happen, but handle gracefully
        logger.warning("check_rate_limit called with no user_id or ip_address")
        return RateLimitInfo(
            limit=limit,
            remaining=0,
            reset_at=int(time.time()) + window_seconds,
            quota_exceeded=True,
        )

    # Try Redis first, fall back to memory
    redis_available = await check_redis_health()

    if redis_available:
        # Use Redis
        count = await redis_incr(key, expire=window_seconds)
        ttl = await redis_ttl(key)

        if count is None or ttl is None:
            # Redis error, fall back to memory
            logger.warning("Redis operation failed, using memory fallback")
            count = await memory_incr(key, expire=window_seconds)
            ttl = await memory_ttl(key)
            if ttl is None:
                ttl = window_seconds
    else:
        # Use memory fallback
        count = await memory_incr(key, expire=window_seconds)
        ttl = await memory_ttl(key)
        if ttl is None:
            ttl = window_seconds

    # Calculate reset time
    reset_at = int(time.time()) + max(ttl, 0)

    # Calculate remaining requests
    remaining = max(0, limit - count)

    # Check if quota exceeded
    quota_exceeded = count > limit

    # Calculate retry_after if quota exceeded
    retry_after = ttl if quota_exceeded else None

    return RateLimitInfo(
        limit=limit,
        remaining=remaining,
        reset_at=reset_at,
        retry_after=retry_after,
        quota_exceeded=quota_exceeded,
    )


async def increment_rate_limit(
    user_id: int | None,
    ip_address: str | None,
    tier: str = "free",
    window: str = "hour",
) -> int:
    """
    Increment rate limit counter for a user or IP.

    This is a convenience function that just increments the counter
    without checking limits. Use check_rate_limit() for enforcement.

    Args:
        user_id: User ID (None for anonymous)
        ip_address: Client IP address
        tier: User tier
        window: Time window (hour or day)

    Returns:
        Current count after increment

    Example:
        >>> count = await increment_rate_limit(user_id=123, tier="pro")
        >>> print(f"User has made {count} requests this hour")
    """
    window_seconds = 3600 if window == "hour" else 86400

    # Build cache key
    if user_id:
        key = f"ratelimit:user:{user_id}:{window}"
    elif ip_address:
        key = f"ratelimit:ip:{ip_address}:{window}"
    else:
        return 0

    # Try Redis first, fall back to memory
    redis_available = await check_redis_health()

    if redis_available:
        count = await redis_incr(key, expire=window_seconds)
        if count is None:
            count = await memory_incr(key, expire=window_seconds)
    else:
        count = await memory_incr(key, expire=window_seconds)

    return count


def get_endpoint_cost(path: str, method: str = "GET") -> int:
    """
    Get cost multiplier for specific endpoints.

    Some endpoints are more expensive than others. This function
    returns how many "request credits" an endpoint costs.

    Args:
        path: Request path
        method: HTTP method

    Returns:
        Cost multiplier (1 = normal, 2 = expensive, etc.)

    Example:
        >>> cost = get_endpoint_cost("/api/v1/batch", "POST")
        >>> print(cost)
        5  # Batch operations cost 5x normal requests
    """
    # Free endpoints (don't count against quota) - check FIRST
    free_patterns = [
        "/health",
        "/metrics",
        "/docs",
        "/openapi.json",
        "/api/v2/auth/login",  # Login shouldn't count
        "/api/v2/auth/register",  # Registration shouldn't count
        "/api/auth/login",  # Version-less login
        "/api/auth/register",  # Version-less registration
        "/api/agents/search",  # Search endpoint free for demo/testing
        "/api/v1/agents/search",  # Legacy search endpoint
    ]

    for pattern in free_patterns:
        if path.startswith(pattern):
            return 0

    # Expensive endpoints (checked AFTER free endpoints)
    expensive_patterns = {
        "/api/v1/batch": 5,  # Batch operations are expensive
        "/api/batch": 5,  # Version-less batch operations
        "/api/v1/agents": 2,  # AI agent calls are expensive
        "/api/agents": 2,  # Version-less agent calls
        "/api/v1/workflows": 2,  # Workflow execution is expensive
        "/api/workflows": 2,  # Version-less workflows
    }

    # Check if path matches any expensive pattern
    for pattern, cost in expensive_patterns.items():
        if path.startswith(pattern):
            return cost

    # Default cost
    return 1


# Export public API
__all__ = [
    "TierType",
    "QuotaLimits",
    "RateLimitInfo",
    "get_tier_quota",
    "check_rate_limit",
    "increment_rate_limit",
    "get_endpoint_cost",
]
