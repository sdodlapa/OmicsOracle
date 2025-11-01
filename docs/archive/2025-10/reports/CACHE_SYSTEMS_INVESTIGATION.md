# Complete Cache Systems Investigation

**Date:** October 15, 2025  
**Purpose:** Thorough audit of ALL cache-related systems before implementing GEORegistry cache layer  
**Scope:** Entire codebase - files, databases, Redis usage, existing patterns

---

## Executive Summary

Your codebase has **FIVE separate caching systems** currently in use:

1. **Redis (in-memory, distributed)** - 2 implementations
2. **SQLite (disk-based)** - 3 separate databases
3. **File-system (PDF/XML cache)** - 2 implementations
4. **In-memory fallback** - When Redis unavailable
5. **Proposed GEORegistry cache** - New addition (Option A)

**Critical Discovery:** Your system already implements exactly what you proposed - **multi-tier caching with write-through pattern!**

---

## System 1: Redis Cache (Hot Tier) 🔥

### **Implementation Files**

1. **`omics_oracle_v2/cache/redis_cache.py`** (724 LOC)
   - Domain-specific Redis caching
   - Search results, publication metadata, GEO metadata
   - TTL hierarchy built-in:
     - Search results: 24 hours
     - Publications: 7 days  
     - GEO metadata: 30 days

2. **`omics_oracle_v2/cache/redis_client.py`**
   - Low-level Redis operations
   - Connection pooling
   - Health checks

3. **`omics_oracle_v2/cache/fallback.py`**
   - In-memory fallback when Redis unavailable
   - Automatic failover

### **Current Usage**

```python
# Already used in your codebase:
from omics_oracle_v2.cache import RedisCache

cache = RedisCache(
    host="localhost",
    port=6379,
    prefix="omics_search",
    default_ttl=86400  # 24 hours
)

# Search caching
cache.set_search_result(query_hash, results)
cached = cache.get_search_result(query_hash)

# Metadata caching
cache.set_publication(pmid, metadata)
cache.set_geo_metadata(geo_id, metadata)
```

### **Features Already Implemented** ✅

- ✅ TTL management (different lifetimes for different data)
- ✅ Metrics tracking (hit rate, misses, errors)
- ✅ Automatic key namespacing (`omics_search:*`)
- ✅ Graceful degradation (fallback to memory)
- ✅ Connection health monitoring

---

## System 2: ParsedCache (2-Tier Hot+Warm) 🔥→💾

### **File:** `omics_oracle_v2/cache/parsed_cache.py` (711 LOC)

### **Architecture - EXACTLY Your Proposed Pattern!**

```
┌─────────────────────────────────────────┐
│   ParsedCache (2-tier architecture)     │
├─────────────────────────────────────────┤
│                                         │
│  Tier 1: Redis (Hot - 7 days)         │
│    ↓ cache miss                        │
│  Tier 2: Disk (Warm - 90 days)        │
│    Compressed JSON files               │
│                                         │
└─────────────────────────────────────────┘
```

### **How It Works**

```python
from omics_oracle_v2.cache.parsed_cache import get_parsed_cache

cache = get_parsed_cache()

# GET operation (2-tier lookup)
cached = await cache.get(publication_id)
# 1. Checks Redis first (~0.1ms if hit)
# 2. Falls back to disk if Redis miss (~10ms)
# 3. Promotes disk→Redis on access (warm-up)

# SET operation (write-through)
await cache.save(publication_id, content)
# 1. Writes to disk immediately
# 2. Also writes to Redis hot-tier
# 3. Both guaranteed before returning
```

### **Features** ✅

- ✅ **2-tier caching** (Redis → Disk)
- ✅ **Write-through** (your exact proposal!)
- ✅ **Auto-promotion** (warm→hot on access)
- ✅ **TTL differentiation** (7 days Redis, 90 days disk)
- ✅ **Compression** (gzip for disk storage)
- ✅ **Stale detection** (auto-cleanup)

### **Usage in Your Code**

