"""
Tests for dashboard components.
"""

from unittest.mock import MagicMock, patch

import pytest

from omics_oracle_v2.lib.dashboard.components import (
    AnalyticsPanel,
    BasePanel,
    ResultsPanel,
    SearchPanel,
    VisualizationPanel,
)
from omics_oracle_v2.lib.dashboard.config import DashboardConfig


class TestBasePanel:
    """Test base panel."""

    def test_initialization(self):
        """Test base panel initialization."""
        config = DashboardConfig()
        panel = BasePanel(config)

        assert panel.config == config

    def test_render_not_implemented(self):
        """Test render method raises NotImplementedError."""
        config = DashboardConfig()
        panel = BasePanel(config)

        with pytest.raises(NotImplementedError):
            panel.render()


class TestSearchPanel:
    """Test search panel."""

    @patch("streamlit.text_input")
    @patch("streamlit.multiselect")
    @patch("streamlit.slider")
    @patch("streamlit.number_input")
    @patch("streamlit.checkbox")
    def test_render_basic(
        self,
        mock_checkbox,
        mock_number_input,
        mock_slider,
        mock_multiselect,
        mock_text_input,
    ):
        """Test basic search panel rendering."""
        config = DashboardConfig()
        panel = SearchPanel(config)

        # Mock return values
        mock_text_input.return_value = "BRCA1 mutations"
        mock_multiselect.return_value = ["pubmed"]
        mock_slider.return_value = (2015, 2024)
        mock_number_input.return_value = 50
        mock_checkbox.return_value = False

        result = panel.render()

        assert result["query"] == "BRCA1 mutations"
        assert result["databases"] == ["pubmed"]
        assert result["year_range"] == (2015, 2024)
        assert result["max_results"] == 50
        assert result["use_llm"] is False

    @patch("streamlit.text_input")
    @patch("streamlit.multiselect")
    @patch("streamlit.slider")
    @patch("streamlit.number_input")
    @patch("streamlit.checkbox")
    def test_render_with_llm(
        self,
        mock_checkbox,
        mock_number_input,
        mock_slider,
        mock_multiselect,
        mock_text_input,
    ):
        """Test search panel with LLM enabled."""
        config = DashboardConfig(enable_llm_analysis=True)
        panel = SearchPanel(config)

        mock_text_input.return_value = "biomarkers"
        mock_multiselect.return_value = ["pubmed", "google_scholar"]
        mock_slider.return_value = (2020, 2024)
        mock_number_input.return_value = 100
        mock_checkbox.return_value = True

        result = panel.render()

        assert result["use_llm"] is True
        assert len(result["databases"]) == 2


