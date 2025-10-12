# Quick Action Summary - What to Delete vs Move

## 🔴 DELETE Immediately (Legacy Code - 430 LOC)

### File: `omics_oracle_v2/agents/search_agent.py`

**Delete these lines:**

1. **Lines 67-75:** Old client initialization
   ```python
   # OLD IMPLEMENTATION (keep for backward compatibility)
   self._geo_client: GEOClient = None
   self._ranker = KeywordRanker(settings.ranking)
   self._enable_semantic = enable_semantic
   self._enable_publications = enable_publications
   self._enable_query_preprocessing = enable_query_preprocessing
   self._semantic_pipeline: Optional[AdvancedSearchPipeline] = None
   self._semantic_index_loaded = False
   self._publication_pipeline = None
   self._preprocessing_pipeline = None
   ```

2. **Lines 373-800:** Entire legacy `_process()` method
   - `_process()` - Legacy search implementation
   - `_build_search_query()` - Old query builder
   - `_build_geo_query_from_preprocessed()` - Duplicate logic
   - `_apply_semantic_filters()` - Not used
   - `_semantic_search()` - Not used
   - `_initialize_semantic_search()` - Not used
   - `_initialize_publication_search()` - Not used
   - `_initialize_query_preprocessing()` - Not used
   - `enable_semantic_search()` - Not used
   - `is_semantic_search_available()` - Not used

3. **Line 79:** Remove feature flag (hardcoded to True anyway)
   ```python
   self._use_unified_pipeline = True  # DELETE - always True
   ```

4. **Lines 368-372:** Remove feature flag check
   ```python
   # DELETE:
   if self._use_unified_pipeline:
       return self._process_unified(input_data, context)

   # LEGACY IMPLEMENTATION: Keep for backward compatibility
   # DELETE ALL OF THIS ↓↓↓
   ```