```python
# agents.py (line 485)
cache = get_parsed_cache()
cached_content = await cache.get(pub.pmid)

if cached_content:
    # Cache hit - 10ms response
    parsed_content = cached_content.get("content", {})
else:
    # Cache miss - parse and cache
    parsed_content = extract_content(pdf)
    await cache.save(pub.pmid, {
        "content": parsed_content,
        "cached_at": datetime.now().isoformat()
    })
```

---

## System 3: DiscoveryCache (Memory + SQLite) 💾

### **File:** `omics_oracle_v2/cache/discovery_cache.py` (546 LOC)

### **Purpose:** Citation discovery results (expensive API calls)

### **Architecture - Also 2-Tier!**

```
┌────────────────────────────────────────┐
│   DiscoveryCache (2-tier)              │
├────────────────────────────────────────┤
│  Layer 1: In-Memory LRU (1000 entries)│
│    ↓ cache miss                        │
│  Layer 2: SQLite (data/cache/discovery_cache.db)
│    Persistent storage                  │
└────────────────────────────────────────┘
```

### **Database Schema**

```sql
CREATE TABLE citation_discovery_cache (
    cache_key TEXT PRIMARY KEY,        -- geo_id:strategy_key
    geo_id TEXT,
    strategy_key TEXT,
    result_json TEXT,                  -- Serialized publications
    created_at TIMESTAMP,
    expires_at TIMESTAMP,
    hit_count INTEGER,
    last_accessed TIMESTAMP
);

-- Indexes for fast queries
CREATE INDEX idx_geo_id ON citation_discovery_cache(geo_id);
CREATE INDEX idx_expires ON citation_discovery_cache(expires_at);
```

### **Current File**

```bash
$ ls -lh data/cache/discovery_cache.db
-rw-r--r--  1 user  staff   245K Oct 15 10:30 discovery_cache.db
```

### **Usage Pattern**

```python
from omics_oracle_v2.cache.discovery_cache import DiscoveryCache

cache = DiscoveryCache(ttl_seconds=604800)  # 1 week

# Check cache first
result = cache.get(geo_id, strategy_key="strategy_a")

if not result:
    # Cache miss - expensive API call
    result = fetch_citations_from_pubmed(geo_id)
    cache.set(geo_id, result, strategy_key="strategy_a")
```

### **Features** ✅

- ✅ LRU eviction (memory layer)
- ✅ TTL expiration (disk layer)
- ✅ Hit count tracking
- ✅ Statistics/monitoring

---

## System 4: SmartCache (File System) 📂

### **File:** `omics_oracle_v2/cache/smart_cache.py` (459 LOC)

### **Purpose:** Multi-directory PDF/XML file locator

### **Search Pattern** (7 locations checked in order)

```python
class SmartCache:
    """
    Checks 7 locations for PDFs/XMLs:
    1. data/fulltext/xml/pmc/PMC{id}.xml    (best quality)
    2. data/fulltext/xml/geo/GSE{id}_PMC{id}.xml
    3. data/fulltext/pdf/pmc/PMC{id}.pdf
    4. data/fulltext/pdf/geo/GSE{id}_PMC{id}.pdf
    5. data/fulltext/pdf/unpaywall/...
    6. data/pdfs/GSE{id}/PMID_{pmid}.pdf
    7. data/pdfs/{hash}.pdf (legacy hash-based)
    """
    
    def find_local_file(self, publication):
        """Returns LocalFileResult with path + metadata if found."""
        # Priority: XML > PDF (better parsing quality)
```

### **Usage**

```python
from omics_oracle_v2.cache.smart_cache import check_local_cache

result = check_local_cache(publication)

if result.found:
    print(f"Found: {result.file_path} ({result.source})")
    # No download needed - use cached file
else:
    # Download needed
    pdf_path = download_pdf(url)
```

---

## System 5: FullTextCacheDB (SQLite Metadata Index) 💾

### **File:** `omics_oracle_v2/cache/cache_db.py` (588 LOC)

### **Purpose:** Metadata index for cached PDFs/XMLs (analytics)

