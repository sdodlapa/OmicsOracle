# PDF Download Failure Investigation & Action Plan
**Date:** October 16, 2025  
**Issue:** "⚠️ No papers downloaded" despite showing "25 citations in DB"  
**Reporter:** User testing GSE570 after auto-discovery bug fixes

---

## 🔍 Issue Summary

User clicked "Download Papers (25 in DB)" for GSE570 and received:
```
⚠️ No papers downloaded
Status: not_downloaded
AI Analysis will use GEO summary only.
```

**Critical Discovery:** The "25 citations in DB" shown on the dashboard is **PHANTOM DATA**. The actual database is empty.

---

## 🐛 Root Causes Identified

### **Issue 1: FulltextService Is a Stub (CRITICAL)**
**File:** `omics_oracle_v2/services/fulltext_service.py`  
**Line:** 88-91

```python
# NOTE: The full implementation would go here
# For now, returning the datasets as-is to get the structure working
# The complete logic will be copied from agents.py in the next iteration

return datasets  # ← Returns input unchanged!
```

**Impact:** 
- `/api/agents/enrich-fulltext` endpoint does NOTHING
- Datasets are returned unmodified (no PDFs downloaded)
- This explains why status is always "not_downloaded"

**When Introduced:** During service refactoring (exact commit TBD)

---

### **Issue 2: Search Results NOT Persisted to Database (CRITICAL)**

**Evidence:**
```bash
Database check shows:
- geo_datasets: 0 rows  ← GSE570 missing
- universal_identifiers: 4 rows  ← All for GSE281238, not GSE570
- pdf_acquisition: 0 rows
```

**But dashboard shows:** "GSE570 - 25 citations in database"

**How is this possible?**

```
Search Flow Analysis:
=====================

1. User searches → SearchOrchestrator.search()
2. Orchestrator calls GEO API → Gets GSE570 metadata
3. GEO data cached in Redis (hot tier) via GEOCache
4. Auto-discovery triggered → Citation APIs called
5. Citations cached in discovery_cache.db (30-day TTL)
6. Data returned to frontend from Redis cache
7. ❌ NEVER persisted to omics_oracle.db (SQLite)

Result: Data visible in UI but database empty!
```

**GEOCache.get() Logic:**
```python
async def get(self, geo_id: str) -> Optional[Dict[str, Any]]:
    # Tier 1: Check Redis hot cache (IN-MEMORY)
    if self.redis_cache:
        cached_data = await self.redis_cache.get_geo_metadata(geo_id)
        if cached_data is not None:
            return cached_data  # ← Returns from Redis
    
    # Tier 2: Check UnifiedDB (SQLite) 
    db_data = self.db.get_geo_dataset(geo_id)
    if db_data:
        # Promote to Redis
        await self.redis_cache.set_geo_metadata(geo_id, db_data)
        return db_data
    
    # Tier 3: Auto-discover if missing
    return await self._auto_discover_and_populate(geo_id)
```

**The Problem:**
- Redis cache is **ephemeral** (cleared on server restart)
- Data only persists in Redis, not SQLite
- SearchService doesn't call `insert_geo_dataset()`
- Auto-discovery caches results but doesn't persist to main DB

---

### **Issue 3: Database Architecture Confusion**

**Two Databases:**
1. **omics_oracle.db** (Main) - SHOULD contain application data
2. **discovery_cache.db** (Cache) - API response cache (30-day TTL)

**Current State:**
- Search results stored in Redis (volatile)
- Citations cached in discovery_cache.db (temporary)
- Main database empty (defeats persistence purpose)

**Architecture Mismatch:**
```
Expected Flow:
Search → Redis (hot) → SQLite (persistent) → Display

Actual Flow:
Search → Redis (hot) → Display
         ↓
         SQLite (NEVER WRITTEN)
```

---

## 📊 Data Flow Analysis

### **Where "25 citations" comes from:**

```python
# Dashboard shows citation count from DatasetResponse model
{
  "geo_id": "GSE570",
  "pubmed_ids": ["12345", "67890", ...],  # 25 IDs
  "publication_count": 25,  # ← Derived from len(pubmed_ids)
  "fulltext_status": "not_downloaded"
}
```

**Source of pubmed_ids:**
1. Auto-discovery calls Semantic Scholar API
2. API response cached in `discovery_cache.db`
3. Response includes list of citing papers
4. List returned to frontend via Redis cache
5. Frontend counts array length → "25 citations in DB"

**The Lie:** "in DB" implies persistent storage, but it's just Redis cache!

---

## 🎯 Action Plan

### **Phase 1: Fix FulltextService (IMMEDIATE - Blocks PDF Downloads)**

**Priority:** 🔴 CRITICAL  
**Files:**
- `omics_oracle_v2/services/fulltext_service.py`

**Actions:**
1. ✅ Identify where complete implementation exists (likely in `agents.py` history)
2. ✅ Copy full PDF download logic to `enrich_datasets()` method
3. ✅ Test with GSE570 to verify PDFs download
4. ✅ Validate error handling for paywall failures
5. ✅ Commit with clear message about fixing stub implementation

