"""
Citation network visualization.

Creates interactive network graphs showing citation relationships,
biomarker connections, and knowledge graphs.
"""

from typing import Any, Dict, List, Optional, Tuple

import networkx as nx
import plotly.graph_objects as go

from omics_oracle_v2.lib.visualizations import (
    BaseVisualization,
    ColorSchemes,
    ExportOptions,
    VisualizationConfig,
    create_output_directory,
)


class CitationNetworkVisualizer(BaseVisualization):
    """Visualize citation networks and knowledge graphs."""

    def create(
        self,
        graph_data: Dict[str, Any],
        layout: str = "spring",
        node_size_by: str = "citations",
        edge_color_by: str = "relationship",
    ) -> go.Figure:
        """Create interactive network visualization.

        Args:
            graph_data: Knowledge graph data from analysis
            layout: Layout algorithm (spring, circular, kamada_kawai)
            node_size_by: Node size metric (citations, connections, impact)
            edge_color_by: Edge color metric (relationship, strength, recency)

        Returns:
            Plotly figure object
        """
        self.data = graph_data

        # Create NetworkX graph
        G = self._build_networkx_graph(graph_data)

        # Calculate layout positions
        pos = self._calculate_layout(G, layout)

        # Create figure
        self.figure = self._create_plotly_figure(G, pos, node_size_by, edge_color_by)

        return self.figure

    def _build_networkx_graph(self, graph_data: Dict[str, Any]) -> nx.Graph:
        """Build NetworkX graph from knowledge graph data."""
        G = nx.Graph()

        # Add nodes
        for node in graph_data.get("nodes", []):
            G.add_node(
                node["id"],
                type=node.get("type", "unknown"),
                label=node.get("label", ""),
                citations=node.get("citations", 0),
                impact=node.get("impact", 0),
                metadata=node.get("metadata", {}),
            )

        # Add edges
        for edge in graph_data.get("edges", []):
            G.add_edge(
                edge["source"],
                edge["target"],
                relationship=edge.get("relationship", ""),
                strength=edge.get("strength", 1.0),
                metadata=edge.get("metadata", {}),
            )

        return G

    def _calculate_layout(self, G: nx.Graph, layout: str) -> Dict:
        """Calculate node positions using specified layout algorithm."""
        layout_funcs = {
            "spring": nx.spring_layout,
            "circular": nx.circular_layout,
            "kamada_kawai": nx.kamada_kawai_layout,
            "shell": nx.shell_layout,
        }

        layout_func = layout_funcs.get(layout, nx.spring_layout)

        # Only spring_layout accepts seed parameter
        if layout == "spring":
            return layout_func(G, seed=42)  # Seed for reproducibility
        else:
            return layout_func(G)

    def _create_plotly_figure(
        self,
        G: nx.Graph,
        pos: Dict,
        node_size_by: str,
        edge_color_by: str,
    ) -> go.Figure:
        """Create Plotly figure from NetworkX graph."""
        # Create edge traces
        edge_traces = self._create_edge_traces(G, pos, edge_color_by)

        # Create node trace
        node_trace = self._create_node_trace(G, pos, node_size_by)

        # Combine traces
        fig = go.Figure(data=edge_traces + [node_trace])

        # Update layout
        fig.update_layout(
            title={
                "text": "Citation Network",
                "x": 0.5,
                "xanchor": "center",
                "font": {"size": 20, "family": self.config.font_family},
            },
            showlegend=self.config.show_legend,
            hovermode="closest",
            width=self.config.width,
            height=self.config.height,
            template=self.config.theme,
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            margin=dict(b=20, l=20, r=20, t=60),
        )

        return fig

    def _create_edge_traces(self, G: nx.Graph, pos: Dict, color_by: str) -> List[go.Scatter]:
        """Create edge traces for the network."""
        # Group edges by relationship type for coloring
        edge_groups: Dict[str, List[Tuple]] = {}

        for edge in G.edges(data=True):
            source, target, data = edge
            relationship = data.get(color_by, "unknown")

            if relationship not in edge_groups:
                edge_groups[relationship] = []

            edge_groups[relationship].append((source, target, data))

        # Create trace for each group
        traces = []
        colors = ColorSchemes.get_scheme(self.config.color_scheme)
        color_list = list(colors.values())

        for idx, (relationship, edges) in enumerate(edge_groups.items()):
            edge_x = []
            edge_y = []

            for source, target, _ in edges:
                x0, y0 = pos[source]
                x1, y1 = pos[target]
                edge_x.extend([x0, x1, None])
                edge_y.extend([y0, y1, None])

            trace = go.Scatter(
                x=edge_x,
                y=edge_y,
                line=dict(width=1.5, color=color_list[idx % len(color_list)], dash="solid"),
                hoverinfo="none",
                mode="lines",
                name=relationship,
                showlegend=True,
            )
            traces.append(trace)

        return traces

    def _create_node_trace(self, G: nx.Graph, pos: Dict, size_by: str) -> go.Scatter:
        """Create node trace for the network."""
        node_x = []
        node_y = []
        node_text = []
        node_sizes = []
        node_colors = []

        colors = ColorSchemes.get_scheme(self.config.color_scheme)

        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)

            # Node data
            data = G.nodes[node]
            node_type = data.get("type", "unknown")
            label = data.get("label", str(node))

            # Size calculation
            size_value = data.get(size_by, 1)
            node_sizes.append(max(10, min(50, size_value * 5)))  # Scale and clamp

            # Color by type
            node_colors.append(colors.get(node_type, colors["primary"]))

            # Hover text
            hover_parts = [
                f"<b>{label}</b>",
                f"Type: {node_type}",
                f"Citations: {data.get('citations', 0)}",
                f"Connections: {G.degree(node)}",
            ]
            node_text.append("<br>".join(hover_parts))

        trace = go.Scatter(
            x=node_x,
            y=node_y,
            mode="markers+text",
            hovertext=node_text,
            hoverinfo="text",
            marker=dict(
                size=node_sizes,
                color=node_colors,
                line=dict(width=2, color="white"),
            ),
            text=[G.nodes[node].get("label", "")[:20] for node in G.nodes()],
            textposition="top center",
            textfont=dict(size=8, family=self.config.font_family),
            name="Nodes",
            showlegend=False,
        )

        return trace

    def update(
        self,
        title: Optional[str] = None,
        layout: Optional[str] = None,
        node_size_by: Optional[str] = None,
        **kwargs,
    ) -> None:
        """Update visualization properties."""
        if self.figure is None:
            raise ValueError("No figure to update. Call create() first.")

        if title:
            self.figure.update_layout(title=title)

        if layout and self.data:
            # Recreate with new layout
            self.create(self.data, layout=layout, node_size_by=node_size_by or "citations")

        # Update any other layout properties
        if kwargs:
            self.figure.update_layout(**kwargs)

    def _export_html(self, options: ExportOptions) -> str:
        """Export as interactive HTML."""
        output_dir = create_output_directory()
        filename = options.filename or "citation_network.html"
        path = output_dir / filename

        self.figure.write_html(
            str(path),
            include_plotlyjs="cdn",
            config={"displayModeBar": True, "responsive": True},
        )

        return str(path)

    def _export_image(self, options: ExportOptions) -> str:
        """Export as static image."""
        output_dir = create_output_directory()
        filename = options.filename or f"citation_network.{options.format}"
        path = output_dir / filename

        width = options.width or self.config.width
        height = options.height or self.config.height

        self.figure.write_image(
            str(path), format=options.format, width=width, height=height, scale=options.scale
        )

        return str(path)

    def _serialize_data(self) -> Dict:
        """Serialize graph data for JSON export."""
        return self.data if self.data else {}

    def _show_figure(self) -> None:
        """Show the figure interactively."""
        self.figure.show()

    def get_network_stats(self) -> Dict[str, Any]:
        """Get network statistics.

        Returns:
            Dictionary with network metrics
        """
        if not self.data:
            return {}

        nodes = self.data.get("nodes", [])
        edges = self.data.get("edges", [])

        G = self._build_networkx_graph(self.data)

        stats = {
            "num_nodes": len(nodes),
            "num_edges": len(edges),
            "density": nx.density(G),
            "avg_degree": sum(dict(G.degree()).values()) / len(G.nodes()) if G.nodes() else 0,
            "connected_components": nx.number_connected_components(G),
        }

        # Add centrality measures for top nodes
        if G.nodes():
            degree_centrality = nx.degree_centrality(G)
            top_nodes = sorted(degree_centrality.items(), key=lambda x: x[1], reverse=True)[:5]
            stats["top_nodes_by_centrality"] = [
                {"node": node, "centrality": cent} for node, cent in top_nodes
            ]

        return stats


def visualize_knowledge_graph(
    graph_data: Dict[str, Any],
    config: Optional[VisualizationConfig] = None,
    layout: str = "spring",
    export_path: Optional[str] = None,
) -> go.Figure:
    """Convenience function to visualize knowledge graph.

    Args:
        graph_data: Knowledge graph data
        config: Visualization configuration
        layout: Layout algorithm
        export_path: Optional path to export HTML

    Returns:
        Plotly figure
    """
    visualizer = CitationNetworkVisualizer(config)
    fig = visualizer.create(graph_data, layout=layout)

    if export_path:
        options = ExportOptions(format="html", filename=export_path)
        visualizer.export(options)

    return fig