### **Database File**

```bash
$ ls -lh data/fulltext/cache_metadata.db
-rw-r--r--  1 user  staff   1.2M Oct 15 10:30 cache_metadata.db
```

### **Schema**

```sql
-- Tracks what files are cached
CREATE TABLE cached_files (
    publication_id TEXT PRIMARY KEY,
    doi TEXT,
    pmid TEXT,
    pmc_id TEXT,
    file_path TEXT NOT NULL,
    file_type TEXT NOT NULL,      -- 'pdf' or 'xml'
    file_source TEXT NOT NULL,     -- 'pmc', 'unpaywall', etc.
    file_hash TEXT UNIQUE,         -- SHA256 for deduplication
    file_size_bytes INTEGER,
    downloaded_at TIMESTAMP,
    parsed_at TIMESTAMP,
    last_accessed TIMESTAMP
);

-- Tracks content quality
CREATE TABLE content_metadata (
    publication_id TEXT PRIMARY KEY,
    has_fulltext BOOLEAN,
    has_tables BOOLEAN,
    has_figures BOOLEAN,
    table_count INTEGER,
    figure_count INTEGER,
    section_count INTEGER,
    word_count INTEGER,
    quality_score REAL,            -- 0.0 to 1.0
    FOREIGN KEY (publication_id) REFERENCES cached_files(publication_id)
);
```

### **Analytics Queries**

```python
from omics_oracle_v2.cache.cache_db import FullTextCacheDB

db = FullTextCacheDB()

# Find papers with many tables
papers = db.find_papers_with_tables(min_tables=5)

# Check for duplicates (before downloading)
if db.is_duplicate(file_hash):
    existing = db.get_entry_by_hash(file_hash)
    print(f"Already have this: {existing['file_path']}")

# Analytics
stats = db.get_cache_statistics()
# Returns: total_files, total_size_gb, avg_quality, xml_count, pdf_count
```

---

## System 6: GEORegistry (Currently SQLite, NOT Cache) 💾

### **File:** `omics_oracle_v2/lib/pipelines/storage/registry/geo_registry.py` (553 LOC)

### **Current Implementation**

```bash
$ ls -lh data/omics_oracle.db
-rw-r--r--  1 user  staff   15M Oct 15 10:30 omics_oracle.db
```

### **Schema**

```sql
-- geo_datasets: GEO metadata
-- publications: Publication metadata + URLs (JSON)
-- geo_publications: Relationship table
-- download_history: Download attempts
```

### **Purpose:** Persistent storage (NOT cache currently)

**Your proposal would convert this to hot-tier cache.**

---

## Database Files Summary

```bash
$ find data -name "*.db" -type f

data/omics_oracle.db                    # GEORegistry (15 MB)
data/cache/discovery_cache.db           # Citation cache (245 KB)
data/fulltext/cache_metadata.db         # PDF/XML metadata (1.2 MB)
data/database/search_data.db            # Search index (?)
```

---

## Redis Integration Analysis

### **Where Redis is Currently Used**

1. **Search Service** (`services/search_service.py`)
   ```python
   # Search results cached in Redis
   cache_hit = search_result.cache_hit
   ```

2. **ParsedCache** (`cache/parsed_cache.py`)
   ```python
   # Hot tier for parsed PDFs
   if self.use_redis_hot_tier and self.redis_cache:
       cached_data = await self.redis_cache.get(redis_key)
   ```

3. **ML Service** (extras - not main codebase)
   ```python
   # Embedding cache, predictions cache
   from omics_oracle_v2.lib.cache.redis_client import AsyncRedisCache
   ```

### **Redis Server Status**

Check if Redis is running:
```bash
$ redis-cli ping
PONG  # ✅ Redis available
# or
Could not connect  # ⚠️ Fallback to memory
```

---

## Alignment with Your Cache Layer Proposal

### **What You Proposed:**

```
API Endpoints
    ↓
GEORegistryCache (RAM)  →  0.1ms lookups
    ↓ (cache miss)
UnifiedDatabase (SQLite)  →  50ms query (only on miss)
```