**Expected Outcome:**
- Clicking "Download Papers" actually downloads PDFs
- Status updates to "success", "partial", or "failed" (not stuck at "not_downloaded")
- PDFs saved to `data/pdfs/` directory
- `pdf_acquisition` table populated

**Estimated Time:** 30 minutes  
**Risk:** Low (copying existing working code)

---

### **Phase 2: Fix Data Persistence (HIGH PRIORITY)**

**Priority:** 🟠 HIGH  
**Files:**
- `omics_oracle_v2/lib/search_engines/orchestrator.py`
- `omics_oracle_v2/services/search_service.py`
- `omics_oracle_v2/lib/pipelines/storage/registry/geo_cache.py`

**Actions:**
1. ✅ Add `insert_geo_dataset()` call in SearchOrchestrator after GEO fetch
2. ✅ Add `insert_publication()` calls for each citation discovered
3. ✅ Modify `_auto_discover_and_populate()` to persist to SQLite, not just Redis
4. ✅ Add transaction handling to ensure atomic writes
5. ✅ Test with fresh search to verify persistence
6. ✅ Restart server and verify data survives (not in Redis)

**Expected Outcome:**
- Search results persist across server restarts
- Database populated: geo_datasets, universal_identifiers tables
- "25 citations in DB" reflects ACTUAL database, not cache
- Redis becomes true cache layer, not primary storage

**Estimated Time:** 1-2 hours  
**Risk:** Medium (changes core data flow)

---

### **Phase 3: Validate Auto-Discovery Fix (VERIFICATION)**

**Priority:** 🟡 MEDIUM  
**Files:**
- `test_auto_discovery_fix.py` (existing)

**Actions:**
1. ✅ Run test script after Phase 1+2 fixes
2. ✅ Search for dataset with known citations (e.g., GSE570)
3. ✅ Verify auto-discovery populates `universal_identifiers`
4. ✅ Verify `identifier_utils.now_iso()` fix works (from yesterday)
5. ✅ Check that citation counts match between Redis and SQLite

**Expected Outcome:**
- Auto-discovery works end-to-end
- Citations persist to database
- No silent failures from `now_iso()` bug

**Estimated Time:** 30 minutes  
**Risk:** Low (validation only)

---

### **Phase 4: Update Dashboard Labels (UX FIX)**

**Priority:** 🟢 LOW  
**Files:**
- `omics_oracle_v2/api/static/dashboard_v2.html`

**Actions:**
1. Change "25 citations in DB" to "25 citations found"
2. Add tooltip: "Citations discovered via API (may not be downloaded)"
3. After Phase 2: Change back to "in DB" (now accurate)
4. Add status indicators:
   - 🔍 Discovered (in cache)
   - 💾 Saved (in database)
   - 📥 Downloaded (PDFs on disk)

**Expected Outcome:**
- Clear distinction between discovered vs. saved vs. downloaded
- No user confusion about data persistence
- Better visibility into pipeline stages

**Estimated Time:** 15 minutes  
**Risk:** None (cosmetic only)

---

### **Phase 5: Document Data Flow (ARCHITECTURAL)**

**Priority:** 🟢 LOW  
**Files:**
- `docs/DATA_FLOW_ARCHITECTURE.md` (new)
- Update `COMPREHENSIVE_ARCHITECTURE.md`

**Actions:**
1. ✅ Document 3-tier caching: Redis → SQLite → Disk
2. ✅ Clarify when each tier is populated
3. ✅ Explain persistence guarantees (Redis volatile, SQLite persistent)
4. ✅ Add diagrams for search, discovery, and download flows
5. ✅ Include decision tree: When to use which database?

**Expected Outcome:**
- Clear architecture reference for future development
- Prevents confusion like "why two databases?"
- Documents expected vs. actual behavior

**Estimated Time:** 45 minutes  
**Risk:** None (documentation only)

---

## 🧪 Testing Strategy

### **Test 1: Fresh Search → PDF Download**
```bash
1. Clear all caches: rm -rf data/database/* data/cache/*
2. Start server
3. Search for "GSE570"
4. Verify: geo_datasets table has 1 row (GSE570)
5. Verify: universal_identifiers has ~25 rows
6. Click "Download Papers"
7. Verify: PDFs appear in data/pdfs/GSE570/
8. Verify: pdf_acquisition table populated
9. Verify: Status updates to "success" or "partial"
```

### **Test 2: Server Restart → Data Persists**
```bash
1. After Test 1, restart server
2. Search for "GSE570" again
3. Verify: Results appear immediately (from SQLite, not re-fetched)
4. Verify: Redis cache repopulated from SQLite
5. Verify: Citation counts match original search
```

### **Test 3: Auto-Discovery Trigger**
```bash
1. Search for obscure dataset (e.g., GSE1261)
2. Verify: Auto-discovery runs (check logs)
3. Verify: Citations inserted to universal_identifiers
4. Verify: No `identifier_utils.now_iso()` errors
5. Verify: url_discovered_at timestamp populated correctly
```

