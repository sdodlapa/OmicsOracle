# Frontend Testing Checklist

**Date**: October 14, 2025  
**Purpose**: Manual validation of end-to-end user experience  
**Estimated Time**: 2-3 hours  
**Tester**: _____________  

## Pre-Testing Setup

### ✅ Environment Check
```bash
# 1. Ensure system is running
cd /Users/sanjeevadodlapati/Downloads/Repos/OmicsOracle
./start_omics_oracle.sh

# 2. Verify services are up
curl http://localhost:8000/health  # Should return {"status": "healthy"}

# 3. Open frontend
# Browser: http://localhost:3000 (or your frontend URL)

# 4. Check logs are clean
tail -f logs/omics_oracle.log
```

### ✅ Pre-Test Data Cleanup (Optional)
```bash
# Start fresh (optional - only if you want clean state)
rm -rf data/pdfs/TEST_*
rm -f data/geo_registry_test.db
```

---

## Test Suite 1: Basic Search Functionality

### Test 1.1: Simple Search Query ⬜

**Objective**: Verify basic search works and returns GEO datasets

**Steps**:
1. Open frontend homepage
2. Enter search query: **"breast cancer biomarkers"**
3. Click "Search" or press Enter
4. Wait for results (should be < 10 seconds)

**Expected Results**:
- ✅ Search completes without errors
- ✅ Returns 5-20 GEO datasets
- ✅ Each dataset shows:
  - GEO ID (e.g., GSE12345)
  - Title
  - Organism
  - Sample count
  - Relevance score
  - Match reasons
- ✅ Results are sorted by relevance (highest first)

**Actual Results**:
```
[ ] PASS - All expected results met
[ ] FAIL - Issues found (describe below)

Issues:
_________________________________________________
_________________________________________________
```

**Screenshots**: (if possible, attach or describe what you see)

---

### Test 1.2: Entity Recognition ⬜

**Objective**: Verify NLP entity extraction works

**Steps**:
1. Enter query: **"TP53 mutations in lung cancer patients"**
2. Click "Search"
3. Observe if entities are highlighted/detected (if UI shows this)

**Expected Results**:
- ✅ Should detect:
  - Gene: TP53
  - Disease: lung cancer
- ✅ Search results should be relevant to both gene and disease

**Actual Results**:
```
[ ] PASS
[ ] FAIL - Issues:
_________________________________________________
```

---

### Test 1.3: No Results Handling ⬜

**Objective**: Verify graceful handling of no results

**Steps**:
1. Enter invalid query: **"xyzinvalidquery123nonsense"**
2. Click "Search"

**Expected Results**:
- ✅ Shows clear message: "No datasets found" or similar
- ✅ No error messages or crashes
- ✅ Suggests trying different keywords

**Actual Results**:
```
[ ] PASS
[ ] FAIL - Issues:
_________________________________________________
```

---

### Test 1.4: Special Characters ⬜

**Objective**: Verify search handles special characters

**Steps**:
1. Enter query: **"BRCA1/BRCA2 & p53"**
2. Click "Search"

**Expected Results**:
- ✅ Search doesn't crash
- ✅ Returns relevant results (even if special chars ignored)

**Actual Results**:
```
[ ] PASS
[ ] FAIL - Issues:
_________________________________________________
```

---

## Test Suite 2: GEO Metadata Display

### Test 2.1: Dataset Details ⬜

**Objective**: Verify all GEO metadata displays correctly

**Steps**:
1. Search: **"diabetes microarray"**
2. Select first dataset (click to expand or view details)

**Expected Results**:
- ✅ Shows complete metadata:
  - **GEO ID**: GSExxxxx
  - **Title**: Full study title
  - **Summary**: GEO summary text (may be truncated)
  - **Organism**: e.g., "Homo sapiens"
  - **Platform**: e.g., "GPL570"
  - **Sample Count**: Number of samples
  - **PubMed IDs**: List of PMIDs (if available)
  - **Relevance Score**: 0.0-1.0
  - **Match Reasons**: Why this dataset matched

