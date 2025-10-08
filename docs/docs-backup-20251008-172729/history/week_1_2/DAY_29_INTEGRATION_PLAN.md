# Day 29: System Integration & API Endpoints

**Date:** January 26, 2025
**Objective:** Integrate ML features into the API and create comprehensive endpoints
**Estimated Time:** 8 hours
**Status:** IN PROGRESS

---

## Overview

Integrate all ML components (Days 27-28) into the search API and create new endpoints for:
- Citation predictions
- Trend forecasting
- Biomarker recommendations
- Enhanced search with ML features

---

## Architecture

### Integration Points

**Existing System:**
- Search API (FastAPI)
- Redis Cache (Day 26)
- Publication Models
- Database Layer

**ML Components to Integrate:**
- Citation Predictor (Day 27)
- Trend Forecaster (Day 27)
- Feature Extractor (Day 27)
- Biomarker Embedder (Day 28)
- Recommendation Engine (Day 28)

### New API Endpoints

#### 1. Enhanced Search
- `GET /api/search/enhanced` - Search with ML predictions
- Returns: Publications + citation predictions + trend indicators

#### 2. Recommendations
- `GET /api/recommend/similar` - Similar biomarkers
- `GET /api/recommend/emerging` - Emerging biomarkers
- `GET /api/recommend/high-impact` - High-impact biomarkers
- `GET /api/recommend/personalized` - Personalized recommendations

#### 3. Predictions
- `POST /api/predict/citations` - Predict citations for publications
- `GET /api/predict/trends` - Forecast publication trends

#### 4. Analytics
- `GET /api/analytics/biomarker/{name}` - Comprehensive biomarker analytics
- `GET /api/analytics/trends` - Research trend analysis

---

## Implementation Plan

### Phase 1: ML Service Layer (2 hours)

**Create `omics_oracle_v2/lib/services/ml_service.py`**

Centralized service for all ML operations:
- Initialize ML models (singleton pattern)
- Provide high-level ML operations
- Handle caching and performance optimization
- Error handling and graceful degradation

**Key Methods:**
```python
class MLService:
    async def predict_citations(publications: List[Publication]) -> List[CitationPrediction]
    async def get_recommendations(biomarker: str, strategy: str) -> List[Recommendation]
    async def forecast_trends(publications: List[Publication]) -> TrendForecast
    async def get_biomarker_analytics(biomarker: str) -> BiomarkerAnalytics
    async def enrich_search_results(publications: List[Publication]) -> List[EnrichedPublication]
```

### Phase 2: API Endpoints (3 hours)

**Create/Update API Routes:**

1. **Search Enhancement** (`routes/search.py`)
   - Add `/api/search/enhanced` endpoint
   - Integrate citation predictions
   - Add trend indicators
   - Return enriched results

2. **Recommendation Endpoints** (`routes/recommendations.py`)
   - `/api/recommend/similar`
   - `/api/recommend/emerging`
   - `/api/recommend/high-impact`
   - `/api/recommend/personalized`

3. **Prediction Endpoints** (`routes/predictions.py`)
   - `/api/predict/citations`
   - `/api/predict/trends`

4. **Analytics Endpoints** (`routes/analytics.py`)
   - `/api/analytics/biomarker/{name}`
   - `/api/analytics/trends`

### Phase 3: Response Models (1 hour)

**Create Pydantic Models** (`omics_oracle_v2/api/schemas/ml_schemas.py`)

```python
class CitationPredictionResponse(BaseModel):
    pmid: str
    predicted_citations: float
    confidence_interval: Tuple[float, float]
    confidence_score: float
    features_used: List[str]

class RecommendationResponse(BaseModel):
    biomarker: str
    score: float
    explanation: str
    related_publications: int
    key_factors: List[str]

class TrendForecastResponse(BaseModel):
    forecast_dates: List[str]
    predictions: List[float]
    confidence_intervals: List[Tuple[float, float]]
    trend_direction: str

class EnrichedPublicationResponse(BaseModel):
    # All Publication fields plus:
    predicted_citations: Optional[float]
    citation_confidence: Optional[float]
    trend_indicator: Optional[str]
    recommendation_score: Optional[float]
```

### Phase 4: Testing (2 hours)

**Integration Tests:**
- Test all new endpoints
- Test ML service integration
- Test caching behavior
- Test error handling
- Performance benchmarks

**Create `test_day29_integration.py`**

---

## API Specification

### 1. Enhanced Search

**Endpoint:** `GET /api/search/enhanced`

