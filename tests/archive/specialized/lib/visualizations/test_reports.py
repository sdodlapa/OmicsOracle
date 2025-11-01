"""
Tests for report visualization.
"""

import pytest

from omics_oracle_v2.lib.visualizations import ExportOptions, VisualizationConfig
from omics_oracle_v2.lib.visualizations.reports import (
    ReportVisualizer,
    create_biomarker_report,
    create_executive_dashboard,
)


@pytest.fixture
def sample_grid_report_data():
    """Sample data for grid layout report."""
    return {
        "panels": [
            {
                "data": {
                    "categories": ["CA-125", "HE4", "PSA", "CEA"],
                    "values": [150, 125, 100, 75],
                },
                "type": "bar",
                "title": "Top Biomarkers",
                "xlabel": "Biomarker",
                "ylabel": "Citations",
            },
            {
                "data": {
                    "categories": ["Diagnostic", "Prognostic", "Therapeutic"],
                    "values": [200, 150, 50],
                },
                "type": "pie",
                "title": "Usage Distribution",
            },
            {
                "data": {
                    "x": [2020, 2021, 2022, 2023, 2024],
                    "y": [100, 150, 200, 250, 300],
                },
                "type": "line",
                "title": "Citation Trend",
                "xlabel": "Year",
                "ylabel": "Citations",
            },
        ],
        "title": "Biomarker Analysis Report",
    }


@pytest.fixture
def sample_vertical_report_data():
    """Sample data for vertical layout report."""
    return {
        "panels": [
            {
                "data": {
                    "categories": ["CA-125", "HE4"],
                    "values": [150, 125],
                },
                "type": "bar",
                "title": "Panel 1",
            },
            {
                "data": {
                    "categories": ["Diagnostic", "Prognostic"],
                    "values": [200, 150],
                },
                "type": "pie",
                "title": "Panel 2",
            },
        ],
        "title": "Vertical Report",
    }


@pytest.fixture
def sample_executive_summary():
    """Sample executive summary data."""
    return {
        "citation_distribution": {
            "CA-125": 150,
            "HE4": 125,
            "PSA": 100,
            "CEA": 75,
        },
        "usage_types": {"Diagnostic": 200, "Prognostic": 150, "Therapeutic": 50},
        "temporal_trend": {
            "2020": 100,
            "2021": 150,
            "2022": 200,
            "2023": 250,
            "2024": 300,
        },
    }


@pytest.fixture
def sample_biomarker_analysis():
    """Sample biomarker analysis data."""
    return {
        "top_biomarkers": {
            "CA-125": 150,
            "HE4": 125,
            "PSA": 100,
            "CEA": 75,
            "AFP": 50,
        },
        "usage_distribution": {
            "Diagnostic": 200,
            "Prognostic": 150,
            "Therapeutic": 50,
        },
        "temporal_trend": {
            "2020": 100,
            "2021": 150,
            "2022": 200,
            "2023": 250,
            "2024": 300,
        },
    }


