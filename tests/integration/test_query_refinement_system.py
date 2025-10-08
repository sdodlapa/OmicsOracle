#!/usr/bin/env python3
"""
Comprehensive Query Refinement System Test

This script performs end-to-end testing of the query refinement system,
simulating various user scenarios and validating the complete flow.
"""

import json
import time
from typing import Any, Dict, List

import requests


class QueryRefinementTester:
    """Test class for the query refinement system."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []

    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test results."""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": time.time(),
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"    Details: {details}")
        print()

    def test_backend_health(self) -> bool:
        """Test backend health endpoint."""
        try:
            response = self.session.get(f"{self.base_url}/health")
            success = response.status_code == 200 and response.json().get("status") == "healthy"
            self.log_test(
                "Backend Health Check",
                success,
                f"Status: {response.status_code}, Response: {response.json()}",
            )
            return success
        except Exception as e:
            self.log_test("Backend Health Check", False, f"Error: {str(e)}")
            return False

    def test_query_suggestions(self) -> bool:
        """Test query suggestions endpoint."""
        try:
            test_queries = [
                {"query": "nonexistent cancer gene xyz123", "result_count": 0},
                {"query": "cancer treatment protocol", "result_count": 2},
                {
                    "query": "breast caner research",
                    "result_count": 0,
                },  # Misspelling
            ]

            all_success = True
            for i, test_query in enumerate(test_queries):
                payload = {
                    "original_query": test_query["query"],
                    "result_count": test_query["result_count"],
                }

                response = self.session.post(f"{self.base_url}/api/refinement/suggestions", json=payload)

                if response.status_code == 200:
                    data = response.json()
                    has_suggestions = len(data.get("suggestions", [])) > 0
                    has_alternatives = len(data.get("alternative_queries", [])) > 0
                    has_explanation = bool(data.get("explanation"))

                    success = has_explanation  # At minimum should have explanation
                    details = f"Query: '{test_query['query']}' -> Suggestions: {len(data.get('suggestions', []))}, Alternatives: {len(data.get('alternative_queries', []))}"

                    self.log_test(f"Query Suggestions Test {i+1}", success, details)
                    all_success = all_success and success
                else:
                    self.log_test(
                        f"Query Suggestions Test {i+1}",
                        False,
                        f"HTTP {response.status_code}: {response.text}",
                    )
                    all_success = False

            return all_success

        except Exception as e:
            self.log_test("Query Suggestions Test", False, f"Error: {str(e)}")
            return False

    def test_similar_queries(self) -> bool:
        """Test similar queries endpoint."""
        try:
            test_queries = ["breast cancer", "gene expression", "covid vaccine"]

            all_success = True
            for i, query in enumerate(test_queries):
                response = self.session.get(
                    f"{self.base_url}/api/refinement/similar-queries",
                    params={"query": query, "limit": 3},
                )

                if response.status_code == 200:
                    data = response.json()
                    has_similar = len(data.get("similar_queries", [])) > 0
                    has_patterns = len(data.get("success_patterns", [])) > 0

                    success = True  # Even empty results are valid
                    details = f"Query: '{query}' -> Similar: {len(data.get('similar_queries', []))}, Patterns: {len(data.get('success_patterns', []))}"

                    self.log_test(f"Similar Queries Test {i+1}", success, details)
                else:
                    self.log_test(
                        f"Similar Queries Test {i+1}",
                        False,
                        f"HTTP {response.status_code}: {response.text}",
                    )
                    all_success = False

            return all_success

        except Exception as e:
            self.log_test("Similar Queries Test", False, f"Error: {str(e)}")
            return False

    def test_enhanced_search(self) -> bool:
        """Test enhanced search endpoint."""
        try:
            test_queries = [
                {
                    "query": "cancer",
                    "use_synonyms": True,
                    "expand_abbreviations": True,
                },
                {
                    "query": "BRCA1",
                    "use_synonyms": False,
                    "expand_abbreviations": True,
                },
                {
                    "query": "covid",
                    "use_synonyms": True,
                    "expand_abbreviations": False,
                },
            ]

            all_success = True
            for i, test_query in enumerate(test_queries):
                response = self.session.post(
                    f"{self.base_url}/api/refinement/search/enhanced",
                    json=test_query,
                )

                if response.status_code == 200:
                    data = response.json()
                    has_results = len(data.get("results", [])) > 0
                    has_query_id = bool(data.get("query_id"))

                    success = has_query_id  # Should always have query_id
                    details = f"Query: '{test_query['query']}' -> Results: {len(data.get('results', []))}, Query ID: {data.get('query_id', 'None')}"

                    self.log_test(f"Enhanced Search Test {i+1}", success, details)
                    all_success = all_success and success
                else:
                    self.log_test(
                        f"Enhanced Search Test {i+1}",
                        False,
                        f"HTTP {response.status_code}: {response.text}",
                    )
                    all_success = False

            return all_success

        except Exception as e:
            self.log_test("Enhanced Search Test", False, f"Error: {str(e)}")
            return False

    def test_feedback_submission(self) -> bool:
        """Test feedback submission endpoint."""
        try:
            test_feedback = [
                {
                    "original_query": "cancer research",
                    "suggested_query": "cancer research human",
                    "user_action": "used_suggestion",
                    "was_helpful": True,
                    "result_improvement": 15,
                },
                {
                    "original_query": "gene expression",
                    "suggested_query": "gene expression microarray",
                    "user_action": "modified_suggestion",
                    "was_helpful": True,
                    "result_improvement": 8,
                },
                {
                    "original_query": "protein folding",
                    "suggested_query": "protein structure folding",
                    "user_action": "ignored",
                    "was_helpful": False,
                },
            ]

            all_success = True
            for i, feedback in enumerate(test_feedback):
                response = self.session.post(f"{self.base_url}/api/refinement/feedback", json=feedback)

                if response.status_code == 200:
                    data = response.json()
                    has_feedback_id = bool(data.get("feedback_id"))
                    has_status = data.get("status") == "received"
                    has_message = bool(data.get("message"))

                    success = has_feedback_id and has_status and has_message
                    details = f"Feedback ID: {data.get('feedback_id')}, Status: {data.get('status')}"

                    self.log_test(f"Feedback Submission Test {i+1}", success, details)
                    all_success = all_success and success
                else:
                    self.log_test(
                        f"Feedback Submission Test {i+1}",
                        False,
                        f"HTTP {response.status_code}: {response.text}",
                    )
                    all_success = False

            return all_success

        except Exception as e:
            self.log_test("Feedback Submission Test", False, f"Error: {str(e)}")
            return False

    def test_analytics_endpoint(self) -> bool:
        """Test analytics endpoint."""
        try:
            response = self.session.get(f"{self.base_url}/api/refinement/analytics")

            if response.status_code == 200:
                data = response.json()
                required_fields = [
                    "total_suggestions_generated",
                    "suggestion_acceptance_rate",
                    "average_result_improvement",
                    "most_common_suggestion_types",
                    "user_feedback_summary",
                    "system_performance",
                ]

                has_all_fields = all(field in data for field in required_fields)
                success = has_all_fields
                details = f"Fields present: {list(data.keys())}"

                self.log_test("Analytics Endpoint Test", success, details)
                return success
            else:
                self.log_test(
                    "Analytics Endpoint Test",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                )
                return False

        except Exception as e:
            self.log_test("Analytics Endpoint Test", False, f"Error: {str(e)}")
            return False

    def test_error_handling(self) -> bool:
        """Test error handling for invalid requests."""
        try:
            error_tests = [
                # Invalid suggestion request
                {
                    "endpoint": "/api/refinement/suggestions",
                    "method": "POST",
                    "data": {"invalid_field": "test"},
                    "expected_status": 422,
                },
                # Invalid feedback request
                {
                    "endpoint": "/api/refinement/feedback",
                    "method": "POST",
                    "data": {
                        "original_query": "test",
                        "suggested_query": "test",
                        "user_action": "invalid_action",  # Should fail validation
                        "was_helpful": True,
                    },
                    "expected_status": 400,
                },
                # Invalid enhanced search request
                {
                    "endpoint": "/api/refinement/search/enhanced",
                    "method": "POST",
                    "data": {},  # Missing required query field
                    "expected_status": 422,
                },
            ]

            all_success = True
            for i, test in enumerate(error_tests):
                if test["method"] == "POST":
                    response = self.session.post(f"{self.base_url}{test['endpoint']}", json=test["data"])
                else:
                    response = self.session.get(f"{self.base_url}{test['endpoint']}")

                success = response.status_code == test["expected_status"]
                details = f"Expected {test['expected_status']}, got {response.status_code}"

                self.log_test(f"Error Handling Test {i+1}", success, details)
                all_success = all_success and success

            return all_success

        except Exception as e:
            self.log_test("Error Handling Test", False, f"Error: {str(e)}")
            return False

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return summary."""
        print("🧪 Starting Query Refinement System Tests\n")
        print("=" * 60)

        # Run all test methods
        test_methods = [
            self.test_backend_health,
            self.test_query_suggestions,
            self.test_similar_queries,
            self.test_enhanced_search,
            self.test_feedback_submission,
            self.test_analytics_endpoint,
            self.test_error_handling,
        ]

        results = []
        for test_method in test_methods:
            results.append(test_method())

        # Calculate summary
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests

        print("=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"Total tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success rate: {(passed_tests/total_tests)*100:.1f}%")

        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['details']}")

        print("\n🎉 Query Refinement System Testing Complete!")

        return {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "success_rate": (passed_tests / total_tests) * 100,
            "all_results": self.test_results,
        }


if __name__ == "__main__":
    tester = QueryRefinementTester()
    summary = tester.run_all_tests()

    # Exit with error code if tests failed
    exit(0 if summary["failed"] == 0 else 1)
