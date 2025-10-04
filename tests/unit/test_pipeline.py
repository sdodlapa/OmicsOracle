"""
Unit tests for the OmicsOracle pipeline module.
"""

from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add src to path
# Import project modules after path setup  # noqa: E402
from omics_oracle.pipeline.pipeline import OmicsOracle, QueryResult, QueryStatus, ResultFormat  # noqa: E402


class TestQueryResult:
    """Test cases for QueryResult class."""

    def test_query_result_initialization(self):
        """Test QueryResult initialization."""
        result = QueryResult(
            query_id="test_001",
            original_query="find cancer studies",
            status=QueryStatus.PENDING,
            start_time=datetime.now(),
        )

        assert result.query_id == "test_001"
        assert result.original_query == "find cancer studies"
        assert result.status == QueryStatus.PENDING
        assert result.start_time is not None
        assert result.end_time is None
        assert result.intent is None
        assert result.entities == {}
        assert result.geo_ids == []
        assert result.metadata == []
        assert result.error is None
        assert result.processing_steps == []

    def test_query_result_duration(self):
        """Test duration calculation."""
        start_time = datetime.now()
        result = QueryResult(
            query_id="test_001",
            original_query="test",
            status=QueryStatus.COMPLETED,
            start_time=start_time,
        )

        # Duration should be None when end_time is None
        assert result.duration is None

        # Set end_time and check duration
        result.end_time = datetime.now()
        assert result.duration is not None
        assert result.duration >= 0

    def test_query_result_status_properties(self):
        """Test status checking properties."""
        result = QueryResult(
            query_id="test_001",
            original_query="test",
            status=QueryStatus.COMPLETED,
            start_time=datetime.now(),
        )

        assert result.is_completed is True
        assert result.is_failed is False

        result.status = QueryStatus.FAILED
        assert result.is_completed is False
        assert result.is_failed is True

    def test_add_step(self):
        """Test adding processing steps."""
        result = QueryResult(
            query_id="test_001",
            original_query="test",
            status=QueryStatus.PENDING,
            start_time=datetime.now(),
        )

        result.add_step("parsing", {"intent": "search"})

        assert len(result.processing_steps) == 1
        step = result.processing_steps[0]
        assert step["step"] == "parsing"
        assert step["details"] == {"intent": "search"}
        assert "timestamp" in step