class TestReportVisualizer:
    """Test suite for report visualization."""

    def test_initialization(self):
        """Test visualizer initialization."""
        viz = ReportVisualizer()
        assert viz.config is not None
        assert viz.figure is None
        assert viz.data is None

    def test_initialization_with_config(self):
        """Test initialization with custom config."""
        config = VisualizationConfig(width=1600, height=1200)
        viz = ReportVisualizer(config)
        assert viz.config.width == 1600
        assert viz.config.height == 1200

    def test_create_grid_layout_3_panels(self, sample_grid_report_data):
        """Test grid layout with 3 panels (should be 2x2)."""
        viz = ReportVisualizer()
        fig = viz.create(sample_grid_report_data, layout="grid")

        assert fig is not None
        assert viz.figure is not None
        assert len(fig.data) == 3  # Three panels

    def test_create_grid_layout_4_panels(self):
        """Test grid layout with 4 panels (should be 2x2)."""
        data = {
            "panels": [
                {"data": {"categories": ["A"], "values": [1]}, "type": "bar"},
                {"data": {"categories": ["B"], "values": [2]}, "type": "bar"},
                {"data": {"categories": ["C"], "values": [3]}, "type": "bar"},
                {"data": {"categories": ["D"], "values": [4]}, "type": "bar"},
            ]
        }

        viz = ReportVisualizer()
        fig = viz.create(data, layout="grid")

        assert fig is not None
        assert len(fig.data) == 4

    def test_create_grid_layout_6_panels(self):
        """Test grid layout with 6 panels (should be 2x3)."""
        data = {"panels": [{"data": {"categories": ["A"], "values": [i]}, "type": "bar"} for i in range(6)]}

        viz = ReportVisualizer()
        fig = viz.create(data, layout="grid")

        assert fig is not None
        assert len(fig.data) == 6

    def test_create_vertical_layout(self, sample_vertical_report_data):
        """Test vertical layout."""
        viz = ReportVisualizer()
        fig = viz.create(sample_vertical_report_data, layout="vertical")

        assert fig is not None
        assert len(fig.data) == 2

    def test_create_horizontal_layout(self, sample_vertical_report_data):
        """Test horizontal layout."""
        viz = ReportVisualizer()
        fig = viz.create(sample_vertical_report_data, layout="horizontal")

        assert fig is not None
        assert len(fig.data) == 2

    def test_bar_panel(self):
        """Test bar chart panel."""
        data = {
            "panels": [
                {
                    "data": {
                        "categories": ["CA-125", "HE4"],
                        "values": [150, 125],
                    },
                    "type": "bar",
                    "title": "Biomarkers",
                }
            ]
        }

        viz = ReportVisualizer()
        fig = viz.create(data)

        assert fig is not None
        assert len(fig.data) == 1

    def test_line_panel(self):
        """Test line chart panel."""
        data = {
            "panels": [
                {
                    "data": {"x": [2020, 2021], "y": [100, 150]},
                    "type": "line",
                    "title": "Trend",
                }
            ]
        }

        viz = ReportVisualizer()
        fig = viz.create(data)

        assert fig is not None
        assert len(fig.data) == 1

    def test_pie_panel(self):
        """Test pie chart panel."""
        data = {
            "panels": [
                {
                    "data": {"categories": ["A", "B"], "values": [50, 50]},
                    "type": "pie",
                    "title": "Distribution",
                }
            ]
        }

        viz = ReportVisualizer()
        fig = viz.create(data)

        assert fig is not None
        assert len(fig.data) == 1

    def test_report_with_summary(self, sample_grid_report_data):
        """Test report with summary included."""
        viz = ReportVisualizer()
        fig = viz.create(sample_grid_report_data, include_summary=True)

        assert fig is not None
        # Check that title is set
        assert fig.layout.title.text is not None

    def test_report_without_summary(self, sample_grid_report_data):
        """Test report without summary."""
        viz = ReportVisualizer()
        fig = viz.create(sample_grid_report_data, include_summary=False)

        assert fig is not None

    def test_update_visualization(self, sample_grid_report_data):
        """Test updating visualization properties."""
        viz = ReportVisualizer()
        viz.create(sample_grid_report_data)

        viz.update(title="Custom Report Title")
        assert "Custom Report Title" in str(viz.figure.layout.title.text)

    def test_export_html(self, sample_grid_report_data, tmp_path):
        """Test HTML export."""
        viz = ReportVisualizer()
        viz.create(sample_grid_report_data)

        options = ExportOptions(format="html", filename="test_report.html")
        output_path = viz.export(options)

        assert output_path.endswith(".html")

    def test_export_json(self, sample_grid_report_data, tmp_path):
        """Test JSON export."""
        viz = ReportVisualizer()
        viz.create(sample_grid_report_data)

        options = ExportOptions(format="json", filename="test_report.json")
        output_path = viz.export(options)

        assert output_path.endswith(".json")

    def test_serialize_data(self, sample_grid_report_data):
        """Test data serialization."""
        viz = ReportVisualizer()
        viz.create(sample_grid_report_data)

        serialized = viz._serialize_data()
        assert serialized == sample_grid_report_data


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_create_executive_dashboard(self, sample_executive_summary):
        """Test executive dashboard creation."""
        fig = create_executive_dashboard(sample_executive_summary)

        assert fig is not None
        # Should have 3 panels (citation dist, usage, trend)
        assert len(fig.data) == 3

    def test_create_biomarker_report_grid(self, sample_biomarker_analysis):
        """Test biomarker report with grid layout."""
        fig = create_biomarker_report(sample_biomarker_analysis, layout="grid")

        assert fig is not None
        assert len(fig.data) == 3

    def test_create_biomarker_report_vertical(self, sample_biomarker_analysis):
        """Test biomarker report with vertical layout."""
        fig = create_biomarker_report(sample_biomarker_analysis, layout="vertical")

        assert fig is not None
        assert len(fig.data) == 3

    def test_create_biomarker_report_horizontal(self, sample_biomarker_analysis):
        """Test biomarker report with horizontal layout."""
        fig = create_biomarker_report(sample_biomarker_analysis, layout="horizontal")

        assert fig is not None
        assert len(fig.data) == 3

    def test_convenience_with_export(self, sample_executive_summary, tmp_path):
        """Test convenience function with export."""
        create_executive_dashboard(sample_executive_summary, export_path="test_dashboard.html")

        # Output file should exist
        from pathlib import Path

        output_dir = Path("data/visualizations")
        assert (output_dir / "test_dashboard.html").exists()


