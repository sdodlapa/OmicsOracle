# Phase 0: Codebase Consolidation - Detailed Plan 🧹

## Overview

Before implementing semantic search, we must consolidate and clean up the codebase to ensure a solid foundation. This phase focuses on refactoring, configuration extraction, and establishing proper testing infrastructure.

---

## Step 1: Code Audit (30 minutes)

### 1.1 Analyze Current Structure

**Objective**: Understand what we have and what needs cleanup

**Commands to run**:
```bash
# Count lines of code
find omics_oracle_v2 -name "*.py" | xargs wc -l

# Find TODO/FIXME comments
grep -r "TODO\|FIXME\|HACK\|XXX" omics_oracle_v2/

# Find hardcoded values
grep -r "0\.[0-9]" omics_oracle_v2/agents/*.py

# Check for duplicated code
# (manually review similar function names)
```

**Create audit report**:
```markdown
# CODE_AUDIT_REPORT.md

## Statistics
- Total lines of code: X
- Number of agents: 5
- Number of models: Y
- Test coverage: Z%

## Issues Found
1. Hardcoded scoring weights in search_agent.py lines 332-360
2. Hardcoded quality thresholds in data_agent.py lines 220-310
3. Duplicate date parsing in 3 places
4. Magic numbers throughout
5. Missing error handling in X places

## Recommendations
1. Extract all scoring weights to config
2. Consolidate date parsing
3. Add proper error handling
4. Create separate ranking module
```

**Deliverable**: `CODE_AUDIT_REPORT.md`

---

## Step 2: Create Configuration Classes (1 hour)

### 2.1 Define Ranking Configuration

**File**: `omics_oracle_v2/core/config.py`

**Add these classes**:

