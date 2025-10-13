"""
Temporal trend visualization.

Creates interactive time-series charts showing citation trends,
usage evolution, and impact trajectories.
"""

from typing import Any, Dict, Optional

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from omics_oracle_v2.lib.visualizations import (
    BaseVisualization,
    ColorSchemes,
    ExportOptions,
    VisualizationConfig,
    create_output_directory,
)


class TrendVisualizer(BaseVisualization):
    """Visualize temporal trends and patterns."""

    def create(
        self,
        trend_data: Dict[str, Any],
        chart_type: str = "line",
        show_peaks: bool = True,
        show_forecast: bool = False,
    ) -> go.Figure:
        """Create temporal trend visualization.

        Args:
            trend_data: Trend analysis data
            chart_type: Type of chart (line, area, bar, scatter)
            show_peaks: Highlight peak periods
            show_forecast: Show trend forecast if available

        Returns:
            Plotly figure object
        """
        self.data = trend_data

        # Determine visualization type based on data
        if "citation_timeline" in trend_data:
            self.figure = self._create_citation_timeline(trend_data, chart_type, show_peaks, show_forecast)
        elif "usage_evolution" in trend_data:
            self.figure = self._create_usage_evolution(trend_data, chart_type)
        elif "impact_trajectory" in trend_data:
            self.figure = self._create_impact_trajectory(trend_data, chart_type)
        else:
            # Generic time series
            self.figure = self._create_generic_timeseries(trend_data, chart_type)

        return self.figure

    def _create_citation_timeline(
        self,
        trend_data: Dict[str, Any],
        chart_type: str,
        show_peaks: bool,
        show_forecast: bool,
    ) -> go.Figure:
        """Create citation timeline visualization."""
        timeline = trend_data["citation_timeline"]

        fig = go.Figure()

        # Main citation trend
        dates = timeline["dates"]
        counts = timeline["counts"]

        if chart_type == "area":
            fig.add_trace(
                go.Scatter(
                    x=dates,
                    y=counts,
                    mode="lines",
                    fill="tozeroy",
                    name="Citations",
                    line=dict(
                        color=ColorSchemes.get_scheme(self.config.color_scheme)["primary"],
                        width=2,
                    ),
                    hovertemplate="<b>%{x}</b><br>Citations: %{y}<extra></extra>",
                )
            )
        elif chart_type == "bar":
            fig.add_trace(
                go.Bar(
                    x=dates,
                    y=counts,
                    name="Citations",
                    marker_color=ColorSchemes.get_scheme(self.config.color_scheme)["primary"],
                    hovertemplate="<b>%{x}</b><br>Citations: %{y}<extra></extra>",
                )
            )
        else:  # line
            fig.add_trace(
                go.Scatter(
                    x=dates,
                    y=counts,
                    mode="lines+markers",
                    name="Citations",
                    line=dict(
                        color=ColorSchemes.get_scheme(self.config.color_scheme)["primary"],
                        width=2,
                    ),
                    marker=dict(size=6),
                    hovertemplate="<b>%{x}</b><br>Citations: %{y}<extra></extra>",
                )
            )

        # Highlight peaks
        if show_peaks and timeline.get("peaks"):
            peak_dates = [peak["date"] for peak in timeline["peaks"]]
            peak_counts = [peak["count"] for peak in timeline["peaks"]]

            fig.add_trace(
                go.Scatter(
                    x=peak_dates,
                    y=peak_counts,
                    mode="markers",
                    name="Peaks",
                    marker=dict(
                        size=12,
                        color=ColorSchemes.get_scheme(self.config.color_scheme)["danger"],
                        symbol="star",
                    ),
                    hovertemplate="<b>Peak: %{x}</b><br>Citations: %{y}<extra></extra>",
                )
            )

        # Add forecast if available
        if show_forecast and timeline.get("forecast"):
            forecast = timeline["forecast"]
            fig.add_trace(
                go.Scatter(
                    x=forecast["dates"],
                    y=forecast["values"],
                    mode="lines",
                    name="Forecast",
                    line=dict(
                        color=ColorSchemes.get_scheme(self.config.color_scheme)["warning"],
                        width=2,
                        dash="dash",
                    ),
                    hovertemplate="<b>Forecast: %{x}</b><br>Expected: %{y}<extra></extra>",
                )
            )

        fig.update_layout(
            title={
                "text": "Citation Timeline",
                "x": 0.5,
                "xanchor": "center",
                "font": {"size": 20, "family": self.config.font_family},
            },
            xaxis_title="Date",
            yaxis_title="Citations",
            width=self.config.width,
            height=self.config.height,
            template=self.config.theme,
            hovermode="x unified",
            showlegend=self.config.show_legend,
        )

        return fig

    def _create_usage_evolution(self, trend_data: Dict[str, Any], chart_type: str) -> go.Figure:
        """Create usage evolution visualization (stacked)."""
        usage = trend_data["usage_evolution"]

        fig = go.Figure()

        colors = ColorSchemes.get_scheme(self.config.color_scheme)
        color_map = {
            "diagnostic": colors.get("success", "#2ca02c"),
            "prognostic": colors.get("warning", "#ff7f0e"),
            "therapeutic": colors.get("danger", "#d62728"),
            "research": colors.get("info", "#17becf"),
        }

        dates = usage["dates"]

        # Create stacked area or bar chart
        for usage_type, counts in usage["by_type"].items():
            if chart_type == "area":
                fig.add_trace(
                    go.Scatter(
                        x=dates,
                        y=counts,
                        mode="lines",
                        stackgroup="one",
                        name=usage_type.capitalize(),
                        line=dict(width=0.5),
                        fillcolor=color_map.get(usage_type, colors["primary"]),
                        hovertemplate=f"<b>{usage_type.capitalize()}</b><br>%{{x}}<br>Count: %{{y}}<extra></extra>",
                    )
                )
            else:  # bar
                fig.add_trace(
                    go.Bar(
                        x=dates,
                        y=counts,
                        name=usage_type.capitalize(),
                        marker_color=color_map.get(usage_type, colors["primary"]),
                        hovertemplate=f"<b>{usage_type.capitalize()}</b><br>%{{x}}<br>Count: %{{y}}<extra></extra>",
                    )
                )

        if chart_type == "bar":
            fig.update_layout(barmode="stack")

        fig.update_layout(
            title={
                "text": "Usage Type Evolution",
                "x": 0.5,
                "xanchor": "center",
                "font": {"size": 20, "family": self.config.font_family},
            },
            xaxis_title="Date",
            yaxis_title="Usage Count",
            width=self.config.width,
            height=self.config.height,
            template=self.config.theme,
            hovermode="x unified",
            showlegend=self.config.show_legend,
        )

        return fig

    def _create_impact_trajectory(self, trend_data: Dict[str, Any], chart_type: str) -> go.Figure:
        """Create impact trajectory visualization."""
        trajectory = trend_data["impact_trajectory"]

        # Create subplot with secondary y-axis
        fig = make_subplots(
            rows=1,
            cols=1,
            specs=[[{"secondary_y": True}]],
        )

        colors = ColorSchemes.get_scheme(self.config.color_scheme)

        # Citation count on primary y-axis
        fig.add_trace(
            go.Scatter(
                x=trajectory["dates"],
                y=trajectory["citation_counts"],
                mode="lines+markers",
                name="Citations",
                line=dict(color=colors["primary"], width=2),
                marker=dict(size=6),
            ),
            secondary_y=False,
        )

        # Impact score on secondary y-axis
        fig.add_trace(
            go.Scatter(
                x=trajectory["dates"],
                y=trajectory["impact_scores"],
                mode="lines+markers",
                name="Impact Score",
                line=dict(color=colors["secondary"], width=2),
                marker=dict(size=6),
            ),
            secondary_y=True,
        )

        # Add growth rate if available
        if trajectory.get("growth_rates"):
            fig.add_trace(
                go.Scatter(
                    x=trajectory["dates"],
                    y=trajectory["growth_rates"],
                    mode="lines",
                    name="Growth Rate",
                    line=dict(color=colors["success"], width=1, dash="dash"),
                    yaxis="y3",
                ),
                secondary_y=False,
            )

        fig.update_layout(
            title={
                "text": "Impact Trajectory",
                "x": 0.5,
                "xanchor": "center",
                "font": {"size": 20, "family": self.config.font_family},
            },
            width=self.config.width,
            height=self.config.height,
            template=self.config.theme,
            hovermode="x unified",
            showlegend=self.config.show_legend,
        )

        fig.update_xaxes(title_text="Date")
        fig.update_yaxes(title_text="Citations", secondary_y=False)
        fig.update_yaxes(title_text="Impact Score", secondary_y=True)

        return fig

    def _create_generic_timeseries(self, trend_data: Dict[str, Any], chart_type: str) -> go.Figure:
        """Create generic time series visualization."""
        fig = go.Figure()

        for series_name, series_data in trend_data.items():
            if isinstance(series_data, dict) and "dates" in series_data and "values" in series_data:
                fig.add_trace(
                    go.Scatter(
                        x=series_data["dates"],
                        y=series_data["values"],
                        mode="lines+markers",
                        name=series_name.replace("_", " ").title(),
                        line=dict(width=2),
                        marker=dict(size=6),
                    )
                )

        fig.update_layout(
            title={
                "text": "Temporal Trends",
                "x": 0.5,
                "xanchor": "center",
                "font": {"size": 20, "family": self.config.font_family},
            },
            xaxis_title="Date",
            yaxis_title="Value",
            width=self.config.width,
            height=self.config.height,
            template=self.config.theme,
            hovermode="x unified",
            showlegend=self.config.show_legend,
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
        filename = options.filename or "trend_visualization.html"
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
        filename = options.filename or f"trend_visualization.{options.format}"
        path = output_dir / filename

        width = options.width or self.config.width
        height = options.height or self.config.height

        self.figure.write_image(
            str(path), format=options.format, width=width, height=height, scale=options.scale
        )

        return str(path)

    def _serialize_data(self) -> Dict:
        """Serialize trend data for JSON export."""
        return self.data if self.data else {}

    def _show_figure(self) -> None:
        """Show the figure interactively."""
        self.figure.show()


def visualize_citation_timeline(
    timeline_data: Dict[str, Any],
    config: Optional[VisualizationConfig] = None,
    chart_type: str = "area",
    export_path: Optional[str] = None,
) -> go.Figure:
    """Convenience function to visualize citation timeline.

    Args:
        timeline_data: Timeline data with dates and counts
        config: Visualization configuration
        chart_type: Type of chart (line, area, bar)
        export_path: Optional path to export HTML

    Returns:
        Plotly figure
    """
    visualizer = TrendVisualizer(config)
    fig = visualizer.create({"citation_timeline": timeline_data}, chart_type=chart_type)

    if export_path:
        options = ExportOptions(format="html", filename=export_path)
        visualizer.export(options)

    return fig
