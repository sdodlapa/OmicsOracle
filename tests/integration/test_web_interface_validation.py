#!/usr/bin/env python3
"""
Web Interface Validation Script

This script validates that the web interface is working correctly
by testing key endpoints and functionality.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Add the src directory to the Python path
import aiohttp

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


class WebInterfaceValidator:
    """Validates web interface functionality."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results: dict = {}

    async def validate_health_endpoint(self) -> bool:
        """Test the health check endpoint."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/status/health") as resp:
                    success = resp.status == 200
                    if success:
                        data = await resp.json()
                        logger.info(f"✅ Health check passed: {data.get('status', 'OK')}")
                    else:
                        logger.warning(f"⚠️  Health check returned: {resp.status}")
                    return success
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
            return False

    async def validate_search_api(self) -> bool:
        """Test the search API endpoint."""
        try:
            async with aiohttp.ClientSession() as session:
                search_data = {
                    "query": "diabetes pancreatic beta cells",
                    "max_results": 3,
                    "include_sra": False,
                }

                async with session.post(f"{self.base_url}/api/search", json=search_data) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        geo_ids = result.get("geo_ids", [])
                        logger.info(f"✅ Search API working - found {len(geo_ids)} results")
                        self.results["search_result"] = result
                        return True
                    else:
                        logger.warning(f"⚠️  Search API returned: {resp.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ Search API failed: {e}")
            return False

    async def validate_ai_api(self) -> bool:
        """Test the AI summarization API."""
        try:
            async with aiohttp.ClientSession() as session:
                ai_data = {
                    "query": "diabetes pancreatic beta cells",
                    "max_results": 2,
                    "include_batch_summary": True,
                    "include_individual_summaries": False,
                }

                async with session.post(f"{self.base_url}/api/ai/summarize", json=ai_data) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        has_ai_summaries = "ai_summaries" in result
                        logger.info(f"✅ AI API working - AI summaries: {has_ai_summaries}")
                        return True
                    else:
                        logger.warning(f"⚠️  AI API returned: {resp.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ AI API failed: {e}")
            return False

    async def validate_static_files(self) -> bool:
        """Test static file serving."""
        try:
            async with aiohttp.ClientSession() as session:
                # Test main page
                async with session.get(f"{self.base_url}/") as resp:
                    if resp.status == 200:
                        content = await resp.text()
                        has_content = len(content) > 100
                        logger.info(f"✅ Main page served - has content: {has_content}")
                        return has_content
                    else:
                        logger.warning(f"⚠️  Main page returned: {resp.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ Static files failed: {e}")
            return False

    async def validate_visualization_api(self) -> bool:
        """Test visualization endpoints."""
        try:
            async with aiohttp.ClientSession() as session:
                viz_data = {"query": "cancer", "max_results": 10}

                # Test one visualization endpoint
                async with session.post(
                    f"{self.base_url}/api/visualization/search-stats",
                    json=viz_data,
                ) as resp:
                    if resp.status == 200:
                        await resp.json()  # Consume response
                        logger.info("✅ Visualization API working")
                        return True
                    else:
                        logger.warning(f"⚠️  Visualization API returned: {resp.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ Visualization API failed: {e}")
            return False

    async def run_validation(self) -> dict:
        """Run all validation tests."""
        logger.info("🌐 Starting Web Interface Validation")
        logger.info("=" * 50)

        tests = [
            ("Health Endpoint", self.validate_health_endpoint),
            ("Search API", self.validate_search_api),
            ("AI API", self.validate_ai_api),
            ("Static Files", self.validate_static_files),
            ("Visualization API", self.validate_visualization_api),
        ]

        results: dict = {}
        passed = 0
        total = len(tests)

        for test_name, test_func in tests:
            logger.info(f"\n🔍 Testing: {test_name}")
            try:
                success = await test_func()
                results[test_name] = {"passed": success, "error": None}
                if success:
                    passed += 1
            except Exception as e:
                logger.error(f"❌ {test_name} failed with exception: {e}")
                results[test_name] = {"passed": False, "error": str(e)}

        # Summary
        success_rate = (passed / total) * 100
        logger.info("\n" + "=" * 50)
        logger.info("📊 Validation Summary")
        logger.info("=" * 50)
        logger.info(f"Tests Passed: {passed}/{total}")
        logger.info(f"Success Rate: {success_rate:.1f}%")

        if success_rate >= 80:
            logger.info("🎉 Web interface validation successful!")
        else:
            logger.warning("⚠️  Web interface has issues that need attention")

        return {
            "summary": {
                "total_tests": total,
                "passed_tests": passed,
                "success_rate": success_rate,
            },
            "results": results,
        }


async def main() -> int:
    """Main validation function."""
    print("🚀 OmicsOracle Web Interface Validation")
    print("=" * 50)
    print("⚠️  Make sure the web server is running on localhost:8000")
    print("   Start with: python -m uvicorn src.omics_oracle.web.main:app --reload")
    print()

    validator = WebInterfaceValidator()
    results = await validator.run_validation()

    # Save results
    results_file = Path(__file__).parent.parent.parent / "web_validation_results.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)

    logger.info(f"\n💾 Results saved to: {results_file}")

    # Return appropriate exit code
    return 0 if results["summary"]["success_rate"] >= 80 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