```python
class RankingConfig(BaseModel):
    """Configuration for relevance ranking algorithms."""
    
    model_config = ConfigDict(protected_namespaces=())
    
    # === Keyword Ranking Weights ===
    keyword_title_weight: float = Field(
        default=0.4,
        ge=0.0,
        le=1.0,
        description="Weight for title matches in keyword ranking"
    )
    keyword_summary_weight: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Weight for summary matches in keyword ranking"
    )
    keyword_organism_bonus: float = Field(
        default=0.15,
        ge=0.0,
        le=1.0,
        description="Bonus for organism matches"
    )
    keyword_sample_count_bonus: float = Field(
        default=0.15,
        ge=0.0,
        le=1.0,
        description="Bonus for large sample counts"
    )
    
    # === Sample Count Thresholds ===
    sample_count_large: int = Field(
        default=100,
        ge=1,
        description="Sample count threshold for 'large' datasets"
    )
    sample_count_good: int = Field(
        default=50,
        ge=1,
        description="Sample count threshold for 'good' datasets"
    )
    sample_count_adequate: int = Field(
        default=10,
        ge=1,
        description="Sample count threshold for 'adequate' datasets"
    )
    
    # === Semantic Ranking (Phase 2) ===
    use_semantic_ranking: bool = Field(
        default=False,  # Disabled until Phase 2
        description="Enable semantic similarity ranking with embeddings"
    )
    semantic_weight: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Weight for semantic similarity score in hybrid ranking"
    )
    keyword_weight: float = Field(
        default=0.4,
        ge=0.0,
        le=1.0,
        description="Weight for keyword score in hybrid ranking"
    )
    semantic_agreement_boost: float = Field(
        default=1.1,
        ge=1.0,
        le=2.0,
        description="Multiplier when semantic and keyword scores agree"
    )
    
    # === LLM Validation (Phase 3) ===
    enable_llm_validation: bool = Field(
        default=False,  # Disabled until Phase 3
        description="Enable LLM-based validation of top results"
    )
    llm_validation_top_n: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Number of top results to validate with LLM"
    )
    llm_validation_weight: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Weight for LLM score when blending with algorithmic score"
    )
    
    # === Synonym Expansion (Phase 1) ===
    use_synonym_expansion: bool = Field(
        default=False,  # Will enable in Phase 1
        description="Expand search terms with biomedical synonyms"
    )
    
    # === Caching ===
    cache_embeddings: bool = Field(
        default=True,
        description="Cache embeddings to disk to reduce API calls"
    )
    embedding_cache_dir: str = Field(
        default=".cache/embeddings",
        description="Directory for embedding cache"
    )


class QualityConfig(BaseModel):
    """Configuration for quality scoring algorithms."""
    
    model_config = ConfigDict(protected_namespaces=())
    
    # === Point Allocations (max 100 points) ===
    points_sample_count: int = Field(
        default=20,
        ge=0,
        le=100,
        description="Maximum points for sample count"
    )
    points_title: int = Field(
        default=15,
        ge=0,
        le=100,
        description="Maximum points for title quality"
    )
    points_summary: int = Field(
        default=15,
        ge=0,
        le=100,
        description="Maximum points for summary quality"
    )
    points_publication: int = Field(
        default=20,
        ge=0,
        le=100,
        description="Maximum points for having publications"
    )
    points_sra_data: int = Field(
        default=10,
        ge=0,
        le=100,
        description="Maximum points for SRA data availability"
    )
    points_recency: int = Field(
        default=10,
        ge=0,
        le=100,
        description="Maximum points for dataset recency"
    )
    points_metadata: int = Field(
        default=10,
        ge=0,
        le=100,
        description="Maximum points for metadata completeness"
    )
    
    # === Sample Count Thresholds ===
    sample_count_excellent: int = Field(default=100, ge=1)
    sample_count_good: int = Field(default=50, ge=1)
    sample_count_adequate: int = Field(default=10, ge=1)
    
    # === Text Length Thresholds ===
    title_length_descriptive: int = Field(default=50, ge=1)
    title_length_adequate: int = Field(default=20, ge=1)
    title_length_minimal: int = Field(default=10, ge=1)
    
    summary_length_comprehensive: int = Field(default=200, ge=1)
    summary_length_good: int = Field(default=100, ge=1)
    summary_length_minimal: int = Field(default=50, ge=1)
    
    # === Recency Thresholds (days) ===
    recency_recent: int = Field(default=365, ge=1, description="< 1 year")
    recency_moderate: int = Field(default=1825, ge=1, description="< 5 years")
    recency_acceptable: int = Field(default=3650, ge=1, description="< 10 years")
    
    # === Metadata Completeness ===
    metadata_weight_required: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Weight for required fields in completeness"
    )
    metadata_weight_optional: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Weight for optional fields in completeness"
    )


# Add to main Settings class
class Settings(BaseSettings):
    """Application settings."""
    
    model_config = SettingsConfig(
        env_prefix="OMICS_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # ... existing fields ...
    
    # New configuration sections
    ranking: RankingConfig = Field(default_factory=RankingConfig)
    quality: QualityConfig = Field(default_factory=QualityConfig)
```

### 2.2 Update Configuration Documentation

**File**: `docs/configuration/RANKING_CONFIG.md`

```markdown
# Ranking Configuration

## Overview

The ranking system uses configurable weights and thresholds to score dataset relevance and quality.

## Ranking Configuration

### Keyword Ranking

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| `keyword_title_weight` | 0.4 | 0.0-1.0 | Weight for title matches |
| `keyword_summary_weight` | 0.3 | 0.0-1.0 | Weight for summary matches |
| `keyword_organism_bonus` | 0.15 | 0.0-1.0 | Bonus for organism match |
| `keyword_sample_count_bonus` | 0.15 | 0.0-1.0 | Bonus for large samples |

### Sample Count Thresholds

| Parameter | Default | Description |
|-----------|---------|-------------|
| `sample_count_large` | 100 | Threshold for large datasets |
| `sample_count_good` | 50 | Threshold for good sample size |
| `sample_count_adequate` | 10 | Threshold for adequate samples |

### Semantic Ranking (Phase 2)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `use_semantic_ranking` | false | Enable semantic similarity |
| `semantic_weight` | 0.6 | Weight for semantic score |
| `keyword_weight` | 0.4 | Weight for keyword score |

## Quality Configuration

### Point Allocations

Total: 100 points maximum

| Component | Points | Description |
|-----------|--------|-------------|
| Sample count | 20 | Based on number of samples |
| Title quality | 15 | Based on title length/descriptiveness |
| Summary quality | 15 | Based on summary completeness |
| Publications | 20 | Has PubMed publications |
| SRA data | 10 | Has raw sequencing data |
| Recency | 10 | How recent the dataset is |
| Metadata | 10 | Metadata completeness |

## Environment Variables

Configure via environment variables with `OMICS_` prefix:

```bash
# Ranking
OMICS_RANKING__USE_SEMANTIC_RANKING=true
OMICS_RANKING__SEMANTIC_WEIGHT=0.6

