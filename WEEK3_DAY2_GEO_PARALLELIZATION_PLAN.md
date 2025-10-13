# Week 3 Day 2: GEO Parallelization Implementation Plan

## Current State Analysis

### Existing Implementation
**Location:** `omics_oracle_v2/lib/search_engines/geo/client.py`

**Current Features:**
- ✅ `batch_get_metadata()` with semaphore-based concurrency
- ✅ Timeout handling (30s per dataset) - ALREADY DONE!
- ✅ Error handling and retry logic
- ✅ Performance metrics logging
- ✅ Rate limiting compliance

**Current Settings:**
- Max concurrent: 10 (default)
- Timeout: 30s per dataset
- Uses asyncio.Semaphore for concurrency control
- Uses asyncio.gather for parallel execution

## Performance Optimization Goals

### Target Metrics
- **Current:** 0.5-1 datasets/sec (estimated, needs profiling)
- **Target:** 2-5 datasets/sec (5-10x improvement)
- **Stretch:** 5-10 datasets/sec with optimal conditions

## Optimization Strategy

### Phase 1: Increase Concurrency (HIGH IMPACT) ⚡
**Current:** max_concurrent=10
**Proposed:** max_concurrent=20

**Rationale:**
- NCBI Entrez allows up to 10 requests/sec with API key
- GEO metadata fetches are I/O bound (network wait time)
- Increasing concurrency reduces total wait time
- Semaphore prevents overwhelming the server

**Expected Impact:** 1.5-2x throughput improvement

### Phase 2: Connection Pooling Optimization (MEDIUM IMPACT) 🔧
**Current:** Single aiohttp session
**Proposed:** Optimize connector settings

**Changes:**
```python
connector = aiohttp.TCPConnector(
    ssl=ssl_context,
    limit=50,              # Total connection limit (up from default 100)
    limit_per_host=20,     # Per-host limit (up from default 0/unlimited)
    ttl_dns_cache=300,     # DNS cache TTL (5 minutes)
    force_close=False,     # Reuse connections
    enable_cleanup_closed=True
)
```

**Expected Impact:** 20-30% throughput improvement

### Phase 3: Adaptive Timeout Handling (LOW IMPACT) ⏱️
**Current:** Fixed 30s timeout
**Proposed:** Adaptive timeout based on response patterns

**Strategy:**
- Fast datasets (< 5s): 10s timeout
- Normal datasets (5-15s): 20s timeout
- Slow datasets (> 15s): 30s timeout
- Track average response time per dataset

**Expected Impact:** 10-15% throughput improvement (reduces wasted time)

### Phase 4: Smart Retry Logic (LOW IMPACT) ♻️
**Current:** Basic error handling
**Proposed:** Exponential backoff with jitter

**Strategy:**
- First failure: Retry immediately
- Second failure: Retry after 1s + random(0-0.5s)
- Third failure: Retry after 2s + random(0-1s)
- Max retries: 3

**Expected Impact:** 5-10% success rate improvement

## Implementation Priority

### High Priority (Implement Today)
1. ✅ **Increase max_concurrent to 20** - Quick win, big impact
2. ✅ **Optimize connection pooling** - Simple config change
3. ✅ **Add concurrency tuning parameter** - Make it configurable

### Medium Priority (Optional)
4. **Adaptive timeout** - More complex, smaller impact
5. **Smart retry logic** - Good for reliability

### Low Priority (Future)
6. **Response caching at HTTP level** - ETags, conditional requests
7. **Batch ID optimization** - Group similar IDs for better caching

## Implementation Details

### Change 1: Increase Default Concurrency

**File:** `omics_oracle_v2/lib/search_engines/geo/client.py`

```python
async def batch_get_metadata(
    self,
    geo_ids: List[str],
    max_concurrent: int = 20,  # CHANGED from 10 to 20
    return_list: bool = False
) -> Union[Dict[str, GEOSeriesMetadata], List[GEOSeriesMetadata]]:
```

**File:** `omics_oracle_v2/lib/search_engines/geo/client.py`

```python
async def batch_get_metadata_smart(
    self,
    geo_ids: List[str],
    max_concurrent: int = 20  # CHANGED from 10 to 20
) -> List[GEOSeriesMetadata]:
```

**Rationale:** Double concurrency for 1.5-2x throughput

### Change 2: Optimize TCP Connector

**File:** `omics_oracle_v2/lib/search_engines/geo/client.py`

```python
async def _get_session(self) -> aiohttp.ClientSession:
    """Get or create optimized aiohttp session."""
    if self.session is None:
        # Create SSL context if verification is disabled
        ssl_context = None
        if not self.verify_ssl:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            logger.warning("SSL verification disabled - use only for testing")

        # Week 3 Day 2: Optimized connector for parallel fetching
        connector = aiohttp.TCPConnector(
            ssl=ssl_context,
            limit=50,                    # Total connection pool size
            limit_per_host=20,          # Connections per host (matches max_concurrent)
            ttl_dns_cache=300,          # Cache DNS for 5 minutes
            force_close=False,          # Reuse connections
            enable_cleanup_closed=True  # Clean up closed connections
        )

        # Week 3 Day 2: Add timeout configuration
        timeout = aiohttp.ClientTimeout(
            total=60,      # Total timeout per request
            connect=10,    # Connection timeout
            sock_read=30   # Socket read timeout
        )

        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout
        )

    return self.session
```