**Keep these methods (they're used):**
- `__init__()` (simplified)
- `_initialize_resources()` (simplified)
- `_cleanup_resources()` (simplified)
- `_validate_input()`
- `_process_unified()` ✅ MAIN METHOD
- `_build_query_with_filters()`
- `_apply_filters()`
- `_rank_datasets()`
- `_calculate_relevance()`
- `_get_applied_filters()`

---

## 📦 MOVE to extras/ (Unused Features - 4,400 LOC)

### 1. RAG Pipeline (Ready for Integration)

```bash
mkdir -p extras/rag
mv omics_oracle_v2/lib/rag/* extras/rag/
# Keep the lib/rag directory, just move contents
```

**Files:**
- `lib/rag/pipeline.py` (613 LOC)
- `lib/rag/context.py` (200 LOC)
- `lib/rag/prompts.py` (300 LOC)
- `lib/rag/__init__.py`

### 2. Semantic Search (95% Complete)

```bash
mkdir -p extras/semantic_search
mv omics_oracle_v2/lib/search/advanced.py extras/semantic_search/
mv omics_oracle_v2/lib/search/hybrid.py extras/semantic_search/
mv omics_oracle_v2/lib/embeddings/geo_pipeline.py extras/semantic_search/
```

**Files:**
- `lib/search/advanced.py` (535 LOC) - AdvancedSearchPipeline
- `lib/search/hybrid.py` (400 LOC) - HybridSearchEngine
- `lib/embeddings/geo_pipeline.py` (200 LOC) - Embedding generation

### 3. Workflow System (Multi-Agent Orchestration)

```bash
mkdir -p extras/workflows
mv omics_oracle_v2/api/routes/workflows.py extras/workflows/routes_workflows.py
mv omics_oracle_v2/api/routes/workflows_dev.py extras/workflows/routes_workflows_dev.py
mv omics_oracle_v2/agents/orchestrator.py extras/workflows/
mv omics_oracle_v2/agents/query_agent.py extras/workflows/
mv omics_oracle_v2/agents/data_agent.py extras/workflows/
mv omics_oracle_v2/agents/report_agent.py extras/workflows/
mv omics_oracle_v2/lib/workflows/* extras/workflows/
```

**Files:**
- `api/routes/workflows.py` (500 LOC)
- `api/routes/workflows_dev.py` (300 LOC)
- `agents/orchestrator.py` (600 LOC)
- `agents/query_agent.py` (400 LOC)
- `agents/data_agent.py` (500 LOC)
- `agents/report_agent.py` (600 LOC)
- `lib/workflows/*` (200 LOC)

### 4. ML Features (Mock Endpoints)

```bash
mkdir -p extras/ml_features
mv omics_oracle_v2/api/routes/analytics.py extras/ml_features/
mv omics_oracle_v2/api/routes/predictions.py extras/ml_features/
mv omics_oracle_v2/api/routes/recommendations.py extras/ml_features/
```

**Files:**
- `api/routes/analytics.py` (300 LOC) - Biomarker analytics
- `api/routes/predictions.py` (300 LOC) - Trend predictions
- `api/routes/recommendations.py` (300 LOC) - Dataset recommendations

### 5. Auth & Quotas (Not Enforced)

```bash
mkdir -p extras/auth_quotas
mv omics_oracle_v2/api/routes/quotas.py extras/auth_quotas/
mv omics_oracle_v2/api/middleware/rate_limit.py extras/auth_quotas/
```

**Files:**
- `api/routes/quotas.py` (400 LOC)
- `api/middleware/rate_limit.py` (200 LOC)

### 6. Batch Scripts (Standalone Tools)

```bash
mkdir -p extras/batch_scripts
mv omics_oracle_v2/lib/pipelines/geo_citation_pipeline.py extras/batch_scripts/
```

**Files:**
- `lib/pipelines/geo_citation_pipeline.py` (373 LOC)

---

## ⚠️ UPDATE (Remove Route Imports)

### File: `omics_oracle_v2/api/main.py`

**Remove these imports:**
```python
# DELETE:
from .routes import workflows, workflows_dev
from .routes import analytics, predictions, recommendations
from .routes import quotas
```

**Remove these router inclusions:**
```python
# DELETE:
app.include_router(workflows.router)
app.include_router(workflows_dev.router)
app.include_router(analytics.router)
app.include_router(predictions.router)
app.include_router(recommendations.router)
app.include_router(quotas.router)
```

**Keep these (actively used):**
```python
# KEEP:
from .routes import agents, auth, health, debug
app.include_router(agents.router)
app.include_router(auth.router)
app.include_router(health.router)
app.include_router(debug.router)
```

---

## ✅ KEEP (Active Code - Don't Touch)

### Core Pipeline
- `lib/pipelines/unified_search_pipeline.py` ✅
- `lib/pipelines/publication_pipeline.py` ⚠️ (will merge later)

### Clients
- `lib/geo/client.py` ✅
- `lib/publications/clients/*.py` ✅
- `lib/citations/clients/*.py` ✅
- `lib/fulltext/manager.py` ✅

### NLP & Query Processing
- `lib/nlp/biomedical_ner.py` ✅
- `lib/nlp/synonym_expansion.py` ✅
- `lib/query/optimizer.py` ✅
- `lib/query/analyzer.py` ✅

### Infrastructure
- `lib/cache/redis_cache.py` ✅
- `lib/database/*.py` ✅
- `lib/storage/*.py` ✅
- `lib/ai/client.py` ✅
- `lib/llm/client.py` ✅

### API Routes (Active)
- `api/routes/agents.py` ✅ (search, analyze, enrich)
- `api/routes/auth.py` ✅ (login, register)
- `api/routes/health.py` ✅ (healthcheck)
- `api/routes/debug.py` ✅ (dev only)

---

## 🎯 Summary

| Action | Files | LOC | Impact |
|--------|-------|-----|--------|
| 🔴 **DELETE** | 1 file (partial) | -430 | Remove legacy SearchAgent code |
| 📦 **MOVE** | ~25 files | -4,400 | Move unused features to extras/ |
| ⚠️ **UPDATE** | 1 file | -50 | Remove route imports from main.py |
| ✅ **KEEP** | ~150 files | 12,600 | Core functionality intact |
| **TOTAL** | | **-4,880 LOC** | **-8.5% codebase** |

---

## 🚀 Quick Start Commands

### Step 1: Create extras directory
```bash
mkdir -p extras/{rag,semantic_search,workflows,ml_features,auth_quotas,batch_scripts}
```

### Step 2: Move files
```bash
# RAG
mv omics_oracle_v2/lib/rag/* extras/rag/

# Semantic Search
mv omics_oracle_v2/lib/search/advanced.py extras/semantic_search/
mv omics_oracle_v2/lib/search/hybrid.py extras/semantic_search/
mv omics_oracle_v2/lib/embeddings/geo_pipeline.py extras/semantic_search/

# Workflows
mv omics_oracle_v2/api/routes/workflows*.py extras/workflows/
mv omics_oracle_v2/agents/orchestrator.py extras/workflows/
mv omics_oracle_v2/agents/query_agent.py extras/workflows/
mv omics_oracle_v2/agents/data_agent.py extras/workflows/
mv omics_oracle_v2/agents/report_agent.py extras/workflows/
mv omics_oracle_v2/lib/workflows/* extras/workflows/

# ML Features
mv omics_oracle_v2/api/routes/analytics.py extras/ml_features/
mv omics_oracle_v2/api/routes/predictions.py extras/ml_features/
mv omics_oracle_v2/api/routes/recommendations.py extras/ml_features/

# Auth/Quotas
mv omics_oracle_v2/api/routes/quotas.py extras/auth_quotas/
mv omics_oracle_v2/api/middleware/rate_limit.py extras/auth_quotas/

# Batch Scripts
mv omics_oracle_v2/lib/pipelines/geo_citation_pipeline.py extras/batch_scripts/
```

### Step 3: Create README
```bash
cat > extras/README.md << 'EOF'
# Extras - Unused Features

Features built but not yet integrated.

## Ready for Integration
- **rag/** - RAG pipeline (production-ready)
- **semantic_search/** - 95% complete (needs embeddings)

## Future Features
- **workflows/** - Multi-agent orchestration
- **ml_features/** - Analytics, predictions, recommendations
- **auth_quotas/** - Production auth & rate limiting
- **batch_scripts/** - Offline processing tools

See CLEANUP_PLAN_DETAILED.md for integration instructions.
EOF
```

### Step 4: Clean up SearchAgent (manual edit)
Open `omics_oracle_v2/agents/search_agent.py` and delete:
- Lines 67-75 (old client init)
- Lines 373-800 (legacy methods)
- Line 79 (feature flag)
- Lines 368-372 (feature flag check)

### Step 5: Update main.py (manual edit)
Open `omics_oracle_v2/api/main.py` and remove:
- Imports for workflows, analytics, predictions, recommendations, quotas
- Router inclusions for the same

### Step 6: Test
```bash
pytest tests/agents/test_search_agent.py -v
pytest tests/api/ -v
```

---

## ✅ Verification Checklist

After cleanup, verify:

- [ ] Frontend still works: `http://localhost:8000/dashboard`
- [ ] Search works: Try a query
- [ ] PDF download works: Click "Download Paper"
- [ ] AI analysis works: Click "AI Analysis"
- [ ] Auth works: Login/Register
- [ ] No import errors: `python -m omics_oracle_v2.api.main`
- [ ] Tests pass: `pytest tests/ -v`
- [ ] Git status clean: All files committed

---

## 🔄 Rollback

If anything breaks:
```bash
# Undo file moves
git checkout HEAD -- omics_oracle_v2/

# Restore extras
rm -rf extras/

# Start over
git reset --hard HEAD
```
