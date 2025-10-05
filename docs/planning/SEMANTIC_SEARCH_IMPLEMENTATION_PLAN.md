# Semantic Search Implementation Plan 🚀

## Overview

This document outlines a phased approach to implement semantic search and enhanced relevance ranking in OmicsOracle, with codebase consolidation as Phase 0.

---

## Phase 0: Codebase Consolidation & Cleanup (FIRST!)

### Duration: 2-3 hours
### Priority: CRITICAL - Must complete before new features

### 0.1 Code Audit & Documentation

**Objective**: Understand current state and identify cleanup needs

**Tasks**:
1. **Audit search_agent.py**
   - Review current ranking logic
   - Identify hardcoded values
   - Document assumptions
   - Check for dead code

2. **Audit data_agent.py**
   - Review quality scoring logic
   - Check for duplicated scoring logic
   - Document quality metrics

3. **Audit orchestrator.py**
   - Review workflow stages
   - Check error handling
   - Verify all agent integrations

**Deliverables**:
- [ ] Code audit report
- [ ] List of refactoring needs
- [ ] Updated architecture diagram

### 0.2 Configuration Consolidation

**Objective**: Move hardcoded values to configuration

**Current Issues**:
```python
# search_agent.py - HARDCODED!
title_score = min(0.4, title_matches * 0.2)  # Magic numbers
summary_score = min(0.3, summary_matches * 0.15)

# data_agent.py - HARDCODED!
if metadata.sample_count >= 100:
    score += 20  # Magic number
```

**Tasks**:
1. Create `RankingConfig` in config system
2. Extract all scoring weights to config
3. Create `QualityConfig` for quality scoring
4. Add validation for config values

**Deliverables**:
```python
# omics_oracle_v2/core/config.py
class RankingConfig(BaseModel):
    """Configuration for relevance ranking."""
    
    # Keyword matching weights
    title_match_weight: float = Field(default=0.4, ge=0.0, le=1.0)
    summary_match_weight: float = Field(default=0.3, ge=0.0, le=1.0)
    organism_match_weight: float = Field(default=0.15, ge=0.0, le=1.0)
    sample_count_weight: float = Field(default=0.15, ge=0.0, le=1.0)
    
    # Semantic search weights (to be added)
    semantic_weight: float = Field(default=0.6, ge=0.0, le=1.0)
    keyword_weight: float = Field(default=0.4, ge=0.0, le=1.0)
    
    # Quality score blending
    use_semantic_ranking: bool = Field(default=True)
    enable_llm_validation: bool = Field(default=False)
    llm_validation_top_n: int = Field(default=10, ge=1, le=50)

class QualityConfig(BaseModel):
    """Configuration for quality scoring."""
    
    sample_count_max_points: int = Field(default=20, ge=0, le=100)
    title_quality_max_points: int = Field(default=15, ge=0, le=100)
    summary_quality_max_points: int = Field(default=15, ge=0, le=100)
    publication_max_points: int = Field(default=20, ge=0, le=100)
    sra_data_max_points: int = Field(default=10, ge=0, le=100)
    recency_max_points: int = Field(default=10, ge=0, le=100)
    metadata_max_points: int = Field(default=10, ge=0, le=100)
```

### 0.3 Code Refactoring

**Objective**: Clean up and modularize existing code

**Tasks**:

1. **Extract Scoring Logic to Separate Classes**
```python
# NEW: omics_oracle_v2/lib/ranking/keyword_ranker.py
class KeywordRanker:
    """Pure keyword-based ranking (current implementation)."""
    
    def calculate_relevance(self, dataset, search_terms) -> Tuple[float, List[str]]:
        """Calculate keyword-based relevance."""
        pass

# NEW: omics_oracle_v2/lib/ranking/quality_scorer.py
class QualityScorer:
    """Dataset quality assessment."""
    
    def calculate_quality(self, metadata) -> Tuple[float, List[str], List[str]]:
        """Calculate quality score with issues and strengths."""
        pass
```

2. **Remove Code Duplication**
   - Consolidate date parsing logic
   - Unify metadata extraction
   - Share validation functions

3. **Improve Error Handling**
   - Add proper exception types
   - Add retry logic for API calls
   - Add fallback mechanisms

