"""
GEO Registry - Cache-First GEO-centric data store

This module provides a high-performance cache layer for GEO datasets using:
- GEOCache (2-tier: Redis hot-tier + UnifiedDB warm-tier)
- No legacy SQLite support
- Cache-only architecture

Key Features:
- Sub-millisecond lookup for cached GEO datasets (Redis)
- Complete data retrieval via UnifiedDB (about 50ms on cache miss)
- Write-through cache with automatic invalidation
- Async-first API design

Usage:
    registry = GEORegistry()
    data = await registry.get_complete_geo_data("GSE12345")
    await registry.invalidate_cache("GSE12345")
    stats = await registry.get_stats()

Migration Note:
    Old SQLite database (data/omics_oracle.db) is NO LONGER USED.
    All data must be in UnifiedDatabase before using this class.
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class GEORegistry:
    """Cache-first registry for GEO datasets."""

    def __init__(self, unified_db_path: str = "data/database/omics_oracle.db", redis_ttl_days: int = 7):
        """Initialize registry with GEOCache (cache-only)."""
        from .geo_cache import GEOCache
        from ..unified_db import UnifiedDatabase
        
        unified_db = UnifiedDatabase(unified_db_path)
        self.cache = GEOCache(unified_db, redis_ttl_days=redis_ttl_days)
        logger.info("GEORegistry initialized: GEOCache only (Redis + UnifiedDB)")

    async def get_complete_geo_data(self, geo_id: str) -> Optional[Dict]:
        """Get ALL data for GEO ID from cache."""
        return await self.cache.get(geo_id)

    async def invalidate_cache(self, geo_id: str) -> bool:
        """Invalidate cache entry for GEO ID."""
        return await self.cache.invalidate(geo_id)

    async def invalidate_batch(self, geo_ids: List[str]) -> int:
        """Invalidate multiple cache entries in parallel."""
        return await self.cache.invalidate_batch(geo_ids)

    async def get_stats(self) -> Dict:
        """Get cache performance statistics."""
        return await self.cache.get_stats()

    async def warm_up(self, geo_ids: List[str]) -> int:
        """Pre-populate cache with frequently accessed GEO datasets."""
        return await self.cache.warm_up(geo_ids)


# Global registry instance
_registry: Optional[GEORegistry] = None


def get_registry() -> GEORegistry:
    """Get global registry instance (singleton)."""
    global _registry
    if _registry is None:
        _registry = GEORegistry()
        logger.info("Global GEORegistry initialized (cache-only)")
    return _registry