**Actual Results**:
```
[ ] PASS - All fields present and correct
[ ] FAIL - Missing fields:
_________________________________________________
```

---

### Test 2.2: PubMed Links ⬜

**Objective**: Verify PubMed links work (if clickable)

**Steps**:
1. Find a dataset with PubMed IDs
2. Click on a PubMed ID link (if UI provides this)

**Expected Results**:
- ✅ Opens PubMed page in new tab
- ✅ Shows correct paper

**Actual Results**:
```
[ ] PASS
[ ] FAIL - Issues:
_________________________________________________
[ ] N/A - No clickable links in UI
```

---

## Test Suite 3: Full-Text Enrichment

### Test 3.1: Download Papers for Single Dataset ⬜

**Objective**: Verify PDF download functionality works

**Steps**:
1. Search: **"GSE123456"** (use a real GSE ID you know has papers)
   - **Recommended test ID**: GSE306759 (has PMID 38287617)
2. Click "Download Papers" or "Enrich with Full-Text" button
3. Wait for download to complete (30-60 seconds)

**Expected Results**:
- ✅ Shows progress indicator (spinner, progress bar, or status message)
- ✅ Completes without errors
- ✅ Shows success message: "Downloaded X papers"
- ✅ Dataset now shows full-text status: "Full-text available (X papers)"
- ✅ Can see paper details:
  - PMID
  - Title
  - Paper type (original/citing)
  - Abstract preview

**Backend Verification** (check filesystem):
```bash
# Check PDFs were downloaded
ls -lah data/pdfs/GSE306759/
# Should show:
# - original/PMID_38287617.pdf
# - metadata.json

cat data/pdfs/GSE306759/metadata.json
# Should show paper metadata with type: "original"
```

**Actual Results**:
```
[ ] PASS - Papers downloaded successfully
[ ] FAIL - Issues:
_________________________________________________

Number of papers downloaded: ___
Paper types found: [ ] original [ ] citing
```

---

### Test 3.2: Citation Discovery ⬜

**Objective**: Verify citing papers are discovered and downloaded

**Steps**:
1. Search: **"GSE10000"** (well-cited dataset)
2. Click "Download Papers"
3. Wait for completion

**Expected Results**:
- ✅ Downloads original paper first
- ✅ Discovers citing papers (may take 30-60 seconds)
- ✅ Shows progress: "Found X citing papers"
- ✅ Downloads 1-5 citing papers (based on configuration)
- ✅ Papers are labeled:
  - "Original Paper" or paper_type: "original"
  - "Citing Paper 1, 2, 3..." or paper_type: "citing"

**Backend Verification**:
```bash
ls -lah data/pdfs/GSE10000/original/
ls -lah data/pdfs/GSE10000/citing/
# Should have PDFs in both directories
```

**Actual Results**:
```
[ ] PASS - Citation discovery working
[ ] FAIL - Issues:
_________________________________________________

Original papers: ___
Citing papers: ___
```

---

### Test 3.3: Batch Download ⬜

**Objective**: Verify downloading papers for multiple datasets

**Steps**:
1. Search: **"cancer biomarkers"**
2. Select 3 datasets (checkboxes or multi-select)
3. Click "Download Papers for Selected"

**Expected Results**:
- ✅ Shows batch progress: "Downloading papers for 3 datasets..."
- ✅ Downloads papers for each dataset sequentially or in parallel
- ✅ Updates status for each dataset as completed
- ✅ Final message: "Completed X/3 datasets"

**Actual Results**:
```
[ ] PASS - Batch download working
[ ] FAIL - Issues:
_________________________________________________

Successful: ___ / 3
Failed: ___ / 3
```

---

### Test 3.4: No Papers Available ⬜

**Objective**: Verify graceful handling when no papers found

