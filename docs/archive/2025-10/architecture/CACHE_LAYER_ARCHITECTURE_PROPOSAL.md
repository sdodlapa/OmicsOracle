# Cache Layer Architecture: GEORegistry as Hot Storage

**Date:** October 15, 2025  
**Proposal:** Transform GEORegistry from database to in-memory cache layer over UnifiedDatabase

---

## Your Proposal (Interpreted)

```
┌─────────────────────────────────────────────────────────┐
│                   Application Layer                      │
│           (API Endpoints, Frontend Queries)              │
└───────────────────┬─────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│              GEORegistry (Hot/Flash Layer)               │
│  • In-memory data structure (dict/cache)                 │
│  • Fast O(1) lookups for frontend                        │
│  • Temporary snapshot during active sessions             │
│  • Eviction policy (LRU, TTL)                           │
└───────────────────┬─────────────────────────────────────┘
                    ↓ (write-through on updates)
┌─────────────────────────────────────────────────────────┐
│           UnifiedDatabase (Cold Storage)                 │
│  • Persistent SQLite database                            │
│  • Source of truth                                       │
│  • Pipeline tracking, audit logs, full history           │
│  • All data eventually written here                      │
└─────────────────────────────────────────────────────────┘
```

### **How It Would Work**

**Read Path:**
```python
# Frontend requests data for GSE12345
data = geo_registry.get("GSE12345")

# Cache hit → return immediately
if data in geo_registry.cache:
    return data  # ~1ms response

# Cache miss → load from UnifiedDatabase
else:
    data = unified_db.get_complete_geo_data("GSE12345")  # ~50ms query
    geo_registry.cache["GSE12345"] = data  # Populate cache
    return data
```

**Write Path (Write-Through):**
```python
# API endpoint downloads new PDFs
enriched_data = await fulltext_service.enrich_datasets(...)

# 1. Update cache immediately (fast response to frontend)
geo_registry.update("GSE12345", enriched_data)

# 2. Write-through to UnifiedDatabase (persistence)
unified_db.save_url_discovery(geo_id, pmid, urls)
unified_db.save_pdf_acquisition(geo_id, pmid, pdf_path)
unified_db.log_event("P3", "success", duration_ms)

# Frontend sees immediate update, data persisted for audit
```

---

## Critical Evaluation

### ✅ **Strengths of This Approach**

#### 1. **Performance Gains**
```python
# Current (separate databases)
geo_registry.get_complete_geo_data("GSE12345")  # ~5-10ms (SQLite query)

# Proposed (in-memory cache)
geo_registry.get("GSE12345")  # ~0.1ms (dict lookup)
```
**50-100x faster** for repeated frontend queries.

#### 2. **Single Source of Truth**
- UnifiedDatabase becomes the ONLY persistent storage
- No data duplication concerns
- No sync issues between two databases
- Simpler backup/restore strategy

#### 3. **Clear Separation of Concerns**
```
Hot Layer (GEORegistry):
  - Purpose: Speed (frontend queries)
  - Lifetime: Session-based (minutes to hours)
  - Storage: RAM
  - Scope: Active GEO datasets only

Cold Layer (UnifiedDatabase):
  - Purpose: Persistence, audit, completeness
  - Lifetime: Permanent
  - Storage: Disk
  - Scope: All historical data
```

#### 4. **Memory Efficiency**
```python
# Only cache what's actively used
class GEORegistry:
    def __init__(self, max_size=1000, ttl_seconds=3600):
        self.cache = {}  # LRU cache with eviction
        self.max_size = max_size
        self.ttl = ttl_seconds
    
    def get(self, geo_id: str):
        # Check cache first
        if geo_id in self.cache:
            entry = self.cache[geo_id]
            if not self._is_expired(entry):
                return entry.data
        
        # Cache miss → load from UnifiedDatabase
        data = self.unified_db.get_complete_geo_data(geo_id)
        self._cache_set(geo_id, data)
        return data
```

