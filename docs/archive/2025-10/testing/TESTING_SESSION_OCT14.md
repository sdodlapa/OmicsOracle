# Frontend Testing Session - October 14, 2025

**Start Time**: _________  
**Tester**: Sanjeeva Dodlapati  
**Session Type**: Manual Frontend Validation  
**Server Status**: ✅ Running (PID: 13933)

---

## Pre-Testing Checklist

- [x] ✅ Server started successfully
- [x] ✅ Import error fixed (GEOSeriesMetadata)
- [x] ✅ Dashboard accessible: http://localhost:8000/dashboard
- [x] ✅ API running: http://localhost:8000
- [ ] 🔄 Dashboard loaded in browser (about to check)

---

## System Information

**URLs**:
- Dashboard: http://localhost:8000/dashboard
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

**Logs**:
```bash
tail -f logs/omics_api.log
```

**Database**:
```bash
sqlite3 data/geo_registry.db
```

---

## Testing Plan (Prioritized)

### 🔥 Phase 1: Critical Tests (1 hour)

**These tests validate core functionality - do these first!**

1. **Test 1.1**: Simple Search Query
   - Query: "breast cancer biomarkers"
   - Expected: 5-20 datasets returned
   - Status: [ ] Not Started [ ] In Progress [ ] PASS [ ] FAIL

2. **Test 3.1**: Download Papers (CRITICAL)
   - GEO ID: GSE306759 (has PMID 38287617)
   - Expected: PDF downloaded to data/pdfs/GSE306759/
   - Status: [ ] Not Started [ ] In Progress [ ] PASS [ ] FAIL

3. **Test 3.2**: Citation Discovery (CRITICAL)
   - Expected: Original + citing papers
   - Status: [ ] Not Started [ ] In Progress [ ] PASS [ ] FAIL

4. **Test 4.1**: View Parsed Content
   - Expected: Sections extracted (abstract, methods, results)
   - Status: [ ] Not Started [ ] In Progress [ ] PASS [ ] FAIL

5. **Test 5.1**: AI Analysis (CRITICAL)
   - Expected: GPT-4 insights with PMIDs
   - Status: [ ] Not Started [ ] In Progress [ ] PASS [ ] FAIL

6. **Test 6.1**: SQLite Registry Check
   - Expected: Data persists in database
   - Status: [ ] Not Started [ ] In Progress [ ] PASS [ ] FAIL

---

### ⭐ Phase 2: Important Tests (1 hour)

7. **Test 2.1**: Dataset Details Display
8. **Test 3.3**: Batch Download
9. **Test 5.2**: Batch AI Analysis
10. **Test 7.1**: Error Handling
11. **Test 8.1**: Performance Check

---

### 💡 Phase 3: Nice-to-Have Tests (30 min)

12-31. Remaining tests from checklist

---

## Quick Commands Reference

### Check What's Running
```bash
# Health check
curl http://localhost:8000/health

# View recent logs
tail -n 50 logs/omics_api.log

# Check if PDFs downloaded
ls -lah data/pdfs/
```

### Backend Verification Commands

**After Test 3.1 (Download Papers)**:
```bash
# Check PDFs
ls -lah data/pdfs/GSE306759/
cat data/pdfs/GSE306759/metadata.json

# Check database
sqlite3 data/geo_registry.db "SELECT * FROM geo_datasets WHERE geo_id = 'GSE306759';"
```

**Check Database Contents**:
```bash
sqlite3 data/geo_registry.db << EOF
.mode column
.headers on
SELECT geo_id, title, organism, sample_count FROM geo_datasets LIMIT 5;
.quit
EOF
```

---

## Test Results Summary

### Tests Completed: 0 / 31

**PASS**: ___  
**FAIL**: ___  
**SKIP**: ___

---

## Issues Found

### Critical (P1) - Must Fix
_None yet_

### Important (P2) - Should Fix
_None yet_

### Minor (P3) - Nice to Fix
_None yet_

---

## Notes & Observations

### What Worked Great
- Server starts successfully after import fix
- 

### What Needs Improvement
- 

### Questions / Clarifications Needed
- 

---

## Next Steps After Testing

1. [ ] Review results together
2. [ ] Prioritize bug fixes (P1/P2/P3)
3. [ ] Fix critical issues
4. [ ] Retest failed scenarios
5. [ ] Create automated tests (Week 2)

---

## Session Timeline

**Planned Duration**: 2-3 hours  
**Actual Duration**: ___________

| Time | Activity | Status |
|------|----------|--------|
| ___ | Pre-testing setup | ✅ Complete |
| ___ | Test 1.1: Simple Search | [ ] |
| ___ | Test 3.1: Download Papers | [ ] |
| ___ | Test 3.2: Citation Discovery | [ ] |
| ___ | Test 4.1: Parsed Content | [ ] |
| ___ | Test 5.1: AI Analysis | [ ] |
| ___ | Test 6.1: Database Check | [ ] |
| ___ | Additional tests | [ ] |
| ___ | Documentation & wrap-up | [ ] |

---

**End of Session Notes**:
_To be filled after testing..._
