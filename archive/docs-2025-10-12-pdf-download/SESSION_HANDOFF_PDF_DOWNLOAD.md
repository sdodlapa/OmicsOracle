# SESSION HANDOFF - PDF Download Issue
**Date**: October 12, 2025  
**Time**: 12:15 PM PST  
**Branch**: fulltext-implementation-20251011

---

## 🚨 CURRENT PROBLEM

**User sees**: "Downloaded 1 of 1 paper(s)" ✅  
**But AI says**: "full text unavailable" ❌

**Root Cause**: HTTP 403 Forbidden when downloading PDF from institutional access

---

## 📊 EVIDENCE FROM LOGS

```
Attempt 1 failed: HTTP 403 from https://academic.oup.com/nar/article/doi/10.1093/nar/gkaf101/8041969
Attempt 2 failed: HTTP 403 from https://academic.oup.com/nar/article/doi/10.1093/nar/gkaf101/8041969
pdf_path: None
```

---

## ✅ FIXES COMPLETED

1. ✅ Added `fulltext_url` and `fulltext_source` to Publication model
2. ✅ Fixed PDF download to set `pdf_path` from results
3. ✅ Added `url`, `source`, `pdf_path` to FullTextContent model
4. ✅ Removed broken download_utils.py (archived)
5. ✅ Using ONLY PDFDownloadManager

---

## 🔴 REMAINING ISSUES

### Issue #1: HTTP 403 - Institutional Access Blocked
**Problem**: Oxford University Press blocks the download
**File**: Logs show institutional URL returns 403

**Solution Needed**: Try other sources when institutional fails:
- PMC (has PMC11851118)
- Unpaywall
- CORE
- Sci-Hub (fallback)

### Issue #2: FullTextManager Stops After First Success
**Problem**: Gets institutional URL (success), tries download (fails 403), stops
**Expected**: Should try PMC, Unpaywall, etc. if download fails

**Code Location**: `omics_oracle_v2/api/routes/agents.py` lines 509-540

---

## 🎯 IMMEDIATE NEXT STEPS

1. **Add logging** to see what sources FullTextManager tries:
```python
# Line ~509 in agents.py
logger.info(f"🔍 STEP 1: Getting URLs from FullTextManager...")
fulltext_results = await fulltext_manager.get_fulltext_batch(publications)

for result in fulltext_results:
    logger.info(f"   Source: {result.source.value}, URL: {result.url}, Success: {result.success}")
```

2. **Check if FullTextManager tries multiple sources** or stops at first URL

3. **Fix waterfall logic** - should try all sources until download succeeds

---

## 📁 KEY FILES

### Modified Files
- `omics_oracle_v2/api/routes/agents.py` - PDF download endpoint
- `omics_oracle_v2/lib/publications/models.py` - Added fulltext_url field
- `omics_oracle_v2/api/models/responses.py` - Added url/source/pdf_path to FullTextContent
- `omics_oracle_v2/lib/fulltext/manager.py` - Removed download logic

### Critical Code Sections
- **Download**: `agents.py` lines 520-540
- **Parse**: `agents.py` lines 544-580
- **FullTextManager**: `manager.py` lines 1050-1130 (waterfall logic)

---

## 🧪 TEST CASE

**PMID**: 39997216  
**DOI**: 10.1093/nar/gkaf101  
**PMC ID**: PMC11851118  

**Expected Flow**:
1. Try institutional → 403 Forbidden
2. Try PMC → Should succeed with PMC11851118
3. Download PDF from PMC
4. Parse PDF
5. AI gets full content

---

## 💻 CURRENT SERVER STATE

- ✅ Server running on http://localhost:8000
- ✅ All code changes applied
- ✅ Models updated with new fields
- ⚠️ Missing: Detailed logging in download flow
- ⚠️ Missing: Multi-source fallback logic

---

## 🔧 QUICK COMMANDS

```bash
# Check logs
tail -f logs/omics_api.log

# Check if PDF downloaded
ls -la data/fulltext/pdfs/

# Restart server
pkill -f "uvicorn.*omics_oracle" && ./start_omics_oracle.sh

# Check for PMC PDFs specifically
find data -name "*PMC11851118*" -o -name "*39997216*"
```

---

## 📝 NEXT SESSION SHOULD:

1. Add verbose logging to trace source waterfall
2. Verify FullTextManager tries all sources
3. Fix if it's stopping after first URL
4. Test with PMC source specifically
5. Verify PDF downloads from PMC
6. Verify AI gets parsed content

**Focus**: Fix the waterfall - should try PMC when institutional fails!
