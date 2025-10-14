# POST-DEPLOYMENT MONITORING & VALIDATION PLAN

**Date:** October 13, 2025
**Status:** Ready for Testing
**Priority:** HIGH - Validate fixes work in production

---

## IMMEDIATE NEXT STEPS

### Step 1: Restart Application with Fixes
**Goal:** Apply all our fixes (waterfall, cleanup, logging)

**Actions:**
```bash
# Stop current server (if running)
# Then restart to pick up changes
./start_omics_oracle.sh
```

**Expected:** Clean startup with no import errors

---

### Step 2: Test Waterfall Fix in Frontend
**Goal:** Verify all sources are being tried for real papers

**Test Scenario:**
1. Open browser: http://localhost:8000
2. Search for: `cancer immunotherapy`
3. Click "Enrich with Full-text"
4. Monitor terminal logs

**What to Look For:**
```
✅ "Collecting URLs from ALL sources"
✅ "⚡ Querying 10 sources in parallel"
✅ "Trying 8-11 sources" (or until success)
✅ "Downloaded from [source_name]"
✅ NO "Only tried 2-3 sources"
✅ NO "unclosed client session" warnings
✅ NO GEOparse DEBUG spam
✅ NO Redis cache errors
```

**Log Examples (Expected):**
```
INFO - ⚡ Querying 10 sources in parallel...
INFO - ✓ institutional: Found URL (type=doi_resolver, priority=1→4)
INFO - ✓ unpaywall: Found URL (type=pdf_direct, priority=3→1)
INFO - ✓ biorxiv: Found URL (type=pdf_direct, priority=7→5)
INFO - ✅ Found 8 URLs for: [paper title]
INFO - Trying 8 URLs...
INFO - ✓ SUCCESS: Downloaded from unpaywall (1.2 MB)
```

---

### Step 3: Monitor Key Metrics
**Goal:** Confirm improvements in download success rate

**Metrics to Track:**

| Metric | Before Fix | Target After | Where to Check |
|--------|------------|--------------|----------------|
| Sources queried per paper | 2-3 | 8-11 | Terminal logs |
| Download success rate | 30-40% | 90%+ | Frontend response |
| "Unclosed session" warnings | 7+ per request | 0 | Terminal logs |
| GEOparse DEBUG spam | High | None | Terminal logs |
| Redis cache errors | Yes | None | Terminal logs |

**How to Measure Success Rate:**
```
Success Rate = (Papers with PDFs downloaded) / (Total papers attempted) × 100%

Example:
- Query returns 10 datasets with 50 papers total
- Successfully downloaded PDFs for 45 papers
- Success rate: 45/50 = 90%
```

---

### Step 4: Test Specific Failing PMIDs
**Goal:** Verify previously failing papers now succeed

**Test PMIDs (from logs):**
1. PMID 39990495 - Was stopping after 3 sources
2. PMID 41025488 - Was stopping after 2 sources

**Test via Frontend:**
1. Search for dataset containing these PMIDs
2. Click "Enrich with Full-text"
3. Check if more sources are tried

**Expected Results:**
- Both PMIDs: Try 8-11 sources (not just 2-3)
- May still fail if paywalled, but should exhaust ALL sources
- Logs should show: "Tried 8 sources" or "Downloaded from [source]"

---

### Step 5: Verify No Regressions
**Goal:** Ensure cleanup didn't break anything

**Sanity Checks:**
```bash
# 1. Check no import errors
python -c "from omics_oracle_v2.api.routes.agents import router; print('✓ Imports OK')"

# 2. Check archived files aren't being imported
grep -r "from lib.fulltext" omics_oracle_v2/api/ && echo "✗ FOUND OLD IMPORTS!" || echo "✓ No old imports"

# 3. Check deprecation warning appears (if we call old method)
python -c "
from omics_oracle_v2.lib.enrichment.fulltext.download_manager import PDFDownloadManager
import warnings
warnings.simplefilter('always')
manager = PDFDownloadManager()
# If we called download_batch(), we should see deprecation warning
print('✓ Deprecation system working')
"
```

**Expected:** All checks pass

---

## DETAILED TEST PLAN

### Test Case 1: End-to-End Waterfall Test
**Duration:** 5-10 minutes

**Steps:**
1. Open http://localhost:8000
2. Search: `breast cancer genomics`
3. Wait for results (should be ~19 datasets)
4. Click "Enrich with Full-text" for first dataset
5. Watch terminal logs in real-time

