# AI Analysis Investigation - October 15, 2025

## 🔍 User Report

**Issue:** AI Analysis appears to be using only GEO summary, not the parsed PDF content, despite showing:
- "1 PDF available for AI analysis"
- "✅ Full-Text Analysis"
- "Analyzed 1 of 1 paper (1 full-text available)"

**Dataset:** GSE296967 with PMID 40375322

**UI Inconsistencies Noted:**
1. Shows "0/1 PDF downloaded" even though 1 paper downloaded
2. Shows "0% processed" even though marked as analyzed
3. AI summary appears to only reference GEO summary content

---

## ✅ Investigation Results

### **CONFIRMED: AI Analysis is NOT using parsed content**

The user's observation is **100% CORRECT**. The AI Analysis is only analyzing the GEO summary, not the full-text PDF content.

---

## 📊 Evidence Chain

### 1. **PDF Downloaded But Not Parsed into Cache**

```bash
# PDF file exists:
✅ data/pdfs/GSE296967/original/pmid_40375322.pdf

# Parsed cache directory is EMPTY:
❌ data/fulltext/parsed/  (directory does not exist)
```

**Implication:** PDF was downloaded but parsed content is not being cached/persisted to disk.

---

### 2. **Frontend Sends Metadata-Only Datasets**

**File:** `omics_oracle_v2/api/static/dashboard_v2.html`

**Code Flow:**
1. User clicks "Download Papers" → calls `/api/agents/enrich-fulltext`
2. **No `include_full_content` parameter** in request (defaults to `false`)
3. API parses PDF but returns only metadata flags:

```python
# agents.py:813-843
if include_full_content:  # ← FALSE by default!
    fulltext_info.update({
        "abstract": parsed_content.get("abstract", ""),  # ← Actual text
        "methods": parsed_content.get("methods", ""),    # ← Actual text
        # ...
    })
else:
    fulltext_info.update({
        "has_abstract": bool(parsed_content.get("abstract")),  # ← Just True/False!
        "has_methods": bool(parsed_content.get("methods")),    # ← Just True/False!
        "content_length": sum(len(str(v)) for v in parsed_content.values() if v),
    })
    logger.warning(
        f"[OK] Added PMID {pub.pmid} with METADATA ONLY "
        f"(set include_full_content=true for full text)"
    )
```

**Result:** Frontend receives dataset with:
```json
{
  "fulltext": [{
    "pmid": "40375322",
    "title": "...",
    "has_abstract": true,
    "has_methods": true,
    "has_results": true,
    "has_discussion": true,
    "content_length": 45678,
    // ❌ NO "abstract", "methods", "results", "discussion" fields!
  }]
}
```

**Log Evidence:**
```
[OK] Added PMID 40375322 with METADATA ONLY (set include_full_content=true for full text)
```

---

### 3. **AI Analysis Tries to Load Content (Fails)**

**File:** `omics_oracle_v2/api/routes/agents.py:1314-1328`

```python
# Load parsed content from disk if not available in dataset object
abstract_text = ft.abstract if hasattr(ft, "abstract") and ft.abstract else None
methods_text = ft.methods if hasattr(ft, "methods") and ft.methods else None
# ...

# If content not in object, load from disk using ParsedCache
if not any([abstract_text, methods_text, results_text, discussion_text]):
    if hasattr(ft, "pmid") and ft.pmid:
        try:
            cached_data = await parsed_cache.get(ft.pmid)  # ← Tries to load
            if cached_data:
                content_data = cached_data.get("content", {})
                abstract_text = content_data.get("abstract", "")
                # ...
        except Exception as e:
            logger.warning(f"[ANALYZE] Could not load parsed content for PMID {ft.pmid}: {e}")
```

**What Happens:**
1. `ft.abstract` doesn't exist (only `ft.has_abstract = true`)
2. All text variables are `None`
3. Tries `parsed_cache.get(pmid)`
4. **Cache file doesn't exist** → Returns `None`
5. All text variables remain `None`

