# Phase 0: Code Audit Report 🔍

**Date**: October 5, 2025
**Auditor**: GitHub Copilot
**Purpose**: Prepare codebase for semantic search implementation

---

## Executive Summary

**Codebase Health**: Good overall structure, but needs consolidation before adding new features.

**Key Findings**:
- ✅ Clean agent-based architecture
- ⚠️  Hardcoded scoring weights and thresholds
- ⚠️  No separate ranking/scoring modules
- ⚠️  Limited test coverage for scoring logic
- ✅ Good model definitions

**Recommendation**: Proceed with Phase 0 refactoring to extract configurations and create modular ranking system.

---

## 1. Code Statistics

### Overall Metrics
- **Total Python Lines**: 20,636 lines
- **Agent Files**: 2,756 lines (13.4% of codebase)
- **Core Files to Refactor**: 791 lines
  - `search_agent.py`: ~390 lines
  - `data_agent.py`: ~401 lines

### File Breakdown
```
omics_oracle_v2/
├── agents/           ~2,756 lines (5 agents)
├── lib/              ~8,000 lines (geo, ai, nlp)
├── api/              ~4,200 lines (routes, models)
├── core/             ~1,800 lines (config, settings)
└── database/         ~1,200 lines (models, session)
```

---

## 2. Issues Found

### 2.1 Hardcoded Scoring Weights

**File**: `omics_oracle_v2/agents/search_agent.py`

**Lines 334-365**: Relevance scoring with magic numbers
```python
# HARDCODED!
title_score = min(0.4, title_matches * 0.2)      # Line 338
summary_score = min(0.3, summary_matches * 0.15)  # Line 346
organism_bonus = 0.15                              # Line 354
sample_bonus = 0.15                                # Line 361
```

**Impact**:
- Cannot tune weights without code changes
- No A/B testing capability
- Difficult to explain scoring to users

**Solution**: Extract to `RankingConfig` in settings

---

### 2.2 Hardcoded Quality Thresholds

**File**: `omics_oracle_v2/agents/data_agent.py`

**Lines 223-285**: Quality scoring with magic numbers
```python
# HARDCODED SAMPLE COUNT THRESHOLDS
if metadata.sample_count >= 100:    # Line 223
    score += 20
elif metadata.sample_count >= 50:   # Line 226
    score += 15
elif metadata.sample_count >= 10:   # Line 229
    score += 10

# HARDCODED TEXT LENGTH THRESHOLDS
if title_len >= 50:                 # Line 243
    score += 15
elif title_len >= 20:               # Line 241
    score += 10

# HARDCODED SUMMARY THRESHOLDS
if summary_len >= 200:              # Line 256
    score += 15
elif summary_len >= 100:            # Line 259
    score += 10
```

**Impact**:
- Thresholds may not be optimal
- Cannot customize for different use cases
- Hard to maintain consistency

**Solution**: Extract to `QualityConfig` in settings

---

### 2.3 Monolithic Scoring Methods

**SearchAgent._calculate_relevance()**: 58 lines (lines 320-378)
- Mixes multiple concerns (title, summary, organism, samples)
- Hard to test individual components
- Difficult to extend with new ranking algorithms

**DataAgent._calculate_quality_score()**: 78 lines (lines 213-291)
- Complex nested conditionals
- Multiple responsibilities
- No clear separation of scoring dimensions

**Solution**:
- Extract `KeywordRanker` class
- Extract `QualityScorer` class
- Create `omics_oracle_v2/lib/ranking/` module

---

### 2.4 Missing Configuration Classes

**Current State**: No dedicated ranking configuration

**What's Missing**:
```python
# Need to add to omics_oracle_v2/core/config.py
class RankingConfig(BaseModel):
    """Configuration for relevance ranking."""
    keyword_title_weight: float = 0.4
    keyword_summary_weight: float = 0.3
    keyword_organism_bonus: float = 0.15
    keyword_sample_count_bonus: float = 0.15
    # ... more config

class QualityConfig(BaseModel):
    """Configuration for quality scoring."""
    points_sample_count: int = 20
    points_title: int = 15
    points_summary: int = 15
    # ... more config
```

**Impact**: Settings scattered throughout code, no single source of truth

---

### 2.5 Limited Test Coverage

**Current Tests**:
- `tests/unit/agents/test_search_agent.py`: Basic search tests
- `tests/unit/agents/test_data_agent.py`: Quality level tests
- **Missing**: Dedicated ranking/scoring unit tests

