# Implementation Roadmap - Quick Reference 🗺️

## Overview

This is a quick reference guide for implementing semantic search and enhanced ranking in OmicsOracle.

---

## Phase Timeline

```
Phase 0: Cleanup         ████████░░░░ 6 hours   [Foundation]
Phase 1: Synonyms        ███░░░░░░░░░ 2 hours   [Quick Win - 30-40% improvement]
Phase 2: Semantic        ████████░░░░ 4 hours   [Major Impact - 2x improvement]
Phase 3: LLM Validation  ████░░░░░░░░ 3 hours   [Polish - Human-like judgment]
Phase 4: Monitoring      ████████████ Ongoing  [Continuous improvement]
───────────────────────────────────────────────────────────────────────
Total Implementation:    15 hours (2 days)
```

---

## Documents Created

| Document | Purpose | When to Use |
|----------|---------|-------------|
| `SCORING_SYSTEM_ANALYSIS.md` | Critical analysis of current system | Understanding problems |
| `SYSTEM_EVALUATION_SUMMARY.md` | Executive summary | Quick overview |
| `SEMANTIC_SEARCH_IMPLEMENTATION_PLAN.md` | Complete implementation plan | Overall strategy |
| `PHASE_0_CLEANUP_DETAILED.md` | Detailed cleanup steps | Phase 0 implementation |
| `semantic_ranker_example.py` | Working code example | Reference implementation |

---

## Implementation Order

### Phase 0: Codebase Consolidation (MUST DO FIRST!)
**Duration**: 6 hours
**Priority**: CRITICAL

#### Steps:
1. **Audit** (30 min)
   - Run code analysis
   - Document issues
   - Create cleanup plan

2. **Configuration** (1 hour)
   - Add `RankingConfig` class
   - Add `QualityConfig` class
   - Update `Settings`

3. **Extract Modules** (1.5 hours)
   - Create `omics_oracle_v2/lib/ranking/`
   - Implement `KeywordRanker`
   - Implement `QualityScorer`

4. **Update Agents** (1 hour)
   - Update `SearchAgent`
   - Update `DataAgent`
   - Remove old code

5. **Testing** (1 hour)
   - Unit tests for rankers
   - Integration tests
   - Coverage check

6. **Documentation** (30 min)
   - Update architecture docs
   - Create migration guide

7. **Cleanup** (30 min)
   - Remove dead code
   - Run full test suite
   - Benchmark performance

**Deliverable**: Clean, well-tested codebase ready for enhancements

---

### Phase 1: Synonym Mapping (Quick Win!)
**Duration**: 2 hours
**Impact**: 30-40% improvement immediately
**Cost**: $0

#### Steps:
1. **Create Synonym Database** (1 hour)
   - File: `omics_oracle_v2/lib/ranking/synonyms.py`
   - Add technique mappings
   - Build reverse index

2. **Integrate** (30 min)
   - Update `SearchAgent`
   - Expand search terms
   - Test integration

3. **Validate** (30 min)
   - Test NOMe-seq recognition
   - Test ATAC-seq expansion
   - Benchmark performance

**Deliverable**: System recognizes biomedical synonyms

**Example**:
```python
# Before:
Query: "chromatin accessibility"
Matches: Only datasets with exact phrase ❌

# After:
Query: "chromatin accessibility"
Matches: ATAC-seq, DNase-seq, FAIRE-seq, NOMe-seq ✅
```

---

### Phase 2: Semantic Search (Major Impact!)
**Duration**: 4 hours
**Impact**: 2x improvement in relevance
**Cost**: ~$0.005 per query

#### Steps:
1. **Embedding Service** (1.5 hours)
   - File: `omics_oracle_v2/lib/ranking/embeddings.py`
   - OpenAI integration
   - Disk caching
   - Similarity calculation

2. **Semantic Ranker** (1.5 hours)
   - File: `omics_oracle_v2/lib/ranking/semantic_ranker.py`
   - Hybrid scoring (60% semantic + 40% keyword)
   - Agreement boost
   - Fallback logic

3. **Integration** (30 min)
   - Update `SearchAgent`
   - Add configuration toggle
   - Error handling

4. **Testing** (30 min)
   - Test embedding generation
   - Test caching
   - Test hybrid scoring
   - Benchmark cost

**Deliverable**: Embedding-based semantic similarity working

**Example**:
```python
# Before:
GSE200685: "NOMe-seq study" → Score: 0.15 ❌

# After:
GSE200685: "NOMe-seq study" → Score: 0.90 ✅
(System understands NOMe-seq = methylation + accessibility)
```

---

### Phase 3: LLM Validation (Optional)
**Duration**: 3 hours
**Impact**: Human-like judgment
**Cost**: ~$0.03 per query

#### Steps:
1. **LLM Validator** (1.5 hours)
   - File: `omics_oracle_v2/lib/ranking/llm_validator.py`
   - GPT-4 integration
   - Prompt engineering
   - Response parsing

2. **Integration** (1 hour)
   - Apply to top 10 results
   - Cost tracking
   - Configuration

3. **Testing** (30 min)
   - Test validation
   - Cost monitoring
   - Quality check

**Deliverable**: LLM validates top results

---

### Phase 4: Monitoring (Ongoing)
**Duration**: Ongoing
**Priority**: Important for long-term success

#### Metrics to Track:
- Embedding API calls & costs
- LLM API calls & costs
- Cache hit rates
- Ranking accuracy
- User satisfaction

#### Tasks:
- Set up dashboards
- Monitor costs
- A/B testing
- User feedback
- Iterate on synonyms

