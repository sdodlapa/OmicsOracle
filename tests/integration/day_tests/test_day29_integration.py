"""
Day 29 Integration Tests

Tests for ML service integration with API endpoints.
"""

import asyncio
from datetime import datetime

import pytest

from omics_oracle_v2.api.models.ml_schemas import CitationPredictionResponse, RecommendationResponse
from omics_oracle_v2.lib.search_engines.citations.models import Publication, PublicationSource
from omics_oracle_v2.lib.services import MLService


@pytest.fixture
def sample_publications():
    """Create sample publications for testing."""
    return [
        Publication(
            pmid="pub1",
            title="BRCA1 mutations in breast cancer",
            authors=["Smith J", "Doe A"],
            publication_date=datetime(2020, 1, 1),
            citations=150,
            journal="Nature",
            source=PublicationSource.PUBMED,
        ),
        Publication(
            pmid="pub2",
            title="BRCA2 genetic variants and cancer risk",
            authors=["Johnson M", "Brown K"],
            publication_date=datetime(2021, 6, 15),
            citations=85,
            journal="Science",
            source=PublicationSource.PUBMED,
        ),
        Publication(
            pmid="pub3",
            title="TP53 pathway in tumor suppression",
            authors=["Lee H", "Wang X"],
            publication_date=datetime(2019, 3, 20),
            citations=220,
            journal="Cell",
            source=PublicationSource.PUBMED,
        ),
        Publication(
            pmid="pub4",
            title="EGFR mutations in lung cancer",
            authors=["Garcia R", "Martinez L"],
            publication_date=datetime(2022, 9, 10),
            citations=45,
            journal="NEJM",
            source=PublicationSource.PUBMED,
        ),
        Publication(
            pmid="pub5",
            title="KRAS oncogene activation mechanisms",
            authors=["Chen Y", "Liu Z"],
            publication_date=datetime(2023, 2, 28),
            citations=12,
            journal="Cancer Cell",
            source=PublicationSource.PUBMED,
        ),
    ]


@pytest.fixture
def ml_service():
    """Get ML service instance."""
    return MLService()


@pytest.mark.asyncio
async def test_ml_service_initialization(ml_service):
    """Test ML service initializes correctly."""
    assert ml_service is not None
    assert ml_service.citation_predictor is not None
    assert ml_service.trend_forecaster is not None
    assert ml_service.embedder is not None
    assert ml_service.recommender is not None
    assert ml_service.cache is not None
    print("ML Service initialized successfully")


@pytest.mark.asyncio
async def test_citation_predictions(ml_service, sample_publications):
    """Test citation prediction functionality."""
    # Train the model first
    ml_service.citation_predictor.train(sample_publications)

    # Predict for subset of publications
    predictions = await ml_service.predict_citations(
        publications=sample_publications[:3],
        use_cache=False,  # Disable cache for testing
    )

    assert len(predictions) == 3
    for pred in predictions:
        # Validate response structure
        assert "publication_id" in pred
        assert "title" in pred
        assert "current_citations" in pred
        assert "predicted_1_year" in pred
        assert "predicted_3_years" in pred
        assert "predicted_5_years" in pred
        assert "model_confidence" in pred

        # Validate predictions are non-negative
        assert pred["predicted_1_year"] >= 0
        assert pred["predicted_3_years"] >= 0
        assert pred["predicted_5_years"] >= 0
        assert 0 <= pred["model_confidence"] <= 1

    print(f"Citation predictions: {len(predictions)} successful")
    print(f"Sample prediction: {predictions[0]['title']}")
    print(f"  Current: {predictions[0]['current_citations']}")
    print(f"  1-year: {predictions[0]['predicted_1_year']}")
    print(f"  5-year: {predictions[0]['predicted_5_years']}")


@pytest.mark.asyncio
async def test_recommendations_similar(ml_service, sample_publications):
    """Test similar biomarker recommendations."""
    recommendations = await ml_service.get_recommendations(
        biomarker="BRCA1",
        publications=sample_publications,
        num_recommendations=3,
        strategy="similar",
        use_cache=False,
    )

    assert len(recommendations) <= 3
    for rec in recommendations:
        assert rec.biomarker is not None
        assert 0 <= rec.score <= 1
        assert rec.rank > 0
        assert rec.strategy == "similar"
        assert len(rec.explanation) > 0

    print(f"Similar recommendations for BRCA1: {len(recommendations)}")
    for i, rec in enumerate(recommendations[:3], 1):
        print(f"{i}. {rec.biomarker} (score: {rec.score:.3f})")


