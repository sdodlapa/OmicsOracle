"""
Citation count prediction using ML models.

Predicts future citation counts for publications based on:
- Publication metadata
- Author information
- Content features
- Temporal patterns
"""

import logging
import pickle
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import cross_val_score, train_test_split

try:
    import xgboost as xgb

    HAS_XGBOOST = True
except Exception:  # noqa: E722
    # XGBoost might fail to load due to missing OpenMP or other issues
    HAS_XGBOOST = False
    xgb = None

from omics_oracle_v2.lib.ml.features import FeatureExtractor
from omics_oracle_v2.lib.publications.models import Publication

logger = logging.getLogger(__name__)


@dataclass
class CitationPrediction:
    """Citation prediction result."""

    predicted_citations: float
    confidence_interval: Tuple[float, float]
    confidence_score: float
    prediction_date: datetime
    features_used: List[str]
    model_type: str


@dataclass
class ModelMetrics:
    """Model evaluation metrics."""

    rmse: float
    mae: float
    r2_score: float
    cross_val_scores: List[float]
    feature_importance: Dict[str, float]


class CitationPredictor:
    """ML model for predicting citation counts."""

    def __init__(
        self,
        model_type: str = "random_forest",
        model_path: Optional[Path] = None,
    ):
        """
        Initialize citation predictor.

        Args:
            model_type: Type of model ('linear', 'random_forest', 'xgboost')
            model_path: Path to save/load model
        """
        self.model_type = model_type
        self.model_path = model_path or Path("omics_oracle_v2/lib/ml/models")
        self.model = None
        self.feature_extractor = FeatureExtractor()
        self.feature_names = None
        self.is_trained = False

    def train(
        self,
        publications: List[Publication],
        test_size: float = 0.15,
        random_state: int = 42,
    ) -> ModelMetrics:
        """
        Train the citation prediction model.

        Args:
            publications: List of publications with known citation counts
            test_size: Fraction of data for testing
            random_state: Random seed for reproducibility

        Returns:
            Model evaluation metrics
        """
        logger.info(f"Training {self.model_type} model on {len(publications)} publications")

        # Extract features
        X, y = self._prepare_training_data(publications)

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )

        # Initialize model
        self.model = self._create_model()

        # Train model
        self.model.fit(X_train, y_train)
        self.is_trained = True

        # Evaluate
        y_pred = self.model.predict(X_test)

        metrics = ModelMetrics(
            rmse=np.sqrt(mean_squared_error(y_test, y_pred)),
            mae=mean_absolute_error(y_test, y_pred),
            r2_score=r2_score(y_test, y_pred),
            cross_val_scores=cross_val_score(self.model, X_train, y_train, cv=5, scoring="r2").tolist(),
            feature_importance=self._get_feature_importance(),
        )

        logger.info(
            f"Model trained: R2={metrics.r2_score:.3f}, " f"RMSE={metrics.rmse:.2f}, MAE={metrics.mae:.2f}"
        )

        return metrics

    def predict_citations(self, publication: Publication) -> CitationPrediction:
        """
        Predict citation count for a single publication.

        Args:
            publication: Publication to predict for

        Returns:
            Citation prediction with confidence interval
        """
        if not self.is_trained:
            raise ValueError("Model not trained. Call train() first.")

        # Extract features
        features = self.feature_extractor.extract_features(publication)
        X = self.feature_extractor.features_to_array(features, self.feature_names)
        X = X.reshape(1, -1)

        # Predict
        pred = self.model.predict(X)[0]

        # Estimate confidence interval (simple approach)
        # For tree-based models, use prediction std from trees
        if hasattr(self.model, "estimators_"):
            # Random Forest or XGBoost with multiple estimators
            predictions = np.array([tree.predict(X)[0] for tree in self.model.estimators_])
            std = np.std(predictions)
            ci = (max(0, pred - 1.96 * std), pred + 1.96 * std)
            confidence = 1.0 - (std / (pred + 1))  # Higher confidence = lower std
        else:
            # Linear model - use simple 20% confidence interval
            ci = (max(0, pred * 0.8), pred * 1.2)
            confidence = 0.7

        return CitationPrediction(
            predicted_citations=max(0, pred),
            confidence_interval=ci,
            confidence_score=min(1.0, max(0.0, confidence)),
            prediction_date=datetime.now(),
            features_used=self.feature_names,
            model_type=self.model_type,
        )

    def predict_batch(self, publications: List[Publication]) -> List[CitationPrediction]:
        """
        Predict citations for multiple publications.

        Args:
            publications: List of publications

        Returns:
            List of citation predictions
        """
        return [self.predict_citations(pub) for pub in publications]

    def get_feature_importance(self) -> Dict[str, float]:
        """
        Get feature importance scores.

        Returns:
            Dictionary of feature_name -> importance_score
        """
        return self._get_feature_importance()

    def save_model(self, path: Optional[Path] = None) -> None:
        """
        Save trained model to disk.

        Args:
            path: Path to save model (uses default if None)
        """
        if not self.is_trained:
            raise ValueError("Cannot save untrained model")

        save_path = path or (self.model_path / f"{self.model_type}_citation_model.pkl")
        save_path.parent.mkdir(parents=True, exist_ok=True)

        model_data = {
            "model": self.model,
            "model_type": self.model_type,
            "feature_names": self.feature_names,
            "is_trained": self.is_trained,
        }

        with open(save_path, "wb") as f:
            pickle.dump(model_data, f)

        logger.info(f"Model saved to {save_path}")

    def load_model(self, path: Optional[Path] = None) -> None:
        """
        Load trained model from disk.

        Args:
            path: Path to load model from (uses default if None)
        """
        load_path = path or (self.model_path / f"{self.model_type}_citation_model.pkl")

        if not load_path.exists():
            raise FileNotFoundError(f"Model file not found: {load_path}")

        with open(load_path, "rb") as f:
            model_data = pickle.load(f)

        self.model = model_data["model"]
        self.model_type = model_data["model_type"]
        self.feature_names = model_data["feature_names"]
        self.is_trained = model_data["is_trained"]

        logger.info(f"Model loaded from {load_path}")

    def _prepare_training_data(self, publications: List[Publication]) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare X (features) and y (targets) for training."""
        # Extract features
        features_list = self.feature_extractor.extract_features_batch(publications)

        # Get feature names from first publication
        self.feature_names = sorted(features_list[0].keys())

        # Convert to arrays
        X = np.array([self.feature_extractor.features_to_array(f, self.feature_names) for f in features_list])

        # Get citation counts as targets
        y = np.array(
            [pub.citation_count if hasattr(pub, "citation_count") else 0 for pub in publications],
            dtype=np.float32,
        )

        logger.info(f"Prepared training data: X shape={X.shape}, y shape={y.shape}")

        return X, y

    def _create_model(self) -> Any:
        """Create ML model based on model_type."""
        if self.model_type == "linear":
            return LinearRegression()

        elif self.model_type == "random_forest":
            return RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                random_state=42,
                n_jobs=-1,
            )

        elif self.model_type == "xgboost":
            if not HAS_XGBOOST:
                logger.warning("XGBoost not installed, falling back to Random Forest")
                return RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)

            return xgb.XGBRegressor(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42,
                n_jobs=-1,
            )

        else:
            raise ValueError(f"Unknown model type: {self.model_type}")

    def _get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance from trained model."""
        if not self.is_trained or self.feature_names is None:
            return {}

        if hasattr(self.model, "feature_importances_"):
            # Tree-based models
            importances = self.model.feature_importances_
        elif hasattr(self.model, "coef_"):
            # Linear models
            importances = np.abs(self.model.coef_)
        else:
            return {}

        # Normalize to sum to 1
        importances = importances / np.sum(importances)

        # Create readable names
        readable_names = self.feature_extractor.get_feature_importance_names()

        # Sort by importance
        importance_dict = {
            readable_names.get(name, name): float(imp) for name, imp in zip(self.feature_names, importances)
        }

        return dict(sorted(importance_dict.items(), key=lambda x: x[1], reverse=True))
