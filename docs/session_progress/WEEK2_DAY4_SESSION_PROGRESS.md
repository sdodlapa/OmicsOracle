# Week 2 Day 4: SearchAgent Migration - Session Progress

**Date:** October 11, 2025
**Sprint:** Sprint 1 - Parallel Metadata Fetching
**Status:** In Progress (Implementation Phase)
**Estimated Time:** 3-4 hours (1 hour completed)

---

## Progress Summary

### Completed ✅
1. **Analysis Phase** (30 min)
   - Read and understood current SearchAgent implementation
   - Analyzed OmicsSearchPipeline interface
   - Created comprehensive migration plan document
   - Identified all deprecated methods

2. **Planning Phase** (30 min)
   - Documented migration strategy
   - Created feature parity matrix
   - Designed backward compatibility approach
   - Planned test suite structure

### In Progress ⏳
3. **Implementation Phase** (1-2 hours)
   - Started modifying SearchAgent code
   - Encountered file corruption during large replacements
   - Reset to clean state
   - **Next:** Take more careful, incremental approach

### Pending ❌
4. **Testing Phase** (30-45 min)
   - Create test suite
   - Run performance comparisons
   - Validate backward compatibility

5. **Documentation Phase** (15-30 min)
   - Update docstrings
   - Create migration guide
   - Document performance improvements

---

## Implementation Strategy (Revised)

### Approach: Incremental Migration

Instead of replacing the entire `_process()` method at once, use a phased approach:

**Phase 1: Add New Components** (Keep old code working)
- Add `_pipeline_config` and `_pipeline` to `__init__()`
- Keep existing `_geo_client`, `_semantic_pipeline`, etc.
- Add lazy initialization of unified pipeline

**Phase 2: Route to New Pipeline** (Conditional)
- Add feature flag: `use_unified_pipeline=True`
- If enabled, route to new pipeline in `_process()`
- If disabled, use old code path
- Test both paths work

**Phase 3: Gradual Deprecation**
- Mark old methods as deprecated
- Add warnings when old path is used
- Keep both paths for 1-2 versions

**Phase 4: Complete Migration**
- Remove old code paths
- Clean up deprecated methods
- Final testing and documentation

---

## Current Challenge

**Issue:** Large file replacements in search_agent.py (972 lines) caused syntax errors

**Root Cause:**
- Tried to replace too much code at once
- Lost track of method boundaries
- File became corrupted with incomplete method definitions

**Solution:**
- Reset file to clean state ✅
- Use smaller, focused replacements
- Test after each change
- Commit frequently

---

## Lessons Learned

1. ✅ **Small, incremental changes** are better than large rewrites
2. ✅ **Test frequently** after each modification
3. ✅ **Commit early, commit often** to have rollback points
4. ✅ **Feature flags** allow parallel code paths during migration
5. ✅ **Backward compatibility** is critical for production systems

---

## Next Steps (Simplified Approach)

### Step 1: Add Unified Pipeline (Keep Old Code) - 15 min

**Goal:** Add new pipeline alongside existing code

```python
def __init__(self, settings, enable_semantic=False, enable_publications=False):
    super().__init__(settings)

    # OLD CODE (keep for now)
    self._geo_client: GEOClient = None
    self._semantic_pipeline: Optional[AdvancedSearchPipeline] = None
    # ... other old initializations ...

    # NEW CODE (add unified pipeline)
    self._use_unified_pipeline = True  # Feature flag
    self._pipeline_config = UnifiedSearchConfig(
        enable_geo_search=True,
        enable_publication_search=enable_publications,
        enable_query_optimization=True,
        enable_caching=True,
        enable_sapbert=enable_semantic,
    )
    self._unified_pipeline: Optional[OmicsSearchPipeline] = None  # Lazy init
```

**Test:** Verify SearchAgent still initializes correctly

### Step 2: Add Unified Pipeline Path in _process() - 20 min

**Goal:** Route to unified pipeline if feature flag enabled

```python
def _process(self, input_data: SearchInput, context: AgentContext) -> SearchOutput:
    # NEW PATH: Use unified pipeline if enabled
    if self._use_unified_pipeline:
        return self._process_unified(input_data, context)

    # OLD PATH: Keep existing logic intact
    # ... (all existing code unchanged) ...
```

