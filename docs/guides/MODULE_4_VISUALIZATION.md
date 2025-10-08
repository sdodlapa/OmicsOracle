# 📊 Module 4: Advanced Visualization System

**Date**: December 28, 2024
**Module**: Interactive Data Visualization & Dashboards
**Priority**: High - User Experience & Insights
**Estimated Timeline**: 4-6 weeks

---

## 🎯 **Module Overview**

The Advanced Visualization System creates interactive, real-time visualizations and dashboards that transform complex biomedical data into intuitive, actionable insights. This module provides the visual intelligence layer for the OmicsOracle platform, enabling researchers to explore patterns, relationships, and trends across datasets, publications, and statistical analyses.

### **Core Objectives**

1. **Interactive Dashboards**: Real-time, responsive visualization interfaces
2. **Multi-Modal Visualization**: Support for diverse chart types and data representations
3. **Real-Time Updates**: Live data streaming and dynamic chart updates
4. **Export Capabilities**: High-quality export in multiple formats
5. **Mobile Responsiveness**: Consistent experience across all devices

---

## 🏗️ **System Architecture**

### **Component Structure**

```
src/omics_oracle/visualization/
├── __init__.py
├── dashboard_engine.py          # Main dashboard orchestrator
├── chart_factory/               # Chart generation
│   ├── __init__.py
│   ├── base_chart.py           # Base chart class
│   ├── metadata_charts.py      # Metadata visualizations
│   ├── statistical_charts.py   # Statistical visualizations
│   ├── network_charts.py       # Network/relationship charts
│   ├── temporal_charts.py      # Time-series visualizations
│   └── custom_charts.py        # Custom/specialized charts
├── interactive/                 # Interactive components
│   ├── __init__.py
│   ├── filters.py              # Interactive filtering
│   ├── drill_down.py           # Drill-down functionality
│   ├── real_time.py            # Real-time updates
│   └── annotations.py          # Interactive annotations
├── data_processing/             # Data preparation for visualization
│   ├── __init__.py
│   ├── aggregator.py           # Data aggregation
│   ├── transformer.py          # Data transformation
│   ├── cache_manager.py        # Visualization caching
│   └── stream_processor.py     # Real-time data processing
├── export/                      # Export capabilities
│   ├── __init__.py
│   ├── image_exporter.py       # Static image export
│   ├── pdf_generator.py        # PDF report generation
│   ├── data_exporter.py        # Raw data export
│   └── interactive_exporter.py # Interactive HTML export
├── themes/                      # Styling and themes
│   ├── __init__.py
│   ├── color_schemes.py        # Color palettes
│   ├── layouts.py              # Layout templates
│   └── responsive_design.py    # Responsive styling
└── models/                      # Data models
    ├── __init__.py
    ├── chart_config.py         # Chart configuration models
    ├── dashboard_config.py     # Dashboard models
    └── export_config.py        # Export configuration models
```

### **Frontend Component Structure**

```
interfaces/modern/src/components/visualization/
├── Dashboard/
│   ├── DashboardContainer.tsx   # Main dashboard container
│   ├── DashboardGrid.tsx        # Grid layout management
│   ├── DashboardControls.tsx    # Dashboard controls
│   └── DashboardExport.tsx      # Export functionality
├── Charts/
│   ├── MetadataCharts/
│   │   ├── OrganismDistribution.tsx
│   │   ├── PlatformTimeline.tsx
│   │   ├── SampleSizeDistribution.tsx
│   │   └── GeographicDistribution.tsx
│   ├── StatisticalCharts/
│   │   ├── StatsSummaryDashboard.tsx
│   │   ├── QualityMetrics.tsx
│   │   ├── DistributionPlots.tsx
│   │   └── CorrelationHeatmap.tsx
│   ├── NetworkCharts/
│   │   ├── PublicationNetwork.tsx
│   │   ├── CitationGraph.tsx
│   │   └── KnowledgeGraph.tsx
│   └── TemporalCharts/
│       ├── TrendAnalysis.tsx
│       ├── TimeSeriesPlot.tsx
│       └── EvolutionTimeline.tsx
├── Interactive/
│   ├── FilterPanel.tsx          # Advanced filtering
│   ├── DrillDownModal.tsx       # Drill-down interface
│   ├── RealTimeIndicator.tsx    # Live data indicator
│   └── AnnotationTools.tsx      # Annotation interface
└── Common/
    ├── ChartContainer.tsx       # Common chart wrapper
    ├── LoadingSpinner.tsx       # Loading states
    ├── ErrorBoundary.tsx        # Error handling
    └── ExportButton.tsx         # Export controls
```