class TestOmicsOracle:
    """Test cases for OmicsOracle pipeline class."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        config = MagicMock()
        config.logging = MagicMock()
        config.logging.level = "INFO"
        config.logging.format = "%(message)s"
        return config

    @pytest.fixture
    def mock_oracle(self, mock_config):
        """Mock OmicsOracle instance for testing."""
        with (
            patch("omics_oracle.pipeline.pipeline.UnifiedGEOClient"),
            patch("omics_oracle.pipeline.pipeline.PromptInterpreter"),
            patch("omics_oracle.pipeline.pipeline.BiomedicalNER"),
            patch("omics_oracle.pipeline.pipeline.EnhancedBiologicalSynonymMapper"),
        ):
            oracle = OmicsOracle(mock_config)
            # Mock the components
            oracle.geo_client = AsyncMock()
            oracle.nlp_interpreter = MagicMock()
            oracle.biomedical_ner = MagicMock()
            oracle.synonym_mapper = MagicMock()

            return oracle

    def test_oracle_initialization(self, mock_config):
        """Test OmicsOracle initialization."""
        with (
            patch("omics_oracle.pipeline.pipeline.UnifiedGEOClient"),
            patch("omics_oracle.pipeline.pipeline.PromptInterpreter"),
            patch("omics_oracle.pipeline.pipeline.BiomedicalNER"),
            patch("omics_oracle.pipeline.pipeline.EnhancedBiologicalSynonymMapper"),
        ):
            oracle = OmicsOracle(mock_config)

            assert oracle.config == mock_config
            assert oracle._query_counter == 0
            assert oracle._active_queries == {}

    def test_generate_query_id(self, mock_oracle):
        """Test query ID generation."""
        query_id_1 = mock_oracle._generate_query_id()
        query_id_2 = mock_oracle._generate_query_id()

        assert query_id_1 == "query_000001"
        assert query_id_2 == "query_000002"
        assert mock_oracle._query_counter == 2

    @pytest.mark.asyncio
    async def test_process_query_success(self, mock_oracle):
        """Test successful query processing."""
        # Set up mocks
        mock_oracle.nlp_interpreter.classify_intent.return_value = {
            "intent": "search",
            "confidence": 0.9,
        }
        mock_oracle.biomedical_ner.extract_biomedical_entities.return_value = {
            "genes": [{"text": "BRCA1", "start": 0, "end": 5}]
        }
        mock_oracle.synonym_mapper.get_synonyms.return_value = [
            "BRCA1",
            "breast cancer 1",
        ]
        mock_oracle.geo_client.search_geo_series.return_value = ["GSE123456"]
        mock_oracle.geo_client.get_geo_metadata.return_value = {
            "accession": "GSE123456",
            "title": "BRCA1 expression study",
            "summary": "Analysis of BRCA1 expression in breast cancer",
        }

        # Process query
        result = await mock_oracle.process_query("BRCA1 expression in cancer")

        # Verify result
        assert result.status == QueryStatus.COMPLETED
        assert result.intent == "search"
        assert result.geo_ids == ["GSE123456"]
        assert len(result.metadata) == 1
        assert result.error is None
        assert result.end_time is not None
        assert len(result.processing_steps) > 0

    @pytest.mark.asyncio
    async def test_process_query_failure(self, mock_oracle):
        """Test query processing failure."""
        # Set up mocks to raise exception
        mock_oracle.nlp_interpreter.classify_intent.side_effect = Exception("NLP failed")

        # Process query and expect exception
        with pytest.raises(Exception):
            await mock_oracle.process_query("test query")

        # Check that query was marked as failed
        query_id = list(mock_oracle._active_queries.keys())[0]
        result = mock_oracle._active_queries[query_id]
        assert result.status == QueryStatus.FAILED
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_get_query_status(self, mock_oracle):
        """Test query status retrieval."""
        # Add a mock query
        result = QueryResult(
            query_id="test_001",
            original_query="test",
            status=QueryStatus.COMPLETED,
            start_time=datetime.now(),
        )
        mock_oracle._active_queries["test_001"] = result

        # Test status retrieval
        retrieved_result = await mock_oracle.get_query_status("test_001")
        assert retrieved_result == result

        # Test non-existent query
        non_existent = await mock_oracle.get_query_status("non_existent")
        assert non_existent is None

    @pytest.mark.asyncio
    async def test_list_active_queries(self, mock_oracle):
        """Test listing active queries."""
        # Initially empty
        queries = await mock_oracle.list_active_queries()
        assert queries == []

        # Add some queries
        mock_oracle._active_queries["query_001"] = MagicMock()
        mock_oracle._active_queries["query_002"] = MagicMock()

        queries = await mock_oracle.list_active_queries()
        assert len(queries) == 2
        assert "query_001" in queries
        assert "query_002" in queries

    @pytest.mark.asyncio
    async def test_cancel_query(self, mock_oracle):
        """Test query cancellation."""
        # Add a pending query
        result = QueryResult(
            query_id="test_001",
            original_query="test",
            status=QueryStatus.PENDING,
            start_time=datetime.now(),
        )
        mock_oracle._active_queries["test_001"] = result

        # Cancel the query
        success = await mock_oracle.cancel_query("test_001")
        assert success is True
        assert result.status == QueryStatus.FAILED
        assert result.error == "Query cancelled by user"
        assert result.end_time is not None

        # Try to cancel non-existent query
        success = await mock_oracle.cancel_query("non_existent")
        assert success is False

    @pytest.mark.asyncio
    async def test_cleanup_completed_queries(self, mock_oracle):
        """Test cleanup of old completed queries."""
        # Add old completed query
        old_result = QueryResult(
            query_id="old_001",
            original_query="old test",
            status=QueryStatus.COMPLETED,
            start_time=datetime.now(),
            end_time=datetime.now(),
        )
        # Make it old by manually setting end_time
        old_result.end_time = datetime(2023, 1, 1)
        mock_oracle._active_queries["old_001"] = old_result

        # Add recent completed query
        recent_result = QueryResult(
            query_id="recent_001",
            original_query="recent test",
            status=QueryStatus.COMPLETED,
            start_time=datetime.now(),
            end_time=datetime.now(),
        )
        mock_oracle._active_queries["recent_001"] = recent_result

        # Cleanup old queries
        cleaned_count = await mock_oracle.cleanup_completed_queries(max_age_hours=1)

        assert cleaned_count == 1
        assert "old_001" not in mock_oracle._active_queries
        assert "recent_001" in mock_oracle._active_queries

    @pytest.mark.asyncio
    async def test_close(self, mock_oracle):
        """Test pipeline cleanup."""
        await mock_oracle.close()
        mock_oracle.geo_client.close.assert_called_once()


class TestEnums:
    """Test cases for enum classes."""

    def test_query_status_enum(self):
        """Test QueryStatus enum values."""
        assert QueryStatus.PENDING.value == "pending"
        assert QueryStatus.PARSING.value == "parsing"
        assert QueryStatus.SEARCHING.value == "searching"
        assert QueryStatus.PROCESSING.value == "processing"
        assert QueryStatus.COMPLETED.value == "completed"
        assert QueryStatus.FAILED.value == "failed"

    def test_result_format_enum(self):
        """Test ResultFormat enum values."""
        assert ResultFormat.JSON.value == "json"
        assert ResultFormat.CSV.value == "csv"
        assert ResultFormat.TSV.value == "tsv"
        assert ResultFormat.EXCEL.value == "excel"
        assert ResultFormat.SUMMARY.value == "summary"
