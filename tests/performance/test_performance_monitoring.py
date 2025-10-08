#!/usr/bin/env python3
"""
Performance Monitoring and Profiling for OmicsOracle

This module provides real-time performance monitoring during tests.
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp
import psutil

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Monitor system performance during tests."""

    def __init__(self):
        self.metrics: Dict[str, List[float]] = {
            "cpu_usage": [],
            "memory_usage": [],
            "response_times": [],
            "disk_io": [],
            "network_io": [],
        }
        self.request_count = 0
        self.error_count = 0
        self.start_time: Optional[float] = None
        self.monitoring = False

    async def start_monitoring(self) -> None:
        """Start performance monitoring."""
        self.start_time = time.time()
        self.monitoring = True
        self.monitor_task = asyncio.create_task(self._collect_metrics())
        logger.info("Performance monitoring started")

    async def stop_monitoring(self) -> Dict[str, Any]:
        """Stop monitoring and return results."""
        self.monitoring = False
        if hasattr(self, "monitor_task"):
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass

        total_time = time.time() - (self.start_time or time.time())
        logger.info(f"Performance monitoring stopped after {total_time:.2f} seconds")

        return self._generate_report()

    async def _collect_metrics(self) -> None:
        """Continuously collect system metrics."""
        while self.monitoring:
            try:
                # CPU and Memory metrics
                cpu_percent = psutil.cpu_percent(interval=None)
                memory_info = psutil.virtual_memory()

                self.metrics["cpu_usage"].append(cpu_percent)
                self.metrics["memory_usage"].append(memory_info.percent)

                # Disk I/O metrics
                disk_io = psutil.disk_io_counters()
                if disk_io:
                    self.metrics["disk_io"].append(disk_io.read_bytes + disk_io.write_bytes)

                # Network I/O metrics
                network_io = psutil.net_io_counters()
                if network_io:
                    self.metrics["network_io"].append(network_io.bytes_sent + network_io.bytes_recv)

                await asyncio.sleep(1)  # Collect every second

            except Exception as e:
                logger.error(f"Error collecting metrics: {e}")
                await asyncio.sleep(1)

    def record_request(self, response_time: float, success: bool = True) -> None:
        """Record a request and its response time."""
        self.metrics["response_times"].append(response_time)
        self.request_count += 1
        if not success:
            self.error_count += 1

    def _generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        total_time = time.time() - (self.start_time or time.time())

        report = {
            "summary": {
                "total_duration": total_time,
                "total_requests": self.request_count,
                "total_errors": self.error_count,
                "error_rate": (self.error_count / max(self.request_count, 1)) * 100,
                "requests_per_second": self.request_count / max(total_time, 1),
                "timestamp": datetime.now().isoformat(),
            },
            "cpu_metrics": self._analyze_metric("cpu_usage"),
            "memory_metrics": self._analyze_metric("memory_usage"),
            "response_time_metrics": self._analyze_metric("response_times"),
            "recommendations": self._generate_recommendations(),
        }

        return report

    def _analyze_metric(self, metric_name: str) -> Dict[str, float]:
        """Analyze a specific metric."""
        values = self.metrics.get(metric_name, [])
        if not values:
            return {"avg": 0, "min": 0, "max": 0, "p95": 0, "p99": 0}

        sorted_values = sorted(values)
        length = len(sorted_values)

        return {
            "avg": sum(values) / length,
            "min": min(values),
            "max": max(values),
            "p50": sorted_values[int(length * 0.5)],
            "p95": sorted_values[int(length * 0.95)],
            "p99": sorted_values[int(length * 0.99)],
            "samples": length,
        }

    def _generate_recommendations(self) -> List[str]:
        """Generate performance recommendations based on metrics."""
        recommendations = []

        # CPU recommendations
        cpu_avg = sum(self.metrics["cpu_usage"]) / max(len(self.metrics["cpu_usage"]), 1)
        if cpu_avg > 80:
            recommendations.append(
                "High CPU usage detected. Consider optimizing algorithms or scaling horizontally."
            )
        elif cpu_avg < 20:
            recommendations.append("Low CPU usage - system can likely handle more load.")

        # Memory recommendations
        memory_avg = sum(self.metrics["memory_usage"]) / max(len(self.metrics["memory_usage"]), 1)
        if memory_avg > 85:
            recommendations.append(
                "High memory usage detected. Check for memory leaks or increase available memory."
            )

        # Response time recommendations
        if self.metrics["response_times"]:
            response_avg = sum(self.metrics["response_times"]) / len(self.metrics["response_times"])
            if response_avg > 5.0:
                recommendations.append(
                    "High response times detected. Consider caching, database optimization, or code profiling."
                )
            elif response_avg < 0.5:
                recommendations.append("Excellent response times - system is performing well.")

        # Error rate recommendations
        error_rate = (self.error_count / max(self.request_count, 1)) * 100
        if error_rate > 5:
            recommendations.append("High error rate detected. Check logs and fix failing endpoints.")
        elif error_rate == 0:
            recommendations.append("No errors detected - excellent system stability.")

        return recommendations


