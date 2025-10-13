"""
Trend forecasting for biomedical research.

Forecasts:
- Publication volume trends
- Citation trends
- Emerging topics
- Research momentum
"""

import logging
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.holtwinters import ExponentialSmoothing

from omics_oracle_v2.lib.publications.models import Publication

# Prophet available but not currently used
# try:
#     from prophet import Prophet
#     HAS_PROPHET = True
# except ImportError:
#     HAS_PROPHET = False


logger = logging.getLogger(__name__)


@dataclass
class ForecastResult:
    """Time series forecast result."""

    predictions: List[float]
    confidence_intervals: List[Tuple[float, float]]
    trend_direction: str  # 'increasing', 'decreasing', 'stable'
    forecast_dates: List[str]
    model_type: str


@dataclass
class EmergingTopic:
    """Emerging research topic."""

    topic: str
    growth_rate: float
    momentum_score: float
    recent_count: int
    historical_avg: float
    related_papers: List[str]  # PMIDs


@dataclass
class TrendAnalysis:
    """Comprehensive trend analysis."""

    topic: str
    historical_trend: List[Tuple[str, int]]  # (date, count) pairs
    forecast: Optional[ForecastResult]
    peak_periods: List[str]
    growth_phases: List[Dict[str, any]]
    current_momentum: float


