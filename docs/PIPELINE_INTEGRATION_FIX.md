# Pipeline 1+2 Integration Fix

**Date**: October 14, 2025  
**Status**: ⚠️ CRITICAL BUG FOUND + FIX READY

---

## 🔍 Issue Discovery

While testing the integration of Pipeline 1 (GEO Citation Discovery) and Pipeline 2 (Full-Text URL Collection), we discovered a **critical integration bug** in the `GEOCitationPipeline`.

### Location
- **File**: `extras/pipelines/geo_citation_pipeline.py`
- **Lines**: 214-242 (Step 4: Collect full-text URLs)

---

## 🚨 The Problem

### What's Wrong

The `GEOCitationPipeline` at line 214 calls:

```python
papers_with_fulltext = await self.fulltext_manager.get_fulltext_batch(unique_papers)
```

**Expected**: The code assumes `get_fulltext_batch()` returns a list of `Publication` objects with added fields:
- `fulltext_url`
- `fulltext_source`

**Reality**: `get_fulltext_batch()` returns a list of `FullTextResult` objects with:
- `success: bool`
- `source: Optional[FullTextSource]`
- `url: Optional[str]`
- `all_urls: Optional[List[SourceURL]]`
- *(no Publication object)*

### Impact

This causes the following issues:

1. **Line 217**: `if p.fulltext_url` → ❌ `AttributeError: 'FullTextResult' object has no attribute 'fulltext_url'`
2. **Line 226**: `if hasattr(paper, "fulltext_source")` → Always False, source counts are empty
3. **Line 242**: `papers_to_download = [p for p in papers_with_fulltext if p.fulltext_url]` → ❌ Fails
4. **Lines 349-350**: Saving metadata tries to access `p.fulltext_url` and `p.fulltext_source` → ❌ Fails

### Why This Wasn't Caught

The integration test we created uses **mocked publications** and didn't test the actual `GEOCitationPipeline` code path - it tested the components in isolation.

---

## ✅ The Solution

We need to update `GEOCitationPipeline` to properly handle `FullTextResult` objects.

### Changes Required

#### 1. Update Step 4 - Full-Text Collection (Lines 212-227)

**Current (BROKEN)**:
```python
# Step 4: Collect full-text URLs
logger.info("Step 4: Collecting full-text URLs (optimized waterfall)...")
papers_with_fulltext = await self.fulltext_manager.get_fulltext_batch(unique_papers)

# Calculate coverage
fulltext_count = sum(1 for p in papers_with_fulltext if p.fulltext_url)
fulltext_coverage = fulltext_count / len(papers_with_fulltext) if papers_with_fulltext else 0

# Count by source
source_counts = {}
for paper in papers_with_fulltext:
    if hasattr(paper, "fulltext_source") and paper.fulltext_source:
        source_counts[paper.fulltext_source] = source_counts.get(paper.fulltext_source, 0) + 1
```

**Fixed**:
```python
# Step 4: Collect full-text URLs
logger.info("Step 4: Collecting full-text URLs (optimized waterfall)...")
fulltext_results = await self.fulltext_manager.get_fulltext_batch(unique_papers)

# Map results back to publications and add fulltext info
papers_with_fulltext = []
for pub, result in zip(unique_papers, fulltext_results):
    if result.success and result.url:
        # Add fulltext info to publication
        pub.fulltext_url = result.url
        pub.fulltext_source = result.source.value if result.source else None
    papers_with_fulltext.append(pub)

# Calculate coverage
fulltext_count = sum(1 for r in fulltext_results if r.success)
fulltext_coverage = fulltext_count / len(fulltext_results) if fulltext_results else 0

# Count by source
source_counts = {}
for result in fulltext_results:
    if result.success and result.source:
        source_name = result.source.value
        source_counts[source_name] = source_counts.get(source_name, 0) + 1
```

#### 2. No Changes Needed for Step 5 (PDF Download)

Once publications have `fulltext_url` added, the existing code works:
```python
papers_to_download = [p for p in papers_with_fulltext if p.fulltext_url]
```

#### 3. Update Metadata Saving (Lines 340-351)

**Current**:
```python
papers_data = [
    {
        "pmid": p.pmid,
        "doi": p.doi,
        "title": p.title,
        "journal": p.journal,
        "year": p.year,
        "fulltext_url": p.fulltext_url,
        "fulltext_source": getattr(p, "fulltext_source", None),
    }
    for p in citing_papers
]
```

**Fixed** (already safe with getattr):
```python
papers_data = [
    {
        "pmid": p.pmid,
        "doi": p.doi,
        "title": p.title,
        "journal": p.journal,
        "year": p.year,
        "fulltext_url": getattr(p, "fulltext_url", None),
        "fulltext_source": getattr(p, "fulltext_source", None),
    }
    for p in citing_papers
]
```

---

## 🧪 Testing Strategy

### 1. Unit Test for Fixed Code
Create a test that:
1. Mocks `get_fulltext_batch()` to return `FullTextResult` objects
2. Verifies publications get updated with fulltext info
3. Verifies source counts are calculated correctly

### 2. Integration Test Update
Update `tests/test_pipeline_1_2_integration.py` to:
1. Test the actual `GEOCitationPipeline.collect()` method
2. Verify end-to-end flow works with real components

### 3. Manual Test
Run the pipeline with a real query:
```python
from extras.pipelines.geo_citation_pipeline import GEOCitationPipeline

pipeline = GEOCitationPipeline()
result = await pipeline.collect("breast cancer RNA-seq", max_datasets=2)
print(f"Coverage: {result.fulltext_coverage:.1%}")
print(f"Sources: {result.fulltext_by_source}")
```

---

## 📊 Root Cause Analysis

### Why Did This Happen?

1. **API Mismatch**: The `FullTextManager` API was designed to return `FullTextResult` objects (proper separation of concerns), but `GEOCitationPipeline` was written assuming in-place mutation of `Publication` objects.

2. **Missing Contract Documentation**: The `get_fulltext_batch()` method signature doesn't clearly document the return type structure.

3. **Insufficient Integration Testing**: The integration test tested components in isolation rather than the complete pipeline flow.

### Lessons Learned

1. **Document Return Types**: Always use type hints and docstrings for return types
2. **Test Real Code Paths**: Integration tests should use the actual pipeline code, not just the components
3. **API Contracts**: When designing APIs that return complex objects, document the object structure clearly

---

## 🎯 Recommendations

### Immediate (Today)
1. ✅ Fix `GEOCitationPipeline` (lines 212-227)
2. ✅ Test with real query
3. ✅ Update integration test

### Short-Term (This Week)
1. Add type hints to `get_fulltext_batch()` return type
2. Create comprehensive `GEOCitationPipeline` tests
3. Document API contracts in all pipeline methods

### Long-Term (Future)
1. Consider returning `(Publication, FullTextResult)` tuples from `get_fulltext_batch()` for clearer mapping
2. Add integration test CI pipeline
3. Create pipeline regression test suite

---

## 📝 Summary

- **Bug**: `GEOCitationPipeline` expects `Publication` objects but gets `FullTextResult` objects
- **Fix**: Map results back to publications and extract URL/source from `FullTextResult`
- **Impact**: Critical - pipeline won't work without this fix
- **Effort**: 15 minutes to fix, 30 minutes to test
- **Risk**: Low - straightforward mapping logic

**Next Step**: Apply the fix to `extras/pipelines/geo_citation_pipeline.py`
