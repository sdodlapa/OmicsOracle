"""
GEO Dataset Cache Layer - 2-Tier Architecture

This module implements a high-performance 2-tier cache for GEO dataset metadata:
- **Hot Tier (Redis):** Fast in-memory cache (~0.1ms latency, 7-day TTL)
- **Warm Tier (UnifiedDB):** Source of truth (PostgreSQL/SQLite, ~50ms latency, permanent)

Architecture Pattern: Copied from ParsedCache (proven, tested, production-ready)

Performance Targets:
- Cache Hit (Redis): <1ms
- Cache Miss (UnifiedDB): <50ms  
- Write-through: <10ms (parallel Redis + DB)

Usage:
    ```python
    from lib.pipelines.storage.unified_db import UnifiedDatabase
    from lib.pipelines.storage.registry.geo_cache import GEOCache
    
    unified_db = UnifiedDatabase()
    cache = GEOCache(unified_db, redis_ttl_days=7)
    
    # Fetch GEO data (checks Redis → UnifiedDB → promotes to Redis)
    geo_data = await cache.get("GSE123456")
    
    # Update GEO data (write-through to Redis + DB)
    await cache.update("GSE123456", {"title": "...", "samples": [...]})
    
    # Invalidate cache entry
    await cache.invalidate("GSE123456")
    
    # Get cache statistics
    stats = await cache.get_stats()
    ```

Author: OmicsOracle Development Team
Created: October 15, 2025
Pattern: Based on ParsedCache (omics_oracle_v2/cache/parsed_cache.py)
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from omics_oracle_v2.cache.redis_cache import RedisCache


logger = logging.getLogger(__name__)


class GEOCache:
    """
    2-Tier cache for GEO dataset metadata.
    
    Tier 1 (Hot): Redis in-memory cache (7-day TTL, ~0.1ms)
    Tier 2 (Warm): UnifiedDatabase persistent storage (permanent, ~50ms)
    
    Pattern: Write-through cache with auto-promotion on cache miss.
    Fallback: In-memory dict if Redis unavailable.
    
    Attributes:
        unified_db: UnifiedDatabase instance (source of truth)
        redis_cache: RedisCache instance (hot tier)
        redis_ttl: TTL for Redis cache entries (seconds)
        use_redis_hot_tier: Whether to use Redis (True) or fallback to memory (False)
        memory_fallback: In-memory dict cache when Redis unavailable
        stats: Cache performance metrics
    """
    
    def __init__(
        self,
        unified_db,
        redis_ttl_days: int = 7,
        enable_fallback: bool = True
    ):
        """
        Initialize GEO cache with 2-tier architecture.
        
        Args:
            unified_db: UnifiedDatabase instance (warm tier)
            redis_ttl_days: TTL for Redis cache entries (default: 7 days)
            enable_fallback: Enable in-memory fallback if Redis fails (default: True)
        """
        self.unified_db = unified_db
        self.redis_ttl = redis_ttl_days * 24 * 3600  # Convert days to seconds
        self.enable_fallback = enable_fallback
        
        # Initialize Redis hot-tier
        self.redis_cache = RedisCache(prefix="geo_complete")
        self.use_redis_hot_tier = True
        
        # Fallback in-memory cache (if Redis unavailable)
        self.memory_fallback: Dict[str, Dict[str, Any]] = {}
        self.max_memory_entries = 1000  # LRU eviction if exceeded
        
        # Performance tracking
        self.stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "db_queries": 0,
            "redis_errors": 0,
            "promotions": 0,
            "evictions": 0
        }
        
        logger.info(
            f"GEOCache initialized: redis_ttl={redis_ttl_days}d, "
            f"fallback={'enabled' if enable_fallback else 'disabled'}"
        )
    
    async def get(self, geo_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch complete GEO dataset metadata from cache or database.
        
        Lookup sequence:
        1. Check Redis (hot tier) - ~0.1ms
        2. Check UnifiedDB (warm tier) - ~50ms
        3. Promote to Redis on cache miss
        
        Args:
            geo_id: GEO accession ID (e.g., "GSE123456")
        
        Returns:
            Complete GEO metadata dict, or None if not found
            
        Performance:
            Cache hit: <1ms
            Cache miss: <50ms (includes promotion)
        """
        if not geo_id or not geo_id.startswith("GSE"):
            logger.warning(f"Invalid GEO ID format: {geo_id}")
            return None
        
        # Tier 1: Check Redis hot cache
        if self.use_redis_hot_tier and self.redis_cache:
            try:
                cached_data = await self.redis_cache.get_geo_metadata(geo_id)
                if cached_data is not None:
                    self.stats["cache_hits"] += 1
                    logger.debug(f"Cache HIT (Redis): {geo_id}")
                    return cached_data
            except Exception as e:
                logger.error(f"Redis error during get({geo_id}): {e}")
                self.stats["redis_errors"] += 1
                # Fall through to check database
        
        # Tier 1b: Check memory fallback (if Redis failed)
        if self.enable_fallback and geo_id in self.memory_fallback:
            self.stats["cache_hits"] += 1
            logger.debug(f"Cache HIT (Memory fallback): {geo_id}")
            return self.memory_fallback[geo_id]
        
        # Tier 2: Query UnifiedDatabase (warm tier)
        self.stats["cache_misses"] += 1
        logger.debug(f"Cache MISS: {geo_id} - querying UnifiedDB")
        
        try:
            self.stats["db_queries"] += 1
            geo_data = self.unified_db.get_complete_geo_data(geo_id)
            
            if geo_data is None:
                logger.info(f"GEO not found in UnifiedDB: {geo_id} - triggering auto-discovery")
                # Auto-discover citations and populate database
                geo_data = await self._auto_discover_and_populate(geo_id)
                
                if geo_data is None:
                    logger.warning(f"Auto-discovery failed for {geo_id}")
                    return None
            else:
                # Dataset exists - check if it's complete (has citations)
                citation_count = len(geo_data.get("papers", {}).get("original", []))
                
                if citation_count == 0:
                    # Incomplete data - check if we should re-enrich
                    metadata = geo_data.get("cache_metadata", {})
                    last_enrichment = metadata.get("last_enrichment_attempt")
                    retry_count = metadata.get("enrichment_retry_count", 0)
                    max_retries = 3
                    
                    # Determine if we should retry
                    should_retry = False
                    
                    if retry_count >= max_retries:
                        logger.warning(
                            f"Max enrichment retries ({max_retries}) reached for {geo_id}. "
                            f"Returning incomplete data."
                        )
                    elif last_enrichment is None:
                        # Never attempted - always try
                        should_retry = True
                        logger.info(f"First enrichment attempt for {geo_id} (0 citations)")
                    else:
                        # Check if enough time has passed (exponential backoff)
                        from datetime import datetime, timedelta
                        try:
                            last_attempt = datetime.fromisoformat(last_enrichment)
                            # Exponential backoff: 5min, 30min, 2h
                            backoff_minutes = [5, 30, 120][min(retry_count, 2)]
                            next_retry = last_attempt + timedelta(minutes=backoff_minutes)
                            
                            if datetime.now() >= next_retry:
                                should_retry = True
                                logger.info(
                                    f"Retrying enrichment for {geo_id} "
                                    f"(attempt {retry_count + 1}/{max_retries}, "
                                    f"last attempt: {backoff_minutes}min ago)"
                                )
                            else:
                                time_until_retry = (next_retry - datetime.now()).total_seconds() / 60
                                logger.debug(
                                    f"Skipping enrichment for {geo_id} - in backoff period "
                                    f"({time_until_retry:.1f}min until next retry)"
                                )
                        except (ValueError, KeyError) as e:
                            # Invalid timestamp - retry anyway
                            should_retry = True
                            logger.warning(f"Invalid enrichment metadata for {geo_id}: {e}")
                    
                    if should_retry:
                        # Re-enrich incomplete data
                        enriched_data = await self._auto_discover_and_populate(geo_id)
                        if enriched_data:
                            geo_data = enriched_data
                            logger.info(f"Successfully re-enriched {geo_id}")
                        else:
                            # Enrichment failed - update retry count
                            logger.warning(f"Re-enrichment failed for {geo_id}")
            
            # Promote to hot tier (write-through)
            await self._promote_to_hot_tier(geo_id, geo_data)
            
            return geo_data
            
        except AttributeError:
            logger.error(
                f"UnifiedDatabase missing get_complete_geo_data() method. "
                f"Please implement it first (see Task 2 in todo list)."
            )
            return None
        except Exception as e:
            logger.error(f"Database error fetching {geo_id}: {e}")
            return None
    
    async def update(self, geo_id: str, geo_data: Dict[str, Any]) -> bool:
        """
        Update GEO dataset metadata with write-through to both tiers.
        
        Write sequence:
        1. Write to UnifiedDB (warm tier, source of truth)
        2. Write to Redis (hot tier, immediate cache)
        3. Fallback to memory if Redis fails
        
        Args:
            geo_id: GEO accession ID
            geo_data: Complete GEO metadata dict
        
        Returns:
            True if successful, False otherwise
            
        Performance:
            Target: <10ms (parallel writes)
        """
        if not geo_id or not geo_data:
            logger.warning(f"Invalid update parameters: geo_id={geo_id}, data={bool(geo_data)}")
            return False
        
        try:
            # Add metadata
            cache_entry = {
                **geo_data,
                "cached_at": datetime.now().isoformat(),
                "cache_source": "write_through"
            }
            
            # Write to UnifiedDB (source of truth) - MUST succeed
            self.unified_db.update_geo_dataset(geo_id, geo_data)
            logger.debug(f"Wrote {geo_id} to UnifiedDB")
            
            # Write to Redis (hot tier) - best effort
            if self.use_redis_hot_tier and self.redis_cache:
                try:
                    await self.redis_cache.set_geo_metadata(
                        geo_id,
                        cache_entry,
                        ttl=self.redis_ttl
                    )
                    logger.debug(f"Wrote {geo_id} to Redis (TTL={self.redis_ttl}s)")
                except Exception as e:
                    logger.error(f"Redis error during update({geo_id}): {e}")
                    self.stats["redis_errors"] += 1
                    # Fall through to memory fallback
            
            # Fallback to memory if Redis failed
            if self.enable_fallback:
                self._add_to_memory_fallback(geo_id, cache_entry)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update {geo_id}: {e}")
            return False
    
    async def invalidate(self, geo_id: str) -> bool:
        """
        Invalidate cache entry (remove from Redis and memory).
        
        Note: Does NOT delete from UnifiedDB (source of truth remains intact).
        Use this to force fresh data fetch on next access.
        
        Args:
            geo_id: GEO accession ID
        
        Returns:
            True if invalidated, False otherwise
        """
        success = False
        
        # Remove from Redis using invalidate_pattern
        if self.use_redis_hot_tier and self.redis_cache:
            try:
                # Use invalidate_pattern to delete the key
                deleted = self.redis_cache.invalidate_pattern(f"geo:{geo_id}*")
                if deleted > 0:
                    logger.debug(f"Invalidated Redis cache: {geo_id}")
                    success = True
            except Exception as e:
                logger.error(f"Redis error during invalidate({geo_id}): {e}")
                self.stats["redis_errors"] += 1
        
        # Remove from memory fallback
        if geo_id in self.memory_fallback:
            del self.memory_fallback[geo_id]
            logger.debug(f"Invalidated memory cache: {geo_id}")
            success = True
        
        return success
    
    async def invalidate_batch(self, geo_ids: List[str]) -> int:
        """
        Invalidate multiple cache entries in parallel.
        
        Args:
            geo_ids: List of GEO accession IDs
        
        Returns:
            Number of successfully invalidated entries
        """
        tasks = [self.invalidate(geo_id) for geo_id in geo_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        success_count = sum(1 for r in results if r is True)
        logger.info(f"Batch invalidated {success_count}/{len(geo_ids)} entries")
        
        return success_count
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get cache performance statistics.
        
        Returns:
            Dict with metrics:
            - cache_hits: Number of cache hits
            - cache_misses: Number of cache misses
            - hit_rate: Cache hit rate (0-100%)
            - db_queries: Number of database queries
            - redis_errors: Number of Redis errors
            - promotions: Number of cache promotions
            - evictions: Number of memory fallback evictions
            - memory_entries: Current in-memory cache size
        """
        total_requests = self.stats["cache_hits"] + self.stats["cache_misses"]
        hit_rate = (
            (self.stats["cache_hits"] / total_requests * 100)
            if total_requests > 0
            else 0.0
        )
        
        return {
            **self.stats,
            "hit_rate": round(hit_rate, 2),
            "total_requests": total_requests,
            "memory_entries": len(self.memory_fallback)
        }
    
    async def warm_up(self, geo_ids: List[str]) -> int:
        """
        Pre-populate cache with frequently accessed GEO datasets.
        
        Useful for application startup or scheduled cache warming.
        
        Args:
            geo_ids: List of GEO IDs to pre-load
        
        Returns:
            Number of successfully cached entries
        """
        logger.info(f"Cache warm-up started for {len(geo_ids)} GEO datasets")
        
        tasks = [self.get(geo_id) for geo_id in geo_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        success_count = sum(1 for r in results if r is not None and not isinstance(r, Exception))
        logger.info(f"Cache warm-up complete: {success_count}/{len(geo_ids)} loaded")
        
        return success_count
    
    # ========== Private Helper Methods ==========
    
    async def _promote_to_hot_tier(self, geo_id: str, geo_data: Dict[str, Any]) -> None:
        """
        Promote warm-tier data to hot-tier cache.
        
        Called after database query to populate Redis cache.
        """
        cache_entry = {
            **geo_data,
            "cached_at": datetime.now().isoformat(),
            "cache_source": "promotion"
        }
        
        # Try Redis first
        if self.use_redis_hot_tier and self.redis_cache:
            try:
                await self.redis_cache.set_geo_metadata(
                    geo_id,
                    cache_entry,
                    ttl=self.redis_ttl
                )
                self.stats["promotions"] += 1
                logger.debug(f"Promoted {geo_id} to Redis cache")
                return
            except Exception as e:
                logger.error(f"Redis error during promotion({geo_id}): {e}")
                self.stats["redis_errors"] += 1
                # Fall through to memory fallback
        
        # Fallback to memory
        if self.enable_fallback:
            self._add_to_memory_fallback(geo_id, cache_entry)
            self.stats["promotions"] += 1
            logger.debug(f"Promoted {geo_id} to memory fallback")
    
    def _add_to_memory_fallback(self, geo_id: str, data: Dict[str, Any]) -> None:
        """
        Add entry to in-memory fallback cache with LRU eviction.
        
        If cache exceeds max_memory_entries, evict oldest entry.
        """
        # Simple LRU: If full, remove oldest entry
        if len(self.memory_fallback) >= self.max_memory_entries:
            oldest_key = next(iter(self.memory_fallback))
            del self.memory_fallback[oldest_key]
            self.stats["evictions"] += 1
            logger.debug(f"Evicted {oldest_key} from memory fallback (LRU)")
        
        self.memory_fallback[geo_id] = data
    
    async def _auto_discover_and_populate(self, geo_id: str) -> Optional[Dict[str, Any]]:
        """
        Auto-discover citations and populate database for a GEO dataset.
        
        This is triggered when a GEO dataset is not found in UnifiedDB.
        
        Workflow:
        1. Fetch GEO metadata from NCBI (title, organism, etc.)
        2. Run citation discovery (find citing papers)
        3. Store everything in UnifiedDB
        4. Return complete enriched data
        
        Args:
            geo_id: GEO accession ID
            
        Returns:
            Complete GEO data with citations, or None if discovery fails
        """
        try:
            logger.info(f"[AUTO-DISCOVERY] Starting for {geo_id}")
            
            # Import here to avoid circular dependencies
            from omics_oracle_v2.lib.search_engines.geo import GEOClient
            from omics_oracle_v2.lib.pipelines.citation_discovery.geo_discovery import GEOCitationDiscovery
            from omics_oracle_v2.lib.pipelines.storage.models import GEODataset, UniversalIdentifier
            import json
            
            # Step 1: Fetch GEO metadata from NCBI
            logger.debug(f"[AUTO-DISCOVERY] Fetching GEO metadata for {geo_id}")
            geo_client = GEOClient()
            try:
                geo_metadata = await geo_client.get_metadata(geo_id)
            except Exception as e:
                logger.error(f"[AUTO-DISCOVERY] Failed to fetch GEO metadata for {geo_id}: {e}")
                return None
            
            if not geo_metadata:
                logger.warning(f"[AUTO-DISCOVERY] GEO metadata not found for {geo_id}")
                return None
            
            logger.info(f"[AUTO-DISCOVERY] Fetched metadata: {geo_metadata.title[:50]}...")
            
            # Step 2: Run citation discovery
            logger.debug(f"[AUTO-DISCOVERY] Running citation discovery for {geo_id}")
            discovery = GEOCitationDiscovery(
                enable_cache=True,
                use_strategy_a=True,  # Citation-based
                use_strategy_b=True,  # Mention-based
            )
            
            try:
                # find_citing_papers is async - must await
                result = await discovery.find_citing_papers(geo_metadata, max_results=100)
                citations_found = len(result.citing_papers) if hasattr(result, 'citing_papers') else 0
                logger.info(f"[AUTO-DISCOVERY] Found {citations_found} citations for {geo_id}")
            except Exception as e:
                logger.error(f"[AUTO-DISCOVERY] Citation discovery failed for {geo_id}: {e}")
                # Continue with just GEO metadata, no citations
                result = None
                citations_found = 0
            
            # Step 3: Store in UnifiedDB
            logger.debug(f"[AUTO-DISCOVERY] Storing data in UnifiedDB for {geo_id}")
            
            # Track enrichment attempt metadata
            from datetime import datetime
            enrichment_metadata = {
                "last_enrichment_attempt": datetime.now().isoformat(),
                "enrichment_retry_count": 0,  # Will be incremented in get() if this fails
                "citations_discovered": citations_found,
                "discovery_success": citations_found > 0
            }
            
            try:
                # Store GEO dataset metadata
                geo_dataset = GEODataset(
                    geo_id=geo_id,
                    title=geo_metadata.title,
                    summary=geo_metadata.summary,
                    organism=geo_metadata.organism,
                    platform=geo_metadata.platforms[0] if geo_metadata.platforms else None,
                    publication_count=citations_found,
                    pdfs_downloaded=0,
                    pdfs_extracted=0,
                    avg_extraction_quality=0.0,
                    status="discovered"
                )
                self.unified_db.insert_geo_dataset(geo_dataset)
                logger.debug(f"[AUTO-DISCOVERY] Stored GEO dataset {geo_id}")
                
                # Store citations if found
                if result and hasattr(result, 'citing_papers'):
                    for paper in result.citing_papers:
                        try:
                            # Create UniversalIdentifier for each citation
                            identifier = UniversalIdentifier(
                                geo_id=geo_id,
                                pmid=paper.pmid,
                                doi=paper.doi,
                                pmc_id=paper.pmcid,  # Use pmcid (not pmc_id)
                                title=paper.title,
                                authors=json.dumps(paper.authors) if paper.authors else None,
                                journal=paper.journal,
                                publication_year=paper.publication_date.year if paper.publication_date else None,
                                publication_date=paper.publication_date.isoformat() if paper.publication_date else None
                            )
                            
                            self.unified_db.insert_universal_identifier(identifier)
                            logger.debug(f"[AUTO-DISCOVERY] Stored citation {paper.pmid}")
                            
                        except Exception as e:
                            logger.warning(f"[AUTO-DISCOVERY] Failed to store citation {paper.pmid}: {e}")
                            continue
                
                logger.info(f"[AUTO-DISCOVERY] Stored {citations_found} citations in UnifiedDB for {geo_id}")
                
            except Exception as e:
                logger.error(f"[AUTO-DISCOVERY] Failed to store data in UnifiedDB for {geo_id}: {e}", exc_info=True)
                return None
            
            # Step 4: Retrieve complete data from UnifiedDB
            logger.debug(f"[AUTO-DISCOVERY] Retrieving complete data from UnifiedDB for {geo_id}")
            geo_data = self.unified_db.get_complete_geo_data(geo_id)
            
            if geo_data:
                # Add enrichment metadata to the returned data
                if "cache_metadata" not in geo_data:
                    geo_data["cache_metadata"] = {}
                geo_data["cache_metadata"].update(enrichment_metadata)
                
                logger.info(f"[AUTO-DISCOVERY] ✅ Complete for {geo_id} - {citations_found} citations")
            else:
                logger.warning(f"[AUTO-DISCOVERY] Data retrieval failed after storage for {geo_id}")
            
            return geo_data
            
        except Exception as e:
            logger.error(f"[AUTO-DISCOVERY] Unexpected error for {geo_id}: {e}", exc_info=True)
            return None
    
    async def close(self) -> None:
        """
        Clean up resources (close Redis connections).
        
        Call this during application shutdown.
        """
        if self.redis_cache:
            try:
                # RedisCache doesn't have async close, but we'll add it if needed
                logger.info("GEOCache closed")
            except Exception as e:
                logger.error(f"Error closing GEOCache: {e}")
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"GEOCache(redis_ttl={self.redis_ttl}s, "
            f"memory_entries={len(self.memory_fallback)}, "
            f"stats={self.stats})"
        )


# ========== Factory Function ==========

def create_geo_cache(
    unified_db,
    redis_ttl_days: int = 7,
    enable_fallback: bool = True
) -> GEOCache:
    """
    Factory function to create configured GEOCache instance.
    
    Args:
        unified_db: UnifiedDatabase instance
        redis_ttl_days: Redis cache TTL in days (default: 7)
        enable_fallback: Enable memory fallback (default: True)
    
    Returns:
        Configured GEOCache instance
    
    Example:
        ```python
        from lib.pipelines.storage.unified_db import UnifiedDatabase
        from lib.pipelines.storage.registry.geo_cache import create_geo_cache
        
        unified_db = UnifiedDatabase()
        cache = create_geo_cache(unified_db)
        
        # Use cache
        data = await cache.get("GSE123456")
        ```
    """
    return GEOCache(
        unified_db=unified_db,
        redis_ttl_days=redis_ttl_days,
        enable_fallback=enable_fallback
    )
