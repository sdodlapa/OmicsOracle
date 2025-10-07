"""
Statistical visualization components.

Creates distribution charts, correlation plots, and statistical summaries
for biomarker analysis.
"""

from typing import Any, Dict, List, Optional

import plotly.graph_objects as go

from omics_oracle_v2.lib.visualizations import (
    BaseVisualization,
    ColorSchemes,
    ExportOptions,
    VisualizationConfig,
    create_output_directory,
)


class StatisticalVisualizer(BaseVisualization):
    """Visualize statistical distributions and correlations."""

    def create(
        self,
        data: Dict[str, Any],
        chart_type: str = "auto",
        show_statistics: bool = True,
    ) -> go.Figure:
        """Create statistical visualization.

        Args:
            data: Statistical data (distributions, correlations, etc.)
            chart_type: Type of chart (auto, histogram, box, violin, pie, heatmap)
            show_statistics: Show statistical annotations

        Returns:
            Plotly figure object
        """
        self.data = data

        # Auto-detect chart type based on data structure
        if chart_type == "auto":
            chart_type = self._detect_chart_type(data)

        # Create appropriate visualization
        if chart_type == "histogram":
            self.figure = self._create_histogram(data, show_statistics)
        elif chart_type == "box":
            self.figure = self._create_box_plot(data, show_statistics)
        elif chart_type == "violin":
            self.figure = self._create_violin_plot(data, show_statistics)
        elif chart_type == "pie":
            self.figure = self._create_pie_chart(data, show_statistics)
        elif chart_type == "heatmap":
            self.figure = self._create_heatmap(data, show_statistics)
        elif chart_type == "scatter":
            self.figure = self._create_scatter_matrix(data, show_statistics)
        else:
            raise ValueError(f"Unsupported chart type: {chart_type}")

        return self.figure

    def _detect_chart_type(self, data: Dict[str, Any]) -> str:
        """Auto-detect appropriate chart type from data structure."""
        if "distribution" in data or "values" in data:
            return "histogram"
        elif "categories" in data and "values" in data:
            return "pie"
        elif "correlation_matrix" in data or "matrix" in data:
            return "heatmap"
        elif "groups" in data:
            return "box"
        else:
            return "histogram"

    def _create_histogram(self, data: Dict[str, Any], show_statistics: bool) -> go.Figure:
        """Create histogram with distribution."""
        fig = go.Figure()

        colors = ColorSchemes.get_scheme(self.config.color_scheme)

        if "distribution" in data:
            dist_data = data["distribution"]
            values = dist_data.get("values", [])
            name = dist_data.get("name", "Distribution")

            fig.add_trace(
                go.Histogram(
                    x=values,
                    name=name,
                    marker_color=colors["primary"],
                    nbinsx=30,
                    hovertemplate="Range: %{x}<br>Count: %{y}<extra></extra>",
                )
            )

            # Add statistics annotations
            if show_statistics and values:
                import numpy as np

                mean = np.mean(values)
                median = np.median(values)

                fig.add_vline(
                    x=mean,
                    line_dash="dash",
                    line_color=colors["danger"],
                    annotation_text=f"Mean: {mean:.2f}",
                    annotation_position="top",
                )

                fig.add_vline(
                    x=median,
                    line_dash="dot",
                    line_color=colors["success"],
                    annotation_text=f"Median: {median:.2f}",
                    annotation_position="bottom",
                )

        fig.update_layout(
            title={
                "text": data.get("title", "Distribution"),
                "x": 0.5,
                "xanchor": "center",
                "font": {"size": 20, "family": self.config.font_family},
            },
            xaxis_title=data.get("xlabel", "Value"),
            yaxis_title=data.get("ylabel", "Frequency"),
            width=self.config.width,
            height=self.config.height,
            template=self.config.theme,
            showlegend=self.config.show_legend,
        )

        return fig

    def _create_box_plot(self, data: Dict[str, Any], show_statistics: bool) -> go.Figure:
        """Create box plot for comparing distributions."""
        fig = go.Figure()

        colors = ColorSchemes.get_scheme(self.config.color_scheme)
        color_list = list(colors.values())

        groups = data.get("groups", {})

        for idx, (group_name, values) in enumerate(groups.items()):
            fig.add_trace(
                go.Box(
                    y=values,
                    name=group_name,
                    marker_color=color_list[idx % len(color_list)],
                    boxmean="sd" if show_statistics else False,
                    hovertemplate=f"<b>{group_name}</b><br>" + "Value: %{y}<br>" + "<extra></extra>",
                )
            )

        fig.update_layout(
            title={
                "text": data.get("title", "Distribution Comparison"),
                "x": 0.5,
                "xanchor": "center",
                "font": {"size": 20, "family": self.config.font_family},
            },
            xaxis_title=data.get("xlabel", "Group"),
            yaxis_title=data.get("ylabel", "Value"),
            width=self.config.width,
            height=self.config.height,
            template=self.config.theme,
            showlegend=self.config.show_legend,
        )

        return fig

    def _create_violin_plot(self, data: Dict[str, Any], show_statistics: bool) -> go.Figure:
        """Create violin plot for distribution visualization."""
        fig = go.Figure()

        colors = ColorSchemes.get_scheme(self.config.color_scheme)
        color_list = list(colors.values())

        groups = data.get("groups", {})

        for idx, (group_name, values) in enumerate(groups.items()):
            fig.add_trace(
                go.Violin(
                    y=values,
                    name=group_name,
                    box_visible=show_statistics,
                    meanline_visible=show_statistics,
                    fillcolor=color_list[idx % len(color_list)],
                    opacity=0.6,
                    hovertemplate=f"<b>{group_name}</b><br>" + "Value: %{y}<br>" + "<extra></extra>",
                )
            )

        fig.update_layout(
            title={
                "text": data.get("title", "Distribution Violin Plot"),
                "x": 0.5,
                "xanchor": "center",
                "font": {"size": 20, "family": self.config.font_family},
            },
            xaxis_title=data.get("xlabel", "Group"),
            yaxis_title=data.get("ylabel", "Value"),
            width=self.config.width,
            height=self.config.height,
            template=self.config.theme,
            showlegend=self.config.show_legend,
        )

        return fig

    def _create_pie_chart(self, data: Dict[str, Any], show_statistics: bool) -> go.Figure:
        """Create pie chart for categorical distribution."""
        fig = go.Figure()

        colors = ColorSchemes.get_scheme(self.config.color_scheme)

        categories = data.get("categories", [])
        values = data.get("values", [])

        # Calculate percentages if showing statistics
        if show_statistics:
            total = sum(values)
            text_info = [f"{cat}<br>{val} ({val/total*100:.1f}%)" for cat, val in zip(categories, values)]
        else:
            text_info = categories

        fig.add_trace(
            go.Pie(
                labels=categories,
                values=values,
                text=text_info,
                textposition="auto",
                hovertemplate="<b>%{label}</b><br>"
                + "Count: %{value}<br>"
                + "Percentage: %{percent}<br>"
                + "<extra></extra>",
                marker=dict(colors=[colors.get(cat.lower(), colors["primary"]) for cat in categories]),
            )
        )

        fig.update_layout(
            title={
                "text": data.get("title", "Category Distribution"),
                "x": 0.5,
                "xanchor": "center",
                "font": {"size": 20, "family": self.config.font_family},
            },
            width=self.config.width,
            height=self.config.height,
            template=self.config.theme,
            showlegend=self.config.show_legend,
        )

        return fig

    def _create_heatmap(self, data: Dict[str, Any], show_statistics: bool) -> go.Figure:
        """Create correlation heatmap."""
        fig = go.Figure()

        matrix = data.get("correlation_matrix") or data.get("matrix", [])
        labels = data.get("labels", [f"Var{i}" for i in range(len(matrix))])

        # Create annotations for cell values
        annotations = []
        if show_statistics:
            for i, row in enumerate(matrix):
                for j, val in enumerate(row):
                    annotations.append(
                        dict(
                            x=j,
                            y=i,
                            text=f"{val:.2f}",
                            showarrow=False,
                            font=dict(color="white" if abs(val) > 0.5 else "black"),
                        )
                    )

        fig.add_trace(
            go.Heatmap(
                z=matrix,
                x=labels,
                y=labels,
                colorscale="RdBu_r",
                zmid=0,
                text=matrix,
                texttemplate="%{text:.2f}" if show_statistics else None,
                textfont={"size": 10},
                hovertemplate="<b>%{x} vs %{y}</b><br>" + "Correlation: %{z:.3f}<br>" + "<extra></extra>",
            )
        )

        fig.update_layout(
            title={
                "text": data.get("title", "Correlation Matrix"),
                "x": 0.5,
                "xanchor": "center",
                "font": {"size": 20, "family": self.config.font_family},
            },
            width=self.config.width,
            height=self.config.height,
            template=self.config.theme,
            annotations=annotations if show_statistics else None,
        )

        return fig

    def _create_scatter_matrix(self, data: Dict[str, Any], show_statistics: bool) -> go.Figure:
        """Create scatter plot matrix for multivariate analysis."""
        import pandas as pd

        df = pd.DataFrame(data.get("data", {}))
        dimensions = data.get("dimensions", df.columns.tolist())

        fig = go.Figure(
            data=go.Splom(
                dimensions=[dict(label=dim, values=df[dim]) for dim in dimensions],
                showupperhalf=False,
                marker=dict(
                    size=5,
                    color=df.index,
                    colorscale="Viridis",
                    showscale=False,
                ),
                diagonal_visible=show_statistics,
            )
        )

        fig.update_layout(
            title={
                "text": data.get("title", "Scatter Matrix"),
                "x": 0.5,
                "xanchor": "center",
                "font": {"size": 20, "family": self.config.font_family},
            },
            width=self.config.width,
            height=self.config.height,
            template=self.config.theme,
            showlegend=False,
        )

        return fig

    def update(
        self,
        title: Optional[str] = None,
        chart_type: Optional[str] = None,
        **kwargs,
    ) -> None:
        """Update visualization properties."""
        if self.figure is None:
            raise ValueError("No figure to update. Call create() first.")

        if title:
            self.figure.update_layout(title=title)

        if chart_type and self.data:
            # Recreate with new chart type
            self.create(self.data, chart_type=chart_type)

        if kwargs:
            self.figure.update_layout(**kwargs)

    def _export_html(self, options: ExportOptions) -> str:
        """Export as interactive HTML."""
        output_dir = create_output_directory()
        filename = options.filename or "statistical_chart.html"
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
        filename = options.filename or f"statistical_chart.{options.format}"
        path = output_dir / filename

        width = options.width or self.config.width
        height = options.height or self.config.height

        self.figure.write_image(
            str(path),
            format=options.format,
            width=width,
            height=height,
            scale=options.scale,
        )

        return str(path)

    def _serialize_data(self) -> Dict:
        """Serialize statistical data for JSON export."""
        return self.data if self.data else {}

    def _show_figure(self) -> None:
        """Show the figure interactively."""
        self.figure.show()


