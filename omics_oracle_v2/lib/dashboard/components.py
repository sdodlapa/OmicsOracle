"""
Dashboard UI components.

Provides reusable panels for search, visualization, and analytics.
"""

from typing import Any, Dict, List, Optional

try:
    import streamlit as st
except ImportError:
    st = None

from .config import DashboardConfig


class BasePanel:
    """Base class for dashboard panels."""

    def __init__(self, config: DashboardConfig):
        """Initialize panel with configuration.

        Args:
            config: Dashboard configuration
        """
        self.config = config

    def render(self) -> None:
        """Render panel content. Override in subclasses."""
        raise NotImplementedError


class SearchPanel(BasePanel):
    """Search interface panel."""

    def __init__(self, config: DashboardConfig):
        """Initialize search panel."""
        super().__init__(config)

    def render(self) -> Dict[str, Any]:
        """Render search panel.

        Returns:
            Search parameters
        """
        if st is None:
            raise ImportError("Streamlit is required for dashboard")

        st.subheader(":mag: Search")

        # Query input
        query = st.text_input(
            "Search Query",
            placeholder="Enter biomarker search query...",
            help="Search for biomarkers, publications, or research topics",
        )

        col1, col2 = st.columns(2)

        with col1:
            # Database selection
            databases = st.multiselect(
                "Databases",
                self.config.default_databases,
                default=self.config.default_databases,
                help="Select databases to search",
            )

        with col2:
            # Year range
            year_range = st.slider(
                "Year Range",
                2000,
                2025,
                (2015, 2024),
                help="Filter publications by year",
            )

        # Advanced options
        with st.expander("Advanced Options"):
            col3, col4 = st.columns(2)

            with col3:
                max_results = st.number_input(
                    "Max Results",
                    min_value=10,
                    max_value=self.config.max_results,
                    value=50,
                    step=10,
                )

            with col4:
                enable_llm = st.checkbox(
                    "Enable LLM Analysis",
                    value=False,
                    disabled=not self.config.enable_llm_analysis,
                )

        # Search button
        search_clicked = st.button(":mag: Search", type="primary", use_container_width=True)

        return {
            "query": query,
            "databases": databases,
            "year_range": year_range,
            "max_results": max_results,
            "use_llm": enable_llm,
            "search_clicked": search_clicked,
        }


class VisualizationPanel(BasePanel):
    """Visualization display panel."""

    def __init__(self, config: DashboardConfig):
        """Initialize visualization panel."""
        super().__init__(config)
        self.viz_types = [
            "Citation Network",
            "Temporal Trends",
            "Statistical Distribution",
            "Multi-Panel Report",
        ]

    def render(self, results: Optional[Dict[str, Any]] = None) -> None:
        """Render visualization panel.

        Args:
            results: Search results to visualize
        """
        if st is None:
            raise ImportError("Streamlit is required for dashboard")

        st.subheader(":bar_chart: Visualizations")

        if results is None or not results:
            st.info("Run a search to generate visualizations")
            return

        # Visualization type selector
        viz_type = st.selectbox(
            "Visualization Type",
            self.viz_types,
        )

        # Render based on type
        if viz_type == "Citation Network":
            self._render_network(results)
        elif viz_type == "Temporal Trends":
            self._render_trends(results)
        elif viz_type == "Statistical Distribution":
            self._render_statistics(results)
        elif viz_type == "Multi-Panel Report":
            self._render_report(results)

    def _render_network(self, results: Dict[str, Any]) -> None:
        """Render citation network visualization."""
        with st.spinner("Generating citation network..."):
            # Import here to avoid circular dependency
            from omics_oracle_v2.lib.visualizations.network import visualize_knowledge_graph

            try:
                fig = visualize_knowledge_graph(results.get("network_data", {}))
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Error generating network: {str(e)}")

    def _render_trends(self, results: Dict[str, Any]) -> None:
        """Render temporal trend visualization."""
        with st.spinner("Generating temporal trends..."):
            from omics_oracle_v2.lib.visualizations.trends import TrendVisualizer

            try:
                viz = TrendVisualizer()
                fig = viz.create(results.get("trend_data", {}), chart_type="line")
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Error generating trends: {str(e)}")

    def _render_statistics(self, results: Dict[str, Any]) -> None:
        """Render statistical distribution."""
        with st.spinner("Generating statistical charts..."):
            from omics_oracle_v2.lib.visualizations.statistics import StatisticalVisualizer

            try:
                viz = StatisticalVisualizer()
                fig = viz.create(results.get("statistics_data", {}), chart_type="auto")
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Error generating statistics: {str(e)}")

    def _render_report(self, results: Dict[str, Any]) -> None:
        """Render multi-panel report."""
        with st.spinner("Generating report..."):
            from omics_oracle_v2.lib.visualizations.reports import create_executive_dashboard

            try:
                fig = create_executive_dashboard(results.get("summary_stats", {}))
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Error generating report: {str(e)}")


