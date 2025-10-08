"""
Unit tests for AI summarization library.

Tests the AI-powered summarization functionality including models,
prompts, utilities, and the main client with mocked OpenAI responses.

Coverage Target: 80%+
"""

from unittest.mock import MagicMock, Mock, patch

import pytest
from pydantic import ValidationError

from omics_oracle_v2.core import AISettings, Settings
from omics_oracle_v2.core.exceptions import AIError
from omics_oracle_v2.lib.ai import (
    BatchSummaryRequest,
    BatchSummaryResponse,
    ModelInfo,
    PromptBuilder,
    SummarizationClient,
    SummaryRequest,
    SummaryResponse,
    SummaryType,
)
from omics_oracle_v2.lib.ai.utils import (
    aggregate_batch_statistics,
    estimate_tokens,
    extract_technical_details,
    prepare_metadata,
    truncate_text,
)

# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def sample_metadata():
    """Sample genomics dataset metadata."""
    return {
        "title": "RNA-seq analysis of cancer cells under treatment",
        "summary": "This study examines gene expression changes in cancer cells treated with drug X. "
        "We performed RNA-seq on 24 samples and identified 500 differentially expressed genes.",
        "organism": "Homo sapiens",
        "platform": "Illumina HiSeq 2500",
        "samples_count": 24,
        "submission_date": "2024-01-15",
        "pubmed_id": "12345678",
    }


@pytest.fixture
def settings():
    """Test settings with AI configuration."""
    return Settings(
        ai=AISettings(
            openai_api_key="test-key-123",
            model="gpt-4",
            max_tokens=1000,
            temperature=0.7,
            timeout=60,
        )
    )


# ============================================================================
# Models Tests
# ============================================================================


class TestSummaryType:
    """Test SummaryType enum."""

    def test_enum_values(self):
        """Test all enum values exist."""
        assert SummaryType.BRIEF.value == "brief"
        assert SummaryType.COMPREHENSIVE.value == "comprehensive"
        assert SummaryType.TECHNICAL.value == "technical"
        assert SummaryType.SIGNIFICANCE.value == "significance"

    def test_enum_membership(self):
        """Test enum membership checks."""
        assert SummaryType.BRIEF in SummaryType
        assert "invalid" not in [t.value for t in SummaryType]


class TestSummaryRequest:
    """Test SummaryRequest model."""

    def test_create_minimal(self, sample_metadata):
        """Test creating request with minimal fields."""
        request = SummaryRequest(metadata=sample_metadata)
        assert request.metadata == sample_metadata
        assert request.query_context is None
        assert request.summary_type == SummaryType.COMPREHENSIVE
        assert request.dataset_id is None

    def test_create_full(self, sample_metadata):
        """Test creating request with all fields."""
        request = SummaryRequest(
            metadata=sample_metadata,
            query_context="cancer treatment response",
            summary_type=SummaryType.BRIEF,
            dataset_id="GSE123456",
            overrides={"max_tokens": 500},
        )
        assert request.query_context == "cancer treatment response"
        assert request.summary_type == SummaryType.BRIEF
        assert request.dataset_id == "GSE123456"
        assert request.overrides == {"max_tokens": 500}

    def test_validation_empty_metadata(self):
        """Test validation fails on empty metadata."""
        with pytest.raises(ValidationError):
            SummaryRequest(metadata={})


class TestSummaryResponse:
    """Test SummaryResponse model."""

    def test_create_response(self):
        """Test creating summary response."""
        response = SummaryResponse(
            dataset_id="GSE123456",
            summary_type=SummaryType.COMPREHENSIVE,
            overview="This study examines...",
            methodology="RNA-seq was performed...",
            significance="The findings reveal...",
            technical_details="Platform: Illumina HiSeq",
            brief="Brief summary",
            token_usage={"total": 850},
            model_used="gpt-4",
        )
        assert response.dataset_id == "GSE123456"
        assert response.overview == "This study examines..."
        assert response.token_usage == {"total": 850}

    def test_has_content_true(self):
        """Test has_content returns True when content exists."""
        response = SummaryResponse(
            dataset_id="GSE123",
            summary_type=SummaryType.COMPREHENSIVE,
            overview="Overview text",
        )
        assert response.has_content() is True

    def test_has_content_false(self):
        """Test has_content returns False when no content."""
        response = SummaryResponse(
            dataset_id="GSE123",
            summary_type=SummaryType.COMPREHENSIVE,
        )
        assert response.has_content() is False

    def test_get_primary_summary_comprehensive(self):
        """Test get_primary_summary returns overview for comprehensive."""
        response = SummaryResponse(
            dataset_id="GSE123",
            summary_type=SummaryType.COMPREHENSIVE,
            overview="Overview text",
            methodology="Method text",
        )
        assert response.get_primary_summary() == "Overview text"

    def test_get_primary_summary_brief(self):
        """Test get_primary_summary returns brief for brief type."""
        response = SummaryResponse(
            dataset_id="GSE123",
            summary_type=SummaryType.BRIEF,
            brief="Brief text",
            overview="Overview text",
        )
        assert response.get_primary_summary() == "Brief text"

    def test_get_primary_summary_fallback(self):
        """Test get_primary_summary returns first available."""
        response = SummaryResponse(
            dataset_id="GSE123",
            summary_type=SummaryType.COMPREHENSIVE,
            methodology="Method text",
            significance="Significance text",
        )
        assert response.get_primary_summary() == "Method text"