**Rationale:** Optimized connection pooling reduces overhead

### Change 3: Make Concurrency Configurable in Settings

**File:** `omics_oracle_v2/core/config.py`

```python
class GEOSettings(BaseSettings):
    \"\"\"GEO API configuration.\"\"\"

    # ... existing fields ...

    # Week 3 Day 2: Concurrency tuning
    max_concurrent_fetches: int = Field(
        default=20,
        description="Maximum concurrent GEO metadata fetches (10-50 recommended)",
        ge=1,
        le=100
    )
```

**Rationale:** Allow tuning per environment (development vs production)

### Change 4: Update Search Orchestrator

**File:** `omics_oracle_v2/lib/search_orchestration/orchestrator.py`

Update to use higher concurrency from config:

```python
# In _search_geo method, when calling batch operations:
max_concurrent = self.config.geo.max_concurrent_fetches if self.config.geo else 20
```

## Testing Plan

### Test 1: Baseline Performance
```python
# Measure current throughput
geo_ids = ['GSE1', 'GSE2', ... 'GSE50']  # 50 IDs
start = time.time()
results = await client.batch_get_metadata(geo_ids, max_concurrent=10)
baseline_time = time.time() - start
baseline_throughput = len(results) / baseline_time
```

### Test 2: Optimized Performance
```python
# Measure with optimizations
results = await client.batch_get_metadata(geo_ids, max_concurrent=20)
optimized_time = time.time() - start
optimized_throughput = len(results) / optimized_time
speedup = baseline_time / optimized_time
```

### Test 3: Success Rate
```python
# Verify reliability didn't decrease
success_rate = len(results) / len(geo_ids) * 100
assert success_rate >= 90, "Success rate should be 90%+"
```

### Test 4: Load Testing
```python
# Test with varying loads
for batch_size in [10, 20, 50, 100]:
    for concurrency in [10, 15, 20, 25]:
        # Measure throughput
        # Find optimal concurrency
```

## Expected Results

### Before Optimization
```
Batch size: 50 datasets
Max concurrent: 10
Time: ~30-40s
Throughput: 1.25-1.67 datasets/sec
Success rate: 95%
```

### After Optimization
```
Batch size: 50 datasets
Max concurrent: 20
Time: ~15-20s (2x faster)
Throughput: 2.5-3.3 datasets/sec
Success rate: 95%+ (maintained)
```

### Stretch Goal
```
Batch size: 50 datasets
Max concurrent: 25 + optimized connector
Time: ~10-12s (3-4x faster)
Throughput: 4-5 datasets/sec
Success rate: 90%+
```

## Monitoring & Validation

### Key Metrics to Track
1. **Throughput** (datasets/sec)
2. **Success rate** (%)
3. **Average response time** (seconds)
4. **Error rate** (%)
5. **Connection pool utilization**

### Logging Enhancements
```python
logger.info(
    f"GEO Fetch Performance: "
    f"{len(results)}/{len(geo_ids)} successful "
    f"in {elapsed:.2f}s "
    f"({throughput:.2f} datasets/sec, "
    f"max_concurrent={max_concurrent})"
)
```

## Rollback Plan

If performance degrades:
1. Revert max_concurrent to 10
2. Revert connector optimizations
3. Monitor error logs for issues
4. Gradual increase: 10 → 15 → 20

## Success Criteria

- ✅ Throughput: 2-5 datasets/sec (5-10x improvement from 0.5)
- ✅ Success rate: ≥90%
- ✅ No increase in errors or timeouts
- ✅ Connection pool stable
- ✅ Backward compatible (old code still works)

## Files to Modify

1. `omics_oracle_v2/lib/search_engines/geo/client.py`
   - Increase max_concurrent default: 10 → 20
   - Optimize _get_session() connector
   - Add better logging

2. `omics_oracle_v2/core/config.py`
   - Add max_concurrent_fetches to GEOSettings

3. `omics_oracle_v2/lib/search_orchestration/orchestrator.py`
   - Use config value for concurrency

4. `tests/week3/test_geo_parallelization.py` (new)
   - Benchmark tests
   - Load tests
   - Validation tests

## Implementation Time

- **Phase 1:** 30 minutes (concurrency increase)
- **Phase 2:** 30 minutes (connector optimization)
- **Phase 3:** 30 minutes (config integration)
- **Testing:** 1 hour (benchmark + validation)
- **Total:** ~2.5 hours

## Risk Assessment

**Low Risk Changes:**
- Increasing max_concurrent (easily reverted)
- Connector optimization (standard aiohttp settings)
- Config addition (backward compatible)

**Potential Issues:**
- Rate limiting by NCBI (mitigated by existing rate limiter)
- Memory usage increase (20 vs 10 concurrent, minimal impact)
- Connection pool exhaustion (mitigated by limits)

## Next Steps After Implementation

1. Run baseline benchmark
2. Apply optimizations
3. Run optimized benchmark
4. Compare results
5. Document findings
6. Update Week 3 summary

---

**Status:** Ready to implement
**Priority:** High (Day 2 of Week 3)
**Est. Time:** 2-3 hours
**Expected ROI:** 2-5x throughput improvement
