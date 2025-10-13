# Week 3 Day 1: Cache Optimization Implementation Plan

## Current State Analysis

### Existing Cache Implementation
**Location:** `omics_oracle_v2/lib/infrastructure/cache/redis_cache.py`

**Current Features:**
- ✅ Basic search result caching (whole-query)
- ✅ TTL management (4 tiers: 1h, 24h, 7d, 30d)
- ✅ Metrics tracking (hits, misses, hit rate)
- ✅ Query hashing for consistent keys
- ✅ Pydantic model serialization support

**Current Performance:**
- Cache granularity: Whole-query only
- No partial result caching
- No cache warming
- No cache key compression
- No cache prioritization

## Optimization Goals

### Goal: 95%+ Cache Hit Rate on Second Run

**Current Bottlenecks:**
1. **No Partial Caching** - Even small query variations miss cache
2. **No Cache Warming** - First run always cold
3. **No Per-Item Caching** - Individual GEO datasets/publications not cached
4. **No Cache Key Optimization** - Long keys waste Redis memory

## Implementation Plan

### Phase 1: Per-Item Caching (HIGH IMPACT) ⚡
**Impact:** 10-50x speedup for partial hits
**Effort:** 2-3 hours

**Tasks:**
1. Add `get_geo_dataset()` / `set_geo_dataset()` methods
2. Add `get_publication()` / `set_publication()` methods
3. Update orchestrator to check per-item cache before search
4. Batch fetch cached items (Redis MGET)

**Example:**
```python
# Before: Cache entire search result (all or nothing)
cached = await cache.get_search_result(query, "geo")  # Miss if query slightly different

# After: Cache individual items (partial hits possible)
cached_datasets = await cache.get_geo_datasets([gse_id1, gse_id2, gse_id3])
# Returns: [GSE1 (hit), GSE2 (miss), GSE3 (hit)] - 66% hit rate!
```

### Phase 2: Cache Warming (MEDIUM IMPACT) 🔥
**Impact:** Eliminate cold starts
**Effort:** 1-2 hours

**Tasks:**
1. Add `warm_cache()` method to populate common queries
2. Pre-cache top 100 GEO datasets
3. Pre-cache common query patterns
4. Add cache warming to startup

**Strategies:**
- **Popular Datasets:** Top 100 most accessed GEO series
- **Common Queries:** "breast cancer", "alzheimer", "diabetes", etc.
- **Recent Datasets:** Last 30 days of GEO submissions

### Phase 3: Cache Key Optimization (LOW IMPACT) 💾
**Impact:** 20-30% memory savings
**Effort:** 1 hour

**Tasks:**
1. Compress cache keys using short prefixes
2. Use base64 encoding for hashes
3. Remove redundant parameters from keys

**Example:**
```python
# Before:
"omics_search:search:geo:5f4dcc3b5aa765d61d8327deb882cf99"

# After:
"os:s:g:X03hK9WqdWHYMn3riCz5mQ"  # 50% shorter
```

### Phase 4: Intelligent Cache Invalidation (MEDIUM IMPACT) ♻️
**Impact:** Higher hit rates, fresher data
**Effort:** 1-2 hours

**Tasks:**
1. Add cache tagging by query type
2. Implement partial cache invalidation
3. Add cache update strategies (refresh vs invalidate)

**Strategies:**
- **Time-based:** Different TTLs for different data types
- **Event-based:** Invalidate when new GEO datasets published
- **Usage-based:** Longer TTL for frequently accessed items

## Detailed Implementation

### 1. Per-Item Caching (Priority 1)

#### A. Add GEO Dataset Caching

