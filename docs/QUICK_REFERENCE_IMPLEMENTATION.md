# Quick Reference: Citation Discovery Enhancement & Code Reorganization

**Date:** October 14, 2025  
**Status:** Ready to Implement

---

## 📚 Documents Created

1. **CITATION_DISCOVERY_IMPLEMENTATION_GUIDE.md** (Main Document)
   - 18 sections covering all phases
   - Detailed code implementations
   - Testing strategies
   - Full technical specifications

2. **CODE_ORGANIZATION_RECOMMENDATION.md** (Structure Analysis)
   - Current vs. proposed structure
   - Migration plan
   - Developer experience analysis
   - Strong recommendation for pipeline-centric layout

3. **THREE_PIPELINE_ARCHITECTURE.md** (Architecture Overview)
   - Complete flow diagrams
   - All 3 pipelines documented
   - Data flow examples

4. **PIPELINE_ANALYSIS_DISCOVERY_VS_URL_COLLECTION.md** (Why Keep Both)
   - Proves Pipeline 1 cannot be deleted
   - Explains fundamental differences
   - Architecture justification

---

## 🎯 Key Decisions

### Decision 1: Enhance Pipeline 1 ✅
**Action:** Add 3 new sources + caching + error handling  
**Impact:** +150% coverage, +50% speed, 100% reliability  
**Time:** 3-4 weeks  

### Decision 2: Reorganize Code ✅
**Action:** Adopt pipeline-centric structure  
**Impact:** Massive clarity improvement  
**Time:** 1 week  
**Do:** Before enhancement work (clean slate)

---

## 🚀 Implementation Order

### Phase 0: Code Reorganization (1 week)
```
Current: Scattered across 3 folders
Proposed: lib/pipelines/pipeline{1,2,3}_*/
```

### Phase 1: Semantic Scholar (3 days)
```python
# Add 2nd citation source
SemanticScholarClient → geo_discovery.py
Coverage: +100%
```

### Phase 2: Caching (2 days)
```python
# Two-layer cache (memory + SQLite)
DiscoveryCache → 70-80% speedup
```

### Phase 3: Error Handling (2 days)
```python
# Retry + fallback chains
FallbackChain → 100% reliability
```

### Phases 4-9: Advanced Features (2-3 weeks)
- Deduplication
- Relevance scoring
- Europe PMC + Crossref
- Quality validation
- Adaptive strategies

---

## 📊 Expected Results

### After Phases 1-3 (Week 2)
| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Sources | 2 | 3 | +50% |
| Coverage | 15-30 | 30-60 | +100% |
| Speed | 2-3s | 1-2s | +50% |
| Reliability | 85% | 99% | +14% |

### After Full Implementation (Week 4)
| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Sources | 2 | 5 | +150% |
| Coverage | 15-30 | 40-80 | +150% |
| Precision | 80% | 95% | +15% |
| Speed | 2-3s | 1-2s | +50% |
| Reliability | 85% | 100% | +15% |

---

## 🏗️ New File Structure

```
omics_oracle_v2/lib/pipelines/
├── pipeline1_discovery/
│   ├── geo_discovery.py            # Main discovery
│   ├── deduplicator.py             # Smart dedup
│   ├── scorer.py                   # Relevance scoring
│   ├── validator.py                # Quality checks
│   ├── cache.py                    # Two-layer cache
│   └── clients/
│       ├── openalex.py
│       ├── pubmed.py
│       ├── semantic_scholar.py     # NEW
│       ├── europepmc.py            # NEW
│       └── crossref.py             # NEW
│
├── pipeline2_url_collection/
│   ├── manager.py                  # URL collection
│   └── sources/                    # 11 sources
│
└── pipeline3_download/
    └── download_manager.py         # PDF download
```

---

## 💻 Quick Start Commands

### 1. Code Reorganization
```bash
# Create branch
git checkout -b refactor/pipeline-organization

# Run migration (see CITATION_DISCOVERY_IMPLEMENTATION_GUIDE.md Section 18.4)
# ... migration commands ...

# Test
pytest tests/

# Commit
git commit -m "refactor: reorganize code into pipeline-centric structure"
```

