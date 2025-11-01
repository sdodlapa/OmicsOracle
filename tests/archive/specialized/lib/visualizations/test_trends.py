"""
Tests for trend visualization.
"""

from datetime import datetime, timedelta
from pathlib import Path

import pytest

from omics_oracle_v2.lib.visualizations import ExportOptions, VisualizationConfig
from omics_oracle_v2.lib.visualizations.trends import TrendVisualizer, visualize_citation_timeline


@pytest.fixture
def sample_citation_timeline():
    """Sample citation timeline data."""
    start_date = datetime(2020, 1, 1)
    dates = [(start_date + timedelta(days=i * 30)).strftime("%Y-%m-%d") for i in range(12)]
    counts = [10, 15, 22, 28, 35, 42, 38, 45, 52, 48, 55, 60]

    return {
        "dates": dates,
        "counts": counts,
        "peaks": [
            {"date": dates[6], "count": 45, "reason": "Major conference"},
            {"date": dates[10], "count": 55, "reason": "Review publication"},
        ],
        "forecast": {
            "dates": [(start_date + timedelta(days=i * 30)).strftime("%Y-%m-%d") for i in range(12, 15)],
            "values": [65, 70, 72],
        },
    }


@pytest.fixture
def sample_usage_evolution():
    """Sample usage evolution data."""
    start_date = datetime(2020, 1, 1)
    dates = [(start_date + timedelta(days=i * 30)).strftime("%Y-%m-%d") for i in range(12)]

    return {
        "dates": dates,
        "by_type": {
            "diagnostic": [5, 8, 10, 12, 15, 18, 20, 22, 25, 28, 30, 32],
            "prognostic": [3, 4, 6, 8, 10, 12, 10, 13, 15, 12, 18, 20],
            "therapeutic": [2, 3, 6, 8, 10, 12, 8, 10, 12, 8, 7, 8],
            "research": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        },
    }


@pytest.fixture
def sample_impact_trajectory():
    """Sample impact trajectory data."""
    start_date = datetime(2020, 1, 1)
    dates = [(start_date + timedelta(days=i * 30)).strftime("%Y-%m-%d") for i in range(12)]

    return {
        "dates": dates,
        "citation_counts": [10, 15, 22, 28, 35, 42, 38, 45, 52, 48, 55, 60],
        "impact_scores": [5.0, 5.5, 6.2, 6.8, 7.5, 8.2, 7.8, 8.5, 9.2, 8.8, 9.5, 10.0],
        "growth_rates": [0.0, 0.5, 0.47, 0.27, 0.25, 0.20, -0.10, 0.18, 0.16, -0.08, 0.15, 0.09],
    }