```python
# redis_cache.py - Add new methods

async def get_geo_dataset(self, gse_id: str) -> Optional[Dict[str, Any]]:
    \"\"\"Get single cached GEO dataset by ID.\"\"\"
    if not self.enabled or not self.client:
        return None

    try:
        key = self._make_key("geo", "dataset", gse_id)
        result = self.client.get(key)

        if result:
            self.metrics.record_hit()
            logger.debug(f"Cache HIT for GEO dataset: {gse_id}")
            return json.loads(result)
        else:
            self.metrics.record_miss()
            return None
    except Exception as e:
        self.metrics.record_error()
        logger.error(f"Error getting cached GEO dataset {gse_id}: {e}")
        return None

async def get_geo_datasets(self, gse_ids: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
    \"\"\"
    Get multiple cached GEO datasets (batch operation).

    Returns dict mapping GSE ID -> dataset (or None if not cached)
    \"\"\"
    if not self.enabled or not self.client or not gse_ids:
        return {gse_id: None for gse_id in gse_ids}

    try:
        # Build keys
        keys = [self._make_key("geo", "dataset", gse_id) for gse_id in gse_ids]

        # Batch fetch (Redis MGET - very efficient)
        results = self.client.mget(keys)

        # Map back to GSE IDs
        cached_datasets = {}
        for gse_id, result in zip(gse_ids, results):
            if result:
                self.metrics.record_hit()
                cached_datasets[gse_id] = json.loads(result)
            else:
                self.metrics.record_miss()
                cached_datasets[gse_id] = None

        hits = sum(1 for v in cached_datasets.values() if v is not None)
        logger.debug(f"Batch fetch: {hits}/{len(gse_ids)} GEO datasets cached")

        return cached_datasets
    except Exception as e:
        self.metrics.record_error()
        logger.error(f"Error batch fetching GEO datasets: {e}")
        return {gse_id: None for gse_id in gse_ids}

async def set_geo_dataset(
    self,
    gse_id: str,
    dataset: Dict[str, Any],
    ttl: int = TTL_GEO_METADATA
) -> bool:
    \"\"\"Cache single GEO dataset.\"\"\"
    if not self.enabled or not self.client:
        return False

    try:
        key = self._make_key("geo", "dataset", gse_id)

        # Serialize dataset
        value = json.dumps(dataset)

        # Set with TTL (30 days default for GEO)
        self.client.setex(key, ttl, value)
        self.metrics.record_set()

        return True
    except Exception as e:
        self.metrics.record_error()
        logger.error(f"Error caching GEO dataset {gse_id}: {e}")
        return False
```

#### B. Update Search Orchestrator

```python
# orchestrator.py - Update _search_geo method

async def _search_geo(self, query: str, max_results: int) -> List[GEOSeriesMetadata]:
    \"\"\"Search GEO with per-item caching.\"\"\"
    if not self.geo_client:
        return []

    try:
        # Step 1: Get search results (just IDs + minimal metadata)
        logger.info(f"🔍 Searching GEO: {query}")
        search_results = await self.geo_client.search(query, max_results=max_results)

        if not search_results:
            return []

        # Step 2: Extract GEO IDs
        gse_ids = [result.geo_id for result in search_results]
        logger.info(f"📋 Found {len(gse_ids)} GEO datasets")

        # Step 3: Check cache for full metadata (batch operation)
        cached_datasets = await self.cache.get_geo_datasets(gse_ids) if self.cache else {}

        # Step 4: Identify which datasets need fetching
        cached_ids = [gse_id for gse_id, data in cached_datasets.items() if data is not None]
        missing_ids = [gse_id for gse_id in gse_ids if gse_id not in cached_ids]

        cache_hit_rate = len(cached_ids) / len(gse_ids) * 100 if gse_ids else 0
        logger.info(
            f"💾 Cache: {len(cached_ids)}/{len(gse_ids)} datasets cached "
            f"({cache_hit_rate:.1f}% hit rate)"
        )

        # Step 5: Fetch missing datasets in parallel
        full_datasets = []

        # Add cached datasets
        for gse_id in cached_ids:
            full_datasets.append(GEOSeriesMetadata(**cached_datasets[gse_id]))

        # Fetch and cache missing datasets
        if missing_ids:
            logger.info(f"⬇️  Fetching {len(missing_ids)} datasets from GEO")
            fetch_tasks = [
                self.geo_client.get_series_metadata(gse_id)
                for gse_id in missing_ids
            ]
            fetched_datasets = await asyncio.gather(*fetch_tasks, return_exceptions=True)

            # Process fetched datasets
            for gse_id, dataset in zip(missing_ids, fetched_datasets):
                if isinstance(dataset, Exception):
                    logger.warning(f"Failed to fetch {gse_id}: {dataset}")
                    continue

                if dataset:
                    full_datasets.append(dataset)

                    # Cache the fetched dataset
                    if self.cache:
                        await self.cache.set_geo_dataset(
                            gse_id,
                            dataset.dict() if hasattr(dataset, 'dict') else dataset.model_dump()
                        )

        return full_datasets

    except Exception as e:
        logger.error(f"GEO search failed: {e}")
        return []
```

