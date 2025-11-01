# Migration Visual Summary

## 🎯 THE KEY INSIGHT

**There are NO parallel systems to archive!**

We have:
- ✅ **Auth System** (SQLAlchemy) - for users, API keys → KEEP AS-IS
- ✅ **Search Components** (Phases 1-5) - for search data → ADD TO ORCHESTRATOR

They don't overlap - they're complementary!

---

## 📊 CURRENT STATE vs TARGET STATE

### BEFORE (Now)
```
Frontend Query
      ↓
SearchOrchestrator
  ├─→ GEO Search    ✅
  ├─→ PubMed Search ❌ (broken)
  ├─→ OpenAlex      ❌ (broken)
  └─→ Results → Frontend
      
❌ NO DATABASE PERSISTENCE
❌ Phases 1-5 sit UNUSED

Separate:
Auth DB (users) ✅ Working
```

### AFTER (Target)
```
Frontend Query
      ↓
SearchOrchestrator
  ├─→ GEO Search         ✅
  ├─→ PubMed Search      ✅ FIXED
  ├─→ OpenAlex           ✅ FIXED
  └─→ PipelineCoordinator (NEW!)
      ├─→ UnifiedDatabase (8 tables)
      └─→ GEOStorage (files)
      
✅ DATABASE PERSISTENCE
✅ Phases 1-5 INTEGRATED

Separate (unchanged):
Auth DB (users) ✅ Working
```

---

## 🗂️ FILE CHANGES (4 files only)

```
1. search_orchestration/config.py
   ADD: db_path, storage_path fields
   TIME: 5 minutes

2. search_orchestration/orchestrator.py  
   ADD: coordinator initialization
   ADD: _persist_results() method
   FIX: PubMed async bug
   FIX: OpenAlex method name
   TIME: 45 minutes

3. (optional) api/routes/agents.py
   No changes needed - orchestrator handles it!
   TIME: 0 minutes

TOTAL: 2 files, ~60 minutes
```

---

## 🎯 WHAT'S NOT CHANGING

### Keep As-Is (No Changes)
```
✅ omics_oracle_v2/database/        (Auth DB - separate concern)
✅ omics_oracle_v2/auth/            (Users, API keys, JWT)
✅ omics_oracle_v2/lib/storage/     (Phases 1-5 - already complete!)
✅ omics_oracle_v2/lib/pipelines/   (Phase 3 - already complete!)
✅ All search clients               (GEO, PubMed, OpenAlex)
✅ All API routes except agents.py  (Auth, users, health, metrics)
```

### Already Integrated (Phases 1-5)
```
✅ UnifiedDatabase      → Used by queries, analytics, coordinator
✅ GEOStorage          → Used by coordinator
✅ PipelineCoordinator → Used by integration tests
✅ DatabaseQueries     → Uses UnifiedDatabase
✅ Analytics           → Uses UnifiedDatabase
```

---

## 🚀 EXECUTION PLAN

### Phase A: Bug Fixes (30 min)
```bash
# 1. Fix PubMed (remove await or use executor)
# 2. Fix OpenAlex (correct method name)
# 3. Fix resource leaks (proper cleanup)
# 4. Test: "DNA methylation" search → No errors
```

### Phase B: Integration (1 hour)
```bash
# 1. Add db_path to config
# 2. Add coordinator to orchestrator
# 3. Add persist method
# 4. Test: Check database for saved citations
```

### Phase C: Validation (30 min)
```bash
# 1. Test auth still works
# 2. Test search + database writes
# 3. Run DatabaseQueries
# 4. Check Analytics
```

**TOTAL: 2 hours** → Then production validation (4-6 hours)

---

## ✅ SUCCESS CRITERIA

After integration, you'll have:

1. ✅ Working frontend search (no errors)
2. ✅ Results persisted to UnifiedDatabase
3. ✅ Auth system unchanged and working
4. ✅ All Phases 1-5 integrated and used
5. ✅ Single search flow (no duplicates)
6. ✅ Ready for production validation

---

## 🎯 NEXT STEP

**Shall I proceed with Phase A (bug fixes)?**

I'll:
1. Check OpenAlex client for correct method name
2. Fix PubMed async issue
3. Fix OpenAlex method call
4. Fix resource leaks
5. Test with frontend

Then move to Phase B (integration).

**Ready? 🚀**
