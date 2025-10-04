"""Tests for core configuration module."""

import os
from pathlib import Path

import pytest

from omics_oracle_v2.core.config import AISettings, GEOSettings, NLPSettings, Settings, get_settings


class TestNLPSettings:
    """Test NLP configuration."""

    def test_default_values(self):
        """Test default NLP settings."""
        settings = NLPSettings()

        assert settings.model_name == "en_core_web_sm"
        assert settings.batch_size == 32
        assert settings.max_entities == 100

    def test_custom_values(self):
        """Test custom NLP settings."""
        settings = NLPSettings(model_name="custom_model", batch_size=64, max_entities=200)

        assert settings.model_name == "custom_model"
        assert settings.batch_size == 64
        assert settings.max_entities == 200

    def test_environment_variables(self, monkeypatch):
        """Test loading from environment variables."""
        monkeypatch.setenv("OMICS_NLP_MODEL_NAME", "env_model")
        monkeypatch.setenv("OMICS_NLP_BATCH_SIZE", "128")

        settings = NLPSettings()

        assert settings.model_name == "env_model"
        assert settings.batch_size == 128

    def test_validation(self):
        """Test settings validation."""
        # Batch size must be >= 1
        with pytest.raises(ValueError):
            NLPSettings(batch_size=0)

        # Max entities must be >= 1
        with pytest.raises(ValueError):
            NLPSettings(max_entities=0)


class TestGEOSettings:
    """Test GEO configuration."""

    def test_default_values(self):
        """Test default GEO settings."""
        settings = GEOSettings()

        assert settings.api_key is None
        assert settings.cache_dir == Path(".cache/geo")
        assert settings.cache_ttl == 3600
        assert settings.max_retries == 3
        assert settings.timeout == 30

    def test_custom_values(self):
        """Test custom GEO settings."""
        settings = GEOSettings(
            api_key="test_key",
            cache_dir=Path("/tmp/cache"),
            cache_ttl=7200,
            max_retries=5,
        )

        assert settings.api_key == "test_key"
        assert settings.cache_dir == Path("/tmp/cache")
        assert settings.cache_ttl == 7200
        assert settings.max_retries == 5

    def test_environment_variables(self, monkeypatch):
        """Test loading from environment variables."""
        monkeypatch.setenv("OMICS_GEO_API_KEY", "env_key")
        monkeypatch.setenv("OMICS_GEO_CACHE_TTL", "1800")

        settings = GEOSettings()

        assert settings.api_key == "env_key"
        assert settings.cache_ttl == 1800


class TestAISettings:
    """Test AI configuration."""

    def test_default_values(self):
        """Test default AI settings."""
        settings = AISettings()

        assert settings.openai_api_key is None
        assert settings.model == "gpt-4"
        assert settings.max_tokens == 1000
        assert settings.temperature == 0.7
        assert settings.timeout == 60

    def test_custom_values(self):
        """Test custom AI settings."""
        settings = AISettings(
            openai_api_key="test_key",
            model="gpt-3.5-turbo",
            max_tokens=2000,
            temperature=0.9,
        )

        assert settings.openai_api_key == "test_key"
        assert settings.model == "gpt-3.5-turbo"
        assert settings.max_tokens == 2000
        assert settings.temperature == 0.9

    def test_validation(self):
        """Test settings validation."""
        # Temperature must be 0.0-2.0
        with pytest.raises(ValueError):
            AISettings(temperature=-0.1)

        with pytest.raises(ValueError):
            AISettings(temperature=2.1)


class TestSettings:
    """Test main Settings class."""

    def test_default_values(self, monkeypatch):
        """Test default main settings."""
        # Clear any environment variables that might interfere
        monkeypatch.delenv("OMICS_DEBUG", raising=False)
        monkeypatch.delenv("OMICS_LOG_LEVEL", raising=False)

        settings = Settings(_env_file=None)  # Don't load .env file for testing

        assert settings.debug is False
        assert settings.log_level == "INFO"
        assert isinstance(settings.nlp, NLPSettings)
        assert isinstance(settings.geo, GEOSettings)
        assert isinstance(settings.ai, AISettings)

    def test_custom_values(self):
        """Test custom main settings."""
        settings = Settings(
            debug=True,
            log_level="DEBUG",
            nlp=NLPSettings(model_name="custom"),
        )

        assert settings.debug is True
        assert settings.log_level == "DEBUG"
        assert settings.nlp.model_name == "custom"

    def test_nested_settings(self):
        """Test accessing nested settings."""
        settings = Settings(_env_file=None)  # Don't load .env file for testing

        # Can access nested settings
        assert settings.nlp.model_name == "en_core_web_sm"
        assert settings.geo.cache_ttl == 3600
        assert settings.ai.model == "gpt-4"

    def test_environment_variables(self, monkeypatch):
        """Test loading from environment variables."""
        # Clear all OMICS_ vars first
        for key in list(os.environ.keys()):
            if key.startswith("OMICS_"):
                monkeypatch.delenv(key, raising=False)

        # Set specific test values
        monkeypatch.setenv("OMICS_DEBUG", "true")
        monkeypatch.setenv("OMICS_LOG_LEVEL", "DEBUG")
        monkeypatch.setenv("OMICS_NLP_MODEL_NAME", "env_model")

        settings = Settings(_env_file=None)  # Don't load .env file for testing

        assert settings.debug is True
        assert settings.log_level == "DEBUG"
        assert settings.nlp.model_name == "env_model"


class TestGetSettings:
    """Test get_settings function."""

    def test_returns_settings_instance(self):
        """Test that get_settings returns a Settings instance."""
        settings = get_settings()

        assert isinstance(settings, Settings)

    def test_uses_environment(self, monkeypatch):
        """Test that get_settings loads from environment."""
        monkeypatch.setenv("OMICS_DEBUG", "true")

        settings = get_settings()

        assert settings.debug is True
