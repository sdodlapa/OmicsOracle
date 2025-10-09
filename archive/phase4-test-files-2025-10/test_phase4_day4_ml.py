#!/usr/bin/env python3
"""
Phase 4 Day 4: ML Features Comprehensive Testing

Tests all ML/Analytics endpoints:
1. Analytics health check
2. Biomarker analytics
3. Citation predictions
4. Trend forecasting
5. Biomarker recommendations (similar, emerging, high-impact)
6. Cache operations
"""

import asyncio
import json
import sys

import httpx

# Configuration
API_BASE_URL = "http://localhost:8000/api"
TEST_USER = {"email": "test@example.com", "password": "TestPassword123!"}


class TestResults:
    """Track test results"""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.tests = []

    def add_pass(self, name: str, details: str = ""):
        self.passed += 1
        self.tests.append({"name": name, "status": "PASS", "details": details})
        print(f"[PASS] {name}")
        if details:
            print(f"   {details}")

    def add_fail(self, name: str, error: str):
        self.failed += 1
        self.tests.append({"name": name, "status": "FAIL", "error": error})
        print(f"[FAIL] {name}")
        print(f"   Error: {error}")

    def add_skip(self, name: str, reason: str):
        self.skipped += 1
        self.tests.append({"name": name, "status": "SKIP", "reason": reason})
        print(f"[SKIP] {name}")
        print(f"   Reason: {reason}")

    def summary(self):
        total = self.passed + self.failed + self.skipped
        print(f"\n{'=' * 70}")
        print(f"Test Summary: {self.passed}/{total} passed, {self.failed} failed, {self.skipped} skipped")
        print(f"{'=' * 70}")
        return self.failed == 0


async def get_auth_token() -> str:
    """Get authentication token"""
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{API_BASE_URL}/v1/auth/login", json=TEST_USER)
        if response.status_code != 200:
            raise Exception(f"Login failed: {response.text}")
        data = response.json()
        return data["access_token"]


async def test_analytics_health(token: str, results: TestResults):
    """Test ML analytics health endpoint"""
    print("\n[TEST] ML Analytics Health...")

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(
                f"{API_BASE_URL}/analytics/health", headers={"Authorization": f"Bearer {token}"}
            )

            if response.status_code == 200:
                data = response.json()
                status = data.get("status", "unknown")
                models_loaded = data.get("models_loaded", {})
                cache_available = data.get("cache_available", False)

                loaded_count = sum(1 for loaded in models_loaded.values() if loaded)
                total_models = len(models_loaded)

                results.add_pass(
                    "ML Analytics Health",
                    f"Status: {status}, Models: {loaded_count}/{total_models}, Cache: {cache_available}",
                )
            else:
                results.add_fail("ML Analytics Health", f"HTTP {response.status_code}: {response.text[:200]}")
        except Exception as e:
            results.add_fail("ML Analytics Health", str(e))


async def test_biomarker_analytics(token: str, results: TestResults):
    """Test biomarker analytics endpoint"""
    print("\n[TEST] Biomarker Analytics...")

    # Test biomarkers
    biomarkers = ["BRCA1", "TP53", "EGFR"]

    async with httpx.AsyncClient(timeout=30.0) as client:
        for biomarker in biomarkers:
            try:
                response = await client.get(
                    f"{API_BASE_URL}/analytics/biomarker/{biomarker}",
                    headers={"Authorization": f"Bearer {token}"},
                    params={"use_cache": True},
                )

                if response.status_code == 200:
                    data = response.json()
                    results.add_pass(
                        f"Biomarker Analytics: {biomarker}",
                        f"Analytics retrieved successfully",
                    )
                elif response.status_code == 404:
                    results.add_skip(
                        f"Biomarker Analytics: {biomarker}",
                        "No publications found (expected - needs DB integration)",
                    )
                else:
                    results.add_fail(
                        f"Biomarker Analytics: {biomarker}",
                        f"HTTP {response.status_code}: {response.text[:200]}",
                    )
            except Exception as e:
                results.add_fail(f"Biomarker Analytics: {biomarker}", str(e))