**Coverage Gaps**:
- ❌ No tests for `_calculate_relevance()` method
- ❌ No tests for `_calculate_quality_score()` method
- ❌ No parametrized tests for different weights
- ❌ No edge case testing (empty titles, no samples, etc.)

**Required Tests** (from Phase 0 plan):
- `tests/unit/lib/ranking/test_keyword_ranker.py`
- `tests/unit/lib/ranking/test_quality_scorer.py`
- `tests/integration/test_ranking_integration.py`
- `tests/benchmarks/test_ranking_performance.py`

---

## 3. Current Architecture Analysis

### 3.1 Agent Structure

```
Orchestrator
    ├── QueryAgent      (NLP, entity extraction)
    ├── SearchAgent     (GEO search, RANKING ← NEEDS REFACTOR)
    ├── DataAgent       (Quality assessment ← NEEDS REFACTOR)
    └── ReportAgent     (AI-powered reports)
```

**SearchAgent Responsibilities**:
- ✅ GEO API interaction
- ✅ Search query building
- ⚠️  **Relevance ranking** (should be extracted)
- ✅ Result filtering

**DataAgent Responsibilities**:
- ✅ Metadata enrichment
- ⚠️  **Quality scoring** (should be extracted)
- ✅ Validation
- ✅ Processing

---

### 3.2 Proposed New Structure

```
omics_oracle_v2/
├── lib/
│   ├── ranking/              ← NEW MODULE
│   │   ├── __init__.py
│   │   ├── keyword_ranker.py
│   │   ├── quality_scorer.py
│   │   ├── synonyms.py       (Phase 1)
│   │   ├── embeddings.py     (Phase 2)
│   │   └── semantic_ranker.py (Phase 2)
│   │
│   ├── ai/
│   ├── geo/
│   └── nlp/
│
├── core/
│   └── config.py             ← ADD RankingConfig, QualityConfig
│
└── agents/
    ├── search_agent.py       ← SIMPLIFIED (uses KeywordRanker)
    └── data_agent.py         ← SIMPLIFIED (uses QualityScorer)
```

**Benefits**:
- Clear separation of concerns
- Easier to test and maintain
- Ready for Phase 1 & 2 enhancements
- Configuration-driven behavior

---

## 4. Dependency Analysis

### 4.1 SearchAgent Dependencies

**Current**:
```python
from ..lib.geo import GEOClient
from ..lib.geo.models import GEOSeriesMetadata
from .models.search import SearchInput, SearchOutput, RankedDataset
```

**After Refactoring** (will need):
```python
from ..lib.geo import GEOClient
from ..lib.geo.models import GEOSeriesMetadata
from ..lib.ranking import KeywordRanker      # NEW
from .models.search import SearchInput, SearchOutput, RankedDataset
```

**Impact**: Minimal - clean import addition

---

### 4.2 DataAgent Dependencies

**Current**:
```python
from ..lib.geo import GEOClient
from ..lib.geo.models import GEOSeriesMetadata
from .models.data import DataInput, DataOutput, ProcessedDataset
```

**After Refactoring** (will need):
```python
from ..lib.geo import GEOClient
from ..lib.geo.models import GEOSeriesMetadata
from ..lib.ranking import QualityScorer      # NEW
from .models.data import DataInput, DataOutput, ProcessedDataset
```

**Impact**: Minimal - clean import addition

---

## 5. Configuration Extraction Plan

### 5.1 Ranking Configuration

**Extract From**: `search_agent.py` lines 334-365

**Create**: `omics_oracle_v2/core/config.py`

```python
class RankingConfig(BaseModel):
    """Configuration for relevance ranking algorithms."""

    model_config = ConfigDict(protected_namespaces=())

    # Keyword matching weights
    keyword_title_weight: float = Field(default=0.4, ge=0.0, le=1.0)
    keyword_summary_weight: float = Field(default=0.3, ge=0.0, le=1.0)
    keyword_organism_bonus: float = Field(default=0.15, ge=0.0, le=1.0)
    keyword_sample_count_bonus: float = Field(default=0.15, ge=0.0, le=1.0)

    # Sample count thresholds
    sample_count_large: int = Field(default=100, ge=1)
    sample_count_medium: int = Field(default=50, ge=1)
    sample_count_small: int = Field(default=10, ge=1)

    # Semantic search (Phase 2)
    use_semantic_ranking: bool = Field(default=False)
    semantic_weight: float = Field(default=0.6, ge=0.0, le=1.0)
    keyword_weight: float = Field(default=0.4, ge=0.0, le=1.0)
```

