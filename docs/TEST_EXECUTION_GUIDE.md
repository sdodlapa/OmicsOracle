# ✅ READY FOR TESTING - Quick Start Guide

**Date:** October 13, 2025
**Status:** Application Running ✅
**URL:** http://localhost:8000

---

## ✅ PRE-FLIGHT CHECKS PASSED

- ✅ Application is running (port 8000 active)
- ✅ No old imports in API code
- ✅ Browser opened successfully
- ✅ All fixes applied:
  - Waterfall fallback fix (agents.py)
  - Resource cleanup (finally block)
  - Redis cache fix (orchestrator.py)
  - GEOparse logging fix (main.py)
  - Old system archived (~1,577 lines)
  - Deprecation warning added

---

## 🧪 TEST EXECUTION GUIDE

### Test 1: Basic Waterfall Test (5 minutes)

**In Browser (http://localhost:8000):**
1. Enter search query: `cancer immunotherapy`
2. Click "Search Datasets"
3. Wait for results (~19 datasets expected)
4. Click "Enrich with Full-text" for first dataset
5. Watch the progress

**In Terminal (watch logs):**
Look for these SUCCESS indicators:
```
✅ "⚡ Querying 10 sources in parallel"
✅ "✓ institutional: Found URL"
✅ "✓ unpaywall: Found URL"
✅ "✓ pmc: Found URL"
✅ "Trying 8 sources" (or more)
✅ "Downloaded from [source]" OR "Tried all X sources"
```

Look for these PROBLEMS (should NOT see):
```
❌ "Only tried 2 sources"
❌ "Unclosed client session"
❌ "GEOparse - GSM9258278"
❌ "Cache set failed"
```

**Expected Outcome:**
- PDFs downloaded for 70-90% of papers (up from 30-40%)
- Terminal shows ALL sources being tried
- Clean logs (no spam)

---

### Test 2: Monitor Terminal Output (2 minutes)

**Watch for Clean Logs:**

Open a second terminal and run:
```bash
cd /Users/sanjeevadodlapati/Downloads/Repos/OmicsOracle

# Watch logs in real-time
tail -f logs/omics_oracle_*.log | grep -E "sources|Downloaded|ERROR|WARNING|Trying"
```

**What You Should See:**
```
INFO - Collecting URLs from ALL sources
INFO - ⚡ Querying 10 sources in parallel...
INFO - Found 8 URLs for: [paper title]
INFO - Trying 8 sources (unpaywall, pmc, institutional...)
INFO - ✓ SUCCESS: Downloaded from unpaywall
```

**What You Should NOT See:**
```
DEBUG - GEOparse - GSM9258278  ❌ (should be silenced)
WARNING - Unclosed client session  ❌ (should be fixed)
ERROR - Cache set failed  ❌ (should be fixed)
```

---

### Test 3: Success Rate Check (10 minutes)

**Run Multiple Enrichments:**
1. Search: `breast cancer genomics`
2. Enrich 3-5 different datasets
3. Note how many papers get PDFs

**Calculate Success Rate:**
```
Papers with PDFs / Total papers attempted = Success Rate

Example:
- Dataset 1: 8/10 papers = 80%
- Dataset 2: 9/10 papers = 90%
- Dataset 3: 7/10 papers = 70%
Average: 83% success rate ✅ (much better than 30-40%!)
```

**What to Record:**
- Total papers attempted: ____
- Papers with PDFs: ____
- Success rate: ____%
- Target: 80-90%+ ✅

---

### Test 4: Specific PMIDs (Optional)

**Test Previously Failing Papers:**

These PMIDs were only trying 2-3 sources before the fix:
- PMID 39990495
- PMID 41025488

**How to Test:**
1. Find dataset containing these PMIDs (or search for them)
2. Enrich that dataset
3. Check logs for these specific PMIDs
4. Verify: Should now try 8-11 sources (not just 2-3)

**Expected:**
```
INFO - PMID 39990495: Trying 8 sources...
INFO - PMID 41025488: Trying 7 sources...
```

---

## 📊 RESULTS TEMPLATE

Copy this and fill in after testing:

```markdown
## Test Results - October 13, 2025

### Test 1: Waterfall Functionality
- [ ] ✅ / [ ] ❌ - Queries 10 sources in parallel
- [ ] ✅ / [ ] ❌ - Tries 8-11 sources per paper
- [ ] ✅ / [ ] ❌ - Downloads successful OR exhausts all sources
- Notes: _______________________________________________

### Test 2: Terminal Output Quality
- [ ] ✅ / [ ] ❌ - No GEOparse DEBUG spam
- [ ] ✅ / [ ] ❌ - No unclosed session warnings
- [ ] ✅ / [ ] ❌ - No Redis cache errors
- [ ] ✅ / [ ] ❌ - Clean, readable logs
- Notes: _______________________________________________

### Test 3: Success Rate
- Total papers attempted: _______
- Papers with PDFs: _______
- Success rate: _______% (target: 80-90%+)
- [ ] ✅ / [ ] ❌ - Success rate improved significantly
- Notes: _______________________________________________

### Test 4: Resource Management
- [ ] ✅ / [ ] ❌ - No resource leaks after multiple enrichments
- [ ] ✅ / [ ] ❌ - Cleanup logs appear
- Notes: _______________________________________________

### Overall Status:
- [ ] ✅ ALL TESTS PASSED - Ready for production
- [ ] ⚠️  MINOR ISSUES - Needs investigation (list below)
- [ ] ❌ CRITICAL ISSUES - Rollback required (list below)

Issues Found:
1. _______________________________________________
2. _______________________________________________
3. _______________________________________________
```

---

## 🎯 SUCCESS CRITERIA

Your fixes are working if you see:

1. **✅ Waterfall Working:**
   - "Querying 10 sources" appears
   - Multiple sources return URLs
   - All URLs attempted in priority order

2. **✅ High Success Rate:**
   - 80-90%+ of papers download successfully
   - Much better than previous 30-40%

3. **✅ Clean Logs:**
   - No GEOparse spam
   - No resource leak warnings
   - No cache errors
   - Only relevant INFO/WARNING/ERROR messages

4. **✅ Better Performance:**
   - Downloads complete faster (multiple sources tried in parallel)
   - No wasted retries on single URLs

---

## 🚨 TROUBLESHOOTING

### If Success Rate Still Low (<50%):
1. Check if sources are returning 403 errors (publisher paywall - expected)
2. Verify institutional access is configured
3. Check if Sci-Hub/LibGen are enabled (optional but helps)

### If Still Seeing "Only tried 2 sources":
1. Verify you restarted the application after fixes
2. Check `agents.py` has the new code
3. Run: `grep "download_with_fallback" omics_oracle_v2/api/routes/agents.py`

### If Resource Leaks Persist:
1. Check `finally` block exists in agents.py
2. Verify cleanup() is being called
3. Check logs for cleanup messages

### If Import Errors:
1. Verify old system is archived
2. Check no code is importing from `lib.fulltext`
3. Restart application

---

## 📝 QUICK COMMANDS

```bash
# Watch logs
tail -f logs/omics_oracle_*.log

# Count successful downloads
grep "Downloaded from" logs/omics_oracle_*.log | wc -l

# Find which sources are working
grep "Downloaded from" logs/omics_oracle_*.log | awk -F'from ' '{print $2}' | cut -d' ' -f1 | sort | uniq -c

# Check for issues
grep -E "ERROR|WARNING|unclosed|GEOparse.*DEBUG" logs/omics_oracle_*.log | tail -20

# Restart application (if needed)
# Stop current (Ctrl+C in terminal running start_omics_oracle.sh)
# Then:
./start_omics_oracle.sh
```

---

## ✅ NEXT ACTIONS

1. **NOW:** Run Test 1 (Basic Waterfall Test) - 5 minutes
2. **THEN:** Monitor logs for clean output - 2 minutes
3. **FINALLY:** Calculate success rate - 10 minutes
4. **DOCUMENT:** Fill in results template above
5. **REPORT:** Share findings (success rate, any issues)

---

## 🎉 EXPECTED OUTCOME

By the end of testing, you should see:

**BEFORE (What we had):**
- Success rate: 30-40%
- Sources tried: 2-3
- Terminal: Messy with spam
- Resource leaks: Yes

**AFTER (What we expect now):**
- Success rate: 80-90%+ ✅
- Sources tried: 8-11 ✅
- Terminal: Clean and readable ✅
- Resource leaks: None ✅

---

**Ready to Test!** 🚀

Start with Test 1 in the browser at: http://localhost:8000