---

## 🔧 **Core Components Implementation**

### **1. Chart Factory System**

**Base Chart Class**:
```python
# src/omics_oracle/visualization/chart_factory/base_chart.py

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import plotly.graph_objects as go
import plotly.express as px
from dataclasses import dataclass

@dataclass
class ChartConfig:
    """Chart configuration parameters"""
    chart_type: str
    title: str
    width: Optional[int] = None
    height: Optional[int] = None
    theme: str = "plotly_white"
    interactive: bool = True
    responsive: bool = True
    export_formats: List[str] = None
    custom_config: Dict[str, Any] = None

    def __post_init__(self):
        if self.export_formats is None:
            self.export_formats = ['png', 'svg', 'html']
        if self.custom_config is None:
            self.custom_config = {}

@dataclass
class ChartData:
    """Standardized chart data structure"""
    data: Any  # DataFrame, dict, or other data structure
    metadata: Dict[str, Any]
    filters: Dict[str, Any] = None
    aggregations: Dict[str, Any] = None

    def __post_init__(self):
        if self.filters is None:
            self.filters = {}
        if self.aggregations is None:
            self.aggregations = {}

class BaseChart(ABC):
    """Base class for all chart types"""

    def __init__(self, config: ChartConfig):
        self.config = config
        self.figure = None
        self.data_cache = {}

    @abstractmethod
    async def create_chart(self, data: ChartData) -> go.Figure:
        """Create the chart from data"""
        pass

    async def update_chart(self, new_data: ChartData) -> go.Figure:
        """Update existing chart with new data"""
        return await self.create_chart(new_data)

    def apply_theme(self, figure: go.Figure) -> go.Figure:
        """Apply theme and styling to the chart"""

        figure.update_layout(
            template=self.config.theme,
            title={
                'text': self.config.title,
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 16, 'family': 'Arial, sans-serif'}
            },
            width=self.config.width,
            height=self.config.height,
            showlegend=True,
            legend={'orientation': 'h', 'yanchor': 'bottom', 'y': 1.02},
            margin={'l': 40, 'r': 40, 't': 60, 'b': 40}
        )

        if self.config.responsive:
            figure.update_layout(autosize=True)

        return figure

    def add_interactivity(self, figure: go.Figure) -> go.Figure:
        """Add interactive features to the chart"""

        if not self.config.interactive:
            return figure

        # Add hover templates
        for trace in figure.data:
            if hasattr(trace, 'hovertemplate'):
                trace.hovertemplate = self._create_hover_template(trace)

        # Add selection and zoom capabilities
        figure.update_layout(
            selectdirection='diagonal',
            dragmode='select'
        )

        return figure

    def _create_hover_template(self, trace) -> str:
        """Create custom hover template"""
        return "<b>%{fullData.name}</b><br>" + \
               "Value: %{y}<br>" + \
               "Category: %{x}<br>" + \
               "<extra></extra>"

class MetadataChart(BaseChart):
    """Charts for dataset metadata visualization"""

    async def create_organism_distribution(self, data: ChartData) -> go.Figure:
        """Create organism distribution pie chart"""

        organism_counts = data.data['organism'].value_counts()

        fig = px.pie(
            values=organism_counts.values,
            names=organism_counts.index,
            title="Dataset Distribution by Organism"
        )

        fig.update_traces(
            hovertemplate="<b>%{label}</b><br>" +
                         "Count: %{value}<br>" +
                         "Percentage: %{percent}<br>" +
                         "<extra></extra>"
        )

        return self.apply_theme(self.add_interactivity(fig))

    async def create_platform_timeline(self, data: ChartData) -> go.Figure:
        """Create platform usage timeline"""

        platform_timeline = data.data.groupby(['year', 'platform']).size().reset_index(name='count')

        fig = px.line(
            platform_timeline,
            x='year',
            y='count',
            color='platform',
            title="Platform Usage Over Time"
        )

        fig.update_layout(
            xaxis_title="Year",
            yaxis_title="Number of Datasets",
            hovermode='x unified'
        )

        return self.apply_theme(self.add_interactivity(fig))

    async def create_sample_size_distribution(self, data: ChartData) -> go.Figure:
        """Create sample size distribution histogram"""

        fig = px.histogram(
            data.data,
            x='sample_count',
            nbins=30,
            title="Sample Size Distribution"
        )

        fig.update_layout(
            xaxis_title="Number of Samples",
            yaxis_title="Number of Datasets",
            bargap=0.1
        )

        # Add statistical annotations
        mean_samples = data.data['sample_count'].mean()
        median_samples = data.data['sample_count'].median()

        fig.add_vline(
            x=mean_samples,
            line_dash="dash",
            line_color="red",
            annotation_text=f"Mean: {mean_samples:.1f}"
        )

        fig.add_vline(
            x=median_samples,
            line_dash="dash",
            line_color="blue",
            annotation_text=f"Median: {median_samples:.1f}"
        )

        return self.apply_theme(self.add_interactivity(fig))
```