Typical memory usage:
- 1000 GEO datasets × ~20KB each = **~20MB RAM** (negligible)
- vs. Disk-based SQLite query overhead

#### 5. **Simplified Architecture**
```python
# Before (two databases)
registry = GEORegistry()  # → data/omics_oracle.db
coordinator = PipelineCoordinator()  # → data/database/omics_oracle.db

# After (cache + database)
cache = GEORegistryCache()  # → RAM (no DB file)
db = UnifiedDatabase()  # → data/omics_oracle.db (single source)
```

#### 6. **Better for Distributed Systems**
- Cache can use Redis/Memcached in production
- Multiple API servers can share cache
- Database remains single source of truth
- Scales horizontally

---

### ⚠️ **Challenges & Trade-offs**

#### 1. **Cache Invalidation Complexity**
```python
# Problem: How to know when cache is stale?

# Scenario 1: Background pipeline updates database
pipeline.save_pdf_acquisition("GSE12345", pmid="12345678", ...)
# → Cache now has old data! Frontend shows "0 PDFs" when 1 exists

# Solution: Invalidate cache on writes
def save_pdf_acquisition(self, geo_id, pmid, ...):
    # Write to DB
    self.db.insert_pdf_acquisition(...)
    
    # Invalidate cache
    cache.invalidate(geo_id)  # Forces reload on next access
```

**Issue:** If pipeline runs offline, cache doesn't know about updates.

**Fix:** Add cache versioning or event bus:
```python
# Event-driven invalidation
event_bus.publish("geo_updated", geo_id="GSE12345")
cache.subscribe("geo_updated", lambda geo_id: cache.invalidate(geo_id))
```

#### 2. **Cold Start Performance**
```python
# First request after server restart
data = cache.get("GSE12345")  # Cache empty
# → Falls back to UnifiedDatabase query (~50ms)
# → 10 datasets × 50ms = 500ms first load

# Workaround: Pre-warm cache on startup
def warmup_cache(top_n=100):
    """Load most-accessed GEO datasets into cache."""
    popular_geos = db.get_most_queried_geos(limit=top_n)
    for geo_id in popular_geos:
        cache.get(geo_id)  # Loads into cache
```

#### 3. **Data Freshness Guarantees**
```python
# Problem: User downloads PDF, expects immediate visibility

# Write-through (your proposal) ✅
def enrich_datasets(...):
    # Download PDF
    pdf_path = await download_pdf(url)
    
    # 1. Update cache immediately
    cache.update("GSE12345", {"pdfs_downloaded": 1})
    
    # 2. Persist to database
    db.save_pdf_acquisition(geo_id, pmid, pdf_path)
    
    # User sees update instantly ✅

# Write-behind (alternative) ⚠️
def enrich_datasets(...):
    # 1. Update cache
    cache.update("GSE12345", ...)
    
    # 2. Queue database write (async)
    db_queue.enqueue(lambda: db.save_pdf_acquisition(...))
    
    # Faster but risky (data loss if crash before write)
```

**Recommendation:** Use **write-through** (your proposal) for data integrity.

#### 4. **Memory Limits**
```python
# What if user queries 10,000 GEO datasets?
# 10,000 × 20KB = 200MB RAM (still acceptable)

# But with full content extraction:
# 10,000 × 500KB (full_text) = 5GB RAM (problematic)

# Solution: Multi-tier caching
class GEORegistryCache:
    def __init__(self):
        self.hot_cache = {}  # Metadata only (~20KB per GEO)
        self.cold_cache = {}  # With full_text (~500KB per GEO)
    
    def get_metadata(self, geo_id):
        return self.hot_cache.get(geo_id) or self._load_metadata(geo_id)
    
    def get_full_content(self, geo_id):
        # Only load when explicitly requested
        return self.cold_cache.get(geo_id) or self._load_full_content(geo_id)
```

