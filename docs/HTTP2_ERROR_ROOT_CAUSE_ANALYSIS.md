# HTTP/2 Protocol Error Analysis & Fix

**Date:** October 13, 2025
**Error:** `net::ERR_HTTP2_PROTOCOL_ERROR`
**Status:** ❌ **NOT FIXED** (previous attempts incomplete)

---

## Root Cause Analysis

### What We Thought Was Fixed
Previous fix added `include_full_content=False` parameter to `/enrich-fulltext` endpoint to reduce response size.

### What's Actually Happening
The HTTP/2 error occurs at the **`/analyze` endpoint**, not `/enrich-fulltext`!

```
Flow:
1. Frontend calls /enrich-fulltext with include_full_content=False ✓
   → Response: Small (~50KB per dataset, only metadata)

2. Frontend stores dataset with fulltext metadata in memory ✓
   → Dataset has: fulltext[{pmid, title, url, has_abstract, has_methods, ...}]

3. User clicks "AI Analysis" button
   → Frontend sends ENTIRE dataset object to /analyze ❌
   → Dataset now includes: All previously enriched fulltext content!

4. Backend /analyze reads ft.abstract, ft.methods, ft.results ❌
   → AI analysis response includes FULL CONTENT (not just snippets)
   → Response size: 500KB - 2MB per dataset

5. Browser receives massive response → HTTP/2 error ❌
```

---

## The Bug in Detail

### File: `omics_oracle_v2/api/routes/agents.py` (lines 836-848)

```python
# Add full-text content if available
if ds.fulltext and len(ds.fulltext) > 0:
    for j, ft in enumerate(ds.fulltext[:2], 1):
        dataset_info.extend([
            f"\n   Paper {j}: {ft.title[:100]}...",
            f"   Abstract: {ft.abstract[:250] if ft.abstract else 'N/A'}...",  ❌ Accessing full content!
            f"   Methods: {ft.methods[:400] if ft.methods else 'N/A'}...",      ❌ Accessing full content!
            f"   Results: {ft.results[:400] if ft.results else 'N/A'}...",      ❌ Accessing full content!
            f"   Discussion: {ft.discussion[:250] if ft.discussion else 'N/A'}...",  ❌
        ])
```

**Problem:** The code accesses `ft.abstract`, `ft.methods`, `ft.results`, `ft.discussion`.

**Two scenarios:**
1. **If `include_full_content=False`:** These fields don't exist → No error, but "N/A" everywhere
2. **If `include_full_content=True`:** These fields contain 10KB-50KB each → Massive response

---

## Why Previous Fix Didn't Work

### What We Did (October 12):
1. Added `include_full_content=False` parameter to `/enrich-fulltext`
2. Changed response to include only metadata:
   ```python
   fulltext_info = {
       "has_abstract": bool(parsed_content.get("abstract")),  # Just boolean!
       "has_methods": bool(parsed_content.get("methods")),
       "content_length": sum(len(str(v)) for v in parsed_content.values())
   }
   ```

### What We Missed:
The frontend **caches the enriched datasets** in memory. If a user:
1. Enriches datasets (gets metadata-only response)
2. Closes browser
3. Re-opens browser
4. Frontend fetches from `/search` again
5. **Full content is now in the dataset object** (if it was previously enriched with `include_full_content=True`)

Or worse, the `/search` endpoint itself might be returning full content!

---

## The Real Fix

### Option 1: Never Send Full Content to Frontend (RECOMMENDED)

**Principle:** Full-text content should ONLY exist on backend for AI analysis.

**Changes:**

1. **Backend: Always exclude full content from responses**
   ```python
   # In /enrich-fulltext response
   # NEVER include abstract, methods, results, discussion
   fulltext_info = {
       "pmid": pub.pmid,
       "title": pub.title,
       "url": pub.fulltext_url,
       "pdf_path": str(pub.pdf_path),
       # Metadata only - no content!
       "has_abstract": bool(parsed_content.get("abstract")),
       "has_methods": bool(parsed_content.get("methods")),
       "has_results": bool(parsed_content.get("results")),
       "content_length": sum(len(str(v)) for v in parsed_content.values())
   }
   ```