**Deliverables**:
- [ ] `omics_oracle_v2/lib/ranking/` module created
- [ ] `KeywordRanker` class extracted
- [ ] `QualityScorer` class extracted
- [ ] Unit tests for refactored code
- [ ] All existing tests still pass

### 0.4 Testing Infrastructure

**Objective**: Ensure we can safely add new features

**Tasks**:
1. Add unit tests for search_agent scoring
2. Add unit tests for data_agent quality
3. Create integration test for full workflow
4. Add benchmark tests for performance

**Deliverables**:
- [ ] Test coverage ≥ 80% for agents
- [ ] Benchmark baseline established
- [ ] CI/CD tests passing

### 0.5 Documentation Update

**Objective**: Document current system before changes

**Tasks**:
1. Document current ranking algorithm
2. Document quality scoring algorithm
3. Create API documentation
4. Update architecture diagrams

**Deliverables**:
- [ ] `docs/ranking/CURRENT_SYSTEM.md`
- [ ] `docs/ranking/QUALITY_SCORING.md`
- [ ] Updated `ARCHITECTURE.md`

---

## Phase 1: Synonym Mapping (Quick Win!)

### Duration: 1-2 hours
### Priority: HIGH - Easy wins, no external dependencies

### 1.1 Create Synonym Database

**Objective**: Build comprehensive biomedical technique synonym mappings

**Implementation**:
```python
# NEW: omics_oracle_v2/lib/ranking/synonyms.py

from typing import Dict, List, Set

class BiomedicalSynonyms:
    """
    Biomedical technique synonym database.
    
    Maps techniques to their common synonyms, abbreviations,
    and alternative names used in the literature.
    """
    
    # Genomics techniques
    DNA_METHYLATION = {
        "canonical": "dna methylation",
        "synonyms": [
            "5mc", "5-methylcytosine", "methylation",
            "bisulfite sequencing", "bisulfite-seq", "bs-seq",
            "wgbs", "whole genome bisulfite sequencing",
            "rrbs", "reduced representation bisulfite sequencing",
            "methylc-seq", "methyl-seq",
            "nome-seq", "nucleosome occupancy and methylome sequencing",
            "em-seq", "enzymatic methyl-seq",
            "tet-assisted bisulfite sequencing", "tab-seq"
        ]
    }
    
    CHROMATIN_ACCESSIBILITY = {
        "canonical": "chromatin accessibility",
        "synonyms": [
            "open chromatin", "accessible chromatin",
            "atac-seq", "assay for transposase-accessible chromatin",
            "dnase-seq", "dnase hypersensitivity sequencing",
            "dnase-hypersensitivity", "dhs",
            "faire-seq", "formaldehyde-assisted isolation of regulatory elements",
            "mnase-seq", "micrococcal nuclease sequencing",
            "nome-seq"
        ]
    }
    
    HI_C = {
        "canonical": "hi-c",
        "synonyms": [
            "hi-c", "hic",
            "3d genome", "3d genome structure",
            "chromatin conformation", "chromosome conformation",
            "chromatin conformation capture", "3c",
            "genome architecture", "spatial genome organization",
            "chromatin architecture", "genome topology",
            "micro-c", "dnase hi-c", "nome-hic"
        ]
    }
    
    RNA_SEQ = {
        "canonical": "rna-seq",
        "synonyms": [
            "rna-seq", "rna sequencing", "rnaseq",
            "transcriptome", "transcriptome sequencing",
            "gene expression profiling", "expression profiling",
            "transcriptomics", "mrna-seq", "mrna sequencing",
            "total rna-seq", "poly-a rna-seq"
        ]
    }
    
    SINGLE_CELL = {
        "canonical": "single-cell",
        "synonyms": [
            "single cell", "single-cell", "sc-",
            "drop-seq", "droplet sequencing",
            "10x genomics", "10x", "10x chromium",
            "cell-level", "per-cell",
            "single-nucleus", "single nucleus", "sn-",
            "sciseq", "sci-seq"
        ]
    }
    
    MULTI_OMICS = {
        "canonical": "multi-omics",
        "synonyms": [
            "multiomics", "multi-omics", "multi omics",
            "joint profiling", "simultaneous profiling",
            "integrated profiling", "coupled assay",
            "combined profiling", "co-profiling",
            "nmt-seq", "nucleosome methylation and transcription sequencing",
            "nome-seq", "sci-met", "snare-seq",
            "paired-seq", "cite-seq", "reap-seq"
        ]
    }
    
    CHIP_SEQ = {
        "canonical": "chip-seq",
        "synonyms": [
            "chip-seq", "chip sequencing", "chipseq",
            "chromatin immunoprecipitation sequencing",
            "histone chip", "histone modification",
            "chip-chip", "cut&run", "cut&tag",
            "cleavage under targets and release using nuclease",
            "cleavage under targets and tagmentation"
        ]
    }
    
    # Build reverse index for fast lookup
    @classmethod
    def get_all_mappings(cls) -> Dict[str, List[str]]:
        """Get all technique mappings."""
        return {
            "dna_methylation": cls.DNA_METHYLATION,
            "chromatin_accessibility": cls.CHROMATIN_ACCESSIBILITY,
            "hi_c": cls.HI_C,
            "rna_seq": cls.RNA_SEQ,
            "single_cell": cls.SINGLE_CELL,
            "multi_omics": cls.MULTI_OMICS,
            "chip_seq": cls.CHIP_SEQ,
        }
    
    @classmethod
    def build_reverse_index(cls) -> Dict[str, str]:
        """Build reverse index: synonym -> canonical."""
        reverse_index = {}
        for category, data in cls.get_all_mappings().items():
            canonical = data["canonical"]
            # Add canonical itself
            reverse_index[canonical.lower()] = canonical
            # Add all synonyms
            for synonym in data["synonyms"]:
                reverse_index[synonym.lower()] = canonical
        return reverse_index
```