**Steps**:
1. Find a dataset with no PubMed IDs (or search: **"unpublished dataset"**)
2. Try to download papers

**Expected Results**:
- ✅ Shows clear message: "No papers found for this dataset"
- ✅ Doesn't crash or show confusing error
- ✅ Suggests checking back later or viewing GEO directly

**Actual Results**:
```
[ ] PASS - Graceful handling
[ ] FAIL - Issues:
_________________________________________________
```

---

## Test Suite 4: PDF Parsing

### Test 4.1: View Parsed Content ⬜

**Objective**: Verify PDF parsing extracts sections correctly

**Steps**:
1. After downloading papers (Test 3.1), expand a paper to view details
2. Look for parsed sections:
   - Abstract
   - Introduction
   - Methods
   - Results
   - Discussion
   - Conclusion

**Expected Results**:
- ✅ Sections are extracted and displayed
- ✅ Text is readable (not garbled)
- ✅ Sections are labeled correctly
- ✅ Preview shows first 200-300 characters with "Read more..."

**Actual Results**:
```
[ ] PASS - Parsing working
[ ] FAIL - Issues:
_________________________________________________

Sections extracted: 
[ ] Abstract [ ] Methods [ ] Results [ ] Discussion
```

---

### Test 4.2: Parse Quality Check ⬜

**Objective**: Verify parsing quality is acceptable

**Steps**:
1. Read the "Methods" section preview
2. Check if text makes sense

**Expected Results**:
- ✅ Text is coherent and readable
- ✅ Formatting is mostly preserved
- ✅ No excessive garbage characters
- ✅ Sections are distinct (not all merged)

**Actual Results**:
```
[ ] PASS - Good quality parsing
[ ] PARTIAL - Some issues but acceptable
[ ] FAIL - Parsing broken:
_________________________________________________
```

---

## Test Suite 5: AI Analysis

### Test 5.1: Single Dataset Analysis ⬜

**Objective**: Verify GPT-4 AI analysis works

**Steps**:
1. After downloading papers (Test 3.1)
2. Click "Analyze with AI" button
3. Wait for analysis (10-30 seconds)

**Expected Results**:
- ✅ Shows loading indicator: "Analyzing..."
- ✅ Completes without errors
- ✅ Displays AI analysis with:
  - **Overview**: 2-3 sentence summary
  - **Key Findings**: 3-5 bullet points
  - **Recommendations**: 2-3 suggestions
  - **Confidence Score**: 0.0-1.0
- ✅ Analysis mentions:
  - GEO ID (e.g., "GSE306759")
  - PMIDs of papers used
  - Specific findings from the papers
- ✅ Analysis is coherent and relevant

**Backend Verification**:
```bash
# Check logs for GPT-4 API call
tail -f logs/omics_oracle.log | grep -i "gpt-4\|openai\|analysis"
```

**Actual Results**:
```
[ ] PASS - AI analysis working perfectly
[ ] PARTIAL - Working but quality issues
[ ] FAIL - Issues:
_________________________________________________

Analysis quality (1-5): ___
Mentions GEO ID: [ ] Yes [ ] No
Mentions PMIDs: [ ] Yes [ ] No
Relevant findings: [ ] Yes [ ] No
```

---

### Test 5.2: Batch Analysis ⬜

**Objective**: Verify AI analysis for multiple datasets

**Steps**:
1. Select 2-3 datasets with downloaded papers
2. Click "Analyze Selected with AI"
3. Wait for batch analysis (30-60 seconds)

**Expected Results**:
- ✅ Analyzes all selected datasets
- ✅ Shows progress: "Analyzing dataset 1/3..."
- ✅ Each dataset gets separate analysis
- ✅ No data leakage (each analysis talks about correct GEO ID)
- ✅ Can distinguish analyses by GEO ID

**Actual Results**:
```
[ ] PASS - Batch analysis working
[ ] FAIL - Issues:
_________________________________________________

Datasets analyzed: ___ / ___
Correct GEO IDs: [ ] Yes [ ] No
```

