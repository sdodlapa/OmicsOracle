#!/usr/bin/env python3
"""
Comprehensive Web Interface Testing Suite for OmicsOracle

This module integrates all testing frameworks and provides unified reporting.
"""

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional


# Simple test runner without complex imports for now
class ComprehensiveTestRunner:
    """Comprehensive test runner for all web interface testing."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize comprehensive test runner."""
        self.base_url = base_url
        self.results: Dict[str, Any] = {}
        self.start_time = time.time()

    def run_simple_availability_test(self) -> Dict[str, Any]:
        """Run a simple availability test using requests."""
        try:
            import requests

            print("🔍 Testing basic availability...")

            endpoints = [
                self.base_url,
                f"{self.base_url}/search",
                f"{self.base_url}/api/health",
            ]

            results = {
                "endpoints_tested": len(endpoints),
                "endpoints_available": 0,
                "response_times": {},
                "status_codes": {},
                "errors": [],
            }

            for endpoint in endpoints:
                try:
                    start = time.time()
                    response = requests.get(endpoint, timeout=10)
                    duration = time.time() - start

                    endpoint_name = endpoint.split("/")[-1] or "home"
                    results["response_times"][endpoint_name] = duration
                    results["status_codes"][endpoint_name] = response.status_code

                    if response.status_code == 200:
                        results["endpoints_available"] += 1

                except Exception as e:
                    endpoint_name = endpoint.split("/")[-1] or "home"
                    results["errors"].append(f"{endpoint_name}: {str(e)}")

            results["availability_score"] = results["endpoints_available"] / results["endpoints_tested"] * 100

            return results

        except ImportError:
            return {"error": "requests library not available", "skipped": True}
        except Exception as e:
            return {"error": str(e), "failed": True}

    def run_all_available_tests(self) -> Dict[str, Any]:
        """Run all available tests."""
        print("🚀 Starting Comprehensive Web Interface Testing")
        print(f"📍 Target URL: {self.base_url}")
        print(f"🕐 Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("")

        # Run basic availability test
        self.results["availability"] = self.run_simple_availability_test()

        # Try to run other tests if available
        self._try_load_tests()
        self._try_security_tests()
        self._try_browser_tests()
        self._try_mobile_tests()

        # Generate comprehensive report
        comprehensive_report = self._generate_report()

        # Save and display results
        self._save_results(comprehensive_report)
        self._print_summary(comprehensive_report)

        return comprehensive_report

    def _try_load_tests(self) -> None:
        """Try to run load tests if available."""
        try:
            from performance.test_load_testing import LoadTestSuite

            print("🔄 Running load tests...")

            load_suite = LoadTestSuite(self.base_url)
            results = load_suite.run_comprehensive_load_test(duration=30, users=5)
            self.results["load_testing"] = results

            print("✅ Load tests completed")

        except ImportError:
            print("⏭️  Load testing suite not available")
            self.results["load_testing"] = {
                "skipped": True,
                "reason": "Module not available",
            }
        except Exception as e:
            print(f"❌ Load tests failed: {str(e)}")
            self.results["load_testing"] = {"error": str(e), "failed": True}

    def _try_security_tests(self) -> None:
        """Try to run security tests if available."""
        try:
            import requests

            print("🔒 Running basic security checks...")

            # Basic security headers check
            response = requests.get(self.base_url, timeout=10)

            security_headers = [
                "X-Content-Type-Options",
                "X-Frame-Options",
                "X-XSS-Protection",
                "Strict-Transport-Security",
                "Content-Security-Policy",
            ]

            headers_present = sum(1 for header in security_headers if header in response.headers)

            self.results["security_basic"] = {
                "headers_tested": len(security_headers),
                "headers_present": headers_present,
                "security_score": (headers_present / len(security_headers)) * 100,
                "headers_found": [h for h in security_headers if h in response.headers],
            }

            print("✅ Basic security checks completed")

        except Exception as e:
            print(f"❌ Security tests failed: {str(e)}")
            self.results["security_basic"] = {"error": str(e), "failed": True}

    def _try_browser_tests(self) -> None:
        """Try to run browser tests if available."""
        try:
            # Check if we can at least validate HTML structure
            from html.parser import HTMLParser

            import requests

            print("🌐 Running basic HTML validation...")

            response = requests.get(self.base_url, timeout=10)
            if response.status_code == 200:
                html_content = response.text

                # Basic HTML checks
                has_doctype = html_content.strip().lower().startswith("<!doctype")
                has_title = "<title>" in html_content.lower()
                has_meta_viewport = 'name="viewport"' in html_content.lower()
                has_css = any(tag in html_content.lower() for tag in ["<style", "<link", ".css"])
                has_js = any(tag in html_content.lower() for tag in ["<script", ".js"])

                html_score = (
                    sum(
                        [
                            has_doctype,
                            has_title,
                            has_meta_viewport,
                            has_css,
                            has_js,
                        ]
                    )
                    / 5
                    * 100
                )

                self.results["html_validation"] = {
                    "has_doctype": has_doctype,
                    "has_title": has_title,
                    "has_meta_viewport": has_meta_viewport,
                    "has_css": has_css,
                    "has_js": has_js,
                    "html_score": html_score,
                }

                print("✅ HTML validation completed")

        except Exception as e:
            print(f"❌ HTML validation failed: {str(e)}")
            self.results["html_validation"] = {"error": str(e), "failed": True}

    def _try_mobile_tests(self) -> None:
        """Try to run mobile tests if available."""
        try:
            import requests

            print("📱 Running basic mobile checks...")

            # Test with mobile user agent
            mobile_headers = {
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15"
            }

            response = requests.get(self.base_url, headers=mobile_headers, timeout=10)

            if response.status_code == 200:
                content = response.text.lower()

                # Basic mobile optimization checks
                has_viewport = 'name="viewport"' in content
                has_responsive_css = any(
                    indicator in content for indicator in ["@media", "responsive", "mobile"]
                )
                has_touch_icons = "apple-touch-icon" in content

                mobile_score = sum([has_viewport, has_responsive_css, has_touch_icons]) / 3 * 100

                self.results["mobile_basic"] = {
                    "has_viewport": has_viewport,
                    "has_responsive_css": has_responsive_css,
                    "has_touch_icons": has_touch_icons,
                    "mobile_score": mobile_score,
                    "page_size": len(response.content),
                }

                print("✅ Basic mobile checks completed")

        except Exception as e:
            print(f"❌ Mobile tests failed: {str(e)}")
            self.results["mobile_basic"] = {"error": str(e), "failed": True}

    def _generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report."""
        end_time = time.time()
        total_duration = end_time - self.start_time

        # Calculate scores
        scores = {}

        # Availability score
        availability = self.results.get("availability", {})
        if not availability.get("error") and not availability.get("skipped"):
            scores["availability"] = availability.get("availability_score", 0)

        # Load testing score
        load_result = self.results.get("load_testing", {})
        if not load_result.get("error") and not load_result.get("skipped"):
            error_rate = load_result.get("error_rate", 100)
            scores["performance"] = max(0, 100 - error_rate)

        # Security score
        security = self.results.get("security_basic", {})
        if not security.get("error") and not security.get("skipped"):
            scores["security"] = security.get("security_score", 0)

        # HTML validation score
        html_val = self.results.get("html_validation", {})
        if not html_val.get("error") and not html_val.get("skipped"):
            scores["html"] = html_val.get("html_score", 0)

        # Mobile score
        mobile = self.results.get("mobile_basic", {})
        if not mobile.get("error") and not mobile.get("skipped"):
            scores["mobile"] = mobile.get("mobile_score", 0)

        # Overall score
        overall_score = sum(scores.values()) / len(scores) if scores else 0

        # Test status
        if overall_score >= 80:
            test_status = "EXCELLENT"
        elif overall_score >= 70:
            test_status = "GOOD"
        elif overall_score >= 60:
            test_status = "FAIR"
        elif overall_score >= 50:
            test_status = "POOR"
        else:
            test_status = "CRITICAL"

        # Generate recommendations
        recommendations = []

        if scores.get("availability", 100) < 100:
            recommendations.append("Fix endpoint availability issues")
        if scores.get("security", 0) < 80:
            recommendations.append("Implement security headers")
        if scores.get("html", 0) < 80:
            recommendations.append("Improve HTML structure and validation")
        if scores.get("mobile", 0) < 80:
            recommendations.append("Enhance mobile optimization")
        if scores.get("performance", 0) < 80:
            recommendations.append("Optimize application performance")

        return {
            "test_metadata": {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "base_url": self.base_url,
                "total_duration": total_duration,
                "tests_run": list(self.results.keys()),
            },
            "overall_assessment": {
                "overall_score": overall_score,
                "test_status": test_status,
                "category_scores": scores,
            },
            "detailed_results": self.results,
            "recommendations": recommendations,
            "summary": {
                "tests_passed": sum(
                    1 for r in self.results.values() if not r.get("error") and not r.get("failed")
                ),
                "tests_failed": sum(1 for r in self.results.values() if r.get("error") or r.get("failed")),
                "tests_skipped": sum(1 for r in self.results.values() if r.get("skipped")),
                "total_tests": len(self.results),
            },
        }

    def _save_results(self, report: Dict[str, Any]) -> None:
        """Save test results to files."""
        # Create results directory
        results_dir = Path("test_results")
        results_dir.mkdir(exist_ok=True)

        timestamp = time.strftime("%Y%m%d_%H%M%S")

        # Save comprehensive report
        comprehensive_file = results_dir / f"comprehensive_test_report_{timestamp}.json"
        with open(comprehensive_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        print(f"📄 Comprehensive report saved to: {comprehensive_file}")

    def _print_summary(self, report: Dict[str, Any]) -> None:
        """Print test summary."""
        print("")
        print("=" * 80)
        print("🏁 COMPREHENSIVE TESTING SUMMARY")
        print("=" * 80)

        assessment = report["overall_assessment"]
        summary = report["summary"]

        print(f"📊 Overall Score: {assessment['overall_score']:.1f}/100 ({assessment['test_status']})")
        print(f"📈 Tests Passed: {summary['tests_passed']}/{summary['total_tests']}")
        print(f"❌ Tests Failed: {summary['tests_failed']}")
        print(f"⏭️  Tests Skipped: {summary['tests_skipped']}")
        print(f"⏱️  Total Duration: {report['test_metadata']['total_duration']:.1f} seconds")

        print("")
        print("📋 Category Scores:")
        for category, score in assessment["category_scores"].items():
            print(f"   • {category.title()}: {score:.1f}/100")

        if report["recommendations"]:
            print("")
            print("🔧 Recommendations:")
            for i, rec in enumerate(report["recommendations"], 1):
                print(f"   {i}. {rec}")

        print("")
        print("=" * 80)


def main():
    """Main function for running comprehensive tests."""
    import argparse

    parser = argparse.ArgumentParser(description="Comprehensive Web Interface Testing")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL to test")

    args = parser.parse_args()

    # Run comprehensive tests
    runner = ComprehensiveTestRunner(args.url)
    runner.run_all_available_tests()


if __name__ == "__main__":
    main()