**Statistical Visualization Components**:
```python
# src/omics_oracle/visualization/chart_factory/statistical_charts.py

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from .base_chart import BaseChart, ChartData, ChartConfig

class StatisticalChart(BaseChart):
    """Charts for statistical data visualization"""

    async def create_quality_metrics_radar(self, data: ChartData) -> go.Figure:
        """Create radar chart for dataset quality metrics"""

        quality_metrics = data.data

        # Define metrics and their values
        metrics = ['Completeness', 'Consistency', 'Accuracy', 'Timeliness', 'Validity']
        values = [
            quality_metrics.get('completeness_score', 0) * 100,
            quality_metrics.get('consistency_score', 0) * 100,
            quality_metrics.get('accuracy_score', 0) * 100,
            quality_metrics.get('timeliness_score', 0) * 100,
            quality_metrics.get('validity_score', 0) * 100
        ]

        fig = go.Figure()

        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=metrics,
            fill='toself',
            name='Quality Metrics',
            line_color='rgb(1, 87, 155)',
            fillcolor='rgba(1, 87, 155, 0.3)'
        ))

        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )
            ),
            showlegend=False,
            title="Dataset Quality Assessment"
        )

        return self.apply_theme(fig)

    async def create_correlation_heatmap(self, data: ChartData) -> go.Figure:
        """Create correlation heatmap for numerical variables"""

        correlation_matrix = data.data

        fig = go.Figure(data=go.Heatmap(
            z=correlation_matrix.values,
            x=correlation_matrix.columns,
            y=correlation_matrix.index,
            colorscale='RdBu_r',
            zmid=0,
            hoverongaps=False,
            hovertemplate="<b>%{y} vs %{x}</b><br>" +
                         "Correlation: %{z:.3f}<br>" +
                         "<extra></extra>"
        ))

        fig.update_layout(
            title="Variable Correlation Matrix",
            xaxis_title="Variables",
            yaxis_title="Variables"
        )

        return self.apply_theme(fig)

    async def create_distribution_comparison(self, data: ChartData) -> go.Figure:
        """Create distribution comparison plots"""

        datasets = data.data

        # Create subplots for multiple distributions
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=['Sample Size Distribution', 'Expression Range Distribution',
                           'Missing Data Distribution', 'Quality Score Distribution'],
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )

        # Sample size distribution
        fig.add_trace(
            go.Histogram(x=datasets['sample_count'], name='Sample Size', nbinsx=20),
            row=1, col=1
        )

        # Expression range distribution
        if 'expression_range' in datasets.columns:
            fig.add_trace(
                go.Histogram(x=datasets['expression_range'], name='Expression Range', nbinsx=20),
                row=1, col=2
            )

        # Missing data percentage
        if 'missing_percentage' in datasets.columns:
            fig.add_trace(
                go.Histogram(x=datasets['missing_percentage'], name='Missing Data %', nbinsx=20),
                row=2, col=1
            )

        # Quality scores
        if 'quality_score' in datasets.columns:
            fig.add_trace(
                go.Histogram(x=datasets['quality_score'], name='Quality Score', nbinsx=20),
                row=2, col=2
            )

        fig.update_layout(height=600, showlegend=False, title_text="Dataset Characteristics Distribution")

        return self.apply_theme(fig)
```

