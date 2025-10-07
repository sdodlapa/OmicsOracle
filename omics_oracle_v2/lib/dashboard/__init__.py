"""
Dashboard components for OmicsOracle.

Provides interactive web-based dashboards for biomarker analysis,
visualization, and search integration.
"""

from omics_oracle_v2.lib.dashboard.app import DashboardApp
from omics_oracle_v2.lib.dashboard.components import AnalyticsPanel, SearchPanel, VisualizationPanel
from omics_oracle_v2.lib.dashboard.config import DashboardConfig

__all__ = [
    "DashboardApp",
    "DashboardConfig",
    "AnalyticsPanel",
    "SearchPanel",
    "VisualizationPanel",
]