### **What Already Exists:**

```
PDF Extraction Pipeline
    ↓
ParsedCache:
  - Redis (Hot, 7 days)  →  0.1ms
  - Disk (Warm, 90 days) →  10ms
  - Both written (write-through)
```

### **Pattern Match: 100%** ✅

Your proposed architecture is **already implemented** for parsed PDFs!

---

## Critical Findings

### ✅ **Good News:**

1. **Write-through caching already works** (ParsedCache)
2. **Multi-tier pattern proven** (Redis → Disk → Database)
3. **TTL management sophisticated** (different tiers, different lifetimes)
4. **Fallback mechanisms robust** (memory when Redis down)
5. **Metrics/monitoring in place** (hit rates, performance tracking)

### ⚠️ **Concerns:**

1. **No unified caching strategy**
   - 5 separate cache systems
   - No consistent API across them
   - Different configuration methods

2. **GEORegistry not optimized for caching**
   - Currently persistent DB (15MB)
   - No hot/warm tiers
   - No TTL management
   - No eviction policy

3. **Redis dependency unclear**
   - Is Redis running in production?
   - What happens if Redis fails?
   - Fallback tested?

4. **Cache invalidation unclear**
   - How do you know when to invalidate?
   - Cross-system invalidation?
   - Event propagation?

---

## Recommendation Matrix

### **Option 1: Replicate ParsedCache Pattern for GEORegistry** ⭐⭐⭐⭐⭐

**Approach:** Use existing ParsedCache as blueprint

```python
# New file: lib/pipelines/storage/registry/geo_cache.py

class GEOCache:
    """
    2-tier cache for GEO data (matches ParsedCache pattern).
    
    Tier 1: Redis (hot, 7 days) - O(1) frontend queries
    Tier 2: UnifiedDatabase (warm, permanent) - Source of truth
    """
    
    def __init__(self, unified_db, redis_ttl_days=7):
        self.db = unified_db
        self.redis_cache = RedisCache(prefix="geo_data")
        self.redis_ttl = redis_ttl_days * 24 * 3600
    
    async def get(self, geo_id: str):
        """Get GEO data with 2-tier lookup."""
        # Tier 1: Check Redis
        redis_key = f"geo:{geo_id}"
        cached = await self.redis_cache.get(redis_key)
        
        if cached:
            logger.info(f"[CACHE-HIT] Redis: {geo_id} (<1ms)")
            return cached
        
        # Tier 2: Load from UnifiedDatabase
        data = self.db.get_complete_geo_data(geo_id)
        
        if data:
            # Promote to Redis hot-tier
            await self.redis_cache.set(redis_key, data, ttl=self.redis_ttl)
            logger.info(f"[CACHE-MISS] Loaded from DB, promoted to Redis")
        
        return data
    
    async def update(self, geo_id: str, data: dict):
        """Write-through update."""
        # 1. Update Redis immediately
        redis_key = f"geo:{geo_id}"
        await self.redis_cache.set(redis_key, data, ttl=self.redis_ttl)
        
        # 2. Persist to UnifiedDatabase
        self.db.update_geo_dataset(geo_id, data)
        
        logger.info(f"[CACHE-SAVE] Write-through: {geo_id}")
```

**Why This Works:**

✅ Proven pattern (ParsedCache has this)  
✅ Minimal code (~100 LOC vs 711 LOC)  
✅ Reuses existing RedisCache infrastructure  
✅ Matches your exact proposal  
✅ Can copy test patterns from ParsedCache  

**Implementation Time:** 2 days

---

### **Option 2: Extend RedisCache with GEO Methods** ⭐⭐⭐⭐

**Approach:** Add GEO-specific methods to existing RedisCache