def create_biomarker_distribution(
    biomarker_data: Dict[str, List[float]],
    config: Optional[VisualizationConfig] = None,
    chart_type: str = "box",
    export_path: Optional[str] = None,
) -> go.Figure:
    """Convenience function for biomarker distribution visualization.

    Args:
        biomarker_data: Dictionary mapping biomarker names to value lists
        config: Visualization configuration
        chart_type: Type of chart (box, violin, histogram)
        export_path: Optional path to export HTML

    Returns:
        Plotly figure
    """
    viz = StatisticalVisualizer(config)
    fig = viz.create(
        {
            "groups": biomarker_data,
            "title": "Biomarker Distribution",
            "xlabel": "Biomarker",
            "ylabel": "Expression Level",
        },
        chart_type=chart_type,
    )

    if export_path:
        options = ExportOptions(format="html", filename=export_path)
        viz.export(options)

    return fig


def create_usage_type_pie(
    usage_counts: Dict[str, int],
    config: Optional[VisualizationConfig] = None,
    export_path: Optional[str] = None,
) -> go.Figure:
    """Convenience function for usage type pie chart.

    Args:
        usage_counts: Dictionary mapping usage types to counts
        config: Visualization configuration
        export_path: Optional path to export HTML

    Returns:
        Plotly figure
    """
    viz = StatisticalVisualizer(config)
    fig = viz.create(
        {
            "categories": list(usage_counts.keys()),
            "values": list(usage_counts.values()),
            "title": "Usage Type Distribution",
        },
        chart_type="pie",
    )

    if export_path:
        options = ExportOptions(format="html", filename=export_path)
        viz.export(options)

    return fig


def create_correlation_heatmap(
    correlation_matrix: List[List[float]],
    labels: List[str],
    config: Optional[VisualizationConfig] = None,
    export_path: Optional[str] = None,
) -> go.Figure:
    """Convenience function for correlation heatmap.

    Args:
        correlation_matrix: 2D correlation matrix
        labels: Variable labels
        config: Visualization configuration
        export_path: Optional path to export HTML

    Returns:
        Plotly figure
    """
    viz = StatisticalVisualizer(config)
    fig = viz.create(
        {
            "correlation_matrix": correlation_matrix,
            "labels": labels,
            "title": "Biomarker Correlation Matrix",
        },
        chart_type="heatmap",
    )

    if export_path:
        options = ExportOptions(format="html", filename=export_path)
        viz.export(options)

    return fig