class TestVisualizationPanel:
    """Test visualization panel."""

    @patch("streamlit.selectbox")
    def test_initialization(self, mock_selectbox):
        """Test visualization panel initialization."""
        config = DashboardConfig()
        panel = VisualizationPanel(config)

        assert panel.config == config
        assert panel.viz_types == [
            "Citation Network",
            "Temporal Trends",
            "Statistical Distribution",
            "Multi-Panel Report",
            "Biomarker Heatmap",
            "Research Flow (Sankey)",
            "Abstract Word Cloud",
        ]

    @patch("streamlit.selectbox")
    @patch("streamlit.info")
    def test_render_no_data(self, mock_info, mock_selectbox):
        """Test rendering without data."""
        config = DashboardConfig()
        panel = VisualizationPanel(config)

        mock_selectbox.return_value = "Citation Network"

        panel.render(None)
        mock_info.assert_called_once()

    @patch("streamlit.selectbox")
    @patch("streamlit.spinner")
    @patch("streamlit.plotly_chart")
    @patch("omics_oracle_v2.lib.visualizations.network.visualize_knowledge_graph")
    def test_render_network(self, mock_viz, mock_plotly, mock_spinner, mock_selectbox):
        """Test rendering citation network."""
        config = DashboardConfig()
        panel = VisualizationPanel(config)

        mock_selectbox.return_value = "Citation Network"
        mock_spinner.return_value.__enter__ = MagicMock()
        mock_spinner.return_value.__exit__ = MagicMock()
        mock_viz.return_value = MagicMock()  # Mock plotly figure

        data = {"network_data": {"nodes": ["A", "B"], "edges": [("A", "B")]}}

        panel.render(data)
        mock_viz.assert_called_once()

    @patch("streamlit.selectbox")
    def test_render_trends(self, mock_selectbox):
        """Test rendering temporal trends."""
        config = DashboardConfig()
        panel = VisualizationPanel(config)

        mock_selectbox.return_value = "Temporal Trends"
        data = {"dates": ["2020", "2021"], "counts": [10, 15]}

        with patch.object(panel, "_render_trends") as mock_render:
            panel.render(data)
            mock_render.assert_called_once_with(data)

    @patch("streamlit.selectbox")
    @patch("streamlit.plotly_chart")
    @patch("streamlit.slider")
    @patch("streamlit.caption")
    def test_render_heatmap(self, mock_caption, mock_slider, mock_plotly, mock_selectbox):
        """Test rendering biomarker heatmap."""
        config = DashboardConfig()
        panel = VisualizationPanel(config)

        mock_selectbox.return_value = "Biomarker Heatmap"
        mock_slider.return_value = 2

        data = {
            "publications": [
                {"biomarkers": ["BRCA1", "TP53"], "year": 2020},
                {"biomarkers": ["BRCA1", "EGFR"], "year": 2021},
            ]
        }

        panel.render(data)
        assert mock_plotly.called or mock_caption.called  # Should attempt rendering

    @patch("streamlit.selectbox")
    @patch("streamlit.plotly_chart")
    def test_render_sankey(self, mock_plotly, mock_selectbox):
        """Test rendering Sankey diagram."""
        config = DashboardConfig()
        panel = VisualizationPanel(config)

        mock_selectbox.return_value = "Research Flow (Sankey)"

        data = {
            "publications": [
                {"year": 2020, "source": "pubmed", "biomarkers": ["BRCA1"]},
                {"year": 2021, "source": "pmc", "biomarkers": ["TP53"]},
            ]
        }

        panel.render(data)
        assert mock_plotly.called  # Should create Sankey

    @patch("streamlit.selectbox")
    @patch("streamlit.plotly_chart")
    @patch("streamlit.info")
    def test_render_wordcloud_fallback(self, mock_info, mock_plotly, mock_selectbox):
        """Test rendering word cloud with fallback."""
        config = DashboardConfig()
        panel = VisualizationPanel(config)

        mock_selectbox.return_value = "Abstract Word Cloud"

        data = {
            "publications": [
                {"abstract": "This is a test abstract about biomarkers and cancer research"},
                {"abstract": "Another abstract discussing genetic mutations and treatments"},
            ]
        }

        panel.render(data)
        # Should use either wordcloud or plotly fallback
        assert mock_plotly.called or mock_info.called


