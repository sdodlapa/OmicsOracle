"""
Main dashboard application.

Streamlit-based web application for biomarker search and analysis.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, Optional

try:
    import streamlit as st
except ImportError:
    st = None

from omics_oracle_v2.lib.dashboard.components import (
    AnalyticsPanel,
    ResultsPanel,
    SearchPanel,
    VisualizationPanel,
)
from omics_oracle_v2.lib.dashboard.config import DashboardConfig
from omics_oracle_v2.lib.dashboard.preferences import PreferencesManager
from omics_oracle_v2.lib.dashboard.search_history import SearchHistoryManager, SearchRecord, SearchTemplate


class DashboardApp:
    """Main dashboard application."""

    def __init__(self, config: Optional[DashboardConfig] = None):
        """Initialize dashboard.

        Args:
            config: Dashboard configuration
        """
        if st is None:
            raise ImportError("Streamlit is required for dashboard")

        self.config = config or DashboardConfig()
        self.history_manager = SearchHistoryManager()
        self.preferences_manager = PreferencesManager()
        self._setup_page()
        self._init_session_state()

    def _setup_page(self) -> None:
        """Configure Streamlit page."""
        st.set_page_config(
            page_title=self.config.app_title,
            page_icon=self.config.app_icon,
            layout=self.config.layout,
            initial_sidebar_state=self.config.sidebar_state,
        )

        # Custom CSS
        st.markdown(
            """
            <style>
            .stButton button {
                width: 100%;
            }
            .metric-card {
                background-color: #f0f2f6;
                padding: 1rem;
                border-radius: 0.5rem;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

    def _init_session_state(self) -> None:
        """Initialize session state variables."""
        if "search_results" not in st.session_state:
            st.session_state.search_results = None
        if "current_query" not in st.session_state:
            st.session_state.current_query = ""
        if "search_history" not in st.session_state:
            st.session_state.search_history = []
        if "viz_data" not in st.session_state:
            st.session_state.viz_data = None
        if "preferences_loaded" not in st.session_state:
            st.session_state.preferences_loaded = False
        if "history_loaded" not in st.session_state:
            st.session_state.history_loaded = False

    def run(self) -> None:
        """Run the dashboard application."""
        # Header
        st.title(f"{self.config.app_icon} {self.config.app_title}")
        st.markdown("Advanced biomarker search and analysis platform")

        # Sidebar
        self._render_sidebar()

        # Main content
        self._render_main_content()

    def _render_sidebar(self) -> None:
        """Render sidebar with settings and info."""
        with st.sidebar:
            st.header("Settings")

            # Feature toggles
            st.subheader("Features")
            enable_viz = st.checkbox("Visualizations", value=self.config.enable_visualizations)
            enable_analytics = st.checkbox("Analytics", value=self.config.enable_analytics)
            enable_export = st.checkbox("Export", value=self.config.enable_export)

            # Update config
            self.config.enable_visualizations = enable_viz
            self.config.enable_analytics = enable_analytics
            self.config.enable_export = enable_export

            st.divider()

            # Search history
            st.subheader(":clock3: Search History")

            # Recent searches
            recent_queries = self.history_manager.get_recent_queries(limit=5)
            if recent_queries:
                st.caption("Recent searches:")
                for query in recent_queries:
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        if st.button(
                            f":mag: {query[:40]}..." if len(query) > 40 else f":mag: {query}",
                            key=f"history_{query}",
                            use_container_width=True,
                        ):
                            st.session_state.current_query = query
                            st.rerun()
                    with col2:
                        if st.button(
                            ":floppy_disk:",
                            key=f"save_{query}",
                            help="Save as template",
                        ):
                            st.session_state.save_template_query = query
                            st.rerun()

            # Saved templates
            templates = self.history_manager.get_templates()
            if templates:
                st.caption("Saved templates:")
                for template in templates[:3]:
                    if st.button(
                        f":bookmark: {template.name}",
                        key=f"template_{template.name}",
                        use_container_width=True,
                        help=template.description,
                    ):
                        st.session_state.current_query = template.query
                        st.rerun()

            # History stats
            stats = self.history_manager.get_stats()
            if stats["total_searches"] > 0:
                st.caption("Statistics:")
                st.metric("Total Searches", stats["total_searches"])

            st.divider()

            # Info
            st.subheader("About")
            st.info(
                """
                OmicsOracle Dashboard provides:
                - Multi-database search
                - LLM-powered analysis
                - Interactive visualizations
                - Citation network analysis
                - Statistical reports
                """
            )

    def _render_main_content(self) -> None:
        """Render main dashboard content."""
        # Search panel
        if self.config.enable_search:
            search_panel = SearchPanel(self.config)
            search_params = search_panel.render()

            # Execute search
            if search_params["search_clicked"] and search_params["query"]:
                self._execute_search(search_params)

        # Results display
        if st.session_state.search_results:
            # Tabs for different views
            tab_names = ["Results"]
            if self.config.enable_visualizations:
                tab_names.append("Visualizations")
            if self.config.enable_analytics:
                tab_names.append("Analytics")

            tabs = st.tabs(tab_names)

            # Results tab
            with tabs[0]:
                results_panel = ResultsPanel(self.config)
                results_panel.render(st.session_state.search_results.get("publications", []))

            # Visualization tab
            if self.config.enable_visualizations and len(tabs) > 1:
                with tabs[1]:
                    viz_panel = VisualizationPanel(self.config)
                    viz_panel.render(st.session_state.search_results)

            # Analytics tab
            if self.config.enable_analytics and len(tabs) > 2:
                with tabs[-1]:
                    analytics_panel = AnalyticsPanel(self.config)
                    analytics_panel.render(st.session_state.search_results)

            # Export button
            if self.config.enable_export:
                st.divider()
                col1, col2, col3 = st.columns([1, 1, 2])
                with col1:
                    if st.button("Export JSON"):
                        self._export_results("json")
                with col2:
                    if st.button("Export CSV"):
                        self._export_results("csv")

        # Template save dialog
        if "save_template_query" in st.session_state:
            self._show_template_dialog(st.session_state.save_template_query)

    def _show_template_dialog(self, query: str) -> None:
        """Show dialog to save search as template.

        Args:
            query: Query to save as template
        """
        with st.form("save_template_form"):
            st.subheader("Save as Template")

            name = st.text_input(
                "Template Name", value=f"Template_{len(self.history_manager.get_templates()) + 1}"
            )
            description = st.text_area("Description", value=f"Search for: {query}")
            tags_input = st.text_input("Tags (comma-separated)", value="")

            submitted = st.form_submit_button("Save Template")

            if submitted and name:
                tags = [tag.strip() for tag in tags_input.split(",") if tag.strip()]

                template = SearchTemplate(
                    name=name,
                    description=description,
                    query=query,
                    databases=["pubmed"],
                    year_range=(2000, 2024),
                    max_results=100,
                    tags=tags,
                )

                self.history_manager.save_template(template)
                st.success(f"Template '{name}' saved!")
                if "save_template_query" in st.session_state:
                    del st.session_state.save_template_query

    def _execute_search(self, params: Dict[str, Any]) -> None:
        """Execute search with given parameters.

        Args:
            params: Search parameters
        """
        query = params["query"]

        # Add to session history
        if query not in st.session_state.search_history:
            st.session_state.search_history.append(query)

        # Show progress
        with st.spinner(f"Searching for: {query}..."):
            try:
                # Import search functionality
                from omics_oracle_v2.lib.publications.config import PublicationSearchConfig
                from omics_oracle_v2.lib.publications.pipeline import PublicationSearchPipeline

                # Create pipeline config
                pipeline_config = PublicationSearchConfig(
                    enable_pubmed="pubmed" in params["databases"],
                    enable_scholar="scholar" in params["databases"],
                    enable_citations=params.get("use_llm", False),
                    max_total_results=params["max_results"],
                )

                # Execute search
                pipeline = PublicationSearchPipeline(pipeline_config)

                # Run async search
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                search_start = datetime.now()
                results = loop.run_until_complete(
                    pipeline.search(
                        query=query,
                        sources=params["databases"],
                        max_results=params["max_results"],
                    )
                )
                search_end = datetime.now()
                execution_time = (search_end - search_start).total_seconds()

                # Save to history manager
                record = SearchRecord(
                    query=query,
                    databases=params["databases"],
                    year_range=params.get("year_range", (2000, 2024)),
                    max_results=params["max_results"],
                    timestamp=search_start.isoformat(),
                    result_count=len(results),
                    execution_time=execution_time,
                    use_llm=params.get("use_llm", False),
                )
                self.history_manager.add_search(record)

                # Process results
                st.session_state.search_results = self._process_results(results, params)
                st.session_state.current_query = query

                st.success(f"Found {len(results)} results in {execution_time:.2f}s!")

            except Exception as e:
                st.error(f"Search failed: {str(e)}")
                st.session_state.search_results = None

    def _process_results(self, results: list, params: Dict[str, Any]) -> Dict[str, Any]:
        """Process search results for visualization.

        Args:
            results: Raw search results
            params: Search parameters

        Returns:
            Processed results dictionary
        """
        # Basic processing
        processed = {
            "publications": results,
            "total_results": len(results),
            "query": params["query"],
            "databases_searched": params["databases"],
        }

        # Calculate metrics
        if results:
            total_citations = sum(r.get("citations", 0) for r in results)
            years = [r.get("year") for r in results if r.get("year")]
            avg_year = sum(years) / len(years) if years else 0

            processed.update(
                {
                    "total_citations": total_citations,
                    "avg_publication_year": avg_year,
                }
            )

            # Build visualization data
            processed.update(
                {
                    "network_data": self._build_network_data(results),
                    "trend_data": self._build_trend_data(results),
                    "statistics_data": self._build_statistics_data(results),
                    "summary_stats": self._build_summary_stats(results),
                    "publication_timeline": self._build_timeline(results),
                    "database_distribution": self._build_distribution(results),
                    "top_biomarkers": self._extract_top_biomarkers(results),
                }
            )

        return processed

    def _build_network_data(self, results: list) -> Dict[str, Any]:
        """Build citation network data."""
        nodes = []
        edges = []

        for pub in results[:50]:  # Limit for performance
            nodes.append(
                {
                    "id": pub.get("id", pub.get("title", "")),
                    "label": pub.get("title", "")[:50],
                    "citations": pub.get("citations", 0),
                    "year": pub.get("year"),
                }
            )

        return {"nodes": nodes, "edges": edges}

    def _build_trend_data(self, results: list) -> Dict[str, Any]:
        """Build temporal trend data."""
        timeline = {}
        for pub in results:
            year = pub.get("year")
            if year:
                timeline[year] = timeline.get(year, 0) + 1

        dates = sorted(timeline.keys())
        return {
            "dates": dates,
            "counts": [timeline[d] for d in dates],
            "title": "Publication Timeline",
        }

    def _build_statistics_data(self, results: list) -> Dict[str, Any]:
        """Build statistical distribution data."""
        citations = [r.get("citations", 0) for r in results if r.get("citations")]

        return {
            "distribution": {"values": citations, "name": "Citation Count"},
            "title": "Citation Distribution",
            "xlabel": "Citations",
            "ylabel": "Frequency",
        }

    def _build_summary_stats(self, results: list) -> Dict[str, Any]:
        """Build summary statistics."""
        # Citation distribution by source
        citation_dist = {}
        for pub in results[:10]:
            title = pub.get("title", "Unknown")[:30]
            citation_dist[title] = pub.get("citations", 0)

        # Usage types (simplified)
        usage_types = {"Diagnostic": 0, "Prognostic": 0, "Therapeutic": 0, "Research": 0}
        for pub in results:
            # Simple keyword matching
            text = (pub.get("title", "") + " " + pub.get("abstract", "")).lower()
            if "diagnostic" in text:
                usage_types["Diagnostic"] += 1
            elif "prognostic" in text:
                usage_types["Prognostic"] += 1
            elif "therapeutic" in text or "treatment" in text:
                usage_types["Therapeutic"] += 1
            else:
                usage_types["Research"] += 1

        # Timeline
        timeline = {}
        for pub in results:
            year = str(pub.get("year", "Unknown"))
            timeline[year] = timeline.get(year, 0) + 1

        return {
            "citation_distribution": citation_dist,
            "usage_types": usage_types,
            "temporal_trend": timeline,
        }

    def _build_timeline(self, results: list) -> Dict[str, int]:
        """Build publication timeline."""
        timeline = {}
        for pub in results:
            year = pub.get("year")
            if year:
                timeline[year] = timeline.get(year, 0) + 1
        return dict(sorted(timeline.items()))

    def _build_distribution(self, results: list) -> Dict[str, int]:
        """Build database distribution."""
        distribution = {}
        for pub in results:
            source = pub.get("source", "Unknown")
            distribution[source] = distribution.get(source, 0) + 1
        return distribution

    def _extract_top_biomarkers(self, results: list) -> list:
        """Extract top biomarkers from results."""
        # Simplified extraction
        biomarkers = []
        for pub in results[:10]:
            biomarkers.append(
                {
                    "Biomarker": pub.get("title", "")[:50],
                    "Citations": pub.get("citations", 0),
                    "Year": pub.get("year", "N/A"),
                    "Source": pub.get("source", "Unknown"),
                }
            )
        return biomarkers

    def _export_results(self, format: str) -> None:
        """Export results in specified format.

        Args:
            format: Export format (json, csv)
        """
        import json
        from datetime import datetime

        if not st.session_state.search_results:
            st.warning("No results to export")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"omicsoracle_results_{timestamp}.{format}"

        if format == "json":
            data = json.dumps(st.session_state.search_results, indent=2)
            st.download_button(
                "Download JSON",
                data=data,
                file_name=filename,
                mime="application/json",
            )
        elif format == "csv":
            import pandas as pd

            df = pd.DataFrame(st.session_state.search_results.get("publications", []))
            csv = df.to_csv(index=False)
            st.download_button("Download CSV", data=csv, file_name=filename, mime="text/csv")


def main():
    """Main entry point for dashboard."""
    app = DashboardApp()
    app.run()


if __name__ == "__main__":
    main()