---

### 5.2 Quality Configuration

**Extract From**: `data_agent.py` lines 223-285

**Create**: `omics_oracle_v2/core/config.py`

```python
class QualityConfig(BaseModel):
    """Configuration for quality scoring algorithms."""

    model_config = ConfigDict(protected_namespaces=())

    # Point allocations (max 100)
    points_sample_count: int = Field(default=20, ge=0, le=100)
    points_title: int = Field(default=15, ge=0, le=100)
    points_summary: int = Field(default=15, ge=0, le=100)
    points_publications: int = Field(default=20, ge=0, le=100)
    points_sra_data: int = Field(default=10, ge=0, le=100)
    points_recency: int = Field(default=10, ge=0, le=100)
    points_metadata: int = Field(default=10, ge=0, le=100)

    # Sample count thresholds
    sample_count_excellent: int = Field(default=100, ge=1)
    sample_count_good: int = Field(default=50, ge=1)
    sample_count_adequate: int = Field(default=10, ge=1)

    # Text length thresholds
    title_length_descriptive: int = Field(default=50, ge=1)
    title_length_adequate: int = Field(default=20, ge=1)

    summary_length_comprehensive: int = Field(default=200, ge=1)
    summary_length_good: int = Field(default=100, ge=1)
    summary_length_minimal: int = Field(default=50, ge=1)

    # Recency thresholds (days)
    recency_recent: int = Field(default=365, ge=1)      # < 1 year
    recency_moderate: int = Field(default=1825, ge=1)   # < 5 years
    recency_acceptable: int = Field(default=3650, ge=1) # < 10 years
```

---

## 6. Refactoring Checklist

### Priority 1: Configuration (Step 2)
- [ ] Add `RankingConfig` to `core/config.py`
- [ ] Add `QualityConfig` to `core/config.py`
- [ ] Update `Settings` class to include new configs
- [ ] Add validation for config values
- [ ] Create config documentation

### Priority 2: Ranking Module (Step 3)
- [ ] Create `omics_oracle_v2/lib/ranking/` directory
- [ ] Create `keyword_ranker.py` with `KeywordRanker` class
- [ ] Create `quality_scorer.py` with `QualityScorer` class
- [ ] Create `__init__.py` with exports
- [ ] Add docstrings and type hints

### Priority 3: Agent Updates (Step 4)
- [ ] Update `SearchAgent` to use `KeywordRanker`
- [ ] Update `DataAgent` to use `QualityScorer`
- [ ] Remove old inline scoring code
- [ ] Update imports
- [ ] Verify functionality

### Priority 4: Testing (Step 5)
- [ ] Create `tests/unit/lib/ranking/test_keyword_ranker.py`
- [ ] Create `tests/unit/lib/ranking/test_quality_scorer.py`
- [ ] Create integration tests
- [ ] Create performance benchmarks
- [ ] Achieve ≥80% coverage

### Priority 5: Documentation (Step 6)
- [ ] Update architecture docs
- [ ] Create configuration guide
- [ ] Create migration guide
- [ ] Update API documentation
- [ ] Add code examples

### Priority 6: Validation (Step 7)
- [ ] Run all existing tests
- [ ] Run new tests
- [ ] Benchmark performance
- [ ] Verify no regressions
- [ ] Update changelog

---

## 7. Risk Assessment

### Low Risk ✅
- Configuration extraction (just moving values)
- Creating new ranking module (additive change)
- Adding tests (no impact on existing code)

### Medium Risk ⚠️
- Updating agent imports (but straightforward)
- Refactoring scoring methods (need careful testing)

### High Risk ❌
- None identified (good incremental approach)

### Mitigation Strategies
1. **Keep old code initially**: Comment out old methods but don't delete
2. **Comprehensive testing**: Test both old and new implementations side-by-side
3. **Gradual rollout**: Use feature flags for new rankers
4. **Performance monitoring**: Benchmark before/after

---

## 8. Estimated Effort

| Step | Task | Time | Difficulty |
|------|------|------|------------|
| 1 | Code Audit | 30 min | ✅ Easy (DONE!) |
| 2 | Config Classes | 1 hour | ✅ Easy |
| 3 | Ranking Module | 1.5 hours | ⚠️ Medium |
| 4 | Agent Updates | 1 hour | ⚠️ Medium |
| 5 | Testing | 1 hour | ⚠️ Medium |
| 6 | Documentation | 30 min | ✅ Easy |
| 7 | Validation | 30 min | ✅ Easy |
| **Total** | **Phase 0** | **6 hours** | **Medium** |