#### 5. **Testing Complexity**
```python
# Need to test cache behavior

def test_cache_hit():
    cache.set("GSE12345", data)
    assert cache.get("GSE12345") == data  # No DB query

def test_cache_miss():
    assert cache.get("GSE99999") == db_data  # Falls back to DB

def test_cache_invalidation():
    cache.set("GSE12345", old_data)
    db.update_geo_dataset("GSE12345", new_data)
    cache.invalidate("GSE12345")
    assert cache.get("GSE12345") == new_data  # Reloaded

def test_cache_eviction():
    # Fill cache to max_size
    for i in range(1001):
        cache.set(f"GSE{i}", data)
    
    # Oldest entry evicted
    assert cache.get("GSE0") == None  # LRU eviction
```

---

## Implementation Analysis

### **Option A: Python Dict + LRU (Simple)** ⭐

```python
from collections import OrderedDict
from datetime import datetime, timedelta
from typing import Dict, Optional, Any

class GEORegistryCache:
    """In-memory cache layer over UnifiedDatabase.
    
    Features:
    - LRU eviction (max_size entries)
    - TTL expiration (entries expire after ttl_seconds)
    - Write-through to UnifiedDatabase
    - O(1) lookups for frontend queries
    """
    
    def __init__(self, unified_db, max_size=1000, ttl_seconds=3600):
        self.db = unified_db
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.max_size = max_size
        self.ttl = timedelta(seconds=ttl_seconds)
        self.stats = {"hits": 0, "misses": 0, "evictions": 0}
    
    def get(self, geo_id: str) -> Optional[Dict]:
        """Get GEO data with cache-first strategy."""
        # Check cache
        if geo_id in self.cache:
            entry = self.cache[geo_id]
            
            # Check expiration
            if datetime.now() - entry.created_at < self.ttl:
                # Move to end (LRU)
                self.cache.move_to_end(geo_id)
                self.stats["hits"] += 1
                return entry.data
            else:
                # Expired - remove
                del self.cache[geo_id]
        
        # Cache miss - load from database
        self.stats["misses"] += 1
        data = self.db.get_complete_geo_data(geo_id)
        
        if data:
            self._cache_set(geo_id, data)
        
        return data
    
    def update(self, geo_id: str, data: Dict):
        """Write-through update: cache + database."""
        # 1. Update cache immediately (fast frontend response)
        self._cache_set(geo_id, data)
        
        # 2. Persist to database (source of truth)
        self.db.update_geo_dataset(geo_id, data)
    
    def invalidate(self, geo_id: str):
        """Remove entry from cache (forces reload)."""
        if geo_id in self.cache:
            del self.cache[geo_id]
    
    def clear(self):
        """Clear entire cache."""
        self.cache.clear()
        self.stats = {"hits": 0, "misses": 0, "evictions": 0}
    
    def _cache_set(self, geo_id: str, data: Dict):
        """Add/update cache entry with LRU eviction."""
        # Evict oldest if at capacity
        if len(self.cache) >= self.max_size and geo_id not in self.cache:
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
            self.stats["evictions"] += 1
        
        # Add/update entry
        self.cache[geo_id] = CacheEntry(data=data, created_at=datetime.now())
        self.cache.move_to_end(geo_id)
    
    def get_stats(self) -> Dict:
        """Get cache statistics."""
        total = self.stats["hits"] + self.stats["misses"]
        hit_rate = self.stats["hits"] / total if total > 0 else 0
        
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hit_rate": f"{hit_rate:.1%}",
            **self.stats
        }


class CacheEntry:
    """Cache entry with metadata."""
    
    def __init__(self, data: Dict, created_at: datetime):
        self.data = data
        self.created_at = created_at
```

