"""
ML API Response Models

Pydantic models for ML-enhanced API responses.
"""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class CitationPredictionResponse(BaseModel):
    """Citation prediction for a publication."""

    model_config = {"protected_namespaces": ()}  # Allow model_ prefix

    publication_id: Optional[str] = Field(None, description="Publication ID")
    title: str = Field(..., description="Publication title")
    current_citations: int = Field(..., description="Current citation count")
    predicted_1_year: int = Field(..., description="Predicted citations in 1 year")
    predicted_3_years: int = Field(..., description="Predicted citations in 3 years")
    predicted_5_years: int = Field(..., description="Predicted citations in 5 years")
    confidence_lower: int = Field(..., description="Lower confidence bound")
    confidence_upper: int = Field(..., description="Upper confidence bound")
    model_confidence: float = Field(..., description="Model confidence score (0-1)")


class SimilarBiomarkerResponse(BaseModel):
    """Similar biomarker with similarity score."""

    biomarker: str = Field(..., description="Biomarker name")
    similarity: float = Field(..., description="Similarity score (0-1)")


class RecommendationResponse(BaseModel):
    """Biomarker recommendation."""

    biomarker: str = Field(..., description="Recommended biomarker")
    score: float = Field(..., description="Recommendation score (0-1)")
    rank: int = Field(..., description="Rank in recommendations (1-based)")
    strategy: str = Field(..., description="Recommendation strategy used")
    explanation: str = Field(..., description="Why this was recommended")
    supporting_evidence: List[str] = Field(..., description="Supporting evidence for recommendation")


class TrendForecastResponse(BaseModel):
    """Publication trend forecast."""

    biomarker: str = Field(..., description="Biomarker name")
    periods: int = Field(..., description="Number of periods forecasted")
    forecast: List[float] = Field(..., description="Forecasted publication volumes")
    lower_bound: List[float] = Field(..., description="Lower confidence bound")
    upper_bound: List[float] = Field(..., description="Upper confidence bound")
    model: str = Field(..., description="Model used for forecasting")


class EnrichedPublicationResponse(BaseModel):
    """Publication enriched with ML predictions."""

    id: Optional[str] = Field(None, description="Publication ID")
    title: str = Field(..., description="Publication title")
    authors: List[str] = Field(..., description="Authors")
    publication_date: Optional[str] = Field(None, description="Publication date (ISO format)")
    citations: int = Field(..., description="Current citation count")
    journal: Optional[str] = Field(None, description="Journal name")
    predicted_citations: Optional[Dict[str, int]] = Field(None, description="Predicted future citations")
    similar_biomarkers: Optional[List[SimilarBiomarkerResponse]] = Field(
        None, description="Similar biomarkers"
    )


class EmergingTopicResponse(BaseModel):
    """Emerging research topic."""

    topic: str = Field(..., description="Topic name")
    growth_rate: float = Field(..., description="Growth rate (percentage)")
    recent_count: int = Field(..., description="Recent publication count")
    total_count: int = Field(..., description="Total publication count")


class BiomarkerTrajectoryResponse(BaseModel):
    """Biomarker research trajectory."""

    status: str = Field(..., description="Trajectory status (emerging/established/declining)")
    growth_rate: float = Field(..., description="Growth rate (percentage)")
    trend: str = Field(..., description="Trend direction (increasing/stable/decreasing)")
    forecasted_peak_month: Optional[str] = Field(None, description="Forecasted peak month (ISO format)")


class BiomarkerAnalyticsResponse(BaseModel):
    """Comprehensive biomarker analytics."""

    biomarker: str = Field(..., description="Biomarker name")
    total_publications: int = Field(..., description="Total publications found")
    emerging_topics: List[EmergingTopicResponse] = Field(..., description="Emerging research topics")
    similar_biomarkers: List[SimilarBiomarkerResponse] = Field(..., description="Similar biomarkers")
    trajectory: BiomarkerTrajectoryResponse = Field(..., description="Research trajectory analysis")


class MLHealthResponse(BaseModel):
    """ML service health status."""

    status: str = Field(..., description="Service status (healthy/degraded/unavailable)")
    models_loaded: Dict[str, bool] = Field(..., description="Status of loaded models")
    cache_available: bool = Field(..., description="Whether cache is available")
    cache_stats: Optional[Dict] = Field(None, description="Cache statistics")


class BatchPredictionRequest(BaseModel):
    """Request for batch citation predictions."""

    publication_ids: List[str] = Field(..., description="Publication IDs to predict for")
    use_cache: bool = Field(True, description="Whether to use cache")


class RecommendationRequest(BaseModel):
    """Request for biomarker recommendations."""

    biomarker: str = Field(..., description="Source biomarker")
    strategy: str = Field(
        "similar",
        description="Strategy (similar/emerging/high_impact)",
        pattern="^(similar|emerging|high_impact)$",
    )
    num_recommendations: int = Field(5, description="Number of recommendations", ge=1, le=20)
    use_cache: bool = Field(True, description="Whether to use cache")


class TrendForecastRequest(BaseModel):
    """Request for trend forecasting."""

    biomarker: str = Field(..., description="Biomarker to forecast")
    periods: int = Field(12, description="Number of periods to forecast", ge=1, le=36)
    use_cache: bool = Field(True, description="Whether to use cache")


class EnhancedSearchRequest(BaseModel):
    """Request for ML-enhanced search."""

    query: str = Field(..., description="Search query")
    include_predictions: bool = Field(True, description="Include citation predictions")
    include_similar: bool = Field(True, description="Include similar biomarkers")
    max_results: int = Field(10, description="Maximum results", ge=1, le=100)
    use_cache: bool = Field(True, description="Whether to use cache")
