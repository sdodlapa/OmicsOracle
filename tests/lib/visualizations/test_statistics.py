"""
Tests for statistical visualization.
"""

import pytest

from omics_oracle_v2.lib.visualizations import ExportOptions, VisualizationConfig
from omics_oracle_v2.lib.visualizations.statistics import (
    StatisticalVisualizer,
    create_biomarker_distribution,
    create_correlation_heatmap,
    create_usage_type_pie,
)


@pytest.fixture
def sample_distribution_data():
    """Sample distribution data for testing."""
    return {
        "distribution": {
            "values": [1.2, 2.3, 1.8, 3.1, 2.7, 1.5, 2.9, 3.5, 2.1, 1.9],
            "name": "Biomarker Expression",
        },
        "title": "Expression Level Distribution",
        "xlabel": "Expression Level",
        "ylabel": "Frequency",
    }


@pytest.fixture
def sample_box_plot_data():
    """Sample box plot data for testing."""
    return {
        "groups": {
            "CA-125": [1.2, 2.3, 1.8, 3.1, 2.7],
            "HE4": [2.5, 3.2, 2.8, 3.9, 3.1],
            "PSA": [1.5, 1.8, 1.3, 2.1, 1.7],
        },
        "title": "Biomarker Expression Comparison",
        "xlabel": "Biomarker",
        "ylabel": "Expression Level",
    }


@pytest.fixture
def sample_pie_chart_data():
    """Sample pie chart data for testing."""
    return {
        "categories": ["Diagnostic", "Prognostic", "Therapeutic", "Research"],
        "values": [150, 85, 60, 105],
        "title": "Usage Type Distribution",
    }


@pytest.fixture
def sample_heatmap_data():
    """Sample heatmap data for testing."""
    return {
        "correlation_matrix": [
            [1.0, 0.8, -0.3, 0.5],
            [0.8, 1.0, -0.2, 0.4],
            [-0.3, -0.2, 1.0, -0.6],
            [0.5, 0.4, -0.6, 1.0],
        ],
        "labels": ["CA-125", "HE4", "PSA", "CEA"],
        "title": "Biomarker Correlation",
    }


class TestStatisticalVisualizer:
    """Test suite for statistical visualization."""

    def test_initialization(self):
        """Test visualizer initialization."""
        viz = StatisticalVisualizer()
        assert viz.config is not None
        assert viz.figure is None
        assert viz.data is None

    def test_initialization_with_config(self):
        """Test initialization with custom config."""
        config = VisualizationConfig(width=1000, height=700)
        viz = StatisticalVisualizer(config)
        assert viz.config.width == 1000
        assert viz.config.height == 700

    def test_create_histogram(self, sample_distribution_data):
        """Test histogram creation."""
        viz = StatisticalVisualizer()
        fig = viz.create(sample_distribution_data, chart_type="histogram")

        assert fig is not None
        assert viz.figure is not None
        assert len(fig.data) >= 1

    def test_histogram_with_statistics(self, sample_distribution_data):
        """Test histogram with statistics annotations."""
        viz = StatisticalVisualizer()
        fig = viz.create(sample_distribution_data, chart_type="histogram", show_statistics=True)

        assert fig is not None
        # Should have vlines for mean and median
        assert len(fig.layout.shapes) >= 2

    def test_create_box_plot(self, sample_box_plot_data):
        """Test box plot creation."""
        viz = StatisticalVisualizer()
        fig = viz.create(sample_box_plot_data, chart_type="box")

        assert fig is not None
        assert len(fig.data) == 3  # Three groups

    def test_box_plot_with_statistics(self, sample_box_plot_data):
        """Test box plot with statistics."""
        viz = StatisticalVisualizer()
        fig = viz.create(sample_box_plot_data, chart_type="box", show_statistics=True)

        assert fig is not None
        # Check that boxmean is set
        for trace in fig.data:
            assert hasattr(trace, "boxmean")

    def test_create_violin_plot(self, sample_box_plot_data):
        """Test violin plot creation."""
        viz = StatisticalVisualizer()
        fig = viz.create(sample_box_plot_data, chart_type="violin")

        assert fig is not None
        assert len(fig.data) == 3  # Three groups

    def test_create_pie_chart(self, sample_pie_chart_data):
        """Test pie chart creation."""
        viz = StatisticalVisualizer()
        fig = viz.create(sample_pie_chart_data, chart_type="pie")

        assert fig is not None
        assert len(fig.data) == 1  # One pie trace

    def test_pie_chart_with_statistics(self, sample_pie_chart_data):
        """Test pie chart with percentages."""
        viz = StatisticalVisualizer()
        fig = viz.create(sample_pie_chart_data, chart_type="pie", show_statistics=True)

        assert fig is not None
        # Check that text includes percentages
        assert fig.data[0].text is not None

    def test_create_heatmap(self, sample_heatmap_data):
        """Test heatmap creation."""
        viz = StatisticalVisualizer()
        fig = viz.create(sample_heatmap_data, chart_type="heatmap")

        assert fig is not None
        assert len(fig.data) == 1  # One heatmap trace

    def test_heatmap_with_annotations(self, sample_heatmap_data):
        """Test heatmap with value annotations."""
        viz = StatisticalVisualizer()
        fig = viz.create(sample_heatmap_data, chart_type="heatmap", show_statistics=True)

        assert fig is not None
        # Check for annotations
        assert fig.layout.annotations is not None
        assert len(fig.layout.annotations) == 16  # 4x4 matrix

    def test_auto_detect_chart_type(self, sample_distribution_data):
        """Test automatic chart type detection."""
        viz = StatisticalVisualizer()
        fig = viz.create(sample_distribution_data, chart_type="auto")

        assert fig is not None
        # Should detect histogram from 'distribution' key

    def test_update_visualization(self, sample_distribution_data):
        """Test updating visualization properties."""
        viz = StatisticalVisualizer()
        viz.create(sample_distribution_data)

        viz.update(title="Custom Title")
        assert "Custom Title" in str(viz.figure.layout.title.text)

    def test_update_without_figure_raises_error(self):
        """Test that update raises error without figure."""
        viz = StatisticalVisualizer()

        with pytest.raises(ValueError, match="No figure to update"):
            viz.update(title="Test")

    def test_export_html(self, sample_distribution_data, tmp_path):
        """Test HTML export."""
        viz = StatisticalVisualizer()
        viz.create(sample_distribution_data)

        options = ExportOptions(format="html", filename="test_stats.html")
        output_path = viz.export(options)

        assert output_path.endswith(".html")

    def test_export_json(self, sample_distribution_data, tmp_path):
        """Test JSON export."""
        viz = StatisticalVisualizer()
        viz.create(sample_distribution_data)

        options = ExportOptions(format="json", filename="test_stats.json")
        output_path = viz.export(options)

        assert output_path.endswith(".json")

    def test_serialize_data(self, sample_distribution_data):
        """Test data serialization."""
        viz = StatisticalVisualizer()
        viz.create(sample_distribution_data)

        serialized = viz._serialize_data()
        assert serialized == sample_distribution_data


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_create_biomarker_distribution(self):
        """Test biomarker distribution convenience function."""
        data = {
            "CA-125": [1.2, 2.3, 1.8, 3.1, 2.7],
            "HE4": [2.5, 3.2, 2.8, 3.9, 3.1],
        }

        fig = create_biomarker_distribution(data, chart_type="box")

        assert fig is not None
        assert len(fig.data) == 2

    def test_create_usage_type_pie(self):
        """Test usage type pie chart convenience function."""
        data = {"Diagnostic": 150, "Prognostic": 85, "Therapeutic": 60}

        fig = create_usage_type_pie(data)

        assert fig is not None
        assert len(fig.data) == 1

    def test_create_correlation_heatmap(self):
        """Test correlation heatmap convenience function."""
        matrix = [[1.0, 0.8], [0.8, 1.0]]
        labels = ["CA-125", "HE4"]

        fig = create_correlation_heatmap(matrix, labels)

        assert fig is not None
        assert len(fig.data) == 1

    def test_convenience_with_export(self, tmp_path):
        """Test convenience function with export."""
        data = {"Diagnostic": 150, "Prognostic": 85}

        create_usage_type_pie(data, export_path="test_usage.html")

        # Output file should exist
        from pathlib import Path

        output_dir = Path("data/visualizations")
        assert (output_dir / "test_usage.html").exists()