**Usage:**
```python
# Initialize
unified_db = UnifiedDatabase()
cache = GEORegistryCache(unified_db, max_size=1000, ttl_seconds=3600)

# Read (cache-first)
data = cache.get("GSE12345")  # ~0.1ms if cached, ~50ms if not

# Write (write-through)
cache.update("GSE12345", {"pdfs_downloaded": 5})

# Invalidate
cache.invalidate("GSE12345")

# Stats
print(cache.get_stats())
# {'size': 847, 'max_size': 1000, 'hit_rate': '94.2%', 'hits': 1523, 'misses': 94, 'evictions': 23}
```

**Pros:**
✅ Simple implementation (~100 LOC)  
✅ No external dependencies  
✅ Built-in LRU + TTL  
✅ Easy to test  

**Cons:**
⚠️ Single-server only (not distributed)  
⚠️ Lost on restart (no persistence)  

---

### **Option B: Redis (Production-Grade)** 🚀

```python
import json
import redis
from typing import Dict, Optional

class GEORegistryCache:
    """Redis-backed cache layer over UnifiedDatabase.
    
    Features:
    - Distributed (multi-server support)
    - Persistent (survives restarts)
    - Automatic TTL expiration
    - Built-in pub/sub for invalidation
    """
    
    def __init__(self, unified_db, redis_url="redis://localhost:6379", ttl_seconds=3600):
        self.db = unified_db
        self.redis = redis.from_url(redis_url, decode_responses=True)
        self.ttl = ttl_seconds
        self.prefix = "geo:"
    
    def get(self, geo_id: str) -> Optional[Dict]:
        """Get GEO data with Redis cache."""
        cache_key = f"{self.prefix}{geo_id}"
        
        # Check Redis
        cached = self.redis.get(cache_key)
        if cached:
            self.redis.incr("cache:hits")
            return json.loads(cached)
        
        # Cache miss - load from database
        self.redis.incr("cache:misses")
        data = self.db.get_complete_geo_data(geo_id)
        
        if data:
            # Store in Redis with TTL
            self.redis.setex(
                cache_key,
                self.ttl,
                json.dumps(data)
            )
        
        return data
    
    def update(self, geo_id: str, data: Dict):
        """Write-through update with pub/sub notification."""
        # 1. Update Redis
        cache_key = f"{self.prefix}{geo_id}"
        self.redis.setex(cache_key, self.ttl, json.dumps(data))
        
        # 2. Persist to database
        self.db.update_geo_dataset(geo_id, data)
        
        # 3. Publish invalidation event (for other servers)
        self.redis.publish("geo:invalidate", geo_id)
    
    def invalidate(self, geo_id: str):
        """Invalidate cache entry."""
        cache_key = f"{self.prefix}{geo_id}"
        self.redis.delete(cache_key)
    
    def subscribe_to_invalidations(self, callback):
        """Subscribe to invalidation events from other servers."""
        pubsub = self.redis.pubsub()
        pubsub.subscribe("geo:invalidate")
        
        for message in pubsub.listen():
            if message["type"] == "message":
                geo_id = message["data"]
                callback(geo_id)
    
    def get_stats(self) -> Dict:
        """Get cache statistics."""
        hits = int(self.redis.get("cache:hits") or 0)
        misses = int(self.redis.get("cache:misses") or 0)
        total = hits + misses
        hit_rate = hits / total if total > 0 else 0
        
        return {
            "hit_rate": f"{hit_rate:.1%}",
            "hits": hits,
            "misses": misses,
            "keys": self.redis.dbsize()
        }
```

**Pros:**
✅ Production-ready  
✅ Distributed caching  
✅ Survives restarts  
✅ Built-in pub/sub  
✅ Battle-tested  

**Cons:**
⚠️ External dependency (Redis server)  
⚠️ More complex setup  
⚠️ Network overhead (local Redis: ~0.5ms, remote: ~5ms)  

---

## Migration Path

### **Phase 1: Refactor GEORegistry to Cache (2 days)**