### 2. Cache Warming (Priority 2)

```python
# redis_cache.py - Add cache warming

class RedisCache:
    # ... existing code ...

    async def warm_cache_popular_datasets(self, dataset_ids: List[str]) -> int:
        \"\"\"
        Warm cache with popular GEO datasets.

        Args:
            dataset_ids: List of GSE IDs to pre-cache

        Returns:
            Number of datasets successfully cached
        \"\"\"
        if not self.enabled or not dataset_ids:
            return 0

        logger.info(f"🔥 Warming cache with {len(dataset_ids)} popular datasets...")

        # Import here to avoid circular dependency
        from omics_oracle_v2.lib.search_engines.geo.client import GEOClient

        geo_client = GEOClient()
        cached_count = 0

        # Fetch and cache in batches of 10
        batch_size = 10
        for i in range(0, len(dataset_ids), batch_size):
            batch = dataset_ids[i:i + batch_size]

            # Fetch batch in parallel
            tasks = [geo_client.get_series_metadata(gse_id) for gse_id in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Cache successful fetches
            for gse_id, dataset in zip(batch, results):
                if isinstance(dataset, Exception):
                    logger.warning(f"Failed to fetch {gse_id} for cache warming: {dataset}")
                    continue

                if dataset:
                    success = await self.set_geo_dataset(
                        gse_id,
                        dataset.dict() if hasattr(dataset, 'dict') else dataset.model_dump()
                    )
                    if success:
                        cached_count += 1

            # Progress update
            if (i + batch_size) % 50 == 0:
                logger.info(f"   Progress: {min(i + batch_size, len(dataset_ids))}/{len(dataset_ids)} datasets cached")

        logger.info(f"✅ Cache warming complete: {cached_count}/{len(dataset_ids)} datasets cached")
        return cached_count

# Common dataset IDs for cache warming
POPULAR_GEO_DATASETS = [
    # Top cancer-related datasets
    "GSE68465",  # Breast cancer
    "GSE15459",  # Colorectal cancer
    "GSE39582",  # Colorectal cancer
    "GSE62254",  # Pancreatic cancer

    # Top neurological datasets
    "GSE44770",  # Alzheimer's disease
    "GSE44771",  # Alzheimer's disease
    "GSE5281",   # Alzheimer's disease
    "GSE36980",  # Parkinson's disease

    # Top immune/inflammatory datasets
    "GSE65133",  # Rheumatoid arthritis
    "GSE46750",  # Lupus
    "GSE55457",  # Inflammatory bowel disease

    # Top cardiovascular datasets
    "GSE71226",  # Heart failure
    "GSE116250", # Atrial fibrillation

    # Recent high-impact studies
    # Add top 50-100 most accessed datasets
]
```

### 3. Cache Key Optimization (Priority 3)

```python
# redis_cache.py - Optimize cache keys

def _make_key(self, *parts: str) -> str:
    \"\"\"
    Create optimized namespaced cache key.

    Uses shorter prefixes and base64 encoding for efficiency.
    \"\"\"
    # Use short prefix (3 chars instead of 12)
    prefix = "oo"  # OmicsOracle

    # Use short type codes
    TYPE_CODES = {
        "search": "s",
        "geo": "g",
        "dataset": "d",
        "publication": "p",
        "metadata": "m",
    }

    # Convert parts to short codes where possible
    short_parts = []
    for part in parts:
        if part in TYPE_CODES:
            short_parts.append(TYPE_CODES[part])
        else:
            short_parts.append(str(part))

    return f"{prefix}:" + ":".join(short_parts)

def _hash_query(self, query: str, **kwargs) -> str:
    \"\"\"
    Create optimized hash of query + parameters.

    Uses base64 encoding for shorter keys.
    \"\"\"
    import base64

    # Sort kwargs for consistent hashing
    params_str = json.dumps(kwargs, sort_keys=True)
    content = f"{query}:{params_str}"

    # Use SHA256 for better distribution, truncate to 16 bytes
    hash_bytes = hashlib.sha256(content.encode()).digest()[:16]

    # Base64 encode (URL-safe, no padding)
    return base64.urlsafe_b64encode(hash_bytes).decode().rstrip('=')
```

