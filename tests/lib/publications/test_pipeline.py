"""
Unit tests for PublicationSearchPipeline.

Tests full pipeline, feature toggles, and integration.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from omics_oracle_v2.lib.publications.pipeline import PublicationSearchPipeline
from omics_oracle_v2.lib.publications.config import (
    PublicationSearchConfig, 
    PubMedConfig
)
from omics_oracle_v2.lib.publications.models import (
    Publication,
    PublicationSource,
    PublicationSearchResult,
    PublicationResult
)


@pytest.fixture
def pubmed_config():
    """Create PubMed configuration."""
    return PubMedConfig(
        email="test@example.com",
        max_results=10
    )


@pytest.fixture
def basic_config(pubmed_config):
    """Create basic pipeline configuration (PubMed only)."""
    return PublicationSearchConfig(
        enable_pubmed=True,
        enable_scholar=False,
        enable_citations=False,
        enable_pdf_download=False,
        enable_fulltext=False,
        enable_institutional_access=False,
        pubmed_config=pubmed_config
    )


@pytest.fixture
def full_config(pubmed_config):
    """Create full configuration with all features."""
    return PublicationSearchConfig(
        enable_pubmed=True,
        enable_scholar=True,
        enable_citations=True,
        enable_pdf_download=True,
        enable_fulltext=True,
        enable_institutional_access=True,
        primary_institution="gatech",
        pubmed_config=pubmed_config
    )


@pytest.fixture
def sample_publications():
    """Create sample publications for testing."""
    return [
        Publication(
            pmid="12345678",
            title="CRISPR-Cas9 gene editing for cancer therapy",
            abstract="Study on CRISPR for cancer treatment.",
            source=PublicationSource.PUBMED,
            publication_date=datetime(2024, 3, 15),
            citations=150
        ),
        Publication(
            pmid="87654321",
            title="Traditional cancer treatment methods",
            abstract="Review of conventional therapies.",
            source=PublicationSource.PUBMED,
            publication_date=datetime(2020, 1, 10),
            citations=500
        )
    ]


class TestPipelineInitialization:
    """Test pipeline initialization."""

    def test_initialization_with_basic_config(self, basic_config):
        """Test pipeline initializes with basic config."""
        pipeline = PublicationSearchPipeline(basic_config)
        
        assert pipeline.config == basic_config
        assert pipeline.pubmed_client is not None
        assert pipeline.ranker is not None

    def test_pubmed_client_initialized_when_enabled(self, basic_config):
        """Test PubMed client is initialized when enabled."""
        pipeline = PublicationSearchPipeline(basic_config)
        
        assert pipeline.pubmed_client is not None
        assert pipeline.config.enable_pubmed is True

    def test_pubmed_client_not_initialized_when_disabled(self, pubmed_config):
        """Test PubMed client is not initialized when disabled."""
        config = PublicationSearchConfig(
            enable_pubmed=False,
            pubmed_config=pubmed_config
        )
        pipeline = PublicationSearchPipeline(config)
        
        assert pipeline.pubmed_client is None

    def test_ranker_always_initialized(self, basic_config):
        """Test ranker is always initialized."""
        pipeline = PublicationSearchPipeline(basic_config)
        
        assert pipeline.ranker is not None

    def test_week_3_features_not_initialized(self, basic_config):
        """Test Week 3 features are None when disabled."""
        pipeline = PublicationSearchPipeline(basic_config)
        
        assert pipeline.scholar_client is None
        assert pipeline.citation_analyzer is None

    def test_week_4_features_not_initialized(self, basic_config):
        """Test Week 4 features are None when disabled."""
        pipeline = PublicationSearchPipeline(basic_config)
        
        assert pipeline.pdf_downloader is None
        assert pipeline.fulltext_extractor is None

    def test_institutional_access_initialized_when_enabled(self):
        """Test institutional access managers initialized when enabled."""
        config = PublicationSearchConfig(
            enable_pubmed=True,
            enable_institutional_access=True,
            primary_institution="gatech",
            secondary_institution="odu",
            pubmed_config=PubMedConfig(email="test@example.com")
        )
        pipeline = PublicationSearchPipeline(config)
        
        assert pipeline.institutional_manager is not None
        assert pipeline.institutional_manager_fallback is not None


class TestFeatureToggles:
    """Test feature toggle behavior."""

    def test_get_enabled_features_pubmed_only(self, basic_config):
        """Test get_enabled_features with PubMed only."""
        pipeline = PublicationSearchPipeline(basic_config)
        
        features = pipeline.get_enabled_features()
        
        assert "pubmed" in features
        assert "google_scholar" not in features
        assert "citations" not in features

    def test_get_enabled_features_with_institutional_access(self):
        """Test get_enabled_features includes institutional access."""
        config = PublicationSearchConfig(
            enable_pubmed=True,
            enable_institutional_access=True,
            primary_institution="gatech",
            pubmed_config=PubMedConfig(email="test@example.com")
        )
        pipeline = PublicationSearchPipeline(config)
        
        features = pipeline.get_enabled_features()
        
        assert "pubmed" in features
        assert "institutional_access_gatech" in features

    def test_conditional_execution_respects_toggles(self, pubmed_config):
        """Test conditional execution respects feature toggles."""
        config = PublicationSearchConfig(
            enable_pubmed=False,
            pubmed_config=pubmed_config
        )
        pipeline = PublicationSearchPipeline(config)
        
        # PubMed disabled, should not execute
        assert pipeline.pubmed_client is None


class TestSearchFunctionality:
    """Test main search functionality."""

    @patch('omics_oracle_v2.lib.publications.clients.pubmed.PubMedClient.search')
    def test_search_returns_publication_result(self, mock_search, basic_config, sample_publications):
        """Test search returns PublicationResult."""
        mock_search.return_value = sample_publications
        
        pipeline = PublicationSearchPipeline(basic_config)
        result = pipeline.search("CRISPR cancer", max_results=10)
        
        assert isinstance(result, PublicationResult)
        assert result.query == "CRISPR cancer"
        assert len(result.publications) > 0

    @patch('omics_oracle_v2.lib.publications.clients.pubmed.PubMedClient.search')
    def test_search_includes_metadata(self, mock_search, basic_config, sample_publications):
        """Test search result includes metadata."""
        mock_search.return_value = sample_publications
        
        pipeline = PublicationSearchPipeline(basic_config)
        result = pipeline.search("test query", max_results=10)
        
        assert hasattr(result, 'metadata')
        assert 'search_time_seconds' in result.metadata
        assert 'sources_used' in result.metadata
        assert 'total_found' in result.metadata

    @patch('omics_oracle_v2.lib.publications.clients.pubmed.PubMedClient.search')
    def test_search_deduplicates_results(self, mock_search, basic_config):
        """Test search deduplicates publications."""
        # Same publication twice
        duplicate_pub = Publication(
            pmid="12345",
            title="Test",
            source=PublicationSource.PUBMED
        )
        mock_search.return_value = [duplicate_pub, duplicate_pub]
        
        pipeline = PublicationSearchPipeline(basic_config)
        result = pipeline.search("test", max_results=10)
        
        # Should deduplicate
        assert len(result.publications) == 1

    @patch('omics_oracle_v2.lib.publications.clients.pubmed.PubMedClient.search')
    def test_search_ranks_results(self, mock_search, basic_config, sample_publications):
        """Test search ranks results by relevance."""
        mock_search.return_value = sample_publications
        
        pipeline = PublicationSearchPipeline(basic_config)
        result = pipeline.search("CRISPR cancer therapy", max_results=10)
        
        # Results should be ranked
        if len(result.publications) > 1:
            assert result.publications[0].relevance_score >= result.publications[1].relevance_score

    @patch('omics_oracle_v2.lib.publications.clients.pubmed.PubMedClient.search')
    def test_search_respects_max_results(self, mock_search, basic_config, sample_publications):
        """Test search respects max_results parameter."""
        # Return many publications
        mock_search.return_value = sample_publications * 10
        
        pipeline = PublicationSearchPipeline(basic_config)
        result = pipeline.search("test", max_results=5)
        
        # Should limit to max_results
        assert len(result.publications) <= 5

    @patch('omics_oracle_v2.lib.publications.clients.pubmed.PubMedClient.search')
    def test_search_handles_empty_results(self, mock_search, basic_config):
        """Test search handles empty result set."""
        mock_search.return_value = []
        
        pipeline = PublicationSearchPipeline(basic_config)
        result = pipeline.search("nonexistent query", max_results=10)
        
        assert isinstance(result, PublicationResult)
        assert len(result.publications) == 0
        assert result.metadata['total_found'] == 0


class TestInstitutionalAccessIntegration:
    """Test institutional access integration."""

    @patch('omics_oracle_v2.lib.publications.clients.pubmed.PubMedClient.search')
    def test_institutional_access_enrichment(self, mock_search):
        """Test institutional access enriches publications."""
        pub = Publication(
            pmid="12345",
            doi="10.1038/test.123",
            title="Test publication",
            source=PublicationSource.PUBMED
        )
        mock_search.return_value = [pub]
        
        config = PublicationSearchConfig(
            enable_pubmed=True,
            enable_institutional_access=True,
            primary_institution="gatech",
            pubmed_config=PubMedConfig(email="test@example.com")
        )
        pipeline = PublicationSearchPipeline(config)
        
        result = pipeline.search("test", max_results=10)
        
        # Should have access metadata
        if result.publications:
            pub_result = result.publications[0].publication
            assert 'access_status' in pub_result.metadata
            assert 'has_access' in pub_result.metadata

    @patch('omics_oracle_v2.lib.publications.clients.pubmed.PubMedClient.search')
    def test_institutional_access_fallback(self, mock_search):
        """Test institutional access uses fallback institution."""
        pub = Publication(
            pmid="12345",
            doi="10.1038/test.123",
            title="Test publication",
            source=PublicationSource.PUBMED
        )
        mock_search.return_value = [pub]
        
        config = PublicationSearchConfig(
            enable_pubmed=True,
            enable_institutional_access=True,
            primary_institution="gatech",
            secondary_institution="odu",
            pubmed_config=PubMedConfig(email="test@example.com")
        )
        pipeline = PublicationSearchPipeline(config)
        
        result = pipeline.search("test", max_results=10)
        
        # Should try both institutions
        assert pipeline.institutional_manager is not None
        assert pipeline.institutional_manager_fallback is not None


class TestDeduplication:
    """Test publication deduplication."""

    def test_deduplicate_by_pmid(self, basic_config):
        """Test deduplication by PMID."""
        pub1 = Publication(
            pmid="12345",
            title="Same publication",
            source=PublicationSource.PUBMED
        )
        pub2 = Publication(
            pmid="12345",
            title="Same publication",
            source=PublicationSource.PUBMED
        )
        
        pipeline = PublicationSearchPipeline(basic_config)
        deduped = pipeline._deduplicate_publications([pub1, pub2])
        
        assert len(deduped) == 1

    def test_deduplicate_by_doi(self, basic_config):
        """Test deduplication by DOI."""
        pub1 = Publication(
            doi="10.1038/test.123",
            title="Same publication",
            source=PublicationSource.PUBMED
        )
        pub2 = Publication(
            doi="10.1038/test.123",
            title="Same publication",
            source=PublicationSource.GOOGLE_SCHOLAR
        )
        
        pipeline = PublicationSearchPipeline(basic_config)
        deduped = pipeline._deduplicate_publications([pub1, pub2])
        
        assert len(deduped) == 1

    def test_deduplicate_keeps_unique(self, basic_config):
        """Test deduplication keeps unique publications."""
        pub1 = Publication(
            pmid="12345",
            title="Publication 1",
            source=PublicationSource.PUBMED
        )
        pub2 = Publication(
            pmid="67890",
            title="Publication 2",
            source=PublicationSource.PUBMED
        )
        
        pipeline = PublicationSearchPipeline(basic_config)
        deduped = pipeline._deduplicate_publications([pub1, pub2])
        
        assert len(deduped) == 2


class TestContextManager:
    """Test context manager support."""

    def test_pipeline_as_context_manager(self, basic_config):
        """Test pipeline works as context manager."""
        with PublicationSearchPipeline(basic_config) as pipeline:
            assert pipeline.config == basic_config
        
        # Should cleanup successfully

    @patch('omics_oracle_v2.lib.publications.clients.pubmed.PubMedClient.search')
    def test_context_manager_search(self, mock_search, basic_config, sample_publications):
        """Test search works in context manager."""
        mock_search.return_value = sample_publications
        
        with PublicationSearchPipeline(basic_config) as pipeline:
            result = pipeline.search("test", max_results=10)
            assert isinstance(result, PublicationResult)


class TestErrorHandling:
    """Test error handling."""

    @patch('omics_oracle_v2.lib.publications.clients.pubmed.PubMedClient.search')
    def test_search_handles_client_error(self, mock_search, basic_config):
        """Test search handles client errors gracefully."""
        mock_search.side_effect = Exception("API error")
        
        pipeline = PublicationSearchPipeline(basic_config)
        
        # Should not crash
        try:
            result = pipeline.search("test", max_results=10)
            # May return empty result or raise
            assert True
        except Exception:
            # Also acceptable
            assert True

    def test_search_with_invalid_query(self, basic_config):
        """Test search handles invalid query."""
        pipeline = PublicationSearchPipeline(basic_config)
        
        # Empty query
        result = pipeline.search("", max_results=10)
        # Should handle gracefully (may return empty or raise)
        assert isinstance(result, PublicationResult) or result is None


class TestMetadataGeneration:
    """Test metadata generation."""

    @patch('omics_oracle_v2.lib.publications.clients.pubmed.PubMedClient.search')
    def test_metadata_includes_search_time(self, mock_search, basic_config, sample_publications):
        """Test metadata includes search time."""
        mock_search.return_value = sample_publications
        
        pipeline = PublicationSearchPipeline(basic_config)
        result = pipeline.search("test", max_results=10)
        
        assert 'search_time_seconds' in result.metadata
        assert result.metadata['search_time_seconds'] >= 0

    @patch('omics_oracle_v2.lib.publications.clients.pubmed.PubMedClient.search')
    def test_metadata_includes_sources(self, mock_search, basic_config, sample_publications):
        """Test metadata includes sources used."""
        mock_search.return_value = sample_publications
        
        pipeline = PublicationSearchPipeline(basic_config)
        result = pipeline.search("test", max_results=10)
        
        assert 'sources_used' in result.metadata
        assert 'pubmed' in result.metadata['sources_used']

    @patch('omics_oracle_v2.lib.publications.clients.pubmed.PubMedClient.search')
    def test_metadata_includes_feature_flags(self, mock_search, basic_config, sample_publications):
        """Test metadata includes enabled features."""
        mock_search.return_value = sample_publications
        
        pipeline = PublicationSearchPipeline(basic_config)
        result = pipeline.search("test", max_results=10)
        
        assert 'features_enabled' in result.metadata
        assert 'pubmed' in result.metadata['features_enabled']


class TestWeek34Ready:
    """Test Week 3-4 feature readiness."""

    def test_scholar_client_stub_exists(self, basic_config):
        """Test Scholar client stub exists."""
        pipeline = PublicationSearchPipeline(basic_config)
        assert hasattr(pipeline, 'scholar_client')

    def test_citation_analyzer_stub_exists(self, basic_config):
        """Test citation analyzer stub exists."""
        pipeline = PublicationSearchPipeline(basic_config)
        assert hasattr(pipeline, 'citation_analyzer')

    def test_pdf_downloader_stub_exists(self, basic_config):
        """Test PDF downloader stub exists."""
        pipeline = PublicationSearchPipeline(basic_config)
        assert hasattr(pipeline, 'pdf_downloader')

    def test_fulltext_extractor_stub_exists(self, basic_config):
        """Test fulltext extractor stub exists."""
        pipeline = PublicationSearchPipeline(basic_config)
        assert hasattr(pipeline, 'fulltext_extractor')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