**Test:** Try both paths, verify both work

### Step 3: Implement _process_unified() - 30 min

**Goal:** New method using OmicsSearchPipeline

```python
def _process_unified(self, input_data: SearchInput, context: AgentContext) -> SearchOutput:
    """Execute search using unified pipeline (Week 2 Day 4 migration)."""
    # Initialize pipeline if needed
    if not self._unified_pipeline:
        self._unified_pipeline = OmicsSearchPipeline(self._pipeline_config)

    # Extract query
    query = input_data.original_query or " ".join(input_data.search_terms)
    query_with_filters = self._build_query_with_filters(query, input_data)

    # Execute unified search
    search_result = self._run_async(
        self._unified_pipeline.search(
            query=query_with_filters,
            max_geo_results=input_data.max_results,
            use_cache=True,
        )
    )

    # Apply filters and ranking
    filtered = self._apply_filters(search_result.geo_datasets, input_data)
    ranked = self._rank_datasets(filtered, input_data)

    return SearchOutput(
        datasets=ranked,
        total_found=search_result.total_results,
        search_terms_used=input_data.search_terms,
        filters_applied=self._get_applied_filters(input_data),
    )
```

**Test:** Run searches with unified pipeline enabled

### Step 4: Performance Testing - 20 min

**Goal:** Validate improvements

- Run same queries with old path vs new path
- Measure latency differences
- Verify cache speedup
- Check parallel download works

### Step 5: Cleanup and Documentation - 20 min

**Goal:** Finalize migration

- Set `_use_unified_pipeline=True` as default
- Add deprecation warnings to old code
- Update docstrings
- Create migration guide

---

## Key Methods to Keep (Don't Remove)

These are still used by the new unified approach:

- ✅ `_apply_filters()` - Still needed for min_samples filtering
- ✅ `_rank_datasets()` - Custom SearchAgent scoring
- ✅ `_calculate_relevance()` - Relevance scoring logic
- ✅ `_get_applied_filters()` - Build filters metadata
- ✅ `_run_async()` - Handle async/sync contexts

## Methods to Deprecate (But Keep for Now)

These are replaced by unified pipeline but keep for backward compat:

- ⚠️ `_initialize_semantic_search()` - Replaced by pipeline
- ⚠️ `_initialize_publication_search()` - Replaced by pipeline
- ⚠️ `_initialize_query_preprocessing()` - Replaced by pipeline
- ⚠️ `_build_search_query()` - Replaced by QueryOptimizer
- ⚠️ `_build_geo_query_from_preprocessed()` - Replaced by QueryOptimizer
- ⚠️ `_semantic_search()` - Replaced by pipeline

---

## Timeline (Revised)

**Completed:** 1 hour (Analysis + Planning)
**Remaining:** 2-3 hours

| Task | Time | Status |
|------|------|--------|
| Step 1: Add unified pipeline (parallel) | 15 min | ⏳ Next |
| Step 2: Add routing logic | 20 min | ❌ |
| Step 3: Implement _process_unified() | 30 min | ❌ |
| Step 4: Testing | 20 min | ❌ |
| Step 5: Cleanup | 20 min | ❌ |
| **Subtotal** | **1h 45min** | |
| **Plus:** Error handling, debugging | +30 min | |
| **Total Remaining** | **~2h 15min** | |

---

## Success Criteria (Updated)

### Must Have
- [x] Migration plan documented
- [ ] Unified pipeline integrated
- [ ] Backward compatibility maintained
- [ ] Tests passing
- [ ] Performance validated (cache + parallel)
- [ ] Clean commit

### Should Have
- [x] Feature flag for safe rollback
- [ ] Deprecation warnings
- [ ] Performance comparison data
- [ ] Migration guide for users

### Nice to Have
- [ ] Both code paths work (old + new)
- [ ] Detailed performance metrics
- [ ] Rollback procedure documented

---

**Status:** Ready to continue with Step 1 (simplified, incremental approach)
**Next Action:** Add unified pipeline alongside existing code (no replacements)
**Risk Level:** Low (incremental changes, feature flag safety)