# Quality
OMICS_QUALITY__POINTS_SAMPLE_COUNT=25
OMICS_QUALITY__SAMPLE_COUNT_EXCELLENT=100
```

## Configuration File

Or via YAML configuration file:

```yaml
# config/production.yml
ranking:
  use_semantic_ranking: true
  semantic_weight: 0.6
  keyword_weight: 0.4
  
quality:
  points_sample_count: 20
  sample_count_excellent: 100
```
```

**Deliverables**:
- [ ] `RankingConfig` class added
- [ ] `QualityConfig` class added
- [ ] Documentation created
- [ ] Environment variable examples

---

## Step 3: Extract Ranking Logic to Module (1.5 hours)

### 3.1 Create Ranking Module Structure

**Create directory**:
```bash
mkdir -p omics_oracle_v2/lib/ranking
touch omics_oracle_v2/lib/ranking/__init__.py
```

### 3.2 Create KeywordRanker Class

**File**: `omics_oracle_v2/lib/ranking/keyword_ranker.py`

```python
"""
Keyword-based relevance ranking.

This is the current/baseline ranking algorithm that uses exact
keyword matching to score dataset relevance.
"""

import logging
from typing import List, Tuple, Set

from ...core.config import RankingConfig

logger = logging.getLogger(__name__)


class KeywordRanker:
    """
    Keyword-based dataset relevance ranking.
    
    Scores datasets based on exact keyword matches in title,
    summary, and other metadata fields.
    """
    
    def __init__(self, config: RankingConfig):
        """
        Initialize keyword ranker.
        
        Args:
            config: Ranking configuration
        """
        self.config = config
    
    def calculate_relevance(
        self,
        title: str,
        summary: str,
        search_terms: List[str],
        organism: str = None,
        organism_filter: str = None,
        sample_count: int = None
    ) -> Tuple[float, List[str]]:
        """
        Calculate keyword-based relevance score.
        
        Args:
            title: Dataset title
            summary: Dataset summary
            search_terms: List of search terms to match
            organism: Dataset organism
            organism_filter: Organism filter from query
            sample_count: Number of samples
            
        Returns:
            Tuple of (score, match_reasons)
        """
        score = 0.0
        reasons = []
        
        # Normalize search terms
        search_terms_lower = {term.lower() for term in search_terms}
        
        # 1. Title matches (highest weight)
        title_score, title_reasons = self._score_title_matches(
            title, search_terms_lower
        )
        score += title_score
        reasons.extend(title_reasons)
        
        # 2. Summary matches (medium weight)
        summary_score, summary_reasons = self._score_summary_matches(
            summary, search_terms_lower
        )
        score += summary_score
        reasons.extend(summary_reasons)
        
        # 3. Organism match (bonus)
        if organism_filter and organism:
            organism_score, organism_reason = self._score_organism_match(
                organism, organism_filter
            )
            score += organism_score
            if organism_reason:
                reasons.append(organism_reason)
        
        # 4. Sample count (bonus)
        if sample_count:
            sample_score, sample_reason = self._score_sample_count(
                sample_count
            )
            score += sample_score
            if sample_reason:
                reasons.append(sample_reason)
        
        # Normalize to 0.0-1.0
        score = min(1.0, score)
        
        # Ensure minimum score if any match exists
        if not reasons:
            reasons.append("General database match")
            score = 0.1
        
        return score, reasons
    
    def _score_title_matches(
        self, title: str, search_terms: Set[str]
    ) -> Tuple[float, List[str]]:
        """Score title keyword matches."""
        if not title:
            return 0.0, []
        
        title_lower = title.lower()
        matches = sum(1 for term in search_terms if term in title_lower)
        
        if matches == 0:
            return 0.0, []
        
        # Score with diminishing returns
        score = min(
            self.config.keyword_title_weight,
            matches * (self.config.keyword_title_weight / 2)
        )
        
        reason = f"Title matches {matches} search term(s)"
        return score, [reason]
    
    def _score_summary_matches(
        self, summary: str, search_terms: Set[str]
    ) -> Tuple[float, List[str]]:
        """Score summary keyword matches."""
        if not summary:
            return 0.0, []
        
        summary_lower = summary.lower()
        matches = sum(1 for term in search_terms if term in summary_lower)
        
        if matches == 0:
            return 0.0, []
        
        # Score with diminishing returns
        score = min(
            self.config.keyword_summary_weight,
            matches * (self.config.keyword_summary_weight / 2)
        )
        
        reason = f"Summary matches {matches} search term(s)"
        return score, [reason]
    
    def _score_organism_match(
        self, organism: str, organism_filter: str
    ) -> Tuple[float, str]:
        """Score organism match."""
        if not organism or not organism_filter:
            return 0.0, None
        
        if organism_filter.lower() in organism.lower():
            return (
                self.config.keyword_organism_bonus,
                f"Organism matches: {organism}"
            )
        
        return 0.0, None
    
    def _score_sample_count(
        self, sample_count: int
    ) -> Tuple[float, str]:
        """Score based on sample count."""
        if sample_count >= self.config.sample_count_large:
            return (
                self.config.keyword_sample_count_bonus,
                f"Large sample size: {sample_count} samples"
            )
        elif sample_count >= self.config.sample_count_good:
            return (
                self.config.keyword_sample_count_bonus * 0.67,
                f"Good sample size: {sample_count} samples"
            )
        elif sample_count >= self.config.sample_count_adequate:
            return (
                self.config.keyword_sample_count_bonus * 0.33,
                f"Adequate sample size: {sample_count} samples"
            )
        
        return 0.0, None
```