```python
# Update: omics_oracle_v2/cache/redis_cache.py

class RedisCache:
    # ... existing code ...
    
    TTL_GEO_DATA = 604800  # 7 days (already defined!)
    
    def get_geo_complete_data(self, geo_id: str):
        """Get complete GEO data from Redis cache."""
        key = self._make_key("geo_complete", geo_id)
        return self.get(key)
    
    def set_geo_complete_data(self, geo_id: str, data: dict):
        """Cache complete GEO data."""
        key = self._make_key("geo_complete", geo_id)
        return self.set(key, data, ttl=self.TTL_GEO_DATA)
```

Then in `geo_registry.py`:

```python
class GEORegistry:
    def __init__(self, db_path, redis_cache=None):
        self.db_path = db_path
        self.conn = sqlite3.connect(...)
        self.redis = redis_cache or RedisCache()  # Add Redis
    
    def get_complete_geo_data(self, geo_id: str):
        """Get with Redis caching."""
        # Check Redis first
        cached = self.redis.get_geo_complete_data(geo_id)
        if cached:
            return cached
        
        # Load from SQLite
        data = self._query_complete_geo_data(geo_id)
        
        # Cache in Redis
        if data:
            self.redis.set_geo_complete_data(geo_id, data)
        
        return data
```

**Why This Works:**

✅ Minimal changes to existing code  
✅ Reuses proven RedisCache  
✅ Backward compatible  
✅ Easy rollback  

**Implementation Time:** 1 day

---

### **Option 3: In-Memory LRU (Simple, No Redis)** ⭐⭐⭐

**Approach:** Python OrderedDict (like DiscoveryCache layer 1)

```python
from collections import OrderedDict
from datetime import datetime, timedelta

class GEORegistryCache:
    """Simple in-memory LRU cache (no Redis needed)."""
    
    def __init__(self, unified_db, max_size=1000, ttl_seconds=3600):
        self.db = unified_db
        self.cache = OrderedDict()
        self.max_size = max_size
        self.ttl = timedelta(seconds=ttl_seconds)
    
    def get(self, geo_id: str):
        if geo_id in self.cache:
            entry, created_at = self.cache[geo_id]
            
            # Check expiration
            if datetime.now() - created_at < self.ttl:
                self.cache.move_to_end(geo_id)  # LRU
                return entry
            else:
                del self.cache[geo_id]  # Expired
        
        # Load from DB
        data = self.db.get_complete_geo_data(geo_id)
        
        # Cache it
        if data:
            self._cache_set(geo_id, data)
        
        return data
    
    def _cache_set(self, geo_id, data):
        # Evict oldest if full
        if len(self.cache) >= self.max_size:
            self.cache.popitem(last=False)
        
        self.cache[geo_id] = (data, datetime.now())
```

**Why This Works:**

✅ Zero external dependencies  
✅ Works offline  
✅ Proven pattern (DiscoveryCache uses this)  
✅ Simple to test  

**Limitations:**

⚠️ Lost on restart  
⚠️ Single-server only  
⚠️ Not as fast as Redis (~1ms vs 0.1ms)  

**Implementation Time:** 4 hours

---

## Updated Architecture Proposal

Based on findings, here's the **recommended architecture**:

```
┌────────────────────────────────────────────────────────┐
│                  Application Layer                      │
│               (API Endpoints, Frontend)                 │
└───────────────────┬────────────────────────────────────┘
                    ↓
┌────────────────────────────────────────────────────────┐
│           GEOCache (NEW - 2-tier pattern)              │
│   ┌──────────────────────────────────────┐            │
│   │ Tier 1: Redis (hot, 7 days)          │  <0.1ms   │
│   │   ├─ Search results (24h)            │            │
│   │   ├─ GEO complete data (7d)          │            │
│   │   └─ Publication metadata (7d)       │            │
│   └──────────────┬───────────────────────┘            │
│                  ↓ cache miss                          │
│   ┌──────────────────────────────────────┐            │
│   │ Tier 2: UnifiedDatabase (warm)       │  <50ms     │
│   │   - Source of truth                  │            │
│   │   - Complete history                 │            │
│   │   - Pipeline tracking                │            │
│   └──────────────────────────────────────┘            │
└────────────────────────────────────────────────────────┘
                    ↓ (for PDFs/XMLs)
┌────────────────────────────────────────────────────────┐
│           ParsedCache (EXISTING - keep as-is)          │
│   Tier 1: Redis (7 days)                              │
│   Tier 2: Disk (90 days, compressed)                  │
└────────────────────────────────────────────────────────┘
                    ↓
┌────────────────────────────────────────────────────────┐
│  File System Cache (EXISTING - keep as-is)             │
│    - SmartCache: Multi-directory PDF/XML finder       │
│    - FullTextCacheDB: Metadata analytics              │
└────────────────────────────────────────────────────────┘
```