class AnalyticsPanel(BasePanel):
    """Analytics and metrics panel."""

    def __init__(self, config: DashboardConfig):
        """Initialize analytics panel."""
        super().__init__(config)

    def render(self, results: Optional[Dict[str, Any]] = None) -> None:
        """Render analytics panel.

        Args:
            results: Search results to analyze
        """
        if st is None:
            raise ImportError("Streamlit is required for dashboard")

        st.subheader(":chart_with_upwards_trend: Analytics")

        if results is None or not results:
            st.info("Run a search to view analytics")
            return

        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total = results.get("total_results", 0)
            st.metric("Total Results", total)

        with col2:
            citations = results.get("total_citations", 0)
            st.metric("Total Citations", citations)

        with col3:
            avg_year = results.get("avg_publication_year", 0)
            st.metric("Avg Year", f"{avg_year:.0f}" if avg_year else "N/A")

        with col4:
            databases = len(results.get("databases_searched", []))
            st.metric("Databases", databases)

        # Detailed analytics
        st.divider()

        tabs = st.tabs(["Top Biomarkers", "Publication Timeline", "Database Distribution"])

        with tabs[0]:
            self._render_top_biomarkers(results)

        with tabs[1]:
            self._render_timeline(results)

        with tabs[2]:
            self._render_database_distribution(results)

    def _render_top_biomarkers(self, results: Dict[str, Any]) -> None:
        """Render top biomarkers table."""
        biomarkers = results.get("top_biomarkers", [])

        if biomarkers:
            st.dataframe(
                biomarkers,
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No biomarker data available")

    def _render_timeline(self, results: Dict[str, Any]) -> None:
        """Render publication timeline."""
        timeline = results.get("timeline", {})

        if timeline:
            st.bar_chart(timeline)
        else:
            st.info("No timeline data available")

    def _render_database_distribution(self, results: Dict[str, Any]) -> None:
        """Render database distribution."""
        distribution = results.get("distribution", {})

        if distribution:
            import plotly.express as px

            fig = px.pie(
                values=list(distribution.values()),
                names=list(distribution.keys()),
                title="Database Distribution",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No distribution data available")


class ResultsPanel(BasePanel):
    """Search results display panel."""

    def __init__(self, config: DashboardConfig):
        """Initialize results panel."""
        super().__init__(config)

    def render(self, results: Optional[List[Dict[str, Any]]] = None) -> None:
        """Render results panel.

        Args:
            results: List of search results
        """
        if st is None:
            raise ImportError("Streamlit is required for dashboard")

        st.subheader(":page_facing_up: Search Results")

        if results is None or not results:
            st.info("No results to display")
            return

        # Results count
        st.caption(f"Showing {len(results)} results")

        # Display results
        for idx, result in enumerate(results, 1):
            with st.container():
                # Title
                title = result.get("title", "Untitled")
                st.markdown(f"**{idx}. {title}**")

                # Metadata
                col1, col2, col3 = st.columns([2, 1, 1])

                with col1:
                    authors = result.get("authors", [])
                    if authors:
                        st.caption(f"Authors: {', '.join(authors[:3])}")

                with col2:
                    year = result.get("year", "N/A")
                    st.caption(f"Year: {year}")

                with col3:
                    citations = result.get("citations", 0)
                    st.caption(f"Citations: {citations}")

                # Abstract
                if "abstract" in result:
                    with st.expander("Abstract"):
                        st.write(result["abstract"])

                # Source link
                if "url" in result:
                    st.caption(f"[View Source]({result['url']})")

                st.divider()