class TrendForecaster:
    """Forecast research trends and identify emerging topics."""

    def __init__(self, min_data_points: int = 12):
        """
        Initialize trend forecaster.

        Args:
            min_data_points: Minimum data points needed for forecasting
        """
        self.min_data_points = min_data_points

    def forecast_publication_volume(
        self,
        publications: List[Publication],
        months_ahead: int = 12,
        method: str = "auto",
    ) -> ForecastResult:
        """
        Forecast publication volume trends.

        Args:
            publications: Historical publications
            months_ahead: Number of months to forecast
            method: Forecasting method ('auto', 'arima', 'exponential')

        Returns:
            Forecast results with confidence intervals
        """
        # Prepare time series data
        time_series = self._prepare_time_series(publications, freq="M")

        if len(time_series) < self.min_data_points:
            logger.warning(
                f"Insufficient data for forecasting: {len(time_series)} points "
                f"(minimum {self.min_data_points})"
            )
            return self._create_simple_forecast(time_series, months_ahead)

        # Choose forecasting method
        if method == "auto":
            method = "exponential" if len(time_series) < 36 else "arima"

        # Perform forecasting
        if method == "arima":
            return self._forecast_arima(time_series, months_ahead)
        elif method == "exponential":
            return self._forecast_exponential(time_series, months_ahead)
        else:
            return self._create_simple_forecast(time_series, months_ahead)

    def forecast_citation_trend(
        self,
        publications: List[Publication],
        biomarker: str,
        months_ahead: int = 12,
    ) -> ForecastResult:
        """
        Forecast citation trends for a specific biomarker.

        Args:
            publications: Publications mentioning the biomarker
            biomarker: Biomarker name
            months_ahead: Months to forecast

        Returns:
            Citation trend forecast
        """
        # Filter publications by biomarker
        relevant_pubs = [
            p for p in publications if biomarker.lower() in (p.title + " " + (p.abstract or "")).lower()
        ]

        if not relevant_pubs:
            logger.warning(f"No publications found for biomarker: {biomarker}")
            return self._create_empty_forecast(months_ahead)

        # Aggregate citations by month
        citation_series = self._prepare_citation_time_series(relevant_pubs)

        if len(citation_series) < self.min_data_points:
            return self._create_simple_forecast(citation_series, months_ahead)

        return self._forecast_exponential(citation_series, months_ahead)

    def detect_emerging_topics(
        self,
        publications: List[Publication],
        min_growth_rate: float = 0.5,
        top_n: int = 10,
    ) -> List[EmergingTopic]:
        """
        Detect emerging research topics.

        Args:
            publications: Recent publications
            min_growth_rate: Minimum growth rate to consider (0.5 = 50% growth)
            top_n: Number of top emerging topics to return

        Returns:
            List of emerging topics sorted by momentum
        """
        # Extract keywords/topics from publications
        topics = self._extract_topics(publications)

        # Calculate growth rates
        emerging = []

        for topic, time_series in topics.items():
            if len(time_series) < 6:  # Need at least 6 months of data
                continue

            # Calculate growth metrics
            recent_count = sum(time_series[-3:])  # Last 3 months
            historical_avg = np.mean(time_series[:-3]) if len(time_series) > 3 else 0

            if historical_avg == 0:
                growth_rate = float("inf") if recent_count > 0 else 0
            else:
                growth_rate = (recent_count - historical_avg) / historical_avg

            # Calculate momentum (velocity + acceleration)
            if len(time_series) >= 6:
                velocity = np.mean(np.diff(time_series[-6:]))
                acceleration = np.mean(np.diff(np.diff(time_series[-6:])))
                momentum = velocity + 0.5 * acceleration
            else:
                momentum = growth_rate

            if growth_rate >= min_growth_rate:
                # Find related papers
                related_pmids = self._find_related_papers(publications, topic)

                emerging.append(
                    EmergingTopic(
                        topic=topic,
                        growth_rate=growth_rate,
                        momentum_score=momentum,
                        recent_count=int(recent_count),
                        historical_avg=float(historical_avg),
                        related_papers=related_pmids[:5],  # Top 5 recent papers
                    )
                )

        # Sort by momentum score
        emerging.sort(key=lambda x: x.momentum_score, reverse=True)

        return emerging[:top_n]

    def analyze_biomarker_trajectory(self, publications: List[Publication], biomarker: str) -> TrendAnalysis:
        """
        Comprehensive trajectory analysis for a biomarker.

        Args:
            publications: Publications mentioning the biomarker
            biomarker: Biomarker name

        Returns:
            Complete trend analysis
        """
        # Filter relevant publications
        relevant_pubs = [
            p for p in publications if biomarker.lower() in (p.title + " " + (p.abstract or "")).lower()
        ]

        # Historical trend
        time_series = self._prepare_time_series(relevant_pubs, freq="M")
        historical = [
            (date, count)
            for date, count in zip(
                pd.date_range(end=datetime.now(), periods=len(time_series), freq="M").strftime("%Y-%m"),
                time_series,
            )
        ]

        # Forecast
        forecast = None
        if len(time_series) >= self.min_data_points:
            forecast = self._forecast_exponential(time_series, periods=12)

        # Detect peaks
        peaks = self._detect_peaks(time_series)
        peak_dates = [
            pd.date_range(end=datetime.now(), periods=len(time_series), freq="M").strftime("%Y-%m")[i]
            for i in peaks
        ]

        # Growth phases
        phases = self._identify_growth_phases(time_series)

        # Current momentum
        momentum = self._calculate_momentum(time_series)

        return TrendAnalysis(
            topic=biomarker,
            historical_trend=historical,
            forecast=forecast,
            peak_periods=peak_dates,
            growth_phases=phases,
            current_momentum=momentum,
        )

    def _prepare_time_series(self, publications: List[Publication], freq: str = "M") -> np.ndarray:
        """Prepare time series from publications."""
        # Group publications by time period
        pub_dates = []
        for pub in publications:
            if pub.publication_date:
                # Use year-month from publication_date
                pub_dates.append(pub.publication_date.strftime("%Y-%m"))

        if not pub_dates:
            return np.array([])

        # Count publications per period
        date_counts = Counter(pub_dates)

        # Create continuous time series
        dates = pd.date_range(start=min(pub_dates), end=datetime.now().strftime("%Y-%m"), freq=freq)

        time_series = [date_counts.get(date.strftime("%Y-%m"), 0) for date in dates]

        return np.array(time_series, dtype=np.float64)

    def _prepare_citation_time_series(self, publications: List[Publication]) -> np.ndarray:
        """Prepare citation time series."""
        # Group citations by publication year
        year_citations = defaultdict(int)

        for pub in publications:
            if pub.publication_date and pub.citations:
                year = pub.publication_date.year
                year_citations[year] += pub.citations

        if not year_citations:
            return np.array([])

        # Create continuous series
        min_year = min(year_citations.keys())
        max_year = datetime.now().year

        time_series = [year_citations.get(year, 0) for year in range(min_year, max_year + 1)]

        return np.array(time_series, dtype=np.float64)

    def _forecast_arima(self, time_series: np.ndarray, periods: int) -> ForecastResult:
        """Forecast using ARIMA model."""
        try:
            # Fit ARIMA model (auto-select parameters in real implementation)
            model = ARIMA(time_series, order=(1, 1, 1))
            fitted = model.fit()

            # Forecast
            forecast = fitted.forecast(steps=periods)
            conf_int = fitted.get_forecast(steps=periods).conf_int()

            # Determine trend
            trend = self._determine_trend(forecast)

            # Generate forecast dates
            forecast_dates = (
                pd.date_range(start=datetime.now(), periods=periods, freq="M").strftime("%Y-%m").tolist()
            )

            return ForecastResult(
                predictions=forecast.tolist(),
                confidence_intervals=[
                    (float(conf_int.iloc[i, 0]), float(conf_int.iloc[i, 1])) for i in range(len(conf_int))
                ],
                trend_direction=trend,
                forecast_dates=forecast_dates,
                model_type="ARIMA",
            )

        except Exception as e:
            logger.warning(f"ARIMA forecasting failed: {e}, using simple method")
            return self._create_simple_forecast(time_series, periods)

    def _forecast_exponential(self, time_series: np.ndarray, periods: int) -> ForecastResult:
        """Forecast using exponential smoothing."""
        try:
            # Fit exponential smoothing model
            model = ExponentialSmoothing(time_series, seasonal_periods=12, trend="add", seasonal="add")
            fitted = model.fit()

            # Forecast
            forecast = fitted.forecast(steps=periods)

            # Simple confidence intervals (+/- 20%)
            conf_int = [(max(0, f * 0.8), f * 1.2) for f in forecast]

            # Determine trend
            trend = self._determine_trend(forecast)

            # Generate forecast dates
            forecast_dates = (
                pd.date_range(start=datetime.now(), periods=periods, freq="M").strftime("%Y-%m").tolist()
            )

            return ForecastResult(
                predictions=forecast.tolist(),
                confidence_intervals=conf_int,
                trend_direction=trend,
                forecast_dates=forecast_dates,
                model_type="Exponential Smoothing",
            )

        except Exception as e:
            logger.warning(f"Exponential smoothing failed: {e}, using simple method")
            return self._create_simple_forecast(time_series, periods)

    def _create_simple_forecast(self, time_series: np.ndarray, periods: int) -> ForecastResult:
        """Create simple forecast using moving average."""
        if len(time_series) == 0:
            return self._create_empty_forecast(periods)

        # Use last 3 points average as baseline
        baseline = np.mean(time_series[-3:]) if len(time_series) >= 3 else np.mean(time_series)

        # Simple linear trend
        if len(time_series) >= 3:
            trend_slope = (time_series[-1] - time_series[-3]) / 3
        else:
            trend_slope = 0

        # Generate predictions
        predictions = [baseline + trend_slope * i for i in range(1, periods + 1)]

        # Confidence intervals (+/- 30%)
        conf_int = [(max(0, p * 0.7), p * 1.3) for p in predictions]

        # Determine trend
        trend = "increasing" if trend_slope > 0.1 else ("decreasing" if trend_slope < -0.1 else "stable")

        # Generate forecast dates
        forecast_dates = (
            pd.date_range(start=datetime.now(), periods=periods, freq="M").strftime("%Y-%m").tolist()
        )

        return ForecastResult(
            predictions=predictions,
            confidence_intervals=conf_int,
            trend_direction=trend,
            forecast_dates=forecast_dates,
            model_type="Simple Moving Average",
        )

    def _create_empty_forecast(self, periods: int) -> ForecastResult:
        """Create empty forecast when no data available."""
        forecast_dates = (
            pd.date_range(start=datetime.now(), periods=periods, freq="M").strftime("%Y-%m").tolist()
        )

        return ForecastResult(
            predictions=[0.0] * periods,
            confidence_intervals=[(0.0, 0.0)] * periods,
            trend_direction="stable",
            forecast_dates=forecast_dates,
            model_type="No Data",
        )

    def _determine_trend(self, forecast: np.ndarray) -> str:
        """Determine trend direction from forecast."""
        if len(forecast) < 2:
            return "stable"

        # Calculate overall trend
        slope = (forecast[-1] - forecast[0]) / len(forecast)

        if slope > 0.1:
            return "increasing"
        elif slope < -0.1:
            return "decreasing"
        else:
            return "stable"

    def _extract_topics(self, publications: List[Publication]) -> Dict[str, List[int]]:
        """Extract topics and their time series."""
        # Simple keyword extraction (in real implementation, use NLP)
        topic_timeline = defaultdict(lambda: defaultdict(int))

        for pub in publications:
            if not pub.publication_date:
                continue

            year = pub.publication_date.year

            # Extract keywords from title (simple approach)
            if pub.title:
                words = pub.title.lower().split()
                # Filter for significant terms (>4 characters, not common words)
                keywords = [
                    w.strip(".,;:!?")
                    for w in words
                    if len(w) > 4 and w not in {"their", "these", "those", "using", "based"}
                ]

                for keyword in keywords:
                    topic_timeline[keyword][year] += 1

        # Convert to time series
        topics = {}
        current_year = datetime.now().year

        for topic, year_counts in topic_timeline.items():
            if len(year_counts) < 3:  # Need at least 3 years
                continue

            min_year = min(year_counts.keys())
            time_series = [
                year_counts.get(year, 0) for year in range(max(min_year, current_year - 5), current_year + 1)
            ]

            if sum(time_series) >= 5:  # At least 5 total occurrences
                topics[topic] = time_series

        return topics

    def _find_related_papers(self, publications: List[Publication], topic: str) -> List[str]:
        """Find papers related to a topic."""
        related = []

        for pub in publications:
            if topic.lower() in (pub.title or "").lower():
                if pub.pmid:
                    related.append(pub.pmid)

        # Sort by year (most recent first)
        related_pubs = [p for p in publications if p.pmid in related]
        related_pubs.sort(key=lambda x: x.year or 0, reverse=True)

        return [p.pmid for p in related_pubs]

    def _detect_peaks(self, time_series: np.ndarray) -> List[int]:
        """Detect peak periods in time series."""
        if len(time_series) < 3:
            return []

        peaks = []
        for i in range(1, len(time_series) - 1):
            if time_series[i] > time_series[i - 1] and time_series[i] > time_series[i + 1]:
                peaks.append(i)

        return peaks

    def _identify_growth_phases(self, time_series: np.ndarray) -> List[Dict[str, any]]:
        """Identify growth/decline phases."""
        if len(time_series) < 4:
            return []

        phases = []
        current_phase = None
        phase_start = 0

        for i in range(1, len(time_series)):
            trend = "growth" if time_series[i] > time_series[i - 1] else "decline"

            if current_phase != trend:
                if current_phase is not None:
                    phases.append(
                        {
                            "type": current_phase,
                            "start_index": phase_start,
                            "end_index": i - 1,
                            "duration": i - phase_start,
                        }
                    )
                current_phase = trend
                phase_start = i

        # Add final phase
        if current_phase:
            phases.append(
                {
                    "type": current_phase,
                    "start_index": phase_start,
                    "end_index": len(time_series) - 1,
                    "duration": len(time_series) - phase_start,
                }
            )

        return phases

    def _calculate_momentum(self, time_series: np.ndarray) -> float:
        """Calculate current momentum score."""
        if len(time_series) < 3:
            return 0.0

        # Velocity (recent slope)
        recent = time_series[-3:]
        velocity = np.mean(np.diff(recent))

        # Acceleration (change in slope)
        if len(time_series) >= 6:
            acceleration = np.mean(np.diff(np.diff(time_series[-6:])))
        else:
            acceleration = 0

        # Combined momentum
        momentum = velocity + 0.5 * acceleration

        return float(momentum)