### 1.2 Integrate Synonym Expansion

**Objective**: Expand queries and dataset text with synonyms

**Implementation**:
```python
# UPDATE: omics_oracle_v2/agents/search_agent.py

from ..lib.ranking.synonyms import BiomedicalSynonyms

class SearchAgent(Agent[SearchInput, SearchOutput]):
    
    def __init__(self, settings: Settings):
        super().__init__(settings)
        self._synonym_index = BiomedicalSynonyms.build_reverse_index()
    
    def _expand_search_terms(self, terms: List[str]) -> List[str]:
        """
        Expand search terms with synonyms.
        
        Args:
            terms: Original search terms
            
        Returns:
            Expanded terms with synonyms
        """
        expanded = set(terms)
        
        for term in terms:
            term_lower = term.lower()
            # Check if term matches any canonical or synonym
            if term_lower in self._synonym_index:
                canonical = self._synonym_index[term_lower]
                # Add canonical term
                expanded.add(canonical)
                logger.debug(f"Expanded '{term}' to include canonical: '{canonical}'")
        
        return list(expanded)
    
    def _calculate_relevance(
        self, dataset: GEOSeriesMetadata, input_data: SearchInput
    ) -> tuple[float, List[str]]:
        """Calculate relevance score with synonym matching."""
        score = 0.0
        reasons = []
        
        # Expand search terms with synonyms
        expanded_terms = self._expand_search_terms(input_data.search_terms)
        search_terms_lower = {term.lower() for term in expanded_terms}
        
        # ... rest of scoring logic with expanded terms
```

### 1.3 Testing & Validation

**Tasks**:
1. Test synonym expansion
2. Verify improved ranking on sample queries
3. Benchmark performance impact

**Test Cases**:
```python
# tests/test_synonym_expansion.py

def test_nome_seq_recognized():
    """NOMe-seq should match DNA methylation AND chromatin accessibility."""
    query = "joint profiling of dna methylation and chromatin accessibility"
    dataset_title = "Genome-wide profiling using NOMe-seq"
    
    # Should recognize NOMe-seq = both techniques
    score = calculate_relevance(query, dataset_title)
    assert score > 0.7, "NOMe-seq should be highly relevant"

def test_atac_seq_expansion():
    """ATAC-seq should match chromatin accessibility query."""
    query = "chromatin accessibility in cancer"
    dataset_title = "ATAC-seq profiling of tumor samples"
    
    score = calculate_relevance(query, dataset_title)
    assert score > 0.6, "ATAC-seq should match accessibility"
```

**Deliverables**:
- [ ] `omics_oracle_v2/lib/ranking/synonyms.py` created
- [ ] Synonym expansion integrated
- [ ] Tests passing
- [ ] Documentation updated
- [ ] Performance benchmarked

---

