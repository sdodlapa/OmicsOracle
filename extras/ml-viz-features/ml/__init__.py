"""
Machine Learning module for OmicsOracle.

Provides ML-based features:
- Citation prediction
- Trend forecasting
- Feature extraction
- Biomarker recommendations
"""

from omics_oracle_v2.lib.ml.citation_predictor import CitationPredictor
from omics_oracle_v2.lib.ml.features import FeatureExtractor
from omics_oracle_v2.lib.ml.trend_forecaster import TrendForecaster

__all__ = [
    "CitationPredictor",
    "FeatureExtractor",
    "TrendForecaster",
]