class TestCustomization:
    """Test customization options."""

    def test_color_schemes(self, sample_grid_report_data):
        """Test different color schemes."""
        schemes = ["default", "colorblind", "high_contrast"]

        for scheme in schemes:
            config = VisualizationConfig(color_scheme=scheme)
            viz = ReportVisualizer(config)
            fig = viz.create(sample_grid_report_data)
            assert fig is not None

    def test_themes(self, sample_grid_report_data):
        """Test different themes."""
        themes = ["plotly_white", "plotly_dark", "seaborn"]

        for theme in themes:
            config = VisualizationConfig(theme=theme)
            viz = ReportVisualizer(config)
            fig = viz.create(sample_grid_report_data)
            assert fig is not None

    def test_custom_dimensions(self, sample_grid_report_data):
        """Test custom dimensions."""
        config = VisualizationConfig(width=1800, height=1400)
        viz = ReportVisualizer(config)
        fig = viz.create(sample_grid_report_data)

        assert fig.layout.width == 1800
        assert fig.layout.height == 1400


class TestEdgeCases:
    """Test edge cases."""

    def test_empty_panels(self):
        """Test with no panels."""
        data = {"panels": []}

        viz = ReportVisualizer()
        fig = viz.create(data)

        assert fig is not None

    def test_single_panel(self):
        """Test with single panel."""
        data = {"panels": [{"data": {"categories": ["A"], "values": [1]}, "type": "bar"}]}

        viz = ReportVisualizer()
        fig = viz.create(data)

        assert fig is not None
        assert len(fig.data) == 1

    def test_many_panels(self):
        """Test with many panels (9 panels for 3x3 grid)."""
        data = {"panels": [{"data": {"categories": ["A"], "values": [i]}, "type": "bar"} for i in range(9)]}

        viz = ReportVisualizer()
        fig = viz.create(data)

        assert fig is not None
        assert len(fig.data) == 9

    def test_unsupported_layout_raises_error(self, sample_grid_report_data):
        """Test that unsupported layout raises ValueError."""
        viz = ReportVisualizer()

        with pytest.raises(ValueError, match="Unsupported layout"):
            viz.create(sample_grid_report_data, layout="unsupported")

    def test_panel_without_title(self):
        """Test panel without title."""
        data = {"panels": [{"data": {"categories": ["A"], "values": [1]}, "type": "bar"}]}

        viz = ReportVisualizer()
        fig = viz.create(data)

        assert fig is not None

    def test_panel_without_labels(self):
        """Test panel without axis labels."""
        data = {
            "panels": [
                {
                    "data": {"categories": ["A"], "values": [1]},
                    "type": "bar",
                    "title": "Test",
                }
            ]
        }

        viz = ReportVisualizer()
        fig = viz.create(data)

        assert fig is not None


class TestLayoutCalculations:
    """Test layout dimension calculations."""

    def test_1_panel_dimensions(self):
        """Test dimensions for 1 panel."""
        data = {"panels": [{"data": {}, "type": "bar"}]}

        viz = ReportVisualizer()
        fig = viz.create(data, layout="grid")

        assert fig is not None

    def test_2_panel_dimensions(self):
        """Test dimensions for 2 panels (1 row x 2 cols)."""
        data = {"panels": [{"data": {}, "type": "bar"} for _ in range(2)]}

        viz = ReportVisualizer()
        fig = viz.create(data, layout="grid")

        assert fig is not None

    def test_3_panel_dimensions(self):
        """Test dimensions for 3 panels (2x2 grid)."""
        data = {"panels": [{"data": {}, "type": "bar"} for _ in range(3)]}

        viz = ReportVisualizer()
        fig = viz.create(data, layout="grid")

        assert fig is not None

    def test_5_panel_dimensions(self):
        """Test dimensions for 5 panels (2x3 grid)."""
        data = {"panels": [{"data": {}, "type": "bar"} for _ in range(5)]}

        viz = ReportVisualizer()
        fig = viz.create(data, layout="grid")

        assert fig is not None

    def test_7_panel_dimensions(self):
        """Test dimensions for 7 panels (3x3 grid)."""
        data = {"panels": [{"data": {}, "type": "bar"} for _ in range(7)]}

        viz = ReportVisualizer()
        fig = viz.create(data, layout="grid")

        assert fig is not None


class TestIntegration:
    """Test integration with other visualization components."""

    def test_mixed_panel_types(self):
        """Test report with mixed panel types."""
        data = {
            "panels": [
                {"data": {"categories": ["A"], "values": [1]}, "type": "bar"},
                {"data": {"x": [1], "y": [2]}, "type": "line"},
                {"data": {"categories": ["C"], "values": [3]}, "type": "pie"},
            ]
        }

        viz = ReportVisualizer()
        fig = viz.create(data)

        assert fig is not None
        assert len(fig.data) == 3