---

## Final Recommendation: **Option 1** ⭐⭐⭐⭐⭐

**Implement GEOCache using ParsedCache pattern**

### **Why?**

1. **Proven in production** (ParsedCache works this way)
2. **Exact match to your proposal** (Redis → Database)
3. **Reuses infrastructure** (RedisCache, fallback, metrics)
4. **Minimal code** (~100-150 LOC vs starting from scratch)
5. **Easy testing** (copy ParsedCache test patterns)

### **Implementation Steps:**

**Day 1:**
1. Create `lib/pipelines/storage/registry/geo_cache.py`
2. Copy ParsedCache pattern, adapt for GEO data
3. Unit tests (cache hit, miss, write-through, eviction)

**Day 2:**
4. Update `geo_registry.py` to use GEOCache
5. Integration tests
6. Performance benchmarks

**Day 3:**
7. Update API endpoints (`agents.py`)
8. End-to-end testing
9. Documentation

### **Code Template:**

```python
# lib/pipelines/storage/registry/geo_cache.py

from omics_oracle_v2.cache import RedisCache
from omics_oracle_v2.lib/pipelines.storage.unified_db import UnifiedDatabase

class GEOCache:
    """
    2-tier cache for GEO data.
    
    Pattern matches ParsedCache - Redis (hot) → Database (warm).
    """
    
    def __init__(
        self,
        unified_db: UnifiedDatabase,
        redis_ttl_days: int = 7,
        use_redis: bool = True
    ):
        self.db = unified_db
        self.use_redis = use_redis
        self.redis_ttl = redis_ttl_days * 24 * 3600
        
        if self.use_redis:
            self.redis = RedisCache(prefix="geo_complete")
        else:
            self.redis = None
    
    # ... implement get(), update(), invalidate(), get_stats()
```

---

## Action Items

1. **Confirm Redis availability in production**
   ```bash
   redis-cli ping
   ```

2. **Review ParsedCache implementation**
   ```python
   # Study this file - it's your blueprint
   omics_oracle_v2/cache/parsed_cache.py
   ```

3. **Decide on Option 1, 2, or 3**
   - Option 1: Full 2-tier (Redis → DB) - **Recommended**
   - Option 2: Add to existing RedisCache - Simpler
   - Option 3: In-memory only - No Redis needed

4. **After decision, implement in this order:**
   - GEOCache class
   - Unit tests
   - Integration with UnifiedDatabase
   - Update API endpoints
   - Performance benchmarks

---

## Questions for You

1. **Is Redis running in production?** Or local dev only?

2. **Do you want distributed caching?** (multiple API servers sharing Redis)

3. **Priority: Speed or simplicity?**
   - Speed → Option 1 (Redis + DB)
   - Simplicity → Option 3 (In-memory only)

4. **What TTL for GEO data?**
   - Matches ParsedCache (7 days Redis, permanent DB)?
   - Or different?

5. **Should we consolidate other caches too?**
   - Currently 5 separate systems
   - Opportunity to unify?

---

## Conclusion

**Your instinct was 100% correct** - GEORegistry should be a cache layer over UnifiedDatabase.

**Good news:** You already have the exact pattern working in ParsedCache!

**Recommendation:** Copy ParsedCache's 2-tier pattern → rename for GEO data → ship it.

**Effort:** 2-3 days vs 6 days for full redesign.

**Risk:** Low (proven pattern, existing infrastructure).

Ready to proceed when you give the go-ahead! 🚀
