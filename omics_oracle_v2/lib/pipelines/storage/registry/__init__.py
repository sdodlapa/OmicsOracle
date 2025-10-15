"""
Registry Module - Centralized data storage for GEO datasets and publications

Moved to storage.registry as part of package consolidation (Oct 2025).
"""

from omics_oracle_v2.lib.pipelines.storage.registry.geo_registry import (GEORegistry,
                                                               get_registry)

__all__ = ["GEORegistry", "get_registry"]