## Phase 2: Semantic Search with OpenAI Embeddings

### Duration: 3-4 hours
### Priority: HIGH - Major impact on relevance

### 2.1 Create Embedding Service

**Objective**: Wrapper for OpenAI embedding generation with caching

**Implementation**:
```python
# NEW: omics_oracle_v2/lib/ranking/embeddings.py

import hashlib
import json
import logging
from pathlib import Path
from typing import List, Optional
import numpy as np

from ...core.config import Settings

logger = logging.getLogger(__name__)

class EmbeddingService:
    """
    OpenAI embedding generation with disk caching.
    
    Caches embeddings to avoid redundant API calls and reduce costs.
    """
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = None
        self.cache_dir = Path(settings.cache_directory) / "embeddings"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize OpenAI client
        if settings.ai.openai_api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=settings.ai.openai_api_key)
                logger.info("Embedding service initialized")
            except ImportError:
                logger.warning("OpenAI library not installed")
        else:
            logger.warning("OpenAI API key not configured")
    
    def _get_cache_key(self, text: str, model: str) -> str:
        """Generate cache key for text."""
        content = f"{model}:{text}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """Get cache file path."""
        return self.cache_dir / f"{cache_key}.json"
    
    def _load_from_cache(self, cache_key: str) -> Optional[List[float]]:
        """Load embedding from cache."""
        cache_path = self._get_cache_path(cache_key)
        if cache_path.exists():
            try:
                with open(cache_path, 'r') as f:
                    data = json.load(f)
                logger.debug(f"Loaded embedding from cache: {cache_key[:8]}...")
                return data['embedding']
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}")
        return None
    
    def _save_to_cache(self, cache_key: str, embedding: List[float]):
        """Save embedding to cache."""
        cache_path = self._get_cache_path(cache_key)
        try:
            with open(cache_path, 'w') as f:
                json.dump({'embedding': embedding}, f)
            logger.debug(f"Saved embedding to cache: {cache_key[:8]}...")
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")
    
    def get_embedding(
        self,
        text: str,
        model: str = "text-embedding-3-small",
        use_cache: bool = True
    ) -> Optional[List[float]]:
        """
        Get embedding for text.
        
        Args:
            text: Text to embed
            model: OpenAI embedding model
            use_cache: Whether to use caching
            
        Returns:
            Embedding vector or None if unavailable
        """
        if not self.client:
            return None
        
        # Check cache
        cache_key = self._get_cache_key(text, model)
        if use_cache:
            cached = self._load_from_cache(cache_key)
            if cached is not None:
                return cached
        
        # Generate embedding
        try:
            # Truncate text to avoid token limit
            truncated = text[:8000]
            
            response = self.client.embeddings.create(
                model=model,
                input=truncated
            )
            
            embedding = response.data[0].embedding
            
            # Cache result
            if use_cache:
                self._save_to_cache(cache_key, embedding)
            
            logger.debug(f"Generated embedding (model={model}, length={len(embedding)})")
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return None
    
    def calculate_similarity(
        self,
        embedding1: List[float],
        embedding2: List[float]
    ) -> float:
        """
        Calculate cosine similarity between embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Similarity score (0.0-1.0)
        """
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        # Cosine similarity
        similarity = np.dot(vec1, vec2) / (
            np.linalg.norm(vec1) * np.linalg.norm(vec2)
        )
        
        # Normalize to 0-1 range (cosine is -1 to 1)
        normalized = (similarity + 1) / 2
        
        return float(normalized)
```

### 2.2 Create Semantic Ranker

**Objective**: Combine keyword and semantic scores

