# Week 2: Integration & Testing Plan

**Status:** Ready to Begin
**Week 1:** ✅ COMPLETE (1,916 lines of production code)
**Week 2 Goal:** Integrate unified pipeline with external services

---

## 🎯 Week 2 Objectives

Integrate the Week 1 unified pipeline components with actual external services:
1. **GEO Client** - NCBI GEO dataset search and metadata fetching
2. **PublicationSearchPipeline** - PubMed, OpenAlex, Google Scholar publication search
3. **Redis Cache** - Production caching layer with local Redis server
4. **SearchAgent Migration** - Update to use OmicsSearchPipeline
5. **Performance Testing** - Benchmark before/after migration

---

## 📅 Day-by-Day Plan

### **Day 1-2: External Search Integration** (Priority: HIGH)

**Goal:** Connect OmicsSearchPipeline to actual search backends

**Tasks:**

#### GEO Client Integration
```python
# Initialize GEO client in OmicsSearchPipeline.__init__()
if config.enable_geo_search:
    from omics_oracle_v2.lib.geo import GEOClient
    from omics_oracle_v2.core.config import GEOSettings

    geo_settings = GEOSettings(
        email=config.ncbi_email,
        api_key=config.ncbi_api_key,
    )
    self.geo_client = GEOClient(geo_settings)
```

**Test Cases:**
- [ ] GEO ID lookup (GSE123456)
- [ ] GEO keyword search ("diabetes RNA-seq")
- [ ] Metadata caching
- [ ] Error handling (invalid IDs, API failures)

#### Publication Pipeline Integration
```python
# Initialize publication pipeline in OmicsSearchPipeline.__init__()
if config.enable_publication_search:
    from omics_oracle_v2.lib.pipelines.publication_pipeline import PublicationSearchPipeline
    from omics_oracle_v2.lib.publications.config import PublicationSearchConfig

    pub_config = PublicationSearchConfig(
        enable_pubmed=True,
        enable_openalex=True,
        enable_citations=False,  # Week 3
    )
    self.publication_pipeline = PublicationSearchPipeline(pub_config)
```

**Test Cases:**
- [ ] Biomedical query ("APOE Alzheimer's disease")
- [ ] Multi-source search results
- [ ] Deduplication with actual duplicates
- [ ] Performance with real API calls

**Deliverables:**
- ✅ GEO client fully integrated
- ✅ Publication pipeline fully integrated
- ✅ Integration tests passing
- ✅ Error handling complete

---

### **Day 3: Redis Cache Testing** (Priority: MEDIUM)

**Goal:** Test Redis caching with local Redis server

**Setup:**
```bash
# Install Redis
brew install redis

# Start Redis server
redis-server

# Test connection
redis-cli ping
# Expected: PONG
```

**Test Cases:**
- [ ] Search result caching (24h TTL)
- [ ] Publication metadata caching (7d TTL)
- [ ] GEO metadata caching (30d TTL)
- [ ] Query optimization caching (24h TTL)
- [ ] Cache hit/miss scenarios
- [ ] TTL expiration
- [ ] Cache invalidation
- [ ] Connection failure graceful degradation

**Performance Tests:**
```python
# Benchmark cache performance
query = "diabetes insulin resistance"

# First run (cache miss)
start = time.time()
result1 = await pipeline.search(query)
cold_time = time.time() - start

# Second run (cache hit)
start = time.time()
result2 = await pipeline.search(query)
hot_time = time.time() - start

speedup = cold_time / hot_time
print(f"Cache speedup: {speedup:.1f}x")
# Expected: 5-10x speedup
```

**Deliverables:**
- ✅ Redis server running locally
- ✅ All cache operations tested
- ✅ Performance gains measured
- ✅ Failure handling verified

---

### **Day 4-5: SearchAgent Migration** (Priority: HIGH)

**Goal:** Migrate SearchAgent to use OmicsSearchPipeline

**Current Architecture:**
```python
# OLD (3 separate pipelines)
class SearchAgent:
    def __init__(self):
        self._geo_client = GEOClient()
        self._publication_pipeline = PublicationSearchPipeline()
        self._geo_citation_pipeline = GEOCitationPipeline()
```

**New Architecture:**
```python
# NEW (unified pipeline)
class SearchAgent:
    def __init__(self):
        config = UnifiedSearchConfig(
            enable_geo_search=True,
            enable_publication_search=True,
            enable_query_optimization=True,
            enable_caching=True,
            enable_deduplication=True,
        )
        self._pipeline = OmicsSearchPipeline(config)

    async def search(self, query: str):
        return await self._pipeline.search(query)
```

**Migration Steps:**
1. [ ] Create SearchAgent wrapper around OmicsSearchPipeline
2. [ ] Update API endpoints to use new SearchAgent
3. [ ] Test backward compatibility
4. [ ] Update dashboard integration
5. [ ] Update bulk collection scripts
6. [ ] Comprehensive integration testing

**Test Cases:**
- [ ] API endpoint compatibility
- [ ] Dashboard search functionality
- [ ] Bulk collection scripts
- [ ] Performance comparison (before/after)
- [ ] Error handling
- [ ] Edge cases (empty queries, invalid IDs, etc.)

