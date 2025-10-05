"""
Redis client module for caching and rate limiting.

Provides async Redis client with connection pooling, health checks,
and graceful fallback to in-memory cache if Redis is unavailable.
"""

import logging
from typing import Any

from redis.asyncio import ConnectionPool, Redis
from redis.exceptions import ConnectionError, TimeoutError

from omics_oracle_v2.core.config import Settings

logger = logging.getLogger(__name__)

# Global Redis client instance
_redis_client: Redis | None = None
_redis_pool: ConnectionPool | None = None
_redis_available: bool = False


async def get_redis_client() -> Redis | None:
    """
    Get or create Redis client instance.

    Returns:
        Redis client if available, None if Redis is unavailable

    Example:
        >>> redis = await get_redis_client()
        >>> if redis:
        >>>     await redis.set("key", "value")
    """
    global _redis_client, _redis_pool, _redis_available

    if _redis_client is not None:
        return _redis_client if _redis_available else None

    try:
        settings = Settings()
        redis_settings = settings.redis

        # Create connection pool
        _redis_pool = ConnectionPool.from_url(
            redis_settings.url,
            password=redis_settings.password,
            max_connections=redis_settings.max_connections,
            socket_timeout=redis_settings.socket_timeout,
            socket_connect_timeout=redis_settings.socket_connect_timeout,
            decode_responses=redis_settings.decode_responses,
            health_check_interval=redis_settings.health_check_interval,
        )

        # Create Redis client
        _redis_client = Redis(connection_pool=_redis_pool)

        # Test connection
        await _redis_client.ping()
        _redis_available = True
        logger.info("Redis client initialized successfully")

        return _redis_client

    except (ConnectionError, TimeoutError, Exception) as e:
        logger.warning(f"Redis connection failed: {e}. Falling back to in-memory cache.")
        _redis_available = False
        _redis_client = None
        return None


async def close_redis_client() -> None:
    """
    Close Redis client and connection pool.

    Should be called during application shutdown.
    """
    global _redis_client, _redis_pool, _redis_available

    if _redis_client is not None:
        try:
            await _redis_client.aclose()
            logger.info("Redis client closed")
        except Exception as e:
            logger.error(f"Error closing Redis client: {e}")
        finally:
            _redis_client = None
            _redis_pool = None
            _redis_available = False


async def check_redis_health() -> bool:
    """
    Check if Redis is healthy and available.

    Returns:
        True if Redis is healthy, False otherwise

    Example:
        >>> if await check_redis_health():
        >>>     # Use Redis
        >>>     pass
        >>> else:
        >>>     # Use fallback
        >>>     pass
    """
    global _redis_available

    redis = await get_redis_client()
    if redis is None:
        _redis_available = False
        return False

    try:
        await redis.ping()
        _redis_available = True
        return True
    except Exception as e:
        logger.warning(f"Redis health check failed: {e}")
        _redis_available = False
        return False


async def redis_get(key: str) -> str | None:
    """
    Get value from Redis.

    Args:
        key: Redis key

    Returns:
        Value if found, None otherwise

    Example:
        >>> value = await redis_get("mykey")
        >>> print(value)
        "myvalue"
    """
    redis = await get_redis_client()
    if redis is None:
        return None

    try:
        return await redis.get(key)
    except Exception as e:
        logger.error(f"Redis GET error for key '{key}': {e}")
        return None


async def redis_set(
    key: str,
    value: Any,
    expire: int | None = None,
) -> bool:
    """
    Set value in Redis with optional expiration.

    Args:
        key: Redis key
        value: Value to store
        expire: Expiration time in seconds (optional)

    Returns:
        True if successful, False otherwise

    Example:
        >>> await redis_set("mykey", "myvalue", expire=3600)
        True
    """
    redis = await get_redis_client()
    if redis is None:
        return False

    try:
        if expire is not None:
            await redis.setex(key, expire, value)
        else:
            await redis.set(key, value)
        return True
    except Exception as e:
        logger.error(f"Redis SET error for key '{key}': {e}")
        return False


async def redis_incr(key: str, expire: int | None = None) -> int | None:
    """
    Increment Redis counter atomically.

    Args:
        key: Redis key
        expire: Set expiration if key doesn't exist (seconds)

    Returns:
        New counter value, or None if Redis unavailable

    Example:
        >>> count = await redis_incr("request:counter", expire=3600)
        >>> print(count)
        1
    """
    redis = await get_redis_client()
    if redis is None:
        return None

    try:
        # Use pipeline for atomic operation
        pipe = redis.pipeline()
        pipe.incr(key)
        if expire is not None:
            # Only set expire if this is the first increment
            pipe.expire(key, expire, nx=True)
        results = await pipe.execute()
        return results[0]  # Return the incremented value
    except Exception as e:
        logger.error(f"Redis INCR error for key '{key}': {e}")
        return None


async def redis_delete(key: str) -> bool:
    """
    Delete key from Redis.

    Args:
        key: Redis key to delete

    Returns:
        True if successful, False otherwise

    Example:
        >>> await redis_delete("mykey")
        True
    """
    redis = await get_redis_client()
    if redis is None:
        return False

    try:
        await redis.delete(key)
        return True
    except Exception as e:
        logger.error(f"Redis DELETE error for key '{key}': {e}")
        return False


async def redis_ttl(key: str) -> int | None:
    """
    Get time-to-live for a key.

    Args:
        key: Redis key

    Returns:
        TTL in seconds, -1 if no expiry, -2 if key doesn't exist, None if Redis unavailable

    Example:
        >>> ttl = await redis_ttl("mykey")
        >>> print(ttl)
        3599
    """
    redis = await get_redis_client()
    if redis is None:
        return None

    try:
        return await redis.ttl(key)
    except Exception as e:
        logger.error(f"Redis TTL error for key '{key}': {e}")
        return None


async def redis_exists(key: str) -> bool:
    """
    Check if key exists in Redis.

    Args:
        key: Redis key

    Returns:
        True if key exists, False otherwise

    Example:
        >>> if await redis_exists("mykey"):
        >>>     print("Key exists")
    """
    redis = await get_redis_client()
    if redis is None:
        return False

    try:
        return await redis.exists(key) > 0
    except Exception as e:
        logger.error(f"Redis EXISTS error for key '{key}': {e}")
        return False


# Export public API
__all__ = [
    "get_redis_client",
    "close_redis_client",
    "check_redis_health",
    "redis_get",
    "redis_set",
    "redis_incr",
    "redis_delete",
    "redis_ttl",
    "redis_exists",
]
