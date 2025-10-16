# ALL Legacy Code Removed - Cache-Only Architecture

**Date:** October 15, 2025  
**Status:** ✅ COMPLETE - No backward compatibility, cache-only

---

## Summary

**USER REQUEST:** "I don't like keeping old code once new system is ready. No need for backward compatibility. I would prefer failure and fix issues than getting confused."

**ACTION TAKEN:** Removed ALL legacy SQLite code immediately. GEORegistry is now **cache-only** with NO fallback.

---

## Files Completely Rewritten

### 1. ✅ `geo_registry.py` - Cache-Only (80 LOC, down from 763 LOC)

**Before:** 763 lines with SQLite schema, queries, deprecated methods, backward compatibility  
**After:** 80 lines - pure cache wrapper

**Removed:**
- ❌ SQLite connection (`self.conn`)
- ❌ `_init_schema()` method (200+ LOC of SQL)
- ❌ `register_geo_dataset()` - direct DB writes
- ❌ `register_publication()` - direct DB writes
- ❌ `link_geo_to_publication()` - direct DB writes  
- ❌ `_legacy_get_complete_geo_data()` - deprecated method
- ❌ `_get_download_history()` - SQLite query
- ❌ `get_summary()` - SQLite aggregation
- ❌ `close()` - connection cleanup
- ❌ `@deprecated` decorator
- ❌ `use_cache` parameter
- ❌ ALL backward compatibility code

**New Implementation:**
```python
class GEORegistry:
    """Cache-first registry for GEO datasets."""
    
    def __init__(self, unified_db_path="data/database/omics_oracle.db", redis_ttl_days=7):
        """Initialize with GEOCache only."""
        unified_db = UnifiedDatabase(unified_db_path)
        self.cache = GEOCache(unified_db, redis_ttl_days=redis_ttl_days)
    
    async def get_complete_geo_data(self, geo_id: str):
        """Get data from cache (Redis → UnifiedDB)."""
        return await self.cache.get(geo_id)
    
    async def invalidate_cache(self, geo_id: str):
        """Invalidate cache entry."""
        return await self.cache.invalidate(geo_id)
    
    async def get_stats(self):
        """Get cache statistics."""
        return await self.cache.get_stats()
    
    async def warm_up(self, geo_ids: List[str]):
        """Pre-populate cache."""
        return await self.cache.warm_up(geo_ids)
```

---

## Architecture Comparison

### Before (Messy):
```
GEORegistry
    ├── if use_cache:
    │   ├── Try GEOCache
    │   └── Fallback to SQLite
    └── else:
        └── Direct SQLite queries (deprecated)

SQLite Methods (500+ LOC):
    - _init_schema()
    - register_geo_dataset()
    - register_publication()
    - link_geo_to_publication()
    - _legacy_get_complete_geo_data()
    - _get_download_history()
    - get_summary()
```

### After (Clean):
```
GEORegistry (80 LOC)
    ↓
GEOCache
    ├── Redis (hot, <1ms)
    └── UnifiedDB (warm, ~50ms)

ALL operations async.
NO fallback.
NO legacy code.
```

---

## Breaking Changes

### ✅ INTENTIONAL - User Requested

**Old code will FAIL immediately:**
```python
# This will raise AttributeError
registry = GEORegistry()
registry.register_geo_dataset("GSE123", {...})  # ❌ Method doesn't exist
registry.conn.execute(...)  # ❌ self.conn doesn't exist
```

**New code (cache-only):**
```python
registry = GEORegistry()
data = await registry.get_complete_geo_data("GSE123")  # ✅ Works
await registry.invalidate_cache("GSE123")  # ✅ Works
```

---

## Migration Impact

### Before Migration (What Breaks):

**API endpoints using GEORegistry:**
- ❌ Any code calling `register_geo_dataset()` → Method removed
- ❌ Any code calling `link_geo_to_publication()` → Method removed
- ❌ Any code accessing `registry.conn` → Attribute removed
- ❌ Sync calls to `get_complete_geo_data()` → Now async only

### After Migration (What Works):

**All GEO data MUST be in UnifiedDB:**
1. ✅ `await registry.get_complete_geo_data(geo_id)` → Works if data in UnifiedDB
2. ✅ Cache hit → Redis returns data (<1ms)
3. ✅ Cache miss → UnifiedDB returns data (~50ms)
4. ❌ Data not in UnifiedDB → Returns `None` (FAIL FAST)

---

## Data Migration Required

**CRITICAL:** Old SQLite database (data/omics_oracle.db) is **NO LONGER ACCESSED**.

**Migration Script Required:**
```python
# scripts/migrate_georegistry_to_unified.py

from omics_oracle_v2.lib.pipelines.storage.unified_db import UnifiedDatabase
import sqlite3
import json

# Connect to OLD database
old_conn = sqlite3.connect("data/omics_oracle.db")
old_conn.row_factory = sqlite3.Row

# Connect to NEW database
unified_db = UnifiedDatabase("data/database/omics_oracle.db")

# Migrate geo_datasets table
for row in old_conn.execute("SELECT * FROM geo_datasets"):
    geo_data = dict(row)
    metadata = json.loads(geo_data['metadata'])
    
    # Insert into UnifiedDatabase
    unified_db.insert_geo_dataset(GEODataset(
        geo_id=geo_data['geo_id'],
        title=geo_data['title'],
        summary=geo_data['summary'],
        organism=geo_data['organism'],
        platform=geo_data['platform'],
        # ... etc
    ))

print("Migration complete!")
old_conn.close()
```

