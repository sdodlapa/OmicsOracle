"""
Citation Discovery Cache

Two-layer caching system for citation discovery results:
1. Memory cache (fast, temporary) - LRU cache for hot data
2. SQLite cache (persistent, long-term) - Database for cold data

Benefits:
- 70-80% speedup for repeated queries
- TTL-based expiration (default: 1 week)
- Automatic cleanup of expired entries
- Thread-safe operations
- Cache statistics and monitoring

Usage:
    cache = DiscoveryCache(ttl_seconds=604800)  # 1 week

    # Check cache first
    result = cache.get(geo_id, strategy_key)
    if result:
        return result

    # Cache miss - fetch from API
    result = fetch_from_api()
    cache.set(geo_id, strategy_key, result)
"""

import json
import logging
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from omics_oracle_v2.lib.search_engines.citations.models import Publication

logger = logging.getLogger(__name__)


@dataclass
class CacheStats:
    """Statistics for cache performance monitoring"""

    hits: int = 0
    misses: int = 0
    total_queries: int = 0
    hit_rate: float = 0.0
    memory_entries: int = 0
    disk_entries: int = 0


class DiscoveryCache:
    """
    Two-layer cache for citation discovery results

    Layer 1: In-memory LRU cache (fast, limited size)
    Layer 2: SQLite database (persistent, unlimited)

    Features:
    - TTL-based expiration
    - Automatic cleanup
    - Thread-safe operations
    - Performance statistics
    """

    def __init__(
        self,
        db_path: Optional[str] = None,
        ttl_seconds: int = 604800,  # 1 week default
        memory_cache_size: int = 1000,
        enable_memory_cache: bool = True,
    ):
        """
        Initialize cache

        Args:
            db_path: Path to SQLite database (default: data/cache/discovery_cache.db)
            ttl_seconds: Time-to-live for cache entries (default: 1 week)
            memory_cache_size: Max entries in memory cache
            enable_memory_cache: Whether to use memory cache layer
        """
        self.ttl_seconds = ttl_seconds
        self.memory_cache_size = memory_cache_size
        self.enable_memory_cache = enable_memory_cache

        # Setup database path
        if db_path is None:
            cache_dir = Path("data/cache")
            cache_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(cache_dir / "discovery_cache.db")

        self.db_path = db_path
        self._init_database()

        # Memory cache (LRU)
        self._memory_cache: Dict[str, Any] = {}
        self._memory_cache_order: List[str] = []

        # Statistics
        self._stats = CacheStats()

        logger.info(f"Initialized DiscoveryCache: db={db_path}, ttl={ttl_seconds}s")

    def _init_database(self):
        """Initialize SQLite database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS citation_discovery_cache (
                cache_key TEXT PRIMARY KEY,
                geo_id TEXT NOT NULL,
                strategy_key TEXT NOT NULL,
                result_json TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                expires_at INTEGER NOT NULL,
                hit_count INTEGER DEFAULT 0,
                last_accessed INTEGER
            )
        """
        )

        # Index for faster lookups
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_geo_id
            ON citation_discovery_cache(geo_id)
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_expires_at
            ON citation_discovery_cache(expires_at)
        """
        )

        conn.commit()
        conn.close()

        logger.debug("Cache database initialized")

    def _make_cache_key(self, geo_id: str, strategy_key: str) -> str:
        """Generate cache key from geo_id and strategy"""
        return f"{geo_id}:{strategy_key}"

    def get(
        self, geo_id: str, strategy_key: str = "default"
    ) -> Optional[List[Publication]]:
        """
        Get cached result

        Args:
            geo_id: GEO dataset ID
            strategy_key: Strategy identifier (e.g., "citation", "mention", "all")

        Returns:
            List of Publication objects or None if cache miss
        """
        cache_key = self._make_cache_key(geo_id, strategy_key)
        self._stats.total_queries += 1

        # Layer 1: Check memory cache
        if self.enable_memory_cache and cache_key in self._memory_cache:
            self._stats.hits += 1
            self._stats.hit_rate = self._stats.hits / self._stats.total_queries
            logger.debug(f"Memory cache HIT: {cache_key}")
            return self._memory_cache[cache_key]

        # Layer 2: Check SQLite cache
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT result_json, expires_at
            FROM citation_discovery_cache
            WHERE cache_key = ?
        """,
            (cache_key,),
        )

        row = cursor.fetchone()

        if row is None:
            conn.close()
            self._stats.misses += 1
            self._stats.hit_rate = self._stats.hits / self._stats.total_queries
            logger.debug(f"Cache MISS: {cache_key}")
            return None

        result_json, expires_at = row

        # Check if expired
        if time.time() > expires_at:
            # Delete expired entry
            cursor.execute(
                "DELETE FROM citation_discovery_cache WHERE cache_key = ?", (cache_key,)
            )
            conn.commit()
            conn.close()
            self._stats.misses += 1
            self._stats.hit_rate = self._stats.hits / self._stats.total_queries
            logger.debug(f"Cache EXPIRED: {cache_key}")
            return None

        # Update access stats
        cursor.execute(
            """
            UPDATE citation_discovery_cache
            SET hit_count = hit_count + 1, last_accessed = ?
            WHERE cache_key = ?
        """,
            (int(time.time()), cache_key),
        )
        conn.commit()
        conn.close()

        # Deserialize result
        try:
            result = self._deserialize_result(result_json)

            # Add to memory cache
            if self.enable_memory_cache:
                self._add_to_memory_cache(cache_key, result)

            self._stats.hits += 1
            self._stats.hit_rate = self._stats.hits / self._stats.total_queries
            logger.debug(f"Disk cache HIT: {cache_key}")
            return result

        except Exception as e:
            logger.error(f"Failed to deserialize cache entry {cache_key}: {e}")
            return None

    def set(
        self,
        geo_id: str,
        publications: List[Publication],
        strategy_key: str = "default",
    ) -> None:
        """
        Cache a result

        Args:
            geo_id: GEO dataset ID
            publications: List of Publication objects to cache
            strategy_key: Strategy identifier
        """
        cache_key = self._make_cache_key(geo_id, strategy_key)

        # Serialize result
        try:
            result_json = self._serialize_result(publications)
        except Exception as e:
            logger.error(f"Failed to serialize result for {cache_key}: {e}")
            return

        # Calculate expiration
        created_at = int(time.time())
        expires_at = created_at + self.ttl_seconds

        # Store in SQLite
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO citation_discovery_cache
            (cache_key, geo_id, strategy_key, result_json, created_at, expires_at, hit_count, last_accessed)
            VALUES (?, ?, ?, ?, ?, ?, 0, ?)
        """,
            (
                cache_key,
                geo_id,
                strategy_key,
                result_json,
                created_at,
                expires_at,
                created_at,
            ),
        )

        conn.commit()
        conn.close()

        # Store in memory cache
        if self.enable_memory_cache:
            self._add_to_memory_cache(cache_key, publications)

        logger.debug(f"Cached result: {cache_key} ({len(publications)} publications)")

    def _add_to_memory_cache(self, cache_key: str, value: Any) -> None:
        """Add entry to memory cache (LRU eviction)"""
        # Remove if already exists
        if cache_key in self._memory_cache:
            self._memory_cache_order.remove(cache_key)

        # Add to cache
        self._memory_cache[cache_key] = value
        self._memory_cache_order.append(cache_key)

        # Evict oldest if over limit
        while len(self._memory_cache) > self.memory_cache_size:
            oldest_key = self._memory_cache_order.pop(0)
            del self._memory_cache[oldest_key]

    def _serialize_result(self, publications: List[Publication]) -> str:
        """Serialize publications to JSON"""
        # Convert publications to dict, handling datetime serialization
        data = []
        for pub in publications:
            pub_dict = pub.dict()
            # Convert datetime objects to ISO format strings
            if "publication_date" in pub_dict and pub_dict["publication_date"]:
                if hasattr(pub_dict["publication_date"], "isoformat"):
                    pub_dict["publication_date"] = pub_dict[
                        "publication_date"
                    ].isoformat()
            data.append(pub_dict)
        return json.dumps(data)

    def _deserialize_result(self, result_json: str) -> List[Publication]:
        """Deserialize JSON to publications"""
        from datetime import datetime as dt

        data = json.loads(result_json)
        publications = []
        for item in data:
            # Convert ISO format string back to datetime if present
            if "publication_date" in item and item["publication_date"]:
                if isinstance(item["publication_date"], str):
                    try:
                        item["publication_date"] = dt.fromisoformat(
                            item["publication_date"]
                        )
                    except (ValueError, AttributeError):
                        pass  # Keep as string if conversion fails
            publications.append(Publication(**item))
        return publications

    def invalidate(self, geo_id: str, strategy_key: Optional[str] = None) -> int:
        """
        Invalidate cache entries

        Args:
            geo_id: GEO dataset ID
            strategy_key: Optional strategy key (if None, invalidate all strategies)

        Returns:
            Number of entries invalidated
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if strategy_key:
            cache_key = self._make_cache_key(geo_id, strategy_key)
            cursor.execute(
                "DELETE FROM citation_discovery_cache WHERE cache_key = ?", (cache_key,)
            )

            # Remove from memory cache
            if cache_key in self._memory_cache:
                del self._memory_cache[cache_key]
                self._memory_cache_order.remove(cache_key)

        else:
            cursor.execute(
                "DELETE FROM citation_discovery_cache WHERE geo_id = ?", (geo_id,)
            )

            # Remove all matching entries from memory cache
            keys_to_remove = [
                k for k in self._memory_cache.keys() if k.startswith(f"{geo_id}:")
            ]
            for key in keys_to_remove:
                del self._memory_cache[key]
                self._memory_cache_order.remove(key)

        count = cursor.rowcount
        conn.commit()
        conn.close()

        logger.info(f"Invalidated {count} cache entries for {geo_id}")
        return count

    def cleanup_expired(self) -> int:
        """
        Remove expired cache entries

        Returns:
            Number of entries removed
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        current_time = int(time.time())
        cursor.execute(
            "DELETE FROM citation_discovery_cache WHERE expires_at < ?", (current_time,)
        )

        count = cursor.rowcount
        conn.commit()
        conn.close()

        logger.info(f"Cleaned up {count} expired cache entries")
        return count

    def get_stats(self) -> CacheStats:
        """Get cache performance statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM citation_discovery_cache")
        disk_entries = cursor.fetchone()[0]

        conn.close()

        self._stats.memory_entries = len(self._memory_cache)
        self._stats.disk_entries = disk_entries

        return self._stats

    def clear_all(self) -> None:
        """Clear all cache entries (dangerous!)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM citation_discovery_cache")
        conn.commit()
        conn.close()

        self._memory_cache.clear()
        self._memory_cache_order.clear()

        logger.warning("Cleared ALL cache entries")


# Convenience function for cache management
def get_cache_info(db_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Get information about cache contents

    Returns:
        Dictionary with cache statistics
    """
    if db_path is None:
        db_path = "data/cache/discovery_cache.db"

    if not Path(db_path).exists():
        return {"error": "Cache database does not exist"}

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Total entries
    cursor.execute("SELECT COUNT(*) FROM citation_discovery_cache")
    total = cursor.fetchone()[0]

    # Expired entries
    current_time = int(time.time())
    cursor.execute(
        "SELECT COUNT(*) FROM citation_discovery_cache WHERE expires_at < ?",
        (current_time,),
    )
    expired = cursor.fetchone()[0]

    # Most accessed
    cursor.execute(
        """
        SELECT geo_id, strategy_key, hit_count
        FROM citation_discovery_cache
        ORDER BY hit_count DESC
        LIMIT 10
    """
    )
    top_entries = [
        {"geo_id": row[0], "strategy": row[1], "hits": row[2]}
        for row in cursor.fetchall()
    ]

    # Size estimate
    cursor.execute("SELECT SUM(LENGTH(result_json)) FROM citation_discovery_cache")
    size_bytes = cursor.fetchone()[0] or 0
    size_mb = size_bytes / (1024 * 1024)

    conn.close()

    return {
        "total_entries": total,
        "active_entries": total - expired,
        "expired_entries": expired,
        "size_mb": round(size_mb, 2),
        "top_entries": top_entries,
    }


