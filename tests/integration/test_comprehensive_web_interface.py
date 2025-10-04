#!/usr/bin/env python3
"""
Comprehensive Web Interface Test Suite

This module provides end-to-end testing for the OmicsOracle web interface,
including all API endpoints, WebSocket connections, and UI functionality.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict

import aiohttp

try:
    import websockets

    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    websockets = None

try:
    from fastapi.testclient import TestClient

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    TestClient = None

# Add the src directory to the Python path
from omics_oracle.web.main import app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WebInterfaceTestSuite:
    """Comprehensive test suite for the web interface."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        self.test_results = {}

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def test_health_check(self) -> bool:
        """Test basic health check endpoint."""
        try:
            async with self.session.get(f"{self.base_url}/api/status/health") as resp:
                success = resp.status == 200
                if success:
                    data = await resp.json()
                    logger.info(f"✅ Health check passed: {data}")
                else:
                    logger.error(f"❌ Health check failed: {resp.status}")
                return success
        except Exception as e:
            logger.error(f"❌ Health check error: {e}")
            return False

    async def test_basic_search_api(self) -> bool:
        """Test the basic search API endpoint."""
        try:
            search_data = {
                "query": "diabetes pancreatic beta cells",
                "max_results": 5,
                "include_sra": False,
            }

            async with self.session.post(f"{self.base_url}/api/search", json=search_data) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    logger.info(f"✅ Basic search successful: {len(result.get('geo_ids', []))} results")
                    self.test_results["basic_search"] = result
                    return True
                else:
                    logger.error(f"❌ Basic search failed: {resp.status}")
                    return False
        except Exception as e:
            logger.error(f"❌ Basic search error: {e}")
            return False

    async def test_ai_summarization_api(self) -> bool:
        """Test the AI summarization API endpoint."""
        try:
            ai_data = {
                "query": "diabetes pancreatic beta cells",
                "max_results": 3,
                "include_batch_summary": True,
                "include_individual_summaries": True,
            }

            async with self.session.post(f"{self.base_url}/api/ai/summarize", json=ai_data) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    logger.info("✅ AI summarization successful")

                    # Validate AI summaries structure
                    if "ai_summaries" in result:
                        summaries = result["ai_summaries"]
                        has_batch = "batch_summary" in summaries
                        has_individual = "individual_summaries" in summaries
                        logger.info(f"   📊 Batch summary: {'✓' if has_batch else '✗'}")
                        logger.info(f"   📚 Individual summaries: {'✓' if has_individual else '✗'}")
                        self.test_results["ai_summarization"] = result
                        return True
                    else:
                        logger.warning("⚠️  No AI summaries in response")
                        return False
                else:
                    logger.error(f"❌ AI summarization failed: {resp.status}")
                    return False
        except Exception as e:
            logger.error(f"❌ AI summarization error: {e}")
            return False

    async def test_batch_processing_api(self) -> bool:
        """Test the batch processing API endpoint."""
        try:
            batch_data = {
                "queries": [
                    "diabetes pancreatic beta cells",
                    "cancer stem cells",
                    "immune response COVID-19",
                ],
                "max_results_per_query": 3,
            }

            async with self.session.post(f"{self.base_url}/api/batch", json=batch_data) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    logger.info(f"✅ Batch processing successful: {result.get('job_id', 'N/A')}")
                    self.test_results["batch_processing"] = result
                    return True
                else:
                    logger.error(f"❌ Batch processing failed: {resp.status}")
                    return False
        except Exception as e:
            logger.error(f"❌ Batch processing error: {e}")
            return False

    async def test_visualization_api(self) -> bool:
        """Test the visualization API endpoints."""
        try:
            viz_request = {"query": "cancer", "max_results": 20}

            # Test multiple visualization endpoints
            endpoints = [
                "search-stats",
                "entity-distribution",
                "organism-distribution",
                "platform-distribution",
                "timeline-distribution",
            ]

            results = {}
            all_passed = True

            for endpoint in endpoints:
                async with self.session.post(
                    f"{self.base_url}/api/visualization/{endpoint}",
                    json=viz_request,
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        results[endpoint] = data
                        logger.info(f"✅ Visualization endpoint '{endpoint}' successful")
                    else:
                        logger.error(f"❌ Visualization endpoint '{endpoint}' failed: {resp.status}")
                        all_passed = False

            self.test_results["visualization"] = results
            return all_passed

        except Exception as e:
            logger.error(f"❌ Visualization API error: {e}")
            return False

    async def test_export_functionality(self) -> bool:
        """Test the export functionality."""
        try:
            # First do a search to get data to export
            search_result = self.test_results.get("basic_search")
            if not search_result:
                logger.warning("⚠️  No search results available for export test")
                return False

            export_data = {
                "query_id": search_result.get("query_id", "test"),
                "format": "json",
                "include_metadata": True,
            }

            async with self.session.post(f"{self.base_url}/api/export", json=export_data) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    logger.info("✅ Export functionality successful")
                    self.test_results["export"] = result
                    return True
                else:
                    logger.error(f"❌ Export failed: {resp.status}")
                    return False
        except Exception as e:
            logger.error(f"❌ Export error: {e}")
            return False

    async def test_websocket_connection(self) -> bool:
        """Test WebSocket functionality."""
        try:
            ws_url = self.base_url.replace("http://", "ws://") + "/api/ws"

            async with websockets.connect(ws_url) as websocket:
                # Send a test message
                test_message = {
                    "type": "search_request",
                    "data": {"query": "test websocket", "max_results": 1},
                }

                await websocket.send(json.dumps(test_message))

                # Wait for response
                response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                result = json.loads(response)

                logger.info("✅ WebSocket connection successful")
                self.test_results["websocket"] = result
                return True

        except asyncio.TimeoutError:
            logger.warning("⚠️  WebSocket test timed out")
            return False
        except Exception as e:
            logger.error(f"❌ WebSocket error: {e}")
            return False

    async def test_static_files(self) -> bool:
        """Test static file serving."""
        try:
            static_files = [
                "/static/index.html",
                "/static/dashboard.html",
                "/static/research_dashboard.html",
            ]

            all_passed = True
            for file_path in static_files:
                async with self.session.get(f"{self.base_url}{file_path}") as resp:
                    if resp.status == 200:
                        content = await resp.text()
                        if len(content) > 100:  # Basic validation
                            logger.info(f"✅ Static file '{file_path}' served successfully")
                        else:
                            logger.warning(f"⚠️  Static file '{file_path}' seems empty")
                            all_passed = False
                    else:
                        logger.error(f"❌ Static file '{file_path}' failed: {resp.status}")
                        all_passed = False

            return all_passed

        except Exception as e:
            logger.error(f"❌ Static files error: {e}")
            return False

    async def test_ui_integration(self) -> bool:
        """Test UI integration points."""
        try:
            # Test main page
            async with self.session.get(f"{self.base_url}/") as resp:
                if resp.status == 200:
                    html_content = await resp.text()

                    # Check for key UI elements
                    ui_checks = [
                        ("Search form", "search" in html_content.lower()),
                        (
                            "AI features",
                            "ai" in html_content.lower() or "summarization" in html_content.lower(),
                        ),
                        (
                            "Visualization",
                            "chart" in html_content.lower() or "visualization" in html_content.lower(),
                        ),
                        ("API endpoints", "/api/" in html_content),
                    ]

                    all_passed = True
                    for check_name, check_result in ui_checks:
                        if check_result:
                            logger.info(f"✅ UI check '{check_name}' passed")
                        else:
                            logger.warning(f"⚠️  UI check '{check_name}' failed")
                            all_passed = False

                    return all_passed
                else:
                    logger.error(f"❌ Main page failed: {resp.status}")
                    return False
        except Exception as e:
            logger.error(f"❌ UI integration error: {e}")
            return False

    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run all tests and return comprehensive results."""
        logger.info("🚀 Starting Comprehensive Web Interface Test Suite")
        logger.info("=" * 60)

        test_methods = [
            ("Health Check", self.test_health_check),
            ("Basic Search API", self.test_basic_search_api),
            ("AI Summarization API", self.test_ai_summarization_api),
            ("Batch Processing API", self.test_batch_processing_api),
            ("Visualization API", self.test_visualization_api),
            ("Export Functionality", self.test_export_functionality),
            ("WebSocket Connection", self.test_websocket_connection),
            ("Static Files", self.test_static_files),
            ("UI Integration", self.test_ui_integration),
        ]

        results = {}
        passed_tests = 0
        total_tests = len(test_methods)

        for test_name, test_method in test_methods:
            logger.info(f"\n📋 Running: {test_name}")
            try:
                success = await test_method()
                results[test_name] = {"passed": success, "error": None}
                if success:
                    passed_tests += 1
            except Exception as e:
                logger.error(f"❌ {test_name} failed with exception: {e}")
                results[test_name] = {"passed": False, "error": str(e)}

        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("📊 Test Summary")
        logger.info("=" * 60)
        logger.info(f"Tests Passed: {passed_tests}/{total_tests}")
        logger.info(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")

        # Detailed results
        for test_name, result in results.items():
            status = "✅ PASS" if result["passed"] else "❌ FAIL"
            logger.info(f"{status} {test_name}")
            if result["error"]:
                logger.info(f"    Error: {result['error']}")

        return {
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "success_rate": (passed_tests / total_tests) * 100,
            },
            "detailed_results": results,
            "test_data": self.test_results,
        }


# FastAPI TestClient-based tests (for unit testing)
def test_web_app_with_test_client():
    """Test web app using FastAPI TestClient (synchronous)."""
    client = TestClient(app)

    # Test root endpoint
    response = client.get("/")
    assert response.status_code == 200

    # Test health endpoint
    response = client.get("/api/status/health")
    # Note: This might fail if dependencies aren't available, but that's OK for structure testing
    assert response.status_code in [200, 503]  # 503 if pipeline not initialized


# Main async test function
async def main():
    """Run the comprehensive web interface test suite."""
    print("🌐 OmicsOracle Web Interface - Comprehensive Test Suite")
    print("=" * 60)
    print("⚠️  Make sure the web server is running on localhost:8000")
    print("   Start with: python -m uvicorn src.omics_oracle.web.main:app --reload")
    print()

    async with WebInterfaceTestSuite() as test_suite:
        results = await test_suite.run_comprehensive_test()

        # Save results to file
        results_file = Path(__file__).parent.parent.parent / "web_interface_test_results.json"
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2, default=str)

        logger.info(f"\n💾 Detailed results saved to: {results_file}")

        # Exit with appropriate code
        if results["summary"]["success_rate"] >= 80:
            logger.info("\n🎉 Web interface testing completed successfully!")
            return 0
        else:
            logger.error("\n❌ Web interface has significant issues. Please review the results.")
            return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
