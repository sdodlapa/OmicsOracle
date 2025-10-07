"""
Report visualization and PDF generation.

Creates multi-panel dashboards and publication-ready reports.
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


class ReportVisualizer(BaseVisualization):
    """Create multi-panel report visualizations."""

    def create(
        self,
        report_data: Dict[str, Any],
        layout: str = "grid",
        include_summary: bool = True,
    ) -> go.Figure:
        """Create report visualization.

        Args:
            report_data: Report data with multiple panels
            layout: Layout type (grid, vertical, horizontal)
            include_summary: Include summary statistics panel

        Returns:
            Plotly figure object
        """
        self.data = report_data

        if layout == "grid":
            self.figure = self._create_grid_layout(report_data, include_summary)
        elif layout == "vertical":
            self.figure = self._create_vertical_layout(report_data, include_summary)
        elif layout == "horizontal":
            self.figure = self._create_horizontal_layout(report_data, include_summary)
        else:
            raise ValueError(f"Unsupported layout: {layout}")

        return self.figure

    def _create_grid_layout(self, report_data: Dict[str, Any], include_summary: bool) -> go.Figure:
        """Create grid layout with multiple panels."""
        panels = report_data.get("panels", [])
        num_panels = len(panels)

        # Handle empty panels
        if num_panels == 0:
            num_panels = 1
            panels = [{"type": "bar", "data": {}}]

        # Calculate grid dimensions
        if num_panels <= 2:
            rows, cols = 1, max(num_panels, 1)
        elif num_panels <= 4:
            rows, cols = 2, 2
        elif num_panels <= 6:
            rows, cols = 2, 3
        else:
            rows, cols = 3, 3

        # Create subplot specs based on panel types
        specs = []
        for i in range(rows):
            row_specs = []
            for j in range(cols):
                idx = i * cols + j
                if idx < len(panels):
                    panel_type = panels[idx].get("type", "bar")
                    if panel_type == "pie":
                        row_specs.append({"type": "domain"})
                    else:
                        row_specs.append({"type": "xy"})
                else:
                    row_specs.append(None)
            specs.append(row_specs)

        # Create subplots
        subplot_titles = [panel.get("title", f"Panel {i+1}") for i, panel in enumerate(panels)]

        fig = make_subplots(
            rows=rows,
            cols=cols,
            specs=specs,
            subplot_titles=subplot_titles,
            vertical_spacing=0.12,
            horizontal_spacing=0.1,
        )

        colors = ColorSchemes.get_scheme(self.config.color_scheme)
        color_list = list(colors.values())

        # Add traces for each panel
        for idx, panel in enumerate(panels):
            row = (idx // cols) + 1
            col = (idx % cols) + 1

            panel_type = panel.get("type", "bar")
            data = panel.get("data", {})

            if panel_type == "bar":
                fig.add_trace(
                    go.Bar(
                        x=data.get("categories", data.get("x", [])),
                        y=data.get("values", data.get("y", [])),
                        name=panel.get("name", ""),
                        marker_color=color_list[idx % len(color_list)],
                        showlegend=False,
                    ),
                    row=row,
                    col=col,
                )
            elif panel_type == "line":
                fig.add_trace(
                    go.Scatter(
                        x=data.get("x", []),
                        y=data.get("y", []),
                        mode="lines+markers",
                        name=panel.get("name", ""),
                        line=dict(color=color_list[idx % len(color_list)]),
                        showlegend=False,
                    ),
                    row=row,
                    col=col,
                )
            elif panel_type == "pie":
                fig.add_trace(
                    go.Pie(
                        labels=data.get("categories", []),
                        values=data.get("values", []),
                        name=panel.get("name", ""),
                        showlegend=False,
                    ),
                    row=row,
                    col=col,
                )

        # Update layout
        fig.update_layout(
            title={
                "text": report_data.get("title", "Biomarker Analysis Report"),
                "x": 0.5,
                "xanchor": "center",
                "font": {"size": 24, "family": self.config.font_family},
            },
            width=self.config.width,
            height=self.config.height,
            template=self.config.theme,
            showlegend=False,
        )

        return fig

    def _create_vertical_layout(self, report_data: Dict[str, Any], include_summary: bool) -> go.Figure:
        """Create vertical stack layout."""
        panels = report_data.get("panels", [])
        num_panels = len(panels)

        # Create subplot specs for pie charts
        specs = []
        for panel in panels:
            panel_type = panel.get("type", "bar")
            if panel_type == "pie":
                specs.append([{"type": "domain"}])
            else:
                specs.append([{"type": "xy"}])

        # Create vertical subplots
        subplot_titles = [panel.get("title", f"Panel {i+1}") for i, panel in enumerate(panels)]

        fig = make_subplots(
            rows=num_panels,
            cols=1,
            specs=specs,
            subplot_titles=subplot_titles,
            vertical_spacing=0.1,
        )

        colors = ColorSchemes.get_scheme(self.config.color_scheme)
        color_list = list(colors.values())

        # Add traces
        for idx, panel in enumerate(panels):
            panel_type = panel.get("type", "bar")
            data = panel.get("data", {})

            if panel_type == "bar":
                fig.add_trace(
                    go.Bar(
                        x=data.get("categories", data.get("x", [])),
                        y=data.get("values", data.get("y", [])),
                        name=panel.get("name", ""),
                        marker_color=color_list[idx % len(color_list)],
                        showlegend=False,
                    ),
                    row=idx + 1,
                    col=1,
                )
            elif panel_type == "line":
                fig.add_trace(
                    go.Scatter(
                        x=data.get("x", []),
                        y=data.get("y", []),
                        mode="lines+markers",
                        name=panel.get("name", ""),
                        line=dict(color=color_list[idx % len(color_list)]),
                        showlegend=False,
                    ),
                    row=idx + 1,
                    col=1,
                )
            elif panel_type == "pie":
                fig.add_trace(
                    go.Pie(
                        labels=data.get("categories", []),
                        values=data.get("values", []),
                        name=panel.get("name", ""),
                        showlegend=False,
                    ),
                    row=idx + 1,
                    col=1,
                )

        fig.update_layout(
            title={
                "text": report_data.get("title", "Biomarker Analysis Report"),
                "x": 0.5,
                "xanchor": "center",
                "font": {"size": 24, "family": self.config.font_family},
            },
            width=self.config.width,
            height=self.config.height,
            template=self.config.theme,
        )

        return fig

    def _create_horizontal_layout(self, report_data: Dict[str, Any], include_summary: bool) -> go.Figure:
        """Create horizontal layout."""
        panels = report_data.get("panels", [])
        num_panels = len(panels)

        # Create subplot specs for pie charts
        specs = []
        for panel in panels:
            panel_type = panel.get("type", "bar")
            if panel_type == "pie":
                specs.append({"type": "domain"})
            else:
                specs.append({"type": "xy"})

        # Create horizontal subplots
        subplot_titles = [panel.get("title", f"Panel {i+1}") for i, panel in enumerate(panels)]

        fig = make_subplots(
            rows=1,
            cols=num_panels,
            specs=[specs],
            subplot_titles=subplot_titles,
            horizontal_spacing=0.1,
        )

        colors = ColorSchemes.get_scheme(self.config.color_scheme)
        color_list = list(colors.values())

        # Add traces
        for idx, panel in enumerate(panels):
            panel_type = panel.get("type", "bar")
            data = panel.get("data", {})

            if panel_type == "bar":
                fig.add_trace(
                    go.Bar(
                        x=data.get("categories", data.get("x", [])),
                        y=data.get("values", data.get("y", [])),
                        name=panel.get("name", ""),
                        marker_color=color_list[idx % len(color_list)],
                        showlegend=False,
                    ),
                    row=1,
                    col=idx + 1,
                )
            elif panel_type == "line":
                fig.add_trace(
                    go.Scatter(
                        x=data.get("x", []),
                        y=data.get("y", []),
                        mode="lines+markers",
                        name=panel.get("name", ""),
                        line=dict(color=color_list[idx % len(color_list)]),
                        showlegend=False,
                    ),
                    row=1,
                    col=idx + 1,
                )
            elif panel_type == "pie":
                fig.add_trace(
                    go.Pie(
                        labels=data.get("categories", []),
                        values=data.get("values", []),
                        name=panel.get("name", ""),
                        showlegend=False,
                    ),
                    row=1,
                    col=idx + 1,
                )

        fig.update_layout(
            title={
                "text": report_data.get("title", "Biomarker Analysis Report"),
                "x": 0.5,
                "xanchor": "center",
                "font": {"size": 24, "family": self.config.font_family},
            },
            width=self.config.width,
            height=self.config.height,
            template=self.config.theme,
        )

        return fig

    def update(
        self,
        title: Optional[str] = None,
        layout: Optional[str] = None,
        **kwargs,
    ) -> None:
        """Update visualization properties."""
        if self.figure is None:
            raise ValueError("No figure to update. Call create() first.")

        if title:
            self.figure.update_layout(title=title)

        if layout and self.data:
            # Recreate with new layout
            self.create(self.data, layout=layout)

        if kwargs:
            self.figure.update_layout(**kwargs)

    def _export_html(self, options: ExportOptions) -> str:
        """Export as interactive HTML."""
        output_dir = create_output_directory()
        filename = options.filename or "report.html"
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
        filename = options.filename or f"report.{options.format}"
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
        """Serialize report data for JSON export."""
        return self.data if self.data else {}

    def _show_figure(self) -> None:
        """Show the figure interactively."""
        self.figure.show()


def create_executive_dashboard(
    summary_stats: Dict[str, Any],
    config: Optional[VisualizationConfig] = None,
    export_path: Optional[str] = None,
) -> go.Figure:
    """Create executive summary dashboard.

    Args:
        summary_stats: Summary statistics and key metrics
        config: Visualization configuration
        export_path: Optional path to export HTML

    Returns:
        Plotly figure
    """
    # Build panels from summary stats
    panels = []

    if "citation_distribution" in summary_stats:
        panels.append(
            {
                "title": "Citation Distribution",
                "type": "bar",
                "data": {
                    "categories": list(summary_stats["citation_distribution"].keys()),
                    "values": list(summary_stats["citation_distribution"].values()),
                },
            }
        )

    if "usage_types" in summary_stats:
        panels.append(
            {
                "title": "Usage Type Distribution",
                "type": "pie",
                "data": {
                    "categories": list(summary_stats["usage_types"].keys()),
                    "values": list(summary_stats["usage_types"].values()),
                },
            }
        )

    if "temporal_trend" in summary_stats:
        trend = summary_stats["temporal_trend"]
        # Handle dict format (year: count)
        if isinstance(trend, dict):
            panels.append(
                {
                    "title": "Citation Trend",
                    "type": "line",
                    "data": {"x": list(trend.keys()), "y": list(trend.values())},
                }
            )
        else:
            # Handle structured format
            panels.append(
                {
                    "title": "Citation Trend",
                    "type": "line",
                    "data": {"x": trend.get("dates", []), "y": trend.get("counts", [])},
                }
            )

    report_data = {
        "title": "Executive Summary Dashboard",
        "panels": panels,
    }

    viz = ReportVisualizer(config)
    fig = viz.create(report_data, layout="grid")

    if export_path:
        options = ExportOptions(format="html", filename=export_path)
        viz.export(options)

    return fig


def create_biomarker_report(
    biomarker_analysis: Dict[str, Any],
    config: Optional[VisualizationConfig] = None,
    layout: str = "vertical",
    export_path: Optional[str] = None,
) -> go.Figure:
    """Create comprehensive biomarker analysis report.

    Args:
        biomarker_analysis: Complete biomarker analysis results
        config: Visualization configuration
        layout: Report layout (grid, vertical, horizontal)
        export_path: Optional path to export HTML

    Returns:
        Plotly figure
    """
    panels = []

    # Top biomarkers panel
    if "top_biomarkers" in biomarker_analysis:
        top = biomarker_analysis["top_biomarkers"]
        # Handle dict format
        if isinstance(top, dict):
            panels.append(
                {
                    "title": "Top Biomarkers by Citations",
                    "type": "bar",
                    "data": {
                        "categories": list(top.keys()),
                        "values": list(top.values()),
                    },
                }
            )
        else:
            # Handle list of dicts format
            panels.append(
                {
                    "title": "Top Biomarkers by Citations",
                    "type": "bar",
                    "data": {
                        "categories": [b["name"] for b in top],
                        "values": [b["citations"] for b in top],
                    },
                }
            )

    # Usage distribution panel
    if "usage_distribution" in biomarker_analysis:
        usage = biomarker_analysis["usage_distribution"]
        panels.append(
            {
                "title": "Usage Type Distribution",
                "type": "pie",
                "data": {"categories": list(usage.keys()), "values": list(usage.values())},
            }
        )

    # Temporal trend panel
    if "temporal_trend" in biomarker_analysis:
        trend = biomarker_analysis["temporal_trend"]
        # Handle dict format
        if isinstance(trend, dict) and "dates" not in trend:
            panels.append(
                {
                    "title": "Citation Timeline",
                    "type": "line",
                    "data": {"x": list(trend.keys()), "y": list(trend.values())},
                }
            )
        else:
            panels.append(
                {
                    "title": "Citation Timeline",
                    "type": "line",
                    "data": {"x": trend.get("dates", []), "y": trend.get("counts", [])},
                }
            )

    report_data = {
        "title": "Biomarker Analysis Report",
        "panels": panels,
    }

    viz = ReportVisualizer(config)
    fig = viz.create(report_data, layout=layout)

    if export_path:
        options = ExportOptions(format="html", filename=export_path)
        viz.export(options)

    return fig