class PerformanceBenchmarks:
    """Automated performance benchmarks."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.monitor = PerformanceMonitor()

    async def run_response_time_benchmark(self) -> Dict[str, Any]:
        """Test API response times under normal load."""
        endpoints = [
            ("/api/status/health", "GET", {}),
            ("/api/search", "POST", {"query": "diabetes", "max_results": 10}),
            (
                "/api/ai/summarize",
                "POST",
                {"query": "cancer", "max_results": 5},
            ),
            (
                "/api/visualization/search-stats",
                "POST",
                {"query": "heart disease", "max_results": 15},
            ),
            ("/", "GET", {}),
        ]

        results = {}

        async with aiohttp.ClientSession() as session:
            for endpoint, method, data in endpoints:
                response_times = []

                # Test each endpoint 10 times
                for _ in range(10):
                    start_time = time.time()

                    try:
                        if method == "GET":
                            async with session.get(f"{self.base_url}{endpoint}") as response:
                                await response.text()
                                success = response.status == 200
                        else:
                            async with session.post(f"{self.base_url}{endpoint}", json=data) as response:
                                await response.text()
                                success = response.status == 200

                        response_time = time.time() - start_time
                        response_times.append(response_time)
                        self.monitor.record_request(response_time, success)

                    except Exception as e:
                        response_time = time.time() - start_time
                        response_times.append(response_time)
                        self.monitor.record_request(response_time, False)
                        logger.error(f"Error testing {endpoint}: {e}")

                if response_times:
                    results[f"{method} {endpoint}"] = {
                        "avg_response_time": sum(response_times) / len(response_times),
                        "min_response_time": min(response_times),
                        "max_response_time": max(response_times),
                        "samples": len(response_times),
                    }

        return results

    async def run_concurrent_users_test(self, max_users: int = 20) -> Dict[str, Any]:
        """Test system with concurrent users."""
        results = {}

        await self.monitor.start_monitoring()

        try:
            # Test with increasing concurrent users
            for user_count in [1, 5, 10, 15, max_users]:
                logger.info(f"Testing with {user_count} concurrent users")

                # Create concurrent tasks
                tasks = []
                for _ in range(user_count):
                    task = asyncio.create_task(self._simulate_user_session())
                    tasks.append(task)

                # Wait for all tasks to complete
                start_time = time.time()
                await asyncio.gather(*tasks, return_exceptions=True)
                duration = time.time() - start_time

                results[f"{user_count}_users"] = {
                    "duration": duration,
                    "requests_per_second": (user_count * 5) / duration,  # Assuming 5 requests per user
                    "concurrent_users": user_count,
                }

                # Brief pause between tests
                await asyncio.sleep(2)

        finally:
            monitoring_results = await self.monitor.stop_monitoring()
            results["monitoring"] = monitoring_results

        return results

    async def _simulate_user_session(self) -> None:
        """Simulate a typical user session."""
        async with aiohttp.ClientSession() as session:
            # Typical user workflow
            actions = [
                ("GET", "/", {}),
                (
                    "POST",
                    "/api/search",
                    {"query": "diabetes", "max_results": 10},
                ),
                (
                    "POST",
                    "/api/ai/summarize",
                    {"query": "cancer", "max_results": 5},
                ),
                ("GET", "/static/dashboard.html", {}),
                (
                    "POST",
                    "/api/visualization/entity-distribution",
                    {"query": "immune", "max_results": 20},
                ),
            ]

            for method, endpoint, data in actions:
                try:
                    start_time = time.time()

                    if method == "GET":
                        async with session.get(f"{self.base_url}{endpoint}") as response:
                            await response.text()
                            success = response.status == 200
                    else:
                        async with session.post(f"{self.base_url}{endpoint}", json=data) as response:
                            await response.text()
                            success = response.status == 200

                    response_time = time.time() - start_time
                    self.monitor.record_request(response_time, success)

                    # Brief pause between requests (simulate user thinking time)
                    await asyncio.sleep(0.5)

                except Exception as e:
                    response_time = time.time() - start_time
                    self.monitor.record_request(response_time, False)
                    logger.error(f"Error in user session {endpoint}: {e}")

    async def save_results(
        self,
        results: Dict[str, Any],
        filename: str = "performance_results.json",
    ) -> None:
        """Save performance results to file."""
        results_file = Path(__file__).parent.parent.parent / filename

        with open(results_file, "w") as f:
            json.dump(results, f, indent=2, default=str)

        logger.info(f"Performance results saved to {results_file}")


async def main():
    """Run performance benchmarks."""
    print("🏃‍♂️ Running Performance Benchmarks")
    print("=" * 50)

    benchmarks = PerformanceBenchmarks()

    # Run response time tests
    print("Testing API response times...")
    response_results = await benchmarks.run_response_time_benchmark()

    # Run concurrent users test
    print("Testing concurrent users...")
    concurrent_results = await benchmarks.run_concurrent_users_test()

    # Combine results
    all_results = {
        "response_time_tests": response_results,
        "concurrent_user_tests": concurrent_results,
        "test_timestamp": datetime.now().isoformat(),
    }

    # Save results
    await benchmarks.save_results(all_results)

    print("\n📊 Performance Test Summary:")
    print(f"Response time tests completed for {len(response_results)} endpoints")
    print(f"Concurrent user tests completed")
    print("Results saved to performance_results.json")


if __name__ == "__main__":
    asyncio.run(main())