---

## 9. Success Criteria

### Must Have ✅
- [ ] All configuration extracted to config classes
- [ ] Separate `KeywordRanker` and `QualityScorer` classes created
- [ ] All existing tests pass
- [ ] New unit tests added (≥80% coverage)
- [ ] No performance regression (< 5% slowdown)
- [ ] Documentation updated

### Nice to Have 🎯
- [ ] Performance improvement (faster than current)
- [ ] >90% test coverage
- [ ] Benchmark suite for future comparisons
- [ ] Configuration validation with helpful error messages

### Must Not Have ❌
- [ ] No breaking changes to API
- [ ] No loss of functionality
- [ ] No significant performance degradation

---

## 10. Recommendations

### Immediate Actions (Next 30 minutes)
1. ✅ **Review this audit report**
2. **Proceed to Step 2**: Create configuration classes
3. **Set up test environment**: Ensure all tests are passing before changes

### Next Steps (After Phase 0)
1. **Phase 1**: Implement synonym mapping (2 hours)
   - 30-40% improvement with zero cost
   - Build on clean foundation from Phase 0

2. **Phase 2**: Implement semantic search (4 hours)
   - 2x improvement in relevance
   - Requires clean ranking module from Phase 0

3. **Phase 3**: Add LLM validation (3 hours)
   - Human-like judgment
   - Optional polish step

---

## 11. Notes

### Key Insights
- **Current system is functional** but not optimal
- **Architecture is good**, just needs better organization
- **No major rewrites needed**, mainly extraction and reorganization
- **Foundation is solid** for adding advanced features

### Potential Issues
- **Environment config**: Ensure `.env` has all needed variables
- **Test data**: May need sample GEO datasets for testing
- **API rate limits**: Be mindful when testing with NCBI

### Dependencies
- All required libraries already installed
- No new dependencies for Phase 0
- Phase 2 will require OpenAI (already configured)

---

## Appendix A: Code Snippets to Extract

### A.1 Relevance Scoring (search_agent.py:320-378)

```python
def _calculate_relevance(
    self, dataset: GEOSeriesMetadata, input_data: SearchInput
) -> tuple[float, List[str]]:
    """Calculate relevance score (0.0-1.0) based on search terms."""
    score = 0.0
    reasons = []
    search_terms_lower = {term.lower() for term in input_data.search_terms}

    # Title matches
    title_lower = (dataset.title or "").lower()
    title_matches = sum(1 for term in search_terms_lower if term in title_lower)
    if title_matches > 0:
        title_score = min(0.4, title_matches * 0.2)
        score += title_score
        reasons.append(f"Title matches {title_matches} search term(s)")

    # ... more code to extract ...
```

**Lines to Extract**: 320-378 (58 lines)

---

### A.2 Quality Scoring (data_agent.py:213-291)

```python
def _calculate_quality_score(
    self, metadata: GEOSeriesMetadata
) -> Tuple[float, List[str], List[str]]:
    """Calculate quality score (0.0-1.0) with issues and strengths."""
    score = 0.0
    issues = []
    strengths = []

    # Sample count scoring
    if metadata.sample_count:
        if metadata.sample_count >= 100:
            score += 20
            strengths.append(f"Large sample size: {metadata.sample_count} samples")
        # ... more code to extract ...
```

**Lines to Extract**: 213-291 (78 lines)

---

## Appendix B: File Locations

### Files to Modify
- `omics_oracle_v2/core/config.py` - Add configs
- `omics_oracle_v2/agents/search_agent.py` - Use KeywordRanker
- `omics_oracle_v2/agents/data_agent.py` - Use QualityScorer

### Files to Create
- `omics_oracle_v2/lib/ranking/__init__.py`
- `omics_oracle_v2/lib/ranking/keyword_ranker.py`
- `omics_oracle_v2/lib/ranking/quality_scorer.py`
- `tests/unit/lib/ranking/test_keyword_ranker.py`
- `tests/unit/lib/ranking/test_quality_scorer.py`
- `tests/integration/test_ranking_integration.py`
- `docs/configuration/RANKING_CONFIG.md`

---

**Audit Complete!** ✅

**Ready to proceed to Step 2: Create Configuration Classes**

---

*Generated: October 5, 2025*
*Phase: 0 (Codebase Consolidation)*
*Next: Step 2 - Configuration Classes*
