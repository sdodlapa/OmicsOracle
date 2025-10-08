# Day 27: ML Features - Citation Prediction & Trend Forecasting

**Date:** October 7, 2025
**Status:** IN PROGRESS
**Goal:** Implement ML-based citation prediction and trend forecasting

---

## Overview

Day 27 adds predictive ML capabilities to OmicsOracle:
- **Citation Prediction**: Forecast future citation counts for publications
- **Trend Forecasting**: Predict research trends and emerging topics
- **Feature Engineering**: Extract meaningful features from publication metadata

---

## Phase 1: Citation Prediction (5-6 hours)

### Objective
Build ML model to predict citation count with 75%+ accuracy

### Tasks

#### Task 1: Feature Extraction (1.5 hours)
**File:** `omics_oracle_v2/lib/ml/features.py`

**Features to Extract:**
1. **Journal Features:**
   - Journal impact factor (if available)
   - Journal category
   - Publication type (research, review, etc.)

2. **Temporal Features:**
   - Publication year
   - Months since publication
   - Publication quarter/season

3. **Author Features:**
   - Number of authors
   - Author collaboration network size
   - First/last author previous citations (if available)

4. **Content Features:**
   - Abstract length
   - Title length
   - Number of keywords
   - MeSH term count
   - Reference count

5. **Metadata Features:**
   - Has full-text available
   - Has DOI
   - Open access status

**Output:** Feature vector for each publication

#### Task 2: Model Training (2 hours)
**File:** `omics_oracle_v2/lib/ml/citation_predictor.py`

**Models to Try:**
1. **Baseline:** Linear Regression
2. **Tree-based:** Random Forest, XGBoost
3. **Ensemble:** Stacking/Voting

**Training Strategy:**
- Use historical citation data
- Train/validation/test split: 70/15/15
- Cross-validation (5-fold)
- Hyperparameter tuning

**Evaluation Metrics:**
- RMSE (Root Mean Squared Error)
- MAE (Mean Absolute Error)
- R² Score
- Accuracy bins (low/medium/high citations)

#### Task 3: API Implementation (1 hour)
**File:** `omics_oracle_v2/lib/ml/citation_predictor.py`

**API Methods:**
```python
class CitationPredictor:
    def predict_citations(self, publication: Publication) -> CitationPrediction
    def predict_batch(self, publications: List[Publication]) -> List[CitationPrediction]
    def get_feature_importance(self) -> Dict[str, float]
    def evaluate_model(self) -> ModelMetrics
```

**CitationPrediction Model:**
- predicted_citations: int
- confidence_interval: Tuple[int, int]
- confidence_score: float (0-1)
- prediction_date: datetime
- features_used: List[str]

#### Task 4: Testing (1 hour)
**File:** `tests/lib/ml/test_citation_predictor.py`

**Tests:**
- Feature extraction accuracy
- Model prediction format
- Batch prediction performance
- Feature importance extraction
- Model persistence (save/load)

---

## Phase 2: Trend Forecasting (4-5 hours)

### Objective
Forecast research trends and identify emerging topics with 70%+ precision

### Tasks

#### Task 1: Time Series Analysis (2 hours)
**File:** `omics_oracle_v2/lib/ml/trend_forecaster.py`

**Analyses:**
1. **Publication Volume Trends:**
   - Publications per month/year
   - Growth rate analysis
   - Seasonality detection

2. **Citation Trends:**
   - Total citations over time
   - Citation velocity (citations per month)
   - Citation acceleration

3. **Topic Trends:**
   - Keyword frequency over time
   - MeSH term evolution
   - Emerging keyword detection

