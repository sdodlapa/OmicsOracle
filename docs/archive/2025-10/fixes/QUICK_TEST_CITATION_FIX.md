# Quick Test Guide - Citation Discovery Fixed

**Date**: October 14, 2025  
**Status**: ✅ Two critical bugs fixed  
**Server**: Running on PID 22200  

---

## What Was Fixed

### 1. Missing `paper_type` Field
- **Error**: `"Publication" object has no field "paper_type"`
- **Fix**: Added `paper_type: Optional[str]` to Publication model
- **Impact**: No more 500 errors when downloading papers

### 2. Missing DOI for Citation Discovery
- **Error**: "Must provide either DOI or OpenAlex ID"
- **Fix**: Now fetches full publication metadata from PubMed (includes DOI)
- **Impact**: Citation discovery now works, should show 1 + N citing papers

---

## How to Test

### Quick Test: GSE189158 (Best Test Case)
This dataset has **7 known citations** per Google Scholar.

**Steps**:
1. Refresh browser: http://localhost:8000/dashboard
2. Search: `GSE189158` or `NOMe-HiC`
3. Click: **Download Papers** button
4. **Expected Result**: Shows **8 papers** (1 original + 7 citing)

**What to Look For**:
- ✅ No error messages
- ✅ Shows "8 linked papers" or "Downloading 8 papers..."
- ✅ Card expands showing paper list
- ✅ Papers marked as "Original Paper" or "Citing Paper"
- ✅ Original paper (PMID 36927507) downloads successfully

---

## Alternative Test: GSE281238
This dataset has **1 citation** per your report.

**Steps**:
1. Search: `sci-L3` or `GSE281238`
2. Click: **Download Papers**
3. **Expected Result**: Shows **2 papers** (1 original + 1 citing)

**Note**: Very recent (Feb 2025), so citing paper may not be indexed in OpenAlex yet. If you only see 1 paper, this is OK - try GSE189158 instead.

---

## Monitor Logs (Optional)

```bash
# Watch citation discovery in real-time
tail -f logs/omics_api.log | grep -i "citation\|citing\|doi"
```

**Expected Log Messages**:
```
Fetching full publication details for PMID 36927507
Found original paper: NOMe-HiC... DOI: 10.1186/s13059-023-02889-x
Found 7 citing papers from OpenAlex
Downloading 8 papers (1 original + 7 citing)
```

---

## Success Criteria

| Check | Expected |
|-------|----------|
| No 500 errors | ✅ |
| GSE189158 shows 8 papers | ✅ |
| Papers marked as "original"/"citing" | ✅ |
| Original paper downloads | ✅ |
| Log shows DOI fetched | ✅ |
| Log shows citing papers found | ✅ |

---

## If Something Fails

### Still Seeing Only 1 Paper?
- Check logs for "No citing papers found"
- Try older dataset (GSE10000, GSE50000)
- Dataset may genuinely have no citations in OpenAlex

### Still Getting 500 Error?
- Check logs for specific error message
- Verify server restarted (PID should be 22200 or newer)
- Try refreshing browser (clear cache)

### Papers Not Downloading?
- Expected for recent papers (behind paywall)
- Check "PDF download pending..." vs "PDF downloaded"
- Try older open access papers

---

## What's Fixed vs What's Not

### ✅ FIXED
- Citation discovery initialization (OpenAlexConfig)
- Citation discovery DOI lookup (fetch from PubMed)
- Publication model paper_type field
- Search dict handling

### 🔄 NOT YET FIXED (Non-Critical)
- PubMed search async/sync issue (doesn't affect GEO search)
- OpenAlex search method name (doesn't affect GEO search)
- These are in multi-source orchestrator, not GEO path

---

## Next Steps After Testing

If tests pass:
1. ✅ Mark Test 3.1 as PASS
2. ✅ Continue to Test 3.2 (verify citation metadata)
3. ✅ Continue to Test 4.1 (PDF parsing)
4. ✅ Continue to Test 5.1 (AI Analysis)

If tests fail:
1. 🔍 Share logs for diagnosis
2. 🔍 Try different datasets
3. 🔍 Check server status

---

## Quick Checklist

- [ ] Server running (check `tail -n 5 logs/omics_api.log`)
- [ ] Browser refreshed
- [ ] Searched for GSE189158
- [ ] Clicked "Download Papers"
- [ ] Saw 8 papers or download progress
- [ ] No error messages shown
- [ ] Original paper downloaded successfully

**If all checked**: ✅ Citation discovery is working! 🎉

---

## Documentation

Full details in:
- `docs/CRITICAL_FIXES_OCT14_PART2.md` - Complete technical analysis
- `docs/CITATION_FIX_VALIDATION.md` - Previous fix details
- `docs/TEST_ISSUES_FOUND_OCT14.md` - Bug tracking

Commits:
- `b4ae6a6` - OpenAlexClient initialization fix
- `a0f9c40` - paper_type field + DOI fetch fix (this one)
