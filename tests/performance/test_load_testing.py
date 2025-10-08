#!/usr/bin/env python3
"""
Load Testing Framework for OmicsOracle Web Interface

This module provides comprehensive load testing using locust.
"""

import json
import random
import time
from typing import Any, Dict, List

from locust import HttpUser, between, task


class OmicsOracleUser(HttpUser):
    """Simulated user for load testing."""

    wait_time = between(0.5, 2)  # Wait 0.5-2 seconds between requests

    def on_start(self) -> None:
        """Setup test user session."""
        self.test_queries = [
            "diabetes pancreatic beta cells",
            "cancer stem cells",
            "immune response COVID-19",
            "Alzheimer's disease neurodegeneration",
            "cardiovascular disease risk factors",
            "gene expression profiling",
            "single cell RNA sequencing",
            "protein interaction networks",
            "metabolomics analysis",
            "epigenetic modifications",
        ]

        self.client.verify = False  # Disable SSL verification for testing

    @task(3)
    def search_datasets(self) -> None:
        """Test dataset search under load."""
        query = random.choice(self.test_queries)
        max_results = random.randint(5, 20)

        try:
            with self.client.post(
                "/api/search",
                json={
                    "query": query,
                    "max_results": max_results,
                    "include_sra": False,
                },
                catch_response=True,
            ) as response:
                if response.status_code != 200:
                    response.failure(f"Search failed with status {response.status_code}: {response.text}")
                else:
                    response.success()
        except (ConnectionError, TimeoutError) as e:
            print(f"Search request error: {e}")

    @task(2)
    def ai_summarization(self) -> None:
        """Test AI summarization under load."""
        query = random.choice(self.test_queries)
        max_results = random.randint(3, 10)

        with self.client.post(
            "/api/summarize",
            json={
                "query": query,
                "max_results": max_results,
                "include_batch_summary": True,
                "include_individual_summaries": False,
            },
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"AI summarization failed with status {response.status_code}")

    @task(1)
    def visualization_api(self) -> None:
        """Test visualization endpoints under load."""
        endpoints = [
            "search-stats",
            "entity-distribution",
            "organism-distribution",
            "platform-distribution",
            "timeline-distribution",
        ]
        endpoint = random.choice(endpoints)
        query = random.choice(self.test_queries)

        with self.client.post(
            f"/api/visualization/{endpoint}",
            json={"query": query, "max_results": 20},
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"Visualization {endpoint} failed with status {response.status_code}")

    @task(4)
    def static_files(self) -> None:
        """Test static file serving under load."""
        files = [
            "/",
            "/static/dashboard.html",
            "/static/research_dashboard.html",
            "/static/index.html",
        ]
        file_path = random.choice(files)

        with self.client.get(file_path, catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Static file {file_path} failed with status {response.status_code}")

    @task(1)
    def health_check(self) -> None:
        """Test health check endpoint."""
        with self.client.get("/api/status", catch_response=True) as response:
            if response.status_code not in [
                200,
                503,
            ]:  # 503 might be expected if services unavailable
                response.failure(f"Health check failed with status {response.status_code}")


class WebSocketUser(HttpUser):
    """User class for testing WebSocket connections under load."""

    wait_time = between(2, 5)

    def __init__(self, *args, **kwargs) -> None:  # type: ignore
        """Initialize WebSocket user."""
        super().__init__(*args, **kwargs)
        self.test_messages: List[Dict[str, Any]] = []

    def on_start(self) -> None:
        """Setup WebSocket test user."""
        self.test_messages = [
            {
                "type": "search_request",
                "data": {"query": "diabetes", "max_results": 5},
            },
            {
                "type": "ai_request",
                "data": {"query": "cancer", "max_results": 3},
            },
            {"type": "ping", "data": {}},
        ]

    @task
    def websocket_communication(self) -> None:
        """Test WebSocket communication patterns."""
        # Note: This is a simplified WebSocket test
        # For full WebSocket load testing, we'd need websocket-specific tools
        # This is a placeholder for now
        time.sleep(0.1)  # Simulate some work


if __name__ == "__main__":
    # This allows running locust programmatically
    print("🔥 Starting Locust Load Testing")
    print("Run: locust -f tests/performance/test_load_testing.py --host=http://localhost:8000")
    print("Then open: http://localhost:8089")