---

### Test 5.3: AI Without Full-Text ⬜

**Objective**: Verify AI skips gracefully without full-text

**Steps**:
1. Find a dataset WITHOUT downloaded papers
2. Click "Analyze with AI"

**Expected Results**:
- ✅ Shows message: "AI Analysis Not Available"
- ✅ Explains: "No full-text papers downloaded. Download papers first."
- ✅ Provides "Download Papers" button
- ✅ Doesn't crash or show confusing error

**Actual Results**:
```
[ ] PASS - Graceful skip
[ ] FAIL - Issues:
_________________________________________________
```

---

## Test Suite 6: Data Persistence & Registry

### Test 6.1: SQLite Registry Check ⬜

**Objective**: Verify data is saved to SQLite registry

**Steps**:
1. After completing Tests 3.1 and 5.1
2. Check SQLite database

**Backend Verification**:
```bash
# Connect to SQLite
sqlite3 data/geo_registry.db

# Check dataset exists
SELECT * FROM geo_datasets WHERE geo_id = 'GSE306759';
# Should return 1 row with metadata

# Check publications are linked
SELECT p.pmid, p.title, gp.paper_type 
FROM publications p
JOIN geo_publications gp ON p.id = gp.publication_id
WHERE gp.geo_id = 'GSE306759';
# Should show original + citing papers

# Check download history
SELECT * FROM download_history 
WHERE geo_id = 'GSE306759' 
ORDER BY downloaded_at DESC 
LIMIT 5;
# Should show download records

# Exit SQLite
.quit
```

**Expected Results**:
- ✅ Dataset row exists in `geo_datasets`
- ✅ Publications linked in `geo_publications`
- ✅ Download history tracked in `download_history`
- ✅ Foreign keys intact (no orphaned records)

**Actual Results**:
```
[ ] PASS - Registry working
[ ] FAIL - Issues:
_________________________________________________
```

---

### Test 6.2: Data Persistence After Restart ⬜

**Objective**: Verify data survives system restart

**Steps**:
1. After completing previous tests (with downloaded papers)
2. Stop the system:
   ```bash
   # Press Ctrl+C on the terminal running start_omics_oracle.sh
   ```
3. Restart the system:
   ```bash
   ./start_omics_oracle.sh
   ```
4. Search for the same dataset (e.g., GSE306759)

**Expected Results**:
- ✅ Dataset still shows "Full-text available"
- ✅ Papers are still accessible (not re-downloaded)
- ✅ AI analysis can still be run (uses cached papers)

**Actual Results**:
```
[ ] PASS - Data persists
[ ] FAIL - Issues:
_________________________________________________
```

---

## Test Suite 7: Error Handling

### Test 7.1: Network Error Handling ⬜

**Objective**: Verify graceful handling of network issues

**Steps**:
1. Disconnect from internet (or use network throttling)
2. Try to search for datasets
3. Try to download papers

**Expected Results**:
- ✅ Shows clear error: "Network error. Please check connection."
- ✅ Doesn't crash the application
- ✅ Allows retry after reconnecting

**Actual Results**:
```
[ ] PASS - Graceful error handling
[ ] FAIL - Issues:
_________________________________________________
[ ] SKIP - Can't test network disconnect
```

---

### Test 7.2: API Rate Limiting ⬜

**Objective**: Verify handling of API rate limits

**Steps**:
1. Make rapid searches (10+ searches in quick succession)
2. Try rapid paper downloads

**Expected Results**:
- ✅ Shows message if rate limited: "Please wait, rate limit reached"
- ✅ Automatically retries with backoff
- ✅ Or shows wait time: "Retry in 30 seconds"

**Actual Results**:
```
[ ] PASS - Rate limiting handled
[ ] FAIL - Issues:
_________________________________________________
[ ] SKIP - Didn't hit rate limit
```