### 3.3 Create QualityScorer Class

**File**: `omics_oracle_v2/lib/ranking/quality_scorer.py`

```python
"""
Dataset quality scoring.

Assesses dataset quality based on metadata completeness,
sample count, publications, and other quality indicators.
"""

import logging
from typing import List, Tuple

from ...core.config import QualityConfig
from ...lib.geo.models import GEOSeriesMetadata

logger = logging.getLogger(__name__)


class QualityScorer:
    """
    Dataset quality assessment.
    
    Scores datasets on multiple quality dimensions including
    sample size, metadata completeness, publications, and recency.
    """
    
    def __init__(self, config: QualityConfig):
        """
        Initialize quality scorer.
        
        Args:
            config: Quality configuration
        """
        self.config = config
    
    def calculate_quality(
        self, metadata: GEOSeriesMetadata
    ) -> Tuple[float, List[str], List[str]]:
        """
        Calculate overall quality score.
        
        Args:
            metadata: GEO dataset metadata
            
        Returns:
            Tuple of (quality_score, issues, strengths)
        """
        score = 0.0
        issues = []
        strengths = []
        
        # 1. Sample count
        sample_score, sample_msg, is_issue = self._score_sample_count(
            metadata.sample_count
        )
        score += sample_score
        if is_issue:
            issues.append(sample_msg)
        else:
            strengths.append(sample_msg)
        
        # 2. Title quality
        title_score, title_msg, is_issue = self._score_title_quality(
            metadata.title
        )
        score += title_score
        if is_issue and title_msg:
            issues.append(title_msg)
        elif title_msg:
            strengths.append(title_msg)
        
        # 3. Summary quality
        summary_score, summary_msg, is_issue = self._score_summary_quality(
            metadata.summary
        )
        score += summary_score
        if is_issue and summary_msg:
            issues.append(summary_msg)
        elif summary_msg:
            strengths.append(summary_msg)
        
        # 4. Publications
        pub_score, pub_msg, is_issue = self._score_publications(
            metadata.pubmed_ids
        )
        score += pub_score
        if is_issue:
            issues.append(pub_msg)
        else:
            strengths.append(pub_msg)
        
        # 5. SRA data
        sra_score, sra_msg, is_issue = self._score_sra_data(
            metadata.has_sra_data()
        )
        score += sra_score
        if is_issue:
            issues.append(sra_msg)
        elif sra_msg:
            strengths.append(sra_msg)
        
        # 6. Recency
        recency_score, recency_msg, is_issue = self._score_recency(
            metadata.get_age_days()
        )
        score += recency_score
        if is_issue and recency_msg:
            issues.append(recency_msg)
        elif recency_msg:
            strengths.append(recency_msg)
        
        # 7. Metadata completeness
        completeness_score, completeness_msg, is_issue = self._score_metadata_completeness(
            metadata
        )
        score += completeness_score
        if is_issue:
            issues.append(completeness_msg)
        elif completeness_msg:
            strengths.append(completeness_msg)
        
        # Normalize to 0.0-1.0
        quality_score = min(1.0, score / 100.0)
        
        return quality_score, issues, strengths
    
    def _score_sample_count(
        self, sample_count: int
    ) -> Tuple[float, str, bool]:
        """Score sample count (0-20 points)."""
        max_points = self.config.points_sample_count
        
        if not sample_count:
            return 0, "Missing sample count information", True
        
        if sample_count >= self.config.sample_count_excellent:
            return (
                max_points,
                f"Large sample size: {sample_count} samples",
                False
            )
        elif sample_count >= self.config.sample_count_good:
            return (
                max_points * 0.75,
                f"Good sample size: {sample_count} samples",
                False
            )
        elif sample_count >= self.config.sample_count_adequate:
            return (
                max_points * 0.5,
                f"Adequate sample size: {sample_count} samples",
                False
            )
        else:
            return (
                max_points * 0.25,
                f"Small sample size: {sample_count} samples",
                True
            )
    
    # ... Additional scoring methods following same pattern ...
    # (Implement _score_title_quality, _score_summary_quality, etc.)
```

