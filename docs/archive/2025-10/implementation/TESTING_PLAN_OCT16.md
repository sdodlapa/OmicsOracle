# Testing Plan - Citation Discovery Fix - Oct 16, 2025

## Status: Ready for Testing ✅

Server is running at: http://localhost:8000/dashboard

## What We Fixed

1. ✅ **Missing `await` in auto-discovery** - Citations now discover automatically
2. ✅ **Missing `await` in manual discovery button** - Manual discovery now works
3. ✅ **Wrong URL path in dashboard** - Requests now reach correct endpoint
4. ✅ **Smart cache re-enrichment** - Incomplete data auto-re-enriches with exponential backoff
5. ✅ **Enrichment metadata tracking** - Retry count and timestamps tracked

## Test Scenarios

### Scenario 1: New Dataset (Fresh Search) ✅

**Expected Behavior**: Auto-discovery runs, citations populated automatically

**Steps**:
1. Open dashboard: http://localhost:8000/dashboard
2. Search for: `CRISPR gene editing` (likely new datasets)
3. Wait for results

**Expected Results**:
```
✅ Datasets appear with citations
✅ Button shows: "📥 Download Papers (X in DB)" (not "🔍 Discover Citations")
✅ Logs show: "[AUTO-DISCOVERY] ✅ Complete for GSE... - X citations"
```

**Check Logs**:
```bash
tail -f logs/omics_api.log | grep "AUTO-DISCOVERY"
```

### Scenario 2: Existing Dataset with 0 Citations (Re-enrichment) ✅

**Expected Behavior**: Smart re-enrichment triggers on first search

**Steps**:
1. Search for: `breast cancer RNA-seq` (GSE307750, GSE306759)
2. Wait for results

**Expected Results**:
```
✅ First search: Re-enrichment triggered (retry_count=0)
✅ Logs show: "Retrying enrichment for GSE... (attempt 1/3)"
✅ After enrichment: Button shows "📥 Download Papers (X in DB)"
✅ Second search (immediate): No re-enrichment (in backoff or has citations)
```

**Check Logs**:
```bash
grep "Retrying enrichment\|Re-enrichment failed\|Successfully re-enriched" logs/omics_api.log
```

### Scenario 3: Manual Discovery Button (Fallback) ✅

**Expected Behavior**: Manual button works if auto-discovery failed

**Steps**:
1. Search for any dataset with "🔍 Discover Citations" button
2. Click the button
3. Wait for discovery to complete

**Expected Results**:
```
✅ Button changes to: "⏳ Discovering..."
✅ After completion: "📥 Download Papers (X in DB)"
✅ Success popup: "Found X citations"
✅ Logs show: "Starting citation discovery for GSE..."
```

**Check Logs**:
```bash
grep "Starting citation discovery\|Discovery complete" logs/omics_api.log
```

### Scenario 4: Exponential Backoff (Failed Enrichment) ⚠️

**Expected Behavior**: Failed enrichments respect backoff schedule

**Trigger Failure** (for testing):
- Turn off internet connection temporarily
- Search for new dataset
- Enrichment will fail

**Expected Results**:
```
✅ First failure: Retry after 5 minutes (backoff_minutes=5)
✅ Second failure: Retry after 30 minutes (backoff_minutes=30)
✅ Third failure: Retry after 2 hours (backoff_minutes=120)
✅ Fourth+ failure: Max retries reached, returns incomplete data
✅ Logs show backoff schedule clearly
```

**Check Logs**:
```bash
grep "in backoff period\|Max enrichment retries" logs/omics_api.log
```

### Scenario 5: Cache Hit Rate (Performance) 📊

**Expected Behavior**: Repeated searches hit cache

**Steps**:
1. Search for: `breast cancer RNA-seq`
2. Note the results
3. Search again (same query)
4. Compare response times

**Expected Results**:
```
✅ First search: ~5-8 seconds (cache miss + enrichment)
✅ Second search: <1 second (cache hit)
✅ Results identical
✅ Logs show: "Cache HIT"
```

**Check Stats**:
```python
# In Python console or debug endpoint
cache_stats = geo_cache.stats
hit_rate = cache_stats["cache_hits"] / (cache_stats["cache_hits"] + cache_stats["cache_misses"])
print(f"Cache hit rate: {hit_rate * 100:.1f}%")
```

## Regression Testing

### Must NOT Break These Features:

- [ ] Basic search still works
- [ ] Search results display correctly
- [ ] Semantic expansion works (SapBERT)
- [ ] Entity extraction works (BERN2)
- [ ] Download Papers button works (for datasets with citations)
- [ ] AI Analysis button works (for datasets with PDFs)
- [ ] PDF download flow works
- [ ] Full-text extraction works

## Error Cases to Test

