"""
GEO database access library.

Provides programmatic access to NCBI Gene Expression Omnibus (GEO) database
with automatic caching, error handling, and data parsing.

Key Components:
    - GEOClient: Main client for GEO data access
    - GEO models: Type-safe data models for series, samples, platforms
    - Cache layer: Automatic response caching to reduce API calls
    - Rate limiting: NCBI-compliant request throttling

Example:
    >>> from omics_oracle_v2.lib.search_engines.geo import GEOClient
    >>> import asyncio
    >>>
    >>> async def example():
    ...     client = GEOClient()
    ...     metadata = await client.get_metadata("GSE123456")
    ...     print(f"{metadata.title}: {metadata.sample_count} samples")
    ...     await client.close()
    >>>
    >>> asyncio.run(example())

Status: Phase 1 Task 4 (Complete)
"""

from .client import GEOClient, NCBIClient
from .models import ClientInfo, GEOPlatform, GEOSample, GEOSeriesMetadata, SearchResult, SRAInfo
from .utils import RateLimiter, retry_with_backoff

__all__ = [
    "GEOClient",
    "NCBIClient",
    "RateLimiter",
    "retry_with_backoff",
    "GEOSeriesMetadata",
    "GEOSample",
    "GEOPlatform",
    "SRAInfo",
    "SearchResult",
    "ClientInfo",
]
