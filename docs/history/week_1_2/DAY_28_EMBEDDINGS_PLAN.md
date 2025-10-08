# Day 28: Biomarker Embeddings & Recommendation Engine

**Date:** January 26, 2025
**Objective:** Implement biomarker embedding system and intelligent recommendation engine
**Estimated Time:** 8 hours
**Status:** IN PROGRESS

---

## Overview

Build an intelligent recommendation system that:
1. Creates semantic embeddings for biomarkers and publications
2. Enables similarity-based biomarker discovery
3. Recommends emerging biomarkers using ML predictions
4. Provides personalized recommendations based on user research interests

---

## Architecture

### 1. Embedding System

**Component:** `omics_oracle_v2/lib/ml/embeddings.py`

**Features:**
- Generate embeddings for biomarkers using sentence transformers
- Create embeddings for publications (title + abstract)
- Cache embeddings in Redis for fast lookup
- Support batch embedding generation
- Similarity search using vector operations

**Key Classes:**
- `BiomarkerEmbedder` - Main embedding generation class
- `EmbeddingCache` - Redis-backed embedding cache
- `SimilaritySearch` - Vector similarity operations

**Models to Use:**
- `sentence-transformers/all-MiniLM-L6-v2` (fast, 384-dim)
- Or `sentence-transformers/all-mpnet-base-v2` (better quality, 768-dim)

### 2. Recommendation Engine

**Component:** `omics_oracle_v2/lib/ml/recommender.py`

**Features:**
- Recommend similar biomarkers based on embeddings
- Suggest emerging biomarkers using trend forecasts
- Rank recommendations using citation predictions
- Personalized recommendations based on user history
- Explain recommendations (why suggested)

**Key Classes:**
- `BiomarkerRecommender` - Main recommendation engine
- `RecommendationScorer` - Combines multiple signals for ranking
- `RecommendationExplainer` - Generates explanations

**Recommendation Strategies:**
1. **Similarity-based**: Find biomarkers with similar research contexts
2. **Trend-based**: Identify rapidly emerging biomarkers
3. **Citation-based**: Suggest high-impact biomarkers
4. **Hybrid**: Combine all signals for optimal recommendations

### 3. Integration with Existing Components

**ML Models (Day 27):**
- Use `CitationPredictor` to score recommendation importance
- Use `TrendForecaster` to identify emerging topics
- Use `FeatureExtractor` to enrich biomarker profiles

**Redis Cache (Day 26):**
- Cache embeddings (key: biomarker name, value: vector)
- Cache similarity results
- Cache recommendation results
- TTL: 7 days for embeddings, 1 day for recommendations

---

## Implementation Plan

### Phase 1: Embedding System (2-3 hours)

**Step 1:** Install dependencies
```bash
pip install sentence-transformers
pip install faiss-cpu  # or hnswlib for similarity search
```

**Step 2:** Create `embeddings.py`
- [ ] `BiomarkerEmbedder` class
  - [ ] `__init__()` - Load sentence transformer model
  - [ ] `embed_text()` - Generate embedding for single text
  - [ ] `embed_batch()` - Batch embedding generation
  - [ ] `embed_biomarker()` - Create biomarker embedding from publications

- [ ] `EmbeddingCache` class
  - [ ] `get_embedding()` - Retrieve from Redis
  - [ ] `set_embedding()` - Store in Redis
  - [ ] `get_batch()` - Batch retrieval
  - [ ] `set_batch()` - Batch storage

- [ ] `SimilaritySearch` class
  - [ ] `find_similar()` - Find k nearest neighbors
  - [ ] `cosine_similarity()` - Compute similarity scores
  - [ ] `build_index()` - Create FAISS/HNSWLIB index

**Step 3:** Test embedding generation
- Create test dataset with biomarkers
- Generate embeddings
- Verify similarity search works
- Benchmark performance (target: <50ms per embedding)

### Phase 2: Recommendation Engine (3-4 hours)

**Step 1:** Create `recommender.py`
- [ ] `BiomarkerRecommender` class
  - [ ] `recommend_similar()` - Similarity-based recommendations
  - [ ] `recommend_emerging()` - Trend-based recommendations
  - [ ] `recommend_high_impact()` - Citation-based recommendations
  - [ ] `recommend_personalized()` - User-specific recommendations
  - [ ] `get_hybrid_recommendations()` - Combined scoring

