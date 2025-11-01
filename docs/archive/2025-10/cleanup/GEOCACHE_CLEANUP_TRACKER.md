# GEOCache Implementation - Cleanup Tracker

**Date Started:** October 15, 2025  
**Implementation:** Option 1 - 2-Tier Cache (Redis → UnifiedDB)  
**Pattern:** Copy ParsedCache architecture

---

## ⚠️ IMPORTANT: Single Plan - No Deviations

**ONLY implement Option 1. All other proposals are ARCHIVED.**

- ❌ Option 2 (Extend RedisCache) - REJECTED
- ❌ Option 3 (In-memory LRU) - REJECTED  
- ❌ Hybrid integration from DATABASE_SYSTEMS_COMPARISON.md - ARCHIVED
- ❌ Direct merge approaches - ARCHIVED

**This document tracks what to DELETE after implementation succeeds.**

---

## Files Being Created (NEW - Keep)

1. ✅ `lib/pipelines/storage/registry/geo_cache.py` (NEW)
   - 2-tier cache implementation
   - Keep permanently

2. ✅ `tests/lib/storage/test_geo_cache.py` (NEW)
   - Unit tests for cache
   - Keep permanently

3. ✅ `docs/GEOCACHE_IMPLEMENTATION.md` (NEW)
   - Implementation guide
   - Keep permanently

---

## Files Being Modified (REVIEW after completion)

1. 🔄 `lib/pipelines/storage/unified_db.py`
   - ADD: `get_complete_geo_data()` method
   - Keep new code

2. 🔄 `lib/pipelines/storage/registry/geo_registry.py`
   - ADD: `self.cache = GEOCache(...)` integration
   - MARK: Old direct DB methods with `@deprecated`
   - DO NOT DELETE YET - needed for migration

3. 🔄 `lib/pipelines/storage/registry/__init__.py`
   - ADD: Import GEOCache
   - Keep

---

## Files/Databases to DELETE After Migration ❌

### **Phase 1: After GEOCache Working (Week 1)**

Mark as deprecated but keep running:
- ⚠️ `data/omics_oracle.db` - Old GEORegistry DB (15 MB)
  - **Action:** Keep for 1 week, verify all data in UnifiedDB
  - **Delete after:** Successful data migration + 1 week validation

### **Phase 2: After Data Migration Complete (Week 2)**

1. ❌ **DELETE DATABASE:**
   ```bash
   # Backup first!
   cp data/omics_oracle.db data/backup/omics_oracle.db.backup_$(date +%Y%m%d)
   
   # Then delete
   rm data/omics_oracle.db
   ```

2. ❌ **DELETE OLD METHODS in geo_registry.py:**
   - Remove direct SQLite query methods
   - Keep only cache wrapper methods
   - Shrink file from 553 LOC → ~150 LOC

3. ❌ **DELETE DOCUMENTATION (outdated proposals):**
   ```bash
   # Archive old proposals
   mv docs/DATABASE_SYSTEMS_COMPARISON.md archive/proposals/
   mv docs/CACHE_LAYER_ARCHITECTURE_PROPOSAL.md archive/proposals/
   
   # These were brainstorming - no longer relevant
   ```

4. ❌ **UPDATE CONFIG FILES:**
   - Remove `data/omics_oracle.db` from backup scripts
   - Update .gitignore if needed

---

## Migration Checklist

### **Pre-Migration Validation**

- [ ] GEOCache tests pass (100% coverage)
- [ ] Performance benchmarks meet targets (cache hit <1ms)
- [ ] UnifiedDB has `get_complete_geo_data()` working
- [ ] Fallback to memory works when Redis down

### **Data Migration Steps**

1. [ ] **Export** data from `data/omics_oracle.db`:
   ```python
   # Script: scripts/migrate_georegistry_to_unified.py
   old_registry = GEORegistry("data/omics_oracle.db")
   unified_db = UnifiedDatabase()
   
   # For each GEO in old registry:
   for geo_id in old_registry.get_all_geo_ids():
       data = old_registry.get_complete_geo_data(geo_id)
       unified_db.import_geo_data(geo_id, data)
   ```

2. [ ] **Verify** data integrity:
   ```python
   # Count records
   old_count = old_registry.count_geo_datasets()
   new_count = unified_db.count_geo_datasets()
   assert old_count == new_count
   
   # Spot check 100 random GEOs
   for geo_id in random.sample(all_geos, 100):
       old_data = old_registry.get_complete_geo_data(geo_id)
       new_data = unified_db.get_complete_geo_data(geo_id)
       assert old_data == new_data
   ```

3. [ ] **Switch** API to use new cache:
   ```python
   # lib/pipelines/storage/registry/__init__.py
   # OLD:
   # _registry_instance = GEORegistry("data/omics_oracle.db")
   
   # NEW:
   from .geo_cache import GEOCache
   from ..unified_db import UnifiedDatabase
   
   _unified_db = UnifiedDatabase()
   _registry_instance = GEOCache(_unified_db)
   ```

4. [ ] **Monitor** for 1 week:
   - Check cache hit rates (should be >80%)
   - Monitor error logs
   - Verify no queries to old DB

5. [ ] **Backup** old database:
   ```bash
   cp data/omics_oracle.db data/backup/omics_oracle.db.final_backup
   ```

6. [ ] **DELETE** old database:
   ```bash
   rm data/omics_oracle.db
   ```

### **Post-Migration Cleanup**

- [ ] Remove old GEORegistry DB methods (keep only cache wrappers)
- [ ] Update documentation
- [ ] Remove from backup scripts
- [ ] Archive old proposal documents
- [ ] Update README.md if mentions old DB

---

## Rollback Plan (If Something Goes Wrong)

1. **Revert code:**
   ```bash
   git revert <commit-hash>
   ```

2. **Switch back to old registry:**
   ```python
   # Restore old __init__.py
   _registry_instance = GEORegistry("data/omics_oracle.db")
   ```

3. **Restore database if deleted:**
   ```bash
   cp data/backup/omics_oracle.db.backup_YYYYMMDD data/omics_oracle.db
   ```

---

## Success Criteria

**GEOCache implementation is successful when:**

✅ All unit tests pass  
✅ Cache hit rate >80% in production  
✅ Cache hit latency <1ms  
✅ Cache miss latency <50ms  
✅ No errors for 1 week  
✅ Old database has zero queries  
✅ Data integrity verified (old vs new matches)  

**Only then proceed with deletion.**

---

## Timeline

- **Day 1-2:** Implement GEOCache
- **Day 3:** Write tests, benchmarks
- **Day 4:** Data migration
- **Day 5-11:** Monitor (1 week)
- **Day 12:** DELETE old database and code

---

## Notes

- **DO NOT delete anything until migration validated**
- **DO NOT implement multiple approaches simultaneously**
- **DO NOT start refactoring /enrich-fulltext until this is done**
- Keep this document updated as we progress
