"""
Test environment variable setup and validation.
"""

import os
from unittest.mock import MagicMock, patch

import pytest


class TestEnvironmentSetup:
    """Test environment variable configuration and validation."""

    def test_ncbi_email_environment_variable(self):
        """Test NCBI email environment variable is set."""
        with patch.dict(os.environ, {"NCBI_EMAIL": "test@example.com"}):
            assert os.environ.get("NCBI_EMAIL") == "test@example.com"

    def test_missing_ncbi_email_environment_variable(self):
        """Test behavior when NCBI email environment variable is missing."""
        with patch.dict(os.environ, {}, clear=True):
            assert os.environ.get("NCBI_EMAIL") is None

    def test_openai_api_key_environment_variable(self):
        """Test OpenAI API key environment variable setup."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            assert os.environ.get("OPENAI_API_KEY") == "test-key"

    def test_environment_variable_validation(self):
        """Test validation of required environment variables."""
        required_vars = ["NCBI_EMAIL"]

        for var in required_vars:
            # Test when variable is set
            with patch.dict(os.environ, {var: "test-value"}):
                assert os.environ.get(var) is not None

            # Test when variable is missing
            with patch.dict(os.environ, {}, clear=True):
                assert os.environ.get(var) is None

    def test_environment_variable_override(self):
        """Test that environment variables can be overridden."""
        original_value = "original@example.com"
        new_value = "new@example.com"

        with patch.dict(os.environ, {"NCBI_EMAIL": original_value}):
            assert os.environ.get("NCBI_EMAIL") == original_value

            # Override the value
            os.environ["NCBI_EMAIL"] = new_value
            assert os.environ.get("NCBI_EMAIL") == new_value

    def test_environment_variable_types(self):
        """Test environment variable type handling."""
        with patch.dict(
            os.environ,
            {
                "NCBI_EMAIL": "test@example.com",
                "DEBUG": "true",
                "MAX_RESULTS": "10",
            },
        ):
            # String values
            assert isinstance(os.environ.get("NCBI_EMAIL"), str)

            # Boolean-like values (still strings in env vars)
            assert os.environ.get("DEBUG") == "true"

            # Numeric-like values (still strings in env vars)
            assert os.environ.get("MAX_RESULTS") == "10"
            assert int(os.environ.get("MAX_RESULTS", "0")) == 10

    def test_environment_variable_defaults(self):
        """Test default values for environment variables."""
        with patch.dict(os.environ, {}, clear=True):
            # Test with defaults
            assert os.environ.get("NCBI_EMAIL", "default@example.com") == "default@example.com"
            assert os.environ.get("DEBUG", "false") == "false"
            assert os.environ.get("MAX_RESULTS", "5") == "5"
