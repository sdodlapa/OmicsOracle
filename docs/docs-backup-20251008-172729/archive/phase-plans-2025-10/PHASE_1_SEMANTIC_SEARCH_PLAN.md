# Phase 1: Advanced Semantic Search - Implementation Plan

**Phase:** 1 - Semantic Search Enhancement
**Start Date:** October 5, 2025
**Estimated Duration:** 8-12 hours
**Status:** 🚀 **READY TO START**

---

## 🎯 Objectives

Transform OmicsOracle's search from basic keyword matching to intelligent semantic understanding:

1. **Semantic Similarity** - Understand query intent beyond exact keywords
2. **Hybrid Search** - Combine keyword + semantic ranking for best results
3. **Query Expansion** - Automatically find synonyms and related terms
4. **Vector Database** - Fast similarity search over large datasets
5. **Relevance Learning** - Improve results based on user interactions

### Expected Outcomes

- 📈 **50-80% improvement** in search relevance
- 🎯 **Better recall** - Find datasets even without exact keyword matches
- 🧠 **Intent understanding** - Handle natural language queries
- ⚡ **Fast performance** - Sub-second search even with embeddings
- 🔄 **Continuous improvement** - Learn from user feedback

---

## 📊 Current State Analysis

### What We Have (Phase 0)

✅ **Keyword Ranking System**
- Title/summary keyword matching
- Configurable weights (RankingConfig)
- 97% test coverage
- ~0.1ms performance

✅ **Quality Scoring System**
- 7-dimensional quality assessment
- Configurable thresholds (QualityConfig)
- 96% test coverage
- ~0.2ms performance

### Limitations of Current Approach

⚠️ **Exact Match Dependency**
- Query: "chromatin accessibility" → Finds datasets with those exact words
- Query: "open chromatin" → Misses "ATAC-seq" datasets (same concept!)
- Query: "gene expression profiling" → Misses "RNA-seq" datasets

⚠️ **No Synonym Understanding**
- "human" ≠ "Homo sapiens" (but should match!)
- "mouse" ≠ "Mus musculus"
- "RNA sequencing" ≠ "transcriptomics"

⚠️ **No Context Understanding**
- "ATAC-seq heart" - Can't understand "heart" modifies "ATAC-seq"
- "cancer treatment response" - Can't understand the relationship

⚠️ **Limited Ranking**
- Simple weighted sum of keyword matches
- No understanding of semantic similarity
- Can't rank by conceptual relevance

### Gap Analysis

| Capability | Current | Needed | Gap |
|------------|---------|--------|-----|
| Exact keyword match | ✅ 100% | ✅ 100% | None |
| Synonym detection | ❌ 0% | ✅ 90% | **High** |
| Semantic similarity | ❌ 0% | ✅ 85% | **High** |
| Natural language queries | ⚠️ 30% | ✅ 90% | **Medium** |
| Context understanding | ❌ 0% | ✅ 80% | **High** |
| Relevance learning | ❌ 0% | ✅ 70% | **Medium** |

---

## 🏗️ Architecture Design

