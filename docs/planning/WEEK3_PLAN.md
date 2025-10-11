# Week 3 Implementation Plan

**Date:** October 11, 2025
**Status:** Planning phase
**Context:** Week 2 Days 4-5 complete, ready for Week 3 features

---

## Week 2 Completion Summary

### Week 2 Day 4: SearchAgent Migration ✅
- Migrated to unified pipeline architecture
- Fixed 10 bugs from comprehensive log analysis
- Smart citation scoring (3-tier dampening)
- Recency bonus for recent papers
- All tests passing (100%)

### Week 2 Day 5: Performance Improvements ✅
- Phase logging clarity (Phase 1 vs Phase 2)
- Cache metrics tracking and visibility
- **Critical cache bug fixed** (was 100% miss rate)
- Session cleanup analyzed (deferred to Week 3)

### Performance Baseline (After Fixes)
- Cache speedup: 1.3x → Expected 10-100x after bug fix
- GEO parallelization: 0.4-0.5 datasets/sec (target: 2-5/sec)
- Test runtime: ~15-16 minutes for full validation
- Memory: Stable, but 5 unclosed sessions per run

---

## Week 3 Goals

### Theme: **Performance & Production Readiness**

**Primary Objectives:**
1. Optimize cache performance (partial cache lookups)
2. Fix GEO parallelization bottleneck
3. Add session cleanup to all async components
4. Production configuration and monitoring
5. Load testing and performance validation

**Success Criteria:**
- Cache speedup: 10-50x on repeated queries
- GEO fetch: 2-5 datasets/sec (5-10x faster)
- 0 unclosed session warnings
- Production deployment ready
- Load test: 10 concurrent users, <5s response time

---

## Week 3 Day 1: Cache Optimization (8 hours)

### Goal: Improve cache from 1.3x to 10-50x speedup

**Current Limitation:**
- Cache checks entire query result as single unit
- If ANY item missing, fetches ALL items fresh
- Example: 100 datasets, 95 cached, 5 new → Re-fetches all 100

**Solution: Partial Cache Lookups**
```python
async def search_with_partial_cache(geo_ids: List[str]) -> List[GEOSeriesMetadata]:
    """
    Smart cache lookup - uses cached items, fetches only uncached.

    Example:
        geo_ids = [GSE001, GSE002, GSE003, GSE004, GSE005]
        cached = [GSE001, GSE003, GSE005]  # 60% hit rate
        uncached = [GSE002, GSE004]        # Only fetch these 2
        result = cached + fetch(uncached)  # Merge results
    """
    cached_items = []
    uncached_ids = []

    # Step 1: Check cache for each ID individually
    for geo_id in geo_ids:
        cache_key = f"geo:metadata:{geo_id}"
        cached = await self.cache.get(cache_key)

        if cached:
            cached_items.append(GEOSeriesMetadata(**cached))
        else:
            uncached_ids.append(geo_id)

    logger.info(f"Cache: {len(cached_items)} hits, {len(uncached_ids)} misses "
                f"({len(cached_items)/len(geo_ids)*100:.1f}% hit rate)")

    # Step 2: Fetch only uncached items
    fresh_items = []
    if uncached_ids:
        fresh_items = await self.fetch_metadata_batch(uncached_ids)

        # Cache new items for next time
        for item in fresh_items:
            cache_key = f"geo:metadata:{item.geo_id}"
            await self.cache.set(cache_key, item.dict(), ttl=2592000)  # 30 days

    # Step 3: Merge and return
    return cached_items + fresh_items
```

**Implementation Tasks:**
1. [ ] Update `GEOClient.fetch_metadata_batch()` to use partial cache
2. [ ] Update `PublicationSearchPipeline.search()` for per-publication caching
3. [ ] Add cache key versioning for schema changes
4. [ ] Add cache warming script for common queries
5. [ ] Test with various hit rate scenarios (0%, 50%, 95%, 100%)

**Expected Results:**
- First run: 0% hit rate, same speed as before
- Second run: 95% hit rate, **50x faster** (only 5% re-fetched)
- Third run: 100% hit rate, **100x faster** (instant)

**Testing:**
```bash
# Test 1: Cold cache
redis-cli FLUSHDB
python tests/week2/test_cache_performance.py  # ~200s

# Test 2: Warm cache (should be ~4s)
python tests/week2/test_cache_performance.py

# Measure speedup
echo "Speedup: 200s / 4s = 50x"
```

**Time estimate:** 6 hours implementation + 2 hours testing

---

## Week 3 Day 2: GEO Parallelization Fix (6 hours)

