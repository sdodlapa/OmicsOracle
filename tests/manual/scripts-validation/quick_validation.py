"""
Quick Validation Script for OmicsOracle Futuristic Interface

This script performs quick validation tests to ensure the interface is working
properly with the modular OmicsOracle pipeline.
"""

import asyncio
import json
import logging
import sys
import time
from pathlib import Path

import requests

# Add project root to path
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8001"
TIMEOUT = 30


class QuickValidator:
    """Quick validation for the futuristic interface"""

    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.results = {}

    def test_health(self) -> bool:
        """Test if the interface is healthy"""
        try:
            logger.info("🏥 Testing health endpoint...")
            response = self.session.get(f"{self.base_url}/api/health", timeout=TIMEOUT)

            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Health check passed: {data}")
                self.results["health"] = data
                return True
            else:
                logger.error(f"❌ Health check failed: HTTP {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"❌ Health check error: {e}")
            return False

    def test_search(self, query: str = "cancer RNA-seq") -> bool:
        """Test search functionality"""
        try:
            logger.info(f"🔍 Testing search with query: '{query}'")

            start_time = time.time()
            response = self.session.post(
                f"{self.base_url}/api/search",
                json={"query": query, "max_results": 5, "search_type": "comprehensive"},
                timeout=TIMEOUT,
            )
            response_time = time.time() - start_time

            if response.status_code == 200:
                data = response.json()

                # Validate response structure
                required_fields = ["query", "results", "total_found", "search_time", "timestamp"]
                if not all(field in data for field in required_fields):
                    logger.error("❌ Response missing required fields")
                    return False

                # Validate dataset fields
                if data["results"]:
                    dataset = data["results"][0]
                    dataset_fields = ["geo_id", "title", "summary", "organism", "sample_count"]
                    if not all(field in dataset for field in dataset_fields):
                        logger.error("❌ Dataset missing required fields")
                        return False

                logger.info(f"✅ Search test passed: {len(data['results'])} results in {response_time:.2f}s")
                self.results["search"] = {
                    "query": query,
                    "results_count": len(data["results"]),
                    "response_time": response_time,
                    "data": data,
                }
                return True
            else:
                logger.error(f"❌ Search test failed: HTTP {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"❌ Search test error: {e}")
            return False

    def test_frontend(self) -> bool:
        """Test if frontend loads"""
        try:
            logger.info("🌐 Testing frontend loading...")
            response = self.session.get(self.base_url, timeout=TIMEOUT)

            if response.status_code == 200:
                html = response.text

                # Check for key elements
                required_elements = [
                    'id="search-input"',
                    'id="search-btn"',
                    'id="search-results"',
                    "OmicsOracle",
                ]

                missing_elements = []
                for element in required_elements:
                    if element not in html:
                        missing_elements.append(element)

                if not missing_elements:
                    logger.info("✅ Frontend test passed")
                    self.results["frontend"] = {"status": "passed"}
                    return True
                else:
                    logger.error(f"❌ Frontend missing elements: {missing_elements}")
                    return False
            else:
                logger.error(f"❌ Frontend test failed: HTTP {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"❌ Frontend test error: {e}")
            return False

    def validate_data_accuracy(self) -> bool:
        """Quick data accuracy validation"""
        try:
            logger.info("🎯 Validating data accuracy...")

            # Test with a specific query
            response = self.session.post(
                f"{self.base_url}/api/search",
                json={"query": "breast cancer", "max_results": 3},
                timeout=TIMEOUT,
            )

            if response.status_code != 200:
                logger.error("❌ Search request failed for accuracy test")
                return False

            data = response.json()
            results = data.get("results", [])

            if not results:
                logger.warning("⚠️ No results returned - cannot validate accuracy")
                return True  # Empty results are valid

            # Check if results look reasonable
            accuracy_checks = []

            for result in results:
                # Check GEO ID format
                geo_id = result.get("geo_id", "")
                if geo_id.startswith("GSE") or geo_id == "Unknown":
                    accuracy_checks.append(True)
                else:
                    accuracy_checks.append(False)

                # Check if title and summary are not empty
                title = result.get("title", "")
                summary = result.get("summary", "")
                if title and summary and len(title) > 10 and len(summary) > 20:
                    accuracy_checks.append(True)
                else:
                    accuracy_checks.append(False)

                # Check sample count is reasonable
                sample_count = result.get("sample_count", 0)
                if isinstance(sample_count, int) and sample_count >= 0:
                    accuracy_checks.append(True)
                else:
                    accuracy_checks.append(False)

            accuracy_score = sum(accuracy_checks) / len(accuracy_checks) if accuracy_checks else 0

            logger.info(f"🎯 Data accuracy score: {accuracy_score:.2f}")
            self.results["accuracy"] = {
                "score": accuracy_score,
                "sample_results": results[:2],  # Save first 2 for review
            }

            return accuracy_score > 0.7  # 70% accuracy threshold

        except Exception as e:
            logger.error(f"❌ Data accuracy validation error: {e}")
            return False

    def run_validation(self) -> bool:
        """Run all validation tests"""
        logger.info("🚀 Starting quick validation of OmicsOracle Futuristic Interface...")

        tests = [
            ("Health Check", self.test_health),
            ("Frontend Loading", self.test_frontend),
            ("Search Functionality", self.test_search),
            ("Data Accuracy", self.validate_data_accuracy),
        ]

        passed = 0
        total = len(tests)

        for test_name, test_func in tests:
            logger.info(f"\n🧪 Running: {test_name}")
            try:
                if test_func():
                    passed += 1
                    logger.info(f"✅ {test_name}: PASSED")
                else:
                    logger.error(f"❌ {test_name}: FAILED")
            except Exception as e:
                logger.error(f"❌ {test_name}: ERROR - {e}")

        # Summary
        success_rate = passed / total
        logger.info(f"\n📊 VALIDATION SUMMARY")
        logger.info(f"Tests Passed: {passed}/{total}")
        logger.info(f"Success Rate: {success_rate:.1%}")

        # Save results
        results_file = Path(__file__).parent / "quick_validation_results.json"
        with open(results_file, "w") as f:
            json.dump(self.results, f, indent=2, default=str)

        logger.info(f"Results saved to: {results_file}")

        return success_rate >= 0.75  # 75% pass rate required


def main():
    """Main validation runner"""
    print("🧬 OmicsOracle Futuristic Interface - Quick Validation")
    print("=" * 55)

    validator = QuickValidator()

    try:
        success = validator.run_validation()

        if success:
            print("\n🎉 VALIDATION SUCCESSFUL!")
            print("The futuristic interface is working correctly with the modular pipeline.")
            return 0
        else:
            print("\n⚠️ VALIDATION ISSUES DETECTED")
            print("Some tests failed. Check the logs above for details.")
            return 1

    except Exception as e:
        logger.error(f"❌ Validation failed with error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