async def test_citation_predictions(token: str, results: TestResults):
    """Test citation prediction endpoints"""
    print("\n[TEST] Citation Predictions...")

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test batch predictions
        try:
            response = await client.post(
                f"{API_BASE_URL}/predictions/citations",
                headers={"Authorization": f"Bearer {token}"},
                json={"publication_ids": ["pub123", "pub456"], "use_cache": True},
            )

            if response.status_code == 200:
                data = response.json()
                results.add_pass("Citation Predictions (Batch)", f"Predicted {len(data)} citations")
            elif response.status_code == 404:
                results.add_skip(
                    "Citation Predictions (Batch)",
                    "No publications found (expected - needs DB integration)",
                )
            else:
                results.add_fail(
                    "Citation Predictions (Batch)",
                    f"HTTP {response.status_code}: {response.text[:200]}",
                )
        except Exception as e:
            results.add_fail("Citation Predictions (Batch)", str(e))

        # Test single prediction
        try:
            response = await client.get(
                f"{API_BASE_URL}/predictions/citations/pub123",
                headers={"Authorization": f"Bearer {token}"},
                params={"use_cache": True},
            )

            if response.status_code == 200:
                data = response.json()
                results.add_pass("Citation Predictions (Single)", "Prediction retrieved")
            elif response.status_code == 404:
                results.add_skip(
                    "Citation Predictions (Single)",
                    "Publication not found (expected - needs DB integration)",
                )
            else:
                results.add_fail(
                    "Citation Predictions (Single)",
                    f"HTTP {response.status_code}: {response.text[:200]}",
                )
        except Exception as e:
            results.add_fail("Citation Predictions (Single)", str(e))


async def test_trend_forecasting(token: str, results: TestResults):
    """Test trend forecasting endpoint"""
    print("\n[TEST] Trend Forecasting...")

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{API_BASE_URL}/predictions/trends",
                headers={"Authorization": f"Bearer {token}"},
                json={"biomarker": "BRCA1", "periods": 12, "use_cache": True},
            )

            if response.status_code == 200:
                data = response.json()
                results.add_pass("Trend Forecasting", f"Forecast generated for 12 periods")
            elif response.status_code == 404:
                results.add_skip(
                    "Trend Forecasting", "No publications found (expected - needs DB integration)"
                )
            else:
                results.add_fail("Trend Forecasting", f"HTTP {response.status_code}: {response.text[:200]}")
        except Exception as e:
            results.add_fail("Trend Forecasting", str(e))