### **Test 4: PDF Download Error Handling**
```bash
1. Search for dataset behind strict paywall
2. Click "Download Papers"
3. Verify: Graceful failure with detailed error modal
4. Verify: Status = "failed" (not stuck at "not_downloaded")
5. Verify: Error logged with all source attempts
```

---

## 📝 Implementation Checklist

### **Phase 1: FulltextService Fix**
- [ ] Find complete implementation (check `agents.py` or git history)
- [ ] Copy full logic to `fulltext_service.py` 
- [ ] Add proper error handling and logging
- [ ] Test PDF download with GSE570
- [ ] Commit: `fix: implement complete PDF download logic in FulltextService`

### **Phase 2: Data Persistence Fix**
- [ ] Add `insert_geo_dataset()` in SearchOrchestrator
- [ ] Add `insert_publication()` in auto-discovery
- [ ] Update `_auto_discover_and_populate()` to use SQLite
- [ ] Add transaction handling
- [ ] Test persistence across server restart
- [ ] Commit: `fix: persist search results to database, not just Redis`

### **Phase 3: Validation**
- [ ] Run `test_auto_discovery_fix.py` 
- [ ] Verify citation counts match
- [ ] Check no silent failures in logs
- [ ] Document results in `AUTO_DISCOVERY_VALIDATION_RESULTS.md`

### **Phase 4: Dashboard UX**
- [ ] Update citation count labels
- [ ] Add status indicators (discovered/saved/downloaded)
- [ ] Add tooltips for clarity
- [ ] Commit: `feat: improve citation status visibility in dashboard`

### **Phase 5: Documentation**
- [ ] Create `DATA_FLOW_ARCHITECTURE.md`
- [ ] Add diagrams for 3-tier caching
- [ ] Document persistence guarantees
- [ ] Update `COMPREHENSIVE_ARCHITECTURE.md`

---

## 🚨 Critical Questions to Answer

### **Q1: Why was FulltextService left as a stub?**
- Check git history for refactoring commit
- Determine if this was intentional (WIP) or accidental
- If WIP, find the complete implementation source

### **Q2: Is Redis cache being used correctly?**
- Redis is **volatile** (clears on restart)
- Should be **cache only**, not primary storage
- Need to verify: Does auto-discovery write to SQLite or just Redis?

### **Q3: What's the intended data flow?**
```
Option A (Current - WRONG):
Search → Redis → Display
         ↓
         (SQLite never written)

Option B (Correct):
Search → SQLite → Redis → Display
         ↓        ↑
         (persist) (cache)
```

### **Q4: Should discovery_cache.db be merged into main DB?**
- Pro: Single source of truth, simpler architecture
- Con: Mixes persistent data with temporary cache (30-day TTL)
- **Decision:** Keep separate (cache can be safely deleted)

---

## 📦 Expected Deliverables

1. ✅ **Working PDF Download** - FulltextService fully implemented
2. ✅ **Persistent Data** - Search results survive server restart
3. ✅ **Accurate UI** - Citation counts reflect actual database
4. ✅ **Auto-Discovery Validation** - End-to-end test passes
5. ✅ **Clear Documentation** - Data flow architecture documented
6. ✅ **Test Results** - All 4 test scenarios pass

---

## 🎯 Success Criteria

**After implementing all fixes:**

- [ ] User searches for GSE570 → Gets results
- [ ] User clicks "Download Papers" → PDFs download successfully
- [ ] Status updates to "success" (not stuck at "not_downloaded")
- [ ] Server restart → Data persists (geo_datasets has rows)
- [ ] Database query shows: geo_datasets (>0), universal_identifiers (>0), pdf_acquisition (>0)
- [ ] "25 citations in DB" reflects ACTUAL database count
- [ ] Auto-discovery works without errors
- [ ] All logs show successful pipeline stages (discovery → URL → download)

---

## 🔄 Next Immediate Action

**START HERE:** Fix FulltextService stub implementation

```bash
# 1. Check what's in the original agents.py endpoint
grep -A 200 "async def enrich_with_fulltext" omics_oracle_v2/api/routes/agents.py

# 2. If implementation is there, copy it to fulltext_service.py
# 3. If not, check git history for when it was removed

# 4. Test the fix:
# - Start server
# - Search for GSE570
# - Click "Download Papers"
# - Verify PDFs download to data/pdfs/GSE570/
# - Check pdf_acquisition table populated
```

**ETA to working system:** 2-3 hours (all phases)

---

## 📌 Summary

**The core issue is two-fold:**

1. **FulltextService is a stub** → PDF downloads do nothing
2. **Search results only in Redis** → No persistence, phantom data

**Both are fixable in one session** by:
- Implementing complete PDF download logic (30 min)
- Adding database persistence to search flow (1-2 hours)
- Validating with end-to-end tests (30 min)

**After fixes, the system will:**
- Download PDFs when user clicks button ✅
- Persist data to SQLite (survive restarts) ✅
- Show accurate citation counts (from database) ✅
- Have clear data flow (Redis cache → SQLite persist) ✅