**Implementation**:
```python
# NEW: omics_oracle_v2/lib/ranking/semantic_ranker.py

from typing import List, Tuple
import logging

from .embeddings import EmbeddingService
from .keyword_ranker import KeywordRanker
from .synonyms import BiomedicalSynonyms
from ...core.config import Settings

logger = logging.getLogger(__name__)

class SemanticRanker:
    """
    Hybrid semantic + keyword ranking.
    
    Combines traditional keyword matching with embedding-based
    semantic similarity for improved relevance scoring.
    """
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.embedding_service = EmbeddingService(settings)
        self.keyword_ranker = KeywordRanker(settings)
        self.synonyms = BiomedicalSynonyms()
        
        # Get weights from config
        self.semantic_weight = settings.ranking.semantic_weight
        self.keyword_weight = settings.ranking.keyword_weight
    
    def rank_dataset(
        self,
        query: str,
        dataset_title: str,
        dataset_summary: str,
        search_terms: List[str],
        dataset_id: str = None
    ) -> Tuple[float, List[str]]:
        """
        Calculate hybrid relevance score.
        
        Args:
            query: Original user query
            dataset_title: Dataset title
            dataset_summary: Dataset summary
            search_terms: Extracted search terms
            dataset_id: Dataset ID for caching
            
        Returns:
            Tuple of (score, reasons)
        """
        reasons = []
        
        # 1. Calculate keyword score
        keyword_score, keyword_reasons = self.keyword_ranker.calculate_relevance(
            title=dataset_title,
            summary=dataset_summary,
            search_terms=search_terms
        )
        reasons.extend([f"Keyword: {r}" for r in keyword_reasons])
        
        # 2. Calculate semantic similarity
        semantic_score = self._calculate_semantic_score(
            query=query,
            dataset_title=dataset_title,
            dataset_summary=dataset_summary,
            dataset_id=dataset_id
        )
        
        if semantic_score is not None:
            reasons.append(f"Semantic similarity: {semantic_score:.2f}")
            
            # 3. Blend scores
            final_score = (
                self.semantic_weight * semantic_score +
                self.keyword_weight * keyword_score
            )
            
            # 4. Boost if both agree
            if semantic_score > 0.7 and keyword_score > 0.5:
                final_score = min(1.0, final_score * 1.1)
                reasons.append("High confidence (semantic + keyword agreement)")
            
            return final_score, reasons
        else:
            # Fall back to keyword only
            reasons.append("Semantic ranking unavailable, using keyword only")
            return keyword_score, reasons
    
    def _calculate_semantic_score(
        self,
        query: str,
        dataset_title: str,
        dataset_summary: str,
        dataset_id: str = None
    ) -> Optional[float]:
        """Calculate semantic similarity score."""
        # Combine title and summary for dataset representation
        dataset_text = f"{dataset_title}. {dataset_summary}"
        
        # Get embeddings
        query_emb = self.embedding_service.get_embedding(
            text=query,
            use_cache=True
        )
        
        dataset_emb = self.embedding_service.get_embedding(
            text=dataset_text,
            use_cache=True
        )
        
        if query_emb is None or dataset_emb is None:
            return None
        
        # Calculate similarity
        similarity = self.embedding_service.calculate_similarity(
            query_emb,
            dataset_emb
        )
        
        return similarity
```

### 2.3 Integration with SearchAgent

**Objective**: Replace existing ranking with hybrid approach

**Tasks**:
1. Update SearchAgent to use SemanticRanker
2. Add configuration toggle (enable/disable semantic)
3. Add fallback to keyword-only if embedding fails
4. Update metrics tracking

**Implementation**:
```python
# UPDATE: omics_oracle_v2/agents/search_agent.py

from ..lib.ranking.semantic_ranker import SemanticRanker

class SearchAgent(Agent[SearchInput, SearchOutput]):
    
    def _initialize_resources(self) -> None:
        """Initialize resources."""
        # ... existing GEO client initialization
        
        # Initialize semantic ranker
        if self.settings.ranking.use_semantic_ranking:
            self.semantic_ranker = SemanticRanker(self.settings)
            logger.info("Semantic ranking enabled")
        else:
            self.semantic_ranker = None
            logger.info("Semantic ranking disabled, using keyword only")
    
    def _rank_datasets(
        self, datasets: List[GEOSeriesMetadata], input_data: SearchInput
    ) -> List[RankedDataset]:
        """Rank datasets with semantic or keyword ranking."""
        ranked = []
        
        for dataset in datasets:
            if self.semantic_ranker and input_data.original_query:
                # Use hybrid semantic + keyword ranking
                score, reasons = self.semantic_ranker.rank_dataset(
                    query=input_data.original_query,
                    dataset_title=dataset.title or "",
                    dataset_summary=dataset.summary or "",
                    search_terms=input_data.search_terms,
                    dataset_id=dataset.geo_id
                )
            else:
                # Fall back to keyword ranking
                score, reasons = self._calculate_relevance(dataset, input_data)
            
            ranked.append(
                RankedDataset(
                    dataset=dataset,
                    relevance_score=score,
                    match_reasons=reasons
                )
            )
        
        # Sort by relevance
        ranked.sort(key=lambda d: d.relevance_score, reverse=True)
        
        return ranked
```

