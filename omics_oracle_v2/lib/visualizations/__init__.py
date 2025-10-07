"""
Visualization base infrastructure.

Provides common functionality for all visualization components.
"""

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Union


@dataclass
class VisualizationConfig:
    """Configuration for visualizations."""

    width: int = 1200
    height: int = 800
    theme: str = "plotly_white"  # plotly_white, plotly_dark, seaborn, etc.
    color_scheme: str = "default"  # default, colorblind, high_contrast
    font_family: str = "Arial, sans-serif"
    font_size: int = 12
    show_legend: bool = True
    interactive: bool = True
    export_format: str = "html"  # html, png, svg, pdf


@dataclass
class ExportOptions:
    """Options for exporting visualizations."""

    format: str = "html"  # html, png, svg, pdf, json
    filename: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    scale: float = 1.0  # For image exports


class BaseVisualization(ABC):
    """Base class for all visualizations."""

    def __init__(self, config: Optional[VisualizationConfig] = None):
        """Initialize visualization with configuration."""
        self.config = config or VisualizationConfig()
        self.figure = None
        self.data = None

    @abstractmethod
    def create(self, data: Any) -> Any:
        """Create the visualization from data.

        Args:
            data: Input data for visualization

        Returns:
            Visualization figure object
        """
        pass

    @abstractmethod
    def update(self, **kwargs) -> None:
        """Update visualization properties.

        Args:
            **kwargs: Properties to update
        """
        pass

    def export(self, options: Optional[ExportOptions] = None) -> Union[str, bytes]:
        """Export visualization to file or bytes.

        Args:
            options: Export options

        Returns:
            File path (str) or bytes depending on format
        """
        if self.figure is None:
            raise ValueError("No figure to export. Call create() first.")

        options = options or ExportOptions()

        if options.format == "html":
            return self._export_html(options)
        elif options.format in ["png", "svg", "pdf"]:
            return self._export_image(options)
        elif options.format == "json":
            return self._export_json(options)
        else:
            raise ValueError(f"Unsupported export format: {options.format}")

    @abstractmethod
    def _export_html(self, options: ExportOptions) -> str:
        """Export as HTML."""
        pass

    @abstractmethod
    def _export_image(self, options: ExportOptions) -> str:
        """Export as image (PNG, SVG, PDF)."""
        pass

    def _export_json(self, options: ExportOptions) -> str:
        """Export data as JSON."""
        output = {
            "type": self.__class__.__name__,
            "config": self.config.__dict__,
            "data": self._serialize_data(),
        }

        if options.filename:
            path = Path(options.filename)
            path.write_text(json.dumps(output, indent=2))
            return str(path)

        return json.dumps(output, indent=2)

    @abstractmethod
    def _serialize_data(self) -> Dict:
        """Serialize visualization data for JSON export."""
        pass

    def show(self) -> None:
        """Display the visualization interactively."""
        if self.figure is None:
            raise ValueError("No figure to show. Call create() first.")
        self._show_figure()

    @abstractmethod
    def _show_figure(self) -> None:
        """Show the figure (implementation-specific)."""
        pass


class ColorSchemes:
    """Predefined color schemes."""

    DEFAULT = {
        "primary": "#1f77b4",
        "secondary": "#ff7f0e",
        "success": "#2ca02c",
        "danger": "#d62728",
        "warning": "#ff7f0e",
        "info": "#17becf",
        "biomarker": "#9467bd",
        "dataset": "#8c564b",
        "paper": "#e377c2",
        "disease": "#bcbd22",
    }

    COLORBLIND_SAFE = {
        "primary": "#0173B2",
        "secondary": "#DE8F05",
        "success": "#029E73",
        "danger": "#CC78BC",
        "warning": "#ECE133",
        "info": "#56B4E9",
        "biomarker": "#949494",
        "dataset": "#FBAFE4",
        "paper": "#CA9161",
        "disease": "#029E73",
    }

    HIGH_CONTRAST = {
        "primary": "#000000",
        "secondary": "#E69F00",
        "success": "#009E73",
        "danger": "#F0E442",
        "warning": "#0072B2",
        "info": "#D55E00",
        "biomarker": "#CC79A7",
        "dataset": "#000000",
        "paper": "#E69F00",
        "disease": "#56B4E9",
    }

    @classmethod
    def get_scheme(cls, name: str) -> Dict[str, str]:
        """Get color scheme by name."""
        schemes = {
            "default": cls.DEFAULT,
            "colorblind": cls.COLORBLIND_SAFE,
            "high_contrast": cls.HIGH_CONTRAST,
        }
        return schemes.get(name.lower(), cls.DEFAULT)


class VisualizationThemes:
    """Predefined visualization themes."""

    LIGHT = {
        "template": "plotly_white",
        "background": "#ffffff",
        "text": "#000000",
        "grid": "#e5e5e5",
    }

    DARK = {
        "template": "plotly_dark",
        "background": "#1e1e1e",
        "text": "#ffffff",
        "grid": "#404040",
    }

    SEABORN = {
        "template": "seaborn",
        "background": "#eaeaf2",
        "text": "#000000",
        "grid": "#ffffff",
    }

    @classmethod
    def get_theme(cls, name: str) -> Dict[str, str]:
        """Get theme by name."""
        themes = {"light": cls.LIGHT, "dark": cls.DARK, "seaborn": cls.SEABORN}
        return themes.get(name.lower(), cls.LIGHT)


def create_output_directory(base_path: str = "data/visualizations") -> Path:
    """Create output directory for visualizations.

    Args:
        base_path: Base directory path

    Returns:
        Path object for the directory
    """
    path = Path(base_path)
    path.mkdir(parents=True, exist_ok=True)
    return path
