# Cache Architecture Audit & Consolidation Plan
**Date**: October 15, 2025  
**Status**: AUDIT COMPLETE - READY FOR CONSOLIDATION  
**Objective**: Eliminate redundant cache layers and standardize on unified hybrid approach

---

## Executive Summary

**FINDING**: System has **6 different cache mechanisms** operating independently, causing:
- ❌ Cache inconsistency (organism bug - GSE189158)
- ❌ Debugging nightmares (cleared one cache, data persists in another)
- ❌ Performance overhead (multiple I/O operations)
- ❌ Code complexity (developers confused about which cache to use)

**RECOMMENDATION**: Consolidate to **2-tier hybrid architecture**:
1. **Hot Tier**: Redis (fast, volatile, TTL-managed)
2. **Warm Tier**: SQLite + File Storage (persistent, queryable)

**IMPACT**: 
- ✅ Single source of truth for cached data
- ✅ Consistent cache invalidation
- ✅ Faster debugging (check one place, not six)
- ✅ Reduced storage footprint (~40% reduction)

---

## Current Cache Inventory

### 1. RedisCache (HOT TIER - Keep ✅)
**File**: `omics_oracle_v2/lib/infrastructure/cache/redis_cache.py`  
**Purpose**: Fast in-memory caching for search results, metadata, publications  
**Storage**: Redis server (localhost:6379)  
**TTL**: 24h (search), 7d (publications), 30d (GEO)  
**Size**: ~50-100MB  
**Usage**: 
- Search orchestrator (primary user)
- API response caching
- Rate limiting support

**Verdict**: **KEEP** - This is our hot tier, handles high-frequency requests perfectly.

**Features**:
- Batch operations (MGET, pipeline)
- Metrics tracking (hit rate, misses)
- Pattern-based invalidation
- Async support

---

### 2. SimpleCache (DUPLICATE - Remove ❌)
**File**: `omics_oracle_v2/lib/search_engines/geo/cache.py`  
**Purpose**: File-based JSON cache for GEO metadata  
**Storage**: `data/cache/{md5_hash}.json`  
**TTL**: 3600s (1 hour) default  
**Size**: ~200-500MB  
**Usage**: GEO client only

**Verdict**: **REMOVE** - Duplicates RedisCache functionality for GEO data.

