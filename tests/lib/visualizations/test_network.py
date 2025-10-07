"""
Tests for citation network visualization.
"""

from pathlib import Path

import pytest

from omics_oracle_v2.lib.visualizations import ExportOptions, VisualizationConfig
from omics_oracle_v2.lib.visualizations.network import CitationNetworkVisualizer, visualize_knowledge_graph


@pytest.fixture
def sample_graph_data():
    """Sample knowledge graph data for testing."""
    return {
        "nodes": [
            {
                "id": "biomarker1",
                "type": "biomarker",
                "label": "CA-125",
                "citations": 150,
                "impact": 8.5,
            },
            {
                "id": "biomarker2",
                "type": "biomarker",
                "label": "HE4",
                "citations": 120,
                "impact": 7.2,
            },
            {
                "id": "paper1",
                "type": "paper",
                "label": "Smith et al. 2020",
                "citations": 45,
                "impact": 6.1,
            },
            {
                "id": "paper2",
                "type": "paper",
                "label": "Jones et al. 2021",
                "citations": 38,
                "impact": 5.8,
            },
            {
                "id": "disease1",
                "type": "disease",
                "label": "Ovarian Cancer",
                "citations": 200,
                "impact": 9.0,
            },
        ],
        "edges": [
            {
                "source": "paper1",
                "target": "biomarker1",
                "relationship": "studies",
                "strength": 0.9,
            },
            {
                "source": "paper1",
                "target": "disease1",
                "relationship": "investigates",
                "strength": 0.8,
            },
            {
                "source": "paper2",
                "target": "biomarker2",
                "relationship": "studies",
                "strength": 0.85,
            },
            {
                "source": "biomarker1",
                "target": "disease1",
                "relationship": "associated_with",
                "strength": 0.95,
            },
            {
                "source": "biomarker2",
                "target": "disease1",
                "relationship": "associated_with",
                "strength": 0.88,
            },
        ],
    }


class TestCitationNetworkVisualizer:
    """Test suite for citation network visualization."""

    def test_initialization(self):
        """Test visualizer initialization."""
        viz = CitationNetworkVisualizer()
        assert viz.config is not None
        assert viz.figure is None
        assert viz.data is None

    def test_initialization_with_config(self):
        """Test visualizer initialization with custom config."""
        config = VisualizationConfig(width=800, height=600, theme="plotly_dark")
        viz = CitationNetworkVisualizer(config)
        assert viz.config.width == 800
        assert viz.config.height == 600
        assert viz.config.theme == "plotly_dark"

    def test_create_network(self, sample_graph_data):
        """Test creating network visualization."""
        viz = CitationNetworkVisualizer()
        fig = viz.create(sample_graph_data)

        assert fig is not None
        assert viz.figure is not None
        assert viz.data == sample_graph_data
        assert len(fig.data) > 0  # Should have traces

    def test_different_layouts(self, sample_graph_data):
        """Test different layout algorithms."""
        viz = CitationNetworkVisualizer()

        layouts = ["spring", "circular", "kamada_kawai", "shell"]

        for layout in layouts:
            fig = viz.create(sample_graph_data, layout=layout)
            assert fig is not None
            assert len(fig.data) > 0

    def test_node_sizing(self, sample_graph_data):
        """Test different node sizing metrics."""
        viz = CitationNetworkVisualizer()

        # Test citations-based sizing
        fig1 = viz.create(sample_graph_data, node_size_by="citations")
        assert fig1 is not None

        # Test impact-based sizing
        fig2 = viz.create(sample_graph_data, node_size_by="impact")
        assert fig2 is not None

    def test_edge_coloring(self, sample_graph_data):
        """Test edge coloring by relationship."""
        viz = CitationNetworkVisualizer()
        fig = viz.create(sample_graph_data, edge_color_by="relationship")

        assert fig is not None
        # Should have multiple traces for different relationships
        assert len(fig.data) > 1

    def test_update_visualization(self, sample_graph_data):
        """Test updating visualization properties."""
        viz = CitationNetworkVisualizer()
        viz.create(sample_graph_data)

        # Update title
        viz.update(title="Custom Network Title")
        assert "Custom Network Title" in str(viz.figure.layout.title.text)

        # Update layout
        viz.update(layout="circular")
        assert viz.figure is not None

    def test_update_without_figure_raises_error(self):
        """Test that update raises error without figure."""
        viz = CitationNetworkVisualizer()

        with pytest.raises(ValueError, match="No figure to update"):
            viz.update(title="Test")

    def test_get_network_stats(self, sample_graph_data):
        """Test network statistics calculation."""
        viz = CitationNetworkVisualizer()
        viz.create(sample_graph_data)

        stats = viz.get_network_stats()

        assert stats["num_nodes"] == 5
        assert stats["num_edges"] == 5
        assert "density" in stats
        assert "avg_degree" in stats
        assert "connected_components" in stats
        assert "top_nodes_by_centrality" in stats

    def test_get_network_stats_empty_data(self):
        """Test network stats with no data."""
        viz = CitationNetworkVisualizer()
        stats = viz.get_network_stats()
        assert stats == {}

    def test_export_html(self, sample_graph_data, tmp_path):
        """Test HTML export."""
        viz = CitationNetworkVisualizer()
        viz.create(sample_graph_data)

        filename = "test_network.html"
        options = ExportOptions(format="html", filename=filename)
        output_path = viz.export(options)

        assert output_path.endswith(".html")
        assert Path(output_path).exists()

    def test_export_without_figure_raises_error(self):
        """Test that export raises error without figure."""
        viz = CitationNetworkVisualizer()

        with pytest.raises(ValueError, match="No figure to export"):
            viz.export()

    def test_export_json(self, sample_graph_data, tmp_path):
        """Test JSON export."""
        viz = CitationNetworkVisualizer()
        viz.create(sample_graph_data)

        filename = "test_network.json"
        options = ExportOptions(format="json", filename=filename)
        output_path = viz.export(options)

        assert output_path.endswith(".json")
        assert Path(output_path).exists()

    def test_serialize_data(self, sample_graph_data):
        """Test data serialization."""
        viz = CitationNetworkVisualizer()
        viz.create(sample_graph_data)

        serialized = viz._serialize_data()
        assert serialized == sample_graph_data
        assert "nodes" in serialized
        assert "edges" in serialized

    def test_serialize_empty_data(self):
        """Test serialization with no data."""
        viz = CitationNetworkVisualizer()
        serialized = viz._serialize_data()
        assert serialized == {}


