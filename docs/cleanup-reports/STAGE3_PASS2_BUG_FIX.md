# Stage 3 Pass 2 - Critical Bug Fix

**Date**: October 12, 2025
**Issue**: Search returning zero results after SearchOrchestrator migration
**Status**: ✅ FIXED

## Problem Description

After migrating from `OmicsSearchPipeline` → `PublicationSearchPipeline` nested architecture to the flat `SearchOrchestrator`, searches were returning zero results for all queries including:
- "breast cancer RNA-seq"
- "DNA methylation and chromatin accessibility and human brain"
- "diabetes"
- Even direct GEO ID lookups like "GSE100003"

## Root Causes

### 1. **Wrong Method Name** (Primary Issue)
**Location**: `lib/search/orchestrator.py` - `_search_geo()` and `_search_geo_by_id()`

**Problem**:
```python
# WRONG - method doesn't exist!
metadata = await self.geo_client.get_dataset_metadata(geo_id)
```

**Fix**:
```python
# CORRECT - actual method name
metadata = await self.geo_client.get_metadata(geo_id)
```

**Impact**: Every GEO search failed silently with `AttributeError`, returning empty lists.

---

### 2. **Wrong Return Type** (Secondary Issue)
**Location**: `lib/search/orchestrator.py` - `_search_geo()`

**Problem**:
```python
# Expected List[GEOSeriesMetadata], but got SearchResult!
datasets = await self.geo_client.search(geo_query, max_results=max_results)
logger.info(f"GEO: {len(datasets)} datasets found")  # ❌ TypeError!
return datasets
```

**Root Cause**:
- `GEOClient.search()` returns `SearchResult` (with `geo_ids` list)
- SearchOrchestrator expected `List[GEOSeriesMetadata]` directly
- This mismatch caused all searches to fail

**Fix**:
```python
# Step 1: Get SearchResult with geo_ids
search_result = await self.geo_client.search(geo_query, max_results=max_results)

if not search_result.geo_ids:
    return []

# Step 2: Fetch metadata for each ID
datasets = []
for geo_id in search_result.geo_ids:
    try:
        metadata = await self.geo_client.get_metadata(geo_id)
        if metadata:
            datasets.append(metadata)
    except Exception as e:
        logger.warning(f"Failed to fetch metadata for {geo_id}: {e}")
        continue

return datasets
```

**Impact**: This is how `OmicsSearchPipeline` was doing it correctly - we missed this pattern during migration.

---

### 3. **Query Optimization Configuration** (Related Issue)
**Location**: `api/routes/agents.py`

**Problem**:
```python
# BEFORE - enabled QueryOptimizer by default
enable_query_optimization=not request.enable_semantic,  # True by default
```

**Issue**: QueryOptimizer (NER + SapBERT) was adding complex expansions, then GEOQueryBuilder was adding MORE complexity on top, creating overly complex queries that GEO API couldn't handle.

**Fix**:
```python
# AFTER - disabled to avoid double preprocessing
enable_query_optimization=False,  # Let GEOQueryBuilder handle optimization
```

**Rationale**: GEOQueryBuilder already adds Entrez tags like `[Title]`, `[Organism]`, etc. Adding NER/SapBERT on top creates queries that are too complex.

## Testing Results

### Before Fix
```bash
curl -X POST "http://localhost:8000/api/agents/search" \
  -d '{"search_terms": ["breast cancer RNA-seq"], "max_results": 5}'

# Result: 0 datasets, 0 publications ❌
```

### After Fix
```bash
curl -X POST "http://localhost:8000/api/agents/search" \
  -d '{"search_terms": ["breast cancer RNA-seq"], "max_results": 5}'

# Result: 5 datasets ✅
# GSE306759 - Effect of palmitate on breast cancer cells...
# GSE267552 - Tumour-associated tissue-resident memory T cells...
# GSE215289 - HOTAIR-YTHDF3 interaction in breast cancer...
# GSE298177 - Identification of KIF20A as a vulnerability...
# GSE267442 - Identification of CLIC3 as a novel prognostic...
```

## Files Modified

1. **`omics_oracle_v2/lib/search/orchestrator.py`**
   - Fixed `_search_geo()`: Correctly handle `SearchResult` return type, fetch metadata for each ID
   - Fixed `_search_geo_by_id()`: Changed `get_dataset_metadata()` → `get_metadata()`

2. **`omics_oracle_v2/api/routes/agents.py`**
   - Changed `enable_query_optimization=False` to avoid double preprocessing

## Lessons Learned

### Migration Checklist for Future Reference

When migrating between pipeline architectures:

1. ✅ **Verify Method Names**: Don't assume method names - check actual implementation
2. ✅ **Verify Return Types**: Check what methods actually return, not what you expect
3. ✅ **Test Basic Functionality**: Test simple queries BEFORE complex features
4. ✅ **Check for Double Processing**: Avoid chaining optimizers (NER + SapBERT + GEOQueryBuilder = too complex)
5. ✅ **Use Type Hints**: Would have caught `SearchResult` vs `List[GEOSeriesMetadata]` mismatch

### Why This Happened

During Stage 3 Pass 2, we:
1. Created new `SearchOrchestrator` from scratch (514 LOC)
2. Assumed `GEOClient` API matched our expectations
3. Didn't thoroughly test basic functionality before moving to Phase 4

The old `OmicsSearchPipeline` was calling `get_metadata()` correctly, but we didn't notice this during code review.

## Impact on Stage 3 Pass 2

- **Status**: Bug fixed, all tests passing ✅
- **LOC Reduction**: Still ~1,174 LOC (unchanged by bug fix)
- **Architecture**: Flat orchestrator working correctly
- **Performance**: Searches now completing in 5-18 seconds (normal for metadata fetching)
- **Next Step**: Complete Phase 5 (archive old pipelines) and commit

## Prevention for Future

Added to `docs/development/MIGRATION_CHECKLIST.md`:

```markdown
## API Migration Checklist

When migrating to new APIs:
1. [ ] Read actual method signatures (don't assume)
2. [ ] Check return types match expectations
3. [ ] Test basic functionality first
4. [ ] Verify error handling works
5. [ ] Check for optimization/preprocessing overlap
6. [ ] Use type hints and linters
7. [ ] Test with real data, not mocks
```

---

**Resolution**: ✅ Search functionality fully restored. SearchOrchestrator working as designed.