### Component Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     Search Request                              │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              Query Understanding Layer                          │
├─────────────────────────────────────────────────────────────────┤
│  • Parse natural language                                       │
│  • Extract entities (genes, conditions, organisms)              │
│  • Generate query embedding (vector)                            │
│  • Expand with synonyms                                         │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Hybrid Search Layer                           │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐              ┌────────────────────────┐  │
│  │ Keyword Search   │              │  Semantic Search       │  │
│  │ (KeywordRanker)  │              │  (VectorDatabase)      │  │
│  │                  │              │                        │  │
│  │ • Title match    │              │ • Cosine similarity    │  │
│  │ • Summary match  │              │ • KNN search           │  │
│  │ • Organism match │              │ • Embedding match      │  │
│  └────────┬─────────┘              └───────────┬────────────┘  │
│           │                                    │                │
│           │         ┌──────────────────────┐   │                │
│           └────────►│   Score Fusion       │◄──┘                │
│                     │  (Weighted Average)  │                    │
│                     └──────────┬───────────┘                    │
└────────────────────────────────┼────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Quality Re-Ranking                           │
├─────────────────────────────────────────────────────────────────┤
│  • Apply quality scores (QualityScorer)                         │
│  • Boost high-quality datasets                                  │
│  • Penalize low-quality datasets                                │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Final Ranked Results                          │
└─────────────────────────────────────────────────────────────────┘
```

### New Components to Build

1. **EmbeddingService** - Generate embeddings for queries and datasets
2. **VectorDatabase** - Store and search dataset embeddings efficiently
3. **SemanticRanker** - Calculate semantic similarity scores
4. **HybridSearchEngine** - Combine keyword + semantic results
5. **QueryExpander** - Expand queries with synonyms/related terms
6. **RelevanceLearner** - Learn from user feedback (future)

---

## 📋 Implementation Steps

### Step 1: Embedding Service (2 hours)

**Objective:** Create service to generate text embeddings

**Tasks:**
1. Research embedding models:
   - OpenAI: `text-embedding-3-small` (1536 dims, $0.02/1M tokens)
   - OpenAI: `text-embedding-3-large` (3072 dims, $0.13/1M tokens)
   - Local: `sentence-transformers` (free, slower, 384-768 dims)

2. Create `EmbeddingService` class:
   ```python
   class EmbeddingService:
       def embed_text(text: str) -> List[float]
       def embed_batch(texts: List[str]) -> List[List[float]]
       def get_dimension() -> int
   ```

3. Implement caching:
   - Cache embeddings in Redis/file system
   - Avoid re-computing same texts

4. Add configuration:
   ```python
   class EmbeddingConfig:
       provider: Literal["openai", "local"]
       model: str
       dimension: int
       batch_size: int
       cache_enabled: bool
   ```

5. Write unit tests (target: 80% coverage)

**Deliverables:**
- `omics_oracle_v2/lib/embeddings/service.py`
- `omics_oracle_v2/lib/embeddings/cache.py`
- `tests/unit/lib/embeddings/test_service.py`
- Configuration in `core/config.py`

---

### Step 2: Vector Database (2 hours)

**Objective:** Store and search dataset embeddings efficiently

**Options:**

| Database | Pros | Cons | Choice |
|----------|------|------|--------|
| **FAISS** | Fast, local, free | No persistence | ✅ **Phase 1** |
| **ChromaDB** | Simple, persistent | Limited scale | ⚠️ Alternative |
| **Pinecone** | Managed, scalable | Paid, cloud-only | 🔮 Future |
| **Weaviate** | Full-featured | Complex setup | 🔮 Future |

**Decision: Start with FAISS**
- ✅ Fast similarity search
- ✅ No external dependencies
- ✅ Works offline
- ✅ Easy to switch later

**Tasks:**
1. Create `VectorDatabase` interface:
   ```python
   class VectorDatabase:
       def add(id: str, embedding: List[float], metadata: dict)
       def search(query_embedding: List[float], k: int) -> List[SearchResult]
       def update(id: str, embedding: List[float])
       def delete(id: str)
       def save() -> None
       def load() -> None
   ```

2. Implement FAISS backend:
   - Index creation (IVF for speed + accuracy)
   - Batch insertion
   - KNN search
   - Persistence to disk

3. Add dataset embedding pipeline:
   - Embed title + summary + keywords
   - Store in vector DB
   - Build search index

4. Write unit tests

**Deliverables:**
- `omics_oracle_v2/lib/vector_db/interface.py`
- `omics_oracle_v2/lib/vector_db/faiss_backend.py`
- `tests/unit/lib/vector_db/test_faiss.py`

---

### Step 3: Semantic Ranker (1.5 hours)

**Objective:** Calculate semantic similarity scores

**Tasks:**
1. Create `SemanticRanker` class:
   ```python
   class SemanticRanker:
       def __init__(
           embedding_service: EmbeddingService,
           vector_db: VectorDatabase
       )

       def calculate_semantic_score(
           query: str,
           k: int = 100
       ) -> List[Tuple[str, float, str]]
       # Returns: [(dataset_id, score, reason)]
   ```

2. Implement similarity calculation:
   - Embed query
   - Search vector DB
   - Convert cosine similarity to 0-1 score
   - Generate explanations ("Semantically similar to: ...")

3. Add configuration:
   ```python
   class SemanticConfig:
       similarity_threshold: float = 0.7
       max_results: int = 100
       score_weight: float = 0.5  # 50% semantic, 50% keyword
   ```

4. Write unit tests

**Deliverables:**
- `omics_oracle_v2/lib/ranking/semantic_ranker.py`
- `tests/unit/lib/ranking/test_semantic_ranker.py`
- Config updates in `core/config.py`

---

### Step 4: Hybrid Search Engine (2 hours)

**Objective:** Combine keyword + semantic ranking

**Tasks:**
1. Create `HybridSearchEngine`:
   ```python
   class HybridSearchEngine:
       def __init__(
           keyword_ranker: KeywordRanker,
           semantic_ranker: SemanticRanker,
           quality_scorer: QualityScorer,
           config: HybridSearchConfig
       )

       def search(
           query: str,
           max_results: int = 20
       ) -> List[SearchResult]
   ```

2. Implement fusion strategies:
   - **Linear Combination**: `α·keyword + β·semantic`
   - **RRF (Reciprocal Rank Fusion)**: Rank-based fusion
   - **Weighted Average**: Configurable weights

3. Add quality boosting:
   ```python
   final_score = (
       alpha * keyword_score +
       beta * semantic_score +
       gamma * quality_score
   )
   ```

4. Generate comprehensive explanations:
   ```python
   {
       "score": 0.92,
       "breakdown": {
           "keyword": 0.85,
           "semantic": 0.95,
           "quality": 0.88
       },
       "reasons": [
           "Keyword match: ATAC-seq (0.15)",
           "Semantically similar to chromatin accessibility (0.92)",
           "High quality: Excellent sample count, Published"
       ]
   }
   ```

5. Write unit tests

**Deliverables:**
- `omics_oracle_v2/lib/search/hybrid_engine.py`
- `tests/unit/lib/search/test_hybrid_engine.py`
- Config class `HybridSearchConfig`

---

### Step 5: Dataset Embedding Pipeline (1.5 hours)

**Objective:** Embed existing datasets and new ones automatically

**Tasks:**
1. Create embedding generator:
   ```python
   def generate_dataset_embedding(metadata: GEOSeriesMetadata) -> List[float]:
       text = f"{metadata.title}. {metadata.summary}. "
       text += f"Organism: {metadata.organism}. "
       text += f"Keywords: {', '.join(metadata.keywords)}"
       return embedding_service.embed_text(text)
   ```

2. Build batch embedding script:
   - Load all GEO datasets from cache
   - Generate embeddings in batches
   - Store in vector DB
   - Save index to disk

3. Add incremental update:
   - Embed new datasets as they're added
   - Update vector DB automatically
   - Rebuild index periodically

4. Create CLI tool:
   ```bash
   python -m omics_oracle_v2.scripts.embed_datasets \
       --batch-size 100 \
       --model text-embedding-3-small \
       --output data/embeddings/
   ```

5. Add monitoring:
   - Track embedding progress
   - Log errors
   - Report statistics

**Deliverables:**
- `omics_oracle_v2/scripts/embed_datasets.py`
- `omics_oracle_v2/lib/embeddings/pipeline.py`
- Documentation for running embeddings

---

### Step 6: Integration with Agents (1.5 hours)

**Objective:** Update SearchAgent to use hybrid search

**Tasks:**
1. Update `SearchAgent._search_datasets()`:
   ```python
   # Before (keyword only)
   results = []
   for dataset in all_datasets:
       score = self.keyword_ranker.calculate_relevance(...)
       results.append((dataset, score))

   # After (hybrid)
   results = self.hybrid_engine.search(
       query=processed_query,
       max_results=self.config.max_results
   )
   ```

2. Add backward compatibility:
   - Flag to enable/disable semantic search
   - Fall back to keyword-only if embeddings not available
   - Graceful degradation

3. Update response format:
   - Include semantic similarity scores
   - Show hybrid ranking breakdown
   - Explain why each dataset matched

4. Add configuration:
   ```python
   class SearchAgentConfig:
       use_semantic_search: bool = True
       semantic_weight: float = 0.5
       keyword_weight: float = 0.5
       quality_weight: float = 0.3
   ```

**Deliverables:**
- Updated `omics_oracle_v2/agents/search_agent.py`
- Updated tests `tests/unit/agents/test_search_agent.py`
- Migration guide in docs

---

### Step 7: Query Expansion (Optional - 1.5 hours)

**Objective:** Automatically expand queries with synonyms

**Tasks:**
1. Create synonym database:
   - Biomedical ontologies (Gene Ontology, Disease Ontology)
   - Common abbreviations (ATAC-seq → chromatin accessibility)
   - Organism names (human → Homo sapiens)

2. Implement query expander:
   ```python
   class QueryExpander:
       def expand(query: str) -> List[str]:
           # Original + synonyms
           return [query] + self.find_synonyms(query)
   ```

3. Integrate with search:
   - Expand query before embedding
   - Search for all variations
   - Merge results

**Deliverables:**
- `omics_oracle_v2/lib/nlp/query_expander.py`
- Synonym database (JSON/CSV)
- Tests

---

### Step 8: Testing & Validation (1 hour)

**Objective:** Comprehensive testing of semantic search

**Tasks:**
1. Unit tests:
   - EmbeddingService: 80% coverage
   - VectorDatabase: 85% coverage
   - SemanticRanker: 80% coverage
   - HybridSearchEngine: 85% coverage

2. Integration tests:
   - End-to-end search flow
   - Keyword vs semantic vs hybrid comparison
   - Performance benchmarks

3. Quality tests:
   - Test queries with expected results
   - Measure precision@k, recall@k
   - Compare to baseline (keyword-only)

4. Performance tests:
   - Search latency (target: <500ms)
   - Embedding generation time
   - Index build time
   - Memory usage

**Test Scenarios:**
```python
test_cases = [
    {
        "query": "chromatin accessibility",
        "expected_to_find": ["ATAC-seq", "DNase-seq"],
        "method": "semantic"
    },
    {
        "query": "open chromatin human",
        "expected_organism": "Homo sapiens",
        "expected_keywords": ["ATAC-seq", "chromatin"],
        "method": "hybrid"
    },
    {
        "query": "GSE123456",
        "expected_exact_match": True,
        "method": "keyword"
    }
]
```

**Deliverables:**
- Comprehensive test suite
- Performance benchmarks
- Quality metrics report
- Comparison with baseline

---

### Step 9: Documentation (1 hour)

**Objective:** Complete documentation for semantic search

**Tasks:**
1. Architecture documentation:
   - System overview
   - Component descriptions
   - Data flow diagrams
   - Configuration guide

2. API documentation:
   - EmbeddingService API
   - VectorDatabase API
   - SemanticRanker API
   - HybridSearchEngine API

3. Usage guide:
   - How to enable semantic search
   - How to embed datasets
   - How to tune parameters
   - Troubleshooting

4. Performance guide:
   - Benchmark results
   - Optimization tips
   - Scaling recommendations

**Deliverables:**
- `docs/architecture/SEMANTIC_SEARCH.md`
- `docs/guides/EMBEDDING_GUIDE.md`
- `docs/performance/SEMANTIC_SEARCH_BENCHMARKS.md`
- Updated `ARCHITECTURE.md`

---

### Step 10: Deployment & Monitoring (30 min)

**Objective:** Deploy and monitor semantic search

**Tasks:**
1. Build embedding index:
   - Run embedding pipeline on all datasets
   - Verify index quality
   - Test search performance

2. Update deployment:
   - Add FAISS to requirements
   - Update Docker image
   - Configure production settings

3. Add monitoring:
   - Search latency metrics
   - Embedding cache hit rate
   - Vector DB query performance
   - Error tracking

4. Create rollback plan:
   - Feature flag for semantic search
   - Fallback to keyword-only
   - Monitoring alerts

**Deliverables:**
- Embedded dataset index
- Updated deployment configs
- Monitoring dashboards
- Rollback procedures

---

## 📊 Success Metrics

### Quantitative Metrics

| Metric | Baseline (Keyword) | Target (Hybrid) | Measurement |
|--------|-------------------|-----------------|-------------|
| **Precision@10** | 0.60 | 0.80 | Manual evaluation |
| **Recall@100** | 0.40 | 0.70 | Manual evaluation |
| **MRR (Mean Reciprocal Rank)** | 0.55 | 0.75 | Test queries |
| **Search Latency** | 50ms | <500ms | p95 latency |
| **User Satisfaction** | Baseline | +30% | User surveys |

### Qualitative Metrics

✅ **Synonym Matching**
- Query "human" finds "Homo sapiens" datasets
- Query "RNA-seq" finds "transcriptomics" datasets

✅ **Concept Understanding**
- Query "chromatin accessibility" finds ATAC-seq datasets
- Query "gene expression" finds RNA-seq and microarray datasets

✅ **Natural Language**
- Query "How does ATAC-seq measure chromatin?" returns relevant datasets
- Query "Find cancer treatment studies" returns oncology datasets

✅ **Robustness**
- Handles typos gracefully
- Degrades gracefully when embeddings unavailable
- Fast enough for interactive use

---

## 🔧 Configuration

### Embedding Configuration

```python
class EmbeddingConfig(BaseModel):
    # Provider
    provider: Literal["openai", "local"] = "openai"

    # OpenAI settings
    openai_model: str = "text-embedding-3-small"
    openai_api_key: Optional[str] = None

    # Local model settings
    local_model: str = "all-MiniLM-L6-v2"
    device: str = "cpu"  # or "cuda"

    # Performance
    batch_size: int = 100
    dimension: int = 1536  # Model-specific

    # Caching
    cache_enabled: bool = True
    cache_dir: str = "data/embeddings/cache"
    cache_ttl: int = 86400 * 30  # 30 days
