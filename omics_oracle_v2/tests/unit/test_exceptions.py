"""Tests for core exceptions module."""

import pytest

from omics_oracle_v2.core.exceptions import AIError, ConfigurationError, GEOError, NLPError, OmicsOracleError


class TestExceptionHierarchy:
    """Test exception inheritance and hierarchy."""

    def test_base_exception(self):
        """Test base OmicsOracleError."""
        exc = OmicsOracleError("Test error")

        assert isinstance(exc, Exception)
        assert str(exc) == "Test error"

    def test_configuration_error(self):
        """Test ConfigurationError inherits from base."""
        exc = ConfigurationError("Config error")

        assert isinstance(exc, OmicsOracleError)
        assert isinstance(exc, Exception)
        assert str(exc) == "Config error"

    def test_nlp_error(self):
        """Test NLPError inherits from base."""
        exc = NLPError("NLP error")

        assert isinstance(exc, OmicsOracleError)
        assert isinstance(exc, Exception)

    def test_geo_error(self):
        """Test GEOError inherits from base."""
        exc = GEOError("GEO error")

        assert isinstance(exc, OmicsOracleError)
        assert isinstance(exc, Exception)

    def test_ai_error(self):
        """Test AIError inherits from base."""
        exc = AIError("AI error")

        assert isinstance(exc, OmicsOracleError)
        assert isinstance(exc, Exception)


class TestExceptionCatching:
    """Test exception catching patterns."""

    def test_catch_specific_exception(self):
        """Test catching specific exception types."""
        with pytest.raises(NLPError):
            raise NLPError("Test")

        with pytest.raises(GEOError):
            raise GEOError("Test")

    def test_catch_base_exception(self):
        """Test catching base exception catches all derived."""
        # NLPError should be caught by OmicsOracleError
        with pytest.raises(OmicsOracleError):
            raise NLPError("Test")

        # GEOError should be caught by OmicsOracleError
        with pytest.raises(OmicsOracleError):
            raise GEOError("Test")

    def test_exception_with_context(self):
        """Test exceptions with chained context."""
        try:
            try:
                raise ValueError("Original error")
            except ValueError as e:
                raise GEOError("GEO processing failed") from e
        except GEOError as e:
            assert isinstance(e.__cause__, ValueError)
            assert str(e.__cause__) == "Original error"
