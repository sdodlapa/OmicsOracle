#!/usr/bin/env python3
"""
AI Summarization Integration Tests

Tests the AI summarization component integration with the pipeline,
including OpenAI API integration, fallback behavior, and caching.
"""

import asyncio
import json
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

# Add project root to path
from src.omics_oracle.core.config import Config
from src.omics_oracle.services.summarizer import SummarizationService


class TestAISummarizationIntegration:
    """Integration tests for AI summarization functionality."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        config = MagicMock()
        config.openai = MagicMock()
        config.openai.api_key = "test_openai_key"
        config.openai.model = "gpt-3.5-turbo"
        config.openai.max_tokens = 1000
        config.openai.temperature = 0.7
        return config

    @pytest.fixture
    def sample_geo_metadata(self):
        """Sample GEO metadata for summarization testing."""
        return {
            "accession": "GSE123456",
            "title": "RNA-seq analysis of cancer cell lines",
            "summary": "This study examines gene expression patterns in various cancer cell lines using RNA-seq technology.",
            "organism": "Homo sapiens",
            "platform": "Illumina HiSeq 2500",
            "samples": [
                "Sample1",
                "Sample2",
                "Sample3",
            ],  # Fix: make samples a list
            "publication_date": "2023-01-15",
        }

    def test_summarizer_initialization_with_api_key(self, mock_config):
        """Test summarizer initialization with valid API key."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test_key"}):
            summarizer = SummarizationService(mock_config, disable_cache=True)
            assert summarizer is not None
            assert summarizer.cache is None  # Fix: check cache attribute instead

    def test_summarizer_initialization_without_api_key(self, mock_config):
        """Test summarizer initialization without API key (fallback mode)."""
        mock_config.openai.api_key = None
        with patch.dict("os.environ", {}, clear=True):
            summarizer = SummarizationService(mock_config, disable_cache=True)
            assert summarizer is not None
            # Should initialize in fallback mode

    def test_openai_api_integration_success(self, mock_config, sample_geo_metadata):
        """Test successful OpenAI API integration."""
        mock_response = {
            "choices": [
                {
                    "message": {
                        "content": "This is a comprehensive study analyzing gene expression in cancer cell lines."
                    }
                }
            ]
        }

        with patch("openai.ChatCompletion.create") as mock_openai:
            mock_openai.return_value = mock_response

            summarizer = SummarizationService(mock_config, disable_cache=True)
            result = summarizer.summarize_dataset(sample_geo_metadata)  # Fix: remove await

            assert result is not None
            assert isinstance(result, dict)
            assert "overview" in result

    def test_openai_api_integration_failure(self, mock_config, sample_geo_metadata):
        """Test OpenAI API failure and fallback behavior."""
        with patch("openai.ChatCompletion.create") as mock_openai:
            mock_openai.side_effect = Exception("API Error")

            summarizer = SummarizationService(mock_config, disable_cache=True)
            result = summarizer.summarize_dataset(sample_geo_metadata)  # Fix: remove await

            # Should fallback to basic summarization
            assert result is not None
            assert isinstance(result, dict)
            assert "overview" in result

    def test_cache_disabling_behavior(self, mock_config, sample_geo_metadata):
        """Test that cache is properly disabled when requested."""
        with patch("openai.ChatCompletion.create") as mock_openai:
            mock_openai.return_value = {"choices": [{"message": {"content": "Test summary"}}]}

            summarizer = SummarizationService(mock_config, disable_cache=True)

            # Call summarize twice with same data
            result1 = summarizer.summarize_dataset(sample_geo_metadata)  # Fix: remove await
            result2 = summarizer.summarize_dataset(sample_geo_metadata)  # Fix: remove await

            # Verify cache is disabled
            assert summarizer.cache is None
            assert result1 is not None
            assert result2 is not None

    def test_summarization_quality_validation(self, mock_config, sample_geo_metadata):
        """Test that summarization results meet quality standards."""
        summarizer = SummarizationService(mock_config, disable_cache=True)
        result = summarizer.summarize_dataset(sample_geo_metadata)  # Fix: remove await

        # Validate result structure
        assert isinstance(result, dict)
        assert "overview" in result
        assert len(result["overview"]) > 10  # Reasonable minimum length

        # Validate content includes key information
        overview = result["overview"]
        assert "GSE123456" in overview  # Accession
        assert "3" in overview  # Sample count
        assert "Homo sapiens" in overview  # Organism

    def test_batch_summarization(self, mock_config):
        """Test batch summarization of multiple datasets."""
        datasets = [
            {
                "accession": "GSE001",
                "title": "Study 1",
                "summary": "First study",
                "samples": ["S1"],
            },
            {
                "accession": "GSE002",
                "title": "Study 2",
                "summary": "Second study",
                "samples": ["S1", "S2"],
            },
            {
                "accession": "GSE003",
                "title": "Study 3",
                "summary": "Third study",
                "samples": ["S1", "S2", "S3"],
            },
        ]

        summarizer = SummarizationService(mock_config, disable_cache=True)
        results = []

        for dataset in datasets:
            result = summarizer.summarize_dataset(dataset)  # Fix: remove await
            results.append(result)

        assert len(results) == 3
        assert all(result is not None for result in results)
        assert all(isinstance(result, dict) for result in results)

    def test_error_handling_malformed_data(self, mock_config):
        """Test error handling with malformed input data."""
        malformed_data = {"invalid": "data", "missing_required_fields": True}

        summarizer = SummarizationService(mock_config, disable_cache=True)

        # Should not raise exception, but handle gracefully
        try:
            result = summarizer.summarize_dataset(malformed_data)
            # Should still return a valid dict structure
            assert isinstance(result, dict)
            assert "overview" in result
        except Exception as e:
            # If exception is raised, it should be a known type
            assert isinstance(e, (ValueError, KeyError, TypeError))

    def test_summarization_with_progress_callback(self, mock_config, sample_geo_metadata):
        """Test summarization with progress callback integration."""
        summarizer = SummarizationService(mock_config, disable_cache=True)

        # Test basic summarization (progress callback would be handled at pipeline level)
        result = summarizer.summarize_dataset(sample_geo_metadata)

        assert result is not None
        assert isinstance(result, dict)
        # Progress callback testing would be done at pipeline integration level


def test_summarization_integration_in_pipeline():
    """Test summarization integration within the full pipeline."""
    # This would test the summarizer as part of the complete search pipeline
    # For now, we'll test the interface contract

    from src.omics_oracle.pipeline.pipeline import OmicsOracle

    config = MagicMock()
    config.logging = MagicMock()
    config.logging.level = "INFO"  # Fix: provide proper string value
    config.logging.format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    config.ncbi = MagicMock()
    config.ncbi.email = "test@example.com"
    config.openai = MagicMock()
    config.openai.api_key = "test_key"

    with patch("src.omics_oracle.pipeline.pipeline.UnifiedGEOClient"), patch(
        "src.omics_oracle.pipeline.pipeline.SummarizationService"
    ) as mock_summarizer, patch("src.omics_oracle.pipeline.pipeline.PromptInterpreter"), patch(
        "src.omics_oracle.pipeline.pipeline.BiomedicalNER"
    ), patch(
        "src.omics_oracle.pipeline.pipeline.EnhancedBiologicalSynonymMapper"
    ), patch(
        "src.omics_oracle.pipeline.pipeline.ImprovedSearchService"
    ):
        pipeline = OmicsOracle(config, disable_cache=True)

        # Verify summarizer was initialized with cache disabled
        mock_summarizer.assert_called_with(config, disable_cache=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
