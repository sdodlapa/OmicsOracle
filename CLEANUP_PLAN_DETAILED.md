# OmicsOracle Cleanup & Refactoring Plan
**Date:** October 12, 2025
**Purpose:** Remove legacy code, move unused features to extras, and simplify architecture
**Branch:** fulltext-implementation-20251011

---

## Executive Summary

**Findings:**
- ✅ **Legacy SearchAgent implementation** (~400 LOC) - kept for "backward compatibility" but NEVER USED
- ✅ **Unused features** built but not integrated: RAG, Semantic Search, Hybrid Search, Workflows, Analytics
- ✅ **Frontend only calls 3 routes:** `/api/agents/search`, `/api/agents/analyze`, `/api/auth/*`
- ✅ **15+ API routes** exist but are NOT USED by frontend

**Impact:**
- Remove legacy code: -400 LOC from SearchAgent
- Move unused features: ~8,000 LOC to extras/
- Delete unused routes: ~3,000 LOC

**Total cleanup:** ~11,400 LOC (20% of codebase)

---

## Part 1: Remove Legacy Code (Immediate)

### 1.1 SearchAgent Legacy Implementation

**File:** `omics_oracle_v2/agents/search_agent.py`

**Current State:**
- Line 79: `self._use_unified_pipeline = True` (HARDCODED to new pipeline)
- Lines 67-800: Entire old implementation kept for "backward compatibility"
- Lines 373-800: Legacy `_process()` method - **NEVER CALLED**

**Analysis:**
```python
# Line 368: Feature flag check
if self._use_unified_pipeline:
    return self._process_unified(input_data, context)  # ✅ ALWAYS TAKEN

# Line 373: Legacy implementation
# LEGACY IMPLEMENTATION: Keep for backward compatibility
logger.info("Using legacy implementation")  # ❌ NEVER REACHED
```

**Action:**
```diff
🔴 DELETE (Lines 373-800):
  - _process() method (legacy implementation)
  - _build_search_query() (old GEO query builder)
  - _build_geo_query_from_preprocessed() (duplicate)
  - _semantic_search() (not used in unified)
  - _initialize_semantic_search() (AdvancedSearchPipeline init)
  - _initialize_publication_search() (nested pipeline)
  - _initialize_query_preprocessing() (nested preprocessing)

🔴 DELETE (Lines 67-75):
  - Old client initialization
  - self._geo_client
  - self._semantic_pipeline
  - self._publication_pipeline
  - self._preprocessing_pipeline

✅ KEEP:
  - _process_unified() - ONLY active implementation
  - _validate_input() - Used
  - _apply_filters() - Used
  - _rank_datasets() - Used
  - _calculate_relevance() - Used
  - _get_applied_filters() - Used
  - _build_query_with_filters() - Used for unified
```

**Impact:** -430 LOC, cleaner code, no duplicate logic

---

### 1.2 Legacy API Routes

**File:** `omics_oracle_v2/api/main.py`

**Current State:**
- Line 187: Comment says "Legacy v1 routes for backwards compatibility (will be removed after frontend updates)"
- But NO v1 routes are actually included!