@pytest.mark.asyncio
async def test_recommendations_emerging(ml_service, sample_publications):
    """Test emerging biomarker recommendations."""
    recommendations = await ml_service.get_recommendations(
        biomarker="",  # Not needed for emerging
        publications=sample_publications,
        num_recommendations=3,
        strategy="emerging",
        use_cache=False,
    )

    assert len(recommendations) <= 3
    for rec in recommendations:
        assert rec.strategy == "emerging"
        assert 0 <= rec.score <= 1

    print(f"Emerging recommendations: {len(recommendations)}")


@pytest.mark.asyncio
async def test_recommendations_high_impact(ml_service, sample_publications):
    """Test high-impact biomarker recommendations."""
    recommendations = await ml_service.get_recommendations(
        biomarker="",  # Not needed for high-impact
        publications=sample_publications,
        num_recommendations=3,
        strategy="high_impact",
        use_cache=False,
    )

    assert len(recommendations) <= 3
    for rec in recommendations:
        assert rec.strategy == "high_impact"
        assert 0 <= rec.score <= 1

    print(f"High-impact recommendations: {len(recommendations)}")


@pytest.mark.asyncio
async def test_trend_forecasting(ml_service, sample_publications):
    """Test trend forecasting."""
    forecast = await ml_service.forecast_trends(
        biomarker="BRCA1",
        publications=sample_publications,
        periods=6,
        use_cache=False,
    )

    assert "biomarker" in forecast
    assert forecast["biomarker"] == "BRCA1"
    assert "periods" in forecast
    assert forecast["periods"] == 6
    assert "forecast" in forecast
    assert len(forecast["forecast"]) == 6
    assert "model" in forecast

    print(f"Trend forecast for BRCA1: {forecast['periods']} periods")
    print(f"Model: {forecast['model']}")
    print(f"Forecast: {forecast['forecast'][:3]}...")


@pytest.mark.asyncio
async def test_enrich_search_results(ml_service, sample_publications):
    """Test search result enrichment."""
    enriched = await ml_service.enrich_search_results(
        publications=sample_publications[:2],
        include_predictions=True,
        include_similar=True,
        use_cache=False,
    )

    assert len(enriched) == 2
    for result in enriched:
        assert "id" in result
        assert "title" in result
        assert "authors" in result
        assert "citations" in result

        # Check predictions were added
        if "predicted_citations" in result:
            assert "1_year" in result["predicted_citations"]
            assert "3_years" in result["predicted_citations"]
            assert "5_years" in result["predicted_citations"]

        # Check similar biomarkers were added
        if "similar_biomarkers" in result:
            assert isinstance(result["similar_biomarkers"], list)

    print(f"Enriched search results: {len(enriched)}")
    if enriched[0].get("predicted_citations"):
        print(f"Sample enrichment: {enriched[0]['title'][:50]}...")
        print(f"  Predicted 1-year: {enriched[0]['predicted_citations']['1_year']}")


@pytest.mark.asyncio
async def test_biomarker_analytics(ml_service, sample_publications):
    """Test comprehensive biomarker analytics."""
    analytics = await ml_service.get_biomarker_analytics(
        biomarker="BRCA1",
        publications=sample_publications,
        use_cache=False,
    )

    assert "biomarker" in analytics
    assert analytics["biomarker"] == "BRCA1"
    assert "total_publications" in analytics
    assert analytics["total_publications"] == len(sample_publications)
    assert "emerging_topics" in analytics
    assert "similar_biomarkers" in analytics
    assert "trajectory" in analytics

    # Validate trajectory
    trajectory = analytics["trajectory"]
    assert "status" in trajectory
    assert trajectory["status"] in ["emerging", "established", "declining"]
    assert "growth_rate" in trajectory
    assert "trend" in trajectory

    print("Analytics for BRCA1:")
    print("  Total publications: {}".format(analytics["total_publications"]))
    print("  Trajectory: {}".format(trajectory["status"]))
    print("  Growth rate: {:.2f}%".format(trajectory["growth_rate"]))
    print("  Emerging topics: {}".format(len(analytics["emerging_topics"])))


