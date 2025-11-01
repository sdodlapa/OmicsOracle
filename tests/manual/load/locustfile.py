"""
Load testing with Locust.
Week 3 Day 5: Performance validation.
"""

from locust import HttpUser, between, task


class OmicsOracleUser(HttpUser):
    """Simulated user for load testing."""

    wait_time = between(1, 3)  # Wait 1-3 seconds between requests

    @task(3)  # 3x weight - most common query
    def search_cancer(self):
        """Search for cancer datasets."""
        self.client.post(
            "/search",
            json={
                "query": "cancer",
                "max_results": 10,
            },
        )

    @task(2)  # 2x weight - specific disease
    def search_diabetes(self):
        """Search for diabetes datasets."""
        self.client.post(
            "/search",
            json={
                "query": "diabetes",
                "max_results": 10,
            },
        )

    @task(1)  # 1x weight - GEO ID lookup
    def geo_lookup(self):
        """Direct GEO ID lookup."""
        self.client.post(
            "/search",
            json={
                "query": "GSE123456",
                "max_results": 1,
            },
        )

    def on_start(self):
        """Called when user starts."""
        # Warm up cache
        self.client.get("/health")