**Step 1:** Create cache interface
```python
# lib/pipelines/storage/registry/cache.py
from abc import ABC, abstractmethod

class GEOCache(ABC):
    """Abstract cache interface."""
    
    @abstractmethod
    def get(self, geo_id: str):
        pass
    
    @abstractmethod
    def update(self, geo_id: str, data: dict):
        pass
    
    @abstractmethod
    def invalidate(self, geo_id: str):
        pass

class InMemoryGEOCache(GEOCache):
    """OrderedDict-based implementation."""
    # ... (Option A code above)

class RedisGEOCache(GEOCache):
    """Redis-based implementation."""
    # ... (Option B code above)
```

**Step 2:** Update UnifiedDatabase to support complete GEO queries
```python
# lib/pipelines/storage/unified_db.py

class UnifiedDatabase:
    def get_complete_geo_data(self, geo_id: str) -> Dict:
        """
        Get all data for a GEO dataset in one query.
        This powers the cache layer.
        """
        with self.get_connection() as conn:
            # Main query with JOINs
            sql = """
                SELECT 
                    g.geo_id,
                    g.title AS geo_title,
                    g.organism,
                    g.platform,
                    g.publication_count,
                    g.pdfs_downloaded,
                    
                    u.pmid,
                    u.title AS paper_title,
                    u.authors,
                    u.journal,
                    u.year,
                    
                    ud.urls_json,
                    
                    p.pdf_path,
                    p.pdf_size,
                    p.status AS pdf_status,
                    
                    c.full_text,
                    c.extraction_quality
                    
                FROM geo_datasets g
                LEFT JOIN universal_identifiers u ON g.geo_id = u.geo_id
                LEFT JOIN url_discovery ud ON u.geo_id = ud.geo_id AND u.pmid = ud.pmid
                LEFT JOIN pdf_acquisition p ON u.geo_id = p.geo_id AND u.pmid = p.pmid
                LEFT JOIN content_extraction c ON u.geo_id = c.geo_id AND u.pmid = c.pmid
                WHERE g.geo_id = ?
            """
            
            cursor = conn.execute(sql, (geo_id,))
            rows = cursor.fetchall()
            
            if not rows:
                return None
            
            # Transform to frontend format
            return self._format_complete_geo_data(rows)
    
    def _format_complete_geo_data(self, rows) -> Dict:
        """Transform SQL rows to frontend format."""
        # ... similar to GEORegistry.get_complete_geo_data() ...
```

**Step 3:** Replace GEORegistry database with cache
```python
# lib/pipelines/storage/registry/__init__.py

# Old (database)
# _registry_instance = GEORegistry()  # SQLite database

# New (cache)
from .cache import InMemoryGEOCache
from ..unified_db import UnifiedDatabase

_unified_db = UnifiedDatabase()
_registry_instance = InMemoryGEOCache(
    unified_db=_unified_db,
    max_size=1000,
    ttl_seconds=3600
)

def get_registry():
    return _registry_instance
```

**Step 4:** Update API endpoints (no changes needed!)
```python
# api/routes/agents.py - NO CHANGES!

registry = get_registry()  # Now returns cache instead of database

# Code works exactly the same
data = registry.get("GSE12345")  # Cache-first lookup
registry.update("GSE12345", new_data)  # Write-through
```

---

### **Phase 2: Migrate Existing Data (1 day)**