class TestVisualizationConvenienceFunctions:
    """Test convenience functions."""

    def test_visualize_knowledge_graph(self, sample_graph_data):
        """Test knowledge graph visualization convenience function."""
        fig = visualize_knowledge_graph(sample_graph_data)

        assert fig is not None
        assert len(fig.data) > 0

    def test_visualize_with_custom_config(self, sample_graph_data):
        """Test visualization with custom config."""
        config = VisualizationConfig(width=1000, height=800)
        fig = visualize_knowledge_graph(sample_graph_data, config=config)

        assert fig is not None
        assert fig.layout.width == 1000
        assert fig.layout.height == 800

    def test_visualize_with_layout(self, sample_graph_data):
        """Test visualization with specific layout."""
        fig = visualize_knowledge_graph(sample_graph_data, layout="circular")

        assert fig is not None
        assert len(fig.data) > 0

    def test_visualize_with_export(self, sample_graph_data, tmp_path):
        """Test visualization with export."""
        export_path = "test_graph.html"
        fig = visualize_knowledge_graph(sample_graph_data, export_path=export_path)

        assert fig is not None
        # Output file should exist in data/visualizations
        output_dir = Path("data/visualizations")
        assert (output_dir / export_path).exists()


class TestNetworkGraphConstruction:
    """Test NetworkX graph construction."""

    def test_build_networkx_graph(self, sample_graph_data):
        """Test NetworkX graph building."""
        viz = CitationNetworkVisualizer()
        G = viz._build_networkx_graph(sample_graph_data)

        assert G.number_of_nodes() == 5
        assert G.number_of_edges() == 5

        # Check node attributes
        node_data = G.nodes["biomarker1"]
        assert node_data["type"] == "biomarker"
        assert node_data["label"] == "CA-125"
        assert node_data["citations"] == 150

        # Check edge attributes
        edge_data = G.edges["paper1", "biomarker1"]
        assert edge_data["relationship"] == "studies"
        assert edge_data["strength"] == 0.9

    def test_calculate_layout(self, sample_graph_data):
        """Test layout calculation."""
        viz = CitationNetworkVisualizer()
        G = viz._build_networkx_graph(sample_graph_data)

        # Test different layouts
        pos_spring = viz._calculate_layout(G, "spring")
        assert len(pos_spring) == 5

        pos_circular = viz._calculate_layout(G, "circular")
        assert len(pos_circular) == 5

        # Positions should be different for different layouts
        # Compare using tuple conversion to avoid numpy array comparison issues
        assert tuple(pos_spring["biomarker1"]) != tuple(pos_circular["biomarker1"])


class TestVisualizationCustomization:
    """Test visualization customization options."""

    def test_color_schemes(self, sample_graph_data):
        """Test different color schemes."""
        schemes = ["default", "colorblind", "high_contrast"]

        for scheme in schemes:
            config = VisualizationConfig(color_scheme=scheme)
            viz = CitationNetworkVisualizer(config)
            fig = viz.create(sample_graph_data)
            assert fig is not None

    def test_themes(self, sample_graph_data):
        """Test different themes."""
        themes = ["plotly_white", "plotly_dark", "seaborn"]

        for theme in themes:
            config = VisualizationConfig(theme=theme)
            viz = CitationNetworkVisualizer(config)
            fig = viz.create(sample_graph_data)
            assert fig is not None

    def test_custom_dimensions(self, sample_graph_data):
        """Test custom width and height."""
        config = VisualizationConfig(width=1600, height=1200)
        viz = CitationNetworkVisualizer(config)
        fig = viz.create(sample_graph_data)

        assert fig.layout.width == 1600
        assert fig.layout.height == 1200

    def test_legend_toggle(self, sample_graph_data):
        """Test legend show/hide."""
        # With legend
        config1 = VisualizationConfig(show_legend=True)
        viz1 = CitationNetworkVisualizer(config1)
        fig1 = viz1.create(sample_graph_data)
        assert fig1.layout.showlegend is True

        # Without legend
        config2 = VisualizationConfig(show_legend=False)
        viz2 = CitationNetworkVisualizer(config2)
        fig2 = viz2.create(sample_graph_data)
        assert fig2.layout.showlegend is False