### Goal: Increase GEO fetch from 0.5 to 2-5 datasets/sec

**Current Performance:**
```log
Batch fetch complete: 5/5 successful in 10.83s (0.5 datasets/sec)
```

**Expected Performance:**
```log
Batch fetch complete: 5/5 successful in 1.5s (3.3 datasets/sec)
```

**Investigation Checklist:**
1. [ ] Verify `fetch_metadata_batch()` uses `asyncio.gather()`
2. [ ] Check `max_concurrent` parameter (should be 10-20)
3. [ ] Profile individual dataset fetch time
4. [ ] Identify bottleneck: network, parsing, or disk I/O
5. [ ] Test with different concurrency levels (5, 10, 20, 50)

**Likely Issues:**
```python
# WRONG - Sequential (current?)
for geo_id in geo_ids:
    result = await self.fetch_metadata(geo_id)  # Waits for each
    results.append(result)

# RIGHT - Parallel
tasks = [self.fetch_metadata(geo_id) for geo_id in geo_ids]
results = await asyncio.gather(*tasks, return_exceptions=True)
```

**Optimization Opportunities:**
1. **Increase max_concurrent**: 5 → 20 (4x parallel)
2. **Stream parsing**: Don't wait for full download before parsing
3. **Connection pooling**: Reuse FTP connections
4. **Timeout handling**: Skip slow datasets (30s timeout)

**Implementation:**
```python
async def fetch_metadata_batch(
    self,
    geo_ids: List[str],
    max_concurrent: int = 20,  # Increased from 10
    timeout: int = 30,          # Add timeout
) -> List[GEOSeriesMetadata]:
    """Fetch multiple dataset metadata in parallel."""

    semaphore = asyncio.Semaphore(max_concurrent)

    async def fetch_with_limit(geo_id: str):
        async with semaphore:
            try:
                return await asyncio.wait_for(
                    self.fetch_metadata(geo_id),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                logger.warning(f"Timeout fetching {geo_id} (>{timeout}s)")
                return None
            except Exception as e:
                logger.error(f"Error fetching {geo_id}: {e}")
                return None

    tasks = [fetch_with_limit(geo_id) for geo_id in geo_ids]
    results = await asyncio.gather(*tasks)

    # Filter out None results
    return [r for r in results if r is not None]
```

**Testing:**
```bash
# Benchmark current vs optimized
python -m pytest tests/performance/test_geo_parallelization.py -v

# Expected:
# - 5 datasets: 10s → 2s (5x faster)
# - 20 datasets: 40s → 5s (8x faster)
# - 100 datasets: 200s → 25s (8x faster)
```

**Time estimate:** 4 hours implementation + 2 hours testing

---

## Week 3 Day 3: Session Cleanup (4 hours)

### Goal: Fix all unclosed aiohttp session warnings

**Current Issue:**
```log
Unclosed client session (x5)
Unclosed connector (x2)
```

**Root Cause:** Components using aiohttp don't have close() methods

**Components to Fix:**
1. **PDFDownloadManager** (`omics_oracle_v2/lib/storage/pdf/download_manager.py`)
2. **FullTextManager** (`omics_oracle_v2/lib/fulltext/manager.py`)
3. **InstitutionalAccessManager** (`omics_oracle_v2/lib/publications/clients/institutional_access.py`)
4. **GEOClient** (`omics_oracle_v2/lib/geo/client.py`)
5. **PublicationSearchPipeline** (`omics_oracle_v2/lib/pipelines/publication_pipeline.py`)

**Implementation Pattern:**
```python
class ComponentWithAiohttp:
    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Lazy initialize session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def some_method(self):
        """Use session for requests."""
        session = await self._get_session()
        async with session.get(url) as response:
            return await response.json()

    async def close(self) -> None:
        """Close aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()
            logger.debug(f"{self.__class__.__name__} session closed")
```

**Testing:**
```bash
# Run with warnings enabled
python -Walways tests/week2/test_day5_quick_validation.py 2>&1 | grep -i unclosed

# Should return: (empty)
```

**Time estimate:** 3 hours implementation + 1 hour testing

---

## Week 3 Day 4: Production Configuration (4 hours)

### Goal: Production-ready deployment configuration

**Tasks:**