**Action:**
✅ Remove the misleading comment (routes don't exist)

---

## Part 2: Move Unused Features to extras/ (Phase 2)

### 2.1 Unused Features Overview

| Feature | Status | LOC | Reason | Action |
|---------|--------|-----|--------|--------|
| **RAG Pipeline** | Built but NO API endpoint | 613 | Not integrated | Move to extras/ |
| **Semantic Search** | 95% complete, missing embeddings | 535 | Not used | Move to extras/ |
| **Hybrid Search** | Built but not wired | 400 | Not used | Move to extras/ |
| **GEO Citation Pipeline** | Standalone script | 373 | Not integrated | Move to extras/ |
| **Workflow System** | Built but not used | 1,200 | Frontend doesn't call it | Move to extras/ |
| **Analytics Routes** | Mock data only | 300 | Not implemented | Move to extras/ |
| **Predictions Routes** | Mock data only | 300 | Not implemented | Move to extras/ |
| **Recommendations Routes** | Mock data only | 300 | Not implemented | Move to extras/ |
| **Quotas System** | Built but auth disabled | 400 | Not enforced | Move to extras/ |

**Total to move:** ~4,400 LOC

---

### 2.2 RAG Pipeline (Ready but Not Integrated)

**Files:**
```
omics_oracle_v2/lib/rag/
├── pipeline.py (613 LOC) ✅ Production-ready
├── context.py (200 LOC)
├── prompts.py (300 LOC)
└── __init__.py
```

**Status:**
- ✅ Complete implementation
- ✅ Multi-provider LLM support (OpenAI, local)
- ✅ Citation tracking
- ✅ Streaming support
- ❌ NO API endpoint
- ❌ NOT called by frontend

**Action:**
```bash
# Move to extras for future integration
mkdir -p extras/rag
mv omics_oracle_v2/lib/rag/* extras/rag/
```

**Note for future:** When integrating RAG:
1. Create API route: `POST /api/agents/rag-answer`
2. Wire to frontend "Ask AI" button
3. Integrate with search results

---

### 2.3 Semantic Search (95% Complete, Missing Index)

**Files:**
```
omics_oracle_v2/lib/search/
├── advanced.py (535 LOC) ✅ AdvancedSearchPipeline
├── hybrid.py (400 LOC) ✅ HybridSearchEngine
└── __init__.py

omics_oracle_v2/lib/embeddings/
├── geo_pipeline.py (200 LOC) ⚠️ One-time script
├── service.py (300 LOC) ✅ Embedding generation
└── __init__.py
```

**Status:**
- ✅ Complete implementation
- ✅ Query expansion
- ✅ Cross-encoder reranking
- ⚠️ Missing: GEO dataset embeddings index
- ❌ NOT wired to API
- ❌ SearchAgent has feature flag `enable_semantic=False`

**Action:**
```bash
# Move to extras for future integration
mkdir -p extras/semantic_search
mv omics_oracle_v2/lib/search/advanced.py extras/semantic_search/
mv omics_oracle_v2/lib/search/hybrid.py extras/semantic_search/
mv omics_oracle_v2/lib/embeddings/geo_pipeline.py extras/semantic_search/
```

**Note for future:** When integrating semantic search:
1. Run: `python extras/semantic_search/geo_pipeline.py` to generate embeddings
2. Enable in SearchAgent: `enable_semantic=True`
3. Add API parameter: `?search_mode=semantic`

---

### 2.4 GEO Citation Pipeline (Standalone Script)

**File:** `omics_oracle_v2/lib/pipelines/geo_citation_pipeline.py` (373 LOC)

**Status:**
- ✅ Complete implementation
- ✅ GEO → Citations → PDFs workflow
- ❌ NOT integrated with main flow
- ❌ NOT called by SearchAgent or API

**Current Flow:**
- Main: `OmicsSearchPipeline` (integrated)
- Separate: `GEOCitationPipeline` (standalone script)

**Why it's not used:**
- Main flow already has citation extraction (via regex in UnifiedSearchPipeline)
- This pipeline is for BATCH processing (not interactive)

**Action:**
```bash
# Move to extras as standalone script
mkdir -p extras/batch_scripts
mv omics_oracle_v2/lib/pipelines/geo_citation_pipeline.py extras/batch_scripts/
```

**Note:** This is useful for:
- Batch citation enrichment
- Offline dataset annotation
- Research paper generation

---

### 2.5 Workflow System (Built but Not Used)

**Files:**
```
omics_oracle_v2/api/routes/
├── workflows.py (500 LOC) ✅ Production workflow routes
├── workflows_dev.py (300 LOC) ✅ Dev workflow routes
└── ...

omics_oracle_v2/agents/
├── orchestrator.py (600 LOC) ✅ Multi-agent orchestrator
└── ...

omics_oracle_v2/lib/workflows/
├── coordinator.py (200 LOC)
├── models.py (100 LOC)
└── ...
```

**Status:**
- ✅ Complete multi-agent orchestration system
- ✅ 4 workflow types: BASIC, COMPREHENSIVE, DEEP_DIVE, COMPARATIVE
- ❌ Frontend NEVER calls `/api/workflows/execute`
- ❌ Frontend only uses single agent: `/api/agents/search`

**Frontend Usage:**
```html
<!-- dashboard_v2.html -->
fetch('/api/agents/search')  <!-- ✅ USED -->
fetch('/api/workflows/execute')  <!-- ❌ NEVER CALLED -->
```

**Why it's not used:**
- Frontend implements single-step workflow (search → display → PDF → AI)
- Multi-agent orchestration is overkill for current use case

**Action:**
```bash
# Move to extras for future multi-agent features
mkdir -p extras/workflows
mv omics_oracle_v2/api/routes/workflows.py extras/workflows/routes_workflows.py
mv omics_oracle_v2/api/routes/workflows_dev.py extras/workflows/routes_workflows_dev.py
mv omics_oracle_v2/agents/orchestrator.py extras/workflows/
mv omics_oracle_v2/lib/workflows/* extras/workflows/
```

**Note for future:** When implementing multi-agent workflows:
1. Add frontend "Advanced Workflow" tab
2. Wire to `/api/workflows/execute`
3. Enable agent coordination

---

### 2.6 Analytics, Predictions, Recommendations (Mock Data Only)

**Files:**
```
omics_oracle_v2/api/routes/
├── analytics.py (300 LOC) ❌ Mock data
├── predictions.py (300 LOC) ❌ Mock data
├── recommendations.py (300 LOC) ❌ Mock data
└── ...
```

**Status:**
- ⚠️ Routes exist but return `[]` or `TODO` comments
- ❌ No actual ML models
- ❌ No database queries
- ❌ Frontend doesn't call these routes

**Example from analytics.py:**
```python
@router.get("/biomarker/{biomarker}")
async def get_biomarker_analytics(biomarker: str):
    publications = []  # TODO: Fetch publications for biomarker
    return {"publications": publications}  # Returns empty!
```

**Action:**
```bash
# Move to extras for future ML features
mkdir -p extras/ml_features
mv omics_oracle_v2/api/routes/analytics.py extras/ml_features/
mv omics_oracle_v2/api/routes/predictions.py extras/ml_features/
mv omics_oracle_v2/api/routes/recommendations.py extras/ml_features/
```

---

### 2.7 Quotas & Rate Limiting (Built but Not Enforced)

**Files:**
```
omics_oracle_v2/api/routes/
├── quotas.py (400 LOC)
└── ...

omics_oracle_v2/api/middleware/
├── rate_limit.py (200 LOC)
└── ...

omics_oracle_v2/auth/
├── dependencies.py (100 LOC)
└── ...
```

**Status:**
- ✅ Complete quota system
- ✅ Tier-based limits
- ❌ Auth DISABLED for demo: `/agents/search` is public
- ❌ Rate limiting SKIPPED for search endpoint

**Current Code:**
```python
# api/main.py
# Rate limiting is DISABLED for /agents/search
app.add_middleware(RateLimitMiddleware, exclude_paths=["/agents/search"])
```

**Action:**
```bash
# Move to extras for future production deployment
mkdir -p extras/auth_quotas
mv omics_oracle_v2/api/routes/quotas.py extras/auth_quotas/
mv omics_oracle_v2/api/middleware/rate_limit.py extras/auth_quotas/
```

**Note:** Keep auth system (`auth/dependencies.py`) for `/auth/login` and `/auth/register` endpoints

---

## Part 3: Reorganize Remaining Code (Phase 3)

### 3.1 New Directory Structure

```
omics_oracle_v2/
├── api/
│   ├── routes/
│   │   ├── agents.py          # ✅ ACTIVE (search, analyze, enrich)
│   │   ├── auth.py            # ✅ ACTIVE (login, register)
│   │   ├── health.py          # ✅ ACTIVE (healthcheck)
│   │   └── debug.py           # ✅ DEV ONLY
│   ├── middleware/
│   ├── static/
│   └── main.py
│
├── agents/
│   ├── search_agent.py        # ✅ SIMPLIFIED (unified only)
│   ├── base.py                # ✅ KEEP
│   └── models/                # ✅ KEEP
│
├── lib/
│   ├── pipelines/
│   │   ├── unified_search_pipeline.py  # ✅ CORE (rename to search_orchestrator.py)
│   │   └── publication_pipeline.py     # ⚠️ MERGE into unified
│   │
│   ├── geo/                   # ✅ KEEP (GEO client)
│   ├── publications/          # ✅ KEEP (PubMed, OpenAlex clients)
│   ├── citations/             # ✅ KEEP (citation clients)
│   ├── fulltext/              # ✅ KEEP (PDF download)
│   ├── nlp/                   # ✅ KEEP (NER, query optimization)
│   ├── query/                 # ✅ KEEP (query analyzer, optimizer)
│   ├── ranking/               # ✅ KEEP (rankers)
│   ├── cache/                 # ✅ KEEP (Redis cache)
│   ├── database/              # ✅ KEEP (SQLAlchemy)
│   ├── ai/                    # ✅ KEEP (summarization client)
│   ├── llm/                   # ✅ KEEP (OpenAI client)
│   └── storage/               # ✅ KEEP (PDF storage)
│
└── core/                      # ✅ KEEP (config, logging)

extras/                        # 🆕 NEW: Unused features
├── rag/                       # RAG pipeline (ready for integration)
├── semantic_search/           # Semantic search (95% complete)
├── workflows/                 # Multi-agent workflows
├── ml_features/               # Analytics, predictions, recommendations
├── auth_quotas/               # Quota system, rate limiting
└── batch_scripts/             # GEO citation pipeline

archive/                       # ✅ KEEP (historical code)
```

---

## Part 4: Implementation Plan

### Phase 1: Remove Legacy Code (Day 1)

**Tasks:**
1. ✅ Remove legacy SearchAgent implementation
   - Delete lines 373-800 in `search_agent.py`
   - Delete old client initialization (lines 67-75)
   - Remove feature flag (hardcoded to True)
   - Clean up imports

2. ✅ Update imports across codebase
   - Remove references to deleted methods
   - Clean up unused imports

3. ✅ Run tests to ensure nothing breaks
   ```bash
   pytest tests/agents/test_search_agent.py -v
   ```

**Expected Impact:** -430 LOC, faster CI/CD

---

### Phase 2: Move Unused Features to extras/ (Day 2)

**Tasks:**
1. Create `extras/` directory structure
   ```bash
   mkdir -p extras/{rag,semantic_search,workflows,ml_features,auth_quotas,batch_scripts}
   ```

2. Move RAG pipeline
   ```bash
   mv omics_oracle_v2/lib/rag/* extras/rag/
   ```

3. Move semantic search
   ```bash
   mv omics_oracle_v2/lib/search/advanced.py extras/semantic_search/
   mv omics_oracle_v2/lib/search/hybrid.py extras/semantic_search/
   mv omics_oracle_v2/lib/embeddings/geo_pipeline.py extras/semantic_search/
   ```

4. Move workflows
   ```bash
   mv omics_oracle_v2/api/routes/workflows*.py extras/workflows/
   mv omics_oracle_v2/agents/orchestrator.py extras/workflows/
   mv omics_oracle_v2/lib/workflows/* extras/workflows/
   ```

5. Move ML features
   ```bash
   mv omics_oracle_v2/api/routes/{analytics,predictions,recommendations}.py extras/ml_features/
   ```

6. Move auth/quotas
   ```bash
   mv omics_oracle_v2/api/routes/quotas.py extras/auth_quotas/
   mv omics_oracle_v2/api/middleware/rate_limit.py extras/auth_quotas/
   ```

7. Move batch scripts
   ```bash
   mv omics_oracle_v2/lib/pipelines/geo_citation_pipeline.py extras/batch_scripts/
   ```

8. Update `main.py` to remove unused route imports
   ```python
   # REMOVE:
   # from .routes import workflows, workflows_dev, analytics, predictions, recommendations, quotas
   ```

9. Create README in extras/
   ```bash
   echo "# Extras - Unused Features

   This directory contains features that are built but not yet integrated.

   ## Ready for Integration
   - rag/ - RAG pipeline (production-ready)
   - semantic_search/ - 95% complete (needs embeddings)

   ## Future Features
   - workflows/ - Multi-agent orchestration
   - ml_features/ - Analytics, predictions, recommendations
   - auth_quotas/ - Production auth & rate limiting
   - batch_scripts/ - Offline processing tools
   " > extras/README.md
   ```

**Expected Impact:** -4,400 LOC from main codebase, clearer structure

---

### Phase 3: Flatten Pipeline Nesting (Day 3-4)

**Goal:** Merge `PublicationSearchPipeline` into `OmicsSearchPipeline`

**Current:**
```python
# OmicsSearchPipeline (600 LOC)
def _search_publications(self):
    return self.publication_pipeline.search()  # ⚠️ NESTED

# PublicationSearchPipeline (1,100 LOC)
def search(self):
    # Duplicate preprocessing
    # Duplicate deduplication
    # Duplicate ranking
    ...
```

**Target:**
```python
# SearchOrchestrator (900 LOC)
def search(self):
    # Unified preprocessing
    # Direct client calls
    # Single deduplication
    # Single ranking
    ...
```

**Tasks:**
1. Create `lib/search/orchestrator.py`
2. Copy core logic from `OmicsSearchPipeline`
3. Inline publication client calls (remove nested pipeline)
4. Remove duplicate preprocessing/ranking/dedup
5. Update SearchAgent to use new orchestrator
6. Delete old pipelines
7. Run full test suite

**Expected Impact:** -700 LOC, simpler call stack

---

## Part 5: Testing & Validation

### 5.1 Test Coverage

**Before Cleanup:**
```bash
pytest tests/ --cov=omics_oracle_v2 --cov-report=term
```

**After Each Phase:**
```bash
# Phase 1: Test SearchAgent
pytest tests/agents/test_search_agent.py -v

# Phase 2: Test API routes (ensure removed routes don't break anything)
pytest tests/api/ -v

# Phase 3: Test search orchestrator
pytest tests/lib/search/ -v

# Full integration test
pytest tests/integration/ -v
```

### 5.2 Frontend Validation

**Test in browser:**
1. Search functionality: `http://localhost:8000/dashboard`
2. PDF download: Click "Download Paper" button
3. AI analysis: Click "AI Analysis" button
4. Auth: Login/Register flows

**Expected:** All features work identically (no breaking changes)

---

## Part 6: Documentation Updates

### 6.1 Update README.md

**Add section:**
```markdown
## Extras Directory

The `extras/` directory contains features that are built but not yet integrated:

### Ready for Integration
- **RAG Pipeline** (`extras/rag/`) - Production-ready RAG with citations
- **Semantic Search** (`extras/semantic_search/`) - 95% complete, needs embeddings

### Future Features
- **Workflows** (`extras/workflows/`) - Multi-agent orchestration
- **ML Features** (`extras/ml_features/`) - Analytics, predictions
- **Auth & Quotas** (`extras/auth_quotas/`) - Production auth system
- **Batch Scripts** (`extras/batch_scripts/`) - Offline processing

See `extras/README.md` for integration instructions.
```

### 6.2 Update Architecture Docs

**Update:**
- `docs/architecture/system_overview.md` - Remove workflow system
- `docs/architecture/data_flow.md` - Simplify to single pipeline
- `END_TO_END_FLOW_ANALYSIS.md` - Update with new structure

---

## Part 7: Success Metrics

### Before Cleanup
| Metric | Value |
|--------|-------|
| Total LOC | 57,555 |
| Active LOC | 12,600 (22%) |
| Redundant LOC | 8,200 (14%) |
| API Routes | 45+ |
| Pipeline Layers | 4-5 |

### After Cleanup (Target)
| Metric | Value | Change |
|--------|-------|--------|
| Total LOC | 46,000 | -20% |
| Active LOC | 12,600 (27%) | +5% ratio |
| Redundant LOC | <2,000 (<5%) | -75% |
| API Routes | 15 | -67% |
| Pipeline Layers | 2-3 | -40% |

### Quality Improvements
- ✅ Simpler codebase (easier to understand)
- ✅ Faster onboarding (less code to learn)
- ✅ Faster CI/CD (fewer tests to run)
- ✅ Clear separation (active vs future features)
- ✅ Better maintainability (no duplicate logic)

---

## Part 8: Rollback Plan

**If something breaks:**

1. **Git safety:** All changes in feature branch
   ```bash
   git checkout -b cleanup-legacy-code
   git add .
   git commit -m "Phase 1: Remove legacy SearchAgent code"
   ```

2. **Revert specific phase:**
   ```bash
   git revert HEAD~1  # Revert last commit (Phase 3)
   git revert HEAD~2  # Revert Phase 2
   git revert HEAD~3  # Revert Phase 1
   ```

3. **Full rollback:**
   ```bash
   git checkout fulltext-implementation-20251011
   ```

---

## Part 9: Timeline

| Phase | Task | Days | Owner |
|-------|------|------|-------|
| 1 | Remove legacy SearchAgent | 1 | Dev |
| 2 | Move unused features to extras/ | 1 | Dev |
| 3 | Flatten pipeline nesting | 2 | Dev |
| 4 | Testing & validation | 1 | QA |
| 5 | Documentation updates | 1 | Tech Writer |
| **Total** | | **6 days** | |

**Start:** October 14, 2025
**Target Completion:** October 21, 2025

---

## Part 10: Next Steps

**Immediate (Next 24 hours):**
1. ✅ Review this plan
2. ✅ Approve cleanup strategy
3. ✅ Create feature branch: `cleanup-legacy-code`
4. ✅ Start Phase 1: Remove legacy SearchAgent

**Short Term (Next Week):**
1. Complete Phase 1-3 cleanup
2. Run full test suite
3. Update documentation
4. Merge to main branch

**Medium Term (Next Month):**
1. Integrate RAG pipeline (from extras/)
2. Generate semantic embeddings
3. Enable semantic search
4. Add advanced workflow UI

---

## Conclusion

This cleanup will:
- ✅ Remove 430 LOC of legacy code (SearchAgent)
- ✅ Move 4,400 LOC to extras/ (unused features)
- ✅ Reduce 700 LOC through pipeline flattening
- ✅ **Total: -5,530 LOC (10% reduction)**
- ✅ Improve code clarity and maintainability
- ✅ Preserve all built features for future use

**Risk:** Low (all changes in feature branch, reversible)
**Reward:** High (cleaner codebase, faster development)

**Recommended Action:** ✅ Proceed with Phase 1
