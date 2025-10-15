"""
Cache module for OmicsOracle.

Provides unified caching system:
- redis_client: Simple operations for API/rate limiting (functional API)
- redis_cache: Domain-specific caching for search/GEO/publications (class-based API)
- fallback: In-memory cache when Redis unavailable
- parsed_cache: 2-tier cache for parsed PDF/XML content (Redis + Disk)
- discovery_cache: Citation discovery results cache (Memory + SQLite)
- cache_db: Metadata index for full-text cache analytics
- smart_cache: Multi-directory file locator for PDFs/XMLs

Architecture:
- API layer -> redis_client (simple key-value operations)
- Domain layer -> RedisCache (search results, metadata, TTL management)
- Pipeline caches -> Specialized caching for specific domains
"""

from omics_oracle_v2.cache.fallback import (memory_cleanup, memory_clear,
                                            memory_delete, memory_exists,
                                            memory_get, memory_incr,
                                            memory_size, memory_ttl)
from omics_oracle_v2.cache.redis_cache import RedisCache
from omics_oracle_v2.cache.redis_client import (check_redis_health,
                                                close_redis_client,
                                                get_redis_client, redis_delete,
                                                redis_exists, redis_get,
                                                redis_incr, redis_set,
                                                redis_ttl)

# Lazy imports to avoid circular dependencies
# Use: from omics_oracle_v2.cache.parsed_cache import ParsedCache
# Use: from omics_oracle_v2.cache.discovery_cache import DiscoveryCache
# Use: from omics_oracle_v2.cache.cache_db import FullTextCacheDB
# Use: from omics_oracle_v2.cache.smart_cache import SmartCache

__all__ = [
    # Domain cache (search, GEO, publications)
    "RedisCache",
    # Redis client (API/rate limiting)
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
    # Pipeline caches (use direct imports to avoid circular dependencies)
    # "ParsedCache", "DiscoveryCache", "FullTextCacheDB", "SmartCache"
]