**Methods:**
- Moving averages
- ARIMA/SARIMA models
- Prophet (Facebook's time series forecasting)
- Trend decomposition

#### Task 2: Emerging Topic Detection (1.5 hours)
**File:** `omics_oracle_v2/lib/ml/trend_forecaster.py`

**Detection Methods:**
1. **Keyword Analysis:**
   - Sudden increase in keyword frequency
   - New keyword combinations
   - Cross-reference with recent high-impact papers

2. **Topic Modeling:**
   - LDA (Latent Dirichlet Allocation)
   - Track topic evolution
   - Identify splitting/merging topics

3. **Trend Metrics:**
   - Growth rate (% increase)
   - Momentum score
   - Peak detection
   - Trend sustainability prediction

#### Task 3: API Implementation (1 hour)
**File:** `omics_oracle_v2/lib/ml/trend_forecaster.py`

**API Methods:**
```python
class TrendForecaster:
    def forecast_publication_volume(self, months_ahead: int) -> ForecastResult
    def forecast_citation_trend(self, biomarker: str, months_ahead: int) -> ForecastResult
    def detect_emerging_topics(self, min_growth_rate: float = 0.5) -> List[EmergingTopic]
    def analyze_biomarker_trajectory(self, biomarker: str) -> TrendAnalysis
```

**Models:**
- ForecastResult: predictions, confidence_intervals, trend_direction
- EmergingTopic: topic, growth_rate, momentum_score, related_papers
- TrendAnalysis: historical_trend, forecast, peak_periods, related_topics

#### Task 4: Testing (1 hour)
**File:** `tests/lib/ml/test_trend_forecaster.py`

**Tests:**
- Time series forecasting accuracy
- Emerging topic detection
- Trend analysis completeness
- Model robustness with sparse data

---

## Implementation Details

### Directory Structure
```
omics_oracle_v2/lib/ml/
├── __init__.py
├── features.py              # Feature extraction
├── citation_predictor.py    # Citation prediction model
├── trend_forecaster.py      # Trend forecasting
└── models/                  # Saved ML models
    ├── citation_model.pkl
    └── trend_model.pkl

tests/lib/ml/
├── __init__.py
├── test_features.py
├── test_citation_predictor.py
└── test_trend_forecaster.py
```

### Dependencies
```bash
# Install ML libraries
pip install scikit-learn==1.3.0
pip install xgboost==2.0.0
pip install prophet==1.1.4
pip install statsmodels==0.14.0
```

### Data Requirements

**For Citation Prediction:**
- Historical publication data with citation counts
- At least 1000 publications for training
- Publications spanning multiple years

**For Trend Forecasting:**
- Time-series publication data (monthly/yearly)
- Keyword/MeSH term frequencies over time
- Citation data over time

---

## Success Criteria

### Citation Prediction
- [ ] Model accuracy > 75% (R² score)
- [ ] RMSE < 20 citations for papers with <100 citations
- [ ] Feature extraction working for all publications
- [ ] Prediction API functional
- [ ] Batch prediction < 1 second per 100 publications
- [ ] All tests passing

### Trend Forecasting
- [ ] Forecast precision > 70% (within 20% of actual)
- [ ] Emerging topics detected with 80%+ relevance
- [ ] Time series analysis working
- [ ] API functional
- [ ] All tests passing

### Code Quality
- [ ] Type hints throughout
- [ ] Comprehensive docstrings
- [ ] Error handling
- [ ] Input validation
- [ ] Model versioning

---

## Timeline

**Morning (9 AM - 1 PM): Citation Prediction**
- 9:00 - 10:30: Feature extraction implementation
- 10:30 - 12:30: Model training and tuning
- 12:30 - 1:00: API implementation

**Afternoon (2 PM - 6 PM): Trend Forecasting**
- 2:00 - 4:00: Time series analysis implementation
- 4:00 - 5:30: Emerging topic detection
- 5:30 - 6:00: API implementation

**Evening (6 PM - 7 PM): Testing**
- 6:00 - 7:00: Comprehensive testing and validation

**Total: ~8 hours**

---

## Expected Deliverables

### Code
- `features.py` (~200 lines)
- `citation_predictor.py` (~300 lines)
- `trend_forecaster.py` (~350 lines)
- **Total: ~850 lines**

### Tests
- `test_features.py` (~150 lines)
- `test_citation_predictor.py` (~200 lines)
- `test_trend_forecaster.py` (~200 lines)
- **Total: ~550 lines**

### Models
- Trained citation prediction model
- Trend forecasting models
- Model evaluation reports

### Documentation
- Feature engineering guide
- Model performance metrics
- API usage examples

---

## Risk Mitigation

**Risk:** Limited historical data for training
**Mitigation:** Use cross-validation, synthetic data augmentation

**Risk:** Model overfitting
**Mitigation:** Regularization, cross-validation, feature selection

**Risk:** Slow prediction time
**Mitigation:** Model optimization, caching, batch processing

**Risk:** Poor accuracy on edge cases
**Mitigation:** Ensemble methods, confidence intervals, fallback predictions

---

## Integration Points

### With Week 3 Components:
- Use `Publication` objects from search pipeline
- Access citation data from citation analyzer
- Use temporal data from trend analyzer

### With Day 23-24 Dashboard:
- Add ML prediction panel
- Show trend forecasts in visualizations
- Display emerging topics

### With Day 26 Caching:
- Cache prediction results (24 hour TTL)
- Cache trend forecasts (1 week TTL)
- Cache model inference results

---

## Next Steps (Day 28)

After Day 27 completion:
- Biomarker embeddings and similarity search
- Recommendation engine
- Cross-disease pattern discovery

---

**Status:** Ready to begin implementation!
**Start Time:** Now
**Expected Completion:** End of day (~8 hours)