#### 1. Environment Configuration (1 hour)
```yaml
# config/production.yml
environment: production

ncbi:
  email: "${NCBI_EMAIL}"  # Required for production
  api_key: "${NCBI_API_KEY}"  # Higher rate limits
  rate_limit: 10  # requests/second

redis:
  host: "${REDIS_HOST}"
  port: "${REDIS_PORT:6379}"
  password: "${REDIS_PASSWORD}"
  ssl: true
  db: 0

semantic_scholar:
  api_key: "${S2_API_KEY}"  # 100 req/sec vs 1 req/sec
  rate_limit: 100

logging:
  level: INFO  # Not DEBUG in production
  format: json  # Structured logging
  handlers:
    - type: file
      path: /var/log/omics_oracle/app.log
      rotation: daily
      retention: 30
    - type: syslog
      host: logs.example.com
```

#### 2. Health Checks (1 hour)
```python
# omics_oracle_v2/api/health.py

@router.get("/health")
async def health_check():
    """Health check endpoint for load balancers."""
    checks = {
        "redis": await check_redis(),
        "ncbi": await check_ncbi(),
        "semantic_scholar": await check_s2(),
    }

    healthy = all(checks.values())
    status_code = 200 if healthy else 503

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "healthy" if healthy else "degraded",
            "checks": checks,
            "timestamp": datetime.utcnow().isoformat(),
        }
    )

@router.get("/metrics")
async def metrics():
    """Prometheus-compatible metrics."""
    return {
        "cache_hit_rate": cache.metrics.hit_rate,
        "avg_search_time_ms": search_metrics.avg_time,
        "requests_total": search_metrics.total,
        "errors_total": search_metrics.errors,
    }
```

#### 3. Rate Limiting (1 hour)
```python
# Add rate limiting middleware
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/search")
@limiter.limit("10/minute")  # Per-user limit
async def search_endpoint(query: SearchRequest):
    ...
```

#### 4. Graceful Shutdown (1 hour)
```python
# omics_oracle_v2/main.py

@app.on_event("shutdown")
async def shutdown():
    """Cleanup resources on shutdown."""
    logger.info("Shutting down OmicsOracle...")

    # Close all pipelines
    if search_agent:
        await search_agent._unified_pipeline.close()

    # Close database connections
    await db.close()

    # Close cache
    await cache.close()

    logger.info("Shutdown complete")
```

**Time estimate:** 4 hours

---

## Week 3 Day 5: Load Testing & Validation (6 hours)

### Goal: Validate production readiness under load

#### 1. Load Testing Setup (2 hours)
```python
# tests/load/locustfile.py

from locust import HttpUser, task, between

class OmicsOracleUser(HttpUser):
    wait_time = between(1, 5)

    @task(3)  # 60% of traffic
    def search_geo(self):
        """Search GEO datasets."""
        self.client.post("/api/search", json={
            "query": "cancer genomics",
            "max_results": 20,
            "organism": "Homo sapiens"
        })

    @task(2)  # 40% of traffic
    def search_publications(self):
        """Search publications."""
        self.client.post("/api/search", json={
            "query": "CRISPR gene editing",
            "search_type": "publication",
            "max_results": 50
        })

    @task(1)  # 20% of traffic
    def geo_id_lookup(self):
        """Direct GEO ID lookup."""
        self.client.post("/api/search", json={
            "query": "GSE123456"
        })
```

**Run Load Tests:**
```bash
# Start application
docker-compose up -d

# Run load test
locust -f tests/load/locustfile.py \
    --host http://localhost:8000 \
    --users 10 \
    --spawn-rate 2 \
    --run-time 10m \
    --html reports/load_test_$(date +%Y%m%d).html

# Monitor metrics
curl http://localhost:8000/metrics
```

#### 2. Performance Benchmarks (2 hours)
```bash
# Benchmark suite
python tests/performance/benchmark_suite.py

Expected results:
- Simple GEO search: <2s (p50), <5s (p95)
- Complex publication search: <10s (p50), <30s (p95)
- GEO ID lookup: <1s (p50), <3s (p95)
- Cache hit: <0.1s (p50), <0.5s (p95)

Concurrent users:
- 1 user: 100% success rate
- 10 users: 100% success rate
- 50 users: 95%+ success rate
- 100 users: Graceful degradation (rate limiting kicks in)
```

#### 3. Stress Testing (2 hours)
```bash
# Find breaking point
ab -n 1000 -c 50 -p search_request.json http://localhost:8000/api/search

# Expected:
# - Handle 50 concurrent requests
# - <5s average response time
# - 0% error rate under normal load
# - Graceful degradation under heavy load
```

**Time estimate:** 6 hours

---

## Detailed Implementation Schedule

