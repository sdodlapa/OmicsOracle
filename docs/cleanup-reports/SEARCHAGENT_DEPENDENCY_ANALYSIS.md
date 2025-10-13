# SearchAgent Dependency Analysis

## Executive Summary

**Question**: Can we remove `search_agent.py` completely?

**Answer**: **YES - SearchAgent can be safely removed** ✅

**Reasoning**:
1. ✅ **API route already migrated** - `/api/agents/search` now uses `OmicsSearchPipeline` directly
2. ✅ **Only dependency is Orchestrator** - which is NOT used in production
3. ✅ **Workflow routes are archived** - in `extras/` folder, not active
4. ✅ **Tests can be archived** - useful as reference but not blocking

---

## Detailed Dependency Trace

### 1. Active Production Code

#### 1.1 API Routes (`omics_oracle_v2/api/routes/agents.py`)
**Status**: ✅ **ALREADY MIGRATED**

**Before** (Stage 3 Pass 1b):
```python
from omics_oracle_v2.agents import SearchAgent

agent = SearchAgent(settings=settings, enable_semantic=request.enable_semantic)
result = agent.execute(search_input)
```

**After** (Stage 3 Pass 1b - CURRENT):
```python
from omics_oracle_v2.lib.pipelines.unified_search_pipeline import OmicsSearchPipeline

pipeline = OmicsSearchPipeline(config)
search_result = await pipeline.search(query=query, ...)
```

**Conclusion**: ✅ API routes no longer depend on SearchAgent

---

#### 1.2 Registered API Endpoints (`omics_oracle_v2/api/main.py`)

Checked all `app.include_router()` calls:
```python
app.include_router(health_router, prefix="/health")
app.include_router(auth_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(agents_router, prefix="/api/agents")  # ← Uses our migrated route
app.include_router(websocket_router, prefix="/ws")
app.include_router(metrics_router)
```

**NO workflow routes registered** ✅

**Conclusion**: ✅ No active endpoints use SearchAgent

---

### 2. Orchestrator Dependency (INACTIVE)

#### 2.1 What is Orchestrator?

**File**: `omics_oracle_v2/agents/orchestrator.py` (528 LOC)

**Purpose**: Multi-agent workflow coordinator that chains:
1. QueryAgent (refine user query)
2. **SearchAgent** (find datasets) ← ONLY SearchAgent usage
3. DataAgent (validate datasets)
4. ReportAgent (generate report)

**Code**:
```python
from omics_oracle_v2.agents.search_agent import SearchAgent

class Orchestrator:
    def __init__(self, settings):
        self.query_agent = QueryAgent(settings)
        self.search_agent = SearchAgent(settings)  # ← Creates instance
        self.data_agent = DataAgent(settings)
        self.report_agent = ReportAgent(settings)

    def _execute_search_stage(self, ...):
        search_input = SearchInput(...)
        result = self.search_agent.execute(search_input)  # ← Calls SearchAgent
        return WorkflowResult(...)
```

**Usage**: Orchestrator uses SearchAgent in `_execute_search_stage()` (lines 394-427)

---

#### 2.2 Where is Orchestrator Used?

**Active Production Code**: ❌ **NOWHERE**

**Archived Code** (in `extras/` folder):
1. `extras/workflows/routes_workflows.py` - workflow endpoints (NOT registered)
2. `extras/workflows/routes_workflows_dev.py` - dev workflows (NOT registered)
3. `extras/workflows/routes_batch.py` - batch processing (NOT registered)

**Test Code**:
1. `omics_oracle_v2/tests/integration/test_agents.py` - integration tests

**Verification**:
```bash
# Checked all active API routes
grep -r "include_router" omics_oracle_v2/api/main.py
# Result: NO workflow routes registered ✅
```

**Conclusion**: ✅ Orchestrator is NOT used in production, only in archived code

---

### 3. Complete Dependency Map