```

### Vector Database Configuration

```python
class VectorDBConfig(BaseModel):
    # Backend
    backend: Literal["faiss", "chromadb"] = "faiss"

    # FAISS settings
    index_type: str = "IVF256,Flat"  # For speed + accuracy
    nprobe: int = 32  # Search probes

    # Persistence
    index_path: str = "data/vector_db/index.faiss"
    metadata_path: str = "data/vector_db/metadata.json"

    # Performance
    build_batch_size: int = 1000
    search_batch_size: int = 100
```

### Semantic Search Configuration

```python
class SemanticConfig(BaseModel):
    # Search parameters
    similarity_threshold: float = 0.7
    max_results: int = 100

    # Scoring
    score_weight: float = 0.5  # vs keyword weight
    quality_boost: float = 0.2  # Boost factor for quality

    # Filtering
    min_semantic_score: float = 0.5
    enable_query_expansion: bool = False
```

### Hybrid Search Configuration

```python
class HybridSearchConfig(BaseModel):
    # Fusion strategy
    fusion_method: Literal["linear", "rrf", "weighted"] = "weighted"

    # Weights (must sum to 1.0)
    keyword_weight: float = 0.4
    semantic_weight: float = 0.4
    quality_weight: float = 0.2

    # RRF parameters
    rrf_k: int = 60

    # Results
    max_results: int = 20
    min_combined_score: float = 0.3