class TestAnalyticsPanel:
    """Test analytics panel."""

    @patch("streamlit.metric")
    @patch("streamlit.tabs")
    def test_render_with_data(self, mock_tabs, mock_metric):
        """Test analytics panel rendering with data."""
        config = DashboardConfig()
        panel = AnalyticsPanel(config)

        data = {
            "total_results": 100,
            "total_citations": 5000,
            "avg_year": 2020,
            "databases": 3,
            "top_biomarkers": [{"title": "Test", "citations": 100}],
            "timeline": {"2020": 50, "2021": 50},
            "distribution": {"pubmed": 80, "google_scholar": 20},
        }

        mock_tabs.return_value = [MagicMock(), MagicMock(), MagicMock()]

        panel.render(data)
        assert mock_metric.call_count >= 4  # At least 4 metrics

    @patch("streamlit.info")
    def test_render_no_data(self, mock_info):
        """Test analytics panel without data."""
        config = DashboardConfig()
        panel = AnalyticsPanel(config)

        panel.render(None)
        mock_info.assert_called_once()

    @patch("streamlit.dataframe")
    @patch("streamlit.info")
    def test_render_top_biomarkers(self, mock_info, mock_dataframe):
        """Test rendering top biomarkers."""
        config = DashboardConfig()
        panel = AnalyticsPanel(config)

        # Method expects a dict with 'top_biomarkers' key
        results = {
            "top_biomarkers": [
                {"title": "Biomarker 1", "citations": 100, "year": 2020},
                {"title": "Biomarker 2", "citations": 80, "year": 2021},
            ]
        }

        panel._render_top_biomarkers(results)
        mock_dataframe.assert_called_once()

    @patch("streamlit.bar_chart")
    @patch("streamlit.info")
    def test_render_timeline(self, mock_info, mock_chart):
        """Test rendering timeline."""
        config = DashboardConfig()
        panel = AnalyticsPanel(config)

        # Method expects a dict with 'timeline' key
        results = {"timeline": {"2020": 30, "2021": 40, "2022": 30}}

        panel._render_timeline(results)
        mock_chart.assert_called_once()
        mock_info.assert_not_called()

    @patch("streamlit.plotly_chart")
    @patch("streamlit.info")
    @patch("plotly.express.pie")
    def test_render_distribution(self, mock_pie, mock_info, mock_chart):
        """Test rendering database distribution."""
        config = DashboardConfig()
        panel = AnalyticsPanel(config)

        # Mock pie chart creation
        mock_pie.return_value = MagicMock()

        # Method expects a dict with 'distribution' key
        results = {"distribution": {"pubmed": 60, "google_scholar": 40}}

        panel._render_database_distribution(results)
        mock_chart.assert_called_once()
        mock_info.assert_not_called()


class TestResultsPanel:
    """Test results panel."""

    @patch("streamlit.info")
    def test_render_empty(self, mock_info):
        """Test rendering empty results."""
        config = DashboardConfig()
        panel = ResultsPanel(config)

        panel.render([])
        mock_info.assert_called_once()

    @patch("streamlit.write")
    @patch("streamlit.expander")
    def test_render_with_results(self, mock_expander, mock_write):
        """Test rendering with results."""
        config = DashboardConfig()
        panel = ResultsPanel(config)

        results = [
            {
                "title": "Test Publication",
                "authors": ["Smith J", "Doe J"],
                "year": 2020,
                "citations": 50,
                "abstract": "Test abstract",
                "source": "pubmed",
                "url": "https://example.com",
            }
        ]

        mock_expander.return_value.__enter__ = MagicMock()
        mock_expander.return_value.__exit__ = MagicMock()

        panel.render(results)
        assert mock_write.call_count >= 1

    @patch("streamlit.markdown")
    @patch("streamlit.caption")
    @patch("streamlit.divider")
    @patch("streamlit.container")
    def test_render_missing_fields(self, mock_container, mock_divider, mock_caption, mock_markdown):
        """Test rendering with missing fields."""
        config = DashboardConfig()
        panel = ResultsPanel(config)

        # Mock container context manager
        mock_container.return_value.__enter__ = MagicMock()
        mock_container.return_value.__exit__ = MagicMock()

        results = [{"title": "Minimal Publication"}]

        panel.render(results)
        # Should at least render the title
        mock_markdown.assert_called()


class TestPanelIntegration:
    """Test panel integration."""

    def test_all_panels_have_render(self):
        """Test all panels have render method."""
        config = DashboardConfig()

        panels = [
            SearchPanel(config),
            VisualizationPanel(config),
            AnalyticsPanel(config),
            ResultsPanel(config),
        ]

        for panel in panels:
            assert hasattr(panel, "render")
            assert callable(panel.render)

    def test_config_sharing(self):
        """Test config is shared across panels."""
        config = DashboardConfig(app_title="Shared Config")

        panels = [
            SearchPanel(config),
            VisualizationPanel(config),
            AnalyticsPanel(config),
            ResultsPanel(config),
        ]

        for panel in panels:
            assert panel.config.app_title == "Shared Config"
