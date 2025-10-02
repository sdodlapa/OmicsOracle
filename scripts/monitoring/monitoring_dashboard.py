#!/usr/bin/env python
"""
OmicsOracle Monitoring Dashboard

This script creates a simple web-based monitoring dashboard that displays
real-time status of the OmicsOracle pipeline and its components.
"""

import asyncio
import datetime
import json
import logging
import os
import sys
import threading
import time
import traceback
import webbrowser
from pathlib import Path

import requests
import uvicorn
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("monitoring_dashboard.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("monitoring_dashboard")

# Add project root to path
script_path = Path(__file__).resolve()
project_root = script_path.parent
logger.info(f"Project root: {project_root}")
# Default API URL to monitor
DEFAULT_API_URL = "http://localhost:8001"

# Create FastAPI app
app = FastAPI(title="OmicsOracle Monitoring Dashboard")

# Create templates directory if it doesn't exist
templates_dir = Path("./monitoring_templates")
templates_dir.mkdir(exist_ok=True)

# Create base template
base_template = templates_dir / "base.html"
if not base_template.exists():
    base_template.write_text(
        """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>OmicsOracle Monitoring Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        .component-status {
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 10px;
        }
        .status-healthy {
            background-color: #d4edda;
            color: #155724;
        }
        .status-warning {
            background-color: #fff3cd;
            color: #856404;
        }
        .status-error {
            background-color: #f8d7da;
            color: #721c24;
        }
        .log-container {
            height: 300px;
            overflow-y: auto;
            background-color: #f8f9fa;
            padding: 10px;
            border-radius: 5px;
            font-family: monospace;
        }
        .chart-container {
            height: 300px;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="container mt-4">
        <h1>OmicsOracle Monitoring Dashboard</h1>
        {% block content %}{% endblock %}
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/js/bootstrap.bundle.min.js"></script>
    {% block scripts %}{% endblock %}
</body>
</html>
"""
    )

# Create index template
index_template = templates_dir / "index.html"
if not index_template.exists():
    index_template.write_text(
        """
{% extends "base.html" %}

{% block content %}
<div class="row mt-4">
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <h5>System Status</h5>
            </div>
            <div class="card-body">
                <div id="system-status">Loading...</div>
                <div class="mt-3">
                    <button id="refresh-status" class="btn btn-primary btn-sm">Refresh</button>
                    <button id="run-tests" class="btn btn-outline-secondary btn-sm">Run Tests</button>
                </div>
            </div>
        </div>
    </div>

    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <h5>Component Status</h5>
            </div>
            <div class="card-body">
                <div id="component-status">Loading...</div>
            </div>
        </div>
    </div>
</div>

<div class="row mt-4">
    <div class="col-md-12">
        <div class="card">
            <div class="card-header">
                <h5>Performance Metrics</h5>
            </div>
            <div class="card-body">
                <div class="chart-container">
                    <canvas id="performanceChart"></canvas>
                </div>
            </div>
        </div>
    </div>
</div>

<div class="row mt-4">
    <div class="col-md-12">
        <div class="card">
            <div class="card-header">
                <h5>Live Logs</h5>
            </div>
            <div class="card-body">
                <div id="log-container" class="log-container">
                    <div class="text-muted">Connecting to log stream...</div>
                </div>
            </div>
        </div>
    </div>
</div>

<div class="row mt-4">
    <div class="col-md-12">
        <div class="card">
            <div class="card-header">
                <h5>Diagnostic Tools</h5>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-4">
                        <div class="card">
                            <div class="card-body">
                                <h6>Pipeline Diagnostics</h6>
                                <button id="run-pipeline-diagnostics" class="btn btn-primary btn-sm">Run Diagnostics</button>
                                <div id="pipeline-diagnostics-status" class="mt-2 small"></div>
                            </div>
                        </div>
                    </div>

                    <div class="col-md-4">
                        <div class="card">
                            <div class="card-body">
                                <h6>GEO Client Test</h6>
                                <button id="run-geo-test" class="btn btn-primary btn-sm">Run Test</button>
                                <div id="geo-test-status" class="mt-2 small"></div>
                            </div>
                        </div>
                    </div>

                    <div class="col-md-4">
                        <div class="card">
                            <div class="card-body">
                                <h6>API Endpoints Test</h6>
                                <button id="run-api-test" class="btn btn-primary btn-sm">Run Test</button>
                                <div id="api-test-status" class="mt-2 small"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<div class="row mt-4 mb-4">
    <div class="col-md-12">
        <div class="card">
            <div class="card-header">
                <h5>Recent Search Queries</h5>
            </div>
            <div class="card-body">
                <div id="recent-queries">No recent queries</div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
    // WebSocket connection
    let ws;
    let performanceChart;
    let metricsData = {
        labels: [],
        responseTime: [],
        queryCount: []
    };

    // Connect to WebSocket
    function connectWebSocket() {
        ws = new WebSocket(`ws://${window.location.host}/ws`);

        ws.onopen = function() {
            console.log('WebSocket connected');
            document.getElementById('log-container').innerHTML = '<div class="text-success">Connected to log stream</div>';
        };

        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);

            if (data.type === 'log') {
                addLogMessage(data.message, data.level);
            } else if (data.type === 'status_update') {
                updateSystemStatus(data.status);
            } else if (data.type === 'component_update') {
                updateComponentStatus(data.components);
            } else if (data.type === 'metrics_update') {
                updateMetrics(data.metrics);
            } else if (data.type === 'recent_queries') {
                updateRecentQueries(data.queries);
            } else if (data.type === 'test_result') {
                updateTestResult(data.test_type, data.result);
            }
        };

        ws.onclose = function() {
            console.log('WebSocket disconnected');
            document.getElementById('log-container').innerHTML += '<div class="text-danger">Disconnected from log stream. Reconnecting...</div>';

            // Reconnect after a delay
            setTimeout(connectWebSocket, 3000);
        };

        ws.onerror = function(error) {
            console.error('WebSocket error:', error);
            document.getElementById('log-container').innerHTML += '<div class="text-danger">WebSocket error. See console for details.</div>';
        };
    }

    // Add log message
    function addLogMessage(message, level) {
        const logContainer = document.getElementById('log-container');
        const levelClass = level === 'error' ? 'text-danger' :
                          level === 'warning' ? 'text-warning' :
                          level === 'success' ? 'text-success' : 'text-dark';

        logContainer.innerHTML += `<div class="\${levelClass}">\${message}</div>`;
        logContainer.scrollTop = logContainer.scrollHeight;
    }

    // Update system status
    function updateSystemStatus(status) {
        const statusElement = document.getElementById('system-status');
        const statusClass = status.status === 'healthy' ? 'status-healthy' :
                           status.status === 'warning' ? 'status-warning' : 'status-error';

        statusElement.innerHTML = `
            <div class="component-status \${statusClass}">
                <strong>Status:</strong> \${status.status}<br>
                <strong>Pipeline Available:</strong> \${status.pipeline_available ? 'Yes' : 'No'}<br>
                <strong>Last Updated:</strong> \${new Date(status.timestamp * 1000).toLocaleTimeString()}<br>
                <strong>Message:</strong> \${status.message}
            </div>
        `;
    }

    // Update component status
    function updateComponentStatus(components) {
        const componentElement = document.getElementById('component-status');
        let html = '';

        for (const component of components) {
            const statusClass = component.status === 'healthy' ? 'status-healthy' :
                               component.status === 'warning' ? 'status-warning' : 'status-error';

            html += `
                <div class="component-status \${statusClass}">
                    <strong>\${component.name}:</strong> \${component.status}<br>
                    <small>\${component.message}</small>
                </div>
            `;
        }

        componentElement.innerHTML = html;
    }

    // Update metrics
    function updateMetrics(metrics) {
        // Add timestamp to labels
        const time = new Date(metrics.timestamp * 1000).toLocaleTimeString();

        // Keep only the most recent 10 data points
        if (metricsData.labels.length >= 10) {
            metricsData.labels.shift();
            metricsData.responseTime.shift();
            metricsData.queryCount.shift();
        }

        metricsData.labels.push(time);
        metricsData.responseTime.push(metrics.avg_response_time);
        metricsData.queryCount.push(metrics.search_queries);

        // Update chart
        if (performanceChart) {
            performanceChart.update();
        } else {
            initChart();
        }
    }

    // Initialize chart
    function initChart() {
        const ctx = document.getElementById('performanceChart').getContext('2d');
        performanceChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: metricsData.labels,
                datasets: [
                    {
                        label: 'Avg Response Time (s)',
                        data: metricsData.responseTime,
                        borderColor: 'rgba(75, 192, 192, 1)',
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        tension: 0.1,
                        yAxisID: 'y'
                    },
                    {
                        label: 'Search Queries',
                        data: metricsData.queryCount,
                        borderColor: 'rgba(54, 162, 235, 1)',
                        backgroundColor: 'rgba(54, 162, 235, 0.2)',
                        tension: 0.1,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Response Time (s)'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        grid: {
                            drawOnChartArea: false
                        },
                        title: {
                            display: true,
                            text: 'Search Queries'
                        }
                    }
                }
            }
        });
    }

    // Update recent queries
    function updateRecentQueries(queries) {
        const queriesElement = document.getElementById('recent-queries');

        if (queries.length === 0) {
            queriesElement.innerHTML = 'No recent queries';
            return;
        }

        let html = '<div class="table-responsive"><table class="table table-sm table-striped">';
        html += '<thead><tr><th>Time</th><th>Query</th><th>Results</th><th>Time (s)</th></tr></thead><tbody>';

        for (const query of queries) {
            const time = new Date(query.timestamp * 1000).toLocaleTimeString();
            html += `
                <tr>
                    <td>\${time}</td>
                    <td>\${query.query}</td>
                    <td>\${query.total_found}</td>
                    <td>\${query.search_time.toFixed(2)}</td>
                </tr>
            `;
        }

        html += '</tbody></table></div>';
        queriesElement.innerHTML = html;
    }

    // Update test result
    function updateTestResult(testType, result) {
        let element;

        switch (testType) {
            case 'pipeline_diagnostics':
                element = document.getElementById('pipeline-diagnostics-status');
                break;
            case 'geo_test':
                element = document.getElementById('geo-test-status');
                break;
            case 'api_test':
                element = document.getElementById('api-test-status');
                break;
            default:
                return;
        }

        if (result.success) {
            element.innerHTML = `<span class="text-success">Success: \${result.message}</span>`;
        } else {
            element.innerHTML = `<span class="text-danger">Failed: \${result.message}</span>`;
        }
    }

    // Event listeners
    document.getElementById('refresh-status').addEventListener('click', function() {
        ws.send(JSON.stringify({ action: 'refresh_status' }));
        addLogMessage('Refreshing system status...', 'info');
    });

    document.getElementById('run-tests').addEventListener('click', function() {
        ws.send(JSON.stringify({ action: 'run_tests' }));
        addLogMessage('Running all tests...', 'info');
    });

    document.getElementById('run-pipeline-diagnostics').addEventListener('click', function() {
        ws.send(JSON.stringify({ action: 'run_pipeline_diagnostics' }));
        document.getElementById('pipeline-diagnostics-status').innerHTML = '<span class="text-muted">Running...</span>';
        addLogMessage('Running pipeline diagnostics...', 'info');
    });

    document.getElementById('run-geo-test').addEventListener('click', function() {
        ws.send(JSON.stringify({ action: 'run_geo_test' }));
        document.getElementById('geo-test-status').innerHTML = '<span class="text-muted">Running...</span>';
        addLogMessage('Running GEO client test...', 'info');
    });

    document.getElementById('run-api-test').addEventListener('click', function() {
        ws.send(JSON.stringify({ action: 'run_api_test' }));
        document.getElementById('api-test-status').innerHTML = '<span class="text-muted">Running...</span>';
        addLogMessage('Running API endpoints test...', 'info');
    });

    // Initialize
    window.addEventListener('load', function() {
        connectWebSocket();
    });
</script>
{% endblock %}
"""
    )

# Setup templates
templates = Jinja2Templates(directory=str(templates_dir))


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket client disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, data):
        for connection in self.active_connections:
            try:
                await connection.send_json(data)
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket: {e}")


