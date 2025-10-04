#!/usr/bin/env python3
"""
Real-time Pipeline Monitoring Integration Test

This test validates that monitoring systems can observe and track:
1. Pipeline state changes
2. Query processing progress
3. Error detection and handling
4. Performance metrics collection
5. WebSocket communication
"""

import asyncio
import json
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add project root to path
from omics_oracle.monitoring.api_monitor import APIMonitoringMiddleware
from omics_oracle.monitoring.pipeline_monitor import PipelineMonitor
from omics_oracle.monitoring.websocket_monitor import WebSocketMonitor


class TestRealTimeMonitoring:
    """Tests for real-time monitoring integration."""

    @pytest.fixture
    def mock_pipeline(self):
        """Mock pipeline for monitoring tests."""
        pipeline = MagicMock()
        pipeline._active_queries = {}
        pipeline._query_counter = 0
        return pipeline

    def test_pipeline_monitor_initialization(self):
        """Test pipeline monitor initialization."""
        monitor = PipelineMonitor()
        assert monitor is not None
        assert hasattr(monitor, "events")
        assert hasattr(monitor, "event_types")
        assert isinstance(monitor.events, list)
        assert isinstance(monitor.event_types, set)
        assert monitor.query_count == 0
        assert monitor.error_count == 0

    def test_pipeline_monitor_query_tracking(self, mock_pipeline):
        """Test query event tracking."""
        monitor = PipelineMonitor()

        # Simulate query start
        query_id = monitor.start_query("cancer RNA-seq")

        # Verify query tracking
        assert monitor.current_query_id == query_id
        assert monitor.query_count == 1

        # End query
        monitor.end_query(query_id, success=True)

        # Verify summary
        summary = monitor.get_summary()
        assert summary["total_queries"] == 1
        assert summary["success_count"] == 1

    def test_pipeline_monitor_error_tracking(self):
        """Test error event tracking."""
        monitor = PipelineMonitor()

        # Simulate query start
        query_id = monitor.start_query("test query")

        # End query with failure
        monitor.end_query(query_id, success=False)

        # Verify error tracking
        summary = monitor.get_summary()
        assert summary["error_count"] > 0

    def test_api_monitoring_middleware_initialization(self):
        """Test API monitoring middleware initialization."""
        from fastapi import FastAPI

        app = FastAPI()

        middleware = APIMonitoringMiddleware(app, log_to_file=False)
        assert middleware is not None
        assert middleware.request_count == 0
        assert middleware.error_count == 0
        assert isinstance(middleware.endpoint_stats, dict)

    def test_api_monitoring_stats_tracking(self):
        """Test API monitoring statistics tracking."""
        from fastapi import FastAPI

        app = FastAPI()

        middleware = APIMonitoringMiddleware(app, log_to_file=False)

        # Simulate some usage
        middleware.request_count = 5
        middleware.error_count = 1

        assert middleware.request_count == 5
        assert middleware.error_count == 1

    def test_websocket_monitor_connection_tracking(self):
        """Test WebSocket connection monitoring."""
        monitor = WebSocketMonitor()

        # Simulate WebSocket connection
        client_id = "client_123"
        monitor.record_connection(client_id, timestamp=time.time())

        # Verify connection was recorded
        assert client_id in monitor.active_connections
        connection = monitor.active_connections[client_id]
        assert connection["status"] == "connected"

    def test_websocket_monitor_message_tracking(self):
        """Test WebSocket message monitoring."""
        monitor = WebSocketMonitor()

        # Setup connection first
        client_id = "client_123"
        monitor.record_connection(client_id, timestamp=time.time())

        # Simulate message
        message_data = {
            "type": "query_update",
            "query_id": "test_query_123",
            "status": "processing",
            "timestamp": time.time(),
        }

        monitor.record_message(client_id, message_data)

        # Verify message was recorded
        assert len(monitor.message_history) > 0
        recorded_message = monitor.message_history[-1]
        assert recorded_message["client_id"] == client_id
        assert recorded_message["type"] == "query_update"

    def test_monitoring_integration_with_pipeline(self, mock_pipeline):
        """Test monitoring integration with pipeline events."""
        pipeline_monitor = PipelineMonitor()
        ws_monitor = WebSocketMonitor()

        # Simulate complete query lifecycle
        query_id = "integration_test_123"
        query = "cancer RNA-seq analysis"
        client_id = "client_integration_test"

        # 1. WebSocket connection established
        ws_monitor.record_connection(client_id, timestamp=time.time())

        # 2. Query processing started
        pipeline_monitor.record_query_start(query_id, query, timestamp=time.time())

        # 3. Progress update sent via WebSocket
        ws_monitor.record_message(
            client_id,
            {
                "type": "query_progress",
                "query_id": query_id,
                "status": "searching",
                "progress": 0.3,
                "timestamp": time.time(),
            },
        )

        # 4. Query completed
        pipeline_monitor.record_query_completion(query_id, results_count=5, timestamp=time.time())

        # 5. Results sent via WebSocket
        ws_monitor.record_message(
            client_id,
            {
                "type": "query_results",
                "query_id": query_id,
                "results_count": 5,
                "timestamp": time.time(),
            },
        )

        # Verify all events were recorded correctly
        assert len(pipeline_monitor.query_events) == 2  # start + completion
        assert len(ws_monitor.message_history) == 2  # progress + results
        assert client_id in ws_monitor.active_connections

    def test_monitoring_error_scenarios(self):
        """Test monitoring during error scenarios."""
        pipeline_monitor = PipelineMonitor()
        ws_monitor = WebSocketMonitor()

        query_id = "error_test_123"
        client_id = "client_error_test"

        # Simulate error scenario
        # 1. Query starts normally
        pipeline_monitor.record_query_start(query_id, "test query", timestamp=time.time())

        # 2. Error occurs during processing
        error_msg = "External API timeout"
        pipeline_monitor.record_error(query_id, error_msg, timestamp=time.time())

        # 3. Error notification sent via WebSocket
        ws_monitor.record_connection(client_id, timestamp=time.time())
        ws_monitor.record_message(
            client_id,
            {
                "type": "query_error",
                "query_id": query_id,
                "error": error_msg,
                "timestamp": time.time(),
            },
        )

        # Verify error tracking
        assert len(pipeline_monitor.error_events) == 1
        assert pipeline_monitor.error_events[0]["error_message"] == error_msg

        error_messages = [msg for msg in ws_monitor.message_history if msg.get("type") == "query_error"]
        assert len(error_messages) == 1

    def test_monitoring_performance_metrics(self):
        """Test performance metrics collection."""
        pipeline_monitor = PipelineMonitor()

        # Simulate multiple queries for metrics
        start_time = time.time()

        for i in range(5):
            query_id = f"perf_test_{i}"

            # Record query processing
            pipeline_monitor.record_query_start(query_id, f"test query {i}", timestamp=start_time + i)
            pipeline_monitor.record_query_completion(
                query_id, results_count=10 + i, timestamp=start_time + i + 1.5
            )

        # Calculate performance metrics
        query_times = []
        for i in range(len(pipeline_monitor.query_events) // 2):
            start_event = pipeline_monitor.query_events[i * 2]
            end_event = pipeline_monitor.query_events[i * 2 + 1]
            query_time = end_event["timestamp"] - start_event["timestamp"]
            query_times.append(query_time)

        # Verify metrics
        assert len(query_times) == 5
        assert all(qt >= 1.5 for qt in query_times)  # All queries took at least 1.5s

    def test_monitoring_data_export(self):
        """Test monitoring data export functionality."""
        pipeline_monitor = PipelineMonitor()
        ws_monitor = WebSocketMonitor()

        # Generate some test data
        pipeline_monitor.record_query_start("export_test", "test query", timestamp=time.time())
        ws_monitor.record_connection("export_client", timestamp=time.time())

        # Test data export
        pipeline_data = pipeline_monitor.export_data()
        ws_data = ws_monitor.export_data()

        # Verify exported data structure
        assert isinstance(pipeline_data, dict)
        assert "query_events" in pipeline_data
        assert "error_events" in pipeline_data

        assert isinstance(ws_data, dict)
        assert "active_connections" in ws_data
        assert "message_history" in ws_data

    def test_monitoring_real_time_updates(self):
        """Test real-time monitoring updates."""
        monitor = PipelineMonitor()

        # Test that monitor can provide real-time status
        status = monitor.get_current_status()
        assert isinstance(status, dict)
        assert "active_queries" in status
        assert "total_queries" in status
        assert "error_count" in status

        # Add some data and verify status updates
        monitor.record_query_start("realtime_test", "test", timestamp=time.time())
        updated_status = monitor.get_current_status()

        assert updated_status["total_queries"] > status["total_queries"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
