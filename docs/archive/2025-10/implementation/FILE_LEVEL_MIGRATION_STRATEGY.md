# Complete File-Level Migration Strategy

**Date:** October 14, 2025  
**Goal:** Separate OLD vs NEW systems, integrate unified database, archive obsolete code  
**Strategy:** Surgical integration - no risky rewrites, clear migration path

---

## 📊 COMPLETE FILE INVENTORY

### **🟢 NEW System (Phases 1-5) - KEEP & INTEGRATE**

#### **Phase 1: Unified Database**
```
omics_oracle_v2/lib/storage/
├── unified_db.py              ✅ NEW - UnifiedDatabase class (8 tables)
├── schema.sql                 ✅ NEW - Database schema
└── models.py                  ✅ NEW - Type-safe dataclasses
```
**Status:** Complete, tested, committed (419d9cb)  
**Action:** ✅ KEEP - Integrate into SearchOrchestrator

---

#### **Phase 2: GEO-Centric Storage**
```
omics_oracle_v2/lib/storage/
├── geo_storage.py             ✅ NEW - GEOStorage class (SHA256, manifests)
└── integrity.py               ✅ NEW - Integrity verification
```
**Status:** Complete, tested, committed (0e90654)  
**Action:** ✅ KEEP - Integrate into SearchOrchestrator

---

#### **Phase 3: Pipeline Coordinator**
```
omics_oracle_v2/lib/pipelines/
└── coordinator.py             ✅ NEW - PipelineCoordinator (P1-P4 integration)
```
**Status:** Complete, tested, committed (9f2bddf)  
**Action:** ✅ KEEP - Add to SearchOrchestrator

---

#### **Phase 4: Queries & Analytics**
```
omics_oracle_v2/lib/storage/
├── queries.py                 ✅ NEW - DatabaseQueries (15+ methods)
└── analytics.py               ✅ NEW - Analytics (10+ methods)
```
**Status:** Complete, tested, committed (7b6dbc3)  
**Action:** ✅ KEEP - Already integrated with UnifiedDatabase

---

#### **Phase 5: Integration Tests**
```
tests/integration/
└── test_integration_workflow.py  ✅ NEW - End-to-end tests
```
**Status:** Complete, 10/11 passing (f664d5e)  
**Action:** ✅ KEEP - Validates entire system

---

### **🟡 OLD System (Pre-Phase 1) - KEEP BUT ISOLATED**

#### **SQLAlchemy Auth Database (User Management)**
```
omics_oracle_v2/database/
├── __init__.py                🟡 OLD - SQLAlchemy for auth ONLY
├── base.py                    🟡 OLD - SQLAlchemy Base
├── session.py                 🟡 OLD - Async sessions for auth
└── migrations/                🟡 OLD - Alembic migrations

omics_oracle_v2/auth/
├── models.py                  🟡 OLD - User, APIKey models (SQLAlchemy)
├── crud.py                    🟡 OLD - User CRUD operations
├── security.py                🟡 OLD - Password hashing, JWT
├── quota.py                   🟡 OLD - Rate limiting
└── schemas.py                 🟡 OLD - Pydantic models for auth
```

**Purpose:** User authentication, API keys, rate limiting  
**Database:** Separate SQLAlchemy async database for users  
**Status:** ✅ WORKING - Handles auth correctly  
**Action:** ✅ **KEEP SEPARATE** - Auth database is independent from search database

**Why Keep Separate?**
- Different concern: Users vs. Search Data
- Different ORM: SQLAlchemy (auth) vs. sqlite3 (search)
- Different tables: `users`, `api_keys` vs. `citations`, `pdfs`, etc.
- Already working: No need to change

**No Conflict:** Auth database and Search database are completely separate!

---

### **🔴 PROBLEMATIC Code - NEEDS INTEGRATION**

#### **Search Orchestrator (Currently Isolated)**
```
omics_oracle_v2/lib/search_orchestration/
├── orchestrator.py            🔴 PROBLEM - NO unified database integration
├── config.py                  🟡 NEEDS UPDATE - Add db_path, storage_path
└── models.py                  ✅ OK - SearchResult models
```

**Current State:**
- ✅ Parallel search (GEO + PubMed + OpenAlex)
- ✅ Redis caching
- ❌ NO UnifiedDatabase
- ❌ NO GEOStorage  
- ❌ NO PipelineCoordinator
- ❌ Results not persisted

**Action Required:**
```python
# orchestrator.py - ADD:
from omics_oracle_v2.lib.pipelines.coordinator import PipelineCoordinator

class SearchOrchestrator:
    def __init__(self, config):
        # ... existing code ...
        
        # ADD: Initialize coordinator for database persistence
        self.coordinator = PipelineCoordinator(
            db_path=config.db_path,
            storage_path=config.storage_path
        )
```

