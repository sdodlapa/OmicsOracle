"""
Test progress callback setup and functionality.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from omics_oracle.core.config import Config
from omics_oracle.pipeline.pipeline import OmicsOracle, ProgressEvent


class TestProgressCallback:
    """Test progress callback setup and operation."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        config = MagicMock(spec=Config)
        config.logging.level = "INFO"
        config.logging.format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        return config

    @pytest.fixture
    def mock_pipeline(self, mock_config):
        """Create a mock pipeline for testing."""
        with patch("src.omics_oracle.geo_tools.geo_client.UnifiedGEOClient"), patch(
            "src.omics_oracle.services.summarizer.SummarizationService"
        ), patch("src.omics_oracle.nlp.prompt_interpreter.PromptInterpreter"), patch(
            "src.omics_oracle.nlp.biomedical_ner.BiomedicalNER"
        ), patch(
            "src.omics_oracle.nlp.biomedical_ner.EnhancedBiologicalSynonymMapper"
        ), patch(
            "src.omics_oracle.services.improved_search.ImprovedSearchService"
        ):
            pipeline = OmicsOracle(config=mock_config, disable_cache=True)
            return pipeline

    def test_progress_callback_setup(self, mock_pipeline):
        """Test setting up progress callback."""
        callback = AsyncMock()

        mock_pipeline.set_progress_callback(callback)

        assert mock_pipeline._progress_callback == callback

    def test_progress_callback_none_by_default(self, mock_pipeline):
        """Test that progress callback is None by default."""
        assert mock_pipeline._progress_callback is None

    @pytest.mark.asyncio
    async def test_progress_callback_execution(self, mock_pipeline):
        """Test that progress callback is executed when set."""
        callback = AsyncMock()
        mock_pipeline.set_progress_callback(callback)

        # Create a mock query result
        query_result = MagicMock()
        query_result.query_id = "test_query_001"
        query_result.add_progress_event = MagicMock()

        # Call _report_progress
        await mock_pipeline._report_progress(
            query_result,
            "test_stage",
            "test_message",
            50.0,
            {"detail": "test_detail"},
        )

        # Verify callback was called
        callback.assert_called_once()

        # Verify the call arguments
        call_args = callback.call_args
        assert call_args[0][0] == "test_query_001"  # query_id

        # Verify the ProgressEvent
        progress_event = call_args[0][1]
        assert isinstance(progress_event, ProgressEvent)
        assert progress_event.stage == "test_stage"
        assert progress_event.message == "test_message"
        assert progress_event.percentage == 50.0
        assert progress_event.detail == {"detail": "test_detail"}

    @pytest.mark.asyncio
    async def test_progress_callback_exception_handling(self, mock_pipeline):
        """Test that progress callback exceptions are handled gracefully."""
        # Create a callback that raises an exception
        callback = AsyncMock(side_effect=Exception("Callback failed"))
        mock_pipeline.set_progress_callback(callback)

        query_result = MagicMock()
        query_result.query_id = "test_query_001"
        query_result.add_progress_event = MagicMock()

        # This should not raise an exception
        try:
            await mock_pipeline._report_progress(query_result, "test_stage", "test_message", 50.0)
        except Exception:
            pytest.fail("Progress callback exception should be handled")

    @pytest.mark.asyncio
    async def test_progress_callback_with_no_callback_set(self, mock_pipeline):
        """Test progress reporting when no callback is set."""
        query_result = MagicMock()
        query_result.query_id = "test_query_001"
        query_result.add_progress_event = MagicMock()

        # This should not raise an exception
        await mock_pipeline._report_progress(query_result, "test_stage", "test_message", 50.0)

        # Verify that query result was still updated
        query_result.add_progress_event.assert_called_once()

    def test_progress_event_creation(self):
        """Test ProgressEvent creation and properties."""
        event = ProgressEvent(
            stage="test_stage",
            message="test_message",
            percentage=75.0,
            detail={"key": "value"},
        )

        assert event.stage == "test_stage"
        assert event.message == "test_message"
        assert event.percentage == 75.0
        assert event.detail == {"key": "value"}
        assert event.timestamp is not None

    def test_progress_event_default_values(self):
        """Test ProgressEvent default values."""
        event = ProgressEvent(stage="test_stage", message="test_message")

        assert event.stage == "test_stage"
        assert event.message == "test_message"
        assert event.percentage == 0.0
        assert event.detail is None
        assert event.timestamp is not None

    @pytest.mark.asyncio
    async def test_multiple_progress_callbacks(self, mock_pipeline):
        """Test that only the last set callback is used."""
        callback1 = AsyncMock()
        callback2 = AsyncMock()

        # Set first callback
        mock_pipeline.set_progress_callback(callback1)
        assert mock_pipeline._progress_callback == callback1

        # Set second callback (should replace first)
        mock_pipeline.set_progress_callback(callback2)
        assert mock_pipeline._progress_callback == callback2

        query_result = MagicMock()
        query_result.query_id = "test_query_001"
        query_result.add_progress_event = MagicMock()

        await mock_pipeline._report_progress(query_result, "test_stage", "test_message", 50.0)

        # Only the second callback should be called
        callback1.assert_not_called()
        callback2.assert_called_once()
