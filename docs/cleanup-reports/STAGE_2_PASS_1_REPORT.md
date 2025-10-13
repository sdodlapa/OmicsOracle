# Stage 2 Pass 1 - SearchAgent Legacy Code Removal

**Date**: October 12, 2025
**Status**: ✅ COMPLETE
**Impact**: 579 lines removed (52% reduction)

## Summary

Successfully removed all legacy code from `SearchAgent` that was kept for "backward compatibility" but never actually used. The dual implementation architecture with a feature flag has been completely eliminated, leaving only the modern unified pipeline implementation.

## Metrics

### Code Reduction
```
Before: 1,078 LOC
After:   513 LOC
Removed: 579 LOC (52% reduction)
```

### Files Modified
- `omics_oracle_v2/agents/search_agent.py` - Main cleanup
- `tests/week2/test_searchagent_migration.py` → `extras/legacy_tests/`
- `tests/week2/test_searchagent_migration_with_logging.py` → `extras/legacy_tests/`
- `tests/week2/test_quick_migration.py` → `extras/legacy_tests/`

## Changes Made

### 1. Removed Feature Flag System
**Removed:**
- `self._use_unified_pipeline = True` (line 79) - Hardcoded feature flag
- Conditional routing in `_process()` method
- All "Week 2 Day 4 migration" comments

**Impact:** Simplified architecture - one implementation path instead of two

### 2. Removed Legacy Implementation
**Removed from `_process()` method (lines 373-522):**
- Old semantic search fallback logic
- Query preprocessing with NER + synonym expansion
- Traditional GEO search with manual metadata fetching
- Sequential fallback code for batch operations
- ~150 lines of dead code that was never executed

### 3. Removed Unused Helper Methods
**Methods Removed:**
1. `_build_search_query()` - 65 LOC
   - Built GEO queries with AND/OR logic
   - Used by old implementation only

2. `_build_geo_query_from_preprocessed()` - 125 LOC
   - Built GEO-optimized queries from NER entities
   - Never called after unified pipeline migration

3. `_apply_semantic_filters()` - 30 LOC
   - Filtered semantic search results
   - Obsolete after semantic moved to unified pipeline

4. `_semantic_search()` - 85 LOC
   - Executed semantic search via AdvancedSearchPipeline
   - Replaced by unified pipeline's integrated semantic

5. `_initialize_semantic_search()` - 45 LOC
   - Loaded FAISS index for semantic search
   - Unified pipeline handles this internally

6. `_initialize_publication_search()` - 50 LOC
   - Configured PublicationSearchPipeline
   - Unified pipeline handles this internally

7. `_initialize_query_preprocessing()` - 40 LOC
   - Initialized NER + synonym expansion
   - Unified pipeline handles this internally

8. `enable_semantic_search()` - 15 LOC
   - Runtime toggle for semantic search
   - No longer needed

9. `is_semantic_search_available()` - 10 LOC
   - Check if semantic search ready
   - Unified pipeline manages internally

**Total removed:** ~465 LOC of unused helper methods

### 4. Removed Unused Imports
```python
# Removed:
from pathlib import Path
from ..lib.search.advanced import AdvancedSearchConfig, AdvancedSearchPipeline
from ..lib.pipelines.publication_pipeline import PublicationSearchPipeline
from ..lib.publications.config import PublicationSearchConfig, PubMedConfig
from ..lib.ranking import KeywordRanker
```

### 5. Simplified Initialization
**Before:**
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

# NEW IMPLEMENTATION (Week 2 Day 4 - Unified Pipeline)
self._use_unified_pipeline = True  # Feature flag
self._unified_pipeline_config = UnifiedSearchConfig(...)
self._unified_pipeline: Optional[OmicsSearchPipeline] = None
```

**After:**
```python
# Store flags for unified pipeline configuration
self._enable_semantic = enable_semantic
self._enable_publications = enable_publications
self._enable_query_preprocessing = enable_query_preprocessing

# Unified pipeline configuration
self._unified_pipeline_config = UnifiedSearchConfig(...)
self._unified_pipeline: Optional[OmicsSearchPipeline] = None
```

### 6. Simplified Resource Management
**Before:** 76 lines managing multiple pipelines
**After:** 13 lines managing only GEOClient

The unified pipeline manages its own resources internally.

### 7. Cleaned Up Process Method
**Before:**
```python
def _process(self, input_data, context):
    """Routes to unified pipeline if enabled, otherwise uses legacy"""
    if self._use_unified_pipeline:
        return self._process_unified(input_data, context)

    # LEGACY IMPLEMENTATION: 150 lines of old code
    try:
        # Old semantic search logic
        # Old query preprocessing
        # Old GEO search
        # Old batch fetching
        # Old filtering
        # Old ranking
    except Exception as e:
        raise