### Day 1: Monday - Cache Optimization
- **09:00-10:00**: Review Week 2 findings, plan Day 1
- **10:00-12:00**: Implement partial cache lookup in GEOClient
- **12:00-13:00**: Lunch break
- **13:00-15:00**: Implement partial cache for PublicationSearchPipeline
- **15:00-16:00**: Write tests for cache scenarios (0%, 50%, 95%, 100% hit rates)
- **16:00-17:00**: Run tests, measure speedup, document results

**Deliverables:**
- [ ] `GEOClient` with partial cache support
- [ ] `PublicationSearchPipeline` with per-publication caching
- [ ] Test suite with various hit rate scenarios
- [ ] Performance report showing 10-50x speedup

---

### Day 2: Tuesday - GEO Parallelization

- **09:00-10:00**: Profile current GEO fetch to identify bottleneck
- **10:00-11:00**: Review `fetch_metadata_batch()` implementation
- **11:00-12:00**: Fix parallelization (increase concurrency, add timeouts)
- **12:00-13:00**: Lunch break
- **13:00-14:00**: Test with various concurrency levels (5, 10, 20)
- **14:00-15:00**: Optimize parsing (stream processing if possible)
- **15:00-16:00**: Run validation tests, measure improvement
- **16:00-17:00**: Document findings, commit changes

**Deliverables:**
- [ ] GEO fetch speed: 2-5 datasets/sec (5-10x improvement)
- [ ] Timeout handling for slow datasets
- [ ] Benchmarks at different concurrency levels
- [ ] Performance report

---

### Day 3: Wednesday - Session Cleanup

- **09:00-10:00**: Audit all async components for aiohttp usage
- **10:00-12:00**: Add close() methods to 5 components
- **12:00-13:00**: Lunch break
- **13:00-14:00**: Update UnifiedSearchPipeline.close() to call all cleanups
- **14:00-15:00**: Test with validation suite
- **15:00-16:00**: Verify 0 unclosed session warnings
- **16:00-17:00**: Code review, commit, document

**Deliverables:**
- [ ] close() methods in all async components
- [ ] 0 unclosed session warnings in tests
- [ ] Cleanup verification in CI/CD
- [ ] Memory leak prevention validated

---

### Day 4: Thursday - Production Config

- **09:00-11:00**: Create production configuration files
- **11:00-12:00**: Implement health check endpoints
- **12:00-13:00**: Lunch break
- **13:00-14:00**: Add rate limiting middleware
- **14:00-15:00**: Implement graceful shutdown
- **15:00-16:00**: Test health checks and shutdown
- **16:00-17:00**: Document deployment process

**Deliverables:**
- [ ] `config/production.yml` with secrets management
- [ ] Health check endpoints (`/health`, `/metrics`)
- [ ] Rate limiting (10 req/min per user)
- [ ] Graceful shutdown handler
- [ ] Deployment documentation

---

### Day 5: Friday - Load Testing & Validation

- **09:00-10:00**: Set up Locust load testing
- **10:00-12:00**: Run load tests with 10, 50, 100 concurrent users
- **12:00-13:00**: Lunch break
- **13:00-14:00**: Analyze results, identify bottlenecks
- **14:00-15:00**: Run stress tests to find breaking point
- **15:00-16:00**: Document findings, create performance report
- **16:00-17:00**: Week 3 retrospective, plan Week 4

**Deliverables:**
- [ ] Load test suite with Locust
- [ ] Performance benchmarks under load
- [ ] Stress test results
- [ ] Production readiness report
- [ ] Week 3 summary document

---

## Success Metrics

### Performance Targets
- **Cache speedup**: 10-50x on repeated queries ✅
- **GEO fetch**: 2-5 datasets/sec ✅
- **Search latency**: <5s (p95) ✅
- **Concurrent users**: 50+ without degradation ✅

### Quality Targets
- **Test coverage**: 80%+ for new code ✅
- **Memory leaks**: 0 unclosed sessions ✅
- **Error rate**: <0.1% under normal load ✅
- **Uptime**: 99.9% availability ✅

### Documentation Targets
- **API docs**: Complete and up-to-date ✅
- **Deployment guide**: Step-by-step instructions ✅
- **Performance report**: Benchmarks and profiling ✅
- **Week 3 summary**: Achievements and next steps ✅

---

## Risk Assessment

### High Risk
1. **GEO parallelization might be limited by NCBI FTP**
   - Mitigation: Add exponential backoff, respect rate limits
   - Fallback: Accept 1-2 datasets/sec as baseline

2. **Cache might not scale to 1M+ datasets**
   - Mitigation: Add cache eviction policy (LRU)
   - Fallback: Implement cache sharding by query type

