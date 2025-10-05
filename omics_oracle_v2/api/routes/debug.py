"""
Debug Dashboard API Routes

Provides endpoints for accessing request traces and debugging information.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse, PlainTextResponse

from omics_oracle_v2.tracing import RequestTrace, RequestTracer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/debug", tags=["Debug"])


@router.get("/traces", response_model=List[RequestTrace], summary="List All Traces")
async def list_traces(
    limit: int = Query(default=50, ge=1, le=1000, description="Maximum traces to return"),
    success_only: bool = Query(default=False, description="Only show successful traces"),
    failed_only: bool = Query(default=False, description="Only show failed traces"),
):
    """
    List all request traces in the system.

    Useful for debugging and monitoring query execution.
    """
    traces = RequestTracer.get_all_traces()

    # Filter
    if success_only:
        traces = [t for t in traces if t.success]
    elif failed_only:
        traces = [t for t in traces if not t.success]

    # Sort by started_at descending (newest first)
    traces.sort(key=lambda t: t.started_at, reverse=True)

    # Limit
    traces = traces[:limit]

    return traces


@router.get("/traces/{trace_id}", response_model=RequestTrace, summary="Get Trace by ID")
async def get_trace(trace_id: str):
    """
    Get detailed information about a specific trace.

    Shows complete event timeline and all metadata.
    """
    trace = RequestTracer.get_trace(trace_id)

    if not trace:
        raise HTTPException(status_code=404, detail=f"Trace {trace_id} not found")

    return trace


@router.get("/traces/{trace_id}/timeline", response_class=PlainTextResponse, summary="Get Trace Timeline")
async def get_trace_timeline(trace_id: str):
    """
    Get a formatted timeline view of a trace.

    Returns plain text with visual timeline of events.
    """
    try:
        timeline = RequestTracer.export_trace(trace_id, format="timeline")
        return timeline
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/traces/{trace_id}/export", response_class=PlainTextResponse, summary="Export Trace JSON")
async def export_trace(trace_id: str):
    """
    Export complete trace data as JSON.

    Useful for saving traces for later analysis.
    """
    try:
        export_data = RequestTracer.export_trace(trace_id, format="json")
        return export_data
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/dashboard", response_class=HTMLResponse, summary="Debug Dashboard")
async def debug_dashboard():
    """
    Interactive debug dashboard for viewing traces.

    Shows:
    - Recent traces
    - Success/failure rates
    - Performance metrics
    - Event timelines
    """
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>OmicsOracle Debug Dashboard</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0;
                padding: 20px;
                background: #f5f5f5;
            }
            .container {
                max-width: 1400px;
                margin: 0 auto;
            }
            h1 {
                color: #333;
                border-bottom: 3px solid #667eea;
                padding-bottom: 10px;
            }
            .stats {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin: 20px 0;
            }
            .stat-card {
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .stat-card h3 {
                margin: 0 0 10px 0;
                color: #666;
                font-size: 14px;
            }
            .stat-card .value {
                font-size: 32px;
                font-weight: bold;
                color: #667eea;
            }
            .traces {
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                margin-top: 20px;
            }
            .trace-item {
                border-bottom: 1px solid #eee;
                padding: 15px 0;
                cursor: pointer;
            }
            .trace-item:hover {
                background: #f9f9f9;
            }
            .trace-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 10px;
            }
            .trace-id {
                font-family: monospace;
                background: #f0f0f0;
                padding: 2px 6px;
                border-radius: 3px;
                font-size: 12px;
            }
            .trace-status {
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
            }
            .trace-status.success {
                background: #d4edda;
                color: #155724;
            }
            .trace-status.failed {
                background: #f8d7da;
                color: #721c24;
            }
            .trace-query {
                font-size: 14px;
                color: #333;
                margin-bottom: 5px;
            }
            .trace-meta {
                font-size: 12px;
                color: #666;
            }
            .refresh-btn {
                background: #667eea;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 14px;
            }
            .refresh-btn:hover {
                background: #5568d3;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔍 OmicsOracle Debug Dashboard</h1>

            <div class="stats" id="stats">
                <div class="stat-card">
                    <h3>Total Traces</h3>
                    <div class="value" id="total-traces">-</div>
                </div>
                <div class="stat-card">
                    <h3>Successful</h3>
                    <div class="value" id="successful-traces">-</div>
                </div>
                <div class="stat-card">
                    <h3>Failed</h3>
                    <div class="value" id="failed-traces">-</div>
                </div>
                <div class="stat-card">
                    <h3>Avg Duration</h3>
                    <div class="value" id="avg-duration">-</div>
                </div>
            </div>

            <div style="margin: 20px 0;">
                <button class="refresh-btn" onclick="loadTraces()">🔄 Refresh</button>
            </div>

            <div class="traces">
                <h2>Recent Traces</h2>
                <div id="traces-list">Loading...</div>
            </div>
        </div>

        <script>
            async function loadTraces() {
                try {
                    const response = await fetch('/debug/traces?limit=50');
                    const traces = await response.json();

                    // Update stats
                    document.getElementById('total-traces').textContent = traces.length;
                    const successful = traces.filter(t => t.success).length;
                    const failed = traces.filter(t => !t.success).length;
                    document.getElementById('successful-traces').textContent = successful;
                    document.getElementById('failed-traces').textContent = failed;

                    const avgDuration = traces.reduce((sum, t) => sum + (t.total_duration_ms || 0), 0) / traces.length;
                    document.getElementById('avg-duration').textContent = avgDuration ? `${(avgDuration/1000).toFixed(2)}s` : '-';

                    // Update traces list
                    const tracesList = document.getElementById('traces-list');
                    if (traces.length === 0) {
                        tracesList.innerHTML = '<p>No traces yet. Execute a workflow to see traces here.</p>';
                        return;
                    }

                    tracesList.innerHTML = traces.map(trace => `
                        <div class="trace-item" onclick="viewTrace('${trace.trace_id}')">
                            <div class="trace-header">
                                <span class="trace-id">${trace.trace_id}</span>
                                <span class="trace-status ${trace.success ? 'success' : 'failed'}">
                                    ${trace.success ? '✅ SUCCESS' : '❌ FAILED'}
                                </span>
                            </div>
                            <div class="trace-query">${trace.query}</div>
                            <div class="trace-meta">
                                ${trace.workflow_type} •
                                ${trace.total_duration_ms ? (trace.total_duration_ms/1000).toFixed(2) + 's' : 'In progress'} •
                                ${trace.total_events} events •
                                ${trace.datasets_found} datasets found •
                                ${new Date(trace.started_at).toLocaleString()}
                            </div>
                        </div>
                    `).join('');

                } catch (error) {
                    document.getElementById('traces-list').innerHTML =
                        `<p style="color: red;">Error loading traces: ${error.message}</p>`;
                }
            }

            function viewTrace(traceId) {
                window.open(`/debug/traces/${traceId}/timeline`, '_blank');
            }

            // Load traces on page load
            loadTraces();

            // Auto-refresh every 5 seconds
            setInterval(loadTraces, 5000);
        </script>
    </body>
    </html>
    """

    return HTMLResponse(content=html_content)


@router.post("/traces/clear", summary="Clear Old Traces")
async def clear_old_traces(max_age_hours: int = Query(default=24, ge=1, le=168)):
    """
    Clear traces older than specified hours.

    Helps manage memory by removing old trace data.
    """
    RequestTracer.clear_old_traces(max_age_hours)

    return {"message": f"Cleared traces older than {max_age_hours} hours"}