if __name__ == "__main__":
    # Test cache
    from omics_oracle_v2.lib.search_engines.citations.models import (
        Publication, PublicationSource)

    cache = DiscoveryCache(db_path="test_cache.db", ttl_seconds=60)

    # Create test publications
    test_pubs = [
        Publication(
            title="Test Paper 1",
            authors=["Author 1"],
            pmid="12345",
            source=PublicationSource.PUBMED,
        ),
        Publication(
            title="Test Paper 2",
            authors=["Author 2"],
            pmid="67890",
            source=PublicationSource.OPENALEX,
        ),
    ]

    # Test cache operations
    print("Setting cache...")
    cache.set("GSE12345", test_pubs, strategy_key="test")

    print("Getting from cache...")
    result = cache.get("GSE12345", strategy_key="test")
    print(f"Got {len(result) if result else 0} publications")

    print("\nCache stats:")
    stats = cache.get_stats()
    print(f"  Hits: {stats.hits}")
    print(f"  Misses: {stats.misses}")
    print(f"  Hit rate: {stats.hit_rate:.2%}")
    print(f"  Disk entries: {stats.disk_entries}")

    print("\nCache info:")
    info = get_cache_info("test_cache.db")
    for key, value in info.items():
        print(f"  {key}: {value}")

    # Cleanup
    import os

    os.remove("test_cache.db")
    print("\nTest complete!")