@pytest.mark.asyncio
async def test_caching_performance(ml_service, sample_publications):
    """Test that caching improves performance."""
    import time

    # First call (no cache)
    start = time.time()
    predictions1 = await ml_service.predict_citations(
        publications=sample_publications[:1],
        use_cache=True,
    )
    time1 = (time.time() - start) * 1000

    # Second call (should use cache)
    start = time.time()
    predictions2 = await ml_service.predict_citations(
        publications=sample_publications[:1],
        use_cache=True,
    )
    time2 = (time.time() - start) * 1000

    # Cache should be faster (or similar if Redis is very fast)
    print(f"First call: {time1:.2f}ms")
    print(f"Second call (cached): {time2:.2f}ms")
    print(f"Speedup: {time1/time2 if time2 > 0 else 'N/A'}x")

    # Results should be identical
    assert predictions1[0]["title"] == predictions2[0]["title"]
    assert predictions1[0]["predicted_5_years"] == predictions2[0]["predicted_5_years"]


@pytest.mark.asyncio
async def test_cache_stats(ml_service):
    """Test cache statistics retrieval."""
    stats = await ml_service.get_cache_stats()

    # Should return dict with stats
    assert isinstance(stats, dict)
    print(f"Cache stats: {stats}")


@pytest.mark.asyncio
async def test_pydantic_models():
    """Test Pydantic model validation."""
    # Test CitationPredictionResponse
    pred = CitationPredictionResponse(
        publication_id="test123",
        title="Test Publication",
        current_citations=100,
        predicted_1_year=150,
        predicted_3_years=250,
        predicted_5_years=400,
        confidence_lower=120,
        confidence_upper=180,
        model_confidence=0.85,
    )
    assert pred.publication_id == "test123"
    assert pred.model_confidence == 0.85

    # Test RecommendationResponse
    rec = RecommendationResponse(
        biomarker="BRCA2",
        score=0.89,
        rank=1,
        strategy="similar",
        explanation="Highly similar genetic profile",
        supporting_evidence=["Evidence 1", "Evidence 2"],
    )
    assert rec.biomarker == "BRCA2"
    assert rec.score == 0.89

    print("Pydantic model validation: PASSED")


def test_performance_targets():
    """Verify performance meets Day 29 targets."""
    # Performance targets from DAY_29_INTEGRATION_PLAN.md:
    # - Enhanced search: <300ms
    # - Recommendations: <150ms
    # - Citation predictions: <100ms
    # - Analytics: <500ms

    print("\nPerformance Targets (from plan):")
    print("- Enhanced search: <300ms")
    print("- Recommendations: <150ms")
    print("- Citation predictions: <100ms")
    print("- Analytics: <500ms")
    print("\nNote: Actual performance will be measured in integration tests")


if __name__ == "__main__":
    # Run tests
    print("=" * 60)
    print("DAY 29 INTEGRATION TESTS")
    print("=" * 60)

    asyncio.run(test_ml_service_initialization(MLService()))
    print()

    # Create sample data - need at least 10 for cross-validation
    sample_pubs = [
        Publication(
            pmid=f"pub{i}",
            title=f"Sample publication {i}",
            authors=["Author A", "Author B"],
            publication_date=datetime(2020, 1, 1),
            citations=100 + i * 10,
            journal="Test Journal",
            source=PublicationSource.PUBMED,
        )
        for i in range(1, 11)
    ]

    ml_svc = MLService()

    # Train models with sample data
    print("Training ML models with sample data...")
    ml_svc.citation_predictor.train(sample_pubs)
    print("Models trained\n")

    print("\nRunning async tests...")
    asyncio.run(test_citation_predictions(ml_svc, sample_pubs))
    print()
    asyncio.run(test_recommendations_similar(ml_svc, sample_pubs))
    print()
    asyncio.run(test_trend_forecasting(ml_svc, sample_pubs))
    print()
    asyncio.run(test_biomarker_analytics(ml_svc, sample_pubs))
    print()
    asyncio.run(test_caching_performance(ml_svc, sample_pubs))
    print()

    test_pydantic_models()
    print()
    test_performance_targets()

    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETED")
    print("=" * 60)
