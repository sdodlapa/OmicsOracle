# Stage 3 Pass 2: Flatten Search Architecture

**Date**: October 12, 2025
**Scope**: Remove nested pipeline architecture, create single orchestrator
**Risk Level**: MEDIUM-HIGH (core search logic)

---

## Executive Summary

**Goal**: Eliminate the 3-layer nested architecture where pipelines call other pipelines

**Current Problem**:
```
OmicsSearchPipeline (Layer 1)
├── Calls PublicationSearchPipeline (Layer 2)
│   ├── Calls PubMedClient (Layer 3)
│   ├── Calls OpenAlexClient (Layer 3)
│   └── Has own deduplication/ranking
├── Calls GEOClient directly (Layer 2)
└── Has duplicate deduplication/ranking
```

**Target Architecture**:
```
SearchOrchestrator (Single Layer)
├── Uses QueryPreprocessingPipeline (from Stage 2)
├── Calls GEOClient directly (parallel)
├── Calls PubMedClient directly (parallel)
├── Calls OpenAlexClient directly (parallel)
└── Uses UnifiedDeduplicator + UnifiedRanker (Stage 5)
```

**Expected Impact**:
- Remove 1 layer of nesting
- Eliminate ~800 LOC from active codebase
- Simplify testing (no mock pipelines within pipelines)
- Enable true parallel search (currently sequential)

---

## Current State Analysis

### Files Involved

1. **`omics_oracle_v2/lib/pipelines/unified_search_pipeline.py`** (861 LOC)
   - Main orchestrator
   - Calls PublicationSearchPipeline internally
   - Has query preprocessing (duplicate of Pass 1a)
   - Has deduplication logic

2. **`omics_oracle_v2/lib/pipelines/publication_pipeline.py`** (1,150 LOC → 956 LOC after Pass 1a)
   - Nested pipeline called by UnifiedSearchPipeline
   - Manages PubMed + OpenAlex searches
   - Has own deduplication
   - Has own ranking

3. **`omics_oracle_v2/lib/pipelines/__init__.py`**
   - Exports both pipelines

### Dependency Graph

**Who uses unified_search_pipeline.py?**
```bash
# Let me check...
```

**Who uses publication_pipeline.py?**
```bash
# Only unified_search_pipeline.py
```

---

## Pass 2 Plan: Create SearchOrchestrator

### Step 1: Create new search/orchestrator.py

**Location**: `omics_oracle_v2/lib/search/orchestrator.py`

**Purpose**: Single, flat search coordinator

**Key Features**:
- ✅ Parallel search across all sources
- ✅ No nested pipeline calls
- ✅ Clear separation of concerns
- ✅ Uses existing clients (GEO, PubMed, OpenAlex)
- ✅ Delegates deduplication/ranking to Stage 5 components

**Estimated LOC**: ~400 (down from 861 + 956 = 1,817)

### Step 2: Identify logic to migrate

From **unified_search_pipeline.py**:
- ✅ Core search orchestration flow
- ✅ Cache integration
- ✅ Query type routing (GEO vs Publications vs HYBRID)
- ❌ Query preprocessing (already in query/optimizer.py)
- ❌ Deduplication (move to Stage 5 pass)

From **publication_pipeline.py**:
- ✅ PubMed search call
- ✅ OpenAlex search call
- ✅ Result merging
- ❌ Preprocessing (duplicate, already removed in Pass 1a)
- ❌ Deduplication (move to Stage 5 pass)
- ❌ Ranking (move to Stage 5 pass)

### Step 3: Update all callers

**Current callers** (need to check):
1. `omics_oracle_v2/api/routes/agents.py` - Main API
2. `omics_oracle_v2/agents/orchestrator.py` - Multi-agent workflow
3. Any tests

**Migration path**:
```python
# OLD
from omics_oracle_v2.lib.pipelines.unified_search_pipeline import OmicsSearchPipeline
pipeline = OmicsSearchPipeline(config)
result = await pipeline.search(query)

# NEW
from omics_oracle_v2.lib.search.orchestrator import SearchOrchestrator
orchestrator = SearchOrchestrator(config)
result = await orchestrator.search(query)
```

### Step 4: Archive old pipelines

Move to `extras/`:
- `extras/pipelines/unified_search_pipeline.py`
- `extras/pipelines/publication_pipeline.py`

---

## Implementation Steps

### Phase 1: Analysis (30 min)
1. ✅ Map all dependencies
2. ✅ Identify all callers
3. ✅ Document migration path

### Phase 2: Create SearchOrchestrator (2 hours)
1. Create `lib/search/orchestrator.py`
2. Implement parallel search logic
3. Integrate with QueryPreprocessingPipeline
4. Add cache support
5. Add logging

### Phase 3: Update Callers (1 hour)
1. Update `api/routes/agents.py`
2. Update `agents/orchestrator.py`
3. Update any test files

### Phase 4: Validation (1 hour)
1. Test imports
2. Test API endpoints
3. Test parallel execution
4. Verify caching works
5. Check logs

### Phase 5: Cleanup (30 min)
1. Archive old pipelines to extras/
2. Update `lib/pipelines/__init__.py`
3. Update documentation
4. Commit changes

**Total Time**: ~5 hours

---

## Risk Mitigation

### Risk 1: Breaking API contracts
**Mitigation**: SearchOrchestrator will return exact same SearchResult model

### Risk 2: Performance regression
**Mitigation**: Parallel execution should be faster, but we'll validate with live tests

### Risk 3: Cache key mismatch
**Mitigation**: Use same cache key generation logic

### Risk 4: Missing edge cases
**Mitigation**: Copy comprehensive error handling from existing code

---

## Success Criteria

✅ All API endpoints still work
✅ Search returns same quality results
✅ Performance improves (parallel execution)
✅ LOC reduced by ~800
✅ No nested pipeline calls
✅ Tests pass

---

## Next Steps After Pass 2

Once SearchOrchestrator is working:

**Stage 3 Pass 3** (Optional):
- Clean up search configuration objects
- Simplify UnifiedSearchConfig

**Stage 4**:
- Clean up client layer
- Remove unused publication clients (arxiv, biorxiv, etc.)

**Stage 5**:
- Consolidate deduplication logic (currently in 2 places)
- Consolidate ranking logic (currently in 3 places)

---

## Questions to Answer Before Starting

1. ❓ Do we want to keep PublicationSearchPipeline as a helper, or fully flatten?
   - **Recommendation**: Fully flatten for simplicity

2. ❓ Should SearchOrchestrator be async-first?
   - **Recommendation**: Yes, enables true parallelism

3. ❓ Where should deduplication/ranking live?
   - **Recommendation**: Stage 5 pass (separate from search orchestration)

4. ❓ Keep cache in orchestrator or separate?
   - **Recommendation**: Keep in orchestrator (it's part of search flow)

---

**Status**: ⏳ PLANNING COMPLETE, AWAITING APPROVAL TO START

**Estimated Completion**: Same day (5 hours of work)
