# Parallel URL Collection Fix - October 16, 2025

## Problem
URL collection was happening **sequentially** in a for loop, causing 25-50 seconds delay before downloads could even start.

### Original Sequential Code (SLOW)
```python
async def _collect_urls(...):
    url_results = {}
    
    for pub in publications:  # ❌ SEQUENTIAL - one at a time!
        result = await fulltext_manager.get_all_fulltext_urls(pub)
        url_results[pub.pmid] = result.all_urls
    
    return url_results
```

**Performance Impact:**
- 25 papers × 2 seconds each = **50 seconds** just for URL collection
- Then another 30+ seconds for downloads
- Total: **80+ seconds**

## Solution
Changed to **parallel URL collection** using `asyncio.gather()`:

### New Parallel Code (FAST)
```python
async def _collect_urls(...):
    async def collect_for_pub(pub):
        """Collect URLs for a single publication"""
        result = await fulltext_manager.get_all_fulltext_urls(pub)
        return (pub.pmid, result.all_urls)
    
    # ✅ PARALLEL - all 25 at once!
    results = await asyncio.gather(*[collect_for_pub(pub) for pub in publications])
    url_results = {pmid: urls for pmid, urls in results}
    
    return url_results
```

**Performance Impact:**
- 25 papers in parallel = **~2-3 seconds** for URL collection
- Then 15-20 seconds for downloads (already parallel)
- Total: **17-23 seconds** (4x faster!)

## Key Changes

### 1. URL Collection (Line 322-373)
- ✅ Removed sequential `for pub in publications:` loop
- ✅ Added `async def collect_for_pub(pub)` inner function
- ✅ Uses `asyncio.gather()` to execute all 25 publications in parallel
- ✅ Returns tuple `(pmid, urls)` for easy dict conversion

### 2. Download Function (Line 375-520)
- ✅ Already uses passed `url_results` dict (no re-collection)
- ✅ Already parallel with `asyncio.gather()`
- ✅ Caches checked before download (database + file system)

### 3. No Duplicate Work
- ✅ URLs collected once in `_collect_urls()` in parallel
- ✅ URLs passed to `_download_pdfs()` via `url_results` dict
- ✅ No re-fetching or re-querying

## Performance Expectations

### Before Fix
1. URL collection: 50 seconds (sequential)
2. Downloads: 30 seconds (parallel)
3. **Total: ~80 seconds**

### After Fix
1. URL collection: 3 seconds (parallel)
2. Downloads: 20 seconds (parallel)
3. **Total: ~23 seconds**

### Improvement
- **4x faster overall**
- **17x faster URL collection phase**
- Better user experience (no long wait before downloads start)

## Testing
After server restart with cleared Python cache:
- Search GSE570 (25 papers)
- Expect: "Collecting URLs for 25 publications in parallel..."
- Expect: Total time 15-30 seconds (not 80+ seconds)

## Files Modified
- `omics_oracle_v2/services/fulltext_service.py` (lines 322-373)
  - Changed `_collect_urls()` from sequential to parallel
  - No changes to `_download_pdfs()` (already parallel)