---

## Files to Delete NOW

**Since we removed backward compatibility, we can delete immediately:**

1. ✅ **OLD DATABASE** (if migration done):
   ```bash
   rm data/omics_oracle.db  # 15 MB
   ```

2. ✅ **OLD DOCUMENTATION:**
   ```bash
   mv docs/DATABASE_SYSTEMS_COMPARISON.md archive/proposals/
   mv docs/CACHE_LAYER_ARCHITECTURE_PROPOSAL.md archive/proposals/
   ```

3. ✅ **CLEANUP TRACKER** (no longer needed):
   ```bash
   rm docs/GEOCACHE_CLEANUP_TRACKER.md  # No migration period
   ```

---

## Testing Strategy

### Unit Tests (Task 4):
```python
import pytest
from omics_oracle_v2.lib.pipelines.storage.registry import GEORegistry

@pytest.mark.asyncio
async def test_cache_only_no_fallback():
    """Test that GEORegistry is cache-only with no fallback."""
    registry = GEORegistry()
    
    # Should not have SQLite connection
    assert not hasattr(registry, 'conn')
    
    # Should not have legacy methods
    assert not hasattr(registry, 'register_geo_dataset')
    assert not hasattr(registry, '_legacy_get_complete_geo_data')
    
    # Should only have cache
    assert hasattr(registry, 'cache')
    assert registry.cache is not None

@pytest.mark.asyncio
async def test_get_complete_geo_data_cache_miss():
    """Test that missing data returns None (no fallback)."""
    registry = GEORegistry()
    
    # Non-existent GEO should return None (fail fast)
    data = await registry.get_complete_geo_data("GSE_NONEXISTENT")
    assert data is None
```

### Integration Tests (Task 5):
```python
# Check that API endpoints handle async correctly
async def test_api_endpoint_async():
    registry = get_registry()
    
    # This should work (async)
    data = await registry.get_complete_geo_data("GSE123456")
    
    # This should fail (sync call to async method)
    with pytest.raises(TypeError):
        data = registry.get_complete_geo_data("GSE123456")  # Missing await
```

---

## Success Metrics

### ✅ Clean Architecture Achieved:
- [x] 90% code reduction (763 LOC → 80 LOC)
- [x] No backward compatibility
- [x] No legacy fallback
- [x] Cache-only architecture
- [x] Async-first API
- [x] Fail-fast on missing data

### ⏳ Migration Pending:
- [ ] Data migration script created
- [ ] All GEO data migrated to UnifiedDB
- [ ] API endpoints updated to use `await`
- [ ] Unit tests pass
- [ ] Integration tests pass

---

## Breaking Changes Summary

| Feature | Before | After | Impact |
|---------|--------|-------|--------|
| `__init__` | `use_cache` param | Removed | No legacy mode |
| `get_complete_geo_data()` | Sync + Async | **Async only** | Must use `await` |
| `register_geo_dataset()` | Exists | **REMOVED** | Use UnifiedDB directly |
| `register_publication()` | Exists | **REMOVED** | Use UnifiedDB directly |
| `link_geo_to_publication()` | Exists | **REMOVED** | Use UnifiedDB directly |
| `self.conn` | SQLite connection | **REMOVED** | No direct DB access |
| `_init_schema()` | SQL schema setup | **REMOVED** | Use UnifiedDB schema |
| Fallback | SQLite fallback | **REMOVED** | Cache-only |
| Error handling | Silent fallback | **Fail fast** | Returns `None` if not found |

---

## User Request Honored

> "I don't like keeping old code once new system is ready. No need for backward compatibility. I would prefer failure and fix issues than getting confused. Either remove it now or later whenever is appropriate time after next steps."

**DONE:** Removed now. No waiting. No backward compatibility. Clean cache-only architecture.

**Philosophy:**
- ✅ Fail fast, fix forward
- ✅ No confusing dual-system code
- ✅ Clean architecture over backward compatibility
- ✅ Force migration, don't allow lazy fallback

---

## Next Steps

### Immediate (This Week):
1. **Create migration script:** `scripts/migrate_georegistry_to_unified.py`
2. **Run migration:** Move data from old DB to UnifiedDB
3. **Verify data integrity:** Count records, spot-check
4. **Update API endpoints:** Add `await` to all registry calls
5. **Run tests:** Ensure no old code references

### Cleanup (After Migration):
1. **Delete:** `data/omics_oracle.db`
2. **Archive:** Old proposal docs
3. **Update:** README and documentation

---

## Summary

**Removed:** 683 lines of legacy SQLite code  
**Kept:** 80 lines of clean cache wrapper  
**Result:** Simple, fast, cache-only architecture

**No backward compatibility = No confusion** ✅