class TestChartTypes:
    """Test different chart types."""

    def test_scatter_matrix_creation(self):
        """Test scatter matrix creation."""
        data = {
            "data": {
                "CA-125": [1.2, 2.3, 1.8, 3.1],
                "HE4": [2.5, 3.2, 2.8, 3.9],
                "PSA": [1.5, 1.8, 1.3, 2.1],
            },
            "dimensions": ["CA-125", "HE4", "PSA"],
            "title": "Biomarker Scatter Matrix",
        }

        viz = StatisticalVisualizer()
        fig = viz.create(data, chart_type="scatter")

        assert fig is not None
        assert len(fig.data) == 1  # SPLOM trace

    def test_unsupported_chart_type_raises_error(self):
        """Test that unsupported chart type raises error."""
        viz = StatisticalVisualizer()
        data = {"values": [1, 2, 3]}

        with pytest.raises(ValueError, match="Unsupported chart type"):
            viz.create(data, chart_type="unsupported")


class TestCustomization:
    """Test customization options."""

    def test_color_schemes(self, sample_distribution_data):
        """Test different color schemes."""
        schemes = ["default", "colorblind", "high_contrast"]

        for scheme in schemes:
            config = VisualizationConfig(color_scheme=scheme)
            viz = StatisticalVisualizer(config)
            fig = viz.create(sample_distribution_data)
            assert fig is not None

    def test_themes(self, sample_distribution_data):
        """Test different themes."""
        themes = ["plotly_white", "plotly_dark", "seaborn"]

        for theme in themes:
            config = VisualizationConfig(theme=theme)
            viz = StatisticalVisualizer(config)
            fig = viz.create(sample_distribution_data)
            assert fig is not None

    def test_custom_dimensions(self, sample_distribution_data):
        """Test custom dimensions."""
        config = VisualizationConfig(width=1600, height=1000)
        viz = StatisticalVisualizer(config)
        fig = viz.create(sample_distribution_data)

        assert fig.layout.width == 1600
        assert fig.layout.height == 1000


class TestEdgeCases:
    """Test edge cases."""

    def test_empty_distribution(self):
        """Test with empty distribution."""
        data = {"distribution": {"values": []}, "title": "Empty"}

        viz = StatisticalVisualizer()
        fig = viz.create(data, chart_type="histogram")

        assert fig is not None

    def test_single_group_box_plot(self):
        """Test box plot with single group."""
        data = {"groups": {"Single": [1, 2, 3, 4, 5]}}

        viz = StatisticalVisualizer()
        fig = viz.create(data, chart_type="box")

        assert fig is not None
        assert len(fig.data) == 1

    def test_empty_pie_chart(self):
        """Test pie chart with no data."""
        data = {"categories": [], "values": []}

        viz = StatisticalVisualizer()
        fig = viz.create(data, chart_type="pie")

        assert fig is not None