### 3.4 Update Module __init__.py

**File**: `omics_oracle_v2/lib/ranking/__init__.py`

```python
"""
Ranking module for dataset relevance and quality scoring.

Provides multiple ranking algorithms:
- KeywordRanker: Traditional keyword matching
- SemanticRanker: Embedding-based semantic similarity (Phase 2)
- LLMValidator: LLM-based validation (Phase 3)
"""

from .keyword_ranker import KeywordRanker
from .quality_scorer import QualityScorer

__all__ = [
    "KeywordRanker",
    "QualityScorer",
]
```

**Deliverables**:
- [ ] `omics_oracle_v2/lib/ranking/` module created
- [ ] `KeywordRanker` class implemented
- [ ] `QualityScorer` class implemented
- [ ] Module exports defined

---

## Step 4: Update Agents to Use New Classes (1 hour)

### 4.1 Update SearchAgent

**File**: `omics_oracle_v2/agents/search_agent.py`

```python
from ..lib.ranking.keyword_ranker import KeywordRanker

class SearchAgent(Agent[SearchInput, SearchOutput]):
    
    def __init__(self, settings: Settings):
        super().__init__(settings)
        self._geo_client: GEOClient = None
        self.keyword_ranker = KeywordRanker(settings.ranking)  # NEW
    
    def _calculate_relevance(
        self, dataset: GEOSeriesMetadata, input_data: SearchInput
    ) -> tuple[float, List[str]]:
        """
        Calculate relevance score using KeywordRanker.
        
        Args:
            dataset: GEO dataset to score
            input_data: Search input with terms
            
        Returns:
            Tuple of (score, match_reasons)
        """
        return self.keyword_ranker.calculate_relevance(
            title=dataset.title or "",
            summary=dataset.summary or "",
            search_terms=input_data.search_terms,
            organism=dataset.organism,
            organism_filter=input_data.organism,
            sample_count=dataset.sample_count
        )
```