### **2. Interactive Dashboard System**

**Dashboard Engine**:
```python
# src/omics_oracle/visualization/dashboard_engine.py

import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from .chart_factory.metadata_charts import MetadataChart
from .chart_factory.statistical_charts import StatisticalChart
from .interactive.real_time import RealTimeUpdater
from .data_processing.aggregator import DataAggregator

@dataclass
class DashboardConfig:
    """Dashboard configuration"""
    dashboard_id: str
    title: str
    layout: str  # 'grid', 'tabs', 'sections'
    charts: List[Dict[str, Any]]
    refresh_interval: int = 30  # seconds
    auto_refresh: bool = True
    responsive: bool = True
    export_enabled: bool = True

class DashboardEngine:
    """Main dashboard orchestration engine"""

    def __init__(self):
        self.active_dashboards = {}
        self.chart_factories = {
            'metadata': MetadataChart,
            'statistical': StatisticalChart
        }
        self.data_aggregator = DataAggregator()
        self.real_time_updater = RealTimeUpdater()

    async def create_dashboard(self, config: DashboardConfig, data_source: str) -> Dict[str, Any]:
        """Create a new dashboard"""

        dashboard = {
            'id': config.dashboard_id,
            'title': config.title,
            'config': config,
            'charts': {},
            'last_update': None,
            'status': 'initializing'
        }

        try:
            # Initialize charts
            for chart_config in config.charts:
                chart = await self._create_chart(chart_config, data_source)
                dashboard['charts'][chart_config['id']] = chart

            # Set up real-time updates if enabled
            if config.auto_refresh:
                await self.real_time_updater.register_dashboard(
                    config.dashboard_id,
                    config.refresh_interval
                )

            dashboard['status'] = 'active'
            self.active_dashboards[config.dashboard_id] = dashboard

            return dashboard

        except Exception as e:
            dashboard['status'] = 'error'
            dashboard['error'] = str(e)
            return dashboard

    async def _create_chart(self, chart_config: Dict[str, Any], data_source: str) -> Dict[str, Any]:
        """Create individual chart"""

        chart_type = chart_config.get('type', 'metadata')
        chart_factory_class = self.chart_factories.get(chart_type)

        if not chart_factory_class:
            raise ValueError(f"Unknown chart type: {chart_type}")

        # Get data for chart
        chart_data = await self.data_aggregator.get_chart_data(
            data_source,
            chart_config.get('data_query', {})
        )

        # Create chart factory instance
        factory_config = ChartConfig(
            chart_type=chart_config.get('chart_subtype', 'default'),
            title=chart_config.get('title', 'Chart'),
            width=chart_config.get('width'),
            height=chart_config.get('height'),
            interactive=chart_config.get('interactive', True)
        )

        chart_factory = chart_factory_class(factory_config)

        # Generate chart
        figure = await chart_factory.create_chart(chart_data)

        return {
            'id': chart_config['id'],
            'figure': figure,
            'config': chart_config,
            'last_update': datetime.utcnow(),
            'data_hash': self._calculate_data_hash(chart_data)
        }

    async def update_dashboard(self, dashboard_id: str, force_refresh: bool = False) -> Dict[str, Any]:
        """Update dashboard with fresh data"""

        if dashboard_id not in self.active_dashboards:
            raise ValueError(f"Dashboard {dashboard_id} not found")

        dashboard = self.active_dashboards[dashboard_id]
        config = dashboard['config']

        updated_charts = {}

        for chart_id, chart in dashboard['charts'].items():
            try:
                # Check if chart needs update
                if not force_refresh:
                    current_hash = await self._get_current_data_hash(chart['config'])
                    if current_hash == chart['data_hash']:
                        updated_charts[chart_id] = chart
                        continue

                # Update chart
                updated_chart = await self._create_chart(
                    chart['config'],
                    config.dashboard_id  # Use dashboard_id as data_source
                )
                updated_charts[chart_id] = updated_chart

            except Exception as e:
                # Keep old chart if update fails
                chart['error'] = str(e)
                updated_charts[chart_id] = chart

        dashboard['charts'] = updated_charts
        dashboard['last_update'] = datetime.utcnow()

        return dashboard

    async def get_dashboard_data(self, dashboard_id: str) -> Dict[str, Any]:
        """Get dashboard data for frontend"""

        if dashboard_id not in self.active_dashboards:
            return {'error': 'Dashboard not found'}

        dashboard = self.active_dashboards[dashboard_id]

        # Convert plotly figures to JSON
        charts_json = {}
        for chart_id, chart in dashboard['charts'].items():
            if 'figure' in chart:
                charts_json[chart_id] = {
                    'figure': chart['figure'].to_json(),
                    'config': chart['config'],
                    'last_update': chart['last_update'].isoformat(),
                    'error': chart.get('error')
                }

        return {
            'id': dashboard['id'],
            'title': dashboard['title'],
            'charts': charts_json,
            'last_update': dashboard['last_update'].isoformat() if dashboard['last_update'] else None,
            'status': dashboard['status']
        }
```

