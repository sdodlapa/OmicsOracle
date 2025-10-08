#!/usr/bimport asyncio
import json
import time
from datetime import datetime

import httpxpython3

"""
Phase 4 Day 8: End-to-End Testing Suite

Comprehensive E2E tests for the complete OmicsOracle workflow.
Tests the full user journey from registration to analysis export.
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Any, Dict, List

import httpx


class Colors:
    """ANSI color codes for terminal output."""

    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


class E2ETestRunner:
    """End-to-End Test Runner for OmicsOracle."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.token = None
        self.user_data = None
        self.test_results = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "tests": [],
        }

    def log(self, message: str, color: str = Colors.RESET):
        """Print colored log message."""
        print(f"{color}{message}{Colors.RESET}")

    def test_result(self, name: str, passed: bool, message: str = "", duration: float = 0):
        """Record test result."""
        self.test_results["total"] += 1
        if passed:
            self.test_results["passed"] += 1
            icon = "[PASS]"
            color = Colors.GREEN
        else:
            self.test_results["failed"] += 1
            icon = "[FAIL]"
            color = Colors.RED

        self.test_results["tests"].append(
            {"name": name, "passed": passed, "message": message, "duration_ms": duration * 1000}
        )

        self.log(f"{icon} {name}", color)
        if message:
            self.log(f"   {message}", Colors.YELLOW)

    async def test_1_server_health(self):
        """Test 1: Server Health Check."""
        self.log(f"\n{Colors.BOLD}Test 1: Server Health Check{Colors.RESET}")

        start = time.time()
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/api/analytics/health")

            if response.status_code == 200:
                data = response.json()
                self.test_result(
                    "Server Health",
                    True,
                    f"Status: {data.get('status', 'unknown')}",
                    time.time() - start,
                )
                return True
            else:
                self.test_result(
                    "Server Health", False, f"Status: {response.status_code}", time.time() - start
                )
                return False

        except Exception as e:
            self.test_result("Server Health", False, str(e), time.time() - start)
            return False

    async def test_2_user_registration(self):
        """Test 2: User Registration."""
        self.log(f"\n{Colors.BOLD}Test 2: User Registration{Colors.RESET}")

        # Generate unique test user
        timestamp = int(time.time())
        test_user = {
            "full_name": f"Test User {timestamp}",
            "email": f"test{timestamp}@omicsoracle.com",
            "password": "TestPass123!",
        }

        start = time.time()
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{self.base_url}/api/auth/register", json=test_user)

            if response.status_code == 201:
                data = response.json()
                self.user_data = test_user
                self.test_result(
                    "User Registration", True, f"User: {test_user['email']}", time.time() - start
                )
                return True
            else:
                self.test_result(
                    "User Registration",
                    False,
                    f"Status: {response.status_code} - {response.text[:100]}",
                    time.time() - start,
                )
                return False

        except Exception as e:
            self.test_result("User Registration", False, str(e), time.time() - start)
            return False

    async def test_3_user_login(self):
        """Test 3: User Login and Token Acquisition."""
        self.log(f"\n{Colors.BOLD}Test 3: User Login{Colors.RESET}")

        if not self.user_data:
            self.test_result("User Login", False, "No user data from registration")
            return False

        start = time.time()
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/auth/login",
                    json={
                        "email": self.user_data["email"],
                        "password": self.user_data["password"],
                    },
                )

            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                if self.token:
                    self.test_result("User Login", True, "Token acquired", time.time() - start)
                    return True
                else:
                    self.test_result("User Login", False, "No token in response", time.time() - start)
                    return False
            else:
                self.test_result("User Login", False, f"Status: {response.status_code}", time.time() - start)
                return False

        except Exception as e:
            self.test_result("User Login", False, str(e), time.time() - start)
            return False

    async def test_4_get_user_profile(self):
        """Test 4: Get Current User Profile."""
        self.log(f"\n{Colors.BOLD}Test 4: User Profile{Colors.RESET}")

        if not self.token:
            self.test_result("User Profile", False, "No auth token")
            return False

        start = time.time()
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/auth/me", headers={"Authorization": f"Bearer {self.token}"}
                )

            if response.status_code == 200:
                data = response.json()
                self.test_result("User Profile", True, f"Email: {data.get('email')}", time.time() - start)
                return True
            else:
                self.test_result(
                    "User Profile", False, f"Status: {response.status_code}", time.time() - start
                )
                return False

        except Exception as e:
            self.test_result("User Profile", False, str(e), time.time() - start)
            return False

    async def test_5_query_agent(self):
        """Test 5: Query Agent - Entity Extraction."""
        self.log(f"\n{Colors.BOLD}Test 5: Query Agent{Colors.RESET}")

        if not self.token:
            self.test_result("Query Agent", False, "No auth token")
            return False

        query = "breast cancer gene expression in human"
        start = time.time()

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/agents/query",
                    json={"query": query},
                    headers={"Authorization": f"Bearer {self.token}"},
                )

            if response.status_code == 200:
                data = response.json()
                entities = data.get("entities", [])
                self.test_result(
                    "Query Agent", True, f"Extracted {len(entities)} entities", time.time() - start
                )
                return True
            else:
                self.test_result("Query Agent", False, f"Status: {response.status_code}", time.time() - start)
                return False

        except Exception as e:
            self.test_result("Query Agent", False, str(e), time.time() - start)
            return False

    async def test_6_search_agent(self):
        """Test 6: Search Agent - Dataset Discovery."""
        self.log(f"\n{Colors.BOLD}Test 6: Search Agent{Colors.RESET}")

        search_terms = ["breast cancer", "gene expression"]
        start = time.time()

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/agents/search",
                    json={"search_terms": search_terms, "max_results": 5, "enable_semantic": False},
                )

            if response.status_code == 200:
                data = response.json()
                datasets = data.get("datasets", [])
                self.test_result("Search Agent", True, f"Found {len(datasets)} datasets", time.time() - start)
                # Store first dataset for analysis test
                self.search_results = datasets
                return True
            else:
                self.test_result(
                    "Search Agent", False, f"Status: {response.status_code}", time.time() - start
                )
                return False

        except Exception as e:
            self.test_result("Search Agent", False, str(e), time.time() - start)
            return False

    async def test_7_data_agent(self):
        """Test 7: Data Agent - Quality Validation."""
        self.log(f"\n{Colors.BOLD}Test 7: Data Agent{Colors.RESET}")

        if not hasattr(self, "search_results") or not self.search_results:
            self.test_result("Data Agent", False, "No search results available")
            return False

        if not self.token:
            self.test_result("Data Agent", False, "No auth token")
            return False

        # Get first dataset ID
        dataset_ids = [ds["geo_id"] for ds in self.search_results[:3]]
        start = time.time()

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/agents/data",
                    json={"dataset_ids": dataset_ids},
                    headers={"Authorization": f"Bearer {self.token}"},
                )

            if response.status_code == 200:
                data = response.json()
                validated = data.get("validated_datasets", [])
                self.test_result(
                    "Data Agent", True, f"Validated {len(validated)} datasets", time.time() - start
                )
                return True
            else:
                self.test_result("Data Agent", False, f"Status: {response.status_code}", time.time() - start)
                return False

        except Exception as e:
            self.test_result("Data Agent", False, str(e), time.time() - start)
            return False

    async def test_8_analysis_agent_no_openai(self):
        """Test 8: Analysis Agent (without OpenAI - expects 503)."""
        self.log(f"\n{Colors.BOLD}Test 8: Analysis Agent{Colors.RESET}")

        if not hasattr(self, "search_results") or not self.search_results:
            self.test_result("Analysis Agent", False, "No search results available")
            return False

        start = time.time()

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/agents/analyze",
                    json={
                        "datasets": self.search_results[:1],
                        "query": "breast cancer gene expression",
                        "max_datasets": 1,
                    },
                )

            # Expect 503 if no OpenAI key, or 200 if key is set
            if response.status_code == 503:
                self.test_result(
                    "Analysis Agent",
                    True,
                    "Expected 503 (no OpenAI key configured)",
                    time.time() - start,
                )
                return True
            elif response.status_code == 200:
                data = response.json()
                self.test_result("Analysis Agent", True, f"Analysis generated", time.time() - start)
                return True
            else:
                self.test_result(
                    "Analysis Agent", False, f"Unexpected status: {response.status_code}", time.time() - start
                )
                return False

        except Exception as e:
            self.test_result("Analysis Agent", False, str(e), time.time() - start)
            return False

    async def test_9_protected_route(self):
        """Test 9: Protected Route Access Control."""
        self.log(f"\n{Colors.BOLD}Test 9: Protected Route Access{Colors.RESET}")

        start = time.time()

        # Test without token (should fail)
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/api/auth/me")

            if response.status_code == 401:
                self.test_result(
                    "Protected Route (no token)",
                    True,
                    "Correctly rejected unauthorized access",
                    time.time() - start,
                )
            else:
                self.test_result(
                    "Protected Route (no token)",
                    False,
                    f"Expected 401, got {response.status_code}",
                    time.time() - start,
                )

        except Exception as e:
            self.test_result("Protected Route (no token)", False, str(e), time.time() - start)

        # Test with token (should succeed)
        start2 = time.time()
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/auth/me", headers={"Authorization": f"Bearer {self.token}"}
                )

            if response.status_code == 200:
                self.test_result("Protected Route (with token)", True, "Access granted", time.time() - start2)
                return True
            else:
                self.test_result(
                    "Protected Route (with token)",
                    False,
                    f"Status: {response.status_code}",
                    time.time() - start2,
                )
                return False

        except Exception as e:
            self.test_result("Protected Route (with token)", False, str(e), time.time() - start2)
            return False

    async def test_10_performance_benchmarks(self):
        """Test 10: Performance Benchmarks."""
        self.log(f"\n{Colors.BOLD}Test 10: Performance Benchmarks{Colors.RESET}")

        benchmarks = []

        # Benchmark 1: Health check (should be very fast)
        start = time.time()
        try:
            async with httpx.AsyncClient() as client:
                await client.get(f"{self.base_url}/api/analytics/health")
            health_time = (time.time() - start) * 1000
            benchmarks.append(("Health Check", health_time, 200))
        except Exception as e:
            self.log(f"   Health benchmark failed: {e}", Colors.RED)

        # Benchmark 2: Auth check (should be fast)
        if self.token:
            start = time.time()
            try:
                async with httpx.AsyncClient() as client:
                    await client.get(
                        f"{self.base_url}/api/auth/me",
                        headers={"Authorization": f"Bearer {self.token}"},
                    )
                auth_time = (time.time() - start) * 1000
                benchmarks.append(("Auth Check", auth_time, 500))
            except Exception as e:
                self.log(f"   Auth benchmark failed: {e}", Colors.RED)

        # Benchmark 3: Query processing
        start = time.time()
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{self.base_url}/api/agents/query",
                    json={"query": "diabetes"},
                    headers={"Authorization": f"Bearer {self.token}"},
                )
            query_time = (time.time() - start) * 1000
            benchmarks.append(("Query Agent", query_time, 1000))
        except Exception as e:
            self.log(f"   Query benchmark failed: {e}", Colors.RED)

        # Report benchmarks
        all_passed = True
        for name, duration, threshold in benchmarks:
            passed = duration < threshold
            if not passed:
                all_passed = False
            status = "[OK]" if passed else "[SLOW]"
            self.log(f"   {status} {name}: {duration:.0f}ms (threshold: {threshold}ms)")

        self.test_result("Performance Benchmarks", all_passed, f"{len(benchmarks)} benchmarks run")
        return all_passed

    async def run_all_tests(self):
        """Run all E2E tests."""
        self.log(f"\n{Colors.BOLD}{'=' * 60}{Colors.RESET}")
        self.log(f"{Colors.BOLD}Phase 4 Day 8: End-to-End Testing{Colors.RESET}")
        self.log(f"{Colors.BOLD}{'=' * 60}{Colors.RESET}")

        start_time = time.time()

        # Run tests in sequence
        await self.test_1_server_health()
        await self.test_2_user_registration()
        await self.test_3_user_login()
        await self.test_4_get_user_profile()
        await self.test_5_query_agent()
        await self.test_6_search_agent()
        await self.test_7_data_agent()
        await self.test_8_analysis_agent_no_openai()
        await self.test_9_protected_route()
        await self.test_10_performance_benchmarks()

        total_time = time.time() - start_time

        # Print summary
        self.log(f"\n{Colors.BOLD}{'=' * 60}{Colors.RESET}")
        self.log(f"{Colors.BOLD}Test Summary{Colors.RESET}")
        self.log(f"{Colors.BOLD}{'=' * 60}{Colors.RESET}")

        self.log(f"\nTotal Tests: {self.test_results['total']}")
        self.log(f"{Colors.GREEN}Passed: {self.test_results['passed']}{Colors.RESET}")
        self.log(f"{Colors.RED}Failed: {self.test_results['failed']}{Colors.RESET}")
        self.log(f"{Colors.YELLOW}Skipped: {self.test_results['skipped']}{Colors.RESET}")
        self.log(f"\nTotal Duration: {total_time:.2f}s")

        # Calculate pass rate
        if self.test_results["total"] > 0:
            pass_rate = (self.test_results["passed"] / self.test_results["total"]) * 100
            self.log(f"Pass Rate: {pass_rate:.1f}%")

            if pass_rate >= 90:
                self.log("\n[EXCELLENT] E2E tests passing!", Colors.GREEN)
            elif pass_rate >= 70:
                self.log("\n[GOOD] Most tests passing", Colors.YELLOW)
            else:
                self.log("\n[WARNING] Needs attention - many tests failing", Colors.RED)

        # Save results
        self.save_results()

        return self.test_results

    def save_results(self):
        """Save test results to JSON file."""
        results_file = "test_phase4_day8_e2e_results.json"

        output = {
            "test_suite": "Phase 4 Day 8 - End-to-End Testing",
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total": self.test_results["total"],
                "passed": self.test_results["passed"],
                "failed": self.test_results["failed"],
                "skipped": self.test_results["skipped"],
                "pass_rate": (
                    (self.test_results["passed"] / self.test_results["total"] * 100)
                    if self.test_results["total"] > 0
                    else 0
                ),
            },
            "tests": self.test_results["tests"],
        }

        with open(results_file, "w") as f:
            json.dump(output, f, indent=2)

        self.log(f"\nResults saved to: {results_file}", Colors.BLUE)


async def main():
    """Main entry point."""
    runner = E2ETestRunner(base_url="http://localhost:8000")
    await runner.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