### 4.2 Update DataAgent

**File**: `omics_oracle_v2/agents/data_agent.py`

```python
from ..lib.ranking.quality_scorer import QualityScorer

class DataAgent(Agent[DataInput, DataOutput]):
    
    def __init__(self, settings: Settings):
        super().__init__(settings)
        self.quality_scorer = QualityScorer(settings.quality)  # NEW
    
    def _calculate_quality_score(
        self, metadata: GEOSeriesMetadata
    ) -> Tuple[float, List[str], List[str]]:
        """
        Calculate quality score using QualityScorer.
        
        Args:
            metadata: GEOSeriesMetadata
            
        Returns:
            Tuple of (quality_score, issues, strengths)
        """
        return self.quality_scorer.calculate_quality(metadata)
```

**Deliverables**:
- [ ] SearchAgent updated
- [ ] DataAgent updated
- [ ] Old code removed
- [ ] All tests passing

---

## Step 5: Create Unit Tests (1 hour)

### 5.1 Test KeywordRanker

**File**: `tests/unit/lib/ranking/test_keyword_ranker.py`

```python
import pytest
from omics_oracle_v2.lib.ranking.keyword_ranker import KeywordRanker
from omics_oracle_v2.core.config import RankingConfig


class TestKeywordRanker:
    
    @pytest.fixture
    def ranker(self):
        config = RankingConfig()
        return KeywordRanker(config)
    
    def test_title_match(self, ranker):
        """Test title keyword matching."""
        score, reasons = ranker.calculate_relevance(
            title="DNA methylation profiling",
            summary="",
            search_terms=["dna methylation"]
        )
        
        assert score > 0, "Should have non-zero score for title match"
        assert any("title" in r.lower() for r in reasons), "Should mention title in reasons"
    
    def test_summary_match(self, ranker):
        """Test summary keyword matching."""
        score, reasons = ranker.calculate_relevance(
            title="",
            summary="This study uses chromatin accessibility profiling",
            search_terms=["chromatin accessibility"]
        )
        
        assert score > 0, "Should have non-zero score for summary match"
        assert any("summary" in r.lower() for r in reasons), "Should mention summary in reasons"
    
    def test_multiple_matches(self, ranker):
        """Test multiple keyword matches."""
        score, reasons = ranker.calculate_relevance(
            title="Joint profiling of DNA methylation",
            summary="Chromatin accessibility was measured simultaneously",
            search_terms=["dna methylation", "chromatin accessibility", "joint profiling"]
        )
        
        assert score > 0.5, "Multiple matches should give higher score"
        assert len(reasons) > 1, "Should have multiple match reasons"
    
    def test_no_match(self, ranker):
        """Test no keyword matches."""
        score, reasons = ranker.calculate_relevance(
            title="RNA sequencing study",
            summary="Gene expression profiling",
            search_terms=["dna methylation"]
        )
        
        assert score < 0.2, "No matches should give low score"
    
    def test_sample_count_bonus(self, ranker):
        """Test sample count bonus."""
        score_small, _ = ranker.calculate_relevance(
            title="Study",
            summary="",
            search_terms=["study"],
            sample_count=5
        )
        
        score_large, reasons_large = ranker.calculate_relevance(
            title="Study",
            summary="",
            search_terms=["study"],
            sample_count=150
        )
        
        assert score_large > score_small, "Larger sample count should increase score"
        assert any("large sample" in r.lower() for r in reasons_large)
```

### 5.2 Test QualityScorer

**File**: `tests/unit/lib/ranking/test_quality_scorer.py`