### 2. Semantic Scholar Implementation
```bash
# Create files
touch omics_oracle_v2/lib/pipelines/pipeline1_discovery/clients/semantic_scholar.py

# Copy implementation from CITATION_DISCOVERY_IMPLEMENTATION_GUIDE.md Section 5.2

# Update geo_discovery.py (Section 5.3)

# Test
pytest tests/unit/lib/pipelines/pipeline1_discovery/test_semantic_scholar.py
```

### 3. Caching Implementation
```bash
# Create cache manager
touch omics_oracle_v2/lib/pipelines/pipeline1_discovery/cache.py

# Copy implementation from Section 6.2

# Integrate (Section 6.3)

# Test
pytest tests/unit/lib/pipelines/pipeline1_discovery/test_cache.py
```

---

## 📋 Implementation Checklist

### Week 1: Code Reorganization
- [ ] Create `lib/pipelines/` structure
- [ ] Move Pipeline 1 files
- [ ] Move Pipeline 2 files
- [ ] Move Pipeline 3 files
- [ ] Update all imports
- [ ] Update tests
- [ ] Integration test
- [ ] Deploy

### Week 2: Quick Wins (Phases 1-3)
- [ ] Implement Semantic Scholar client
- [ ] Integrate into geo_discovery.py
- [ ] Write tests for S2
- [ ] Implement cache manager
- [ ] Integrate caching
- [ ] Implement retry logic
- [ ] Implement fallback chains
- [ ] Full integration test
- [ ] Deploy to staging

### Week 3: Advanced Features (Phases 4-6)
- [ ] Implement deduplicator
- [ ] Implement relevance scorer
- [ ] Add Europe PMC client
- [ ] Add Crossref client
- [ ] Write comprehensive tests
- [ ] Integration test
- [ ] Deploy to staging

### Week 4: Polish & Deploy (Phases 7-9)
- [ ] Implement quality validator
- [ ] Implement adaptive strategies
- [ ] Performance optimization
- [ ] Full system test
- [ ] Documentation update
- [ ] Production deployment
- [ ] Monitor & validate

---

## 🎓 Key Insights

### Why Reorganize?
**Before:** "Where's the citation code?" → 30-60 min search  
**After:** "Where's the citation code?" → Open `pipeline1_discovery/` → 5 min

### Why Enhance Pipeline 1?
**Problem:** Only 2 sources, brittle, no caching  
**Solution:** 5 sources, resilient, cached, scored  
**Result:** 2.5x more papers, 95% precision, 100% uptime

### Why Keep Pipeline 1 Separate?
**Pipeline 1:** "WHICH papers?" (discovery)  
**Pipeline 2:** "WHERE to download?" (URL lookup)  
**Cannot merge:** Fundamentally different problems

---

## 📞 Next Actions

1. **Review documents** (30 min)
   - CITATION_DISCOVERY_IMPLEMENTATION_GUIDE.md
   - CODE_ORGANIZATION_RECOMMENDATION.md

2. **Make decision** (15 min)
   - Approve code reorganization?
   - Approve enhancement plan?
   - Set timeline

3. **Start implementation** (Week 1)
   - Create feature branch
   - Begin migration
   - Or start with Semantic Scholar if skipping reorg

---

## 🏆 Success Criteria

### Code Quality
- ✅ All tests pass
- ✅ Code coverage >80%
- ✅ No breaking changes
- ✅ Clean architecture

### Performance
- ✅ 70%+ cache hit rate
- ✅ <2 sec per discovery
- ✅ 40-80 papers found
- ✅ 95%+ precision

### Reliability
- ✅ Graceful degradation
- ✅ No total failures
- ✅ Retry logic works
- ✅ Fallback chains tested

---

**Status:** Ready for Approval & Implementation ✅  
**Confidence Level:** Very High (9/10)  
**Risk Level:** Low (incremental, backward-compatible)

---