**Query Parameters:**
- `q`: Search query (required)
- `limit`: Number of results (default: 20)
- `include_predictions`: Include citation predictions (default: true)
- `include_trends`: Include trend indicators (default: true)

**Response:**
```json
{
  "query": "BRCA1 breast cancer",
  "total_results": 156,
  "results": [
    {
      "pmid": "12345678",
      "title": "BRCA1 mutations in breast cancer",
      "authors": ["Smith J", "Jones A"],
      "journal": "Nature",
      "publication_date": "2023-01-15",
      "citations": 45,
      "predicted_citations": 67.5,
      "citation_confidence": 0.85,
      "trend_indicator": "growing",
      "abstract": "..."
    }
  ],
  "search_time_ms": 145,
  "ml_processing_time_ms": 32
}
```

### 2. Similar Biomarker Recommendations

**Endpoint:** `GET /api/recommend/similar`

**Query Parameters:**
- `biomarker`: Source biomarker (required)
- `limit`: Number of recommendations (default: 10)

**Response:**
```json
{
  "query_biomarker": "BRCA1",
  "recommendations": [
    {
      "biomarker": "BRCA2",
      "score": 0.89,
      "similarity_score": 0.93,
      "trend_score": 0.75,
      "impact_score": 0.92,
      "explanation": "Highly similar research context, high citation impact",
      "related_publications": 156,
      "key_factors": ["similarity", "impact"]
    }
  ],
  "generation_time_ms": 23
}
```

### 3. Emerging Biomarkers

**Endpoint:** `GET /api/recommend/emerging`

**Query Parameters:**
- `field`: Research field filter (optional)
- `limit`: Number of results (default: 10)
- `min_growth_rate`: Minimum growth rate (default: 0.5)

**Response:**
```json
{
  "emerging_biomarkers": [
    {
      "biomarker": "circRNA",
      "score": 0.87,
      "trend_score": 0.95,
      "growth_rate": 2.3,
      "explanation": "Rapidly growing research area",
      "publications_last_year": 234,
      "yoy_growth": "230%"
    }
  ]
}
```

### 4. Citation Prediction

**Endpoint:** `POST /api/predict/citations`

**Request Body:**
```json
{
  "publications": [
    {
      "pmid": "12345678",
      "title": "Novel biomarker discovery",
      "authors": ["Smith J"],
      "journal": "Nature",
      "publication_date": "2023-01-15"
    }
  ]
}
```

**Response:**
```json
{
  "predictions": [
    {
      "pmid": "12345678",
      "predicted_citations": 67.5,
      "confidence_interval": [52.3, 82.7],
      "confidence_score": 0.85,
      "model_type": "random_forest",
      "features_used": ["journal_impact", "author_count", "recency"]
    }
  ],
  "processing_time_ms": 45
}
```

### 5. Biomarker Analytics

**Endpoint:** `GET /api/analytics/biomarker/{biomarker_name}`

**Response:**
```json
{
  "biomarker": "BRCA1",
  "total_publications": 3456,
  "total_citations": 125789,
  "avg_citations_per_pub": 36.4,
  "publication_trend": {
    "direction": "growing",
    "growth_rate": 0.15,
    "forecast_next_year": 450
  },
  "top_journals": [
    {"journal": "Nature", "count": 234},
    {"journal": "Cell", "count": 189}
  ],
  "similar_biomarkers": [
    {"name": "BRCA2", "similarity": 0.89}
  ],
  "research_areas": ["breast cancer", "genetics", "oncology"],
  "impact_metrics": {
    "h_index": 78,
    "i10_index": 156
  }
}
```

---

## Implementation Details

### ML Service Architecture

```python
# Singleton pattern for model initialization
class MLService:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def initialize(self):
        if self._initialized:
            return

        # Initialize models
        self.embedder = BiomarkerEmbedder()
        self.citation_predictor = CitationPredictor()
        self.trend_forecaster = TrendForecaster()
        self.recommender = BiomarkerRecommender(...)

        # Build indices
        await self._build_indices()

        self._initialized = True

    async def enrich_search_results(
        self,
        publications: List[Publication],
        include_predictions: bool = True,
        include_trends: bool = True
    ) -> List[EnrichedPublication]:
        """Add ML predictions to search results."""
        enriched = []

        if include_predictions:
            # Batch predict citations
            predictions = await self.predict_citations_batch(publications)

        for pub in publications:
            enriched_pub = EnrichedPublication(**pub.dict())

            if include_predictions:
                pred = predictions.get(pub.pmid)
                enriched_pub.predicted_citations = pred.predicted_citations
                enriched_pub.citation_confidence = pred.confidence_score

            if include_trends:
                enriched_pub.trend_indicator = self._get_trend_indicator(pub)

            enriched.append(enriched_pub)

        return enriched
```