```python
import pytest
from omics_oracle_v2.lib.ranking.quality_scorer import QualityScorer
from omics_oracle_v2.core.config import QualityConfig
from omics_oracle_v2.lib.geo.models import GEOSeriesMetadata


class TestQualityScorer:
    
    @pytest.fixture
    def scorer(self):
        config = QualityConfig()
        return QualityScorer(config)
    
    def test_high_quality_dataset(self, scorer):
        """Test scoring of high-quality dataset."""
        metadata = GEOSeriesMetadata(
            geo_id="GSE123456",
            title="Comprehensive study of DNA methylation in cancer with 150 samples",
            summary="This is a detailed summary with comprehensive methodology and results...",
            organism="Homo sapiens",
            sample_count=150,
            pubmed_ids=["12345678"]
        )
        
        score, issues, strengths = scorer.calculate_quality(metadata)
        
        assert score > 0.7, "High quality dataset should score > 0.7"
        assert len(strengths) > len(issues), "Should have more strengths than issues"
        assert any("large sample" in s.lower() for s in strengths)
    
    def test_low_quality_dataset(self, scorer):
        """Test scoring of low-quality dataset."""
        metadata = GEOSeriesMetadata(
            geo_id="GSE999999",
            title="Study",
            summary="Short summary",
            organism="Unknown",
            sample_count=3,
            pubmed_ids=[]
        )
        
        score, issues, strengths = scorer.calculate_quality(metadata)
        
        assert score < 0.5, "Low quality dataset should score < 0.5"
        assert len(issues) > len(strengths), "Should have more issues than strengths"
```

### 5.3 Integration Tests

**File**: `tests/integration/test_ranking_integration.py`

```python
"""Test full ranking workflow."""

import pytest
from omics_oracle_v2.agents.search_agent import SearchAgent
from omics_oracle_v2.agents.data_agent import DataAgent
from omics_oracle_v2.core.config import Settings


class TestRankingIntegration:
    
    @pytest.fixture
    def settings(self):
        return Settings()
    
    @pytest.fixture
    def search_agent(self, settings):
        return SearchAgent(settings)
    
    @pytest.fixture
    def data_agent(self, settings):
        return DataAgent(settings)
    
    def test_search_and_quality_pipeline(self, search_agent, data_agent):
        """Test complete search → quality pipeline."""
        # This will be a more complex test once we have test data
        pass
```

**Deliverables**:
- [ ] KeywordRanker tests created
- [ ] QualityScorer tests created
- [ ] Integration tests created
- [ ] All tests passing
- [ ] Coverage ≥ 80%

---

## Step 6: Update Documentation (30 minutes)

### 6.1 Update Architecture Documentation

**File**: `docs/ARCHITECTURE.md`

Add section:
```markdown
## Ranking System

### Overview

The ranking system consists of two main components:
1. **Relevance Ranking**: Scores how relevant a dataset is to the user query
2. **Quality Scoring**: Assesses the quality of dataset metadata

### Components

#### KeywordRanker
- Location: `omics_oracle_v2/lib/ranking/keyword_ranker.py`
- Responsibility: Keyword-based relevance scoring
- Configuration: `Settings.ranking`

#### QualityScorer  
- Location: `omics_oracle_v2/lib/ranking/quality_scorer.py`
- Responsibility: Dataset quality assessment
- Configuration: `Settings.quality`

### Extensibility

The ranking system is designed to be extensible:
- Phase 1: Add synonym expansion
- Phase 2: Add semantic similarity
- Phase 3: Add LLM validation

Each phase builds on the previous without breaking existing functionality.
```

### 6.2 Create Migration Guide

**File**: `docs/MIGRATION_GUIDE.md`

```markdown
# Migration Guide: Refactored Ranking System

## What Changed

1. Scoring weights moved from hardcoded values to configuration
2. Ranking logic extracted to separate classes
3. Configuration now in `Settings.ranking` and `Settings.quality`

## Updating Your Code

### Before
```python
# Hardcoded in search_agent.py
title_score = min(0.4, title_matches * 0.2)
```

### After
```python
# Configured via Settings
self.keyword_ranker = KeywordRanker(settings.ranking)
score, reasons = self.keyword_ranker.calculate_relevance(...)
```

## Configuration

### Environment Variables
```bash
OMICS_RANKING__KEYWORD_TITLE_WEIGHT=0.5
OMICS_QUALITY__POINTS_SAMPLE_COUNT=25
```

### Configuration File
```yaml
ranking:
  keyword_title_weight: 0.5