```
SearchAgent Dependencies (Complete List)
│
├── 1. PRODUCTION CODE (Active)
│   ├── ❌ omics_oracle_v2/api/routes/agents.py
│   │   └── Status: ✅ MIGRATED (now uses OmicsSearchPipeline directly)
│   │
│   └── ❌ omics_oracle_v2/api/main.py
│       └── Status: ✅ NO workflow routes registered
│
├── 2. ORCHESTRATOR (Inactive - in extras/)
│   ├── omics_oracle_v2/agents/orchestrator.py
│   │   └── Status: ⚠️ Imports SearchAgent but NOT used in production
│   │
│   ├── extras/workflows/routes_workflows.py
│   │   └── Status: 📦 ARCHIVED (not registered in API)
│   │
│   ├── extras/workflows/routes_workflows_dev.py
│   │   └── Status: 📦 ARCHIVED (not registered in API)
│   │
│   └── extras/workflows/routes_batch.py
│       └── Status: 📦 ARCHIVED (not registered in API)
│
├── 3. TESTS (Can be archived)
│   ├── omics_oracle_v2/tests/unit/agents/test_search_agent.py
│   │   └── Status: 📝 Unit tests for SearchAgent
│   │
│   ├── omics_oracle_v2/tests/integration/test_agents.py
│   │   └── Status: 📝 Integration tests (includes Orchestrator)
│   │
│   ├── extras/legacy_tests/test_quick_migration.py
│   │   └── Status: 📦 ARCHIVED
│   │
│   └── extras/legacy_tests/test_searchagent_migration.py
│       └── Status: 📦 ARCHIVED
│
├── 4. IMPORTS (Can be updated)
│   ├── omics_oracle_v2/agents/__init__.py
│   │   └── Status: ⚠️ Currently exports SearchAgent (can remove)
│   │
│   └── omics_oracle_v2/api/dependencies.py
│       └── Status: ⚠️ Comments reference SearchAgent (can update)
│
└── 5. DOCUMENTATION (References only)
    ├── COMPREHENSIVE_CODEBASE_REVIEW.md
    ├── END_TO_END_FLOW_ANALYSIS.md
    ├── CLEANUP_PLAN_DETAILED.md
    └── Various cleanup reports
        └── Status: 📄 Documentation only
```

---

## What SearchAgent Actually Does

Let me trace through the actual functionality to see if we need to migrate anything:

### SearchAgent Methods Used by Orchestrator

**File**: `omics_oracle_v2/agents/search_agent.py`

```python
class SearchAgent(Agent[SearchInput, SearchOutput]):

    # 1. USED BY ORCHESTRATOR
    def execute(self, input_data: SearchInput) -> AgentResult[SearchOutput]:
        """Main entry point - calls _process()"""
        # ✅ Standard Agent pattern, not SearchAgent-specific

    # 2. CALLED BY execute()
    def _process(self, input_data: SearchInput, context: AgentContext) -> SearchOutput:
        """Routes to _process_unified()"""
        return self._process_unified(input_data, context)

    # 3. CALLED BY _process()
    def _process_unified(self, input_data: SearchInput, context: AgentContext) -> SearchOutput:
        """Does the actual work"""

        # Build query with filters
        query_with_filters = self._build_query_with_filters(query, input_data)

        # Call OmicsSearchPipeline
        search_result = self._run_async(
            self._unified_pipeline.search(query=query_with_filters, ...)
        )

        # Apply min_samples filter
        filtered_datasets = self._apply_filters(geo_datasets, input_data)

        # Rank datasets
        ranked_datasets = self._rank_datasets(filtered_datasets, input_data)

        return SearchOutput(...)

    # 4. HELPER METHODS
    def _build_query_with_filters(self, query, input_data):
        """Adds organism/study_type to query"""
        # Simple string building

    def _apply_filters(self, datasets, input_data):
        """Filters by min_samples"""
        # Simple list comprehension

    def _rank_datasets(self, datasets, input_data):
        """Simple keyword-based ranking"""
        # Basic scoring algorithm
```

### Functionality Breakdown

| Method | Complexity | Purpose | Needed? |
|--------|-----------|---------|---------|
| `execute()` | Low | Standard Agent wrapper | ❌ Agent pattern overhead |
| `_process()` | Low | Routes to unified | ❌ Unnecessary indirection |
| `_process_unified()` | Medium | Main orchestration | ⚠️ Could extract |
| `_build_query_with_filters()` | Low | Add organism/study_type | ✅ Simple - 15 LOC |
| `_apply_filters()` | Low | Filter by min_samples | ✅ Simple - 8 LOC |
| `_rank_datasets()` | Low | Keyword ranking | ✅ Simple - 25 LOC |

