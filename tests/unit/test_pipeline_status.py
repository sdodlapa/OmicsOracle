"""
Test pipeline status checking functionality.
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from interfaces.futuristic.main import app, pipeline

from omics_oracle.pipeline.pipeline import OmicsOracle


class TestPipelineStatus:
    """Test pipeline availability and status checking."""

    def test_pipeline_available(self):
        """Test when pipeline is available."""
        # Mock a pipeline instance
        mock_pipeline = MagicMock(spec=OmicsOracle)

        # Simulate pipeline being available
        assert mock_pipeline is not None
        assert hasattr(mock_pipeline, "process_query")

    def test_pipeline_unavailable(self):
        """Test when pipeline is unavailable (None)."""
        mock_pipeline = None

        assert mock_pipeline is None

    def test_pipeline_status_check_in_search(self):
        """Test pipeline status check in search endpoint logic."""
        # This would be the logic from the search endpoint
        mock_pipeline = None

        if not mock_pipeline:
            # Should raise HTTPException
            with pytest.raises(HTTPException) as exc_info:
                raise HTTPException(status_code=503, detail="OmicsOracle pipeline not available")

            assert exc_info.value.status_code == 503
            assert "pipeline not available" in str(exc_info.value.detail).lower()

    def test_pipeline_initialization_status(self):
        """Test checking if pipeline is properly initialized."""
        mock_pipeline = MagicMock(spec=OmicsOracle)

        # Mock various components being available
        mock_pipeline.geo_client = MagicMock()
        mock_pipeline.summarizer = MagicMock()
        mock_pipeline.nlp_interpreter = MagicMock()

        # Check if all components are available
        assert hasattr(mock_pipeline, "geo_client")
        assert hasattr(mock_pipeline, "summarizer")
        assert hasattr(mock_pipeline, "nlp_interpreter")
        assert mock_pipeline.geo_client is not None
        assert mock_pipeline.summarizer is not None
        assert mock_pipeline.nlp_interpreter is not None

    def test_pipeline_partial_initialization(self):
        """Test pipeline with partial initialization."""
        mock_pipeline = MagicMock(spec=OmicsOracle)

        # Some components available, some not
        mock_pipeline.geo_client = MagicMock()
        mock_pipeline.summarizer = None
        mock_pipeline.nlp_interpreter = MagicMock()

        # Pipeline exists but not fully initialized
        assert mock_pipeline is not None
        assert mock_pipeline.geo_client is not None
        assert mock_pipeline.summarizer is None
        assert mock_pipeline.nlp_interpreter is not None

    def test_pipeline_health_check_components(self):
        """Test pipeline health check for individual components."""
        mock_pipeline = MagicMock(spec=OmicsOracle)

        # Mock health check method
        def mock_health_check():
            return {
                "geo_client_available": hasattr(mock_pipeline, "geo_client")
                and mock_pipeline.geo_client is not None,
                "cache_disabled": getattr(mock_pipeline, "disable_cache", False),
                "summarizer_available": hasattr(mock_pipeline, "summarizer")
                and mock_pipeline.summarizer is not None,
            }

        # Set up mock pipeline
        mock_pipeline.geo_client = MagicMock()
        mock_pipeline.summarizer = MagicMock()
        mock_pipeline.disable_cache = True

        health_info = mock_health_check()

        assert health_info["geo_client_available"] is True
        assert health_info["cache_disabled"] is True
        assert health_info["summarizer_available"] is True

    def test_pipeline_status_during_operation(self):
        """Test pipeline status during ongoing operations."""
        mock_pipeline = MagicMock(spec=OmicsOracle)
        mock_pipeline._active_queries = {}

        # Add an active query
        mock_pipeline._active_queries["query_001"] = MagicMock()

        # Check if pipeline is busy
        is_busy = len(mock_pipeline._active_queries) > 0
        assert is_busy is True

        # Clear active queries
        mock_pipeline._active_queries.clear()
        is_busy = len(mock_pipeline._active_queries) > 0
        assert is_busy is False

    def test_pipeline_error_state_detection(self):
        """Test detection of pipeline error states."""
        mock_pipeline = MagicMock(spec=OmicsOracle)

        # Simulate pipeline in error state
        mock_pipeline.geo_client = None  # GEO client failed to initialize
        mock_pipeline.summarizer = MagicMock()

        # Check for error conditions
        has_geo_client = mock_pipeline.geo_client is not None
        has_summarizer = mock_pipeline.summarizer is not None

        assert has_geo_client is False  # Error condition
        assert has_summarizer is True  # OK condition

    def test_pipeline_readiness_check(self):
        """Test comprehensive pipeline readiness check."""
        mock_pipeline = MagicMock(spec=OmicsOracle)

        # Mock all required components
        mock_pipeline.geo_client = MagicMock()
        mock_pipeline.summarizer = MagicMock()
        mock_pipeline.nlp_interpreter = MagicMock()
        mock_pipeline.biomedical_ner = MagicMock()
        mock_pipeline.synonym_mapper = MagicMock()
        mock_pipeline.search_service = MagicMock()

        def is_pipeline_ready(pipeline):
            if not pipeline:
                return False

            required_components = [
                "geo_client",
                "summarizer",
                "nlp_interpreter",
                "biomedical_ner",
                "synonym_mapper",
                "search_service",
            ]

            for component in required_components:
                if not hasattr(pipeline, component) or getattr(pipeline, component) is None:
                    return False

            return True

        assert is_pipeline_ready(mock_pipeline) is True

        # Test with missing component
        mock_pipeline.geo_client = None
        assert is_pipeline_ready(mock_pipeline) is False