### 2.4 Testing & Validation

**Test Cases**:
```python
# tests/test_semantic_ranking.py

def test_nome_seq_semantic_match():
    """NOMe-seq should get high semantic similarity."""
    query = "joint profiling of DNA methylation and chromatin accessibility"
    dataset = {
        "title": "Genome-wide NOMe-seq profiling",
        "summary": "We used NOMe-seq to simultaneously measure DNA methylation and chromatin accessibility..."
    }
    
    score, reasons = semantic_ranker.rank_dataset(
        query=query,
        dataset_title=dataset["title"],
        dataset_summary=dataset["summary"],
        search_terms=["joint profiling", "dna methylation", "chromatin accessibility"]
    )
    
    assert score > 0.8, f"NOMe-seq should get high score, got {score}"
    assert any("semantic" in r.lower() for r in reasons), "Should have semantic reasoning"

def test_embedding_caching():
    """Embeddings should be cached."""
    text = "Test dataset for caching"
    
    # First call - generates embedding
    emb1 = embedding_service.get_embedding(text)
    
    # Second call - should use cache
    emb2 = embedding_service.get_embedding(text)
    
    assert emb1 == emb2, "Cached embedding should match"
    # Check cache file exists
    cache_key = embedding_service._get_cache_key(text, "text-embedding-3-small")
    cache_path = embedding_service._get_cache_path(cache_key)
    assert cache_path.exists(), "Cache file should exist"
```

**Performance Testing**:
```python
# tests/benchmark_semantic.py

def benchmark_semantic_vs_keyword():
    """Compare performance and accuracy."""
    test_queries = [
        "joint profiling of chromatin accessibility AND DNA methylation",
        "single-cell RNA sequencing in cancer",
        "Hi-C genome architecture in development"
    ]
    
    for query in test_queries:
        # Test with 50 datasets
        results_semantic = rank_with_semantic(query, datasets)
        results_keyword = rank_with_keyword(query, datasets)
        
        print(f"Query: {query}")
        print(f"  Semantic top-5: {[r.geo_id for r in results_semantic[:5]]}")
        print(f"  Keyword top-5: {[r.geo_id for r in results_keyword[:5]]}")
        print(f"  Overlap: {calculate_overlap(results_semantic, results_keyword)}")
```

**Deliverables**:
- [ ] `EmbeddingService` implemented with caching
- [ ] `SemanticRanker` implemented
- [ ] SearchAgent updated
- [ ] Configuration added
- [ ] Tests passing
- [ ] Benchmark completed
- [ ] Documentation updated

---

## Phase 3: LLM Validation (Optional Polish)

### Duration: 2-3 hours
### Priority: MEDIUM - Nice to have, adds cost

### 3.1 Create LLM Validator

**Objective**: Use GPT-4 to validate top results