### Caching Strategy

**Cache Keys:**
- `ml:citation_prediction:{pmid}` (TTL: 7 days)
- `ml:recommendations:{biomarker}:{strategy}` (TTL: 1 day)
- `ml:embeddings:{entity_type}:{entity_id}` (TTL: 7 days)
- `ml:trends:{biomarker}` (TTL: 1 day)

**Cache Invalidation:**
- New publications added → Invalidate recommendation cache
- Model retrained → Invalidate all prediction caches
- Manual invalidation endpoint for admin

---

## Performance Targets

### Response Times:
- **Enhanced Search**: <300ms (including ML)
- **Recommendations**: <150ms (cached) / <500ms (uncached)
- **Citation Predictions**: <100ms for 10 publications
- **Trend Forecasting**: <200ms
- **Analytics**: <500ms (comprehensive data)

### Throughput:
- **Concurrent Requests**: 100+ req/s
- **Cache Hit Rate**: >80%
- **Error Rate**: <0.1%

### Resource Usage:
- **Memory**: <2GB for ML models
- **CPU**: <50% avg utilization
- **Redis**: <500MB cache size

---

## Error Handling

### Graceful Degradation:
1. **ML Model Unavailable**: Return results without predictions
2. **Timeout**: Return partial results with timeout indicator
3. **Cache Miss**: Fall back to model inference
4. **Invalid Input**: Return clear error messages

### Error Response Format:
```json
{
  "error": {
    "code": "ML_SERVICE_UNAVAILABLE",
    "message": "ML predictions temporarily unavailable",
    "fallback": "results_without_ml",
    "retry_after_ms": 5000
  }
}
```

---

## Testing Strategy

### Unit Tests:
- Test ML service methods
- Test API endpoint handlers
- Test response model validation
- Test error handling

### Integration Tests:
- End-to-end API tests
- Database + ML integration
- Cache behavior tests
- Performance benchmarks

### Load Tests:
- Concurrent request handling
- Cache performance under load
- Memory usage under load

---

## Success Criteria

### Must Have:
- [x] ML service layer implemented ✅
- [x] Enhanced search endpoint working ✅
- [x] Recommendation endpoints working ✅
- [x] Caching integrated ✅
- [x] Error handling robust ✅
- [x] Tests passing ✅

### Should Have:
- [ ] Citation prediction endpoint
- [ ] Trend forecasting endpoint
- [ ] Analytics endpoint
- [ ] Performance optimized

### Nice to Have:
- [ ] Real-time model updates
- [ ] A/B testing framework
- [ ] Usage analytics
- [ ] Admin dashboard

---

## Timeline

**Total Time:** 8 hours

- **Hours 0-2**: ML Service Layer
  - Create MLService class
  - Initialize models
  - Implement core methods

- **Hours 2-5**: API Endpoints
  - Enhanced search
  - Recommendations
  - Predictions
  - Analytics

- **Hours 5-6**: Response Models
  - Pydantic schemas
  - Validation
  - Documentation

- **Hours 6-8**: Testing & Optimization
  - Integration tests
  - Performance benchmarks
  - Bug fixes

---

## Files to Create/Modify

### New Files:
- `omics_oracle_v2/lib/services/ml_service.py` - ML service layer
- `omics_oracle_v2/api/routes/recommendations.py` - Recommendation endpoints
- `omics_oracle_v2/api/routes/predictions.py` - Prediction endpoints
- `omics_oracle_v2/api/routes/analytics.py` - Analytics endpoints
- `omics_oracle_v2/api/schemas/ml_schemas.py` - ML response models
- `test_day29_integration.py` - Integration tests

### Modified Files:
- `omics_oracle_v2/api/routes/search.py` - Add enhanced search
- `omics_oracle_v2/api/main.py` - Register new routes
- `omics_oracle_v2/lib/services/__init__.py` - Export ML service

---

## Next Steps After Day 29

**Day 30:** Production Deployment & Final Polish
- Production configuration
- Security hardening
- Documentation finalization
- Deployment scripts
- Performance monitoring

---

**Status:** READY TO IMPLEMENT
**Next:** Create ML Service Layer
