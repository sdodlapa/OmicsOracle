"""Tests for user preferences management."""

import tempfile
from pathlib import Path

import pytest

from omics_oracle_v2.lib.dashboard.preferences import (
    DARK_THEME,
    FOREST_THEME,
    LIGHT_THEME,
    OCEAN_THEME,
    PreferencesManager,
    Theme,
    UserPreferences,
)


@pytest.fixture
def temp_storage():
    """Temporary storage directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def manager(temp_storage):
    """Preferences manager with temp storage."""
    return PreferencesManager(storage_dir=temp_storage)


@pytest.fixture
def sample_theme():
    """Sample theme."""
    return Theme(
        name="Custom",
        primary_color="#ff0000",
        background_color="#000000",
        text_color="#ffffff",
    )


def test_theme_creation():
    """Test creating a theme."""
    theme = Theme(name="Test", primary_color="#123456")
    assert theme.name == "Test"
    assert theme.primary_color == "#123456"
    assert theme.background_color == "#ffffff"  # default


def test_theme_serialization():
    """Test theme to/from dict."""
    theme = Theme(name="Test", primary_color="#123456")
    data = theme.to_dict()

    assert isinstance(data, dict)
    assert data["name"] == "Test"

    restored = Theme.from_dict(data)
    assert restored.name == theme.name
    assert restored.primary_color == theme.primary_color


def test_predefined_themes():
    """Test predefined themes exist."""
    assert LIGHT_THEME.name == "Light"
    assert DARK_THEME.name == "Dark"
    assert OCEAN_THEME.name == "Ocean"
    assert FOREST_THEME.name == "Forest"


def test_user_preferences_defaults():
    """Test default user preferences."""
    prefs = UserPreferences()

    assert prefs.theme == LIGHT_THEME
    assert prefs.layout == "wide"
    assert prefs.sidebar_state == "expanded"
    assert prefs.default_databases == ["pubmed"]
    assert prefs.default_max_results == 100
    assert prefs.enable_visualizations is True
    assert prefs.favorites == []


def test_user_preferences_custom():
    """Test custom user preferences."""
    prefs = UserPreferences(
        layout="centered",
        default_databases=["pubmed", "pmc"],
        default_max_results=200,
        favorites=["BRCA1", "TP53"],
    )

    assert prefs.layout == "centered"
    assert prefs.default_databases == ["pubmed", "pmc"]
    assert prefs.default_max_results == 200
    assert prefs.favorites == ["BRCA1", "TP53"]


def test_user_preferences_serialization():
    """Test user preferences to/from dict."""
    prefs = UserPreferences(layout="centered", favorites=["BRCA1"])
    data = prefs.to_dict()

    assert isinstance(data, dict)
    assert data["layout"] == "centered"
    assert "theme" in data

    restored = UserPreferences.from_dict(data)
    assert restored.layout == prefs.layout
    assert restored.favorites == prefs.favorites


def test_user_preferences_update():
    """Test updating preferences."""
    prefs = UserPreferences()
    prefs.update(layout="centered", default_max_results=200)

    assert prefs.layout == "centered"
    assert prefs.default_max_results == 200


def test_manager_initialization(temp_storage):
    """Test manager initialization."""
    manager = PreferencesManager(storage_dir=temp_storage)

    assert manager.storage_dir == temp_storage
    assert manager.preferences_file == temp_storage / "preferences.json"
    assert manager.storage_dir.exists()


def test_manager_default_preferences(manager):
    """Test manager starts with defaults."""
    prefs = manager.preferences

    assert prefs.theme == LIGHT_THEME
    assert prefs.layout == "wide"
    assert prefs.default_databases == ["pubmed"]


def test_update_theme(manager, sample_theme):
    """Test updating theme."""
    manager.update_theme(sample_theme)

    assert manager.preferences.theme.name == "Custom"
    assert manager.preferences.theme.primary_color == "#ff0000"


def test_update_layout(manager):
    """Test updating layout."""
    manager.update_layout("centered", "collapsed")

    assert manager.preferences.layout == "centered"
    assert manager.preferences.sidebar_state == "collapsed"


def test_update_layout_no_sidebar(manager):
    """Test updating layout without sidebar state."""
    manager.update_layout("centered")

    assert manager.preferences.layout == "centered"
    assert manager.preferences.sidebar_state == "expanded"  # unchanged


def test_update_search_defaults(manager):
    """Test updating search defaults."""
    manager.update_search_defaults(
        databases=["pubmed", "pmc"], max_results=200, year_start=2010, year_end=2023, use_llm=True
    )

    prefs = manager.preferences
    assert prefs.default_databases == ["pubmed", "pmc"]
    assert prefs.default_max_results == 200
    assert prefs.default_year_start == 2010
    assert prefs.default_year_end == 2023
    assert prefs.default_use_llm is True


def test_update_search_defaults_partial(manager):
    """Test updating search defaults partially."""
    manager.update_search_defaults(max_results=150)

    prefs = manager.preferences
    assert prefs.default_max_results == 150
    assert prefs.default_databases == ["pubmed"]  # unchanged


def test_update_features(manager):
    """Test updating feature preferences."""
    manager.update_features(visualizations=False, analytics=False, export=True, llm=True)

    prefs = manager.preferences
    assert prefs.enable_visualizations is False
    assert prefs.enable_analytics is False
    assert prefs.enable_export is True
    assert prefs.enable_llm is True


def test_update_features_partial(manager):
    """Test updating features partially."""
    manager.update_features(visualizations=False)

    prefs = manager.preferences
    assert prefs.enable_visualizations is False
    assert prefs.enable_analytics is True  # unchanged


def test_add_favorite(manager):
    """Test adding favorites."""
    manager.add_favorite("BRCA1")
    manager.add_favorite("TP53")

    favorites = manager.get_favorites()
    assert len(favorites) == 2
    assert "BRCA1" in favorites
    assert "TP53" in favorites


def test_add_favorite_duplicate(manager):
    """Test adding duplicate favorite."""
    manager.add_favorite("BRCA1")
    manager.add_favorite("BRCA1")

    favorites = manager.get_favorites()
    assert len(favorites) == 1


def test_remove_favorite(manager):
    """Test removing favorites."""
    manager.add_favorite("BRCA1")
    manager.add_favorite("TP53")

    manager.remove_favorite("BRCA1")

    favorites = manager.get_favorites()
    assert len(favorites) == 1
    assert "TP53" in favorites


def test_remove_nonexistent_favorite(manager):
    """Test removing nonexistent favorite."""
    manager.remove_favorite("BRCA1")  # Should not error

    favorites = manager.get_favorites()
    assert len(favorites) == 0


def test_get_favorites_copy(manager):
    """Test that get_favorites returns a copy."""
    manager.add_favorite("BRCA1")

    favorites = manager.get_favorites()
    favorites.append("TP53")

    # Original should be unchanged
    assert len(manager.get_favorites()) == 1


def test_reset_to_defaults(manager):
    """Test resetting to defaults."""
    manager.update_layout("centered")
    manager.add_favorite("BRCA1")
    manager.update_search_defaults(max_results=200)

    manager.reset_to_defaults()

    prefs = manager.preferences
    assert prefs.layout == "wide"
    assert prefs.favorites == []
    assert prefs.default_max_results == 100


def test_get_available_themes(manager):
    """Test getting available themes."""
    themes = manager.get_available_themes()

    assert len(themes) == 4
    assert any(t.name == "Light" for t in themes)
    assert any(t.name == "Dark" for t in themes)
    assert any(t.name == "Ocean" for t in themes)
    assert any(t.name == "Forest" for t in themes)


def test_persistence(temp_storage, sample_theme):
    """Test that preferences persist across manager instances."""
    # Create manager and set preferences
    manager1 = PreferencesManager(storage_dir=temp_storage)
    manager1.update_theme(sample_theme)
    manager1.update_layout("centered")
    manager1.add_favorite("BRCA1")

    # Create new manager instance
    manager2 = PreferencesManager(storage_dir=temp_storage)

    # Verify preferences were loaded
    prefs = manager2.preferences
    assert prefs.theme.name == "Custom"
    assert prefs.layout == "centered"
    assert "BRCA1" in prefs.favorites


def test_error_handling_corrupted_file(temp_storage):
    """Test error handling with corrupted preferences file."""
    manager = PreferencesManager(storage_dir=temp_storage)

    # Write corrupted JSON
    with open(manager.preferences_file, "w") as f:
        f.write("not valid json{{{")

    # Create new manager - should handle error gracefully
    manager2 = PreferencesManager(storage_dir=temp_storage)

    # Should have default preferences
    assert manager2.preferences.layout == "wide"
    assert manager2.preferences.favorites == []


def test_theme_colors_valid_format():
    """Test that theme colors follow valid format."""
    theme = LIGHT_THEME

    # Basic validation of hex color format
    assert theme.primary_color.startswith("#")
    assert len(theme.primary_color) == 7  # #RRGGBB


def test_preferences_all_fields():
    """Test that preferences include all expected fields."""
    prefs = UserPreferences()
    data = prefs.to_dict()

    # Verify key fields exist
    assert "theme" in data
    assert "layout" in data
    assert "sidebar_state" in data
    assert "default_databases" in data
    assert "default_max_results" in data
    assert "enable_visualizations" in data
    assert "favorites" in data


def test_multiple_database_defaults(manager):
    """Test setting multiple default databases."""
    databases = ["pubmed", "pmc", "google_scholar"]
    manager.update_search_defaults(databases=databases)

    assert manager.preferences.default_databases == databases


def test_year_range_validation(manager):
    """Test year range settings."""
    manager.update_search_defaults(year_start=2015, year_end=2024)

    prefs = manager.preferences
    assert prefs.default_year_start == 2015
    assert prefs.default_year_end == 2024
    assert prefs.default_year_start < prefs.default_year_end


def test_export_format_preference(manager):
    """Test export format preference."""
    prefs = manager.preferences
    assert prefs.default_export_format in ["json", "csv"]


def test_display_preferences(manager):
    """Test display preferences."""
    prefs = manager.preferences

    assert isinstance(prefs.results_per_page, int)
    assert prefs.results_per_page > 0

    assert isinstance(prefs.show_abstracts, bool)
    assert isinstance(prefs.compact_view, bool)