class TestBatchSummaryRequest:
    """Test BatchSummaryRequest model."""

    def test_create_batch_request(self):
        """Test creating batch summary request."""
        request = BatchSummaryRequest(
            query="cancer genomics",
            results=[{"id": "GSE123", "metadata": {"title": "Study 1"}}],
            max_datasets=10,
        )
        assert request.query == "cancer genomics"
        assert len(request.results) == 1
        assert request.max_datasets == 10


class TestBatchSummaryResponse:
    """Test BatchSummaryResponse model."""

    def test_create_batch_response(self):
        """Test creating batch summary response."""
        response = BatchSummaryResponse(
            query="cancer genomics",
            total_datasets=5,
            summarized_count=3,
            statistics={
                "organisms": {"Homo sapiens": 3},
                "platforms": {"Illumina": 2, "Affymetrix": 1},
            },
            overview="Analysis of 3 datasets...",
        )
        assert response.total_datasets == 5
        assert response.summarized_count == 3
        assert "organisms" in response.statistics


class TestModelInfo:
    """Test ModelInfo model."""

    def test_create_model_info(self):
        """Test creating model info."""
        info = ModelInfo(
            model_name="gpt-4",
            available=True,
            max_tokens=8000,
            temperature=0.7,
        )
        assert info.model_name == "gpt-4"
        assert info.available is True


# ============================================================================
# Utilities Tests
# ============================================================================


class TestPrepareMetadata:
    """Test prepare_metadata utility."""

    def test_prepare_complete_metadata(self, sample_metadata):
        """Test preparing complete metadata."""
        result = prepare_metadata(sample_metadata)
        assert result["title"] == sample_metadata["title"]
        assert result["summary"] == sample_metadata["summary"]
        assert result["organism"] == "Homo sapiens"
        assert result["platform"] == "Illumina HiSeq 2500"
        assert result["samples_count"] == 24

    def test_prepare_minimal_metadata(self):
        """Test preparing minimal metadata."""
        minimal = {"title": "Test Study"}
        result = prepare_metadata(minimal)
        assert result["title"] == "Test Study"
        assert result["summary"] == ""
        assert result["organism"] == "Unknown"

    def test_prepare_with_none_values(self):
        """Test handling None values."""
        data = {"title": "Test", "summary": None, "organism": None}
        result = prepare_metadata(data)
        assert result["summary"] == ""
        assert result["organism"] == "Unknown"

    def test_prepare_empty_dict(self):
        """Test handling empty dictionary."""
        result = prepare_metadata({})
        assert result["title"] == ""
        assert result["summary"] == ""


class TestEstimateTokens:
    """Test estimate_tokens utility."""

    def test_estimate_simple_text(self):
        """Test token estimation for simple text."""
        text = "The quick brown fox jumps"  # 5 words
        tokens = estimate_tokens(text)
        assert tokens > 0
        assert tokens < 20  # Should be ~6-7 tokens

    def test_estimate_empty_text(self):
        """Test token estimation for empty text."""
        assert estimate_tokens("") == 0
        assert estimate_tokens("   ") == 0

    def test_estimate_long_text(self):
        """Test token estimation for longer text."""
        text = " ".join(["word"] * 100)  # 100 words
        tokens = estimate_tokens(text)
        assert tokens > 100
        assert tokens < 200  # Should be ~130 tokens


class TestExtractTechnicalDetails:
    """Test extract_technical_details utility."""

    def test_extract_complete_details(self, sample_metadata):
        """Test extracting complete technical details."""
        details = extract_technical_details(sample_metadata)
        assert "Platform: Illumina HiSeq 2500" in details
        assert "Samples: 24" in details
        assert "Organism: Homo sapiens" in details
        assert "Date: 2024-01-15" in details

    def test_extract_minimal_details(self):
        """Test extracting minimal details."""
        minimal = {"platform": "Illumina"}
        details = extract_technical_details(minimal)
        assert "Platform: Illumina" in details
        assert "Samples:" not in details

    def test_extract_empty_metadata(self):
        """Test extracting from empty metadata."""
        details = extract_technical_details({})
        assert details == ""