**Result in Prompt:**
```python
dataset_info.extend([
    f"   Abstract: {abstract_text[:250] if abstract_text else 'N/A'}...",  # ← 'N/A'
    f"   Methods: {methods_text[:400] if methods_text else 'N/A'}...",     # ← 'N/A'
    f"   Results: {results_text[:400] if results_text else 'N/A'}...",     # ← 'N/A'
    f"   Discussion: {discussion_text[:250] if discussion_text else 'N/A'}...",  # ← 'N/A'
])
```

**Actual Prompt Sent to GPT-4:**
```
1. **GSE296967** (Relevance: 20%)
   Title: CD105+ fibroblasts support an immunosuppressive niche...
   Organism: Unknown organism, Samples: 30
   GEO Summary: Background: Aging is the greatest risk factor for breast cancer...

   [DOC] Full-text content from 1 of 1 linked publication(s):

   Paper 1: CD105+ fibroblasts support... (PMID: 40375322)
   Abstract: N/A...
   Methods: N/A...
   Results: N/A...
   Discussion: N/A...

Note: Analysis based on GEO metadata only (no full-text papers available).
```

**Counter Variable:**
```python
total_fulltext_papers = 0  # ← Never increments because all content is N/A
```

So the final prompt includes:
```
Note: Analysis based on GEO metadata only (no full-text papers available).
```

---

## 🐛 Root Causes

### **Bug #1: Cache Not Being Saved**

**Location:** `omics_oracle_v2/api/routes/agents.py:754-773`

PDF is parsed during `enrich-fulltext` and cache is supposed to be saved:

```python
extractor = PDFExtractor(enable_enrichment=True)
parsed_content = extractor.extract_text(
    Path(pub.pdf_path), 
    metadata={"pmid": pub.pmid, "title": pub.title}
)

# Cache it for future use
await cache.save(
    publication_id=pub.pmid,
    content=parsed_content,
    source_file=str(pub.pdf_path),
    source_type="pdf",
)
logger.info(f"   [CACHE] Saved parsed content for {pub.pmid}")
```

**But:** The `data/fulltext/parsed/` directory doesn't exist! Cache save is either:
- Failing silently
- Not being called
- Saving to wrong location

---

### **Bug #2: Frontend Doesn't Request Full Content**

**Location:** `omics_oracle_v2/api/static/dashboard_v2.html:~1490`

When "Download Papers" button is clicked:

```javascript
const response = await authenticatedFetch('http://localhost:8000/api/agents/enrich-fulltext', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        geo_id: dataset.geo_id,
        max_papers: null,  // Download all
        download_original: true,
        include_citing_papers: false
        // ❌ MISSING: include_full_content: true
    })
});
```

**Should Be:**
```javascript
body: JSON.stringify({
    geo_id: dataset.geo_id,
    max_papers: null,
    download_original: true,
    include_citing_papers: false,
    include_full_content: true  // ← ADD THIS
})
```

---

### **Bug #3: UI Status Not Updated**

The frontend shows:
- "1 PDF available for AI analysis" ✅ (Correct - based on `fulltext.length`)
- "0/1 PDF downloaded" ❌ (Wrong - should show 1/1)
- "0% processed" ❌ (Wrong - should show 100%)

**Location:** `dashboard_v2.html` - PDF download status calculation

The card footer shows:
```html
📄 0/1 PDF downloaded
📊 0% processed
```

But this is reading from the **original dataset metadata**, not the enriched fulltext response.

---

## 🔧 Required Fixes

### **Fix #1: Investigate Cache Save Failure** ⚠️ HIGH PRIORITY

**Action:**
1. Check if `ParsedCache.save()` is being called successfully
2. Verify cache directory creation
3. Add error handling and logging
4. Test cache retrieval

**Files to Check:**
- `omics_oracle_v2/lib/pipelines/text_enrichment/parsed_cache.py`
- Look for `async def save()` method
- Verify directory creation logic

---

### **Fix #2: Frontend Sends `include_full_content=true`** ⚠️ HIGH PRIORITY

