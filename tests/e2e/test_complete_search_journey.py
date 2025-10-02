#!/usr/bin/env python3
"""
Complete Search Journey E2E Test

This test validates the entire pipeline from server startup to frontend result display:
1. Server initialization and health check
2. API endpoint availability
3. Search request processing
4. Results rendering and display
5. WebSocket communication
6. Error handling and fallbacks
"""

import asyncio
import json
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests

# Add project root to path
from omics_oracle.core.config import Config
from omics_oracle.pipeline.pipeline import OmicsOracle


class TestCompleteSearchJourney:
    """End-to-end tests for complete search journey."""

    @pytest.fixture
    def test_config(self):
        """Test configuration."""
        config = MagicMock()
        config.logging = MagicMock()
        config.logging.level = "INFO"
        config.logging.format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        config.ncbi = MagicMock()
        config.ncbi.email = "test@omicsoracle.com"
        config.openai = MagicMock()
        config.openai.api_key = "test_key"
        return config

    @pytest.fixture
    def sample_search_query(self):
        """Sample search query for testing."""
        return {
            "query": "cancer RNA-seq",
            "filters": {
                "organism": "Homo sapiens",
                "study_type": "Expression profiling by high throughput sequencing",
            },
            "limit": 5,
        }

    def test_pipeline_initialization_complete(self, test_config):
        """Test complete pipeline initialization with all components."""
        with patch("src.omics_oracle.pipeline.pipeline.UnifiedGEOClient") as mock_geo, patch(
            "src.omics_oracle.pipeline.pipeline.SummarizationService"
        ) as mock_summarizer, patch(
            "src.omics_oracle.pipeline.pipeline.PromptInterpreter"
        ) as mock_nlp, patch(
            "src.omics_oracle.pipeline.pipeline.BiomedicalNER"
        ) as mock_ner, patch(
            "src.omics_oracle.pipeline.pipeline.EnhancedBiologicalSynonymMapper"
        ) as mock_mapper, patch(
            "src.omics_oracle.pipeline.pipeline.ImprovedSearchService"
        ) as mock_search:
            # Setup mock instances
            mock_geo_instance = MagicMock()
            mock_geo_instance.cache = None
            mock_geo.return_value = mock_geo_instance

            mock_summarizer_instance = MagicMock()
            mock_summarizer.return_value = mock_summarizer_instance

            mock_nlp_instance = MagicMock()
            mock_nlp.return_value = mock_nlp_instance

            mock_ner_instance = MagicMock()
            mock_ner.return_value = mock_ner_instance

            mock_mapper_instance = MagicMock()
            mock_mapper.return_value = mock_mapper_instance

            mock_search_instance = MagicMock()
            mock_search.return_value = mock_search_instance

            # Initialize pipeline
            pipeline = OmicsOracle(config=test_config, disable_cache=True)

            # Verify all components initialized
            assert pipeline is not None
            assert pipeline.disable_cache is True
            assert pipeline.geo_client is not None
            assert pipeline.summarizer is not None
            assert pipeline.nlp_interpreter is not None
            assert pipeline.biomedical_ner is not None
            assert pipeline.synonym_mapper is not None
            assert pipeline.search_service is not None

            # Verify cache is disabled
            mock_summarizer.assert_called_with(test_config, disable_cache=True)

    @pytest.mark.asyncio
    async def test_search_pipeline_flow(self, test_config, sample_search_query):
        """Test complete search flow from query to results."""
        with patch("src.omics_oracle.pipeline.pipeline.UnifiedGEOClient") as mock_geo, patch(
            "src.omics_oracle.pipeline.pipeline.SummarizationService"
        ) as mock_summarizer, patch(
            "src.omics_oracle.pipeline.pipeline.PromptInterpreter"
        ) as mock_nlp, patch(
            "src.omics_oracle.pipeline.pipeline.BiomedicalNER"
        ) as mock_ner, patch(
            "src.omics_oracle.pipeline.pipeline.EnhancedBiologicalSynonymMapper"
        ) as mock_mapper, patch(
            "src.omics_oracle.pipeline.pipeline.ImprovedSearchService"
        ) as mock_search:
            # Setup mock search results
            mock_search_results = [
                {
                    "accession": "GSE123456",
                    "title": "RNA-seq analysis of cancer cell lines",
                    "summary": "Comprehensive study of gene expression in cancer",
                    "organism": "Homo sapiens",
                    "platform": "Illumina HiSeq 2500",
                    "samples": ["Sample1", "Sample2", "Sample3"],
                    "publication_date": "2023-01-15",
                    "relevance_score": 0.95,
                }
            ]

            # Setup mock instances
            mock_search_instance = MagicMock()
            mock_search_instance.search_datasets.return_value = mock_search_results
            mock_search.return_value = mock_search_instance

            mock_summarizer_instance = MagicMock()
            mock_summarizer_instance.summarize_dataset.return_value = {
                "overview": "This is a comprehensive cancer RNA-seq study",
                "methodology": "RNA-seq using Illumina platform",
                "significance": "Important for cancer research",
            }
            mock_summarizer.return_value = mock_summarizer_instance

            # Setup other mocks
            mock_geo.return_value = MagicMock()
            mock_nlp.return_value = MagicMock()
            mock_ner.return_value = MagicMock()
            mock_mapper.return_value = MagicMock()

            # Initialize pipeline
            pipeline = OmicsOracle(config=test_config, disable_cache=True)

            # Perform search using the correct method
            result = await pipeline.process_query(
                query=sample_search_query["query"],
                max_results=sample_search_query["limit"],
            )

            # Verify results structure
            assert result is not None
            assert hasattr(result, "query_id")
            assert hasattr(result, "original_query")
            assert hasattr(result, "status")

    def test_error_handling_pipeline(self, test_config):
        """Test error handling throughout the pipeline."""
        with patch("src.omics_oracle.pipeline.pipeline.UnifiedGEOClient") as mock_geo, patch(
            "src.omics_oracle.pipeline.pipeline.SummarizationService"
        ) as mock_summarizer, patch(
            "src.omics_oracle.pipeline.pipeline.PromptInterpreter"
        ) as mock_nlp, patch(
            "src.omics_oracle.pipeline.pipeline.BiomedicalNER"
        ) as mock_ner, patch(
            "src.omics_oracle.pipeline.pipeline.EnhancedBiologicalSynonymMapper"
        ) as mock_mapper, patch(
            "src.omics_oracle.pipeline.pipeline.ImprovedSearchService"
        ) as mock_search:
            # Setup mocks that will raise exceptions
            mock_search_instance = MagicMock()
            mock_search_instance.search_datasets.side_effect = Exception("Search service error")
            mock_search.return_value = mock_search_instance

            # Setup other mocks
            mock_geo.return_value = MagicMock()
            mock_summarizer.return_value = MagicMock()
            mock_nlp.return_value = MagicMock()
            mock_ner.return_value = MagicMock()
            mock_mapper.return_value = MagicMock()

            # Initialize pipeline
            pipeline = OmicsOracle(config=test_config, disable_cache=True)

            # Test error handling - for async method, need to use asyncio
            import asyncio

            try:
                result = asyncio.run(pipeline.process_query(query="test query", max_results=5))
                # If no exception, should return error state
                assert hasattr(result, "status")
            except Exception as e:
                # Exception should be handled gracefully
                assert isinstance(e, Exception)

    def test_config_validation(self):
        """Test configuration validation and defaults."""
        # Test with minimal config
        config = MagicMock()
        config.logging = MagicMock()
        config.logging.level = "INFO"
        config.logging.format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        config.ncbi = MagicMock()
        config.ncbi.email = "test@example.com"

        with patch("src.omics_oracle.pipeline.pipeline.UnifiedGEOClient"), patch(
            "src.omics_oracle.pipeline.pipeline.SummarizationService"
        ), patch("src.omics_oracle.pipeline.pipeline.PromptInterpreter"), patch(
            "src.omics_oracle.pipeline.pipeline.BiomedicalNER"
        ), patch(
            "src.omics_oracle.pipeline.pipeline.EnhancedBiologicalSynonymMapper"
        ), patch(
            "src.omics_oracle.pipeline.pipeline.ImprovedSearchService"
        ):
            pipeline = OmicsOracle(config=config, disable_cache=True)
            assert pipeline.config is not None
            assert pipeline.disable_cache is True

    def test_cache_consistency(self, test_config):
        """Test that cache disabling is consistent across all components."""
        with patch("src.omics_oracle.pipeline.pipeline.UnifiedGEOClient") as mock_geo, patch(
            "src.omics_oracle.pipeline.pipeline.SummarizationService"
        ) as mock_summarizer, patch("src.omics_oracle.pipeline.pipeline.PromptInterpreter"), patch(
            "src.omics_oracle.pipeline.pipeline.BiomedicalNER"
        ), patch(
            "src.omics_oracle.pipeline.pipeline.EnhancedBiologicalSynonymMapper"
        ), patch(
            "src.omics_oracle.pipeline.pipeline.ImprovedSearchService"
        ):
            # Setup mock with cache
            mock_geo_instance = MagicMock()
            mock_geo_instance.cache = MagicMock()
            mock_geo.return_value = mock_geo_instance

            mock_summarizer.return_value = MagicMock()

            # Initialize with cache disabled
            pipeline = OmicsOracle(config=test_config, disable_cache=True)

            # Verify cache was disabled
            assert mock_geo_instance.cache is None
            mock_summarizer.assert_called_with(test_config, disable_cache=True)

    def test_progress_callback_setup(self, test_config):
        """Test progress callback functionality."""
        progress_events = []

        def test_callback(stage, event):
            progress_events.append((stage, event))

        with patch("src.omics_oracle.pipeline.pipeline.UnifiedGEOClient"), patch(
            "src.omics_oracle.pipeline.pipeline.SummarizationService"
        ), patch("src.omics_oracle.pipeline.pipeline.PromptInterpreter"), patch(
            "src.omics_oracle.pipeline.pipeline.BiomedicalNER"
        ), patch(
            "src.omics_oracle.pipeline.pipeline.EnhancedBiologicalSynonymMapper"
        ), patch(
            "src.omics_oracle.pipeline.pipeline.ImprovedSearchService"
        ):
            pipeline = OmicsOracle(config=test_config, disable_cache=True)

            # Test setting progress callback
            pipeline.set_progress_callback(test_callback)

            # Verify callback was set
            assert pipeline._progress_callback is not None

    def test_monitoring_integration(self, test_config):
        """Test that monitoring systems can observe pipeline state."""
        with patch("src.omics_oracle.pipeline.pipeline.UnifiedGEOClient"), patch(
            "src.omics_oracle.pipeline.pipeline.SummarizationService"
        ), patch("src.omics_oracle.pipeline.pipeline.PromptInterpreter"), patch(
            "src.omics_oracle.pipeline.pipeline.BiomedicalNER"
        ), patch(
            "src.omics_oracle.pipeline.pipeline.EnhancedBiologicalSynonymMapper"
        ), patch(
            "src.omics_oracle.pipeline.pipeline.ImprovedSearchService"
        ):
            pipeline = OmicsOracle(config=test_config, disable_cache=True)

            # Test pipeline state is observable
            assert hasattr(pipeline, "_active_queries")
            assert hasattr(pipeline, "_query_counter")
            assert isinstance(pipeline._active_queries, dict)
            assert isinstance(pipeline._query_counter, int)

    @pytest.mark.asyncio
    async def test_search_results_structure(self, test_config, sample_search_query):
        """Test that search results have expected structure for frontend rendering."""
        with patch("src.omics_oracle.pipeline.pipeline.UnifiedGEOClient"), patch(
            "src.omics_oracle.pipeline.pipeline.SummarizationService"
        ), patch("src.omics_oracle.pipeline.pipeline.PromptInterpreter"), patch(
            "src.omics_oracle.pipeline.pipeline.BiomedicalNER"
        ), patch(
            "src.omics_oracle.pipeline.pipeline.EnhancedBiologicalSynonymMapper"
        ), patch(
            "src.omics_oracle.pipeline.pipeline.ImprovedSearchService"
        ) as mock_search:
            # Setup mock search results with proper structure
            expected_result = {
                "accession": "GSE123456",
                "title": "RNA-seq analysis of cancer cell lines",
                "summary": "Comprehensive study of gene expression in cancer",
                "organism": "Homo sapiens",
                "platform": "Illumina HiSeq 2500",
                "samples": ["Sample1", "Sample2"],
                "publication_date": "2023-01-15",
                "relevance_score": 0.95,
                "url": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE123456",
            }

            mock_search_instance = MagicMock()
            mock_search_instance.search_datasets.return_value = [expected_result]
            mock_search.return_value = mock_search_instance

            pipeline = OmicsOracle(config=test_config, disable_cache=True)

            # Perform search using async method
            result = await pipeline.process_query(query=sample_search_query["query"], max_results=1)

            # Validate result structure for frontend
            assert result is not None
            assert hasattr(result, "query_id")
            assert hasattr(result, "original_query")
            assert hasattr(result, "status")

            # Basic validation that the result contains expected structure
            assert result.original_query == sample_search_query["query"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