class TestTrendVisualizer:
    """Test suite for trend visualization."""

    def test_initialization(self):
        """Test visualizer initialization."""
        viz = TrendVisualizer()
        assert viz.config is not None
        assert viz.figure is None
        assert viz.data is None

    def test_initialization_with_config(self):
        """Test visualizer initialization with custom config."""
        config = VisualizationConfig(width=1000, height=700, theme="plotly_dark")
        viz = TrendVisualizer(config)
        assert viz.config.width == 1000
        assert viz.config.height == 700
        assert viz.config.theme == "plotly_dark"

    def test_create_citation_timeline(self, sample_citation_timeline):
        """Test creating citation timeline visualization."""
        viz = TrendVisualizer()
        fig = viz.create({"citation_timeline": sample_citation_timeline})

        assert fig is not None
        assert viz.figure is not None
        assert len(fig.data) >= 1  # At least main trace

    def test_citation_timeline_line_chart(self, sample_citation_timeline):
        """Test citation timeline as line chart."""
        viz = TrendVisualizer()
        fig = viz.create({"citation_timeline": sample_citation_timeline}, chart_type="line")

        assert fig is not None
        assert len(fig.data) >= 1

    def test_citation_timeline_area_chart(self, sample_citation_timeline):
        """Test citation timeline as area chart."""
        viz = TrendVisualizer()
        fig = viz.create({"citation_timeline": sample_citation_timeline}, chart_type="area")

        assert fig is not None
        assert len(fig.data) >= 1

    def test_citation_timeline_bar_chart(self, sample_citation_timeline):
        """Test citation timeline as bar chart."""
        viz = TrendVisualizer()
        fig = viz.create({"citation_timeline": sample_citation_timeline}, chart_type="bar")

        assert fig is not None
        assert len(fig.data) >= 1

    def test_citation_timeline_with_peaks(self, sample_citation_timeline):
        """Test citation timeline with peak highlighting."""
        viz = TrendVisualizer()
        fig = viz.create({"citation_timeline": sample_citation_timeline}, show_peaks=True)

        assert fig is not None
        # Should have main trace + peaks trace
        assert len(fig.data) >= 2

    def test_citation_timeline_with_forecast(self, sample_citation_timeline):
        """Test citation timeline with forecast."""
        viz = TrendVisualizer()
        fig = viz.create({"citation_timeline": sample_citation_timeline}, show_forecast=True)

        assert fig is not None
        # Should have main trace + forecast trace (+ peaks if enabled)
        assert len(fig.data) >= 2

    def test_create_usage_evolution(self, sample_usage_evolution):
        """Test creating usage evolution visualization."""
        viz = TrendVisualizer()
        fig = viz.create({"usage_evolution": sample_usage_evolution})

        assert fig is not None
        assert viz.figure is not None
        # Should have trace for each usage type
        assert len(fig.data) >= 3

    def test_usage_evolution_area_chart(self, sample_usage_evolution):
        """Test usage evolution as stacked area chart."""
        viz = TrendVisualizer()
        fig = viz.create({"usage_evolution": sample_usage_evolution}, chart_type="area")

        assert fig is not None
        assert len(fig.data) >= 3

    def test_usage_evolution_bar_chart(self, sample_usage_evolution):
        """Test usage evolution as stacked bar chart."""
        viz = TrendVisualizer()
        fig = viz.create({"usage_evolution": sample_usage_evolution}, chart_type="bar")

        assert fig is not None
        assert len(fig.data) >= 3

    def test_create_impact_trajectory(self, sample_impact_trajectory):
        """Test creating impact trajectory visualization."""
        viz = TrendVisualizer()
        fig = viz.create({"impact_trajectory": sample_impact_trajectory})

        assert fig is not None
        assert viz.figure is not None
        # Should have citation and impact traces (at minimum)
        assert len(fig.data) >= 2

    def test_impact_trajectory_with_growth_rate(self, sample_impact_trajectory):
        """Test impact trajectory with growth rate."""
        viz = TrendVisualizer()
        fig = viz.create({"impact_trajectory": sample_impact_trajectory})

        assert fig is not None
        # Should have citation, impact, and growth rate traces
        assert len(fig.data) >= 3

    def test_create_generic_timeseries(self):
        """Test creating generic time series."""
        generic_data = {
            "series1": {
                "dates": ["2020-01", "2020-02", "2020-03"],
                "values": [10, 20, 15],
            },
            "series2": {
                "dates": ["2020-01", "2020-02", "2020-03"],
                "values": [5, 15, 25],
            },
        }

        viz = TrendVisualizer()
        fig = viz.create(generic_data)

        assert fig is not None
        assert len(fig.data) == 2  # Two series

    def test_update_visualization(self, sample_citation_timeline):
        """Test updating visualization properties."""
        viz = TrendVisualizer()
        viz.create({"citation_timeline": sample_citation_timeline})

        # Update title
        viz.update(title="Custom Timeline Title")
        assert "Custom Timeline Title" in str(viz.figure.layout.title.text)

        # Update chart type
        viz.update(chart_type="bar")
        assert viz.figure is not None

    def test_update_without_figure_raises_error(self):
        """Test that update raises error without figure."""
        viz = TrendVisualizer()

        with pytest.raises(ValueError, match="No figure to update"):
            viz.update(title="Test")

    def test_export_html(self, sample_citation_timeline, tmp_path):
        """Test HTML export."""
        viz = TrendVisualizer()
        viz.create({"citation_timeline": sample_citation_timeline})

        filename = "test_trends.html"
        options = ExportOptions(format="html", filename=filename)
        output_path = viz.export(options)

        assert output_path.endswith(".html")
        assert Path(output_path).exists()

    def test_export_without_figure_raises_error(self):
        """Test that export raises error without figure."""
        viz = TrendVisualizer()

        with pytest.raises(ValueError, match="No figure to export"):
            viz.export()

    def test_export_json(self, sample_citation_timeline, tmp_path):
        """Test JSON export."""
        viz = TrendVisualizer()
        viz.create({"citation_timeline": sample_citation_timeline})

        filename = "test_trends.json"
        options = ExportOptions(format="json", filename=filename)
        output_path = viz.export(options)

        assert output_path.endswith(".json")
        assert Path(output_path).exists()

    def test_serialize_data(self, sample_citation_timeline):
        """Test data serialization."""
        viz = TrendVisualizer()
        data = {"citation_timeline": sample_citation_timeline}
        viz.create(data)

        serialized = viz._serialize_data()
        assert serialized == data
        assert "citation_timeline" in serialized

    def test_serialize_empty_data(self):
        """Test serialization with no data."""
        viz = TrendVisualizer()
        serialized = viz._serialize_data()
        assert serialized == {}


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_visualize_citation_timeline(self, sample_citation_timeline):
        """Test citation timeline convenience function."""
        fig = visualize_citation_timeline(sample_citation_timeline)

        assert fig is not None
        assert len(fig.data) >= 1

    def test_visualize_with_custom_config(self, sample_citation_timeline):
        """Test visualization with custom config."""
        config = VisualizationConfig(width=1200, height=900)
        fig = visualize_citation_timeline(sample_citation_timeline, config=config)

        assert fig is not None
        assert fig.layout.width == 1200
        assert fig.layout.height == 900

    def test_visualize_with_chart_type(self, sample_citation_timeline):
        """Test visualization with specific chart type."""
        fig = visualize_citation_timeline(sample_citation_timeline, chart_type="bar")

        assert fig is not None
        assert len(fig.data) >= 1

    def test_visualize_with_export(self, sample_citation_timeline, tmp_path):
        """Test visualization with export."""
        export_path = "test_timeline.html"
        fig = visualize_citation_timeline(sample_citation_timeline, export_path=export_path)

        assert fig is not None
        # Output file should exist in data/visualizations
        output_dir = Path("data/visualizations")
        assert (output_dir / export_path).exists()