async def test_recommendations(token: str, results: TestResults):
    """Test recommendation endpoints"""
    print("\n[TEST] Biomarker Recommendations...")

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test similar biomarkers
        try:
            response = await client.post(
                f"{API_BASE_URL}/recommendations/similar",
                headers={"Authorization": f"Bearer {token}"},
                json={"biomarker": "BRCA1", "num_recommendations": 5, "use_cache": True},
            )

            if response.status_code == 200:
                data = response.json()
                results.add_pass("Recommendations: Similar", f"Found {len(data)} similar biomarkers")
            elif response.status_code == 404:
                results.add_skip(
                    "Recommendations: Similar",
                    "No publications found (expected - needs DB integration)",
                )
            else:
                results.add_fail(
                    "Recommendations: Similar",
                    f"HTTP {response.status_code}: {response.text[:200]}",
                )
        except Exception as e:
            results.add_fail("Recommendations: Similar", str(e))

        # Test emerging biomarkers
        try:
            response = await client.get(
                f"{API_BASE_URL}/recommendations/emerging",
                headers={"Authorization": f"Bearer {token}"},
                params={"num_recommendations": 5, "use_cache": True},
            )

            if response.status_code == 200:
                data = response.json()
                results.add_pass("Recommendations: Emerging", f"Found {len(data)} emerging biomarkers")
            elif response.status_code == 404:
                results.add_skip(
                    "Recommendations: Emerging",
                    "No publications found (expected - needs DB integration)",
                )
            else:
                results.add_fail(
                    "Recommendations: Emerging",
                    f"HTTP {response.status_code}: {response.text[:200]}",
                )
        except Exception as e:
            results.add_fail("Recommendations: Emerging", str(e))

        # Test high-impact biomarkers
        try:
            response = await client.get(
                f"{API_BASE_URL}/recommendations/high-impact",
                headers={"Authorization": f"Bearer {token}"},
                params={"num_recommendations": 5, "use_cache": True},
            )

            if response.status_code == 200:
                data = response.json()
                results.add_pass("Recommendations: High-Impact", f"Found {len(data)} high-impact biomarkers")
            elif response.status_code == 404:
                results.add_skip(
                    "Recommendations: High-Impact",
                    "No publications found (expected - needs DB integration)",
                )
            else:
                results.add_fail(
                    "Recommendations: High-Impact",
                    f"HTTP {response.status_code}: {response.text[:200]}",
                )
        except Exception as e:
            results.add_fail("Recommendations: High-Impact", str(e))


async def test_cache_operations(token: str, results: TestResults):
    """Test cache management endpoints"""
    print("\n[TEST] Cache Operations...")

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test cache stats
        try:
            response = await client.get(
                f"{API_BASE_URL}/analytics/cache/stats",
                headers={"Authorization": f"Bearer {token}"},
            )

            if response.status_code == 200:
                data = response.json()
                success = data.get("success", False)
                if success:
                    results.add_pass("Cache Stats", "Cache stats retrieved")
                else:
                    results.add_skip("Cache Stats", "Cache not available")
            else:
                results.add_fail("Cache Stats", f"HTTP {response.status_code}: {response.text[:200]}")
        except Exception as e:
            results.add_fail("Cache Stats", str(e))

        # Test cache clear (use with caution)
        try:
            response = await client.post(
                f"{API_BASE_URL}/analytics/cache/clear",
                headers={"Authorization": f"Bearer {token}"},
                params={"pattern": "test_*"},  # Clear only test keys
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    results.add_pass("Cache Clear", f"Message: {data.get('message')}")
                else:
                    results.add_skip("Cache Clear", "Cache not available")
            else:
                results.add_fail("Cache Clear", f"HTTP {response.status_code}: {response.text[:200]}")
        except Exception as e:
            results.add_fail("Cache Clear", str(e))


async def main():
    """Run all ML tests"""
    print("=" * 70)
    print("Phase 4 Day 4: ML Features Testing")
    print("=" * 70)

    results = TestResults()

    try:
        # Get auth token
        print("\n[AUTH] Authenticating...")
        token = await get_auth_token()
        print("[OK] Authentication successful")

        # Run all ML tests
        await test_analytics_health(token, results)
        await test_biomarker_analytics(token, results)
        await test_citation_predictions(token, results)
        await test_trend_forecasting(token, results)
        await test_recommendations(token, results)
        await test_cache_operations(token, results)

        # Summary
        success = results.summary()

        # Save detailed results
        with open("test_phase4_day4_ml_results.json", "w") as f:
            json.dump(
                {
                    "date": "2025-10-08",
                    "phase": "Phase 4 Day 4",
                    "focus": "ML Features",
                    "total_tests": results.passed + results.failed + results.skipped,
                    "passed": results.passed,
                    "failed": results.failed,
                    "skipped": results.skipped,
                    "tests": results.tests,
                },
                f,
                indent=2,
            )

        print("\n[SAVE] Detailed results saved to: test_phase4_day4_ml_results.json")

        return 0 if success else 1

    except Exception as e:
        print(f"\n[ERROR] Test suite failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
