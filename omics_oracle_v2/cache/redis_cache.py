"""
Redis Cache for OmicsOracle Unified Pipeline

CORE COMPONENT: Caching layer for performance and rate limiting.

Features:
- Search result caching
- Metadata caching
- Publication caching
- TTL management
- Cache invalidation

Benefits:
- Avoid redundant API calls
- Respect rate limits
- Faster response times
- Reduced load on external services
"""

import hashlib
import json
import logging
from typing import Any, Dict, Optional

try:
    import redis
    from redis import Redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logging.warning("Redis not available - caching will be disabled")

logger = logging.getLogger(__name__)


class CacheMetrics:
    """Track cache performance metrics."""

    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.sets = 0
        self.errors = 0
        self.total_requests = 0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        if self.total_requests == 0:
            return 0.0
        return (self.hits / self.total_requests) * 100

    def record_hit(self):
        """Record a cache hit."""
        self.hits += 1
        self.total_requests += 1

    def record_miss(self):
        """Record a cache miss."""
        self.misses += 1
        self.total_requests += 1

    def record_set(self):
        """Record a cache set operation."""
        self.sets += 1

    def record_error(self):
        """Record a cache error."""
        self.errors += 1

    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary."""
        return {
            "total_requests": self.total_requests,
            "hits": self.hits,
            "misses": self.misses,
            "sets": self.sets,
            "errors": self.errors,
            "hit_rate": f"{self.hit_rate:.1f}%",
        }

    def log_summary(self):
        """Log cache metrics summary."""
        if self.total_requests > 0:
            logger.info(
                f"Cache Metrics: {self.hits} hits, {self.misses} misses "
                f"({self.hit_rate:.1f}% hit rate), {self.sets} sets, {self.errors} errors"
            )


class RedisCache:
    """
    Redis-based caching for OmicsOracle search results and metadata.

    CORE COMPONENT - Improves performance and respects rate limits.

    Cache hierarchy:
    - Search results: 24 hours (frequent queries)
    - Publication metadata: 7 days (stable data)
    - GEO metadata: 30 days (very stable)
    - Deduplication hashes: 1 hour (temporary)
    """

    # Default TTLs (in seconds)
    TTL_SEARCH_RESULTS = 86400  # 24 hours
    TTL_PUBLICATION = 604800  # 7 days
    TTL_GEO_METADATA = 2592000  # 30 days
    TTL_DEDUP_HASH = 3600  # 1 hour
    TTL_QUERY_OPTIMIZATION = 86400  # 24 hours

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        prefix: str = "omics_search",
        default_ttl: int = 86400,
        enabled: bool = True,
    ):
        """
        Initialize Redis cache.

        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            prefix: Key prefix for namespacing
            default_ttl: Default TTL in seconds
            enabled: Enable/disable caching
        """
        self.host = host
        self.port = port
        self.db = db
        self.prefix = prefix
        self.default_ttl = default_ttl
        self.enabled = enabled and REDIS_AVAILABLE

        self.client: Optional[Redis] = None
        self.metrics = CacheMetrics()  # Add metrics tracking

        if self.enabled:
            self._connect()
        else:
            logger.warning("Redis cache is disabled")

    def _connect(self):
        """Connect to Redis server."""
        try:
            self.client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            # Test connection
            self.client.ping()
            logger.info(f"Connected to Redis at {self.host}:{self.port} (db={self.db})")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.enabled = False
            self.client = None

    def _make_key(self, *parts: str) -> str:
        """
        Create namespaced cache key.

        Args:
            *parts: Key components

        Returns:
            Formatted key with prefix
        """
        return f"{self.prefix}:" + ":".join(str(p) for p in parts)

    def _hash_query(self, query: str, **kwargs) -> str:
        """
        Create hash of query + parameters for cache key.

        Args:
            query: Query string
            **kwargs: Additional parameters

        Returns:
            MD5 hash of query + params
        """
        # Sort kwargs for consistent hashing
        params_str = json.dumps(kwargs, sort_keys=True)
        content = f"{query}:{params_str}"
        return hashlib.md5(content.encode()).hexdigest()

    async def get_search_result(
        self, query: str, search_type: str, **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached search result.

        Args:
            query: Search query
            search_type: Type of search (geo, publications, etc.)
            **kwargs: Additional search parameters

        Returns:
            Cached result or None
        """
        if not self.enabled or not self.client:
            return None

        try:
            query_hash = self._hash_query(query, search_type=search_type, **kwargs)
            key = self._make_key("search", search_type, query_hash)

            result = self.client.get(key)
            if result:
                self.metrics.record_hit()  # Track cache hit
                logger.info(f"[HIT] Redis cache HIT for query: {query[:50]}")
                return json.loads(result)
            else:
                self.metrics.record_miss()  # Track cache miss
                logger.info(f"[MISS] Redis cache MISS for query: {query[:50]}")
                return None
        except Exception as e:
            self.metrics.record_error()  # Track error
            logger.error(f"Error getting cached search result: {e}")
            return None

    async def set_search_result(
        self,
        query: str,
        search_type: str,
        result: Any,
        ttl: Optional[int] = None,
        **kwargs,
    ) -> bool:
        """
        Cache search result.

        Args:
            query: Search query
            search_type: Type of search
            result: Search result to cache
            ttl: Time to live in seconds (default: TTL_SEARCH_RESULTS)
            **kwargs: Additional search parameters

        Returns:
            True if cached successfully
        """
        if not self.enabled or not self.client:
            return False

        try:
            query_hash = self._hash_query(query, search_type=search_type, **kwargs)
            key = self._make_key("search", search_type, query_hash)

            # Convert result to JSON
            # Priority: model_dump() (Pydantic v2) > to_dict() > dict() (Pydantic v1) > __dict__
            if hasattr(result, "model_dump"):
                result_dict = result.model_dump(mode="json")
            elif hasattr(result, "to_dict"):
                result_dict = result.to_dict()
            elif hasattr(result, "dict"):
                result_dict = result.dict()
            elif hasattr(result, "__dict__"):
                result_dict = result.__dict__
            else:
                result_dict = result

            result_json = json.dumps(
                result_dict, default=str
            )  # Use default=str for datetime objects

            # Set with TTL
            ttl = ttl or self.TTL_SEARCH_RESULTS
            self.client.setex(key, ttl, result_json)

            self.metrics.record_set()  # Track cache set
            logger.debug(f"Cached search result for query: {query[:50]} (TTL={ttl}s)")
            return True
        except Exception as e:
            self.metrics.record_error()  # Track error
            logger.error(f"Error caching search result: {e}")
            return False

    async def get_publication(self, pmid: str) -> Optional[Dict[str, Any]]:
        """
        Get cached publication metadata.

        Args:
            pmid: PubMed ID

        Returns:
            Cached publication or None
        """
        if not self.enabled or not self.client:
            return None

        try:
            key = self._make_key("publication", pmid)
            result = self.client.get(key)

            if result:
                logger.debug(f"Cache HIT for PMID: {pmid}")
                return json.loads(result)
            else:
                return None
        except Exception as e:
            logger.error(f"Error getting cached publication: {e}")
            return None

    async def set_publication(
        self,
        pmid: str,
        publication: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Cache publication metadata.

        Args:
            pmid: PubMed ID
            publication: Publication object
            ttl: Time to live in seconds

        Returns:
            True if cached successfully
        """
        if not self.enabled or not self.client:
            return False

        try:
            key = self._make_key("publication", pmid)

            # Convert to JSON
            if hasattr(publication, "to_dict"):
                pub_dict = publication.to_dict()
            elif hasattr(publication, "__dict__"):
                pub_dict = publication.__dict__
            else:
                pub_dict = publication

            pub_json = json.dumps(pub_dict)

            # Set with TTL
            ttl = ttl or self.TTL_PUBLICATION
            self.client.setex(key, ttl, pub_json)

            logger.debug(f"Cached publication: {pmid} (TTL={ttl}s)")
            return True
        except Exception as e:
            logger.error(f"Error caching publication: {e}")
            return False

    async def get_geo_metadata(self, geo_id: str) -> Optional[Dict[str, Any]]:
        """
        Get cached GEO metadata.

        Args:
            geo_id: GEO accession (GSE, GPL, etc.)

        Returns:
            Cached metadata or None
        """
        if not self.enabled or not self.client:
            return None

        try:
            key = self._make_key("geo", geo_id.upper())
            result = self.client.get(key)

            if result:
                logger.debug(f"Cache HIT for GEO: {geo_id}")
                return json.loads(result)
            else:
                return None
        except Exception as e:
            logger.error(f"Error getting cached GEO metadata: {e}")
            return None

    async def set_geo_metadata(
        self,
        geo_id: str,
        metadata: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Cache GEO metadata.

        Args:
            geo_id: GEO accession
            metadata: Metadata object
            ttl: Time to live in seconds

        Returns:
            True if cached successfully
        """
        if not self.enabled or not self.client:
            return False

        try:
            key = self._make_key("geo", geo_id.upper())

            # Convert to JSON-serializable dict
            if hasattr(metadata, "model_dump"):
                # Pydantic v2
                meta_dict = metadata.model_dump(mode="json")
            elif hasattr(metadata, "dict"):
                # Pydantic v1
                meta_dict = metadata.dict()
            elif hasattr(metadata, "to_dict"):
                meta_dict = metadata.to_dict()
            elif hasattr(metadata, "__dict__"):
                meta_dict = metadata.__dict__
            else:
                meta_dict = metadata

            meta_json = json.dumps(
                meta_dict, default=str
            )  # Use default=str for datetime objects

            # Set with TTL
            ttl = ttl or self.TTL_GEO_METADATA
            self.client.setex(key, ttl, meta_json)

            logger.debug(f"Cached GEO metadata: {geo_id} (TTL={ttl}s)")
            return True
        except Exception as e:
            logger.error(f"Error caching GEO metadata: {e}")
            return False

    async def get_geo_datasets_batch(
        self, geo_ids: list[str]
    ) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Get multiple cached GEO datasets (batch operation for efficiency).

        This is a key optimization - uses Redis MGET for atomic batch fetch.

        Args:
            geo_ids: List of GEO accessions to fetch

        Returns:
            Dict mapping GSE ID -> dataset (None if not cached)
        """
        if not self.enabled or not self.client or not geo_ids:
            return {geo_id: None for geo_id in geo_ids}

        try:
            # Build keys
            normalized_ids = [geo_id.upper() for geo_id in geo_ids]
            keys = [self._make_key("geo", geo_id) for geo_id in normalized_ids]

            # Batch fetch (Redis MGET - very efficient, single round trip)
            results = self.client.mget(keys)

            # Map back to GSE IDs
            cached_datasets = {}
            hits = 0
            for geo_id, result in zip(geo_ids, results):
                if result:
                    self.metrics.record_hit()
                    cached_datasets[geo_id] = json.loads(result)
                    hits += 1
                else:
                    self.metrics.record_miss()
                    cached_datasets[geo_id] = None

            hit_rate = (hits / len(geo_ids) * 100) if geo_ids else 0
            logger.debug(
                f"Batch fetch: {hits}/{len(geo_ids)} GEO datasets cached ({hit_rate:.1f}% hit rate)"
            )

            return cached_datasets
        except Exception as e:
            self.metrics.record_error()
            logger.error(f"Error batch fetching GEO datasets: {e}")
            return {geo_id: None for geo_id in geo_ids}

    async def set_geo_datasets_batch(
        self,
        datasets: Dict[str, Any],
        ttl: Optional[int] = None,
    ) -> int:
        """
        Cache multiple GEO datasets (batch operation).

        Args:
            datasets: Dict mapping GSE ID -> dataset dict
            ttl: Time to live in seconds

        Returns:
            Number of datasets successfully cached
        """
        if not self.enabled or not self.client or not datasets:
            return 0

        try:
            ttl = ttl or self.TTL_GEO_METADATA
            cached_count = 0

            # Use pipeline for efficiency (batches commands)
            pipe = self.client.pipeline()

            for geo_id, dataset in datasets.items():
                try:
                    key = self._make_key("geo", geo_id.upper())

                    # Convert to JSON
                    if hasattr(dataset, "model_dump"):
                        dataset_dict = dataset.model_dump()
                    elif hasattr(dataset, "to_dict"):
                        dataset_dict = dataset.to_dict()
                    elif hasattr(dataset, "dict"):
                        dataset_dict = dataset.dict()
                    elif hasattr(dataset, "__dict__"):
                        dataset_dict = dataset.__dict__
                    else:
                        dataset_dict = dataset

                    dataset_json = json.dumps(dataset_dict)

                    # Add to pipeline
                    pipe.setex(key, ttl, dataset_json)
                    self.metrics.record_set()
                    cached_count += 1
                except Exception as e:
                    logger.warning(f"Failed to serialize dataset {geo_id}: {e}")
                    continue

            # Execute pipeline (single round trip to Redis)
            pipe.execute()

            logger.debug(f"Batch cached {cached_count} GEO datasets (TTL={ttl}s)")
            return cached_count
        except Exception as e:
            self.metrics.record_error()
            logger.error(f"Error batch caching GEO datasets: {e}")
            return 0

    async def get_optimized_query(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Get cached query optimization result.

        Args:
            query: Original query

        Returns:
            Cached optimization or None
        """
        if not self.enabled or not self.client:
            return None

        try:
            query_hash = hashlib.md5(query.encode()).hexdigest()
            key = self._make_key("query_opt", query_hash)

            result = self.client.get(key)
            if result:
                logger.debug(f"Cache HIT for query optimization: {query[:50]}")
                return json.loads(result)
            else:
                return None
        except Exception as e:
            logger.error(f"Error getting cached query optimization: {e}")
            return None

    async def set_optimized_query(
        self,
        query: str,
        optimization: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Cache query optimization result.

        Args:
            query: Original query
            optimization: OptimizedQuery object
            ttl: Time to live in seconds

        Returns:
            True if cached successfully
        """
        if not self.enabled or not self.client:
            return False

        try:
            query_hash = hashlib.md5(query.encode()).hexdigest()
            key = self._make_key("query_opt", query_hash)

            # Convert to JSON
            if hasattr(optimization, "to_dict"):
                opt_dict = optimization.to_dict()
            else:
                opt_dict = optimization

            opt_json = json.dumps(opt_dict)

            # Set with TTL
            ttl = ttl or self.TTL_QUERY_OPTIMIZATION
            self.client.setex(key, ttl, opt_json)

            logger.debug(f"Cached query optimization: {query[:50]} (TTL={ttl}s)")
            return True
        except Exception as e:
            logger.error(f"Error caching query optimization: {e}")
            return False

    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all keys matching pattern.

        Args:
            pattern: Key pattern (e.g., "search:*")

        Returns:
            Number of keys deleted
        """
        if not self.enabled or not self.client:
            return 0

        try:
            full_pattern = self._make_key(pattern)
            keys = self.client.keys(full_pattern)

            if keys:
                deleted = self.client.delete(*keys)
                logger.info(f"Invalidated {deleted} keys matching: {pattern}")
                return deleted
            else:
                return 0
        except Exception as e:
            logger.error(f"Error invalidating cache pattern: {e}")
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        if not self.enabled or not self.client:
            return {"enabled": False}

        try:
            info = self.client.info("stats")

            # Count keys by prefix
            key_counts = {}
            for key_type in ["search", "publication", "geo", "query_opt"]:
                pattern = self._make_key(key_type, "*")
                count = len(self.client.keys(pattern))
                key_counts[key_type] = count

            return {
                "enabled": True,
                "connected": True,
                "total_keys": info.get("db0", {}).get("keys", 0),
                "key_counts": key_counts,
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(
                    info.get("keyspace_hits", 0), info.get("keyspace_misses", 0)
                ),
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"enabled": True, "connected": False, "error": str(e)}

    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        """Calculate cache hit rate percentage."""
        total = hits + misses
        if total == 0:
            return 0.0
        return (hits / total) * 100

    async def get(self, key: str) -> Optional[Any]:
        """
        Generic get method for any cached data.

        Args:
            key: Cache key (will be prefixed automatically)

        Returns:
            Cached value (parsed from JSON) or None
        """
        if not self.enabled or not self.client:
            return None

        try:
            result = self.client.get(key)
            if result:
                self.metrics.record_hit()
                return json.loads(result)
            else:
                self.metrics.record_miss()
                return None
        except Exception as e:
            self.metrics.record_error()
            logger.error(f"Error getting cached value for key {key}: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Generic set method for caching any data.

        Args:
            key: Cache key (will be prefixed automatically)
            value: Value to cache (will be JSON serialized)
            ttl: Time to live in seconds (default: self.default_ttl)

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.client:
            return False

        try:
            # Serialize value to JSON
            value_json = json.dumps(value, default=str)

            # Set with TTL
            ttl = ttl or self.default_ttl
            self.client.setex(key, ttl, value_json)

            self.metrics.record_set()
            logger.debug(f"Cached value for key: {key} (TTL={ttl}s)")
            return True
        except Exception as e:
            self.metrics.record_error()
            logger.error(f"Error caching value for key {key}: {e}")
            return False

    def close(self):
        """Close Redis connection."""
        if self.client:
            self.client.close()
            logger.info("Redis connection closed")


# Example usage and tests
if __name__ == "__main__":
    import asyncio

    logging.basicConfig(level=logging.DEBUG)

    async def test_cache():
        cache = RedisCache(
            host="localhost",
            port=6379,
            db=0,
            prefix="test_omics",
            enabled=True,
        )

        # Test search result caching
        print("\n=== Testing Search Result Cache ===")
        query = "alzheimer's disease"
        result = {"publications": [{"pmid": "12345", "title": "Test"}]}

        # Set
        success = await cache.set_search_result(query, "publications", result)
        print(f"Set result: {success}")

        # Get
        cached = await cache.get_search_result(query, "publications")
        print(f"Got result: {cached}")

        # Test publication caching
        print("\n=== Testing Publication Cache ===")
        pub = {"pmid": "12345", "title": "Test Publication"}
        success = await cache.set_publication("12345", pub)
        print(f"Set publication: {success}")

        cached_pub = await cache.get_publication("12345")
        print(f"Got publication: {cached_pub}")

        # Stats
        print("\n=== Cache Statistics ===")
        stats = cache.get_stats()
        for key, value in stats.items():
            print(f"{key}: {value}")

        # Cleanup
        cache.invalidate_pattern("*")
        cache.close()

    asyncio.run(test_cache())
