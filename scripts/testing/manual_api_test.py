#!/usr/bin/env python3
"""
Manual API Testing Script for OmicsOracle v2

This script performs comprehensive manual testing of all API endpoints.
Results are saved to docs/testing/MANUAL_TESTING_RESULTS.md
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import httpx

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# API Base URL
BASE_URL = "http://localhost:8000"

# Test results
test_results = {
    "health": [],
    "auth": [],
    "agents": [],
    "workflows": [],
    "batch": [],
    "websocket": [],
    "quotas": [],
    "issues": [],
}

# Test user credentials
TEST_USER = {
    "email": "testuser@example.com",
    "password": "TestPassword123!",
    "username": "testuser",
}


class TestRunner:
    """API test runner."""

    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)
        self.token: Optional[str] = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    def log_test(self, category: str, test_name: str, status: str, notes: str = ""):
        """Log test result."""
        result = {
            "test": test_name,
            "status": status,
            "notes": notes,
            "timestamp": datetime.now().isoformat(),
        }
        test_results[category].append(result)

        emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{emoji} {category.upper()} - {test_name}: {status}")
        if notes:
            print(f"   Notes: {notes}")

    def log_issue(self, severity: str, issue: str, steps: str, expected: str, actual: str):
        """Log an issue found during testing."""
        test_results["issues"].append(
            {
                "severity": severity,
                "issue": issue,
                "steps": steps,
                "expected": expected,
                "actual": actual,
                "timestamp": datetime.now().isoformat(),
            }
        )
        print(f"\n🐛 ISSUE FOUND ({severity}):")
        print(f"   Issue: {issue}")
        print(f"   Expected: {expected}")
        print(f"   Actual: {actual}\n")

    async def test_health(self):
        """Test health endpoints."""
        print("\n" + "=" * 60)
        print("TESTING: Health & Metrics Endpoints")
        print("=" * 60 + "\n")

        # Health check
        try:
            response = await self.client.get(f"{self.base_url}/health")
            if response.status_code == 200:
                data = response.json()
                self.log_test("health", "Health Check", "PASS", f"Response: {data}")
            else:
                self.log_test("health", "Health Check", "FAIL", f"Status: {response.status_code}")
                self.log_issue(
                    "HIGH",
                    "Health check failed",
                    "GET /health",
                    "200 OK",
                    f"{response.status_code} {response.text}",
                )
        except Exception as e:
            self.log_test("health", "Health Check", "ERROR", str(e))
            self.log_issue("CRITICAL", "Health endpoint error", "GET /health", "200 OK", str(e))

        # Metrics check
        try:
            response = await self.client.get(f"{self.base_url}/metrics")
            if response.status_code == 200:
                self.log_test("health", "Metrics Endpoint", "PASS", "Prometheus metrics returned")
            else:
                self.log_test("health", "Metrics Endpoint", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("health", "Metrics Endpoint", "ERROR", str(e))

        # Root endpoint
        try:
            response = await self.client.get(f"{self.base_url}/")
            if response.status_code == 200:
                data = response.json()
                self.log_test("health", "Root Endpoint", "PASS", f"API Info: {data.get('name')}")
            else:
                self.log_test("health", "Root Endpoint", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("health", "Root Endpoint", "ERROR", str(e))

    async def test_auth(self):
        """Test authentication endpoints."""
        print("\n" + "=" * 60)
        print("TESTING: Authentication Endpoints")
        print("=" * 60 + "\n")

        # Register new user
        try:
            response = await self.client.post(f"{self.base_url}/api/v2/auth/register", json=TEST_USER)
            if response.status_code == 200:
                data = response.json()
                self.log_test("auth", "User Registration", "PASS", f"User ID: {data.get('id')}")
            elif response.status_code == 400 and "already registered" in response.text:
                self.log_test("auth", "User Registration", "PASS", "User already exists (expected)")
            else:
                self.log_test(
                    "auth",
                    "User Registration",
                    "FAIL",
                    f"Status: {response.status_code}, Response: {response.text}",
                )
                self.log_issue(
                    "HIGH",
                    "User registration failed",
                    f"POST /api/v2/auth/register with {TEST_USER}",
                    "200 OK or 400 (already exists)",
                    f"{response.status_code} {response.text}",
                )
        except Exception as e:
            self.log_test("auth", "User Registration", "ERROR", str(e))
            self.log_issue(
                "CRITICAL", "Registration endpoint error", "POST /api/v2/auth/register", "200 OK", str(e)
            )

        # Login
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v2/auth/login",
                json={
                    "email": TEST_USER["email"],
                    "password": TEST_USER["password"],
                },
            )
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.log_test("auth", "User Login", "PASS", "Token received")
            else:
                self.log_test(
                    "auth", "User Login", "FAIL", f"Status: {response.status_code}, Response: {response.text}"
                )
                self.log_issue(
                    "CRITICAL",
                    "Login failed",
                    f"POST /api/v2/auth/login with correct credentials",
                    "200 OK with access_token",
                    f"{response.status_code} {response.text}",
                )
                return  # Can't continue without token
        except Exception as e:
            self.log_test("auth", "User Login", "ERROR", str(e))
            self.log_issue("CRITICAL", "Login endpoint error", "POST /api/v2/auth/login", "200 OK", str(e))
            return

        # Get current user
        try:
            response = await self.client.get(
                f"{self.base_url}/api/v2/users/me", headers={"Authorization": f"Bearer {self.token}"}
            )
            if response.status_code == 200:
                data = response.json()
                self.log_test("auth", "Get Current User", "PASS", f"Email: {data.get('email')}")
            else:
                self.log_test("auth", "Get Current User", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("auth", "Get Current User", "ERROR", str(e))

    async def test_agents(self):
        """Test agent endpoints."""
        print("\n" + "=" * 60)
        print("TESTING: Agents API Endpoints")
        print("=" * 60 + "\n")

        if not self.token:
            print("⚠️ Skipping agent tests - no authentication token")
            return

        headers = {"Authorization": f"Bearer {self.token}"}

        # List agents
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/agents", headers=headers)
            if response.status_code == 200:
                data = response.json()
                self.log_test("agents", "List Agents", "PASS", f"Found {len(data)} agents")
            else:
                self.log_test("agents", "List Agents", "FAIL", f"Status: {response.status_code}")
                self.log_issue(
                    "CRITICAL",
                    "List agents failed",
                    "GET /api/v1/agents with auth",
                    "200 OK with agent list",
                    f"{response.status_code} {response.text}",
                )
        except Exception as e:
            self.log_test("agents", "List Agents", "ERROR", str(e))
            self.log_issue("CRITICAL", "List agents error", "GET /api/v1/agents", "200 OK", str(e))

        # Execute NER agent (if available)
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/agents/ner/execute",
                headers=headers,
                json={"text": "Aspirin is used to treat fever and pain.", "parameters": {}},
            )
            if response.status_code == 200:
                data = response.json()
                self.log_test("agents", "Execute NER Agent", "PASS", f"Task ID: {data.get('task_id')}")
            elif response.status_code == 404:
                self.log_test("agents", "Execute NER Agent", "SKIP", "NER agent not found")
            else:
                self.log_test("agents", "Execute NER Agent", "FAIL", f"Status: {response.status_code}")
                self.log_issue(
                    "HIGH",
                    "NER agent execution failed",
                    "POST /api/v1/agents/ner/execute with text",
                    "200 OK with task_id",
                    f"{response.status_code} {response.text}",
                )
        except Exception as e:
            self.log_test("agents", "Execute NER Agent", "ERROR", str(e))

    async def test_workflows(self):
        """Test workflow endpoints."""
        print("\n" + "=" * 60)
        print("TESTING: Workflows API Endpoints")
        print("=" * 60 + "\n")

        if not self.token:
            print("⚠️ Skipping workflow tests - no authentication token")
            return

        headers = {"Authorization": f"Bearer {self.token}"}

        # List workflows
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/workflows", headers=headers)
            if response.status_code == 200:
                data = response.json()
                self.log_test("workflows", "List Workflows", "PASS", "Found {} workflows".format(len(data)))
            else:
                self.log_test("workflows", "List Workflows", "FAIL", f"Status: {response.status_code}")
                self.log_issue(
                    "CRITICAL",
                    "List workflows failed",
                    "GET /api/v1/workflows with auth",
                    "200 OK with workflow list",
                    f"{response.status_code} {response.text}",
                )
        except Exception as e:
            self.log_test("workflows", "List Workflows", "ERROR", str(e))
            self.log_issue("CRITICAL", "List workflows error", "GET /api/v1/workflows", "200 OK", str(e))

    async def test_batch(self):
        """Test batch processing endpoints."""
        print("\n" + "=" * 60)
        print("TESTING: Batch Processing API Endpoints")
        print("=" * 60 + "\n")

        if not self.token:
            print("⚠️ Skipping batch tests - no authentication token")
            return

        headers = {"Authorization": f"Bearer {self.token}"}

        # List batch jobs (might be empty)
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/batch/jobs", headers=headers)
            if response.status_code == 200:
                data = response.json()
                self.log_test("batch", "List Batch Jobs", "PASS", f"Found {len(data)} jobs")
            else:
                self.log_test("batch", "List Batch Jobs", "FAIL", f"Status: {response.status_code}")
                self.log_issue(
                    "HIGH",
                    "List batch jobs failed",
                    "GET /api/v1/batch/jobs with auth",
                    "200 OK with job list",
                    f"{response.status_code} {response.text}",
                )
        except Exception as e:
            self.log_test("batch", "List Batch Jobs", "ERROR", str(e))

    async def test_quotas(self):
        """Test quota management endpoints."""
        print("\n" + "=" * 60)
        print("TESTING: Quota Management API Endpoints")
        print("=" * 60 + "\n")

        if not self.token:
            print("⚠️ Skipping quota tests - no authentication token")
            return

        headers = {"Authorization": f"Bearer {self.token}"}

        # Get current user's quota
        try:
            response = await self.client.get(f"{self.base_url}/api/v2/quotas/me", headers=headers)
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    "quotas",
                    "Get My Quota",
                    "PASS",
                    f"Tier: {data.get('tier')}, Remaining: {data.get('requests_remaining')}",
                )
            else:
                self.log_test("quotas", "Get My Quota", "FAIL", f"Status: {response.status_code}")
                self.log_issue(
                    "HIGH",
                    "Get quota failed",
                    "GET /api/v2/quotas/me with auth",
                    "200 OK with quota info",
                    f"{response.status_code} {response.text}",
                )
        except Exception as e:
            self.log_test("quotas", "Get My Quota", "ERROR", str(e))

    async def run_all_tests(self):
        """Run all API tests."""
        print("\n" + "=" * 80)
        print("OMICSORACLE V2 MANUAL API TESTING")
        print(f"Started: {datetime.now().isoformat()}")
        print(f"Base URL: {self.base_url}")
        print("=" * 80)

        # Check if server is running
        try:
            response = await self.client.get(self.base_url, timeout=5.0)
            print(f"✅ Server is running (status: {response.status_code})")
        except Exception as e:
            print(f"❌ Server is not running: {e}")
            print("\nPlease start the server first:")
            print("  uvicorn omics_oracle_v2.api.main:app --reload --env-file test_environment.env\n")
            return

        # Run all test suites
        await self.test_health()
        await self.test_auth()
        await self.test_agents()
        await self.test_workflows()
        await self.test_batch()
        await self.test_quotas()

        print("\n" + "=" * 80)
        print("TESTING COMPLETE")
        print("=" * 80 + "\n")

        # Summary
        total_tests = sum(len(results) for category, results in test_results.items() if category != "issues")
        passed = sum(
            1
            for category, results in test_results.items()
            if category != "issues"
            for result in results
            if result["status"] == "PASS"
        )
        failed = sum(
            1
            for category, results in test_results.items()
            if category != "issues"
            for result in results
            if result["status"] == "FAIL"
        )
        errors = sum(
            1
            for category, results in test_results.items()
            if category != "issues"
            for result in results
            if result["status"] == "ERROR"
        )
        issues = len(test_results["issues"])

        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⚠️ Errors: {errors}")
        print(f"🐛 Issues Found: {issues}")

        # Save results
        self.save_results()

    def save_results(self):
        """Save test results to markdown file."""
        output_file = Path("docs/testing/MANUAL_TESTING_RESULTS.md")
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w") as f:
            f.write(f"# Manual Testing Results - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**Base URL:** {self.base_url}\n\n")
            f.write("---\n\n")

            # Summary
            total_tests = sum(
                len(results) for category, results in test_results.items() if category != "issues"
            )
            passed = sum(
                1
                for category, results in test_results.items()
                if category != "issues"
                for result in results
                if result["status"] == "PASS"
            )
            failed = sum(
                1
                for category, results in test_results.items()
                if category != "issues"
                for result in results
                if result["status"] == "FAIL"
            )
            errors = sum(
                1
                for category, results in test_results.items()
                if category != "issues"
                for result in results
                if result["status"] == "ERROR"
            )

            f.write("## Summary\n\n")
            f.write(f"- **Total Tests:** {total_tests}\n")
            f.write(f"- **Passed:** {passed} ✅\n")
            f.write(f"- **Failed:** {failed} ❌\n")
            f.write(f"- **Errors:** {errors} ⚠️\n")
            f.write(f"- **Issues Found:** {len(test_results['issues'])} 🐛\n\n")

            # Test results by category
            for category in ["health", "auth", "agents", "workflows", "batch", "quotas"]:
                if test_results[category]:
                    f.write(f"## {category.title()} Tests\n\n")
                    for result in test_results[category]:
                        status_emoji = (
                            "✅" if result["status"] == "PASS" else "❌" if result["status"] == "FAIL" else "⚠️"
                        )
                        f.write(f"- {status_emoji} **{result['test']}:** {result['status']}\n")
                        if result["notes"]:
                            f.write(f"  - Notes: {result['notes']}\n")
                    f.write("\n")

            # Issues found
            if test_results["issues"]:
                f.write("## Issues Found\n\n")
                for i, issue in enumerate(test_results["issues"], 1):
                    f.write(f"### Issue #{i}: {issue['issue']}\n\n")
                    f.write(f"- **Severity:** {issue['severity']}\n")
                    f.write(f"- **Steps to Reproduce:** {issue['steps']}\n")
                    f.write(f"- **Expected:** {issue['expected']}\n")
                    f.write(f"- **Actual:** {issue['actual']}\n")
                    f.write(f"- **Timestamp:** {issue['timestamp']}\n\n")

            # Raw results JSON
            f.write("## Raw Results (JSON)\n\n")
            f.write("```json\n")
            f.write(json.dumps(test_results, indent=2))
            f.write("\n```\n")

        print(f"\n📄 Results saved to: {output_file}\n")


async def main():
    """Main entry point."""
    async with TestRunner() as runner:
        await runner.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
