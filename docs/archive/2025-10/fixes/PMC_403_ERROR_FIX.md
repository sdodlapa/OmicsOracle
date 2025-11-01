# PMC 403 Error Fix - October 16, 2025

## Problem Summary

**Issue:** PDF downloads failing with "Download Failed After Trying All Sources" error for dataset GSE570 (PMID: 15780141).

**Root Cause:** 
1. PubMed Central (PMC) is returning HTTP 403 errors for programmatic PDF access
2. The URL pattern matching for PMC was incomplete, missing the common pattern `www.ncbi.nlm.nih.gov/pmc/`
3. Only recognized `pmc.ncbi.nlm.nih.gov` pattern, so the workaround wasn't triggering

**Evidence from Logs:**
```
[WARNING] cache attempt 1/2 failed: HTTP 403 from https://pmc.ncbi.nlm.nih.gov/articles/PMC1087880/pdf/
[FAIL] All 1 URLs failed for: Therapeutic targets for HIV-1 infection in the hos
[DEBUG] pub.pdf_url = https://www.ncbi.nlm.nih.gov/pmc/articles/PMC1087880/pdf/
[DEBUG] NOT clearing pdf_url (doesn't match PMC pattern)  ← THE BUG!
```

## Solution Implemented

### File: `omics_oracle_v2/services/fulltext_service.py`

#### Fix #1: Improved PMC URL Pattern Detection

**Before:**
```python
if pub.pdf_url and 'pmc.ncbi.nlm.nih.gov' in pub.pdf_url:
    pub.pdf_url = None  # Clear broken PMC URL
```

**After:**
```python
if pub.pdf_url and ('/pmc/' in pub.pdf_url.lower() or 'pmc.ncbi' in pub.pdf_url.lower()):
    logger.warning(f"[{geo_id}] PMID:{pub.pmid} - Skipping PMC URL (403 errors): {pub.pdf_url}")
    pub.pdf_url = None  # Force waterfall instead of using cached PMC URL
```

**Impact:** Now catches BOTH PMC URL patterns:
- ✅ `https://pmc.ncbi.nlm.nih.gov/articles/PMC1087880/pdf/` (old pattern)
- ✅ `https://www.ncbi.nlm.nih.gov/pmc/articles/PMC1087880/pdf/` (new pattern - THE FIX!)

#### Fix #2: Improved OpenAlex Fallback Trigger

**Before:**
```python
if len(result.all_urls) == 1 and 'pmc.ncbi.nlm.nih.gov' in result.all_urls[0].url:
    # Try OpenAlex
```

**After:**
```python
only_pmc = (
    len(result.all_urls) == 1 and 
    ('/pmc/' in result.all_urls[0].url.lower() or 'pmc.ncbi' in result.all_urls[0].url.lower())
)

if only_pmc:
    logger.warning(f"[{geo_id}] PMID:{pub.pmid} - Only PMC URL available, adding OpenAlex fallback")
    # Try OpenAlex
```

**Impact:** OpenAlex fallback now triggers for both PMC URL patterns.

## How The Fix Works

### Original Flow (BROKEN):
1. ✅ PubMed provides: `https://www.ncbi.nlm.nih.gov/pmc/articles/PMC1087880/pdf/`
2. ❌ Pattern check fails (only looking for `pmc.ncbi.nlm.nih.gov`)
3. ❌ Uses PMC URL as-is
4. ❌ PMC returns 403 Forbidden
5. ❌ No fallback attempted
6. ❌ Download fails completely

### New Flow (FIXED):
1. ✅ PubMed provides: `https://www.ncbi.nlm.nih.gov/pmc/articles/PMC1087880/pdf/`
2. ✅ Pattern check succeeds (matches `/pmc/` pattern)
3. ✅ Clears broken PMC URL → forces waterfall
4. ✅ FullTextManager tries all sources:
   - Institutional Access (Georgia Tech, ODU)
   - **Unpaywall** ← likely to work
   - **OpenAlex** ← likely to work
   - CORE
   - bioRxiv/arXiv
   - Crossref
   - Sci-Hub (last resort)
   - LibGen (final fallback)
5. ✅ One of the sources provides working URL
6. ✅ Download succeeds

## Expected Behavior After Fix

### For GSE570 (PMID: 15780141):

**Paper:** "Therapeutic targets for HIV-1 infection in the host"
- **DOI:** `10.1186/1742-4690-2-20`
- **Journal:** Retrovirology (BMC - Open Access)
- **Status:** Should be freely available via Unpaywall or OpenAlex

**Expected Result:**
```
✅ Success! Downloaded 1 of 1 paper(s).

Status: success

You can now use AI Analysis.
```

## Testing Checklist

- [ ] Server auto-reloaded with changes
- [ ] Search for "GSE570" in dashboard
- [ ] Click "📥 Download Papers" button
- [ ] Verify download succeeds (not 403 error)
- [ ] Check logs show OpenAlex/Unpaywall attempts
- [ ] Verify AI Analysis button becomes active

## PMC URL Patterns Now Handled

| Pattern | Example | Detection |
|---------|---------|-----------|
| Legacy PMC | `https://pmc.ncbi.nlm.nih.gov/articles/PMC1087880/pdf/` | ✅ `pmc.ncbi` check |
| Modern PMC | `https://www.ncbi.nlm.nih.gov/pmc/articles/PMC1087880/pdf/` | ✅ `/pmc/` check |
| PMC OA | `https://www.ncbi.nlm.nih.gov/pmc/articles/PMC1087880/` | ✅ `/pmc/` check |
| PMC FTP | `ftp://ftp.ncbi.nlm.nih.gov/pub/pmc/` | ✅ `/pmc/` check |

## Why PMC Returns 403

PMC has implemented stricter bot detection and rate limiting:
- User-Agent filtering (blocks automated requests)
- IP-based rate limiting
- Session/cookie requirements
- Referrer checking

**Our Solution:** Don't use PMC URLs at all - use alternative OA sources instead!

## Related Files

- `omics_oracle_v2/services/fulltext_service.py` - Main fix location
- `omics_oracle_v2/lib/pipelines/url_collection/manager.py` - FullTextManager waterfall
- `omics_oracle_v2/lib/pipelines/pdf_download/download_manager.py` - PDF downloader
- `omics_oracle_v2/api/static/dashboard_v2.html` - Error message display

## Monitoring

After fix, check logs for:
```
[{geo_id}] PMID:{pmid} - Skipping PMC URL (403 errors): https://...
[{geo_id}] PMID:{pmid} - Only PMC URL available, adding OpenAlex fallback
[{geo_id}] PMID:{pmid} - OpenAlex found PDF: https://...
```

## Metrics

**Before Fix:**
- PMC URLs: 403 errors → 100% failure
- Waterfall: Not triggered
- Success Rate: 0%

**After Fix (Expected):**
- PMC URLs: Skipped automatically
- Waterfall: Full cascade through 9 sources
- Success Rate: 70-90% (for OA papers)

## Next Steps

If downloads still fail after this fix:
1. Check if paper is truly Open Access (use Unpaywall API directly)
2. Verify DOI is correct in publication metadata
3. Check OpenAlex API response for this DOI
4. Consider adding publisher-specific sources
5. Check Sci-Hub/LibGen as last resort

## Author

- **Date:** October 16, 2025
- **Issue:** PMC 403 errors blocking all downloads
- **Fix:** Comprehensive PMC URL pattern detection
- **Impact:** Restored waterfall fallback for all PMC papers