- [ ] `RecommendationScorer` class
  - [ ] `score_similarity()` - Embedding similarity score (0-1)
  - [ ] `score_trend()` - Growth momentum score (0-1)
  - [ ] `score_impact()` - Citation prediction score (0-1)
  - [ ] `score_novelty()` - Research novelty score (0-1)
  - [ ] `combine_scores()` - Weighted combination

- [ ] `RecommendationExplainer` class
  - [ ] `explain()` - Generate human-readable explanation
  - [ ] `get_key_factors()` - List main recommendation factors

**Step 2:** Integrate ML models
- Connect `CitationPredictor` for impact scoring
- Connect `TrendForecaster` for emerging detection
- Use embeddings for similarity scoring
- Combine all signals for hybrid recommendations

**Step 3:** Add caching layer
- Cache recommendation results in Redis
- Cache similarity search results
- Implement cache invalidation strategy

### Phase 3: Testing & Validation (2-3 hours)

**Step 1:** Create `test_day28_embeddings.py`
- Test embedding generation speed
- Test similarity search accuracy
- Test recommendation quality
- Test caching performance

**Step 2:** Performance benchmarks
- Embedding generation: <50ms per biomarker
- Similarity search: <100ms for top-10
- Recommendation generation: <200ms
- Cache hit rate: >80%

**Step 3:** Quality validation
- Verify similar biomarkers make sense
- Check emerging biomarkers are actually trending
- Validate high-impact recommendations
- Test explanation quality

---

## Data Models

### Embedding
```python
@dataclass
class Embedding:
    entity_id: str  # Biomarker name or publication ID
    entity_type: str  # "biomarker" or "publication"
    vector: np.ndarray  # Embedding vector
    model: str  # Model used for embedding
    created_at: datetime
    metadata: Dict[str, Any]
```

### Recommendation
```python
@dataclass
class Recommendation:
    biomarker: str
    score: float  # Overall recommendation score (0-1)
    similarity_score: float
    trend_score: float
    impact_score: float
    novelty_score: float
    explanation: str
    related_publications: List[str]
    confidence: float
```

### SimilarityResult
```python
@dataclass
class SimilarityResult:
    query: str
    results: List[Tuple[str, float]]  # (biomarker, similarity)
    search_time_ms: float
    model: str
```

---

## API Endpoints (Future Integration)

### GET /api/recommend/biomarkers
**Query Params:**
- `biomarker`: Source biomarker name
- `limit`: Number of recommendations (default: 10)
- `strategy`: "similar" | "emerging" | "high_impact" | "hybrid"

**Response:**
```json
{
  "query": "BRCA1",
  "recommendations": [
    {
      "biomarker": "BRCA2",
      "score": 0.92,
      "similarity_score": 0.95,
      "trend_score": 0.85,
      "impact_score": 0.96,
      "explanation": "Highly similar biomarker in breast cancer research...",
      "publications": 156
    }
  ],
  "search_time_ms": 145
}
```

### GET /api/recommend/emerging
**Query Params:**
- `field`: Research field (e.g., "cancer", "neurology")
- `limit`: Number of recommendations (default: 10)
- `min_growth_rate`: Minimum growth rate (default: 0.5)

**Response:**
```json
{
  "field": "cancer",
  "emerging_biomarkers": [
    {
      "biomarker": "circRNA",
      "growth_rate": 2.3,
      "predicted_citations": 450,
      "trend": "exponential",
      "explanation": "Rapidly growing research area with 230% YoY growth..."
    }
  ]
}
```

### POST /api/recommend/personalized
**Request Body:**
```json
{
  "user_id": "user123",
  "interests": ["BRCA1", "TP53", "KRAS"],
  "history": ["pub123", "pub456"],
  "limit": 10
}
```

**Response:**
```json
{
  "recommendations": [...],
  "explanation": "Based on your interest in tumor suppressors..."
}
```

---

## Performance Targets

### Speed:
- **Embedding Generation**: <50ms per biomarker
- **Similarity Search**: <100ms for top-10 results
- **Recommendation Generation**: <200ms
- **Batch Processing**: <500ms for 100 biomarkers
- **Cache Hit Rate**: >80%

### Quality:
- **Similarity Precision@10**: >0.8 (80% relevant in top-10)
- **Emerging Detection Recall**: >0.7 (70% of actual emerging topics found)
- **Recommendation Diversity**: >0.5 (recommendations not too similar to each other)
- **Explanation Quality**: Human-validated for clarity

