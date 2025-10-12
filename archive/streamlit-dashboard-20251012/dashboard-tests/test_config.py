"""
Tests for dashboard configuration.
"""

from omics_oracle_v2.lib.dashboard.config import (
    DEFAULT_CONFIG,
    MINIMAL_CONFIG,
    RESEARCH_CONFIG,
    DashboardConfig,
)


class TestDashboardConfig:
    """Test dashboard configuration."""

    def test_default_initialization(self):
        """Test default config initialization."""
        config = DashboardConfig()

        assert config.app_title == "OmicsOracle Dashboard"
        assert config.app_icon == ":dna:"
        assert config.layout == "wide"
        assert config.enable_search is True
        assert config.enable_visualizations is True

    def test_custom_initialization(self):
        """Test custom config initialization."""
        config = DashboardConfig(app_title="Custom Dashboard", max_results=200, enable_llm_analysis=False)

        assert config.app_title == "Custom Dashboard"
        assert config.max_results == 200
        assert config.enable_llm_analysis is False

    def test_default_databases(self):
        """Test default databases initialization."""
        config = DashboardConfig()

        assert config.default_databases == ["pubmed", "google_scholar"]

    def test_custom_databases(self):
        """Test custom databases."""
        config = DashboardConfig(default_databases=["pubmed", "semantic_scholar", "arxiv"])

        assert len(config.default_databases) == 3
        assert "semantic_scholar" in config.default_databases

    def test_to_streamlit_config(self):
        """Test conversion to Streamlit config."""
        config = DashboardConfig()
        st_config = config.to_streamlit_config()

        assert "theme" in st_config
        assert "primaryColor" in st_config["theme"]
        assert st_config["theme"]["primaryColor"] == config.primary_color

    def test_from_dict(self):
        """Test creating config from dictionary."""
        config_dict = {
            "app_title": "Test Dashboard",
            "max_results": 150,
            "enable_cache": False,
        }

        config = DashboardConfig.from_dict(config_dict)

        assert config.app_title == "Test Dashboard"
        assert config.max_results == 150
        assert config.enable_cache is False

    def test_update(self):
        """Test updating config values."""
        config = DashboardConfig()
        config.update(app_title="Updated Title", max_results=300)

        assert config.app_title == "Updated Title"
        assert config.max_results == 300

    def test_update_invalid_key(self):
        """Test updating with invalid key is ignored."""
        config = DashboardConfig()
        config.update(invalid_key="value")

        assert not hasattr(config, "invalid_key")


class TestConfigPresets:
    """Test configuration presets."""

    def test_default_config(self):
        """Test default configuration preset."""
        assert DEFAULT_CONFIG.enable_advanced_search is True
        assert DEFAULT_CONFIG.enable_llm_analysis is True
        assert DEFAULT_CONFIG.max_results == 100

    def test_minimal_config(self):
        """Test minimal configuration preset."""
        assert MINIMAL_CONFIG.enable_advanced_search is False
        assert MINIMAL_CONFIG.enable_llm_analysis is False
        assert MINIMAL_CONFIG.max_results == 50

    def test_research_config(self):
        """Test research configuration preset."""
        assert RESEARCH_CONFIG.enable_advanced_search is True
        assert RESEARCH_CONFIG.enable_llm_analysis is True
        assert RESEARCH_CONFIG.max_results == 200
        assert len(RESEARCH_CONFIG.default_databases) == 3


class TestConfigValidation:
    """Test configuration validation."""

    def test_positive_max_results(self):
        """Test max_results must be positive."""
        config = DashboardConfig(max_results=100)
        assert config.max_results > 0

    def test_positive_cache_ttl(self):
        """Test cache_ttl must be positive."""
        config = DashboardConfig(cache_ttl=7200)
        assert config.cache_ttl > 0

    def test_valid_layout(self):
        """Test layout is valid."""
        config = DashboardConfig(layout="wide")
        assert config.layout in ["wide", "centered"]

    def test_color_scheme(self):
        """Test color scheme validation."""
        config = DashboardConfig()
        assert config.primary_color.startswith("#")
        assert len(config.primary_color) == 7  # #RRGGBB


class TestConfigSerialization:
    """Test configuration serialization."""

    def test_dict_roundtrip(self):
        """Test config to dict and back."""
        config1 = DashboardConfig(app_title="Test", max_results=250)

        # Convert to dict
        config_dict = {
            "app_title": config1.app_title,
            "max_results": config1.max_results,
        }

        # Create from dict
        config2 = DashboardConfig.from_dict(config_dict)

        assert config2.app_title == config1.app_title
        assert config2.max_results == config1.max_results