**Problems**:
- MD5 hashing makes debugging impossible (can't find GSE189158 cache file)
- Short TTL causes frequent re-fetching
- No metrics or visibility
- Not queryable (must scan all files)

**Migration Path**: 
```python
# OLD (SimpleCache)
cached = self.cache.get(f"geo:{geo_id}")
self.cache.set(f"geo:{geo_id}", data)

# NEW (RedisCache)
cached = await self.redis_cache.get_geo_metadata(geo_id)
await self.redis_cache.set_geo_metadata(geo_id, data)
```

---

### 3. ParsedCache (WARM TIER - Keep ✅)
**File**: `omics_oracle_v2/lib/pipelines/text_enrichment/parsed_cache.py`  
**Purpose**: Persistent storage for parsed PDF/XML content  
**Storage**: `data/fulltext/parsed/{publication_id}.json.gz`  
**TTL**: 90 days  
**Size**: ~2-5GB  
**Usage**: PDF parser, AI Analysis

**Verdict**: **KEEP** - Essential warm tier for expensive parsing operations.

**Features**:
- Compression (80% space savings)
- Long TTL (parsing is expensive)
- Human-readable format (debugging friendly)
- Normalizer integration

**Enhancement Needed**:
- Integrate with FullTextCacheDB for metadata indexing
- Add Redis hot-tier for frequently accessed papers

---

### 4. SmartCache (COORDINATOR - Keep ✅)
**File**: `omics_oracle_v2/lib/pipelines/pdf_download/smart_cache.py`  
**Purpose**: Multi-location file finder (not a cache, a coordinator)  
**Storage**: None (scans multiple directories)  
**TTL**: N/A  
**Size**: 0 bytes  
**Usage**: Finds PDFs/XMLs across source-specific directories

**Verdict**: **KEEP** - Not a cache layer, it's a smart file locator.

**Features**:
- Searches XML and PDF directories by source
- Priority-based search (XML > institutional PDF > arXiv PDF)
- Legacy hash-based fallback

**Enhancement Needed**:
- Query FullTextCacheDB first before filesystem scan
- Add Redis layer for "file existence" lookups

---

### 5. FullTextCacheDB (WARM TIER - Keep ✅)
**File**: `omics_oracle_v2/lib/pipelines/text_enrichment/cache_db.py`  
**Purpose**: SQLite metadata index for parsed content  
**Storage**: `data/fulltext/cache_metadata.db`  
**TTL**: None (permanent until deleted)  
**Size**: ~50-100MB  
**Usage**: Fast queries, deduplication, analytics

**Verdict**: **KEEP** - Critical for sub-millisecond queries and analytics.

**Features**:
- Fast indexed queries (<1ms)
- Deduplication via SHA256 hashing
- Analytics (papers with tables, quality scores)
- Usage tracking

**Enhancement Needed**:
- Auto-sync with ParsedCache (currently manual)
- Add foreign key to UnifiedDB geo_datasets table

---

### 6. GEOparse Cache (EXTERNAL - Keep but Hide ✅)
**File**: N/A (managed by GEOparse library)  
**Purpose**: NCBI SOFT file caching  
**Storage**: `data/cache/GSE{id}_family.soft.gz`  
**TTL**: None (permanent)  
**Size**: ~1-2GB  
**Usage**: GEOparse library downloads

**Verdict**: **KEEP** - External dependency, but hide from developers.

**Problems**:
- No TTL (stale data persists forever)
- Developers don't know it exists
- No invalidation API

**Enhancement Needed**:
- Document its existence
- Add utility to clear stale SOFT files (>90 days)
- Wrap GEOparse calls to check Redis first

---

## Redundancy Matrix

| Data Type | RedisCache | SimpleCache | ParsedCache | FullTextCacheDB | GEOparse | Total Copies |
|-----------|-----------|-------------|-------------|-----------------|----------|--------------|
| **GEO Metadata** | ✅ 30d | ✅ 1h | ❌ | ❌ | ✅ ∞ | **3 copies!** ❌ |
| **Search Results** | ✅ 24h | ❌ | ❌ | ❌ | ❌ | 1 copy ✅ |
| **Parsed Content** | ❌ | ❌ | ✅ 90d | ✅ ∞ | ❌ | 2 copies ✅ |
| **Publications** | ✅ 7d | ❌ | ❌ | ❌ | ❌ | 1 copy ✅ |

**CRITICAL ISSUE**: GEO metadata stored in **3 different places**!
- RedisCache: `omics_search:geo:GSE189158`
- SimpleCache: `data/cache/{md5}.json`
- GEOparse: `data/cache/GSE189158_family.soft.gz`

This explains the GSE189158 organism bug - we cleared Redis and SimpleCache, but GEOparse still had stale SOFT file with empty organism!

---

## Proposed Architecture

### Tier 1: Hot Cache (Redis)
**Purpose**: Sub-10ms response for high-frequency requests  
**TTL**: 1h - 30d based on stability  
**Data**:
- Search results (24h)
- GEO metadata (30d)
- Publications (7d)
- Query optimizations (24h)
- File existence checks (1h) ← NEW

**Operations**:
```python
# Batch operations for efficiency
datasets = await redis_cache.get_geo_datasets_batch(geo_ids)
await redis_cache.set_geo_datasets_batch(datasets, ttl=2592000)

# Pattern invalidation
redis_cache.invalidate_pattern("geo:GSE*")  # Clear all GEO data
```

---

### Tier 2: Warm Cache (SQLite + Files)
**Purpose**: Persistent storage for expensive operations  
**TTL**: 90d (auto-cleanup of stale entries)  
**Data**:
- Parsed content (ParsedCache) → JSON.gz files
- Content metadata (FullTextCacheDB) → SQLite index
- PDF/XML files (SmartCache coordinator) → Source-organized directories

**Operations**:
```python
# Save parsed content (auto-indexes to FullTextCacheDB)
await parsed_cache.save(
    publication_id="PMC123",
    content=parsed_data,
    source_file="data/fulltext/pdf/pmc/PMC123.pdf"
)

# Fast queries via SQLite
papers = cache_db.find_papers_with_tables(min_tables=3, min_quality=0.9)
```

---

### Tier 3: Cold Storage (External Libraries)
**Purpose**: Raw data from external APIs (hidden from developers)  
**TTL**: Managed externally  
**Data**:
- GEOparse SOFT files
- Browser cache (static assets)

**Operations**:
```python
# Developers NEVER interact directly
# Wrapped by GEO client with Redis hot-tier check
```

---

## Consolidation Plan

### Phase 1: Remove SimpleCache (1-2 hours)
**Files to Modify**:
1. `omics_oracle_v2/lib/search_engines/geo/client.py`
   - Remove `from .cache import SimpleCache`
   - Replace `self.cache = SimpleCache(...)` with `self.redis_cache = RedisCache(...)`
   - Update all `self.cache.get/set` calls to `await self.redis_cache.get_geo_metadata/set_geo_metadata`

2. `omics_oracle_v2/lib/search_engines/geo/cache.py`
   - **DELETE FILE** (move to archive)

**Testing**:
```bash
# Clear all caches
redis-cli FLUSHALL
rm -rf data/cache/*.json

# Test GEO search
curl -X POST http://localhost:8000/api/agents/search \
  -H "Content-Type: application/json" \
  -d '{"search_terms": ["GSE189158"], "max_results": 1}'

# Verify Redis keys created
redis-cli KEYS "omics_search:geo:*"

# Should show: omics_search:geo:GSE189158
```

**Expected Impact**:
- ✅ Single cache location for GEO metadata
- ✅ Longer TTL (30d vs 1h) → fewer API calls
- ✅ Batch operations → faster multi-dataset searches
- ✅ Metrics tracking → visibility into cache performance

---

### Phase 2: GEOparse Cache Wrapper (2-3 hours)
**Goal**: Check Redis before downloading SOFT files

**New File**: `omics_oracle_v2/lib/search_engines/geo/geoparse_wrapper.py`
```python
"""
Redis-aware GEOparse wrapper.

Checks Redis hot cache before downloading SOFT files.
Dramatically reduces NCBI API calls and speeds up queries.
"""

async def get_gse_with_cache(geo_id: str, redis_cache: RedisCache) -> GEOparse.GSE:
    """
    Get GSE object with Redis hot-tier caching.
    
    Cache layers:
    1. Redis (30d TTL) ← Check here first
    2. GEOparse disk cache (∞ TTL) ← Only if Redis miss
    3. NCBI FTP download ← Last resort
    """
    # Check Redis first
    cached = await redis_cache.get_geo_metadata(geo_id)
    if cached:
        # Reconstruct GSE from cached metadata (lightweight)
        return create_gse_from_metadata(cached)
    
    # Download via GEOparse (expensive)
    gse = GEOparse.get_GEO(geo=geo_id, destdir="data/cache")
    
    # Extract and cache metadata
    metadata = extract_metadata_from_gse(gse)
    await redis_cache.set_geo_metadata(geo_id, metadata, ttl=2592000)
    
    return gse
```

**Modify**: `omics_oracle_v2/lib/search_engines/geo/client.py`
```python
# OLD
gse = GEOparse.get_GEO(geo=geo_id, destdir=self.settings.cache_dir)

# NEW
gse = await get_gse_with_cache(geo_id, self.redis_cache)
```

**Testing**:
```bash
# First request (NCBI download)
time curl -X POST .../search -d '{"search_terms": ["GSE50081"]}'
# Expected: ~2-5 seconds

# Second request (Redis cache hit)
time curl -X POST .../search -d '{"search_terms": ["GSE50081"]}'
# Expected: ~50-100ms (40-100x faster!)
```

---

### Phase 3: ParsedCache + FullTextCacheDB Integration (2-3 hours)
**Goal**: Auto-sync file cache with database index

**Modify**: `omics_oracle_v2/lib/pipelines/text_enrichment/parsed_cache.py`
```python
async def save(self, publication_id, content, **kwargs):
    # ... existing save logic ...
    
    # NEW: Auto-sync to database (currently manual)
    try:
        db = get_cache_db()
        db.add_entry(
            publication_id=publication_id,
            file_path=str(cache_file),
            file_type=source_type,
            table_count=len(content.get("tables", [])),
            quality_score=quality_score,
            # ... all metadata fields ...
        )
    except Exception as e:
        logger.warning(f"Database sync failed (non-critical): {e}")
```

**Modify**: `omics_oracle_v2/lib/pipelines/pdf_download/smart_cache.py`
```python
def find_local_file(self, publication):
    # NEW: Check database index FIRST (sub-millisecond)
    db = get_cache_db()
    db_entry = db.get_entry(publication.id)
    
    if db_entry and Path(db_entry['file_path']).exists():
        return LocalFileResult(
            found=True,
            file_path=Path(db_entry['file_path']),
            file_type=db_entry['file_type'],
            source=db_entry['file_source'],
            size_bytes=db_entry['file_size_bytes']
        )
    
    # FALLBACK: Filesystem scan (slower but handles edge cases)
    return self._check_xml_files(...) or self._check_pdf_files(...)
```

**Expected Impact**:
- ✅ Database always in sync with files
- ✅ Sub-millisecond file lookups (no filesystem scan)
- ✅ Analytics queries work immediately after download

---

### Phase 4: Add Redis Hot-Tier for Parsed Content (3-4 hours)
**Goal**: Cache frequently accessed parsed content in Redis

**Modify**: `omics_oracle_v2/lib/infrastructure/cache/redis_cache.py`
```python
async def get_parsed_content(self, publication_id: str) -> Optional[Dict]:
    """Get parsed content from Redis (hot tier)."""
    key = self._make_key("parsed", publication_id)
    result = self.client.get(key)
    
    if result:
        self.metrics.record_hit()
        logger.debug(f"Redis hit for parsed content: {publication_id}")
        return json.loads(result)
    
    self.metrics.record_miss()
    return None

async def set_parsed_content(self, publication_id: str, content: Dict, ttl: int = 3600):
    """Cache parsed content in Redis (1h TTL by default)."""
    key = self._make_key("parsed", publication_id)
    
    # Only cache content summary (not full text to save memory)
    summary = {
        "tables": content.get("tables", []),
        "figures": content.get("figures", []),
        "sections": {k: v[:500] for k, v in content.get("sections", {}).items()},  # Truncate
        "metadata": content.get("metadata", {})
    }
    
    self.client.setex(key, ttl, json.dumps(summary))
    self.metrics.record_set()
```

**Modify**: `omics_oracle_v2/lib/pipelines/text_enrichment/parsed_cache.py`
```python
async def get(self, publication_id: str):
    # NEW: Check Redis hot-tier first
    if hasattr(self, 'redis_cache'):
        cached = await self.redis_cache.get_parsed_content(publication_id)
        if cached:
            logger.info(f"Redis hot-tier hit: {publication_id}")
            return cached
    
    # FALLBACK: Load from disk (warm tier)
    content = ... # existing disk load logic
    
    # NEW: Populate Redis for next time
    if content and hasattr(self, 'redis_cache'):
        await self.redis_cache.set_parsed_content(publication_id, content)
    
    return content
```

**Expected Impact**:
- ✅ AI Analysis requests 10-50x faster for recently analyzed papers
- ✅ Reduced disk I/O for popular papers
- ✅ Automatic eviction (1h TTL) keeps memory usage controlled

---

### Phase 5: Cache Invalidation Utility (1 hour)
**New File**: `scripts/utilities/clear_all_caches.py`
```python
"""
Master cache clearing utility.

Clears ALL cache layers in correct order.
Use this for debugging cache issues.
"""

import asyncio
from pathlib import Path
import redis
import sqlite3

async def clear_all_caches():
    """Clear all cache layers."""
    
    # 1. Redis (hot tier)
    print("Clearing Redis cache...")
    r = redis.Redis(host='localhost', port=6379, db=0)
    r.flushall()
    print(f"  ✓ Deleted all Redis keys")
    
    # 2. SimpleCache (being removed)
    print("Clearing SimpleCache files...")
    cache_dir = Path("data/cache")
    json_files = list(cache_dir.glob("*.json"))
    for f in json_files:
        f.unlink()
    print(f"  ✓ Deleted {len(json_files)} JSON cache files")
    
    # 3. GEOparse SOFT files
    print("Clearing GEOparse SOFT files...")
    soft_files = list(cache_dir.glob("GSE*_family.soft.gz"))
    for f in soft_files:
        f.unlink()
    print(f"  ✓ Deleted {len(soft_files)} SOFT files")
    
    # 4. FullTextCacheDB
    print("Clearing FullTextCacheDB...")
    db_path = Path("data/fulltext/cache_metadata.db")
    if db_path.exists():
        conn = sqlite3.connect(str(db_path))
        conn.execute("DELETE FROM cached_files")
        conn.execute("DELETE FROM content_metadata")
        conn.commit()
        conn.close()
        print(f"  ✓ Cleared database tables")
    
    # 5. ParsedCache files
    print("Clearing ParsedCache files...")
    parsed_dir = Path("data/fulltext/parsed")
    parsed_files = list(parsed_dir.glob("*.json*"))
    for f in parsed_files:
        f.unlink()
    print(f"  ✓ Deleted {len(parsed_files)} parsed content files")
    
    # 6. SQLite registry (geo_datasets)
    print("Clearing SQLite geo_datasets...")
    db_path = Path("data/omics_oracle.db")
    if db_path.exists():
        conn = sqlite3.connect(str(db_path))
        conn.execute("DELETE FROM geo_datasets")
        conn.commit()
        conn.close()
        print(f"  ✓ Cleared geo_datasets table")
    
    print("\n✅ All caches cleared successfully!")

if __name__ == "__main__":
    asyncio.run(clear_all_caches())
```

**Usage**:
```bash
# Clear everything for clean-slate testing
python scripts/utilities/clear_all_caches.py

# Verify
redis-cli DBSIZE  # Should return 0
ls data/cache/*.json  # Should return empty
ls data/fulltext/parsed/  # Should return empty
```

---

## Testing Strategy

### Test 1: GEO Metadata Consistency (GSE189158 Bug Fix)
```bash
# Clear all caches
python scripts/utilities/clear_all_caches.py

# Search GSE189158
curl -X POST http://localhost:8000/api/agents/search \
  -H "Content-Type: application/json" \
  -d '{"search_terms": ["GSE189158"], "max_results": 1}' | \
  jq '.datasets[0].organism'

# Expected: "Homo sapiens" (not empty!)

# Verify single cache location
redis-cli GET "omics_search:geo:GSE189158" | jq '.organism'

# Expected: "Homo sapiens"
```

**Success Criteria**:
- ✅ Organism field populated correctly
- ✅ Only one cache entry (Redis)
- ✅ No SimpleCache or GEOparse stale data

---

### Test 2: Cache Performance Benchmark
```bash
# First request (cache cold)
time curl -X POST .../search -d '{"search_terms": ["GSE100000"]}' > /dev/null
# Baseline: 2-5 seconds

# Second request (Redis hit)
time curl -X POST .../search -d '{"search_terms": ["GSE100000"]}' > /dev/null
# Target: <100ms (20-50x faster)

# Check Redis metrics
curl http://localhost:8000/api/cache/stats | jq '.hit_rate'
# Target: >80% after warmup
```

---

### Test 3: AI Analysis Speed (ParsedCache + Redis)
```bash
# First analysis (disk load)
time curl -X POST .../agents/ai-analysis -d '{"geo_id": "GSE189158"}' > /dev/null
# Baseline: 5-10 seconds

# Second analysis (Redis hot-tier)
time curl -X POST .../agents/ai-analysis -d '{"geo_id": "GSE189158"}' > /dev/null
# Target: <1 second (5-10x faster)
```

---

## Migration Timeline

### Day 1: Preparation (4 hours)
- ✅ Code audit complete (this document)
- [ ] Create feature branch: `cache-consolidation-oct15`
- [ ] Write unit tests for RedisCache GEO methods
- [ ] Backup production data

### Day 2: Phase 1 - Remove SimpleCache (4 hours)
- [ ] Modify `geo/client.py` to use RedisCache
- [ ] Delete `geo/cache.py`
- [ ] Update imports across codebase
- [ ] Run unit tests
- [ ] Test GEO search with clean cache

### Day 3: Phase 2 - GEOparse Wrapper (4 hours)
- [ ] Create `geoparse_wrapper.py`
- [ ] Integrate with `geo/client.py`
- [ ] Test cache hit performance
- [ ] Measure API call reduction

### Day 4: Phase 3 - Database Integration (4 hours)
- [ ] Auto-sync ParsedCache → FullTextCacheDB
- [ ] Update SmartCache to query DB first
- [ ] Test file lookup performance
- [ ] Verify analytics queries

### Day 5: Phase 4 - Redis Hot-Tier for Parsed Content (4 hours)
- [ ] Add parsed content methods to RedisCache
- [ ] Integrate with ParsedCache
- [ ] Test AI Analysis speed
- [ ] Monitor memory usage

### Day 6: Testing & Documentation (4 hours)
- [ ] Run all test suites
- [ ] Create `clear_all_caches.py` utility
- [ ] Update documentation
- [ ] Performance benchmarks
- [ ] Create migration guide for team

**Total Effort**: 24 hours (~3 days)  
**Risk Level**: Medium (comprehensive testing required)  
**Rollback Plan**: Keep SimpleCache in archive, can restore if issues

---

## Expected Outcomes

### Performance Improvements
- **GEO Search**: 20-50x faster on cache hits (5s → 100ms)
- **AI Analysis**: 5-10x faster for recent papers (10s → 1s)
- **File Lookups**: 100-1000x faster with DB index (100ms → <1ms)
- **Memory Usage**: -40% (eliminate duplicate storage)
- **Disk Usage**: -30% (remove JSON cache files)

### Developer Experience
- **Single invalidation command**: `python clear_all_caches.py`
- **Debugging visibility**: Check Redis with `redis-cli`, not MD5 hashes
- **Metrics dashboard**: Hit rates, TTLs, sizes in one place
- **Less cognitive load**: 2 tiers instead of 6 independent systems

### Operational Benefits
- **Consistent cache behavior**: All data sources use same TTL strategy
- **Reduced API calls**: Redis hot-tier + longer TTLs = fewer NCBI hits
- **Better monitoring**: CacheMetrics class tracks everything
- **Easier troubleshooting**: Clear root cause when cache issues arise

---

## Risk Assessment

### High Risk
- **Data Loss**: Clearing wrong cache during migration
  - Mitigation: Backup `data/` directory before starting
  - Rollback: Restore from backup
  
### Medium Risk
- **Performance Regression**: Redis overhead for small queries
  - Mitigation: Benchmark before/after each phase
  - Rollback: Keep SimpleCache in archive for 30 days

### Low Risk
- **GEOparse compatibility**: Wrapper breaks library assumptions
  - Mitigation: Test wrapper extensively with various GEO IDs
  - Rollback: Remove wrapper, use direct GEOparse calls

---

## Success Metrics

### Before Consolidation
- **Cache Layers**: 6 independent systems
- **GEO Metadata Copies**: 3 (Redis, SimpleCache, GEOparse)
- **Cache Hit Rate**: Unknown (no metrics)
- **Debugging Time**: 30+ minutes to find cache entry
- **GSE189158 Organism**: Empty (cache inconsistency bug)

### After Consolidation
- **Cache Layers**: 2 tiers (hot + warm)
- **GEO Metadata Copies**: 1 (Redis only, GEOparse hidden)
- **Cache Hit Rate**: 80%+ (tracked by CacheMetrics)
- **Debugging Time**: <1 minute (single Redis query)
- **GSE189158 Organism**: "Homo sapiens" ✅

---

## Next Steps

1. **Review this document** with team (30 min)
2. **Approve consolidation plan** (decision: go/no-go)
3. **Create feature branch** `cache-consolidation-oct15`
4. **Start Phase 1** (remove SimpleCache)
5. **Daily standups** to track progress and blockers

---

## Questions for Discussion

1. **Should we keep GEOparse SOFT files?**
   - Pro: Free backup, no re-download if Redis cleared
   - Con: 1-2GB disk space, never expires
   - **Recommendation**: Keep but add 90-day cleanup script

2. **Redis memory limit?**
   - Current: No limit (uses all available RAM)
   - Risk: OOM if dataset is huge
   - **Recommendation**: Set maxmemory=2GB, eviction-policy=allkeys-lru

3. **ParsedCache Redis TTL?**
   - Option A: 1h (aggressive, saves memory)
   - Option B: 24h (better hit rate for repeated analysis)
   - **Recommendation**: 1h initially, increase if hit rate low

4. **Backward compatibility?**
   - Should we support reading old SimpleCache files?
   - **Recommendation**: No - clean break, document migration

---

**End of Audit Report**