## Testing Plan

### Test 1: Per-Item Cache Effectiveness
```python
# Test partial cache hits
async def test_per_item_cache():
    cache = RedisCache()

    # First search: cache miss, populate cache
    result1 = await orchestrator.search("breast cancer", max_geo_results=10)
    assert len(result1.geo_datasets) == 10

    # Second search: similar query, should have partial hits
    result2 = await orchestrator.search("breast cancer gene expression", max_geo_results=10)

    # Check metrics: Should have >50% hit rate even with different query
    metrics = cache.metrics.get_summary()
    assert metrics['hit_rate'] > 50.0
```

### Test 2: Cache Warming
```python
async def test_cache_warming():
    cache = RedisCache()

    # Warm cache with popular datasets
    warmed = await cache.warm_cache_popular_datasets(POPULAR_GEO_DATASETS[:20])
    assert warmed >= 15  # At least 75% success rate

    # Search should now hit cache
    result = await orchestrator.search("breast cancer", max_geo_results=5)

    # All results should be from cache
    metrics = cache.metrics.get_summary()
    assert metrics['hit_rate'] == 100.0
```

## Success Metrics

### Targets
- ✅ **Cache Hit Rate:** 95%+ on second run
- ✅ **Per-Item Hits:** 70%+ on similar queries
- ✅ **Cache Warming:** <30 seconds for top 100 datasets
- ✅ **Memory Efficiency:** 20-30% reduction in Redis memory usage
- ✅ **Query Speed:** 10-50x faster on partial cache hits

### Monitoring
```python
# Add to orchestrator.py close() method
def log_cache_stats(self):
    if self.cache:
        self.cache.metrics.log_summary()

        # Log detailed breakdown
        logger.info("Cache Performance Breakdown:")
        logger.info(f"  - Whole-query hits: {whole_query_hits}")
        logger.info(f"  - Per-item hits: {per_item_hits}")
        logger.info(f"  - Cache warming hits: {warming_hits}")
```

## Implementation Order

1. **Hour 1-2:** Implement per-item GEO dataset caching
2. **Hour 3:** Update orchestrator to use per-item cache
3. **Hour 4:** Test and validate per-item caching
4. **Hour 5-6:** Implement cache warming
5. **Hour 7:** Implement cache key optimization
6. **Hour 8:** Testing, validation, documentation

## Files to Modify

1. `omics_oracle_v2/lib/infrastructure/cache/redis_cache.py`
   - Add get/set_geo_dataset methods
   - Add get/set_publication methods
   - Add cache warming methods
   - Optimize key generation

2. `omics_oracle_v2/lib/search_orchestration/orchestrator.py`
   - Update _search_geo to use per-item cache
   - Update _search_publications to use per-item cache
   - Add cache stats logging

3. `tests/lib/cache/test_per_item_caching.py` (new)
   - Test per-item caching
   - Test cache warming
   - Test optimization

## Expected Impact

**Before Optimization:**
- First run: 0% cache hit rate (20 sec search)
- Second run: 100% hit rate on exact same query (0.1 sec)
- Similar query: 0% hit rate (20 sec search)

**After Optimization:**
- First run: 0% cache hit rate (20 sec search)
- Second run: 100% hit rate (0.1 sec)
- Similar query: **70-95% partial hit rate** (2-6 sec search) ⚡

**ROI:** 3-10x faster for common research workflows where users explore related queries.