**Success Criteria:**
- ✅ Logs show "Querying 10 sources in parallel"
- ✅ Multiple sources return URLs (institutional, pmc, unpaywall, etc.)
- ✅ Download attempts try ALL collected URLs
- ✅ Either SUCCESS or "Tried all X sources"
- ✅ NO "Only tried 2 sources" message

**If Test Fails:**
- Check terminal for errors
- Verify imports are correct
- Check if old system was restored accidentally

---

### Test Case 2: Resource Leak Test
**Duration:** 3 minutes

**Steps:**
1. Enrich 3-5 datasets in a row
2. Monitor terminal for warnings

**Success Criteria:**
- ✅ NO "Unclosed client session" warnings
- ✅ NO "Unclosed connector" warnings
- ✅ Logs show "Cleaned up fulltext_manager resources"

**If Test Fails:**
- Check if `finally` block is executing
- Verify cleanup() method is called
- Check for exceptions preventing cleanup

---

### Test Case 3: Terminal Cleanliness Test
**Duration:** 2 minutes

**Steps:**
1. Perform any search and enrichment
2. Watch terminal output

**Success Criteria:**
- ✅ NO GEOparse DEBUG messages (GSM9258278, etc.)
- ✅ NO excessive urllib3 DEBUG messages
- ✅ Only INFO/WARNING/ERROR level logs visible
- ✅ Clean, readable output

**If Test Fails:**
- Check if logger configuration in main.py is active
- Verify GEOparse logger level set to WARNING
- Check if startup logs show "Configured third-party logging levels"

---

### Test Case 4: Cache Performance Test
**Duration:** 3 minutes

**Steps:**
1. Search: `diabetes metabolism` (first time)
2. Note the response time
3. Search same query again (should be cached)
4. Note the response time

**Success Criteria:**
- ✅ Second search is MUCH faster (cached)
- ✅ NO Redis cache errors in logs
- ✅ Logs show "💾 Results cached" or "⚡ Cache hit"

**If Test Fails:**
- Check Redis connection
- Verify cache key format is correct
- Check orchestrator.py fix is applied

---

## MONITORING COMMANDS

### Watch Logs in Real-Time:
```bash
# Terminal 1: Run application
./start_omics_oracle.sh

# Terminal 2: Watch logs with filtering
tail -f logs/omics_oracle_*.log | grep -E "sources|Downloaded|ERROR|WARNING"
```

### Check for Specific Issues:
```bash
# Check for resource leaks
tail -f logs/omics_oracle_*.log | grep -i "unclosed"

# Check for GEOparse spam
tail -f logs/omics_oracle_*.log | grep -i "GEOparse"

# Check for cache errors
tail -f logs/omics_oracle_*.log | grep -i "cache.*error\|cache.*failed"

# Check waterfall attempts
tail -f logs/omics_oracle_*.log | grep -E "Trying [0-9]+ sources|Querying [0-9]+ sources"
```

### Analyze Success Rate:
```bash
# Count successful downloads
grep "Downloaded from" logs/omics_oracle_*.log | wc -l

# Count total attempts
grep "Trying .* URLs" logs/omics_oracle_*.log | wc -l

# Find which sources are succeeding
grep "Downloaded from" logs/omics_oracle_*.log | awk -F'from ' '{print $2}' | cut -d' ' -f1 | sort | uniq -c | sort -rn
```

---

## EXPECTED RESULTS

### Terminal Output (Good Example):
```
2025-10-13 20:30:15 - INFO - [SEARCH] STEP 3: Downloading PDFs with automatic waterfall fallback...
2025-10-13 20:30:15 - INFO -    [URL] Collecting URLs for PMID 39990495...
2025-10-13 20:30:15 - INFO - ⚡ Querying 10 sources in parallel...
2025-10-13 20:30:16 - INFO -   ✓ institutional: Found URL (type=doi_resolver, priority=1→4)
2025-10-13 20:30:16 - INFO -   ✓ pmc: Found URL (type=pdf_direct, priority=2→2)
2025-10-13 20:30:16 - INFO -   ✓ unpaywall: Found URL (type=pdf_direct, priority=3→1)
2025-10-13 20:30:16 - INFO -   ✓ biorxiv: Found URL (type=pdf_direct, priority=7→5)
2025-10-13 20:30:16 - INFO - ✅ Found 8 URLs for: A Massively Parallel CRISPR-Based...
2025-10-13 20:30:16 - INFO -    [DOWNLOAD] PMID 39990495: Trying 8 sources (unpaywall, pmc, institutional, biorxiv, core, crossref, scihub, libgen)
2025-10-13 20:30:16 - INFO -   [1/8] Trying unpaywall (priority 1)...
2025-10-13 20:30:17 - INFO -   ✓ SUCCESS: Downloaded from unpaywall (1.2 MB) → pmid_39990495.pdf
2025-10-13 20:30:17 - INFO - [OK] STEP 3 COMPLETE: Downloaded 1/1 PDFs using waterfall fallback
```