### **3. Real-Time Update System**

**WebSocket Integration**:
```python
# src/omics_oracle/visualization/interactive/real_time.py

import asyncio
import json
from typing import Dict, Set, Callable, Any
from datetime import datetime, timedelta
import websockets
from dataclasses import dataclass

@dataclass
class UpdateSubscription:
    """Real-time update subscription"""
    dashboard_id: str
    chart_ids: Set[str]
    update_interval: int
    last_update: datetime
    callback: Optional[Callable] = None

class RealTimeUpdater:
    """Manage real-time dashboard updates"""

    def __init__(self):
        self.subscriptions = {}
        self.websocket_connections = {}
        self.update_tasks = {}
        self.is_running = False

    async def start(self):
        """Start the real-time update service"""
        self.is_running = True

        # Start update loop
        asyncio.create_task(self._update_loop())

    async def stop(self):
        """Stop the real-time update service"""
        self.is_running = False

        # Cancel all update tasks
        for task in self.update_tasks.values():
            task.cancel()

        # Close websocket connections
        for ws in self.websocket_connections.values():
            await ws.close()

    async def register_dashboard(self,
                               dashboard_id: str,
                               update_interval: int = 30,
                               chart_ids: Set[str] = None) -> None:
        """Register a dashboard for real-time updates"""

        subscription = UpdateSubscription(
            dashboard_id=dashboard_id,
            chart_ids=chart_ids or set(),
            update_interval=update_interval,
            last_update=datetime.utcnow()
        )

        self.subscriptions[dashboard_id] = subscription

        # Start update task for this dashboard
        self.update_tasks[dashboard_id] = asyncio.create_task(
            self._dashboard_update_task(dashboard_id)
        )

    async def unregister_dashboard(self, dashboard_id: str) -> None:
        """Unregister a dashboard from real-time updates"""

        if dashboard_id in self.subscriptions:
            del self.subscriptions[dashboard_id]

        if dashboard_id in self.update_tasks:
            self.update_tasks[dashboard_id].cancel()
            del self.update_tasks[dashboard_id]

        if dashboard_id in self.websocket_connections:
            await self.websocket_connections[dashboard_id].close()
            del self.websocket_connections[dashboard_id]

    async def add_websocket_connection(self, dashboard_id: str, websocket) -> None:
        """Add websocket connection for dashboard"""
        self.websocket_connections[dashboard_id] = websocket

    async def _dashboard_update_task(self, dashboard_id: str) -> None:
        """Background task for dashboard updates"""

        while self.is_running and dashboard_id in self.subscriptions:
            try:
                subscription = self.subscriptions[dashboard_id]

                # Check if update is needed
                now = datetime.utcnow()
                if (now - subscription.last_update).seconds >= subscription.update_interval:

                    # Check for data changes
                    has_changes = await self._check_for_data_changes(dashboard_id)

                    if has_changes:
                        # Notify connected clients
                        await self._notify_dashboard_update(dashboard_id)
                        subscription.last_update = now

                # Wait before next check
                await asyncio.sleep(5)  # Check every 5 seconds

            except Exception as e:
                # Log error and continue
                await asyncio.sleep(10)  # Wait longer on error

    async def _check_for_data_changes(self, dashboard_id: str) -> bool:
        """Check if dashboard data has changed"""

        # This would integrate with your data sources to check for changes
        # For now, return False (no changes)
        return False

    async def _notify_dashboard_update(self, dashboard_id: str) -> None:
        """Notify clients of dashboard updates"""

        if dashboard_id not in self.websocket_connections:
            return

        websocket = self.websocket_connections[dashboard_id]

        try:
            update_message = {
                'type': 'dashboard_update',
                'dashboard_id': dashboard_id,
                'timestamp': datetime.utcnow().isoformat(),
                'charts_updated': list(self.subscriptions[dashboard_id].chart_ids)
            }

            await websocket.send(json.dumps(update_message))

        except websockets.ConnectionClosed:
            # Remove closed connection
            del self.websocket_connections[dashboard_id]
        except Exception as e:
            # Log error
            pass

    async def _update_loop(self):
        """Main update loop"""
        while self.is_running:
            try:
                # Perform any global update tasks
                await self._cleanup_expired_subscriptions()
                await asyncio.sleep(60)  # Run cleanup every minute

            except Exception as e:
                await asyncio.sleep(10)

    async def _cleanup_expired_subscriptions(self):
        """Clean up expired or inactive subscriptions"""

        expired_dashboards = []
        cutoff_time = datetime.utcnow() - timedelta(hours=24)

        for dashboard_id, subscription in self.subscriptions.items():
            if subscription.last_update < cutoff_time:
                expired_dashboards.append(dashboard_id)

        for dashboard_id in expired_dashboards:
            await self.unregister_dashboard(dashboard_id)
```