```python
#!/usr/bin/env python3
"""Migrate GEORegistry database to UnifiedDatabase."""

import sqlite3
from lib.pipelines.storage.unified_db import UnifiedDatabase
from lib.pipelines.storage.registry.geo_registry import GEORegistry

def migrate():
    # Connect to both databases
    old_registry = GEORegistry()  # data/omics_oracle.db
    unified_db = UnifiedDatabase()  # data/database/omics_oracle.db
    
    print("Migrating GEORegistry data to UnifiedDatabase...")
    
    # Get all GEO datasets from old registry
    geo_ids = old_registry.get_all_geo_ids()
    print(f"Found {len(geo_ids)} GEO datasets to migrate")
    
    for i, geo_id in enumerate(geo_ids, 1):
        # Get complete data from old registry
        data = old_registry.get_complete_geo_data(geo_id)
        
        # Save to UnifiedDatabase
        # 1. GEO metadata
        unified_db.insert_geo_dataset(geo_id, data["geo"])
        
        # 2. Publications
        for paper in data["papers"]["original"] + data["papers"]["citing"]:
            unified_db.insert_universal_identifier(
                geo_id=geo_id,
                pmid=paper["pmid"],
                title=paper["title"],
                # ... other fields
            )
            
            # 3. URLs
            if paper.get("urls"):
                unified_db.insert_url_discovery(
                    geo_id=geo_id,
                    pmid=paper["pmid"],
                    urls=paper["urls"]
                )
            
            # 4. PDF info
            if paper.get("pdf_path"):
                unified_db.insert_pdf_acquisition(
                    geo_id=geo_id,
                    pmid=paper["pmid"],
                    pdf_path=paper["pdf_path"],
                    # ... other fields
                )
        
        if i % 100 == 0:
            print(f"  Migrated {i}/{len(geo_ids)} datasets...")
    
    print("✅ Migration complete!")
    print(f"   Old database: data/omics_oracle.db (can be archived)")
    print(f"   New database: data/database/omics_oracle.db")
    print(f"   Cache: In-memory (will populate on first access)")

if __name__ == "__main__":
    migrate()
```

---

### **Phase 3: Testing & Validation (1 day)**

```python
# tests/test_cache_layer.py

import pytest
from lib.pipelines.storage.registry import get_registry
from lib.pipelines.storage.unified_db import UnifiedDatabase

@pytest.fixture
def cache():
    db = UnifiedDatabase(":memory:")  # In-memory for tests
    from lib.pipelines.storage.registry.cache import InMemoryGEOCache
    return InMemoryGEOCache(db, max_size=10, ttl_seconds=60)

def test_cache_miss_loads_from_database(cache):
    """First access should load from database."""
    data = cache.get("GSE12345")
    
    assert data is not None
    assert cache.get_stats()["misses"] == 1
    assert cache.get_stats()["hits"] == 0

def test_cache_hit_returns_from_memory(cache):
    """Second access should hit cache."""
    cache.get("GSE12345")  # Prime cache
    data = cache.get("GSE12345")  # Should hit cache
    
    assert data is not None
    assert cache.get_stats()["hits"] == 1

def test_write_through_updates_both(cache):
    """Updates should go to cache AND database."""
    cache.update("GSE12345", {"pdfs_downloaded": 5})
    
    # Check cache
    cached = cache.get("GSE12345")
    assert cached["pdfs_downloaded"] == 5
    
    # Check database
    cache.invalidate("GSE12345")  # Clear cache
    from_db = cache.get("GSE12345")  # Force DB load
    assert from_db["pdfs_downloaded"] == 5

def test_lru_eviction(cache):
    """Oldest entries should be evicted."""
    # Fill cache to capacity (max_size=10)
    for i in range(11):
        cache.get(f"GSE{i}")
    
    assert cache.get_stats()["evictions"] >= 1
    assert cache.get_stats()["size"] == 10

def test_ttl_expiration(cache):
    """Expired entries should be reloaded."""
    import time
    
    # Set very short TTL
    cache.ttl = timedelta(seconds=0.1)
    
    cache.get("GSE12345")  # Prime cache
    time.sleep(0.2)  # Wait for expiration
    
    cache.get("GSE12345")  # Should reload from DB
    assert cache.get_stats()["misses"] == 2  # Two DB loads
```

---

## Objective Assessment

### **Should You Implement This?**

#### **YES - Implement This** ✅ (Recommendation)