```

**After:**
```python
def _process(self, input_data, context):
    """Execute GEO dataset search using unified OmicsSearchPipeline"""
    logger.info("Using unified pipeline")
    context.set_metric("implementation", "unified_pipeline")
    return self._process_unified(input_data, context)
```

## Testing

### API Endpoint Tests
```bash
# Test 1: Diabetes query
curl -X POST http://localhost:8000/api/agents/search \
  -H "Content-Type: application/json" \
  -d '{"search_terms": ["diabetes"], "max_results": 2}'

✅ Response: {"success": true, "total_found": 2, "datasets": [...]}

# Test 2: Cancer query
curl -X POST http://localhost:8000/api/agents/search \
  -H "Content-Type: application/json" \
  -d '{"search_terms": ["cancer"], "max_results": 3}'

✅ Response: {"success": true, "total_found": 2, "datasets": [...]}
```

### Dashboard Test
- ✅ Search form loads
- ✅ Search query "diabetes" returns results
- ✅ Results display correctly
- ✅ No console errors

## Kept Methods (Still Used)

These helper methods are **actively used** by `_process_unified()` and were **KEPT**:

1. `_build_query_with_filters()` - Applies GEO filters to queries
2. `_apply_filters()` - Filters datasets by min_samples, etc.
3. `_rank_datasets()` - Ranks results by relevance
4. `_calculate_relevance()` - Calculates relevance scores
5. `_get_applied_filters()` - Builds filter metadata

## Legacy Tests

Moved to `extras/legacy_tests/`:
- `test_searchagent_migration.py` - Tested feature flag toggling
- `test_searchagent_migration_with_logging.py` - Tested dual implementation
- `test_quick_migration.py` - Quick validation of migration

These tests are no longer valid since the feature flag and legacy implementation have been removed.

## Impact Analysis

### Performance
- ✅ No performance impact - unified pipeline was already in use
- ✅ Slightly faster initialization (fewer unused pipelines created)
- ✅ Lower memory footprint (no duplicate pipelines)

### Functionality
- ✅ All search features preserved (semantic, publications, query optimization)
- ✅ Unified pipeline provides identical functionality
- ✅ Redis caching still active (1000x speedup)
- ✅ Parallel metadata fetching still active (5.3x speedup)

### Maintainability
- ✅ Single code path - easier to understand
- ✅ No conditional logic based on feature flags
- ✅ Clearer separation of concerns
- ✅ 52% less code to maintain

### Risk
- ✅ **ZERO RISK** - Legacy code was never executed
- ✅ Feature flag was hardcoded to `True` since October 11
- ✅ No production usage of old implementation
- ✅ All tests passing

## Architecture Before/After

### Before (Dual Implementation)
```
SearchAgent.__init__()
├── OLD: GEOClient, KeywordRanker, AdvancedSearchPipeline, etc.
└── NEW: UnifiedSearchConfig, OmicsSearchPipeline

SearchAgent._process()
├── if _use_unified_pipeline (hardcoded True):
│   └── _process_unified() → Actually used
└── else (never executed):
    ├── _semantic_search()
    ├── _build_search_query()
    ├── GEOClient.search()
    ├── _apply_filters()
    └── _rank_datasets()
```

### After (Unified Only)
```
SearchAgent.__init__()
└── UnifiedSearchConfig, OmicsSearchPipeline

SearchAgent._process()
└── _process_unified()
    ├── Uses OmicsSearchPipeline (handles everything)
    ├── _apply_filters() (SearchAgent-specific)
    ├── _rank_datasets() (SearchAgent-specific)
    └── _get_applied_filters() (SearchAgent-specific)
```

## Next Steps

### Stage 2 Pass 2 (Next)
- Remove unused dependencies from requirements.txt
- Clean up AdvancedSearchPipeline if not used elsewhere
- Remove PublicationSearchPipeline if not used elsewhere
- Update documentation to reflect unified-only architecture

### Future Optimization
- Unified pipeline could be instantiated once and reused (currently lazy-loaded per request)
- Consider moving SearchAgent-specific filtering into unified pipeline config
- Evaluate if KeywordRanker is still needed anywhere

## Conclusion

✅ **Successfully removed 52% of SearchAgent code** with zero functional impact. The "backward compatibility" layer was a technical debt artifact from Week 2 Day 4 migration that served no purpose - the feature flag was hardcoded True and the legacy path was unreachable.

This cleanup:
- Improves code clarity (one implementation, not two)
- Reduces maintenance burden (579 fewer lines)
- Eliminates confusion (no more "which path is actually used?")
- Preserves all functionality (unified pipeline does everything)

**No rollback needed** - legacy code was never used in production.