2. **Backend: AI analysis loads content from disk**
   ```python
   # In /analyze endpoint
   for ft in ds.fulltext:
       if ft.get('pdf_path'):
           # Load parsed content from disk/cache
           parsed = await load_parsed_content(ft['pdf_path'])
           abstract = parsed.get('abstract', '')[:250]
           methods = parsed.get('methods', '')[:400]
           # Use in prompt...
   ```

3. **Frontend: Send minimal dataset info**
   ```javascript
   // Only send essential fields
   const minimalDataset = {
       geo_id: dataset.geo_id,
       title: dataset.title,
       summary: dataset.summary,
       organism: dataset.organism,
       sample_count: dataset.sample_count,
       relevance_score: dataset.relevance_score,
       pubmed_ids: dataset.pubmed_ids,  // Backend loads full-text from disk
       fulltext_count: dataset.fulltext?.length || 0
   };

   const response = await fetch('/api/agents/analyze', {
       body: JSON.stringify({
           datasets: [minimalDataset],
           query: currentQuery
       })
   });
   ```

---

### Option 2: Strip Content Before Sending (QUICK FIX)

**Frontend change only:**

```javascript
// Before sending to /analyze, strip full content
function stripFullTextContent(dataset) {
    const cleanDataset = { ...dataset };

    if (cleanDataset.fulltext) {
        cleanDataset.fulltext = cleanDataset.fulltext.map(ft => ({
            pmid: ft.pmid,
            title: ft.title,
            url: ft.url,
            pdf_path: ft.pdf_path,
            // Remove large text fields
            has_abstract: !!ft.abstract || ft.has_abstract,
            has_methods: !!ft.methods || ft.has_methods,
            has_results: !!ft.results || ft.has_results,
            has_discussion: !!ft.discussion || ft.has_discussion,
            content_length: ft.content_length || 0
        }));
    }

    return cleanDataset;
}

// Use when calling /analyze
const response = await fetch('/api/agents/analyze', {
    body: JSON.stringify({
        datasets: [stripFullTextContent(dataset)],
        query: currentQuery
    })
});
```

---

### Option 3: Hybrid (BEST)

Combine both approaches:

1. **Backend never sends full content** (prevents future issues)
2. **Frontend strips on send** (defensive programming)
3. **Backend loads from disk for analysis** (source of truth)

---

## Testing the Fix

### Test 1: Check Response Size

```bash
# Before fix (expect 500KB - 2MB)
curl -X POST http://localhost:8000/api/agents/analyze \
  -H "Content-Type: application/json" \
  -d '{"datasets": [...], "query": "test"}' \
  | wc -c

# After fix (expect <50KB)
curl -X POST http://localhost:8000/api/agents/analyze \
  -H "Content-Type: application/json" \
  -d '{"datasets": [...], "query": "test"}' \
  | wc -c
```

### Test 2: Verify AI Analysis Quality

```python
# Ensure AI still gets full content
analysis_prompt = "...Methods: {methods[:400]}..."  # Should have content
assert len(methods) > 100, "AI should see full methods section!"
```

### Test 3: Frontend Console

```javascript
// Before sending
console.log('Dataset size:', JSON.stringify(dataset).length);
// Should be <10KB per dataset
```

---

## Implementation Priority

### Critical (Fix Today):
1. ✅ Option 2: Frontend strips content before sending to `/analyze`
   - **Impact:** Immediate fix, no backend changes
   - **Risk:** Low
   - **Time:** 10 minutes

### High (Fix This Week):
2. ⚠️ Option 1: Backend loads content from disk for analysis
   - **Impact:** Prevents future issues, cleaner architecture
   - **Risk:** Medium (need to ensure caching works)
   - **Time:** 2-3 hours

### Medium (Future):
3. 📋 Add response size monitoring
   - **Impact:** Catch similar issues early
   - **Risk:** Low
   - **Time:** 1 hour

---

## Conclusion

**Status:** ❌ HTTP/2 error NOT fixed in previous attempt
**Root Cause:** `/analyze` endpoint receives massive dataset objects with full-text content
**Immediate Fix:** Frontend strips content before sending
**Long-term Fix:** Backend never sends full content, loads from disk for analysis
**Estimated Fix Time:** 10 minutes (frontend) + 2 hours (backend)

---

**Next Steps:**
1. Implement Option 2 (frontend strip) immediately
2. Test with large dataset
3. Implement Option 1 (backend disk loading) this week
4. Add monitoring to prevent recurrence