---

## Quick Start Commands

### Run Phase 0 Audit:
```bash
# Code statistics
find omics_oracle_v2 -name "*.py" | xargs wc -l

# Find hardcoded values
grep -r "0\.[0-9]" omics_oracle_v2/agents/*.py

# Find TODOs
grep -r "TODO\|FIXME" omics_oracle_v2/
```

### Run Tests:
```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# Coverage
pytest --cov=omics_oracle_v2 --cov-report=html

# Benchmarks
pytest tests/benchmarks/ -v
```

### Check Code Quality:
```bash
# Linting
pylint omics_oracle_v2/

# Formatting
black omics_oracle_v2/ --check

# Type checking
mypy omics_oracle_v2/
```

---

## Configuration Examples

### Enable Semantic Search (Phase 2):
```bash
# Environment variable
export OMICS_RANKING__USE_SEMANTIC_RANKING=true
export OMICS_RANKING__SEMANTIC_WEIGHT=0.6
```

Or in `config/production.yml`:
```yaml
ranking:
  use_semantic_ranking: true
  semantic_weight: 0.6
  keyword_weight: 0.4
```

### Enable LLM Validation (Phase 3):
```bash
export OMICS_RANKING__ENABLE_LLM_VALIDATION=true
export OMICS_RANKING__LLM_VALIDATION_TOP_N=10
```

---

## Cost Estimates

| Component | Cost per Query | Monthly (1000 queries) |
|-----------|----------------|------------------------|
| NCBI API | $0 | $0 |
| Embeddings (50 datasets) | ~$0.005 | ~$5 |
| LLM Validation (top 10) | ~$0.030 | ~$30 |
| **Total** | **~$0.035** | **~$35** |

**Very affordable for 2x better results!**

---

## Success Metrics

### Phase 0:
- ✅ All configuration extracted
- ✅ Test coverage ≥ 80%
- ✅ No performance regression
- ✅ Documentation complete

### Phase 1:
- ✅ NOMe-seq recognized as joint profiling
- ✅ 30-40% more datasets found
- ✅ Synonym database comprehensive

### Phase 2:
- ✅ Semantic similarity working
- ✅ Cache hit rate > 50%
- ✅ Cost < $0.01 per query
- ✅ 2x better ranking accuracy

### Phase 3:
- ✅ LLM validation working
- ✅ Cost tracked and acceptable
- ✅ Top results validated

---

## File Structure After Implementation

```
omics_oracle_v2/
├── core/
│   ├── config.py               # ← Updated with RankingConfig, QualityConfig
│   └── ...
├── lib/
│   ├── ranking/                # ← NEW MODULE
│   │   ├── __init__.py
│   │   ├── keyword_ranker.py   # Phase 0
│   │   ├── quality_scorer.py   # Phase 0
│   │   ├── synonyms.py         # Phase 1
│   │   ├── embeddings.py       # Phase 2
│   │   ├── semantic_ranker.py  # Phase 2
│   │   └── llm_validator.py    # Phase 3
│   ├── ai/
│   ├── geo/
│   └── nlp/
├── agents/
│   ├── search_agent.py         # ← Updated to use new rankers
│   ├── data_agent.py           # ← Updated to use QualityScorer
│   └── ...
└── ...

tests/
├── unit/
│   └── lib/
│       └── ranking/            # ← NEW TESTS
│           ├── test_keyword_ranker.py
│           ├── test_quality_scorer.py
│           ├── test_synonyms.py
│           ├── test_embeddings.py
│           └── test_semantic_ranker.py
├── integration/
│   └── test_ranking_integration.py
└── benchmarks/
    └── test_ranking_performance.py

docs/
├── planning/                   # ← NEW DOCUMENTATION
│   ├── SEMANTIC_SEARCH_IMPLEMENTATION_PLAN.md
│   ├── PHASE_0_CLEANUP_DETAILED.md
│   └── ...
├── configuration/
│   └── RANKING_CONFIG.md       # ← NEW
└── ...
```

---

## Common Issues & Solutions

### Issue: Embeddings too expensive
**Solution**: Increase cache hit rate, use smaller model (text-embedding-3-small)

### Issue: LLM validation slow
**Solution**: Only validate top N results, use parallel requests

### Issue: Synonyms incomplete
**Solution**: Add more mappings based on user queries, use ontologies

### Issue: Semantic ranking not better than keyword
**Solution**: Adjust weights, check embeddings quality, validate test cases

---

## Next Actions

1. **Review all documentation**
   - [ ] Read `SEMANTIC_SEARCH_IMPLEMENTATION_PLAN.md`
   - [ ] Read `PHASE_0_CLEANUP_DETAILED.md`
   - [ ] Understand the strategy

2. **Decide on approach**
   - [ ] Approve phased implementation
   - [ ] Set timeline
   - [ ] Allocate resources

3. **Start Phase 0**
   - [ ] Run code audit
   - [ ] Create configuration classes
   - [ ] Extract ranking modules
   - [ ] Write tests
   - [ ] Validate

4. **Then proceed sequentially**
   - Phase 0 → Phase 1 → Phase 2 → (Optional) Phase 3

---

## Questions?

- **Why Phase 0 first?** Clean foundation prevents technical debt
- **Can we skip phases?** No, each builds on previous
- **When will we see results?** Phase 1 gives 30-40% improvement in ~2 hours!
- **Is it worth the cost?** Yes! 3.5 cents per query for 2x better results

---

**Ready to start? Begin with Phase 0!** 🚀
