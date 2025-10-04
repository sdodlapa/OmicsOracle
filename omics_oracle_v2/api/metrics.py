"""
Prometheus Metrics for OmicsOracle API.

Provides metrics collection and exposure for monitoring with Prometheus.
"""

import logging
import time
from typing import Callable

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

# HTTP Request metrics
http_requests_total = Counter(
    "omicsoracle_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

http_request_duration_seconds = Histogram(
    "omicsoracle_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
)

http_request_size_bytes = Histogram(
    "omicsoracle_http_request_size_bytes",
    "HTTP request size in bytes",
    ["method", "endpoint"],
)

http_response_size_bytes = Histogram(
    "omicsoracle_http_response_size_bytes",
    "HTTP response size in bytes",
    ["method", "endpoint"],
)

# Agent execution metrics
agent_executions_total = Counter(
    "omicsoracle_agent_executions_total",
    "Total agent executions",
    ["agent", "status"],
)

agent_execution_duration_seconds = Histogram(
    "omicsoracle_agent_execution_duration_seconds",
    "Agent execution duration in seconds",
    ["agent"],
)

# Workflow metrics
workflow_executions_total = Counter(
    "omicsoracle_workflow_executions_total",
    "Total workflow executions",
    ["workflow_type", "status"],
)

workflow_duration_seconds = Histogram(
    "omicsoracle_workflow_duration_seconds",
    "Workflow execution duration in seconds",
    ["workflow_type"],
)

# Batch job metrics
batch_jobs_total = Counter(
    "omicsoracle_batch_jobs_total",
    "Total batch jobs",
    ["status"],
)

batch_job_workflows = Histogram(
    "omicsoracle_batch_job_workflows",
    "Number of workflows per batch job",
)

# WebSocket metrics
websocket_connections_total = Counter(
    "omicsoracle_websocket_connections_total",
    "Total WebSocket connections",
)

websocket_active_connections = Gauge(
    "omicsoracle_websocket_active_connections",
    "Current active WebSocket connections",
)

websocket_messages_sent = Counter(
    "omicsoracle_websocket_messages_sent",
    "Total WebSocket messages sent",
    ["message_type"],
)

# Error metrics
errors_total = Counter(
    "omicsoracle_errors_total",
    "Total errors",
    ["error_type", "endpoint"],
)

# System metrics
active_requests = Gauge(
    "omicsoracle_active_requests",
    "Number of requests currently being processed",
)


class PrometheusMetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware to collect Prometheus metrics for HTTP requests.

    Tracks request counts, durations, sizes, and status codes.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and collect metrics.

        Args:
            request: Incoming request
            call_next: Next middleware/endpoint

        Returns:
            Response from the endpoint
        """
        # Skip metrics for the metrics endpoint itself
        if request.url.path == "/metrics":
            return await call_next(request)

        # Extract endpoint path (remove query params and path params)
        endpoint = self._get_endpoint_path(request.url.path)
        method = request.method

        # Track active requests
        active_requests.inc()

        # Start timing
        start_time = time.time()

        try:
            # Get request size
            request_size = int(request.headers.get("content-length", 0))
            http_request_size_bytes.labels(method=method, endpoint=endpoint).observe(request_size)

            # Process request
            response = await call_next(request)

            # Record request duration
            duration = time.time() - start_time
            http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)

            # Get response size
            response_size = int(response.headers.get("content-length", 0))
            http_response_size_bytes.labels(method=method, endpoint=endpoint).observe(response_size)

            # Record request count
            http_requests_total.labels(method=method, endpoint=endpoint, status=response.status_code).inc()

            return response

        except Exception as e:
            # Record error
            duration = time.time() - start_time
            http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)

            errors_total.labels(error_type=type(e).__name__, endpoint=endpoint).inc()

            logger.error(
                f"Error processing request {method} {endpoint}: {e}",
                exc_info=True,
            )
            raise

        finally:
            # Decrement active requests
            active_requests.dec()

    def _get_endpoint_path(self, path: str) -> str:
        """
        Extract endpoint path template from actual path.

        Args:
            path: Actual request path

        Returns:
            Endpoint path template
        """
        # Remove query parameters
        path = path.split("?")[0]

        # Common path patterns to normalize
        patterns = [
            ("/api/v1/agents/", "/api/v1/agents/{agent}"),
            ("/api/v1/workflows/", "/api/v1/workflows/{endpoint}"),
            ("/api/v1/batch/jobs/", "/api/v1/batch/jobs/{job_id}"),
            ("/ws/workflows/", "/ws/workflows/{workflow_id}"),
        ]

        for prefix, template in patterns:
            if path.startswith(prefix) and len(path) > len(prefix):
                return template

        return path


def track_agent_execution(agent_name: str, duration: float, status: str) -> None:
    """
    Track agent execution metrics.

    Args:
        agent_name: Name of the agent
        duration: Execution duration in seconds
        status: Execution status (success/failure)
    """
    agent_executions_total.labels(agent=agent_name, status=status).inc()
    agent_execution_duration_seconds.labels(agent=agent_name).observe(duration)


def track_workflow_execution(workflow_type: str, duration: float, status: str) -> None:
    """
    Track workflow execution metrics.

    Args:
        workflow_type: Type of workflow
        duration: Execution duration in seconds
        status: Execution status (success/failure)
    """
    workflow_executions_total.labels(workflow_type=workflow_type, status=status).inc()
    workflow_duration_seconds.labels(workflow_type=workflow_type).observe(duration)


def track_batch_job(status: str, workflow_count: int) -> None:
    """
    Track batch job metrics.

    Args:
        status: Job status
        workflow_count: Number of workflows in the job
    """
    batch_jobs_total.labels(status=status).inc()
    batch_job_workflows.observe(workflow_count)


def track_websocket_connection(connected: bool) -> None:
    """
    Track WebSocket connection metrics.

    Args:
        connected: True if connecting, False if disconnecting
    """
    if connected:
        websocket_connections_total.inc()
        websocket_active_connections.inc()
    else:
        websocket_active_connections.dec()


def track_websocket_message(message_type: str) -> None:
    """
    Track WebSocket message metrics.

    Args:
        message_type: Type of message sent
    """
    websocket_messages_sent.labels(message_type=message_type).inc()


def get_metrics() -> bytes:
    """
    Get Prometheus metrics in text format.

    Returns:
        Metrics in Prometheus text format
    """
    return generate_latest()


def get_metrics_content_type() -> str:
    """
    Get content type for Prometheus metrics.

    Returns:
        Content type header value
    """
    return CONTENT_TYPE_LATEST
