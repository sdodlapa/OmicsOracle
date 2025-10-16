"""
Registry Module - Centralized data storage for GEO datasets and publications

Moved to storage.registry as part of package consolidation (Oct 2025).

NEW (Oct 15, 2025): GEOCache integration
- GEOCache: 2-tier cache (Redis hot-tier → UnifiedDB warm-tier)
- GEORegistry: Enhanced with cache support (use_cache=True by default)
- create_geo_cache: Factory function for cache instances
"""

from omics_oracle_v2.lib.pipelines.storage.registry.geo_registry import (
    GEORegistry,
    get_registry
)
from omics_oracle_v2.lib.pipelines.storage.registry.geo_cache import (
    GEOCache,
    create_geo_cache
)

__all__ = [
    "GEORegistry", 
    "get_registry",
    "GEOCache",
    "create_geo_cache"
]
