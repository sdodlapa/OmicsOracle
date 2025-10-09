#!/usr/bin/env python3
"""
Phase 4 Day 3: Comprehensive LLM Features Testing

Tests all remaining agent endpoints:
1. [OK] Authentication (already tested - 6/6 passing)
2. [OK] Search endpoint (already tested)
3. [OK] LLM Analysis (tested yesterday - working with GPT-4)
4. [TEST] Q&A Interface (testing now)
5. [TEST] Report Generation (testing now)
6. [TEST] Dataset Validation (testing now)
7. [TEST] End-to-end workflow
"""

import asyncio
import json
import sys

import httpx

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
TEST_USER = {"email": "test@example.com", "password": "TestPassword123!"}

# Sample dataset for testing
SAMPLE_DATASET = {
    "geo_id": "GSE292511",
    "title": "CRISPR screen for NF2 loss in pancreatic cancer",
    "summary": "Pancreatic ductal adenocarcinoma study using CRISPR screening to identify genetic dependencies associated with the loss of the NF2 gene",
    "organism": "Homo sapiens",
    "sample_count": 16,
    "platform": "GPL21290",
    "relevance_score": 0.85,
    "match_reasons": ["Title matches search terms", "High sample count"],
}


class TestResults:
    """Track test results"""

    def __init__(self):
        self.passed = 0
        self.failed = 0
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

    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*70}")
        print(f"Test Summary: {self.passed}/{total} passed")
        print(f"{'='*70}")
        return self.failed == 0


async def get_auth_token() -> str:
    """Get authentication token"""
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{API_BASE_URL}/auth/login", json=TEST_USER)
        if response.status_code != 200:
            raise Exception(f"Login failed: {response.text}")
        data = response.json()
        return data["access_token"]


async def test_analyze_endpoint(token: str, results: TestResults):
    """Test LLM analysis endpoint (already working, quick verification)"""
    print("\n[TEST] LLM Analysis Endpoint...")

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{API_BASE_URL}/agents/analyze",
                headers={"Authorization": f"Bearer {token}"},
                json={"datasets": [SAMPLE_DATASET], "query": "CRISPR pancreatic cancer", "max_datasets": 1},
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("model_used") == "gpt-4":
                    results.add_pass(
                        "LLM Analysis",
                        f"GPT-4 analysis completed in {data.get('execution_time_ms', 0)/1000:.1f}s",
                    )
                else:
                    results.add_fail("LLM Analysis", "Invalid response format")
            else:
                results.add_fail("LLM Analysis", f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            results.add_fail("LLM Analysis", str(e))


async def test_query_endpoint(token: str, results: TestResults):
    """Test Q&A interface endpoint (entity extraction & intent detection)"""
    print("\n[TEST] Query Agent (Entity Extraction)...")

    queries = [
        "breast cancer RNA-seq studies",
        "pancreatic cancer CRISPR screening",
        "neuroblastoma gene expression microarray",
    ]

    async with httpx.AsyncClient(timeout=30.0) as client:
        for query_text in queries:
            try:
                response = await client.post(
                    f"{API_BASE_URL}/agents/query",
                    headers={"Authorization": f"Bearer {token}"},
                    json={"query": query_text},
                )

                if response.status_code == 200:
                    data = response.json()
                    entities = data.get("entities", [])
                    search_terms = data.get("search_terms", [])
                    if entities and search_terms:
                        results.add_pass(
                            f"Query: '{query_text[:40]}...'",
                            f"Extracted {len(entities)} entities, {len(search_terms)} search terms",
                        )
                    else:
                        results.add_fail(f"Query: '{query_text}'", "Missing entities or search terms")
                elif response.status_code == 404:
                    results.add_fail(
                        f"Query: '{query_text}'", "Endpoint not found (may not be implemented yet)"
                    )
                else:
                    results.add_fail(
                        f"Query: '{query_text}'", f"HTTP {response.status_code}: {response.text[:200]}"
                    )
            except Exception as e:
                results.add_fail(f"Query: '{query_text}'", str(e))


async def test_report_endpoint(token: str, results: TestResults):
    """Test report generation endpoint"""
    print("\n[TEST] Report Generation...")

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                f"{API_BASE_URL}/agents/report",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "dataset_ids": ["GSE292511"],
                    "report_type": "brief",
                    "report_format": "markdown",
                    "include_recommendations": True,
                },
            )

            if response.status_code == 200:
                data = response.json()
                full_report = data.get("full_report", "")
                report_type = data.get("report_type", "")
                datasets_analyzed = data.get("datasets_analyzed", 0)
                if full_report and len(full_report) > 100:
                    results.add_pass(
                        "Report Generation",
                        f"Generated {report_type} report ({len(full_report)} chars, {datasets_analyzed} datasets)",
                    )
                else:
                    results.add_fail("Report Generation", "Report too short or missing")
            elif response.status_code == 404:
                results.add_fail("Report Generation", "Endpoint not found (may not be implemented yet)")
            else:
                results.add_fail("Report Generation", f"HTTP {response.status_code}: {response.text[:200]}")
        except Exception as e:
            results.add_fail("Report Generation", str(e))