class TestAggregateBatchStatistics:
    """Test aggregate_batch_statistics utility."""

    def test_aggregate_multiple_results(self):
        """Test aggregating statistics from multiple results."""
        results = [
            {"metadata": {"organism": "Homo sapiens", "platform": "Illumina"}},
            {"metadata": {"organism": "Mus musculus", "platform": "Illumina"}},
            {"metadata": {"organism": "Homo sapiens", "platform": "Affymetrix"}},
        ]
        stats = aggregate_batch_statistics(results)
        assert stats["organisms"]["Homo sapiens"] == 2
        assert stats["organisms"]["Mus musculus"] == 1
        assert stats["platforms"]["Illumina"] == 2
        assert stats["platforms"]["Affymetrix"] == 1

    def test_aggregate_empty_results(self):
        """Test aggregating empty results."""
        stats = aggregate_batch_statistics([])
        assert stats["organisms"] == {}
        assert stats["platforms"] == {}

    def test_aggregate_missing_metadata(self):
        """Test aggregating with missing metadata."""
        results = [
            {"metadata": {"organism": "Homo sapiens"}},  # No platform
            {"metadata": {"platform": "Illumina"}},  # No organism
        ]
        stats = aggregate_batch_statistics(results)
        assert "Homo sapiens" in stats["organisms"]
        assert "Illumina" in stats["platforms"]


class TestTruncateText:
    """Test truncate_text utility."""

    def test_truncate_long_text(self):
        """Test truncating long text."""
        text = "word " * 100  # 100 words
        truncated = truncate_text(text, max_length=50)
        assert len(truncated) <= 53  # 50 + "..."
        assert truncated.endswith("...")

    def test_truncate_short_text(self):
        """Test truncating short text (no truncation)."""
        text = "Short text"
        truncated = truncate_text(text, max_length=50)
        assert truncated == text
        assert not truncated.endswith("...")

    def test_truncate_custom_suffix(self):
        """Test truncating with custom suffix."""
        text = "word " * 100
        truncated = truncate_text(text, max_length=50, suffix=" [MORE]")
        assert truncated.endswith(" [MORE]")


# ============================================================================
# Prompts Tests
# ============================================================================


class TestPromptBuilder:
    """Test PromptBuilder utility."""

    def test_build_overview_prompt(self, sample_metadata):
        """Test building overview prompt."""
        prompt = PromptBuilder.build_overview_prompt(sample_metadata)
        assert "RNA-seq analysis of cancer cells" in prompt
        assert "Homo sapiens" in prompt
        assert "overview" in prompt.lower()

    def test_build_overview_with_context(self, sample_metadata):
        """Test building overview prompt with query context."""
        prompt = PromptBuilder.build_overview_prompt(sample_metadata, query_context="cancer treatment")
        assert "cancer treatment" in prompt
        assert "context" in prompt.lower()

    def test_build_methodology_prompt(self, sample_metadata):
        """Test building methodology prompt."""
        prompt = PromptBuilder.build_methodology_prompt(sample_metadata)
        assert "methods" in prompt.lower() or "methodology" in prompt.lower()
        assert "Illumina" in prompt

    def test_build_significance_prompt(self, sample_metadata):
        """Test building significance prompt."""
        prompt = PromptBuilder.build_significance_prompt(sample_metadata)
        assert "significance" in prompt.lower() or "impact" in prompt.lower()

    def test_get_system_message_overview(self):
        """Test getting system message for overview."""
        message = PromptBuilder.get_system_message("overview")
        assert "genomic" in message.lower() or "biomedical" in message.lower()
        assert len(message) > 0

    def test_get_system_message_methodology(self):
        """Test getting system message for methodology."""
        message = PromptBuilder.get_system_message("methodology")
        assert len(message) > 0

    def test_get_system_message_brief(self):
        """Test getting system message for brief."""
        message = PromptBuilder.get_system_message("brief")
        assert "concise" in message.lower() or "brief" in message.lower()


# ============================================================================
# Client Tests
# ============================================================================


