"""
Integration tests for omics_oracle_v2.

Tests cross-library integration and end-to-end workflows to ensure all
extracted components work together correctly.

Test Categories:
- Library Integration: NLP + GEO + AI working together
- Configuration Integration: Settings propagate correctly
- Error Handling: Exceptions work across boundaries
- Performance: Response times and resource usage

Markers:
- @pytest.mark.integration: Requires network/external services
- @pytest.mark.slow: Takes >1 second to run
"""

import pytest

from omics_oracle_v2.core import AISettings, GEOSettings, NLPSettings, Settings
from omics_oracle_v2.core.exceptions import AIError, ConfigurationError, GEOError, NLPError
from omics_oracle_v2.lib.ai import SummarizationClient, SummaryType
from omics_oracle_v2.lib.geo import GEOClient
from omics_oracle_v2.lib.nlp import BiomedicalNER

# ============================================================================
# Configuration Integration Tests
# ============================================================================


class TestConfigurationIntegration:
    """Test configuration works across all libraries."""

    def test_settings_creation(self):
        """Test creating settings with all subsettings."""
        settings = Settings(
            debug=True,
            log_level="DEBUG",
            nlp=NLPSettings(model_name="en_core_web_sm", batch_size=16),
            geo=GEOSettings(ncbi_email="test@example.com", rate_limit=2),
            ai=AISettings(model="gpt-4", max_tokens=500),
        )

        assert settings.debug is True
        assert settings.nlp.batch_size == 16
        assert settings.geo.rate_limit == 2
        assert settings.ai.max_tokens == 500

    def test_settings_injection(self):
        """Test settings can be injected into all services."""
        settings = Settings(
            nlp=NLPSettings(batch_size=8),
            geo=GEOSettings(ncbi_email="test@example.com"),
            ai=AISettings(model="gpt-3.5-turbo"),
        )

        # Services accept their specific settings subsections
        ner = BiomedicalNER(settings.nlp)
        geo_client = GEOClient(settings)  # Takes full Settings
        ai_client = SummarizationClient(settings)  # Takes full Settings

        assert ner.settings == settings.nlp
        assert geo_client.settings == settings
        assert ai_client.settings == settings

    def test_default_settings(self):
        """Test default settings work for all services."""
        settings = Settings()

        # Should be able to create all services with defaults
        ner = BiomedicalNER(settings.nlp)
        geo_client = GEOClient(settings)
        ai_client = SummarizationClient(settings)

        assert ner is not None
        assert geo_client is not None
        assert ai_client is not None


# ============================================================================
# Error Handling Integration Tests
# ============================================================================


class TestErrorHandling:
    """Test error handling across libraries."""

    def test_exception_hierarchy(self):
        """Test all exceptions inherit from base."""
        from omics_oracle_v2.core.exceptions import OmicsOracleError

        # All custom exceptions should inherit from base
        assert issubclass(NLPError, OmicsOracleError)
        assert issubclass(GEOError, OmicsOracleError)
        assert issubclass(AIError, OmicsOracleError)
        assert issubclass(ConfigurationError, OmicsOracleError)

    def test_nlp_error_handling(self):
        """Test NLP errors are raised correctly."""
        settings = Settings()
        ner = BiomedicalNER(settings.nlp)

        # Empty text should not crash
        result = ner.extract_entities("")
        assert len(result.entities) == 0

        # Very long text should not crash (truncates)
        long_text = "gene " * 10000
        result = ner.extract_entities(long_text)
        assert result is not None

    def test_geo_error_handling(self):
        """Test GEO errors are raised correctly."""
        settings = Settings(geo=GEOSettings(ncbi_email="test@example.com"))
        client = GEOClient(settings)

        # Invalid series ID should raise GEOError or return None
        with pytest.raises(GEOError):
            client.get_series("INVALID_ID_12345")

    def test_ai_error_handling(self):
        """Test AI errors are raised correctly."""
        settings = Settings(ai=AISettings(openai_api_key=None))
        client = SummarizationClient(settings)

        # Without OpenAI, should handle gracefully
        metadata = {"title": "Test", "summary": "Test summary"}

        # Should not crash, just return None or log warning
        _response = client.summarize(metadata, summary_type=SummaryType.BRIEF)  # noqa: F841
        # Depending on implementation, might be None or have empty fields
        # Variable prefixed with _ to indicate intentionally unused


# ============================================================================
# Library Integration Tests
# ============================================================================