---

#### **Search Clients (Have Bugs)**
```
omics_oracle_v2/lib/search_engines/citations/
├── pubmed.py                  🔴 BUG - Line 475: await list error
└── openalex.py                🔴 BUG - Missing search_publications() method
```

**Action Required:**
- Fix PubMed: Remove `await` (method is synchronous)
- Fix OpenAlex: Use correct method name

---

### **🟢 GOOD Code - ALREADY WORKS**

#### **Search Engines (Work Correctly)**
```
omics_oracle_v2/lib/search_engines/
├── geo/
│   ├── client.py              ✅ WORKS - GEO search client
│   ├── query_builder.py       ✅ WORKS - GEO query optimization
│   └── models.py              ✅ WORKS - GEOSeriesMetadata
└── citations/
    ├── pubmed.py              ⚠️ WORKS but has async bug (fixable)
    └── openalex.py            ⚠️ WORKS but has method name bug (fixable)
```

**Action:** Keep, fix bugs only

---

#### **API Routes**
```
omics_oracle_v2/api/routes/
├── agents.py                  🔴 NEEDS UPDATE - Add database save calls
├── auth.py                    ✅ OK - Uses auth database (separate)
├── users.py                   ✅ OK - Uses auth database (separate)
├── health.py                  ✅ OK - Health checks
└── metrics.py                 ✅ OK - Prometheus metrics
```

**Action:**
- `agents.py`: Update to save results via PipelineCoordinator
- Others: No changes needed

---

## 🎯 MIGRATION STRATEGY

### **Key Principle: COEXISTENCE, NOT REPLACEMENT**

```
┌─────────────────────────────────────────────────────────────────┐
│  TWO DATABASES (DIFFERENT PURPOSES)                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Database 1: AUTH (SQLAlchemy)         ✅ KEEP AS-IS           │
│  ├── omics_oracle.db                                            │
│  ├── Tables: users, api_keys                                    │
│  └── Used by: auth/, api/routes/auth.py, api/routes/users.py   │
│                                                                  │
│  Database 2: SEARCH (sqlite3)          ✅ ADD TO ORCHESTRATOR  │
│  ├── data/database/omics_oracle.db                             │
│  ├── Tables: citations, urls, pdfs, enriched_content, etc.     │
│  └── Used by: SearchOrchestrator (NEW), PipelineCoordinator    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**No Conflict!** Two separate databases for two separate concerns.

---

## 📋 DETAILED MIGRATION STEPS

### **Step 1: Add Database Config** (5 min)

**File:** `omics_oracle_v2/lib/search_orchestration/config.py`

**Change:**
```python
@dataclass
class SearchConfig:
    # ... existing fields ...
    
    # ADD: Database paths for persistence
    db_path: str = "data/database/search_data.db"  # Search database
    storage_path: str = "data/pdfs"                # PDF storage
```

**Why:** Orchestrator needs to know where to store data

---

### **Step 2: Integrate PipelineCoordinator** (30 min)

**File:** `omics_oracle_v2/lib/search_orchestration/orchestrator.py`

**Changes:**

```python
# ADD import at top:
from omics_oracle_v2.lib.pipelines.coordinator import PipelineCoordinator

class SearchOrchestrator:
    def __init__(self, config: SearchConfig):
        # ... existing code (geo_client, pubmed_client, etc.) ...
        
        # ADD: Initialize pipeline coordinator for database persistence
        logger.info(f"Initializing PipelineCoordinator (db={config.db_path})")
        self.coordinator = PipelineCoordinator(
            db_path=config.db_path,
            storage_path=config.storage_path
        )
        logger.info("PipelineCoordinator initialized successfully")

    async def search(self, query, ...):
        # ... existing search logic ...
        
        # Get results (existing code)
        search_result = SearchResult(...)
        
        # ADD: Save to database AFTER search
        await self._persist_results(search_result)
        
        return search_result
    
    # ADD: New method to save results
    async def _persist_results(self, result: SearchResult) -> None:
        """Save search results to unified database."""
        if not result.geo_datasets:
            return
        
        logger.info(f"Persisting {len(result.geo_datasets)} datasets to database")
        
        for dataset in result.geo_datasets:
            try:
                # P1: Save citation discovery
                if dataset.pubmed_ids:
                    for pmid in dataset.pubmed_ids[:1]:  # Save primary PMID
                        self.coordinator.save_citation_discovery(
                            geo_id=dataset.geo_id,
                            pmid=pmid,
                            citation_data={
                                "title": dataset.title,
                                "summary": dataset.summary,
                                "organism": dataset.organism,
                                "platform": dataset.platforms[0] if dataset.platforms else None,
                                "sample_count": dataset.sample_count,
                                "publication_date": dataset.publication_date,
                            }
                        )
                        logger.debug(f"Saved citation: {dataset.geo_id} -> {pmid}")
            except Exception as e:
                logger.error(f"Failed to save {dataset.geo_id}: {e}")
        
        logger.info("Database persistence complete")
