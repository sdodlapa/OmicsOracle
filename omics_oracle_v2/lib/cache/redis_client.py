"""
Async Redis cache client for high-performance caching.

Provides:
- Async Redis operations
- Automatic serialization (pickle/JSON)
- TTL management
- Cache statistics
- Key generation utilities
"""

import hashlib
import logging
import pickle
from typing import Any, Dict, Optional

import redis.asyncio as redis

logger = logging.getLogger(__name__)


class AsyncRedisCache:
    """
    Async Redis cache client.

    Features:
    - Async get/set operations
    - Automatic TTL management
    - Pickle serialization for complex objects
    - Cache statistics tracking
    - Pattern-based deletion

    Example:
        >>> cache = AsyncRedisCache()
        >>> await cache.set("key", {"data": "value"}, ttl=3600)
        >>> result = await cache.get("key")
        >>> stats = cache.get_stats()
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        default_ttl: int = 3600,
    ):
        """
        Initialize Redis cache client.

        Args:
            host: Redis host
            port: Redis port
            db: Redis database number (0-15)
            password: Redis password (if required)
            default_ttl: Default TTL in seconds (1 hour default)
        """
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.default_ttl = default_ttl

        # Initialize Redis client
        self.redis = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=False,  # Binary mode for pickle
        )

        # Statistics
        self.hits = 0
        self.misses = 0

        logger.info(f"Redis cache initialized: {host}:{port}/{db}")

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        try:
            value = await self.redis.get(key)
            if value:
                self.hits += 1
                logger.debug(f"Cache HIT: {key[:32]}...")
                return pickle.loads(value)
            else:
                self.misses += 1
                logger.debug(f"Cache MISS: {key[:32]}...")
                return None
        except Exception as e:
            logger.error(f"Cache get error for key {key[:32]}: {e}")
            self.misses += 1
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Set value in cache with TTL.

        Args:
            key: Cache key
            value: Value to cache (will be pickled)
            ttl: Time to live in seconds (uses default if not provided)
        """
        try:
            ttl = ttl or self.default_ttl
            serialized = pickle.dumps(value)
            await self.redis.setex(key, ttl, serialized)
            logger.debug(f"Cache SET: {key[:32]}... (TTL: {ttl}s)")
        except Exception as e:
            logger.error(f"Cache set error for key {key[:32]}: {e}")

    async def delete(self, key: str):
        """
        Delete key from cache.

        Args:
            key: Cache key to delete
        """
        try:
            await self.redis.delete(key)
            logger.debug(f"Cache DELETE: {key[:32]}...")
        except Exception as e:
            logger.error(f"Cache delete error for key {key[:32]}: {e}")

    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists
        """
        try:
            return bool(await self.redis.exists(key))
        except Exception as e:
            logger.error(f"Cache exists error for key {key[:32]}: {e}")
            return False

    async def clear_pattern(self, pattern: str):
        """
        Clear all keys matching pattern.

        Args:
            pattern: Pattern to match (e.g., "search:*")

        Note:
            Uses SCAN for safe iteration over large keyspaces
        """
        try:
            cursor = 0
            deleted_count = 0

            while True:
                cursor, keys = await self.redis.scan(cursor=cursor, match=pattern, count=100)

                if keys:
                    await self.redis.delete(*keys)
                    deleted_count += len(keys)

                if cursor == 0:
                    break

            logger.info(f"Cleared {deleted_count} keys matching pattern: {pattern}")
        except Exception as e:
            logger.error(f"Cache clear pattern error for {pattern}: {e}")

    async def clear_all(self):
        """Clear all keys in current database."""
        try:
            await self.redis.flushdb()
            logger.info("Cleared all cache keys")
        except Exception as e:
            logger.error(f"Cache clear all error: {e}")

    async def get_ttl(self, key: str) -> Optional[int]:
        """
        Get TTL for a key.

        Args:
            key: Cache key

        Returns:
            TTL in seconds, -1 if no TTL, None if key doesn't exist
        """
        try:
            ttl = await self.redis.ttl(key)
            return ttl if ttl >= -1 else None
        except Exception as e:
            logger.error(f"Cache TTL error for key {key[:32]}: {e}")
            return None

    async def set_ttl(self, key: str, ttl: int):
        """
        Update TTL for existing key.

        Args:
            key: Cache key
            ttl: New TTL in seconds
        """
        try:
            await self.redis.expire(key, ttl)
            logger.debug(f"Cache TTL updated: {key[:32]}... -> {ttl}s")
        except Exception as e:
            logger.error(f"Cache set TTL error for key {key[:32]}: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dict with hits, misses, and hit rate
        """
        total = self.hits + self.misses
        hit_rate = self.hits / total if total > 0 else 0

        return {
            "hits": self.hits,
            "misses": self.misses,
            "total_requests": total,
            "hit_rate": hit_rate,
            "hit_rate_percent": hit_rate * 100,
        }

    def reset_stats(self):
        """Reset cache statistics."""
        self.hits = 0
        self.misses = 0
        logger.info("Cache statistics reset")

    async def close(self):
        """Close Redis connection."""
        try:
            await self.redis.close()
            logger.info("Redis cache connection closed")
        except Exception as e:
            logger.error(f"Error closing Redis connection: {e}")

    @staticmethod
    def generate_key(prefix: str, *args, **kwargs) -> str:
        """
        Generate cache key from arguments.

        Creates a stable hash-based key from function arguments.

        Args:
            prefix: Key prefix (e.g., "search", "llm")
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            SHA256 hash-based cache key

        Example:
            >>> key = AsyncRedisCache.generate_key("search", "cancer", max_results=50)
            >>> # Returns: "search:a1b2c3d4..."
        """
        # Create stable string representation
        content = f"{prefix}:{args}:{sorted(kwargs.items())}"

        # Generate hash
        hash_value = hashlib.sha256(content.encode()).hexdigest()

        # Return prefixed key
        return f"{prefix}:{hash_value}"


class CacheDecorator:
    """
    Decorator for caching async function results.

    Example:
        >>> cache = AsyncRedisCache()
        >>> decorator = CacheDecorator(cache)
        >>>
        >>> @decorator.cached(ttl=3600, key_prefix="my_func")
        >>> async def my_function(arg1, arg2):
        >>>     return expensive_computation(arg1, arg2)
    """

    def __init__(self, cache: AsyncRedisCache):
        """
        Initialize cache decorator.

        Args:
            cache: AsyncRedisCache instance
        """
        self.cache = cache

    def cached(self, ttl: Optional[int] = None, key_prefix: str = "cache"):
        """
        Decorator to cache async function results.

        Args:
            ttl: TTL in seconds (uses cache default if not provided)
            key_prefix: Prefix for cache keys

        Returns:
            Decorated function
        """

        def decorator(func):
            async def wrapper(*args, **kwargs):
                # Generate cache key
                cache_key = self.cache.generate_key(f"{key_prefix}:{func.__name__}", *args, **kwargs)

                # Try cache first
                cached_value = await self.cache.get(cache_key)
                if cached_value is not None:
                    logger.debug(f"Cache HIT for {func.__name__}: {cache_key[:16]}...")
                    return cached_value

                # Cache miss - execute function
                logger.debug(f"Cache MISS for {func.__name__}: {cache_key[:16]}...")
                result = await func(*args, **kwargs)

                # Store in cache
                await self.cache.set(cache_key, result, ttl)

                return result

            return wrapper

        return decorator