class TestVisualizationCustomization:
    """Test visualization customization options."""

    def test_color_schemes(self, sample_citation_timeline):
        """Test different color schemes."""
        schemes = ["default", "colorblind", "high_contrast"]

        for scheme in schemes:
            config = VisualizationConfig(color_scheme=scheme)
            viz = TrendVisualizer(config)
            fig = viz.create({"citation_timeline": sample_citation_timeline})
            assert fig is not None

    def test_themes(self, sample_citation_timeline):
        """Test different themes."""
        themes = ["plotly_white", "plotly_dark", "seaborn"]

        for theme in themes:
            config = VisualizationConfig(theme=theme)
            viz = TrendVisualizer(config)
            fig = viz.create({"citation_timeline": sample_citation_timeline})
            assert fig is not None

    def test_custom_dimensions(self, sample_citation_timeline):
        """Test custom width and height."""
        config = VisualizationConfig(width=1600, height=1000)
        viz = TrendVisualizer(config)
        fig = viz.create({"citation_timeline": sample_citation_timeline})

        assert fig.layout.width == 1600
        assert fig.layout.height == 1000

    def test_legend_toggle(self, sample_citation_timeline):
        """Test legend show/hide."""
        # With legend
        config1 = VisualizationConfig(show_legend=True)
        viz1 = TrendVisualizer(config1)
        fig1 = viz1.create({"citation_timeline": sample_citation_timeline})
        assert fig1.layout.showlegend is True

        # Without legend
        config2 = VisualizationConfig(show_legend=False)
        viz2 = TrendVisualizer(config2)
        fig2 = viz2.create({"citation_timeline": sample_citation_timeline})
        assert fig2.layout.showlegend is False


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_timeline_data(self):
        """Test with empty timeline data."""
        viz = TrendVisualizer()
        empty_data = {"citation_timeline": {"dates": [], "counts": []}}

        # Should not raise error
        fig = viz.create(empty_data)
        assert fig is not None

    def test_missing_peaks_data(self, sample_citation_timeline):
        """Test timeline without peaks data."""
        data = sample_citation_timeline.copy()
        del data["peaks"]

        viz = TrendVisualizer()
        fig = viz.create({"citation_timeline": data}, show_peaks=True)

        assert fig is not None

    def test_missing_forecast_data(self, sample_citation_timeline):
        """Test timeline without forecast data."""
        data = sample_citation_timeline.copy()
        del data["forecast"]

        viz = TrendVisualizer()
        fig = viz.create({"citation_timeline": data}, show_forecast=True)

        assert fig is not None

    def test_single_data_point(self):
        """Test with single data point."""
        single_point = {"citation_timeline": {"dates": ["2020-01-01"], "counts": [10]}}

        viz = TrendVisualizer()
        fig = viz.create(single_point)

        assert fig is not None
        assert len(fig.data) >= 1
