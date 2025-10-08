#!/usr/bin/env python3
"""
Simple Load Testing for OmicsOracle Web Interface
"""

import random

from locust import HttpUser, between, task


class SimpleOmicsUser(HttpUser):
    """Simplified user for load testing."""

    wait_time = between(0.1, 1)  # Very short wait time

    def on_start(self) -> None:
        """Setup test user session."""
        self.test_queries = [
            "diabetes",
            "cancer",
            "COVID-19",
            "Alzheimer",
            "heart disease",
        ]

    @task(5)
    def health_check(self) -> None:
        """Test health check endpoint frequently."""
        self.client.get("/api/status")

    @task(3)
    def search_datasets(self) -> None:
        """Test dataset search."""
        query = random.choice(self.test_queries)
        self.client.post(
            "/api/search",
            json={"query": query, "max_results": 5, "include_sra": False},
        )

    @task(2)
    def get_homepage(self) -> None:
        """Test homepage loading."""
        self.client.get("/")

    @task(1)
    def ai_summarization(self) -> None:
        """Test AI summarization."""
        query = random.choice(self.test_queries)
        self.client.post(
            "/api/summarize",
            json={
                "query": query,
                "max_results": 3,
                "include_batch_summary": True,
                "include_individual_summaries": False,
            },
        )


if __name__ == "__main__":
    print("🔥 Simple Load Test")
    print("Run: locust -f tests/performance/simple_load_test.py --host=http://localhost:8000")