manager = ConnectionManager()


# API client to monitor the OmicsOracle API
class APIClient:
    def __init__(self, api_url):
        self.api_url = api_url
        self.recent_queries = []

    async def get_health(self):
        try:
            response = requests.get(f"{self.api_url}/api/health", timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "status": "error",
                    "message": f"Health check failed with status code {response.status_code}",
                    "timestamp": time.time(),
                    "pipeline_available": False,
                }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Health check failed: {str(e)}",
                "timestamp": time.time(),
                "pipeline_available": False,
            }

    def get_component_status(self, health_data):
        components = []

        # Pipeline status
        pipeline_status = "healthy" if health_data.get("pipeline_available", False) else "error"
        components.append(
            {
                "name": "Pipeline",
                "status": pipeline_status,
                "message": "Pipeline is initialized and ready"
                if pipeline_status == "healthy"
                else "Pipeline not available",
            }
        )

        # Get pipeline component status if available
        pipeline_info = health_data.get("pipeline_info", {})

        # GEO client status
        geo_status = "healthy" if pipeline_info.get("geo_client_available", False) else "error"
        components.append(
            {
                "name": "GEO Client",
                "status": geo_status,
                "message": "GEO client is initialized"
                if geo_status == "healthy"
                else "GEO client not available",
            }
        )

        # Summarizer status
        summarizer_status = "healthy" if pipeline_info.get("summarizer_available", False) else "error"
        components.append(
            {
                "name": "Summarizer",
                "status": summarizer_status,
                "message": "Summarizer is initialized"
                if summarizer_status == "healthy"
                else "Summarizer not available",
            }
        )

        # NCBI email status
        ncbi_email = pipeline_info.get("ncbi_email", "Not set")
        email_status = "healthy" if ncbi_email and ncbi_email != "Not set" else "error"
        components.append(
            {
                "name": "NCBI Email",
                "status": email_status,
                "message": f"Email configured: {ncbi_email}"
                if email_status == "healthy"
                else "NCBI email not configured",
            }
        )

        # Environment info
        env_info = health_data.get("environment", {})
        entrez_email = env_info.get("entrez_email", "Not set")
        entrez_status = "healthy" if entrez_email and entrez_email != "Not set" else "error"
        components.append(
            {
                "name": "Bio.Entrez.email",
                "status": entrez_status,
                "message": f"Email configured: {entrez_email}"
                if entrez_status == "healthy"
                else "Bio.Entrez.email not configured",
            }
        )

        return components

    def get_metrics(self):
        # In a real implementation, you would collect metrics from a database or monitoring system
        # For this example, we'll generate some synthetic metrics
        return {
            "timestamp": time.time(),
            "avg_response_time": self.get_avg_response_time(),
            "search_queries": len(self.recent_queries),
            "error_rate": 0.0,  # Could be calculated from API response status codes
        }

    def get_avg_response_time(self):
        if not self.recent_queries:
            return 0.0

        total_time = sum(query.get("search_time", 0) for query in self.recent_queries)
        return total_time / len(self.recent_queries)

    def add_query(self, query_data):
        # Add a query to the recent queries list (limited to 10)
        self.recent_queries.append(query_data)
        if len(self.recent_queries) > 10:
            self.recent_queries.pop(0)

    async def run_test(self, test_type):
        """Run a test script and return the result"""
        if test_type == "pipeline_diagnostics":
            script_path = project_root / "debug_pipeline_init.py"
        elif test_type == "geo_test":
            script_path = project_root / "test_geo_client.py"
        elif test_type == "api_test":
            script_path = project_root / "test_api_endpoints.py"
        else:
            return {
                "success": False,
                "message": f"Unknown test type: {test_type}",
            }

        if not script_path.exists():
            return {
                "success": False,
                "message": f"Test script not found: {script_path}",
            }

        try:
            # Run the script
            cmd = [sys.executable, str(script_path)]
            if test_type == "api_test":
                cmd.append(self.api_url)

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()
            success = process.returncode == 0

            return {
                "success": success,
                "message": "Test completed successfully" if success else "Test failed",
                "return_code": process.returncode,
                "stdout": stdout.decode(),
                "stderr": stderr.decode(),
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error running test: {str(e)}",
            }