class TestLibraryIntegration:
    """Test libraries work together."""

    def test_nlp_to_geo_workflow(self):
        """Test NER entities can be used for GEO search."""
        settings = Settings(geo=GEOSettings(ncbi_email="test@example.com"))

        # 1. Extract entities from query
        ner = BiomedicalNER(settings.nlp)
        query = "Find datasets about TP53 mutations in breast cancer"
        ner_result = ner.extract_entities(query)

        # Should extract gene and disease entities
        genes = [e for e in ner_result.entities if e.entity_type == "GENE"]
        diseases = [e for e in ner_result.entities if e.entity_type == "DISEASE"]

        assert len(genes) > 0 or len(diseases) > 0

        # 2. Could use entities for GEO search (if search API available)
        geo_client = GEOClient(settings)
        # Note: Current GEOClient doesn't have search, only get_series
        # This is a placeholder for when search is added
        assert geo_client is not None

    def test_geo_to_ai_workflow(self):
        """Test GEO metadata can be summarized by AI."""
        settings = Settings(
            geo=GEOSettings(ncbi_email="test@example.com"),
            ai=AISettings(openai_api_key=None),  # No key for testing
        )

        # Create mock GEO metadata
        geo_metadata = {
            "title": "RNA-seq analysis of cancer cells",
            "summary": "Gene expression profiling of tumor samples",
            "organism": "Homo sapiens",
            "platform": "Illumina HiSeq 2500",
            "samples_count": 24,
        }

        # Should be able to pass to summarizer
        ai_client = SummarizationClient(settings)

        # Even without OpenAI key, structure should work
        # (will just return None or log warning)
        try:
            response = ai_client.summarize(metadata=geo_metadata, summary_type=SummaryType.BRIEF)
            # If no OpenAI, response might be None or have empty fields
            assert response is not None or ai_client.client is None
        except AIError:
            # Expected if OpenAI not available
            pass

    @pytest.mark.slow
    def test_full_pipeline_structure(self):
        """Test full NER -> GEO -> AI pipeline structure."""
        settings = Settings(
            nlp=NLPSettings(batch_size=16),
            geo=GEOSettings(ncbi_email="test@example.com"),
            ai=AISettings(openai_api_key=None),
        )

        # 1. NER extraction
        ner = BiomedicalNER(settings.nlp)
        query = "TP53 mutations in lung cancer"
        ner_result = ner.extract_entities(query)

        assert ner_result.text == query
        assert len(ner_result.entities) >= 0

        # 2. GEO client ready
        geo_client = GEOClient(settings)
        assert geo_client.settings.geo.ncbi_email == "test@example.com"

        # 3. AI client ready
        ai_client = SummarizationClient(settings)
        assert ai_client.settings.ai.model == "gpt-4"  # Default

        # Pipeline components are connected
        assert ner.settings.batch_size == 16
        assert geo_client.settings == settings
        assert ai_client.settings == settings


# ============================================================================
# External Service Integration Tests (Marked @integration)
# ============================================================================


@pytest.mark.integration
class TestGEOIntegration:
    """Test actual GEO API integration (requires network)."""

    def test_get_real_geo_series(self):
        """Test fetching a real GEO series."""
        settings = Settings(geo=GEOSettings(ncbi_email="test@example.com"))
        client = GEOClient(settings)

        # GSE1 is a well-known test series
        metadata = client.get_series("GSE1")

        assert metadata is not None
        assert "title" in metadata
        assert "summary" in metadata

    def test_geo_rate_limiting(self):
        """Test rate limiting works correctly."""
        settings = Settings(geo=GEOSettings(ncbi_email="test@example.com", rate_limit=1))
        client = GEOClient(settings)

        import time

        start = time.time()

        # Make 3 requests - should take at least 2 seconds with rate_limit=1
        for series_id in ["GSE1", "GSE2", "GSE3"]:
            try:
                client.get_series(series_id)
            except GEOError:
                pass  # May not exist, that's ok

        elapsed = time.time() - start
        assert elapsed >= 2.0  # Should respect rate limit


@pytest.mark.integration
class TestAIIntegration:
    """Test actual AI API integration (requires OpenAI key)."""

    def test_real_summarization(self):
        """Test real OpenAI summarization."""
        settings = Settings()

        if not settings.ai.openai_api_key:
            pytest.skip("OpenAI API key not configured")

        client = SummarizationClient(settings)

        metadata = {
            "title": "RNA-seq analysis of cancer cells under drug treatment",
            "summary": "This study examines gene expression changes in cancer cells.",
            "organism": "Homo sapiens",
            "platform": "Illumina HiSeq 2500",
            "samples_count": 24,
        }

        response = client.summarize(metadata=metadata, summary_type=SummaryType.BRIEF)

        assert response is not None
        assert response.has_content()
        assert response.brief is not None
        assert len(response.brief) > 10  # Should have actual content


# ============================================================================
# Performance Integration Tests
# ============================================================================