### Medium Risk
1. **Load testing might reveal new bottlenecks**
   - Mitigation: Profile under load, optimize hot paths
   - Plan extra time for fixes

2. **Production config might require infrastructure changes**
   - Mitigation: Document requirements early
   - Coordinate with DevOps

### Low Risk
1. **Session cleanup might have edge cases**
   - Mitigation: Comprehensive testing
   - Monitor in production

---

## Week 4 Preview: PDF Processing & Ranking Improvements

**Goals:**
1. **Ranking improvement**: Fix citation scoring to prioritize recent papers
   - Current: Old papers with many citations ranked highest
   - Target: Recent papers ranked highest, citations as secondary signal
   - Implementation: Recency-first scoring with citation dampening
2. Enable PDF download (configurable)
3. Full-text extraction from PDFs
4. Storage management and cleanup
5. Background processing pipeline

**Ranking Fix Details:**
```python
# Current (WRONG - favors old papers):
citation_score = log(citations + 1) / log(30828 + 1)  # 0.00 → 0.93
recency_bonus = 0.05 if age < 365 days else 0.00
final_score = citation_score + recency_bonus

# Proposed (RIGHT - favors recent papers):
recency_score = exp(-age_days / 365)  # 1.0 → 0.37 over 1 year
citation_signal = min(log(citations + 1) / 5, 0.3)  # Capped at 0.3
final_score = 0.7 * recency_score + 0.3 * citation_signal

# Examples:
# New paper (0 citations, 0 days): 0.7 * 1.0 + 0.3 * 0.0 = 0.70
# Popular recent (50 cit, 30 days): 0.7 * 0.92 + 0.3 * 0.24 = 0.71
# Seminal old (30k cit, 3650 days): 0.7 * 0.00 + 0.3 * 0.30 = 0.09
```

**Prerequisite:** Week 3 performance optimizations complete

**Estimated effort:** 5 days (40 hours)

---

## Quick Start Commands (Week 3)

### Monday Morning
```bash
# Review current status
cat CURRENT_STATUS.md
cat docs/planning/WEEK3_PLAN.md

# Start Day 1: Cache optimization
git checkout -b week3/cache-optimization
python tests/week2/test_cache_performance.py  # Baseline
```

### Daily Workflow
```bash
# Morning: Pull latest changes
git pull origin sprint-1/parallel-metadata-fetching

# During day: Run tests frequently
pytest tests/ -v --cov

# Evening: Commit progress
git add -A
git commit -m "Week 3 Day X: [description]"
git push
```

### End of Week
```bash
# Create Week 3 summary
cat > WEEK3_SUMMARY.md

# Merge to main branch
git checkout sprint-1/parallel-metadata-fetching
git merge week3/cache-optimization
git merge week3/parallelization-fix
git push

# Tag release
git tag -a v0.3.0 -m "Week 3: Performance & Production Readiness"
git push --tags
```

---

## Decision Log

### Decisions Made (Week 2 Day 5)
1. **GEO lazy loading**: Documented but deferred to future sprint
   - Rationale: 90% time savings possible, but not needed for current scale
   - Priority: LOW (nice to have)

2. **Session cleanup**: Analyzed but deferred to Week 3 Day 3
   - Rationale: Non-critical, doesn't block functionality
   - Priority: MEDIUM (quality improvement)

3. **Cache bug**: Fixed immediately
   - Rationale: Critical issue blocking all performance gains
   - Priority: CRITICAL

4. **Citation scoring reversal**: Identified but deferred to Week 4
   - Current issue: Old papers with many citations get highest weight
   - Desired: Recent papers should get highest weight
   - Example problem:
     * 30,828 citations → 0.93 score (HOMA-IR - seminal but old)
     * 0 citations → 0.00 score (new paper - potentially most relevant)
   - Rationale: Stay focused on Week 3 performance goals
   - Priority: HIGH (user experience improvement)
   - Proposed solution: Invert scoring or use recency-first ranking

### Decisions Pending
1. **GEO vector index**: Build now or wait?
   - Decision point: After Week 3 Day 1 (measure keyword ranking quality)
   - If keyword ranking is good → skip vector index
   - If ranking poor → build index in Week 3 Day 2

2. **Semantic Scholar API key**: Use free tier or paid?
   - Current: Free tier (1 req/sec, sufficient for now)
   - Upgrade if: Load testing shows bottleneck
   - Cost: $0 (free) vs $100/month (commercial)

---

**Document Created:** October 11, 2025 - 06:35 AM
**Next Review:** Monday, October 14, 2025
**Status:** Week 3 ready to start 🚀