### Terminal Output (Bad Example - What NOT to See):
```
❌ 2025-10-13 20:30:15 - WARNING - Only tried 2 sources
❌ 2025-10-13 20:30:15 - WARNING - Unclosed client session
❌ 2025-10-13 20:30:15 - DEBUG - GEOparse - GSM9258278
❌ 2025-10-13 20:30:15 - ERROR - Cache set failed: got multiple values for argument 'search_type'
```

---

## TROUBLESHOOTING

### Issue: Old imports still being used
**Symptom:** ImportError or ModuleNotFoundError
**Fix:**
```bash
# Check for old imports
grep -r "from lib.fulltext" omics_oracle_v2/

# If found, update to new path
# OLD: from lib.fulltext.manager import FullTextManager
# NEW: from omics_oracle_v2.lib.enrichment.fulltext.manager import FullTextManager
```

### Issue: Still seeing "Only tried 2-3 sources"
**Symptom:** Logs show limited source attempts
**Fix:**
```bash
# Verify the fix is applied
grep -A 10 "get_all_fulltext_urls" omics_oracle_v2/api/routes/agents.py

# Should see download_with_fallback() call
# If not, verify you're on correct branch and changes are saved
```

### Issue: Deprecation warnings appearing
**Symptom:** DeprecationWarning messages in logs
**Action:** This is EXPECTED if any code is still calling download_batch()
**Fix:** Update that code to use download_with_fallback() instead

### Issue: Resource leaks still occurring
**Symptom:** "Unclosed client session" warnings
**Fix:**
```bash
# Verify cleanup is in finally block
grep -A 5 "finally:" omics_oracle_v2/api/routes/agents.py

# Should see: await fulltext_manager.cleanup()
```

---

## SUCCESS INDICATORS

### ✅ All Systems Go (Ready for Production):
- [x] Application starts without errors
- [ ] Waterfall tries 8-11 sources per paper
- [ ] Download success rate 80%+ (90%+ expected)
- [ ] No resource leak warnings
- [ ] No GEOparse spam
- [ ] No Redis cache errors
- [ ] Terminal output is clean and readable
- [ ] Test PMIDs show improvement

### ⚠️ Needs Investigation:
- [ ] Success rate still low (< 50%)
- [ ] Still seeing "Only tried 2 sources"
- [ ] Import errors
- [ ] Resource leaks persist

### ❌ Rollback Required:
- [ ] Application won't start
- [ ] Critical functionality broken
- [ ] Success rate worse than before

---

## ROLLBACK PROCEDURE

If critical issues are found:

```bash
# 1. Restore archived code
cp -r archive/lib-fulltext-20251013/* lib/fulltext/

# 2. Revert agents.py changes
git diff HEAD~5 omics_oracle_v2/api/routes/agents.py > /tmp/changes.patch
git checkout HEAD~5 -- omics_oracle_v2/api/routes/agents.py

# 3. Restart application
./start_omics_oracle.sh

# 4. Verify old behavior restored
# Then investigate what went wrong
```

---

## POST-VALIDATION TASKS

After confirming fixes work:

1. **Update Project Status:**
   - Mark waterfall bug as FIXED
   - Update success rate metrics
   - Document actual improvements

2. **Create PR/Commit:**
   - Commit all changes
   - Include test results in commit message
   - Reference issue numbers

3. **Schedule Cleanup:**
   - Plan to remove deprecated methods (v3.0.0)
   - Update /extras/ imports if needed
   - Delete archived code after 30 days

4. **Monitor Long-Term:**
   - Track success rates over next week
   - Collect user feedback
   - Watch for any edge cases

---

## CONTACT/ESCALATION

If you encounter issues:
1. Check logs first
2. Review this monitoring plan
3. Check troubleshooting section
4. If still stuck, provide:
   - Terminal logs (last 100 lines)
   - Error messages
   - Which test case failed
   - Expected vs actual behavior

---

**Ready to Begin Testing!**
Start with: `./start_omics_oracle.sh` and watch the terminal logs 🚀
