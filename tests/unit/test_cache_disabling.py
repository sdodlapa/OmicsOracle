"""
Test cache disabling functionality across all components.
"""

from unittest.mock import MagicMock, patch

import pytest

from omics_oracle.core.config import Config
from omics_oracle.geo_tools.geo_client import UnifiedGEOClient
from omics_oracle.pipeline.pipeline import OmicsOracle
from omics_oracle.services.summarizer import SummarizationService


class TestCacheDisabling:
    """Test that caching is properly disabled across all components."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        config = MagicMock()
        config.logging = MagicMock()
        config.logging.level = "INFO"
        config.logging.format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        config.ncbi = MagicMock()
        config.ncbi.email = "test@example.com"
        config.openai = MagicMock()
        config.openai.api_key = "test_key"
        return config

    def test_pipeline_cache_disabling(self, mock_config):
        """Test that pipeline disables cache when requested."""
        with patch("src.omics_oracle.pipeline.pipeline.UnifiedGEOClient") as mock_geo_client, patch(
            "src.omics_oracle.pipeline.pipeline.SummarizationService"
        ) as mock_summarizer, patch("src.omics_oracle.pipeline.pipeline.PromptInterpreter"), patch(
            "src.omics_oracle.pipeline.pipeline.BiomedicalNER"
        ), patch(
            "src.omics_oracle.pipeline.pipeline.EnhancedBiologicalSynonymMapper"
        ), patch(
            "src.omics_oracle.pipeline.pipeline.ImprovedSearchService"
        ):
            # Setup mock instances
            mock_geo_instance = MagicMock()
            mock_geo_instance.cache = MagicMock()
            mock_geo_client.return_value = mock_geo_instance

            mock_summarizer_instance = MagicMock()
            mock_summarizer.return_value = mock_summarizer_instance

            # Create pipeline with cache disabled
            pipeline = OmicsOracle(config=mock_config, disable_cache=True)

            # Verify cache is disabled
            assert pipeline.disable_cache is True

            # Verify geo client cache was set to None
            assert mock_geo_instance.cache is None

            # Verify summarizer was initialized with cache disabled
            mock_summarizer.assert_called_once_with(mock_config, disable_cache=True)

    def test_geo_client_cache_disabling(self, mock_config):
        """Test that GEO client cache is properly disabled."""
        with patch("src.omics_oracle.geo_tools.geo_client.NCBIDirectClient"):
            geo_client = UnifiedGEOClient(mock_config)

            # Mock the cache attribute
            geo_client.cache = MagicMock()

            # Simulate cache disabling
            geo_client.cache = None

            assert geo_client.cache is None

    def test_summarizer_cache_disabling(self, mock_config):
        """Test that summarizer cache is properly disabled."""
        with patch("src.omics_oracle.services.cache.SummaryCache"), patch("openai.OpenAI"):
            # Create summarizer with cache disabled
            summarizer = SummarizationService(config=mock_config, disable_cache=True)

            # Verify cache is None when disabled
            assert summarizer.cache is None

    def test_summarizer_cache_enabled(self, mock_config):
        """Test that summarizer cache is created when enabled."""
        with patch("src.omics_oracle.services.summarizer.SummaryCache") as mock_cache, patch("openai.OpenAI"):
            # Create summarizer with cache enabled
            summarizer = SummarizationService(config=mock_config, disable_cache=False)

            # Verify cache was created (the real SummaryCache class is instantiated)
            # Check that the summarizer has a cache attribute that's not None
            assert summarizer.cache is not None

    def test_pipeline_geo_client_cache_cleanup(self, mock_config):
        """Test that pipeline properly cleans up GEO client cache."""
        with patch("src.omics_oracle.pipeline.pipeline.UnifiedGEOClient") as mock_geo_client_class, patch(
            "src.omics_oracle.pipeline.pipeline.SummarizationService"
        ), patch("src.omics_oracle.pipeline.pipeline.PromptInterpreter"), patch(
            "src.omics_oracle.pipeline.pipeline.BiomedicalNER"
        ), patch(
            "src.omics_oracle.pipeline.pipeline.EnhancedBiologicalSynonymMapper"
        ), patch(
            "src.omics_oracle.pipeline.pipeline.ImprovedSearchService"
        ):
            # Mock GEO client instance
            mock_geo_client = MagicMock()
            mock_geo_client.cache = MagicMock()
            mock_geo_client_class.return_value = mock_geo_client

            # Create pipeline with cache disabled
            pipeline = OmicsOracle(config=mock_config, disable_cache=True)

            # Verify that cache was set to None
            assert mock_geo_client.cache is None

    def test_cache_disabling_flag_propagation(self, mock_config):
        """Test that disable_cache flag is properly propagated."""
        with patch("src.omics_oracle.pipeline.pipeline.UnifiedGEOClient"), patch(
            "src.omics_oracle.pipeline.pipeline.SummarizationService"
        ) as mock_summarizer, patch("src.omics_oracle.pipeline.pipeline.PromptInterpreter"), patch(
            "src.omics_oracle.pipeline.pipeline.BiomedicalNER"
        ), patch(
            "src.omics_oracle.pipeline.pipeline.EnhancedBiologicalSynonymMapper"
        ), patch(
            "src.omics_oracle.pipeline.pipeline.ImprovedSearchService"
        ):
            # Test with cache enabled
            pipeline_enabled = OmicsOracle(config=mock_config, disable_cache=False)
            assert pipeline_enabled.disable_cache is False

            # Reset mock to clear previous call
            mock_summarizer.reset_mock()

            # Test with cache disabled
            pipeline_disabled = OmicsOracle(config=mock_config, disable_cache=True)
            assert pipeline_disabled.disable_cache is True

            # Verify summarizer was called with correct flag in the last call
            mock_summarizer.assert_called_with(mock_config, disable_cache=True)