```

**Why:** Connects search results to database without breaking existing functionality

---

### **Step 3: Fix PubMed Client** (5 min)

**File:** `omics_oracle_v2/lib/search_orchestration/orchestrator.py`

**Find line ~475:**
```python
async def _search_pubmed(self, query: str, max_results: int):
    # BEFORE (BROKEN):
    results = await self.pubmed_client.search(query, max_results=max_results)
```

**Replace with:**
```python
async def _search_pubmed(self, query: str, max_results: int):
    # AFTER (FIXED):
    # Run synchronous method in executor to avoid blocking
    loop = asyncio.get_event_loop()
    results = await loop.run_in_executor(
        None,
        self.pubmed_client.search,
        query,
        max_results
    )
```

**Why:** `pubmed_client.search()` is synchronous, can't await it directly

---

### **Step 4: Fix OpenAlex Client** (10 min)

**First, check actual method name:**
```bash
grep -n "def.*search" omics_oracle_v2/lib/search_engines/citations/openalex.py
```

**File:** `omics_oracle_v2/lib/search_orchestration/orchestrator.py`

**Find line ~491:**
```python
async def _search_openalex(self, query: str, max_results: int):
    # BEFORE (BROKEN):
    results = await self.openalex_client.search_publications(query, max_results=max_results)
```

**Replace with (using correct method name):**
```python
async def _search_openalex(self, query: str, max_results: int):
    # AFTER (FIXED - check actual method name):
    results = await self.openalex_client.search(query, max_results=max_results)
    # OR if method is synchronous:
    loop = asyncio.get_event_loop()
    results = await loop.run_in_executor(
        None,
        self.openalex_client.search,
        query,
        max_results
    )
```

**Why:** Method name is incorrect

---

### **Step 5: Fix Resource Leaks** (15 min)

**File:** `omics_oracle_v2/lib/search_orchestration/orchestrator.py`

**Find `close()` method:**
```python
async def close(self):
    """Clean up resources."""
    logger.info("Closing SearchOrchestrator")
    
    # ADD: Close coordinator (cascades to database)
    if hasattr(self, 'coordinator') and self.coordinator:
        try:
            # PipelineCoordinator doesn't have close() yet, but database does
            if hasattr(self.coordinator.db, 'close'):
                self.coordinator.db.close()
            logger.debug("Database closed")
        except Exception as e:
            logger.warning(f"Database close failed: {e}")
    
    # Existing closes...
    if self.geo_client:
        await self.geo_client.close()
    
    if self.cache:
        await self.cache.close()
    
    logger.info("SearchOrchestrator closed")
```

**Why:** Prevents connection leaks

---

### **Step 6: Update API Route** (OPTIONAL - orchestrator handles it)

**File:** `omics_oracle_v2/api/routes/agents.py`

**No changes needed!** SearchOrchestrator now saves automatically.

**BUT** if you want explicit control:
```python
@router.post("/search", ...)
async def execute_search(request: SearchRequest):
    # ... existing code ...
    
    # Search (now saves to DB automatically)
    search_result = await pipeline.search(query=query, ...)
    
    # Optional: Return database IDs in response
    # (for future: allow users to retrieve saved searches)
    
    return SearchResponse(...)