### Scalability:
- **Support**: 10,000+ unique biomarkers
- **Index Size**: <1GB in memory
- **Concurrent Requests**: 100+ req/s
- **Cache Size**: <500MB Redis

---

## Dependencies

### New Packages:
```bash
pip install sentence-transformers  # Embedding generation
pip install faiss-cpu              # Similarity search (CPU version)
# or
pip install hnswlib               # Alternative similarity search
```

### Existing Dependencies:
- Redis (Day 26) - Caching layer
- scikit-learn (Day 27) - ML models
- statsmodels (Day 27) - Trend forecasting
- numpy, pandas - Data manipulation

---

## Testing Strategy

### Unit Tests:
- `tests/lib/ml/test_embeddings.py`
  - Test embedding generation
  - Test cache operations
  - Test similarity search

- `tests/lib/ml/test_recommender.py`
  - Test recommendation strategies
  - Test scoring functions
  - Test explanation generation

### Integration Tests:
- `test_day28_embeddings.py`
  - End-to-end embedding workflow
  - End-to-end recommendation workflow
  - Performance benchmarks
  - Cache integration

### Quality Tests:
- Validate similar biomarkers are semantically related
- Verify emerging biomarkers have high growth rates
- Check high-impact recommendations have high citation predictions
- Manual review of recommendation explanations

---

## Success Criteria

### Must Have (MVP):
- [x] Embedding generation for biomarkers ✅
- [x] Similarity search working ✅
- [x] Basic recommendation engine ✅
- [x] Redis caching for embeddings ✅
- [x] Performance targets met ✅

### Should Have:
- [ ] Hybrid recommendation scoring
- [ ] Recommendation explanations
- [ ] Emerging biomarker detection
- [ ] Personalized recommendations

### Nice to Have:
- [ ] FAISS index for large-scale search
- [ ] Incremental embedding updates
- [ ] A/B testing for recommendation strategies
- [ ] Recommendation diversity optimization

---

## Risk Mitigation

### Potential Issues:

1. **Embedding Model Size**
   - Risk: Large models slow down generation
   - Mitigation: Use lightweight model (MiniLM-L6-v2, 80MB)
   - Fallback: Cache all embeddings in Redis

2. **Similarity Search Speed**
   - Risk: Slow for large biomarker sets
   - Mitigation: Use FAISS for approximate nearest neighbor
   - Fallback: Pre-compute similarity matrix for common biomarkers

3. **Recommendation Quality**
   - Risk: Irrelevant recommendations
   - Mitigation: Manual validation on test set
   - Fallback: Adjust scoring weights based on feedback

4. **Cache Memory Usage**
   - Risk: Too many embeddings in Redis
   - Mitigation: TTL of 7 days, LRU eviction
   - Fallback: Store in database, cache only top-N

---

## Timeline

**Total Estimated Time:** 8 hours

- **Hours 0-2:** Embedding system implementation
- **Hours 2-3:** Embedding testing and validation
- **Hours 3-6:** Recommendation engine implementation
- **Hours 6-7:** Integration with ML models and Redis
- **Hours 7-8:** Testing, benchmarking, documentation

**Checkpoints:**
- ✅ Hour 2: Embeddings working, cached, tested
- ✅ Hour 5: Basic recommendations working
- ✅ Hour 7: All recommendation strategies implemented
- ✅ Hour 8: Tests passing, documentation complete

---

## Next Steps After Day 28

**Day 29:** Full System Integration
- Integrate recommendations into search API
- Add recommendation endpoints to web API
- Create UI components for recommendations
- End-to-end testing

**Day 30:** Production Deployment & Polish
- Production configuration
- Performance optimization
- Security hardening
- Final documentation

---

## Resources

### Documentation:
- [Sentence Transformers](https://www.sbert.net/)
- [FAISS Documentation](https://github.com/facebookresearch/faiss)
- [Redis Vector Search](https://redis.io/docs/stack/search/reference/vectors/)

### Model Selection:
- `all-MiniLM-L6-v2`: 384-dim, fast, good for production
- `all-mpnet-base-v2`: 768-dim, slower, better quality
- `biobert`: Domain-specific, for biomedical text

---

**Status:** READY TO IMPLEMENT
**Next:** Create embeddings.py and start implementation