class TestSummarizationClient:
    """Test SummarizationClient."""

    def test_init_with_settings(self, settings):
        """Test client initialization with settings."""
        client = SummarizationClient(settings)
        assert client.settings == settings

    def test_init_without_openai(self):
        """Test client initialization without OpenAI."""
        settings_no_key = Settings(ai=AISettings(openai_api_key=None))
        client = SummarizationClient(settings_no_key)
        # Should initialize but client will be None
        assert client.settings == settings_no_key

    def test_get_model_info_available(self, settings):
        """Test getting model info when available."""
        with patch("omics_oracle_v2.lib.ai.client.HAS_OPENAI", True):
            client = SummarizationClient(settings)
            info = client.get_model_info()
            assert info.model_name == "gpt-4"
            assert info.max_tokens == 1000
            assert info.temperature == 0.7

    def test_get_model_info_unavailable(self):
        """Test getting model info when unavailable."""
        with patch("omics_oracle_v2.lib.ai.client.HAS_OPENAI", False):
            settings_no_key = Settings(ai=AISettings(openai_api_key=None))
            client = SummarizationClient(settings_no_key)
            info = client.get_model_info()
            assert info.available is False

    @patch("omics_oracle_v2.lib.ai.client.HAS_OPENAI", True)
    def test_summarize_comprehensive(self, settings, sample_metadata):
        """Test comprehensive summarization."""
        client = SummarizationClient(settings)

        # Mock OpenAI client
        mock_openai = MagicMock()
        mock_response = Mock()
        mock_response.choices = [
            Mock(message=Mock(content="Overview text")),
            Mock(message=Mock(content="Methodology text")),
            Mock(message=Mock(content="Significance text")),
        ]
        mock_openai.chat.completions.create.return_value = mock_response
        client.client = mock_openai

        response = client.summarize(
            metadata=sample_metadata,
            summary_type=SummaryType.COMPREHENSIVE,
        )

        assert response.summary_type == SummaryType.COMPREHENSIVE
        assert response.overview is not None
        assert mock_openai.chat.completions.create.call_count >= 3

    @patch("omics_oracle_v2.lib.ai.client.HAS_OPENAI", True)
    def test_summarize_brief(self, settings, sample_metadata):
        """Test brief summarization."""
        client = SummarizationClient(settings)

        # Mock OpenAI client
        mock_openai = MagicMock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Brief summary"))]
        mock_openai.chat.completions.create.return_value = mock_response
        client.client = mock_openai

        response = client.summarize(
            metadata=sample_metadata,
            summary_type=SummaryType.BRIEF,
        )

        assert response.summary_type == SummaryType.BRIEF
        assert response.brief is not None
        assert mock_openai.chat.completions.create.call_count == 1

    @patch("omics_oracle_v2.lib.ai.client.HAS_OPENAI", False)
    def test_summarize_without_openai(self, sample_metadata):
        """Test summarization fails without OpenAI."""
        settings_no_key = Settings(ai=AISettings(openai_api_key=None))
        client = SummarizationClient(settings_no_key)

        with pytest.raises(AIError, match="OpenAI package not available"):
            client.summarize(metadata=sample_metadata)

    @patch("omics_oracle_v2.lib.ai.client.HAS_OPENAI", True)
    def test_summarize_batch(self, settings):
        """Test batch summarization."""
        client = SummarizationClient(settings)

        results = [
            {"id": "GSE123", "metadata": {"organism": "Homo sapiens", "platform": "Illumina"}},
            {"id": "GSE456", "metadata": {"organism": "Mus musculus", "platform": "Affymetrix"}},
        ]

        response = client.summarize_batch(
            query="test query",
            results=results,
            max_datasets=10,
        )

        assert response.query == "test query"
        assert response.total_datasets == 2
        assert "organisms" in response.statistics
        assert response.statistics["organisms"]["Homo sapiens"] == 1

    @patch("omics_oracle_v2.lib.ai.client.HAS_OPENAI", True)
    def test_call_llm_success(self, settings):
        """Test successful LLM call."""
        client = SummarizationClient(settings)

        # Mock OpenAI client
        mock_openai = MagicMock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Test response"))]
        mock_openai.chat.completions.create.return_value = mock_response
        client.client = mock_openai

        result = client._call_llm(
            prompt="Test prompt",
            system_message="Test system",
            max_tokens=500,
        )

        assert result == "Test response"
        mock_openai.chat.completions.create.assert_called_once()

    @patch("omics_oracle_v2.lib.ai.client.HAS_OPENAI", True)
    def test_call_llm_error(self, settings):
        """Test LLM call with error."""
        client = SummarizationClient(settings)

        # Mock OpenAI client to raise exception
        mock_openai = MagicMock()
        mock_openai.chat.completions.create.side_effect = Exception("API Error")
        client.client = mock_openai

        with pytest.raises(AIError, match="Failed to call LLM"):
            client._call_llm(prompt="Test", system_message="Test")


# ============================================================================
# Integration Tests (require OpenAI API)
# ============================================================================


@pytest.mark.integration
class TestSummarizationClientIntegration:
    """Integration tests with real OpenAI API (requires API key)."""

    def test_real_summarization(self, sample_metadata):
        """Test real summarization with OpenAI API."""
        # Only runs if OPENAI_API_KEY is set
        settings = Settings()
        if not settings.ai.openai_api_key:
            pytest.skip("OpenAI API key not configured")

        client = SummarizationClient(settings)
        response = client.summarize(
            metadata=sample_metadata,
            summary_type=SummaryType.BRIEF,
        )

        assert response.has_content()
        assert response.brief is not None
        assert len(response.brief) > 0