# Background task to monitor the API
async def monitor_api():
    api_client = APIClient(DEFAULT_API_URL)

    while True:
        try:
            # Get health status
            health_data = await api_client.get_health()

            # Get component status
            components = api_client.get_component_status(health_data)

            # Get metrics
            metrics = api_client.get_metrics()

            # Broadcast updates to all connected clients
            await manager.broadcast({"type": "status_update", "status": health_data})

            await manager.broadcast({"type": "component_update", "components": components})

            await manager.broadcast({"type": "metrics_update", "metrics": metrics})

            await manager.broadcast({"type": "recent_queries", "queries": api_client.recent_queries})

            # Log an update
            await manager.broadcast(
                {
                    "type": "log",
                    "message": f"System status updated: {health_data['status']}",
                    "level": "info",
                }
            )

        except Exception as e:
            logger.error(f"Error in API monitoring: {e}")
            logger.error(traceback.format_exc())

            # Broadcast error to clients
            await manager.broadcast(
                {
                    "type": "log",
                    "message": f"Error monitoring API: {str(e)}",
                    "level": "error",
                }
            )

        # Wait before next update
        await asyncio.sleep(30)  # Update every 30 seconds


# API routes
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)

    # Send initial log message
    await websocket.send_json(
        {
            "type": "log",
            "message": "Connected to monitoring dashboard",
            "level": "success",
        }
    )

    try:
        while True:
            # Wait for messages from the client
            data = await websocket.receive_text()
            try:
                message = json.loads(data)

                # Process client commands
                if message.get("action") == "refresh_status":
                    # Client requested a status refresh
                    api_client = APIClient(DEFAULT_API_URL)
                    health_data = await api_client.get_health()
                    components = api_client.get_component_status(health_data)

                    await websocket.send_json({"type": "status_update", "status": health_data})

                    await websocket.send_json({"type": "component_update", "components": components})

                    await websocket.send_json(
                        {
                            "type": "log",
                            "message": "Status refreshed",
                            "level": "success",
                        }
                    )

                elif message.get("action") in [
                    "run_pipeline_diagnostics",
                    "run_geo_test",
                    "run_api_test",
                ]:
                    # Run a test script
                    test_type = message.get("action").replace("run_", "")

                    api_client = APIClient(DEFAULT_API_URL)
                    result = await api_client.run_test(test_type)

                    await websocket.send_json(
                        {
                            "type": "test_result",
                            "test_type": test_type,
                            "result": result,
                        }
                    )

                    level = "success" if result["success"] else "error"
                    await websocket.send_json(
                        {
                            "type": "log",
                            "message": f"Test {test_type} completed: {result['message']}",
                            "level": level,
                        }
                    )

                elif message.get("action") == "run_tests":
                    # Run all tests
                    await websocket.send_json(
                        {
                            "type": "log",
                            "message": "Running all tests...",
                            "level": "info",
                        }
                    )

                    api_client = APIClient(DEFAULT_API_URL)

                    for test_type in [
                        "pipeline_diagnostics",
                        "geo_test",
                        "api_test",
                    ]:
                        await websocket.send_json(
                            {
                                "type": "log",
                                "message": f"Running {test_type}...",
                                "level": "info",
                            }
                        )

                        result = await api_client.run_test(test_type)

                        await websocket.send_json(
                            {
                                "type": "test_result",
                                "test_type": test_type,
                                "result": result,
                            }
                        )

                        level = "success" if result["success"] else "error"
                        await websocket.send_json(
                            {
                                "type": "log",
                                "message": f"Test {test_type} completed: {result['message']}",
                                "level": level,
                            }
                        )

            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}")
                await websocket.send_json(
                    {
                        "type": "log",
                        "message": f"Error processing command: {str(e)}",
                        "level": "error",
                    }
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket)


# Startup event
@app.on_event("startup")
async def startup_event():
    # Start API monitoring task
    asyncio.create_task(monitor_api())


def open_browser():
    """Open the dashboard in a web browser"""
    time.sleep(1)  # Wait for server to start
    webbrowser.open("http://localhost:8080")


def start_dashboard():
    """Start the monitoring dashboard"""
    # Start the server in a new thread
    thread = threading.Thread(target=open_browser)
    thread.daemon = True
    thread.start()

    # Start Uvicorn server
    uvicorn.run(app, host="0.0.0.0", port=8080)


if __name__ == "__main__":
    start_dashboard()