quality:
  points_sample_count: 25
```
```

**Deliverables**:
- [ ] Architecture documentation updated
- [ ] Migration guide created
- [ ] API documentation generated
- [ ] README updated

---

## Step 7: Cleanup & Validation (30 minutes)

### 7.1 Remove Dead Code

**Tasks**:
1. Remove old commented-out code
2. Remove unused imports
3. Remove debug print statements
4. Consolidate duplicate functions

**Commands**:
```bash
# Find unused imports
pylint --disable=all --enable=unused-import omics_oracle_v2/

# Find TODO comments
grep -r "TODO\|FIXME" omics_oracle_v2/

# Check for print statements (should use logger)
grep -r "print(" omics_oracle_v2/ --include="*.py"
```

### 7.2 Run Full Test Suite

```bash
# Run all tests
pytest tests/ -v --cov=omics_oracle_v2 --cov-report=html

# Check coverage
open htmlcov/index.html

# Run linting
pylint omics_oracle_v2/
black omics_oracle_v2/ --check
mypy omics_oracle_v2/
```

### 7.3 Performance Benchmark

**File**: `tests/benchmarks/test_ranking_performance.py`

```python
"""Benchmark ranking performance."""

import pytest
import time
from omics_oracle_v2.lib.ranking import KeywordRanker, QualityScorer
from omics_oracle_v2.core.config import Settings


def test_keyword_ranking_performance():
    """Benchmark keyword ranking speed."""
    settings = Settings()
    ranker = KeywordRanker(settings.ranking)
    
    # Simulate 100 datasets
    start = time.time()
    for i in range(100):
        ranker.calculate_relevance(
            title=f"Dataset {i} about DNA methylation",
            summary=f"Summary for dataset {i}",
            search_terms=["dna methylation", "cancer"]
        )
    elapsed = time.time() - start
    
    print(f"Ranked 100 datasets in {elapsed:.2f}s ({elapsed/100*1000:.1f}ms per dataset)")
    assert elapsed < 1.0, "Should rank 100 datasets in < 1 second"
```

**Deliverables**:
- [ ] Dead code removed
- [ ] All tests passing
- [ ] Coverage ≥ 80%
- [ ] Performance benchmarked
- [ ] No linting errors

---

## Checklist

### Configuration
- [ ] RankingConfig class added
- [ ] QualityConfig class added
- [ ] Settings updated
- [ ] Documentation created

### Refactoring
- [ ] KeywordRanker class created
- [ ] QualityScorer class created
- [ ] SearchAgent updated
- [ ] DataAgent updated
- [ ] Old code removed

### Testing
- [ ] KeywordRanker tests
- [ ] QualityScorer tests
- [ ] Integration tests
- [ ] Coverage ≥ 80%
- [ ] Performance benchmarks

### Documentation
- [ ] Architecture updated
- [ ] Migration guide created
- [ ] Configuration guide created
- [ ] API docs generated

### Quality
- [ ] No linting errors
- [ ] No dead code
- [ ] All TODOs addressed
- [ ] Performance acceptable

---

## Timeline

| Task | Duration | Dependencies |
|------|----------|--------------|
| 1. Code Audit | 30 min | None |
| 2. Configuration | 1 hour | Task 1 |
| 3. Extract Ranking | 1.5 hours | Task 2 |
| 4. Update Agents | 1 hour | Task 3 |
| 5. Unit Tests | 1 hour | Task 4 |
| 6. Documentation | 30 min | Task 5 |
| 7. Cleanup | 30 min | Task 6 |

**Total: ~6 hours**

---

## Success Criteria

- [ ] All hardcoded values moved to configuration
- [ ] Ranking logic in separate reusable classes
- [ ] Test coverage ≥ 80%
- [ ] All existing functionality preserved
- [ ] Performance not degraded
- [ ] Documentation complete
- [ ] Ready for Phase 1 (Synonyms)

---

**Once Phase 0 is complete, we can proceed to Phase 1 (Synonym Mapping) with confidence!** 🚀