### Case 1: Invalid GEO ID
**Input**: Search returns invalid GSE ID (shouldn't happen, but test anyway)
**Expected**: Graceful error, no crash

### Case 2: PubMed API Down
**Simulate**: Block api.ncbi.nlm.nih.gov in /etc/hosts
**Expected**: 
- Enrichment fails gracefully
- Logs show error
- Retry scheduled with backoff
- No infinite loops

### Case 3: Database Locked
**Simulate**: Open database file in another process
**Expected**:
- Graceful error
- Fallback to memory cache
- No data loss

### Case 4: Concurrent Enrichments
**Test**: Search for 20+ new datasets simultaneously
**Expected**:
- No race conditions
- All enrichments complete
- No duplicate entries
- Proper concurrency handling

## Performance Benchmarks

### Target Metrics:

| Metric | Target | Critical |
|--------|--------|----------|
| First search (new dataset) | <10s | <15s |
| Cache hit (complete data) | <1s | <2s |
| Re-enrichment trigger | <12s | <20s |
| Manual discovery | <15s | <30s |
| Cache hit rate (after 10 searches) | >60% | >40% |
| Enrichment success rate | >90% | >70% |

### Load Testing:

```bash
# Install Apache Bench if needed
brew install httpd

# Test search endpoint
ab -n 100 -c 10 http://localhost:8000/api/agents/search

# Expected:
# - 99% of requests < 10s
# - 0% failures
# - No memory leaks
```

## Monitoring During Testing

### Terminal 1: API Logs (Real-time)
```bash
tail -f logs/omics_api.log | grep -E "AUTO-DISCOVERY|Retrying enrichment|ERROR|WARNING"
```

### Terminal 2: Error Tracking
```bash
tail -f logs/omics_api.log | grep "ERROR\|CRITICAL\|Traceback"
```

### Terminal 3: Performance Metrics
```bash
tail -f logs/omics_api.log | grep "TIME\|execution time"
```

## Success Criteria

### Critical (Must Pass):
- [x] Server starts without errors ✅
- [ ] Auto-discovery works for new datasets
- [ ] Re-enrichment works for incomplete data
- [ ] Manual discovery button works
- [ ] No infinite retry loops
- [ ] Exponential backoff functions correctly
- [ ] No regression in existing features

### Important (Should Pass):
- [ ] Cache hit rate >60%
- [ ] First search <10s
- [ ] Cache hits <1s
- [ ] Enrichment success rate >90%
- [ ] Proper error logging

### Nice to Have:
- [ ] Admin UI for retry management (Phase 2)
- [ ] Real-time enrichment status (Phase 2)
- [ ] Metrics dashboard (Phase 2)

## Known Issues / Limitations

1. **No Admin UI Yet**: Can't manually reset retry count (Phase 2)
2. **No Real-time Status**: Can't see enrichment progress in UI (Phase 2)
3. **No Metrics Dashboard**: Must check logs for stats (Phase 2)
4. **Fixed Backoff Schedule**: Not configurable yet (could make configurable)

## Rollback Triggers

Stop testing and rollback if:
- ❌ Server crashes repeatedly
- ❌ Infinite retry loops detected
- ❌ Data corruption observed
- ❌ >50% enrichment failure rate
- ❌ Cache hit rate <20%
- ❌ Major regression in existing features

## Test Data

### Recommended Test Queries:

1. **New Datasets** (likely not in cache):
   - `CRISPR gene editing 2025`
   - `COVID-19 vaccine response`
   - `single cell sequencing neurodegeneration`

2. **Existing Datasets** (may have 0 citations):
   - `breast cancer RNA-seq` (GSE307750, GSE306759)
   - `alzheimer's disease microarray`

3. **Popular Datasets** (likely complete):
   - `BRCA1 mutations`
   - `immune response to infection`

## Next Steps After Testing

### If All Tests Pass ✅:
1. Document test results in this file
2. Update CHANGELOG.md
3. Commit changes to git
4. Deploy to production
5. Monitor for 24 hours

### If Tests Fail ❌:
1. Document failure details
2. Check logs for root cause
3. Fix issues
4. Re-test
5. If unfixable, rollback:
   ```bash
   git checkout HEAD~1 -- omics_oracle_v2/lib/pipelines/storage/registry/geo_cache.py
   ```

## Test Results Log

### Test Run #1 - Oct 16, 2025 (Pending)

**Tester**: [Your name]
**Environment**: macOS, localhost:8000
**Duration**: [TBD]

#### Scenario 1: New Dataset
- [ ] Tested
- [ ] Result: 
- [ ] Issues found:

#### Scenario 2: Re-enrichment
- [ ] Tested
- [ ] Result:
- [ ] Issues found:

#### Scenario 3: Manual Discovery
- [ ] Tested
- [ ] Result:
- [ ] Issues found:

#### Scenario 4: Backoff
- [ ] Tested
- [ ] Result:
- [ ] Issues found:

#### Scenario 5: Cache Performance
- [ ] Tested
- [ ] Result:
- [ ] Issues found:

### Overall Result: [PASS/FAIL/PARTIAL]

**Notes**:
[Add detailed notes here]

**Recommendations**:
[Add recommendations here]

---

**Ready to Test**: YES ✅
**Server Status**: Running on http://localhost:8000/dashboard
**Next Action**: Run Scenario 1 (New Dataset Search)
