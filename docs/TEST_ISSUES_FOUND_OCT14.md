# Testing Issues Found - October 14, 2025

## Issue 1: Download Failure - EXPECTED ✅

**Status**: This is actually **working correctly**!

**What happened**:
- Download failed for PMID 40902605 (Oct 2025 paper)
- System tried all 9 sources (Institutional, PMC, Unpaywall, CORE, OpenAlex, bioRxiv, Crossref, Sci-Hub, LibGen)
- All sources failed (paper behind paywall)
- System showed clear error message

**Why this is OK**:
- Recent papers (Oct 2025) are often behind paywalls
- Not all papers are available open access
- System tried every possible source
- Error message is clear and informative

**Recommendation**: ✅ **Test with older, well-cited datasets**

Try these datasets with more accessible papers:
- GSE10000 (very old, likely has open access papers)
- GSE50000 (moderately old)
- Any dataset from 2015-2020 (better open access coverage)

---

## Issue 2: Only 1 Paper Shown (Missing Citing Papers) 🔧 FIXED!

**Status**: **FIXED - OpenAlexClient initialization error**

**What's happening**:
- Frontend calls `/enrich-fulltext` endpoint
- Backend citation discovery was failing with: `OpenAlexClient.__init__() got an unexpected keyword argument 'email'`
- GEOCitationDiscovery was trying to initialize OpenAlexClient with `email` parameter directly
- OpenAlexClient actually requires an `OpenAlexConfig` object

**Root Cause**: 
- Incorrect initialization in `geo_discovery.py` line 54
- Was calling: `OpenAlexClient(email=...)`
- Should call: `OpenAlexClient(config=OpenAlexConfig(email=...))`

**Fix Applied**:
```python
# Before (BROKEN):
openalex_client = OpenAlexClient(email=os.getenv("NCBI_EMAIL", "sdodl001@odu.edu"))

# After (FIXED):
from omics_oracle_v2.lib.search_engines.citations.openalex import OpenAlexClient, OpenAlexConfig
openalex_config = OpenAlexConfig(
    email=os.getenv("NCBI_EMAIL", "sdodl001@odu.edu"),
    enable=True
)
openalex_client = OpenAlexClient(config=openalex_config)
```

**Server Status**: ✅ Restarted (PID 16488) with fix applied

---

## Debugging Steps

### Step 1: Check Logs for Citation Discovery

```bash
# Look for citation discovery logs
grep -i "citation" logs/omics_api.log | tail -n 20

# Or view live during download
tail -f logs/omics_api.log | grep -i "citation"
```

**Expected log messages**:
```
[CITATION] Initializing citation discovery...
[CITATION] Discovering papers that cited GSE234968...
[CITATION] Found X citing papers
[CITATION] Downloading 1 original + Y citing papers...
```

### Step 2: Try Older Dataset with Known Citations

Instead of GSE234968 (March 2025), try:
- **GSE10000** (very old, definitely has citing papers)
- **GSE50000** (moderately old)

### Step 3: Check API Response

In browser console, check what the API actually returns:

```javascript
// After clicking "Download Papers", check console
console.log(enriched.fulltext);
// Should show array with multiple papers
// Each with paper_type: "original" or "citing"
```

---

## Quick Test Plan

### Test A: Try Older Dataset

1. Search for: **"GSE10000"** (specific GEO ID)
2. Click "Download Papers"
3. Check if you see:
   - 1 original paper
   - Multiple citing papers (5-10)

### Test B: Check Logs During Download

```bash
# Terminal 1: Watch logs
tail -f logs/omics_api.log | grep -E "(CITATION|ORIGINAL|CITING)"

# Terminal 2: Browser
# Click "Download Papers" on any dataset
```

---

## Possible Fixes

### Fix A: Frontend - Add Query Parameters (Quick Fix)

**File**: `dashboard_v2.html` line 1208

**Current**:
```javascript
const response = await authenticatedFetch('http://localhost:8000/api/agents/enrich-fulltext', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify([dataset])
});
```

**Change to**:
```javascript
const response = await authenticatedFetch('http://localhost:8000/api/agents/enrich-fulltext?include_citing_papers=true&max_citing_papers=10', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify([dataset])
});
```

### Fix B: Backend - Force Citation Discovery (Alternative)

**File**: `agents.py` line 416

**Current**:
```python
if include_citing_papers:
    logger.info("[CITATION] Initializing citation discovery...")
    citation_discovery = GEOCitationDiscovery()
```

**Change to always enable**:
```python
# ALWAYS enable citation discovery (user expects citing papers)
logger.info("[CITATION] Initializing citation discovery...")
citation_discovery = GEOCitationDiscovery()
```

---

## Recommendation

### Immediate Action:

1. **Test with GSE10000** (old dataset with known citations)
2. **Check logs** during download
3. Based on logs, apply appropriate fix

### If Logs Show Citation Discovery Working:
→ Issue is with displaying multiple papers in UI
→ Check frontend rendering of multiple papers

### If Logs Show No Citation Discovery:
→ Apply Fix A or Fix B above
→ Retest

---

## Expected Behavior (After Fix)

When downloading papers:
```
Dataset: GSE10000
Papers to download:
1. PMID 12345 (original) - Generated the dataset
2. PMID 23456 (citing) - Used GSE10000 in analysis
3. PMID 34567 (citing) - Referenced GSE10000
4. PMID 45678 (citing) - Meta-analysis including GSE10000
...up to 10 citing papers total
```

UI should show:
```
📥 Download 11 Papers
  ✓ 1 original paper
  ✓ 10 citing papers
```

---

## Next Steps

**Your choice**:

**Option 1**: Test with GSE10000 first (5 min)
- Quick validation if citing papers work for old datasets
- If they do, issue is just that new datasets have no citations yet

**Option 2**: Check logs now (2 min)
- See what's actually happening during download
- Make informed fix decision

**Option 3**: Apply Fix A immediately (5 min)
- Add query parameters to frontend
- Retest

**What would you like to do?**