**Total useful code**: ~50 LOC of simple filtering/ranking logic

---

## Migration Options

### Option 1: Remove SearchAgent Completely (RECOMMENDED ✅)

**What to do**:

1. **Update Orchestrator** to use `OmicsSearchPipeline` directly
   - Replace `self.search_agent = SearchAgent(settings)`
   - With `self.search_pipeline = OmicsSearchPipeline(config)`
   - Migrate the 50 LOC of filtering/ranking if needed

2. **Archive SearchAgent files**:
   ```bash
   mv omics_oracle_v2/agents/search_agent.py extras/agents/
   mv omics_oracle_v2/tests/unit/agents/test_search_agent.py extras/tests/
   ```

3. **Update imports**:
   - `omics_oracle_v2/agents/__init__.py` - remove SearchAgent export
   - `omics_oracle_v2/api/dependencies.py` - remove SearchAgent references

**Pros**:
- ✅ Clean architecture - no wrapper layers
- ✅ 462 LOC removed from active codebase
- ✅ Easier to maintain (one less abstraction)
- ✅ Consistent with our migration strategy

**Cons**:
- ⚠️ Need to update Orchestrator (simple change)
- ⚠️ Need to decide where to put 50 LOC of filtering/ranking

**Effort**: Low (1-2 hours)
- 30 min: Update Orchestrator to use pipeline directly
- 30 min: Migrate filtering/ranking logic (if needed)
- 30 min: Update imports and test

---

### Option 2: Keep SearchAgent for Orchestrator (NOT RECOMMENDED ❌)

**What to do**:
- Keep current state
- Document that SearchAgent is only for Orchestrator
- Mark as deprecated for all other uses

**Pros**:
- ✅ No code changes needed
- ✅ Orchestrator still works

**Cons**:
- ❌ Maintains dead code (Orchestrator not used)
- ❌ Confusing architecture (why keep wrapper?)
- ❌ 462 LOC stays in codebase unnecessarily
- ❌ Goes against our cleanup goals

**Effort**: None, but technical debt remains

---

## Recommended Action Plan

### Phase 1: Update Orchestrator (30 minutes)

**File**: `omics_oracle_v2/agents/orchestrator.py`

**Change**:
```python
# BEFORE
from omics_oracle_v2.agents.search_agent import SearchAgent

class Orchestrator:
    def __init__(self, settings):
        self.search_agent = SearchAgent(settings)

    def _execute_search_stage(self, ...):
        result = self.search_agent.execute(search_input)

# AFTER
from omics_oracle_v2.lib.pipelines.unified_search_pipeline import OmicsSearchPipeline, UnifiedSearchConfig

class Orchestrator:
    def __init__(self, settings):
        config = UnifiedSearchConfig(
            enable_geo_search=True,
            enable_publication_search=True,
        )
        self.search_pipeline = OmicsSearchPipeline(config)

    def _execute_search_stage(self, ...):
        # Build query with filters (migrate from SearchAgent)
        query = self._build_search_query(input_data)

        # Call pipeline
        search_result = await self.search_pipeline.search(query=query, ...)

        # Apply filters and ranking (migrate from SearchAgent)
        filtered = self._filter_datasets(search_result.geo_datasets, input_data)
        ranked = self._rank_datasets(filtered, input_data)

        return WorkflowResult(...)
```

**Migrate these 3 simple methods** (50 LOC total):
1. `_build_search_query()` - from `SearchAgent._build_query_with_filters()`
2. `_filter_datasets()` - from `SearchAgent._apply_filters()`
3. `_rank_datasets()` - from `SearchAgent._rank_datasets()`

---

### Phase 2: Archive SearchAgent (15 minutes)

```bash
# Move files to extras
mkdir -p extras/agents
mv omics_oracle_v2/agents/search_agent.py extras/agents/

mkdir -p extras/tests/unit/agents
mv omics_oracle_v2/tests/unit/agents/test_search_agent.py extras/tests/unit/agents/
```

