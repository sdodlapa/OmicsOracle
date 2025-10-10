# Full-Text Enhancement: Quick Start Summary

**For Academic Research Purposes Only**

---

## 🎯 What We're Doing

**Objective**: Increase full-text PDF access from **40-50%** to **70-90%**

**Approach**:
1. **Phase 1 (2 weeks)**: Legal OA sources → 60-70% coverage, $0 cost ✅ SAFE
2. **Phase 2 (optional)**: Sci-Hub fallback → 90-95% coverage ⚠️ REQUIRES LEGAL REVIEW

---

## 📊 Current State (What We Already Have)

| Component | Status | Notes |
|-----------|--------|-------|
| PDFDownloader | ✅ Working | Concurrent downloads, retry logic |
| FullTextExtractor | ✅ Working | pdfplumber, PyPDF2, HTML |
| Institutional Access | ✅ Working | Georgia Tech VPN, ODU EZProxy |
| Unpaywall | ✅ Built-in | Via institutional_access.py |
| PMC | ✅ Working | 6M+ articles |
| OpenAlex | ✅ Working | Has OA URLs in metadata! |

**Current Coverage**: ~40-50% (legal only)

---

## 🚀 Phase 1: Legal OA Enhancement (START HERE)

### What We're Adding

| New Source | Coverage Gain | Cost | Legal Risk |
|------------|---------------|------|------------|
| **CORE** | +10-15% | Free API key | NONE ✅ |
| **bioRxiv/medRxiv** | +2-3% | Free | NONE ✅ |
| **Crossref** | +2-3% | Free | NONE ✅ |
| **arXiv** | +2-3% | Free | NONE ✅ |
| **Enhanced OpenAlex** | +5-10% | Free | NONE ✅ |
| **Total** | **+20-30%** | **$0** | **NONE ✅** |

### Result: 60-70% Total Coverage (Legal Only)

---

## 📋 Implementation Plan (2 Weeks)

### Week 1: Build OA Source Clients
```
Day 1-2: CORE API Client        (+10-15%)
Day 2-3: arXiv Client            (+2-3%)
Day 3-4: bioRxiv Client          (+2-3%)
Day 4:   Enhance OpenAlex        (+5-10%)
Day 5:   Crossref Client         (+2-3%)
```

### Week 2: Integrate & Test
```
Day 6-7:   FullTextManager (waterfall orchestrator)
Day 7:     Update config + pipeline
Day 8:     Integration testing
Day 9-10:  Coverage benchmark + bug fixes
```

---

## 🏗️ Architecture Overview

```
Publication → FullTextManager → Waterfall Strategy
                    ↓
        ┌───────────┴──────────┐
        │ Try sources in order │
        └───────────┬──────────┘
                    ↓
    ┌───────────────┴───────────────┐
    │ 1. Institutional (GT VPN/ODU) │ ← Highest quality
    │ 2. PMC                        │
    │ 3. OpenAlex OA URLs           │
    │ 4. Unpaywall                  │
    │ 5. CORE                       │ ← NEW
    │ 6. bioRxiv/medRxiv            │ ← NEW
    │ 7. Crossref                   │ ← NEW
    │ 8. arXiv                      │ ← NEW
    └───────────────┬───────────────┘
                    ↓
            ✅ Success or ❌ Not Found
```

**Waterfall Logic**: Try each source until success or exhaustion

---

## 📁 New Files to Create

```
omics_oracle_v2/lib/publications/
├── clients/
│   └── oa_sources/              ← NEW DIRECTORY
│       ├── __init__.py
│       ├── core_client.py       ← CORE API (45M papers)
│       ├── arxiv_client.py      ← arXiv preprints
│       ├── biorxiv_client.py    ← bioRxiv/medRxiv
│       └── crossref_client.py   ← Crossref links
└── fulltext_manager.py          ← NEW - Orchestrator

tests/
├── test_core_client.py
├── test_arxiv_client.py
├── test_biorxiv_client.py
├── test_fulltext_manager.py
└── test_fulltext_coverage.py    ← Benchmark (1000 DOIs)
```

---

## 🛠️ Quick Start Steps

### 1. Get API Keys (5 minutes)
```bash
# CORE (free)
# Visit: https://core.ac.uk/api-keys/register
# Add to config: core_api_key = "YOUR_KEY"

# Others: No API keys needed!
```

### 2. Install Dependencies (if needed)
```bash
pip install aiohttp feedparser
```

### 3. Start Implementation
```bash
# Create directory structure
mkdir -p omics_oracle_v2/lib/publications/clients/oa_sources

# Start with CORE client (highest impact)
# See FULLTEXT_ENHANCEMENT_PLAN.md for detailed code
```

---

## ✅ Success Metrics

### Phase 1 Complete When:
- [ ] Coverage ≥60% on 1000 test DOIs
- [ ] Average time <2s per paper
- [ ] All 5 OA clients working
- [ ] FullTextManager integrated
- [ ] Tests passing (≥80% coverage)
- [ ] Documentation complete

### Then Measure:
- Is 60-70% coverage sufficient?
- Or proceed to Phase 2 (Sci-Hub fallback)?

---

## ⚠️ Phase 2: Sci-Hub Fallback (OPTIONAL)

**Only implement if**:
1. ✅ Phase 1 complete
2. ✅ Coverage measured (<70% insufficient)
3. ✅ Legal review with university counsel
4. ✅ Written institutional approval
5. ✅ User opts in explicitly

**Benefits**:
- +30-40% additional coverage
- Total 90-95% coverage

**Risks**:
- Moderate-high legal risk
- Requires compliance framework
- Audit logging required
- Research-only use

**Approach** (if approved):
- Use LibGen torrents (NOT live scraping)
- More ethical, faster, safer
- Selective downloads (not full corpus)
- Strict access controls

---

## 📚 Documentation

See detailed docs in:
- **FULLTEXT_ENHANCEMENT_PLAN.md** - Complete implementation guide
- **FULLTEXT_ACCESS_STRATEGY.md** - Strategic analysis of all options
- **FULLTEXT_IMPLEMENTATION_ROADMAP.md** - Original 2-week roadmap

---

## 🎯 Recommendation

**START**: Phase 1 (legal OA enhancement)
- 2 weeks implementation
- $0 cost
- No legal risk
- 60-70% coverage target

**THEN DECIDE**: Phase 2 only if needed after measuring Phase 1 results

---

## 💡 Key Points

1. ✅ **100% legal in Phase 1** - all sources are open access or institutional
2. ✅ **$0 total cost** - all APIs are free
3. ✅ **Production-ready** - builds on existing solid infrastructure
4. ✅ **Research purposes** - designed for academic research workflow
5. ⚠️ **Phase 2 optional** - only with legal approval

---

**Ready to start? Begin with CORE API client implementation!**

See `FULLTEXT_ENHANCEMENT_PLAN.md` for detailed implementation steps.