**File:** `omics_oracle_v2/api/static/dashboard_v2.html`

**Line:** ~1495 (in `downloadPapersForDataset()` function)

**Change:**
```javascript
// OLD:
body: JSON.stringify({
    geo_id: dataset.geo_id,
    max_papers: null,
    download_original: true,
    include_citing_papers: false
})

// NEW:
body: JSON.stringify({
    geo_id: dataset.geo_id,
    max_papers: null,
    download_original: true,
    include_citing_papers: false,
    include_full_content: true  // ← ADD THIS
})
```

**Impact:**
- Dataset response will include full text content
- AI Analysis will have immediate access to content
- No need to load from cache

**Trade-off:**
- Larger HTTP response size (could trigger HTTP/2 errors for many papers)
- Solution: Only include for single-dataset enrichment (Download Papers button)

---

### **Fix #3: Update UI Status After Enrichment** 🔧 MEDIUM PRIORITY

**File:** `omics_oracle_v2/api/static/dashboard_v2.html`

**Line:** ~1520 (after enrichment response received)

**Change:**
```javascript
// After enrichment completes:
const enrichedData = await response.json();

// Update the dataset in currentResults
currentResults[index] = enrichedData.datasets[0];

// Re-render the card to show updated status
displayResults(currentResults);  // ← Re-render all cards
```

**Better Approach:**
```javascript
// Update specific card without full re-render
updateDatasetCard(index, enrichedData.datasets[0]);

function updateDatasetCard(index, enrichedDataset) {
    // Update PDF count
    const pdfCount = enrichedDataset.fulltext ? enrichedDataset.fulltext.length : 0;
    const totalPMIDs = enrichedDataset.pubmed_ids ? enrichedDataset.pubmed_ids.length : 0;
    
    // Update status display
    const cardFooter = document.querySelector(`#card-${index} .dataset-footer`);
    cardFooter.innerHTML = `
        📄 ${pdfCount}/${totalPMIDs} PDF downloaded
        📊 ${pdfCount === 0 ? 0 : 100}% processed
    `;
    
    // Update dataset in currentResults
    currentResults[index] = enrichedDataset;
}
```

---

## 🎯 Immediate Action Plan

### **Step 1: Verify Cache Issue** (5 mins)

Check if cache directory exists and investigate save logic:

```bash
# Check if directory exists
ls -la data/fulltext/parsed/

# Check ParsedCache save logic
grep -n "async def save" omics_oracle_v2/lib/pipelines/text_enrichment/parsed_cache.py
```

---

### **Step 2: Apply Frontend Fix** (2 mins)

Add `include_full_content: true` to enrich-fulltext request:

**File:** `dashboard_v2.html:~1495`

```diff
  body: JSON.stringify({
      geo_id: dataset.geo_id,
      max_papers: null,
      download_original: true,
      include_citing_papers: false,
+     include_full_content: true
  })
```

---

### **Step 3: Test End-to-End** (10 mins)

1. Search for "BRCA1 mutations"
2. Click "Download Papers" on GSE296967
3. Wait for enrichment to complete
4. Click "AI Analysis"
5. **Verify prompt includes actual Methods/Results text** (not "N/A")

**Expected Log:**
```
[ANALYZE] Loaded parsed content from cache for PMID 40375322
   Abstract: Background: Aging is the greatest risk factor...
   Methods: Primary fibroblast cultures were established...
   Results: We found that peri-epithelial CD105+ fibroblasts...