async def test_validate_endpoint(token: str, results: TestResults):
    """Test dataset validation endpoint"""
    print("\n[TEST] Dataset Validation...")

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{API_BASE_URL}/agents/validate",
                headers={"Authorization": f"Bearer {token}"},
                json={"dataset_ids": ["GSE292511"], "min_quality_score": 0.5},
            )

            if response.status_code == 200:
                data = response.json()
                validated = data.get("validated_datasets", [])
                total_processed = data.get("total_processed", 0)
                if validated and len(validated) > 0:
                    quality_score = validated[0].get("quality_metrics", {}).get("quality_score", 0)
                    results.add_pass(
                        "Dataset Validation",
                        f"Validated {total_processed} dataset(s), quality score: {quality_score:.2f}",
                    )
                else:
                    results.add_fail("Dataset Validation", "No validation results")
            elif response.status_code == 404:
                results.add_fail("Dataset Validation", "Endpoint not found (may not be implemented yet)")
            else:
                results.add_fail("Dataset Validation", f"HTTP {response.status_code}: {response.text[:200]}")
        except Exception as e:
            results.add_fail("Dataset Validation", str(e))


async def test_search_endpoint(token: str, results: TestResults):
    """Test search endpoint (quick verification)"""
    print("\n[TEST] Search Endpoint...")

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{API_BASE_URL}/agents/search",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "search_terms": ["pancreatic cancer", "CRISPR"],
                    "max_results": 5,
                    "enable_semantic": False,
                },
            )

            if response.status_code == 200:
                data = response.json()
                datasets = data.get("datasets", [])
                if len(datasets) > 0:
                    results.add_pass("Search", f"Found {len(datasets)} datasets")
                else:
                    results.add_fail("Search", "No datasets returned")
            else:
                results.add_fail("Search", f"HTTP {response.status_code}: {response.text[:200]}")
        except Exception as e:
            results.add_fail("Search", str(e))


async def main():
    """Run all tests"""
    print("=" * 70)
    print("Phase 4 Day 3: LLM Features Testing")
    print("=" * 70)

    results = TestResults()

    try:
        # Get auth token
        print("\n[AUTH] Authenticating...")
        token = await get_auth_token()
        print("[OK] Authentication successful")

        # Run all endpoint tests
        await test_analyze_endpoint(token, results)
        await test_search_endpoint(token, results)
        await test_query_endpoint(token, results)
        await test_report_endpoint(token, results)
        await test_validate_endpoint(token, results)

        # Summary
        success = results.summary()

        # Save detailed results
        with open("test_phase4_day3_results.json", "w") as f:
            json.dump(
                {
                    "date": "2025-10-08",
                    "phase": "Phase 4 Day 3",
                    "total_tests": results.passed + results.failed,
                    "passed": results.passed,
                    "failed": results.failed,
                    "tests": results.tests,
                },
                f,
                indent=2,
            )

        print("\n[SAVE] Detailed results saved to: test_phase4_day3_results.json")

        return 0 if success else 1

    except Exception as e:
        print(f"\n[ERROR] Test suite failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