---

### Phase 3: Update Imports (15 minutes)

**File**: `omics_oracle_v2/agents/__init__.py`
```python
# REMOVE
from .search_agent import SearchAgent

# UPDATE __all__
__all__ = [
    "Agent",
    "DataAgent",
    "Orchestrator",
    "QueryAgent",
    "ReportAgent",
    # "SearchAgent",  # REMOVED - use OmicsSearchPipeline directly
]
```

**File**: `omics_oracle_v2/api/dependencies.py`
```python
# REMOVE deprecated note about SearchAgent
# (already updated in Pass 1b)
```

---

### Phase 4: Test (30 minutes)

1. **Test Orchestrator** (if needed - currently not used):
   ```python
   python -c "from omics_oracle_v2.agents import Orchestrator; print('✓ Import OK')"
   ```

2. **Test active API** (already working):
   ```bash
   python scripts/test_api_search_updated.py
   ```

3. **Test imports**:
   ```python
   python -c "from omics_oracle_v2.agents import DataAgent, QueryAgent, ReportAgent; print('✓ All imports OK')"
   ```

---

## Impact Analysis

### Files to Change
1. ✅ `omics_oracle_v2/agents/orchestrator.py` - Update to use pipeline (~50 LOC changes)
2. ✅ `omics_oracle_v2/agents/__init__.py` - Remove SearchAgent export (~2 LOC)
3. ✅ Move `search_agent.py` to `extras/` (archive)
4. ✅ Move `test_search_agent.py` to `extras/` (archive)

### LOC Impact
- **Removed from active code**: 462 LOC (search_agent.py)
- **Added to Orchestrator**: ~50 LOC (simple filters/ranking)
- **Net reduction**: **~410 LOC** 🎉

### Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Orchestrator breaks | Low | Low | Not used in production; easy to fix |
| Import errors | Very Low | Low | Simple find/replace |
| Missing functionality | Very Low | Low | All logic is simple, easy to migrate |
| API breaks | None | None | Already migrated in Pass 1b |

**Overall Risk**: 🟢 **VERY LOW**

---

## Conclusion

### Answer: YES, Remove SearchAgent ✅

**Rationale**:
1. ✅ **Already migrated from production** - API routes use pipeline directly
2. ✅ **Only dependency is inactive code** - Orchestrator not used in production
3. ✅ **Simple migration** - Only 50 LOC of logic to move
4. ✅ **Big cleanup win** - Remove 462 LOC, simplify architecture
5. ✅ **Low risk** - Easy to test and validate

**Recommendation**: **Proceed with full SearchAgent removal**

**Estimated effort**: 1.5 hours
**Expected LOC reduction**: ~410 LOC
**Risk level**: Low 🟢

---

## Next Steps

1. ✅ **Approve this analysis** - Review and confirm approach
2. ⏭️ **Execute Phase 1** - Update Orchestrator (30 min)
3. ⏭️ **Execute Phase 2** - Archive SearchAgent (15 min)
4. ⏭️ **Execute Phase 3** - Update imports (15 min)
5. ⏭️ **Execute Phase 4** - Test and validate (30 min)
6. ⏭️ **Document** - Update Stage 3 Pass 1b report

**Total time**: ~1.5 hours
**Total LOC removed**: ~410 LOC (cumulative with Pass 1a: 194 + 410 = **604 LOC** in Stage 3!)

---

## Questions for User

1. **Orchestrator**: Do you want to keep Orchestrator functional, or can we mark it as "needs update" since it's not used?
   - Option A: Update it now (adds 30 min)
   - Option B: Leave it broken with TODO comment (faster)

2. **Filtering/Ranking logic**: Where should the 50 LOC go?
   - Option A: Put in Orchestrator (if we update it)
   - Option B: Create a utility module `lib/utils/dataset_ranking.py`
   - Option C: Don't migrate - let Orchestrator use pipeline results as-is

My recommendation: **Option B for Orchestrator** (leave with TODO) and **Option C for logic** (don't migrate unless needed).

---

**Ready to proceed?** Say "yes" and I'll execute all 4 phases!