```

---

## ⚡ Performance Targets

### Latency Targets

| Operation | Target | Maximum |
|-----------|--------|---------|
| Embed query | 50ms | 100ms |
| Vector search | 100ms | 300ms |
| Hybrid search (total) | 300ms | 500ms |
| Index build (10k datasets) | 5min | 10min |

### Accuracy Targets

| Metric | Keyword | Semantic | Hybrid | Target |
|--------|---------|----------|--------|--------|
| Precision@10 | 0.60 | 0.75 | 0.80 | ≥0.75 |
| Recall@100 | 0.40 | 0.65 | 0.70 | ≥0.65 |
| MRR | 0.55 | 0.70 | 0.75 | ≥0.70 |

### Scale Targets

| Metric | Target |
|--------|--------|
| Datasets indexed | 100,000+ |
| Queries per second | 100+ |
| Index size | <5GB |
| Memory usage | <2GB |

---

## 🚧 Risks & Mitigation

### Technical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Slow embedding generation** | High | Medium | Batch processing, caching, async |
| **High memory usage** | Medium | Low | FAISS optimization, pagination |
| **Poor semantic quality** | High | Medium | Multiple models, fine-tuning |
| **API rate limits** | Medium | Medium | Local models, request batching |

### Operational Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Index corruption** | High | Low | Regular backups, checksums |
| **Cold start delay** | Medium | High | Pre-warm cache, lazy loading |
| **Cost overruns** | Medium | Medium | Local models, usage monitoring |

---

## 📅 Timeline

### Week 1 (8 hours)

| Day | Tasks | Hours | Status |
|-----|-------|-------|--------|
| **Day 1** | Steps 1-2: Embedding + Vector DB | 4h | 🚀 Ready |
| **Day 2** | Steps 3-4: Semantic + Hybrid | 4h | 📅 Planned |

### Week 2 (4 hours)

| Day | Tasks | Hours | Status |
|-----|-------|-------|--------|
| **Day 3** | Steps 5-6: Pipeline + Integration | 3h | 📅 Planned |
| **Day 4** | Steps 8-10: Testing + Deploy | 1h | 📅 Planned |

**Total Estimated Time:** 8-12 hours

---

## ✅ Acceptance Criteria

Phase 1 is complete when:

1. ✅ **Embedding Service** operational with 80%+ test coverage
2. ✅ **Vector Database** built with 10k+ indexed datasets
3. ✅ **Semantic Search** working with <500ms latency
4. ✅ **Hybrid Search** showing 30%+ improvement over keyword-only
5. ✅ **Integration** complete with SearchAgent
6. ✅ **Tests** passing with 80%+ coverage
7. ✅ **Documentation** comprehensive and clear
8. ✅ **Performance** meeting latency targets
9. ✅ **Deployment** successful in dev/staging
10. ✅ **Quality** metrics validated

---

## 🔮 Future Enhancements (Phase 2+)

- **Fine-tuned embeddings** on biomedical data
- **Multi-modal search** (text + images + graphs)
- **Relevance feedback** learning from clicks
- **Personalized search** based on user history
- **Federated search** across multiple databases
- **Real-time indexing** with streaming updates
- **Advanced query understanding** with LLMs
- **Explainable AI** for ranking decisions

---

**Ready to start Phase 1?** Let's build the future of genomic data search! 🚀