**Implementation**:
```python
# NEW: omics_oracle_v2/lib/ranking/llm_validator.py

from typing import Dict, List, Tuple
import logging

from ...lib.ai.client import SummarizationClient
from ...core.config import Settings

logger = logging.getLogger(__name__)

class LLMValidator:
    """
    LLM-based relevance validation for top results.
    
    Uses GPT-4 to provide human-like judgment on dataset relevance.
    Only applied to top N results to control costs.
    """
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.ai_client = SummarizationClient(settings)
        self.enabled = settings.ranking.enable_llm_validation
        self.top_n = settings.ranking.llm_validation_top_n
    
    def validate_relevance(
        self,
        query: str,
        dataset_title: str,
        dataset_summary: str,
        current_score: float
    ) -> Tuple[float, str]:
        """
        Validate dataset relevance using LLM.
        
        Args:
            query: User query
            dataset_title: Dataset title
            dataset_summary: Dataset summary  
            current_score: Current relevance score
            
        Returns:
            Tuple of (adjusted_score, explanation)
        """
        if not self.enabled or not self.ai_client.client:
            return current_score, "LLM validation disabled"
        
        prompt = self._build_validation_prompt(
            query, dataset_title, dataset_summary
        )
        
        try:
            response = self.ai_client._call_llm(
                prompt=prompt,
                system_message="You are an expert in biomedical data analysis.",
                max_tokens=200
            )
            
            # Parse response
            llm_score, explanation = self._parse_llm_response(response)
            
            # Blend with current score (70% LLM, 30% algorithmic)
            if llm_score is not None:
                adjusted_score = 0.7 * llm_score + 0.3 * current_score
                return adjusted_score, f"LLM: {explanation}"
            else:
                return current_score, "LLM validation failed to parse"
                
        except Exception as e:
            logger.error(f"LLM validation error: {e}")
            return current_score, f"LLM validation error: {str(e)}"
    
    def _build_validation_prompt(
        self, query: str, title: str, summary: str
    ) -> str:
        """Build prompt for LLM validation."""
        return f"""Evaluate how relevant this dataset is to the user's query.

User Query: {query}

Dataset Title: {title}

Dataset Summary: {summary[:500]}...

Rate the relevance on a scale of 0.0 to 1.0, where:
- 0.9-1.0: Highly relevant, directly addresses the query
- 0.7-0.8: Very relevant, covers most aspects
- 0.5-0.6: Moderately relevant, some overlap
- 0.3-0.4: Slightly relevant, tangential
- 0.0-0.2: Not relevant

Respond in this format:
SCORE: 0.X
REASON: Brief explanation of relevance
"""
    
    def _parse_llm_response(self, response: str) -> Tuple[Optional[float], str]:
        """Parse LLM response to extract score and reason."""
        try:
            lines = response.strip().split('\n')
            score_line = [l for l in lines if l.startswith('SCORE:')][0]
            reason_line = [l for l in lines if l.startswith('REASON:')][0]
            
            score = float(score_line.split(':')[1].strip())
            reason = reason_line.split(':')[1].strip()
            
            return score, reason
        except:
            return None, response
```

### 3.2 Integration

**Tasks**:
1. Add LLM validation to top N results
2. Add cost tracking
3. Add configuration toggle
4. Update metrics

**Deliverables**:
- [ ] `LLMValidator` implemented
- [ ] Integration complete
- [ ] Cost tracking added
- [ ] Configuration added
- [ ] Tests passing

---

## Phase 4: Monitoring & Optimization

### Duration: Ongoing
### Priority: HIGH - Ensure system performs well

### 4.1 Metrics & Logging

**Add tracking for**:
- Embedding API calls & costs
- LLM API calls & costs
- Cache hit rates
- Ranking performance
- User interactions

### 4.2 Performance Optimization

**Tasks**:
1. Batch embedding generation
2. Optimize cache storage
3. Add request throttling
4. Monitor API rate limits

### 4.3 Quality Monitoring

**Tasks**:
1. A/B test semantic vs keyword
2. Track user engagement metrics
3. Collect feedback on results
4. Iterate on synonym mappings

---

## Timeline Summary

| Phase | Duration | Dependencies | Deliverables |
|-------|----------|--------------|--------------|
| 0: Cleanup | 2-3 hours | None | Clean codebase, configs, tests |
| 1: Synonyms | 1-2 hours | Phase 0 | 30-40% improvement |
| 2: Semantic | 3-4 hours | Phase 0, 1 | 2x improvement |
| 3: LLM | 2-3 hours | Phase 2 | Polish, validation |
| 4: Monitor | Ongoing | All | Metrics, optimization |

**Total: 8-12 hours for full implementation**

---

## Success Criteria

### Phase 0:
- [ ] All configuration extracted
- [ ] All tests passing
- [ ] Code coverage ≥ 80%
- [ ] Documentation complete

### Phase 1:
- [ ] NOMe-seq recognized as joint profiling
- [ ] ATAC-seq matches chromatin accessibility
- [ ] 30-40% more relevant datasets found

### Phase 2:
- [ ] Semantic similarity working
- [ ] Cache hit rate > 50%
- [ ] Cost < $0.01 per query
- [ ] Ranking accuracy 2x better

### Phase 3:
- [ ] LLM validation working
- [ ] Cost tracked and within budget
- [ ] Top results validated

---

## Next Steps

1. Review this implementation plan
2. Get approval for phased approach
3. Start with Phase 0 (cleanup)
4. Implement phases sequentially
5. Test and validate each phase
6. Deploy incrementally

**Ready to start with Phase 0: Codebase Consolidation?** 🚀
