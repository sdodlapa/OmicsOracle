"""
Cache module for OmicsOracle.

Provides Redis-based caching with automatic fallback to in-memory cache
when Redis is unavailable. Used for rate limiting and general caching.
"""

from omics_oracle_v2.cache.fallback import (
    memory_cleanup,
    memory_clear,
    memory_delete,
    memory_exists,
    memory_get,
    memory_incr,
    memory_size,
    memory_ttl,
)
from omics_oracle_v2.cache.redis_client import (
    check_redis_health,
    close_redis_client,
    get_redis_client,
    redis_delete,
    redis_exists,
    redis_get,
    redis_incr,
    redis_set,
    redis_ttl,
)

__all__ = [
    # Redis client
    "get_redis_client",
    "close_redis_client",
    "check_redis_health",
    "redis_get",
    "redis_set",
    "redis_incr",
    "redis_delete",
    "redis_ttl",
    "redis_exists",
    # Memory fallback
    "memory_incr",
    "memory_get",
    "memory_delete",
    "memory_ttl",
    "memory_exists",
    "memory_clear",
    "memory_size",
    "memory_cleanup",
]