---

## 🎯 **Frontend Integration**

### **React Dashboard Components**

```typescript
// interfaces/modern/src/components/visualization/Dashboard/DashboardContainer.tsx

import React, { useState, useEffect, useCallback } from 'react';
import { WebSocketService } from '../../../services/websocket';
import { VisualizationAPI } from '../../../services/api';
import { DashboardGrid } from './DashboardGrid';
import { DashboardControls } from './DashboardControls';

interface DashboardContainerProps {
  dashboardId: string;
  title: string;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

export const DashboardContainer: React.FC<DashboardContainerProps> = ({
  dashboardId,
  title,
  autoRefresh = true,
  refreshInterval = 30
}) => {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(new Date());

  // WebSocket connection for real-time updates
  useEffect(() => {
    if (!autoRefresh) return;

    const wsService = new WebSocketService();

    wsService.connect(`/ws/dashboard/${dashboardId}`);

    wsService.onMessage((message) => {
      if (message.type === 'dashboard_update') {
        handleRefresh();
      }
    });

    return () => {
      wsService.disconnect();
    };
  }, [dashboardId, autoRefresh]);

  // Load initial dashboard data
  useEffect(() => {
    loadDashboardData();
  }, [dashboardId]);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const data = await VisualizationAPI.getDashboard(dashboardId);
      setDashboardData(data);
      setError(null);
      setLastUpdate(new Date());
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = useCallback(async () => {
    await loadDashboardData();
  }, [dashboardId]);

  const handleExport = useCallback(async (format: string) => {
    try {
      const exportData = await VisualizationAPI.exportDashboard(dashboardId, format);

      // Trigger download
      const blob = new Blob([exportData], { type: 'application/octet-stream' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${dashboardId}_${new Date().toISOString().split('T')[0]}.${format}`;
      link.click();
      URL.revokeObjectURL(url);

    } catch (err) {
      setError(err.message);
    }
  }, [dashboardId]);

  if (loading) {
    return (
      <div className="dashboard-loading">
        <div className="spinner" />
        <p>Loading dashboard...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dashboard-error">
        <h3>Error Loading Dashboard</h3>
        <p>{error}</p>
        <button onClick={handleRefresh}>Retry</button>
      </div>
    );
  }

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <h1>{title}</h1>
        <DashboardControls
          onRefresh={handleRefresh}
          onExport={handleExport}
          lastUpdate={lastUpdate}
          autoRefresh={autoRefresh}
        />
      </div>

      <DashboardGrid
        charts={dashboardData?.charts || {}}
        layout={dashboardData?.layout || 'grid'}
      />
    </div>
  );
};
```

---

## 🎯 **Implementation Timeline**

### **Phase 1: Core Visualizations (Weeks 1-2)**

**Week 1: Foundation**
- [ ] Base chart system and factory pattern
- [ ] Metadata visualization components
- [ ] Basic statistical charts
- [ ] Chart theming and styling

**Week 2: Interactive Features**
- [ ] Interactive filtering and drilling
- [ ] Chart annotation system
- [ ] Export functionality
- [ ] Responsive design implementation

### **Phase 2: Advanced Features (Weeks 3-4)**

**Week 3: Real-Time System**
- [ ] WebSocket integration
- [ ] Real-time data streaming
- [ ] Live chart updates
- [ ] Connection management

**Week 4: Specialized Charts**
- [ ] Network visualization
- [ ] Temporal analysis charts
- [ ] Publication relationship graphs
- [ ] Custom visualization components

### **Phase 3: Integration & Polish (Weeks 5-6)**

**Week 5: Dashboard System**
- [ ] Dashboard orchestration engine
- [ ] Layout management
- [ ] Configuration system
- [ ] Performance optimization

**Week 6: Production Ready**
- [ ] Comprehensive testing
- [ ] Documentation completion
- [ ] Performance monitoring
- [ ] Deployment optimization

---

## 📋 **Success Metrics**

### **Performance Metrics**
- **Load Time**: <2 seconds for standard dashboards
- **Interaction Response**: <100ms for chart interactions
- **Real-Time Latency**: <500ms for live updates
- **Memory Usage**: <100MB per dashboard

### **User Experience Metrics**
- **Mobile Responsiveness**: 100% functionality on mobile devices
- **Export Success**: 99%+ successful exports
- **Chart Clarity**: >4.5/5 user rating for chart readability
- **Interactive Features**: >90% feature utilization rate

### **Technical Metrics**
- **API Response Time**: <300ms for visualization data
- **WebSocket Reliability**: 99.9% connection stability
- **Cache Hit Rate**: >85% for repeated visualizations
- **Error Rate**: <1% visualization rendering errors

---

This comprehensive specification provides the foundation for creating a world-class visualization system that transforms complex biomedical data into intuitive, interactive insights for researchers and stakeholders.
