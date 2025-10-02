"""
GEO database access library.

Provides programmatic access to NCBI Gene Expression Omnibus (GEO) database
with automatic caching, error handling, and data parsing.

Key Components:
    - UnifiedGEOClient: Main client for GEO data access
    - GEO models: Type-safe data models for series, samples, platforms
    - Cache layer: Automatic response caching to reduce API calls
    - Parsers: SOFT and MINiML format parsers

Example:
    >>> from omics_oracle_v2.lib.geo import UnifiedGEOClient
    >>> client = UnifiedGEOClient()
    >>> series = client.get_series("GSE123456")
    >>> print(f"{series.title}: {series.sample_count} samples")

Status: Phase 1 Task 4 (In Progress)
"""

# Exports will be added as modules are implemented
# from .client import UnifiedGEOClient
# from .models import GEOSeries, GEOSample, GEOPlatform

__all__ = []
