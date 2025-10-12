"""
User preferences management for dashboard.

Provides persistent user settings including themes, layout preferences,
and default search configurations.
"""

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class Theme:
    """Dashboard theme configuration."""

    name: str
    primary_color: str = "#1f77b4"
    background_color: str = "#ffffff"
    secondary_background_color: str = "#f0f2f6"
    text_color: str = "#31333F"
    font: str = "sans serif"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Theme":
        """Create from dictionary."""
        return cls(**data)


# Predefined themes
LIGHT_THEME = Theme(
    name="Light",
    primary_color="#1f77b4",
    background_color="#ffffff",
    secondary_background_color="#f0f2f6",
    text_color="#31333F",
)

DARK_THEME = Theme(
    name="Dark",
    primary_color="#00d4ff",
    background_color="#0e1117",
    secondary_background_color="#262730",
    text_color="#fafafa",
)

OCEAN_THEME = Theme(
    name="Ocean",
    primary_color="#006994",
    background_color="#f0f8ff",
    secondary_background_color="#e6f3ff",
    text_color="#1a1a1a",
)

FOREST_THEME = Theme(
    name="Forest",
    primary_color="#2d5016",
    background_color="#f5f9f0",
    secondary_background_color="#e8f4e0",
    text_color="#1a1a1a",
)


@dataclass
class UserPreferences:
    """User preferences for dashboard."""

    # Theme settings
    theme: Theme = field(default_factory=lambda: LIGHT_THEME)

    # Layout settings
    layout: str = "wide"  # "wide" or "centered"
    sidebar_state: str = "expanded"  # "expanded" or "collapsed"

    # Default search settings
    default_databases: List[str] = field(default_factory=lambda: ["pubmed"])
    default_max_results: int = 100
    default_year_start: int = 2000
    default_year_end: int = 2024
    default_use_llm: bool = False

    # Feature preferences
    enable_visualizations: bool = True
    enable_analytics: bool = True
    enable_export: bool = True
    enable_llm: bool = False

    # Favorite biomarkers for quick search
    favorites: List[str] = field(default_factory=list)

    # Export preferences
    default_export_format: str = "json"  # "json" or "csv"

    # Display preferences
    results_per_page: int = 10
    show_abstracts: bool = True
    compact_view: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["theme"] = self.theme.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserPreferences":
        """Create from dictionary."""
        if "theme" in data and isinstance(data["theme"], dict):
            data["theme"] = Theme.from_dict(data["theme"])
        return cls(**data)

    def update(self, **kwargs) -> None:
        """Update preferences.

        Args:
            **kwargs: Preferences to update
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)


class PreferencesManager:
    """Manages user preferences."""

    def __init__(self, storage_dir: Optional[Path] = None):
        """Initialize preferences manager.

        Args:
            storage_dir: Directory for storing preferences
        """
        if storage_dir is None:
            storage_dir = Path.home() / ".omicsoracle" / "dashboard"

        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.preferences_file = self.storage_dir / "preferences.json"
        self._preferences: UserPreferences = UserPreferences()

        self._load()

    def _load(self) -> None:
        """Load preferences from disk."""
        if self.preferences_file.exists():
            try:
                with open(self.preferences_file, "r") as f:
                    data = json.load(f)
                    self._preferences = UserPreferences.from_dict(data)
            except Exception as e:
                print(f"Error loading preferences: {e}")
                self._preferences = UserPreferences()

    def _save(self) -> None:
        """Save preferences to disk."""
        try:
            with open(self.preferences_file, "w") as f:
                json.dump(self._preferences.to_dict(), f, indent=2)
        except Exception as e:
            print(f"Error saving preferences: {e}")

    @property
    def preferences(self) -> UserPreferences:
        """Get current preferences."""
        return self._preferences

    def update_theme(self, theme: Theme) -> None:
        """Update theme.

        Args:
            theme: New theme
        """
        self._preferences.theme = theme
        self._save()

    def update_layout(self, layout: str, sidebar_state: str = None) -> None:
        """Update layout preferences.

        Args:
            layout: Layout style ("wide" or "centered")
            sidebar_state: Sidebar state ("expanded" or "collapsed")
        """
        self._preferences.layout = layout
        if sidebar_state:
            self._preferences.sidebar_state = sidebar_state
        self._save()

    def update_search_defaults(
        self,
        databases: List[str] = None,
        max_results: int = None,
        year_start: int = None,
        year_end: int = None,
        use_llm: bool = None,
    ) -> None:
        """Update default search settings.

        Args:
            databases: Default databases
            max_results: Default max results
            year_start: Default year start
            year_end: Default year end
            use_llm: Default LLM usage
        """
        if databases is not None:
            self._preferences.default_databases = databases
        if max_results is not None:
            self._preferences.default_max_results = max_results
        if year_start is not None:
            self._preferences.default_year_start = year_start
        if year_end is not None:
            self._preferences.default_year_end = year_end
        if use_llm is not None:
            self._preferences.default_use_llm = use_llm
        self._save()

    def update_features(
        self, visualizations: bool = None, analytics: bool = None, export: bool = None, llm: bool = None
    ) -> None:
        """Update feature preferences.

        Args:
            visualizations: Enable visualizations
            analytics: Enable analytics
            export: Enable export
            llm: Enable LLM
        """
        if visualizations is not None:
            self._preferences.enable_visualizations = visualizations
        if analytics is not None:
            self._preferences.enable_analytics = analytics
        if export is not None:
            self._preferences.enable_export = export
        if llm is not None:
            self._preferences.enable_llm = llm
        self._save()

    def add_favorite(self, biomarker: str) -> None:
        """Add biomarker to favorites.

        Args:
            biomarker: Biomarker name
        """
        if biomarker not in self._preferences.favorites:
            self._preferences.favorites.append(biomarker)
            self._save()

    def remove_favorite(self, biomarker: str) -> None:
        """Remove biomarker from favorites.

        Args:
            biomarker: Biomarker name
        """
        if biomarker in self._preferences.favorites:
            self._preferences.favorites.remove(biomarker)
            self._save()

    def get_favorites(self) -> List[str]:
        """Get favorite biomarkers.

        Returns:
            List of favorite biomarkers
        """
        return self._preferences.favorites.copy()

    def reset_to_defaults(self) -> None:
        """Reset preferences to defaults."""
        self._preferences = UserPreferences()
        self._save()

    def get_available_themes(self) -> List[Theme]:
        """Get available themes.

        Returns:
            List of available themes
        """
        return [LIGHT_THEME, DARK_THEME, OCEAN_THEME, FOREST_THEME]