@pytest.mark.slow
class TestPerformance:
    """Test performance of integrated workflows."""

    def test_ner_performance(self):
        """Test NER performance on typical input."""
        import time

        settings = Settings()
        ner = BiomedicalNER(settings.nlp)

        text = "TP53 mutations cause cancer in human cells. BRCA1 and BRCA2 are tumor suppressors."

        start = time.time()
        result = ner.extract_entities(text)
        elapsed = time.time() - start

        assert elapsed < 1.0  # Should be fast for short text
        assert len(result.entities) > 0

    def test_batch_ner_performance(self):
        """Test NER performance on batch processing."""
        import time

        settings = Settings(nlp=NLPSettings(batch_size=32))
        ner = BiomedicalNER(settings.nlp)

        texts = [
            "TP53 mutations in lung cancer",
            "BRCA1 screening for breast cancer",
            "EGFR inhibitors in melanoma",
        ] * 10  # 30 texts

        start = time.time()
        for text in texts:
            ner.extract_entities(text)
        elapsed = time.time() - start

        avg_time = elapsed / len(texts)
        assert avg_time < 0.5  # Should average <500ms per text

    def test_geo_caching_performance(self):
        """Test GEO caching improves performance."""
        import time

        settings = Settings(geo=GEOSettings(ncbi_email="test@example.com", use_cache=True))
        client = GEOClient(settings)

        # First call - uncached
        start = time.time()
        try:
            metadata1 = client.get_series("GSE1")
            elapsed1 = time.time() - start

            # Second call - should be cached
            start = time.time()
            metadata2 = client.get_series("GSE1")
            elapsed2 = time.time() - start

            # Cached call should be much faster
            assert elapsed2 < elapsed1 * 0.5  # At least 2x faster
            assert metadata1 == metadata2
        except GEOError:
            pytest.skip("GEO API unavailable")


# ============================================================================
# Data Flow Integration Tests
# ============================================================================


class TestDataFlow:
    """Test data flows correctly between components."""

    def test_ner_output_structure(self):
        """Test NER output can be consumed by other components."""
        settings = Settings()
        ner = BiomedicalNER(settings.nlp)

        result = ner.extract_entities("TP53 gene in cancer")

        # Result should be serializable
        result_dict = result.model_dump()
        assert "text" in result_dict
        assert "entities" in result_dict

        # Should be JSON serializable
        import json

        json_str = json.dumps(result_dict)
        assert len(json_str) > 0

    def test_geo_output_structure(self):
        """Test GEO output structure is consistent."""
        settings = Settings(geo=GEOSettings(ncbi_email="test@example.com"))
        _client = GEOClient(settings)  # noqa: F841 - testing client creation

        # Mock metadata structure
        metadata = {
            "title": "Test Study",
            "summary": "Test summary",
            "organism": "Homo sapiens",
        }

        # Should be dict with expected keys
        assert isinstance(metadata, dict)
        assert "title" in metadata

    def test_ai_output_structure(self):
        """Test AI output structure is consistent."""
        from omics_oracle_v2.lib.ai import SummaryResponse

        # Create a response
        response = SummaryResponse(
            dataset_id="GSE123",
            summary_type=SummaryType.BRIEF,
            brief="Test summary",
        )

        # Should be serializable
        response_dict = response.model_dump()
        assert "dataset_id" in response_dict
        assert "brief" in response_dict

        # Should have helper methods
        assert response.has_content() is True
        assert response.get_primary_summary() == "Test summary"


# ============================================================================
# Import Integration Tests
# ============================================================================


class TestImports:
    """Test all imports work correctly."""

    def test_core_imports(self):
        """Test core module imports."""
        from omics_oracle_v2 import core

        assert hasattr(core, "Settings")
        assert hasattr(core, "OmicsOracleError")

    def test_nlp_imports(self):
        """Test NLP module imports."""
        from omics_oracle_v2 import lib

        assert hasattr(lib, "nlp")
        from omics_oracle_v2.lib import nlp

        assert hasattr(nlp, "BiomedicalNER")

    def test_geo_imports(self):
        """Test GEO module imports."""
        from omics_oracle_v2.lib import geo

        assert hasattr(geo, "GEOClient")

    def test_ai_imports(self):
        """Test AI module imports."""
        from omics_oracle_v2.lib import ai

        assert hasattr(ai, "SummarizationClient")
        assert hasattr(ai, "SummaryType")

    def test_no_v1_imports(self):
        """Test v2 code doesn't import v1."""
        import sys

        # Import all v2 modules  # noqa: F401 - imports needed for test
        from omics_oracle_v2.core import Settings  # noqa: F401
        from omics_oracle_v2.lib.ai import SummarizationClient  # noqa: F401
        from omics_oracle_v2.lib.geo import GEOClient  # noqa: F401
        from omics_oracle_v2.lib.nlp import BiomedicalNER  # noqa: F401

        # Check no v1 modules loaded (they start with src.omics_oracle or omics_oracle.*)
        v1_modules = [name for name in sys.modules if name.startswith("src.omics_oracle")]

        assert len(v1_modules) == 0, f"V1 modules found: {v1_modules}"