```

---

## 📋 Testing Checklist

- [ ] Cache directory created: `data/fulltext/parsed/`
- [ ] Cache file saved: `data/fulltext/parsed/40375322.json.gz`
- [ ] Frontend sends `include_full_content: true`
- [ ] Enrichment response includes `fulltext[0].abstract` (not just `has_abstract`)
- [ ] AI Analysis prompt shows actual Methods text (not "N/A")
- [ ] AI Analysis summary references specific experimental details
- [ ] UI shows "1/1 PDF downloaded" after enrichment
- [ ] UI shows "100% processed" after enrichment

---

## 🚨 Impact Assessment

**Current State:**
- ❌ AI Analysis provides NO value for datasets with PDFs
- ❌ Users think they're getting full-text analysis but only get GEO summary analysis
- ❌ Wasted API calls to GPT-4 for minimal context
- ❌ Wasted time downloading/parsing PDFs that aren't used

**Expected Improvement After Fixes:**
- ✅ AI Analysis references actual Methods, Results, Discussion sections
- ✅ Specific experimental details and findings cited
- ✅ Meaningful comparisons of methodologies
- ✅ 40-50% quality improvement in analysis (as designed for RAG system)
- ✅ Accurate UI status display

---

## 📌 Related Issues

### **Issue #1: HTTP/2 Framing Layer Errors**

**Context:** Previous issues with large HTTP responses (Oct 13-14)

**Concern:** Setting `include_full_content=true` could trigger HTTP/2 errors if:
- Multiple papers with long full-text content
- Total response size > 16 MB

**Mitigation:**
1. Only use `include_full_content=true` for **single-dataset enrichment** (Download Papers button)
2. For bulk enrichment (multiple datasets), keep `include_full_content=false`
3. Rely on cache for bulk AI Analysis (load from disk as designed)

**Fix Priority:** Fix cache save/load first, then optionally use `include_full_content` as optimization

---

### **Issue #2: Cache Not Persisting**

**Symptoms:**
- PDF parsed successfully during enrichment
- Cache save called with no errors
- But cache file doesn't exist on disk

**Possible Causes:**
1. Directory permission issues
2. Async save not awaited properly
3. Cache path misconfigured
4. Silent exception in save logic

**Investigation Needed:** Read `ParsedCache.save()` implementation

---

## 🎓 Lessons Learned

### **Design Insight: Metadata-Only Response is Intentional**

The `include_full_content` parameter exists specifically to handle:
- **Bulk operations:** Avoid HTTP/2 errors with 20+ datasets
- **Caching strategy:** Send metadata, load full content from disk when needed
- **Response size optimization:** Typical dataset metadata = 2 KB, full-text = 50+ KB

**The design is correct**, but **the cache is broken**.

### **Frontend Assumption Was Wrong**

The frontend assumed that after enrichment, the dataset object would automatically have full content attached. But:
- Backend intentionally strips full content (by default)
- Frontend should either:
  - Request `include_full_content=true` for single enrichment
  - OR rely on backend loading from cache during analysis

**The fix should be on the backend cache, not the frontend request.**

---

## ✅ Recommended Solution

### **PRIMARY FIX: Fix the cache save/load** (Backend)

1. Investigate why `ParsedCache.save()` isn't persisting files
2. Fix cache directory creation
3. Verify cache retrieval in AI Analysis endpoint
4. Test with PMID 40375322

**Benefits:**
- Works for both single and bulk analysis
- No HTTP/2 errors
- Follows original design intent
- Scalable to many datasets

---

### **OPTIONAL FIX: Frontend sends `include_full_content=true`** (Frontend)

Only for **single-dataset enrichment** (Download Papers button):

1. Add `include_full_content: true` to request
2. Dataset object will have immediate access to content
3. AI Analysis skips cache load step

**Benefits:**
- Faster analysis (no disk I/O)
- Works even if cache is broken
- Simpler debugging

**Risks:**
- Larger HTTP response (but safe for single dataset)
- Doesn't scale to bulk operations

---

## 📊 Conclusion

**User's observation is validated:** AI Analysis is indeed only using GEO summary, not the parsed PDF content.

**Root cause:** Cache save/load mechanism is broken. Parsed content exists during enrichment but is not persisted to disk or not being retrieved during analysis.

**Priority:** Fix `ParsedCache` implementation first. Frontend fix is optional optimization.

**Expected Timeline:**
- Cache investigation: 10-15 mins
- Cache fix: 5-10 mins
- Testing: 5-10 mins
- **Total: 20-35 minutes**

---

**Next Step:** Investigate `ParsedCache.save()` method to understand why cache files aren't being created.
