"""
Dashboard configuration and settings.
"""

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class DashboardConfig:
    """Configuration for dashboard application."""

    # Application settings
    app_title: str = "OmicsOracle Dashboard"
    app_icon: str = ":dna:"
    layout: str = "wide"
    sidebar_state: str = "expanded"

    # Theme settings
    primary_color: str = "#1f77b4"
    background_color: str = "#ffffff"
    secondary_background_color: str = "#f0f2f6"
    text_color: str = "#262730"
    font: str = "sans-serif"

    # Feature flags
    enable_search: bool = True
    enable_visualizations: bool = True
    enable_analytics: bool = True
    enable_export: bool = True
    enable_advanced_search: bool = True

    # Search settings
    default_databases: List[str] = None
    max_results: int = 100
    enable_llm_analysis: bool = True

    # Visualization settings
    default_chart_type: str = "auto"
    enable_interactive_plots: bool = True
    default_color_scheme: str = "default"

    # Cache settings
    enable_cache: bool = True
    cache_ttl: int = 3600  # 1 hour

    # API settings
    api_timeout: int = 30
    max_concurrent_requests: int = 5

    def __post_init__(self):
        """Initialize default values."""
        if self.default_databases is None:
            self.default_databases = ["pubmed", "google_scholar"]

    def to_streamlit_config(self) -> Dict:
        """Convert to Streamlit config format."""
        return {
            "theme": {
                "primaryColor": self.primary_color,
                "backgroundColor": self.background_color,
                "secondaryBackgroundColor": self.secondary_background_color,
                "textColor": self.text_color,
                "font": self.font,
            }
        }

    @classmethod
    def from_dict(cls, config_dict: Dict) -> "DashboardConfig":
        """Create config from dictionary."""
        return cls(**config_dict)

    def update(self, **kwargs) -> None:
        """Update configuration values."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)


# Default configurations
DEFAULT_CONFIG = DashboardConfig()

MINIMAL_CONFIG = DashboardConfig(
    enable_advanced_search=False,
    enable_llm_analysis=False,
    max_results=50,
)

RESEARCH_CONFIG = DashboardConfig(
    enable_advanced_search=True,
    enable_llm_analysis=True,
    max_results=200,
    default_databases=["pubmed", "google_scholar", "semantic_scholar"],
)