---

### Test 7.3: Invalid GEO ID ⬜

**Objective**: Verify handling of invalid GEO IDs

**Steps**:
1. Search for invalid GEO ID: **"GSE999999999"** (doesn't exist)

**Expected Results**:
- ✅ Shows clear message: "Dataset not found in GEO"
- ✅ Suggests checking GEO ID spelling
- ✅ No crash or stack trace shown to user

**Actual Results**:
```
[ ] PASS - Graceful handling
[ ] FAIL - Issues:
_________________________________________________
```

---

## Test Suite 8: Performance

### Test 8.1: Search Response Time ⬜

**Objective**: Verify search is reasonably fast

**Steps**:
1. Search: **"cancer"**
2. Measure time to results

**Expected Results**:
- ✅ Results appear in < 10 seconds
- ✅ Ideally < 5 seconds

**Actual Results**:
```
Time to results: ___ seconds

[ ] PASS (< 10 sec)
[ ] SLOW (10-30 sec) - acceptable but could be faster
[ ] FAIL (> 30 sec) - too slow
```

---

### Test 8.2: Download Speed ⬜

**Objective**: Verify paper downloads are reasonably fast

**Steps**:
1. Download papers for 1 dataset (Test 3.1)
2. Measure total time

**Expected Results**:
- ✅ Single paper: < 30 seconds
- ✅ With citations (3-5 papers): < 2 minutes

**Actual Results**:
```
Time for 1 paper: ___ seconds
Time for 3-5 papers: ___ seconds

[ ] PASS - Acceptable speed
[ ] SLOW - Works but slow
[ ] FAIL - Too slow (> 5 minutes)
```

---

### Test 8.3: UI Responsiveness ⬜

**Objective**: Verify UI stays responsive during operations

**Steps**:
1. Start a paper download
2. Try to navigate to other datasets
3. Try to search for other terms

**Expected Results**:
- ✅ UI remains responsive (doesn't freeze)
- ✅ Can interact with other datasets while downloading
- ✅ Progress updates smoothly

**Actual Results**:
```
[ ] PASS - UI stays responsive
[ ] PARTIAL - Slight lag but usable
[ ] FAIL - UI freezes during operations
```

---

## Test Suite 9: Edge Cases

### Test 9.1: Very Long Query ⬜

**Objective**: Verify handling of extremely long search queries

**Steps**:
1. Enter a very long query (500+ characters)
2. Click "Search"

**Expected Results**:
- ✅ Query is truncated or processed
- ✅ Shows results or clear message
- ✅ No crash

**Actual Results**:
```
[ ] PASS
[ ] FAIL - Issues:
_________________________________________________
```

---

### Test 9.2: Empty Query ⬜

**Objective**: Verify handling of empty search

**Steps**:
1. Leave search box empty
2. Click "Search"

**Expected Results**:
- ✅ Shows validation message: "Please enter a search query"
- ✅ Or shows popular/recent searches
- ✅ Doesn't perform empty search

**Actual Results**:
```
[ ] PASS
[ ] FAIL - Issues:
_________________________________________________
```

---

### Test 9.3: Unicode Characters ⬜

**Objective**: Verify handling of special Unicode characters

**Steps**:
1. Search: **"α-synuclein β-catenin"** (Greek letters)
2. Search: **"café résumé"** (accented characters)

**Expected Results**:
- ✅ Handles Unicode gracefully
- ✅ Returns relevant results
- ✅ No encoding errors

**Actual Results**:
```
[ ] PASS
[ ] FAIL - Issues:
_________________________________________________
```

---

## Test Suite 10: User Experience

### Test 10.1: First-Time User Experience ⬜

**Objective**: Evaluate if a new user can use the system

**Steps**:
1. Pretend you've never used the system
2. Try to accomplish basic task: "Find cancer datasets and analyze them"

**Expected Results**:
- ✅ UI is intuitive (minimal learning curve)
- ✅ Buttons are clearly labeled
- ✅ Help text or tooltips available
- ✅ Error messages are helpful
- ✅ Can complete task without documentation

**Actual Results**:
```
[ ] PASS - Very intuitive
[ ] GOOD - Mostly intuitive with minor confusion
[ ] FAIR - Requires some learning
[ ] FAIL - Confusing UI

Notes:
_________________________________________________
_________________________________________________
```

---

### Test 10.2: Loading Indicators ⬜

**Objective**: Verify user gets feedback during long operations

**Steps**:
1. Note all loading states during:
   - Search
   - Download
   - AI Analysis

**Expected Results**:
- ✅ Clear loading indicators (spinners, progress bars)
- ✅ Status messages: "Searching...", "Downloading 2/5 papers..."
- ✅ User knows system is working (not frozen)

**Actual Results**:
```
[ ] PASS - Excellent feedback
[ ] GOOD - Basic feedback present
[ ] FAIL - No/poor feedback

Missing indicators for:
_________________________________________________
```

---

### Test 10.3: Mobile Responsiveness ⬜ (Optional)

**Objective**: Check if UI works on mobile devices

**Steps**:
1. Open frontend on mobile device or resize browser window
2. Try basic operations

**Expected Results**:
- ✅ Layout adapts to small screens
- ✅ Buttons are tappable (not too small)
- ✅ Core functionality works

**Actual Results**:
```
[ ] PASS - Mobile friendly
[ ] PARTIAL - Works but not optimized
[ ] FAIL - Broken on mobile
[ ] SKIP - Desktop only (acceptable for now)
```

---

## Summary & Results

### Overall Test Results

**Total Tests**: 31  
**Passed**: ___  
**Failed**: ___  
**Skipped**: ___  
**Pass Rate**: ____%

### Critical Issues (Must Fix)

**Priority 1 (Blocking)**:
1. _________________________________________________
2. _________________________________________________
3. _________________________________________________

**Priority 2 (Important)**:
1. _________________________________________________
2. _________________________________________________

**Priority 3 (Nice to Have)**:
1. _________________________________________________
2. _________________________________________________

### Positive Findings

**What Worked Great**:
1. _________________________________________________
2. _________________________________________________
3. _________________________________________________

### Recommendations

**Immediate Actions**:
1. _________________________________________________
2. _________________________________________________

**Future Improvements**:
1. _________________________________________________
2. _________________________________________________

---

## Next Steps

### After Testing

1. **Document Results**: Fill out this checklist completely
2. **Prioritize Issues**: Mark issues as P1/P2/P3
3. **Create Bug Reports**: For each critical issue
4. **Discuss Fixes**: Share results for collaborative fixing
5. **Retest**: After fixes, retest failed scenarios

### Files to Attach (if possible)

- [ ] Completed checklist
- [ ] Screenshots of issues
- [ ] Log excerpts showing errors
- [ ] Database dumps (if data corruption found)

---

## Testing Tips

### Before You Start
- ✅ Clear browser cache
- ✅ Use incognito/private window
- ✅ Have terminal open to view logs
- ✅ Take screenshots of issues
- ✅ Note exact error messages

### During Testing
- ✅ Test one thing at a time
- ✅ Don't skip failed tests (document and continue)
- ✅ Note any unexpected behavior
- ✅ Check browser console for JavaScript errors (F12)
- ✅ Monitor system logs in real-time

### After Testing
- ✅ Don't panic if issues found (that's the point!)
- ✅ Every bug found now = bug prevented in production
- ✅ Detailed notes make fixing much faster

---

## Questions or Issues During Testing?

If you encounter anything unclear:
1. Note it in the checklist
2. Take a screenshot
3. Check logs for error details
4. We'll review together and fix!

---

**Happy Testing! 🚀**

Remember: The goal is to **find issues**, not to prove everything works.  
Every bug you find now is one less bug users will see!