**Reasons:**

1. **Architecturally Superior**
   - Single source of truth (UnifiedDatabase)
   - Clear separation: cache (speed) vs database (persistence)
   - Industry-standard pattern (write-through cache)
   - Aligns with modern architecture best practices

2. **Performance Benefits**
   - 50-100x faster frontend queries (0.1ms vs 5-10ms)
   - Reduces database load (fewer queries)
   - Scalable to distributed systems

3. **Maintainability**
   - Eliminates data duplication concerns
   - Simpler to reason about ("cache is just fast access")
   - Easier to test (cache + DB separately)
   - Future-proof (can swap Redis later)

4. **Your Intuition is Correct**
   - GEORegistry IS temporary/snapshot data
   - UnifiedDatabase IS permanent source of truth
   - Current two-database setup doesn't reflect this
   - Cache pattern makes the architecture **explicit**

5. **Manageable Effort**
   - Phase 1 (refactor): 2 days
   - Phase 2 (migrate): 1 day
   - Phase 3 (test): 1 day
   - **Total: 4 days** (worth it for long-term benefits)

6. **Low Risk**
   - Can implement in parallel (don't break existing code)
   - Migration is one-time, automated
   - Extensive testing before switching
   - Rollback plan: keep old database as backup

---

### **Implementation Recommendation**

**Timeline:**
```
Week 1 (4 days):
  Day 1-2: Implement InMemoryGEOCache + UnifiedDB.get_complete_geo_data()
  Day 3:   Migrate data from old GEORegistry to UnifiedDatabase
  Day 4:   Test cache layer, verify all queries work

Week 2 (2 days):
  Day 5:   Update API endpoints to use cache
  Day 6:   Integration testing, documentation
  
→ Total: 6 days for production-ready implementation
```

**Start with Option A** (Python Dict + LRU):
- Simple, no dependencies
- Sufficient for current needs
- Can migrate to Redis later if needed

**Upgrade to Option B** (Redis) when:
- Multiple API servers needed
- Need distributed caching
- Cache persistence required

---

## Comparison: Current vs Proposed

### **Current Architecture (Two Databases)**

```
API Endpoint
    ↓
GEORegistry (SQLite)  →  5-10ms queries
    ↓
Response to Frontend

PipelineCoordinator
    ↓
UnifiedDatabase (SQLite)  →  Separate data
    ↓
Pipeline tracking

Problems:
❌ Data duplicated across two databases
❌ Sync issues (which is source of truth?)
❌ Two systems to maintain
❌ Unclear responsibility boundaries
```

### **Proposed Architecture (Cache + Database)**

```
API Endpoint
    ↓
GEORegistryCache (RAM)  →  0.1ms lookups
    ↓ (cache miss)
UnifiedDatabase (SQLite)  →  50ms query (only on miss)
    ↓
Response to Frontend

PipelineCoordinator
    ↓
UnifiedDatabase (SQLite)  →  Source of truth
    ↓
Pipeline tracking + data storage

Benefits:
✅ Single source of truth (UnifiedDatabase)
✅ Fast frontend queries (cache)
✅ Clear responsibilities (cache = speed, DB = persistence)
✅ No data duplication
✅ Scalable architecture
```

---

## Final Verdict

### **Implement the Cache Layer** 🎯

Your intuition is spot-on. This architecture is:
- **More correct** (matches intent: temporary vs permanent)
- **More performant** (50-100x faster queries)
- **More maintainable** (single source of truth)
- **More scalable** (can distribute cache later)

The 4-6 day investment will pay off in:
- Cleaner architecture
- Better performance
- Easier maintenance
- No data duplication concerns

**Next Steps:**
1. Approve this architectural direction
2. I'll implement Phase 1 (InMemoryGEOCache)
3. We'll test it alongside current system
4. Migrate data and switch over
5. Archive old GEORegistry database

**Question:** Should I proceed with implementation?