```

---

## 📦 WHAT TO ARCHIVE (NOTHING!)

**Critical Decision:** We're NOT archiving anything because there are NO duplicate systems!

### **Why No Archiving Needed:**

1. **Auth Database (SQLAlchemy):** ✅ KEEP
   - Purpose: User management, API keys, rate limiting
   - Location: `omics_oracle_v2/database/`, `omics_oracle_v2/auth/`
   - Action: No changes

2. **Search Database (UnifiedDatabase):** ✅ ADD
   - Purpose: Search results, citations, PDFs, extraction
   - Location: `omics_oracle_v2/lib/storage/unified_db.py`
   - Action: Integrate into orchestrator

3. **SearchOrchestrator:** ✅ ENHANCE
   - Purpose: Coordinate searches
   - Location: `omics_oracle_v2/lib/search_orchestration/`
   - Action: Add database persistence (don't replace!)

**No Parallel Systems!** We're adding persistence to existing search orchestrator.

---

## 🎯 FILE CHANGE SUMMARY

### **Files to Modify (6 files)**

| File | Changes | Lines | Time |
|------|---------|-------|------|
| `search_orchestration/config.py` | Add db_path, storage_path | +2 | 5 min |
| `search_orchestration/orchestrator.py` | Add coordinator, persist method, fix bugs | +50 | 45 min |
| `search_engines/citations/pubmed.py` (or orchestrator) | Fix async issue | -1, +5 | 5 min |
| `search_engines/citations/openalex.py` (or orchestrator) | Fix method name | -1, +1 | 10 min |

**Total:** 4 files, ~58 lines changed, ~65 minutes

---

### **Files to Keep Unchanged (All Others)**

✅ UnifiedDatabase (lib/storage/unified_db.py)  
✅ GEOStorage (lib/storage/geo_storage.py)  
✅ PipelineCoordinator (lib/pipelines/coordinator.py)  
✅ DatabaseQueries (lib/storage/queries.py)  
✅ Analytics (lib/storage/analytics.py)  
✅ Auth system (database/, auth/)  
✅ API routes (except agents.py if optional changes)  
✅ All search clients (geo, pubmed, openalex)  

---

## ✅ VALIDATION PLAN

### **After Integration:**

1. **Test Auth Still Works**
   ```bash
   # Login should still work (uses separate auth database)
   curl -X POST http://localhost:8000/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","password":"test"}'
   ```

2. **Test Search Works**
   ```bash
   # Search and check logs for database saves
   # Frontend: "DNA methylation and brain cancer"
   tail -f logs/omics_api.log | grep "Persisting"
   ```

3. **Verify Database Writes**
   ```bash
   # Check unified database has data
   sqlite3 data/database/search_data.db "SELECT COUNT(*) FROM citations;"
   ```

4. **Test DatabaseQueries**
   ```python
   from omics_oracle_v2.lib.storage.queries import DatabaseQueries
   
   queries = DatabaseQueries("data/database/search_data.db")
   citations = queries.get_citations_for_geo("GSE12345")
   print(f"Found {len(citations)} citations")
   ```

---

## 🚀 EXECUTION ORDER

### **Phase A: Quick Wins (30 min)**

1. ✅ Fix PubMed bug (5 min)
2. ✅ Fix OpenAlex bug (10 min)
3. ✅ Fix resource leaks (15 min)
4. ✅ Test frontend search (10 min)

**Checkpoint:** Frontend search works without errors

---

### **Phase B: Database Integration (1 hour)**

1. ✅ Add config fields (5 min)
2. ✅ Add PipelineCoordinator to orchestrator (30 min)
3. ✅ Add _persist_results() method (15 min)
4. ✅ Test database writes (10 min)

**Checkpoint:** Search results persist to database

---

### **Phase C: Validation (30 min)**

1. ✅ Test auth still works (5 min)
2. ✅ Test search + database (10 min)
3. ✅ Query database with DatabaseQueries (10 min)
4. ✅ Check analytics work (5 min)

**Checkpoint:** All systems working together

---

## 📊 FINAL ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────┐
│  Frontend Dashboard                                             │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│  API Routes                                                     │
│  ├─→ /api/auth/*       → Auth Database (SQLAlchemy)           │
│  └─→ /api/agents/search → SearchOrchestrator                   │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│  SearchOrchestrator (ENHANCED)                                  │
│  ├─→ Parallel Search (GEO + PubMed + OpenAlex)                │
│  ├─→ Redis Caching                                             │
│  └─→ PipelineCoordinator (NEW!)                               │
│      ├─→ UnifiedDatabase (8 tables)                           │
│      └─→ GEOStorage (SHA256, manifests)                       │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│  TWO DATABASES (COEXIST)                                        │
│  ├─→ omics_oracle.db (Auth - SQLAlchemy)                      │
│  └─→ data/database/search_data.db (Search - sqlite3)          │
└─────────────────────────────────────────────────────────────────┘
```

**Key Points:**
- ✅ No parallel systems - single enhanced orchestrator
- ✅ Two databases for two purposes (auth vs. search)
- ✅ All Phases 1-5 integrated
- ✅ No old code to archive (auth system stays)
- ✅ Minimal changes (4 files, ~60 minutes)

---

## 🎯 READY TO PROCEED?

**I will:**
1. Make the 4 file changes (surgical, targeted)
2. Test each change incrementally
3. Verify database integration works
4. Then proceed to production validation

**No risky rewrites, no archiving needed - just clean integration!**

Shall I start with Phase A (bug fixes)?