**Deliverables:**
- ✅ SearchAgent migrated to unified pipeline
- ✅ All API tests passing
- ✅ Dashboard integration complete
- ✅ Performance benchmarks documented

---

## 📊 Success Metrics

### Functionality
- [ ] GEO ID fast path working (6x+ speedup)
- [ ] Multi-source publication search working
- [ ] Deduplication removing actual duplicates
- [ ] Cache hit rate >80% for repeated queries
- [ ] All existing features working with new pipeline

### Performance
- [ ] GEO ID queries: <500ms (vs 1,350ms before)
- [ ] Text queries: <2s with cache miss
- [ ] Cache hit queries: <200ms
- [ ] No performance regression vs old architecture

### Code Quality
- [ ] All unit tests passing
- [ ] Integration tests complete
- [ ] Error handling comprehensive
- [ ] Logging appropriate
- [ ] Documentation updated

---

## 🧪 Testing Strategy

### Unit Tests
```bash
# Test individual components
pytest tests/query/test_analyzer.py -v
pytest tests/query/test_optimizer.py -v
pytest tests/cache/test_redis_cache.py -v
pytest tests/pipelines/test_unified_search_pipeline.py -v
```

### Integration Tests
```bash
# Test with actual external services
python test_unified_pipeline_integration.py
```

### End-to-End Tests
```bash
# Test complete workflows
python test_e2e_geo_search.py
python test_e2e_publication_search.py
python test_e2e_mixed_search.py
```

### Performance Benchmarks
```bash
# Compare before/after performance
python benchmark_unified_pipeline.py
```

---

## 🚧 Potential Issues & Mitigations

### Issue 1: API Rate Limiting
**Risk:** External APIs (NCBI, PubMed) have rate limits
**Mitigation:**
- Use caching aggressively
- Implement exponential backoff
- Batch requests where possible
- Monitor API usage

### Issue 2: Redis Connection Failures
**Risk:** Redis server down or unreachable
**Mitigation:**
- Graceful degradation (already implemented)
- Connection retry logic
- Health check monitoring
- Fallback to no-cache mode

### Issue 3: Backward Compatibility
**Risk:** Breaking changes to existing API
**Mitigation:**
- Keep SearchAgent as wrapper (maintains API contract)
- Comprehensive regression tests
- Feature flags for gradual rollout
- Rollback plan documented

### Issue 4: Performance Regression
**Risk:** New pipeline slower than old architecture
**Mitigation:**
- Benchmark before/after
- Profile hot paths
- Optimize bottlenecks
- A/B testing in production

---

## 📚 Documentation Updates

### To Create:
- [ ] `WEEK_2_INTEGRATION_COMPLETE.md` - Final summary
- [ ] `REDIS_CACHING_GUIDE.md` - Cache configuration and tuning
- [ ] `SEARCHAGENT_MIGRATION_GUIDE.md` - Migration instructions
- [ ] `PERFORMANCE_BENCHMARKS.md` - Before/after comparisons

### To Update:
- [ ] `README.md` - Add unified pipeline instructions
- [ ] `API_REFERENCE.md` - Update endpoint documentation
- [ ] `QUICK_START.md` - Update getting started guide

---

## 🎯 Week 2 Completion Criteria

**Must Have:**
- ✅ GEO client integrated and tested
- ✅ Publication pipeline integrated and tested
- ✅ Redis cache working with all operations
- ✅ SearchAgent migrated successfully
- ✅ All existing functionality working
- ✅ Performance same or better

**Should Have:**
- ✅ Cache hit rate >80% for common queries
- ✅ GEO ID queries 5x+ faster
- ✅ Comprehensive integration tests
- ✅ Performance benchmarks documented

**Nice to Have:**
- ✅ Dashboard showing cache statistics
- ✅ API analytics for cache performance
- ✅ Advanced query syntax documentation
- ✅ User feedback incorporated

---

## 🚀 Beyond Week 2: Week 3-4 Preview

### Week 3: Advanced Features (Days 11-15)
- [ ] UMLS Linker integration for canonical entity IDs
- [ ] SynonymExpander enhancement for all entity types
- [ ] Direct SapBERT similarity search
- [ ] Batch query optimization

### Week 4: Production Polish (Days 16-20)
- [ ] Parallel search execution (asyncio.gather)
- [ ] Query result pagination
- [ ] Memory usage optimization
- [ ] API documentation generation
- [ ] Migration guide for existing code
- [ ] Performance tuning guide

---

## 📝 Notes

**Current Status (End of Week 1):**
- ✅ QueryAnalyzer: 268 lines, tested
- ✅ QueryOptimizer: 562 lines, tested with production tools
- ✅ RedisCache: 553 lines, implementation complete
- ✅ OmicsSearchPipeline: 521 lines, orchestration tested
- ✅ **Total:** 1,916 lines of production code

**Week 2 Target:**
- Complete integration with external services
- Production-ready unified pipeline
- Performance validated
- Ready for Week 3 advanced features

**Contact & Support:**
- Questions? Check `docs/FAQ.md`
- Issues? Open GitHub issue
- Discussion? See `docs/CONTRIBUTING.md`

---

**Last Updated:** October 11, 2025
**Next Review:** Day 6 (mid-Week 2 checkpoint)
**Prepared By:** AI Assistant with User Approval
