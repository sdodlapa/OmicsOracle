"""
In-memory fallback cache for rate limiting when Redis is unavailable.

Uses Python's asyncio locks and dictionaries to provide thread-safe
rate limiting without external dependencies. Note: This is per-instance
and does not work in distributed/multi-instance deployments.
"""

import asyncio
import logging
import time
from typing import Dict, Tuple

logger = logging.getLogger(__name__)

# Global in-memory cache
_memory_cache: Dict[str, Tuple[int, float]] = {}  # key -> (count, expire_time)
_cache_lock = asyncio.Lock()


async def memory_incr(key: str, expire: int | None = None) -> int:
    """
    Increment counter in memory with optional expiration.

    Args:
        key: Cache key
        expire: Expiration time in seconds

    Returns:
        New counter value

    Example:
        >>> count = await memory_incr("user:123:hour", expire=3600)
        >>> print(count)
        1
    """
    async with _cache_lock:
        now = time.time()

        # Clean up expired keys (garbage collection)
        expired_keys = [
            k for k, (_, expire_time) in _memory_cache.items() if expire_time > 0 and expire_time < now
        ]
        for k in expired_keys:
            del _memory_cache[k]

        # Get or create counter
        if key in _memory_cache:
            count, expire_time = _memory_cache[key]
            # Check if expired
            if expire_time > 0 and expire_time < now:
                count = 0
                expire_time = now + expire if expire else 0
            count += 1
        else:
            count = 1
            expire_time = now + expire if expire else 0

        _memory_cache[key] = (count, expire_time)
        return count


async def memory_get(key: str) -> int | None:
    """
    Get counter value from memory.

    Args:
        key: Cache key

    Returns:
        Counter value or None if not found/expired

    Example:
        >>> count = await memory_get("user:123:hour")
        >>> print(count)
        5
    """
    async with _cache_lock:
        now = time.time()

        if key not in _memory_cache:
            return None

        count, expire_time = _memory_cache[key]

        # Check if expired
        if expire_time > 0 and expire_time < now:
            del _memory_cache[key]
            return None

        return count


async def memory_delete(key: str) -> bool:
    """
    Delete key from memory cache.

    Args:
        key: Cache key

    Returns:
        True if key existed, False otherwise

    Example:
        >>> await memory_delete("user:123:hour")
        True
    """
    async with _cache_lock:
        if key in _memory_cache:
            del _memory_cache[key]
            return True
        return False


async def memory_ttl(key: str) -> int | None:
    """
    Get time-to-live for a key.

    Args:
        key: Cache key

    Returns:
        TTL in seconds, -1 if no expiry, -2 if key doesn't exist

    Example:
        >>> ttl = await memory_ttl("user:123:hour")
        >>> print(ttl)
        3599
    """
    async with _cache_lock:
        now = time.time()

        if key not in _memory_cache:
            return -2

        _, expire_time = _memory_cache[key]

        if expire_time == 0:
            return -1  # No expiration

        remaining = int(expire_time - now)
        if remaining <= 0:
            del _memory_cache[key]
            return -2

        return remaining


async def memory_exists(key: str) -> bool:
    """
    Check if key exists in memory cache.

    Args:
        key: Cache key

    Returns:
        True if key exists and not expired

    Example:
        >>> if await memory_exists("user:123:hour"):
        >>>     print("Key exists")
    """
    async with _cache_lock:
        now = time.time()

        if key not in _memory_cache:
            return False

        _, expire_time = _memory_cache[key]

        # Check if expired
        if expire_time > 0 and expire_time < now:
            del _memory_cache[key]
            return False

        return True


async def memory_clear() -> None:
    """
    Clear all keys from memory cache.

    Useful for testing and cleanup.

    Example:
        >>> await memory_clear()
    """
    async with _cache_lock:
        _memory_cache.clear()
        logger.info("Memory cache cleared")


async def memory_size() -> int:
    """
    Get number of keys in memory cache.

    Returns:
        Number of keys (excluding expired)

    Example:
        >>> size = await memory_size()
        >>> print(f"Cache has {size} keys")
    """
    async with _cache_lock:
        now = time.time()

        # Count only non-expired keys
        count = sum(
            1 for _, (_, expire_time) in _memory_cache.items() if expire_time == 0 or expire_time > now
        )
        return count


async def memory_cleanup() -> int:
    """
    Remove all expired keys from memory cache.

    Returns:
        Number of keys removed

    Example:
        >>> removed = await memory_cleanup()
        >>> logger.info(f"Cleaned up {removed} expired keys")
    """
    async with _cache_lock:
        now = time.time()

        expired_keys = [
            k for k, (_, expire_time) in _memory_cache.items() if expire_time > 0 and expire_time < now
        ]

        for k in expired_keys:
            del _memory_cache[k]

        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired keys from memory cache")

        return len(expired_keys)


# Export public API
__all__ = [
    "memory_incr",
    "memory_get",
    "memory_delete",
    "memory_ttl",
    "memory_exists",
    "memory_clear",
    "memory_size",
    "memory_cleanup",
]
