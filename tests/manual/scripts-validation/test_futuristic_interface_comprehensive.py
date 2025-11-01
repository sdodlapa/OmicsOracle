"""
Comprehensive Test Suite for OmicsOracle Futuristic Interface

This module provides extensive testing to ensure that the futuristic interface
properly integrates with the modular OmicsOracle pipeline and displays accurate
information on the web interface.
"""

import asyncio
import json
import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Add project root to path
from src.omics_oracle.core.config import Config
from src.omics_oracle.pipeline.pipeline import OmicsOracle

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test configuration
BASE_URL = "http://localhost:8001"
TEST_TIMEOUT = 30
TEST_QUERIES = [
    "breast cancer RNA-seq",
    "diabetes microarray",
    "alzheimer gene expression",
    "heart disease genomics",
    "lung cancer proteomics",
]


class FuturisticInterfaceTestSuite:
    """Comprehensive test suite for the futuristic interface"""

    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.driver = None
        self.test_results = {
            "backend_tests": {},
            "frontend_tests": {},
            "integration_tests": {},
            "data_accuracy_tests": {},
            "summary": {},
        }

    def setup_selenium(self):
        """Set up Selenium WebDriver for frontend testing"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")  # Run in headless mode
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")

            self.driver = webdriver.Chrome(options=chrome_options)
            logger.info("✅ Selenium WebDriver initialized")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to initialize Selenium: {e}")
            return False

    def cleanup_selenium(self):
        """Clean up Selenium WebDriver"""
        if self.driver:
            self.driver.quit()
            self.driver = None

    async def test_backend_health(self) -> Dict[str, Any]:
        """Test backend health and pipeline initialization"""
        logger.info("🏥 Testing backend health...")

        test_result = {"status": "failed", "response_time": None, "pipeline_available": False, "error": None}

        try:
            start_time = time.time()
            response = self.session.get(f"{self.base_url}/api/health", timeout=TEST_TIMEOUT)
            response_time = time.time() - start_time

            test_result["response_time"] = response_time

            if response.status_code == 200:
                data = response.json()
                test_result["status"] = "passed"
                test_result["pipeline_available"] = data.get("pipeline_available", False)
                test_result["data"] = data
                logger.info(f"✅ Backend health check passed ({response_time:.2f}s)")
            else:
                test_result["error"] = f"HTTP {response.status_code}"
                logger.error(f"❌ Backend health check failed: HTTP {response.status_code}")

        except Exception as e:
            test_result["error"] = str(e)
            logger.error(f"❌ Backend health check failed: {e}")

        return test_result

    async def test_search_api(self, query: str) -> Dict[str, Any]:
        """Test search API with a specific query"""
        logger.info(f"🔍 Testing search API with query: '{query}'")

        test_result = {
            "query": query,
            "status": "failed",
            "response_time": None,
            "results_count": 0,
            "data_structure_valid": False,
            "required_fields_present": False,
            "error": None,
        }

        try:
            start_time = time.time()
            response = self.session.post(
                f"{self.base_url}/api/search",
                json={"query": query, "max_results": 5, "search_type": "comprehensive"},
                timeout=TEST_TIMEOUT,
            )
            response_time = time.time() - start_time

            test_result["response_time"] = response_time

            if response.status_code == 200:
                data = response.json()
                test_result["status"] = "passed"
                test_result["results_count"] = len(data.get("results", []))
                test_result["data"] = data

                # Validate data structure
                test_result["data_structure_valid"] = self._validate_search_response(data)
                test_result["required_fields_present"] = self._validate_dataset_fields(
                    data.get("results", [])
                )

                logger.info(
                    f"✅ Search API test passed for '{query}' ({response_time:.2f}s, {test_result['results_count']} results)"
                )
            else:
                test_result["error"] = f"HTTP {response.status_code}: {response.text}"
                logger.error(f"❌ Search API test failed for '{query}': HTTP {response.status_code}")

        except Exception as e:
            test_result["error"] = str(e)
            logger.error(f"❌ Search API test failed for '{query}': {e}")

        return test_result

    def _validate_search_response(self, data: Dict[str, Any]) -> bool:
        """Validate the structure of search response"""
        required_fields = ["query", "results", "total_found", "search_time", "timestamp"]
        return all(field in data for field in required_fields)

    def _validate_dataset_fields(self, datasets: List[Dict[str, Any]]) -> bool:
        """Validate that datasets have required fields"""
        if not datasets:
            return True  # Empty results are valid

        required_fields = [
            "geo_id",
            "title",
            "summary",
            "organism",
            "sample_count",
            "platform",
            "publication_date",
            "study_type",
            "ai_summary",
            "relevance_score",
        ]

        for dataset in datasets:
            if not all(field in dataset for field in required_fields):
                return False

        return True

    async def test_frontend_loading(self) -> Dict[str, Any]:
        """Test frontend loading and basic functionality"""
        if not self.driver:
            return {"status": "skipped", "error": "Selenium not available"}

        logger.info("🌐 Testing frontend loading...")

        test_result = {
            "status": "failed",
            "page_loaded": False,
            "elements_present": False,
            "javascript_errors": [],
            "error": None,
        }

        try:
            # Load the page
            self.driver.get(self.base_url)

            # Wait for page to load
            WebDriverWait(self.driver, TEST_TIMEOUT).until(EC.presence_of_element_located((By.ID, "app")))

            test_result["page_loaded"] = True

            # Check for key elements
            required_elements = [
                "search-input",
                "search-btn",
                "search-results",
                "live-updates",
                "system-stats",
            ]

            elements_found = []
            for element_id in required_elements:
                try:
                    element = self.driver.find_element(By.ID, element_id)
                    elements_found.append(element_id)
                except Exception:
                    pass

            test_result["elements_present"] = len(elements_found) == len(required_elements)
            test_result["elements_found"] = elements_found

            # Check for JavaScript errors
            logs = self.driver.get_log("browser")
            js_errors = [log for log in logs if log["level"] == "SEVERE"]
            test_result["javascript_errors"] = js_errors

            if test_result["page_loaded"] and test_result["elements_present"] and not js_errors:
                test_result["status"] = "passed"
                logger.info("✅ Frontend loading test passed")
            else:
                test_result["status"] = "partial"
                logger.warning("⚠️ Frontend loading test had issues")

        except Exception as e:
            test_result["error"] = str(e)
            logger.error(f"❌ Frontend loading test failed: {e}")

        return test_result

    async def test_search_functionality(self, query: str) -> Dict[str, Any]:
        """Test end-to-end search functionality"""
        if not self.driver:
            return {"status": "skipped", "error": "Selenium not available"}

        logger.info(f"🔍 Testing end-to-end search functionality for: '{query}'")

        test_result = {
            "query": query,
            "status": "failed",
            "search_executed": False,
            "results_displayed": False,
            "ui_updates": False,
            "error": None,
        }

        try:
            # Enter search query
            search_input = self.driver.find_element(By.ID, "search-input")
            search_input.clear()
            search_input.send_keys(query)

            # Click search button
            search_btn = self.driver.find_element(By.ID, "search-btn")
            search_btn.click()

            test_result["search_executed"] = True

            # Wait for results to appear (with timeout)
            try:
                WebDriverWait(self.driver, TEST_TIMEOUT).until(
                    lambda driver: driver.find_element(By.ID, "search-results").text
                    != "Enter a search query to find biomedical datasets..."
                )
                test_result["results_displayed"] = True
            except Exception:
                logger.warning(f"⚠️ No results displayed for query: '{query}'")

            # Check if UI was updated
            live_updates = self.driver.find_element(By.ID, "live-updates")
            stats = self.driver.find_element(By.ID, "system-stats")

            if "System ready" not in live_updates.text and "0" not in stats.text:
                test_result["ui_updates"] = True

            if test_result["search_executed"] and (
                test_result["results_displayed"] or test_result["ui_updates"]
            ):
                test_result["status"] = "passed"
                logger.info(f"✅ End-to-end search test passed for '{query}'")
            else:
                test_result["status"] = "partial"
                logger.warning(f"⚠️ End-to-end search test had issues for '{query}'")

        except Exception as e:
            test_result["error"] = str(e)
            logger.error(f"❌ End-to-end search test failed for '{query}': {e}")

        return test_result

    async def test_data_accuracy(self) -> Dict[str, Any]:
        """Test data accuracy by comparing with direct OmicsOracle pipeline"""
        logger.info("🎯 Testing data accuracy...")

        test_result = {"status": "failed", "comparisons": [], "accuracy_score": 0.0, "error": None}

        try:
            # Initialize direct pipeline for comparison
            config = Config()
            pipeline = OmicsOracle(config)

            test_query = "cancer RNA-seq"

            # Get results from API
            api_response = self.session.post(
                f"{self.base_url}/api/search",
                json={"query": test_query, "max_results": 3},
                timeout=TEST_TIMEOUT,
            )

            if api_response.status_code != 200:
                raise Exception(f"API request failed: {api_response.status_code}")

            api_data = api_response.json()

            # Get results from direct pipeline
            pipeline_result = await pipeline.process_query(test_query, max_results=3)

            # Compare results
            comparison = self._compare_results(api_data, pipeline_result)
            test_result["comparisons"] = [comparison]
            test_result["accuracy_score"] = comparison.get("accuracy_score", 0.0)

            if test_result["accuracy_score"] > 0.7:  # 70% accuracy threshold
                test_result["status"] = "passed"
                logger.info(f"✅ Data accuracy test passed (score: {test_result['accuracy_score']:.2f})")
            else:
                test_result["status"] = "failed"
                logger.error(f"❌ Data accuracy test failed (score: {test_result['accuracy_score']:.2f})")

        except Exception as e:
            test_result["error"] = str(e)
            logger.error(f"❌ Data accuracy test failed: {e}")

        return test_result

    def _compare_results(self, api_data: Dict[str, Any], pipeline_result) -> Dict[str, Any]:
        """Compare API results with direct pipeline results"""
        comparison = {
            "api_results_count": len(api_data.get("results", [])),
            "pipeline_results_count": len(pipeline_result.geo_ids),
            "geo_ids_match": 0,
            "accuracy_score": 0.0,
        }

        api_geo_ids = [result.get("geo_id") for result in api_data.get("results", [])]
        pipeline_geo_ids = pipeline_result.geo_ids

        # Calculate overlap
        if api_geo_ids and pipeline_geo_ids:
            matching_ids = set(api_geo_ids) & set(pipeline_geo_ids)
            comparison["geo_ids_match"] = len(matching_ids)
            comparison["accuracy_score"] = len(matching_ids) / max(len(api_geo_ids), len(pipeline_geo_ids))

        comparison["api_geo_ids"] = api_geo_ids
        comparison["pipeline_geo_ids"] = pipeline_geo_ids

        return comparison

    async def run_comprehensive_tests(self) -> Dict[str, Any]:
        """Run all tests and return comprehensive results"""
        logger.info("🚀 Starting comprehensive test suite for OmicsOracle Futuristic Interface...")

        start_time = time.time()

        # Backend tests
        logger.info("📡 Running backend tests...")
        self.test_results["backend_tests"]["health"] = await self.test_backend_health()

        # Search API tests
        self.test_results["backend_tests"]["search_api"] = {}
        for query in TEST_QUERIES[:3]:  # Test first 3 queries
            result = await self.test_search_api(query)
            self.test_results["backend_tests"]["search_api"][query] = result
            await asyncio.sleep(1)  # Prevent rate limiting

        # Data accuracy tests
        logger.info("🎯 Running data accuracy tests...")
        self.test_results["data_accuracy_tests"]["comparison"] = await self.test_data_accuracy()

        # Frontend tests (if Selenium is available)
        if self.setup_selenium():
            logger.info("🌐 Running frontend tests...")
            self.test_results["frontend_tests"]["loading"] = await self.test_frontend_loading()

            # End-to-end search tests
            self.test_results["integration_tests"]["search_functionality"] = {}
            for query in TEST_QUERIES[:2]:  # Test first 2 queries
                result = await self.test_search_functionality(query)
                self.test_results["integration_tests"]["search_functionality"][query] = result
                await asyncio.sleep(2)  # Allow time for UI updates

            self.cleanup_selenium()
        else:
            logger.warning("⚠️ Selenium not available, skipping frontend tests")

        # Generate summary
        total_time = time.time() - start_time
        self.test_results["summary"] = self._generate_summary(total_time)

        logger.info(f"✅ Comprehensive test suite completed in {total_time:.2f}s")

        return self.test_results

    def _generate_summary(self, total_time: float) -> Dict[str, Any]:
        """Generate test summary"""
        summary = {
            "total_time": total_time,
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "tests_skipped": 0,
            "overall_status": "unknown",
        }

        # Count tests from all categories
        for category, tests in self.test_results.items():
            if category == "summary":
                continue

            if isinstance(tests, dict):
                for test_name, result in tests.items():
                    if isinstance(result, dict):
                        if "status" in result:
                            summary["tests_run"] += 1
                            if result["status"] == "passed":
                                summary["tests_passed"] += 1
                            elif result["status"] == "failed":
                                summary["tests_failed"] += 1
                            elif result["status"] == "skipped":
                                summary["tests_skipped"] += 1
                    elif isinstance(result, dict):
                        # Handle nested test results
                        for nested_result in result.values():
                            if isinstance(nested_result, dict) and "status" in nested_result:
                                summary["tests_run"] += 1
                                if nested_result["status"] == "passed":
                                    summary["tests_passed"] += 1
                                elif nested_result["status"] == "failed":
                                    summary["tests_failed"] += 1
                                elif nested_result["status"] == "skipped":
                                    summary["tests_skipped"] += 1

        # Determine overall status
        if summary["tests_failed"] == 0 and summary["tests_passed"] > 0:
            summary["overall_status"] = "passed"
        elif summary["tests_passed"] > summary["tests_failed"]:
            summary["overall_status"] = "mostly_passed"
        else:
            summary["overall_status"] = "failed"

        return summary

    def save_results(self, filename: str = "futuristic_interface_test_results.json"):
        """Save test results to file"""
        results_path = Path(__file__).parent / filename

        with open(results_path, "w") as f:
            json.dump(self.test_results, f, indent=2, default=str)

        logger.info(f"📊 Test results saved to: {results_path}")

        return results_path


async def main():
    """Main test runner"""
    print("🧬 OmicsOracle Futuristic Interface - Comprehensive Test Suite")
    print("=" * 70)

    test_suite = FuturisticInterfaceTestSuite()

    try:
        results = await test_suite.run_comprehensive_tests()
        results_file = test_suite.save_results()

        # Print summary
        summary = results["summary"]
        print("\n📊 TEST SUMMARY")
        print("-" * 30)
        print(f"Total Tests: {summary['tests_run']}")
        print(f"Passed: {summary['tests_passed']} ✅")
        print(f"Failed: {summary['tests_failed']} ❌")
        print(f"Skipped: {summary['tests_skipped']} ⏭️")
        print(f"Overall Status: {summary['overall_status'].upper()}")
        print(f"Total Time: {summary['total_time']:.2f}s")
        print(f"Results saved to: {results_file}")

        return summary["overall_status"] in ["passed", "mostly_passed"]

    except Exception as e:
        logger.error(f"❌ Test suite execution failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
