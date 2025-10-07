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
            key="search_query_input",
        )

        col1, col2 = st.columns(2)

        with col1:
            # Database selection
            databases = st.multiselect(
                "Databases",
                self.config.default_databases,
                default=self.config.default_databases,
                help="Select databases to search",
                key="search_databases",
            )

        with col2:
            # Year range
            year_range = st.slider(
                "Year Range",
                2000,
                2025,
                (2015, 2024),
                help="Filter publications by year",
                key="search_year_range",
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
                    key="search_max_results",
                )

            with col4:
                enable_llm = st.checkbox(
                    "Enable LLM Analysis",
                    value=False,
                    disabled=not self.config.enable_llm_analysis,
                    key="search_enable_llm",
                )

        # Search button
        search_clicked = st.button(
            ":mag: Search", type="primary", use_container_width=True, key="search_button"
        )

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
            "Biomarker Heatmap",
            "Research Flow (Sankey)",
            "Abstract Word Cloud",
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
            key="viz_type_selector",
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
        elif viz_type == "Biomarker Heatmap":
            self._render_heatmap(results)
        elif viz_type == "Research Flow (Sankey)":
            self._render_sankey(results)
        elif viz_type == "Abstract Word Cloud":
            self._render_wordcloud(results)

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

    def _render_heatmap(self, results: Dict[str, Any]) -> None:
        """Render biomarker correlation heatmap."""
        with st.spinner("Generating biomarker heatmap..."):
            try:
                import numpy as np
                import plotly.graph_objects as go

                # Extract biomarkers and publications
                publications = results.get("publications", [])
                if not publications:
                    st.warning("No data available for heatmap")
                    return

                # Build biomarker co-occurrence matrix
                biomarkers = set()
                for pub in publications:
                    biomarkers.update(pub.get("biomarkers", []))

                biomarker_list = sorted(list(biomarkers))[:20]  # Limit to top 20
                n = len(biomarker_list)

                # Create co-occurrence matrix
                matrix = np.zeros((n, n))
                for pub in publications:
                    pub_biomarkers = pub.get("biomarkers", [])
                    for i, bio1 in enumerate(biomarker_list):
                        if bio1 in pub_biomarkers:
                            for j, bio2 in enumerate(biomarker_list):
                                if bio2 in pub_biomarkers:
                                    matrix[i][j] += 1

                # Create heatmap
                fig = go.Figure(
                    data=go.Heatmap(
                        z=matrix,
                        x=biomarker_list,
                        y=biomarker_list,
                        colorscale="Blues",
                        hoverongaps=False,
                        hovertemplate="<b>%{x}</b> & <b>%{y}</b><br>Co-occurrences: %{z}<extra></extra>",
                    )
                )

                fig.update_layout(
                    title="Biomarker Co-occurrence Heatmap",
                    xaxis_title="Biomarkers",
                    yaxis_title="Biomarkers",
                    height=600,
                )

                st.plotly_chart(fig, use_container_width=True)

                # Add filter controls
                st.caption("Filter by minimum co-occurrences:")
                st.slider("Minimum", 1, 10, 2, key="heatmap_filter")

            except Exception as e:
                st.error(f"Error generating heatmap: {str(e)}")

    def _render_sankey(self, results: Dict[str, Any]) -> None:
        """Render research flow Sankey diagram."""
        with st.spinner("Generating research flow diagram..."):
            try:
                import plotly.graph_objects as go

                publications = results.get("publications", [])
                if not publications:
                    st.warning("No data available for Sankey diagram")
                    return

                # Build flow data: Year -> Database -> Biomarker
                nodes = []
                node_dict = {}
                links = {"source": [], "target": [], "value": []}

                def get_node_index(label, category):
                    key = f"{category}:{label}"
                    if key not in node_dict:
                        node_dict[key] = len(nodes)
                        nodes.append({"label": label, "category": category})
                    return node_dict[key]

                # Process publications
                for pub in publications[:50]:  # Limit for clarity
                    year = pub.get("year", "Unknown")
                    source_db = pub.get("source", "Unknown")
                    biomarkers = pub.get("biomarkers", [])

                    year_idx = get_node_index(str(year), "year")
                    db_idx = get_node_index(source_db, "database")

                    # Year -> Database
                    links["source"].append(year_idx)
                    links["target"].append(db_idx)
                    links["value"].append(1)

                    # Database -> Biomarkers
                    for biomarker in biomarkers[:3]:  # Top 3 biomarkers
                        bio_idx = get_node_index(biomarker, "biomarker")
                        links["source"].append(db_idx)
                        links["target"].append(bio_idx)
                        links["value"].append(1)

                # Create Sankey diagram
                fig = go.Figure(
                    data=[
                        go.Sankey(
                            node=dict(
                                pad=15,
                                thickness=20,
                                line=dict(color="black", width=0.5),
                                label=[n["label"] for n in nodes],
                                color=[
                                    "#1f77b4"
                                    if n["category"] == "year"
                                    else "#ff7f0e"
                                    if n["category"] == "database"
                                    else "#2ca02c"
                                    for n in nodes
                                ],
                            ),
                            link=dict(source=links["source"], target=links["target"], value=links["value"]),
                        )
                    ]
                )

                fig.update_layout(
                    title="Research Flow: Year -> Database -> Biomarker",
                    font_size=12,
                    height=600,
                )

                st.plotly_chart(fig, use_container_width=True)

            except Exception as e:
                st.error(f"Error generating Sankey diagram: {str(e)}")

    def _render_wordcloud(self, results: Dict[str, Any]) -> None:
        """Render word cloud from abstracts."""
        with st.spinner("Generating word cloud..."):
            try:
                publications = results.get("publications", [])
                if not publications:
                    st.warning("No data available for word cloud")
                    return

                # Combine all abstracts
                text = " ".join([pub.get("abstract", "") for pub in publications])

                if not text.strip():
                    st.warning("No abstract text available")
                    return

                # Try to use wordcloud library
                try:
                    import matplotlib.pyplot as plt
                    from wordcloud import WordCloud

                    # Create word cloud
                    wordcloud = WordCloud(
                        width=800,
                        height=400,
                        background_color="white",
                        colormap="viridis",
                        stopwords=set(
                            [
                                "the",
                                "a",
                                "an",
                                "and",
                                "or",
                                "but",
                                "in",
                                "on",
                                "at",
                                "to",
                                "for",
                                "of",
                                "with",
                                "by",
                                "from",
                                "as",
                                "is",
                                "was",
                                "are",
                                "were",
                                "been",
                                "be",
                                "have",
                                "has",
                                "had",
                                "do",
                                "does",
                                "did",
                            ]
                        ),
                    ).generate(text)

                    # Display
                    fig, ax = plt.subplots(figsize=(10, 5))
                    ax.imshow(wordcloud, interpolation="bilinear")
                    ax.axis("off")
                    st.pyplot(fig)

                    # Add filter controls
                    st.caption("Common terms in abstracts")

                except ImportError:
                    # Fallback: simple word frequency chart
                    from collections import Counter

                    import plotly.express as px

                    words = text.lower().split()
                    # Filter short words and common terms
                    words = [
                        w
                        for w in words
                        if len(w) > 4
                        and w
                        not in [
                            "these",
                            "their",
                            "there",
                            "which",
                            "could",
                            "would",
                            "should",
                        ]
                    ]

                    word_freq = Counter(words).most_common(30)

                    fig = px.bar(
                        x=[w[0] for w in word_freq],
                        y=[w[1] for w in word_freq],
                        labels={"x": "Word", "y": "Frequency"},
                        title="Top 30 Words in Abstracts",
                    )

                    st.plotly_chart(fig, use_container_width=True)
                    st.info("Install wordcloud package for enhanced visualization: pip install wordcloud")

            except Exception as e:
                st.error(f"Error generating word cloud: {str(e)}")


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

                # Institutional Access (Week 4)
                if result.get("has_access"):
                    access_status = result.get("access_status", {})
                    access_url = result.get("access_url")

                    # Show access status badges
                    access_col1, access_col2 = st.columns([1, 3])

                    with access_col1:
                        if access_status.get("unpaywall"):
                            st.success("✅ Open Access")
                        elif access_status.get("vpn"):
                            st.info("🔐 VPN Required")
                        elif access_status.get("ezproxy"):
                            st.info("🏛️ Institutional")

                    with access_col2:
                        if access_url:
                            # Different message for VPN vs EZProxy
                            if access_status.get("vpn"):
                                st.markdown(
                                    f"**[📥 Access via GT Library]({access_url})**",
                                    help="Connect to GT VPN first (vpn.gatech.edu), then click to access",
                                )
                            else:
                                st.markdown(
                                    f"**[📥 Access via Georgia Tech Library]({access_url})**",
                                    help="Click to access through institutional subscription",
                                )

                # Source link (fallback)
                elif "url" in result:
                    st.caption(f"[View Source]({result['url']})")

                st.divider()
