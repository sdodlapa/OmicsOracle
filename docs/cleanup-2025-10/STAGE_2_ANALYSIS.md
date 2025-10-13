# Stage 2 Analysis: Agent Layer Redundancy

## Discovery: Dual Implementation in SearchAgent

### Critical Finding
**File:** `omics_oracle_v2/agents/search_agent.py` (1,078 LOC)

**Line 80 shows feature flag:**
```python
# OLD IMPLEMENTATION (keep for backward compatibility)
self._geo_client: GEOClient = None
self._ranker = KeywordRanker(settings.ranking)

# NEW IMPLEMENTATION (Week 2 Day 4 - Unified Pipeline)
self._use_unified_pipeline = True  # Feature flag: True = use new, False = use old
```

### Two Complete Search Implementations

#### OLD Implementation (Lines ~373-522):
- **Comment:** "# LEGACY IMPLEMENTATION: Keep for backward compatibility"
- Direct GEOClient usage
- Manual query building
- KeywordRanker for ranking
- ~150 LOC of legacy code

#### NEW Implementation (Lines ~252-350):
- **Method:** `_process_unified()`
- Uses `OmicsSearchPipeline` (unified)
- Modern architecture
- ~100 LOC

### Redundant Code Identified

1. **Dual _process() methods:**
   - `_process_unified()` - NEW (line 252)
   - `_process()` - LEGACY switcher (line 351) that calls old code

2. **Duplicate query building:**
   - `_build_search_query()` - OLD (line 523)
   - `_build_geo_query_from_preprocessed()` - NEW (line 586)

3. **Multiple initialization paths:**
   - `_initialize_semantic_search()` - OLD (line 848)
   - `_initialize_publication_search()` - OLD (line 889)
   - `_initialize_query_preprocessing()` - OLD (line 940)
   - All superseded by unified pipeline

### Impact Analysis

**Current state:**
- Feature flag `_use_unified_pipeline = True` means old code is NEVER executed
- Old implementation kept "for backward compatibility" but nothing uses it
- ~400 LOC of dead code (37% of file)

**Dependencies:**
```python
from ..lib.pipelines.unified_search_pipeline import OmicsSearchPipeline  # NEW
from ..lib.pipelines.publication_pipeline import PublicationSearchPipeline  # OLD
from ..lib.search.advanced import AdvancedSearchPipeline  # OLD
```

### Recommendation: Stage 2 Pass 1

**Safe to remove:**
1. All code paths when `_use_unified_pipeline == False`
2. Remove feature flag
3. Remove old pipeline imports
4. Keep only `_process_unified()` logic
5. Rename `_process_unified()` → `_process()`

**Expected impact:**
- Remove ~400 LOC from search_agent.py (37% reduction)
- Simpler code paths
- Easier maintenance
- No functional change (old code already unused)

**Testing:**
- Verify `_use_unified_pipeline = True` everywhere
- Confirm no external code sets flag to False
- Test search endpoint after removal

## Next: Verify Assumption

Need to confirm:
1. Is `_use_unified_pipeline` ever set to False?
2. Do any external callers depend on old behavior?
3. Is unified pipeline fully tested and stable?
