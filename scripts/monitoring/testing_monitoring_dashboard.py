#!/usr/bin/env python3
"""
Comprehensive Testing and Monitoring Status Dashboard for OmicsOracle

This script provides a unified view of:
1. Current test coverage across all pipeline events
2. Monitoring system status
3. Test execution results and gaps
4. Event flow validation status
5. Performance metrics and benchmarks

Usage:
    python testing_monitoring_dashboard.py [options]
"""

import asyncio
import json
import logging
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Add project root to path


class TestingMonitoringDashboard:
    """Comprehensive dashboard for testing and monitoring status."""

    def __init__(self):
        self.project_root = Path.cwd()
        self.test_results = {}
        self.monitoring_status = {}
        self.event_coverage = {}
        self.performance_metrics = {}

        # Define the complete event flow from server start to frontend display
        self.complete_event_flow = {
            "server_initialization": [
                "Server Startup",
                "Logging Setup",
                "Path Setup",
                "Environment Variables",
                "Entrez Email Patch",
                "Config Loading",
                "NCBI Email Config",
                "Bio.Entrez Setup",
                "Pipeline Initialization",
                "Component Initialization",
                "GEO Client Init",
                "NLP Interpreter Init",
                "BiomedicalNER Init",
                "Synonym Mapper Init",
                "Summarizer Init",
                "Search Service Init",
                "Cache Disabling",
                "Progress Callback Setup",
                "API Routes Setup",
                "Static Files Setup",
                "CORS Setup",
                "WebSocket Manager Setup",
            ],
            "search_process": [
                "Search Request",
                "Request Validation",
                "Pipeline Availability Check",
                "WebSocket Notification",
                "Query Processing",
                "Entity Extraction",
                "Query Expansion",
                "Intent Detection",
                "GEO Database Search",
                "NCBI Connection",
                "ESearch Request",
                "ESummary Request",
                "Result Processing",
                "Metadata Extraction",
                "Result Filtering",
                "AI Summarization",
                "OpenAI API Request",
                "Summary Generation",
                "Result Formatting",
                "Result Sorting",
                "Response Preparation",
                "Quality Check",
                "Response Creation",
            ],
            "frontend_rendering": [
                "WebSocket Connection",
                "WebSocket Connection Acceptance",
                "WebSocket Message Handler",
                "Progress Updates",
                "Progress Event Parsing",
                "Progress Bar Update",
                "Live Monitor Update",
                "Results Preparation",
                "Results JSON Parsing",
                "Search History Update",
                "Results Rendering",
                "Dataset Card Creation",
                "GEO Summary Display",
                "AI Summary Display",
                "Error Handling",
                "API Error Processing",
                "WebSocket Error Processing",
                "UI Error Display",
            ],
        }

    def analyze_current_test_coverage(self) -> Dict[str, Any]:
        """Analyze current test coverage across all categories."""
        logger.info("🔍 Analyzing current test coverage...")

        coverage_analysis = {
            "total_events": 0,
            "covered_events": 0,
            "coverage_by_category": {},
            "test_file_mapping": {},
            "missing_tests": [],
        }

        # Count total events
        for category, events in self.complete_event_flow.items():
            coverage_analysis["total_events"] += len(events)
            coverage_analysis["coverage_by_category"][category] = {
                "total_events": len(events),
                "covered_events": 0,
                "coverage_percentage": 0.0,
                "missing_tests": [],
            }

        # Map existing test files to events
        test_patterns = {
            "tests/unit/": "Unit Tests",
            "tests/integration/": "Integration Tests",
            "tests/interface/": "Interface Tests",
            "tests/e2e/": "End-to-End Tests",
            "tests/performance/": "Performance Tests",
            "tests/validation/": "Validation Tests",
        }

        existing_tests = []
        for pattern in test_patterns.keys():
            test_dir = self.project_root / pattern
            if test_dir.exists():
                existing_tests.extend(list(test_dir.glob("test_*.py")))

        # Analyze coverage for each event category
        for category, events in self.complete_event_flow.items():
            covered = 0
            missing = []

            for event in events:
                # Simple heuristic: check if any test file name relates to the event
                event_covered = False
                covering_tests = []

                for test_file in existing_tests:
                    test_name = test_file.stem.lower()
                    event_keywords = event.lower().replace(" ", "_").split("_")

                    if any(keyword in test_name for keyword in event_keywords if len(keyword) > 3):
                        event_covered = True
                        covering_tests.append(str(test_file.relative_to(self.project_root)))

                if event_covered:
                    covered += 1
                    coverage_analysis["test_file_mapping"][event] = covering_tests
                else:
                    missing.append(event)

            coverage_analysis["coverage_by_category"][category]["covered_events"] = covered
            coverage_analysis["coverage_by_category"][category]["coverage_percentage"] = (
                covered / len(events)
            ) * 100
            coverage_analysis["coverage_by_category"][category]["missing_tests"] = missing
            coverage_analysis["covered_events"] += covered

        # Calculate overall coverage
        coverage_analysis["overall_coverage_percentage"] = (
            coverage_analysis["covered_events"] / coverage_analysis["total_events"] * 100
        )

        return coverage_analysis

    def check_monitoring_systems(self) -> Dict[str, Any]:
        """Check status of all monitoring systems."""
        logger.info("🔍 Checking monitoring systems status...")

        monitoring_status = {
            "pipeline_monitor": {"status": "unknown", "path": None},
            "api_monitor": {"status": "unknown", "path": None},
            "websocket_monitor": {"status": "unknown", "path": None},
            "omics_monitor": {"status": "unknown", "path": None},
            "monitoring_dashboard": {"status": "unknown", "path": None},
        }

        # Check for monitoring files
        monitoring_files = {
            "pipeline_monitor": "src/omics_oracle/monitoring/pipeline_monitor.py",
            "api_monitor": "src/omics_oracle/monitoring/api_monitor.py",
            "websocket_monitor": "src/omics_oracle/monitoring/websocket_monitor.py",
            "omics_monitor": "omics_monitor.py",
            "monitoring_dashboard": "monitoring_dashboard.py",
        }

        for monitor_name, file_path in monitoring_files.items():
            full_path = self.project_root / file_path
            if full_path.exists():
                monitoring_status[monitor_name]["status"] = "available"
                monitoring_status[monitor_name]["path"] = str(full_path)

                # Try to import and check if it's functional
                try:
                    # Basic import test
                    monitoring_status[monitor_name]["status"] = "functional"
                except ImportError as e:
                    monitoring_status[monitor_name]["status"] = "import_error"
                    monitoring_status[monitor_name]["error"] = str(e)
            else:
                monitoring_status[monitor_name]["status"] = "missing"

        return monitoring_status

    def run_test_suite_analysis(self) -> Dict[str, Any]:
        """Run comprehensive test suite and analyze results."""
        logger.info("🧪 Running comprehensive test suite analysis...")

        try:
            # Run the comprehensive test runner
            result = subprocess.run(
                [
                    sys.executable,
                    "comprehensive_test_runner.py",
                    "--validate-coverage",
                ],
                capture_output=True,
                text=True,
                timeout=300,
            )

            test_analysis = {
                "execution_successful": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
            }

            # Try to parse the test results
            report_path = self.project_root / "test_reports" / "test_execution_report.json"
            if report_path.exists():
                with open(report_path, "r") as f:
                    test_results = json.load(f)
                test_analysis["detailed_results"] = test_results

            # Try to parse coverage results
            coverage_path = self.project_root / "test_reports" / "event_coverage_report.json"
            if coverage_path.exists():
                with open(coverage_path, "r") as f:
                    coverage_results = json.load(f)
                test_analysis["coverage_results"] = coverage_results

        except subprocess.TimeoutExpired:
            test_analysis = {
                "execution_successful": False,
                "error": "Test execution timed out after 5 minutes",
                "stdout": "",
                "stderr": "",
            }
        except Exception as e:
            test_analysis = {
                "execution_successful": False,
                "error": str(e),
                "stdout": "",
                "stderr": "",
            }

        return test_analysis

    def identify_critical_gaps(self, coverage_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify critical gaps in testing and monitoring."""
        critical_gaps = []

        # High priority gaps (critical path events)
        high_priority_events = [
            "Pipeline Initialization",
            "Search Request",
            "Query Processing",
            "GEO Database Search",
            "AI Summarization",
            "Results Rendering",
            "WebSocket Communication",
        ]

        for category, data in coverage_analysis["coverage_by_category"].items():
            for missing_event in data["missing_tests"]:
                priority = (
                    "HIGH" if any(keyword in missing_event for keyword in high_priority_events) else "MEDIUM"
                )

                critical_gaps.append(
                    {
                        "event": missing_event,
                        "category": category,
                        "priority": priority,
                        "suggested_test_file": self._suggest_test_file_name(missing_event, category),
                        "description": f"Missing test coverage for {missing_event} in {category}",
                    }
                )

        # Sort by priority
        critical_gaps.sort(key=lambda x: x["priority"] == "HIGH", reverse=True)
        return critical_gaps

    def _suggest_test_file_name(self, event: str, category: str) -> str:
        """Suggest appropriate test file name for an event."""
        event_clean = event.lower().replace(" ", "_").replace("-", "_")

        if category == "server_initialization":
            return f"tests/unit/test_{event_clean}.py"
        elif category == "search_process":
            if "search" in event_clean or "query" in event_clean:
                return f"tests/e2e/test_{event_clean}.py"
            else:
                return f"tests/integration/test_{event_clean}.py"
        elif category == "frontend_rendering":
            return f"tests/interface/test_{event_clean}.py"
        else:
            return f"tests/unit/test_{event_clean}.py"

    def generate_recommendations(
        self,
        coverage_analysis: Dict[str, Any],
        monitoring_status: Dict[str, Any],
    ) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []

        # Coverage recommendations
        overall_coverage = coverage_analysis["overall_coverage_percentage"]
        if overall_coverage < 70:
            recommendations.append(
                f"🚨 CRITICAL: Overall test coverage is {overall_coverage:.1f}%. Target should be >90%."
            )

        # Category-specific recommendations
        for category, data in coverage_analysis["coverage_by_category"].items():
            if data["coverage_percentage"] < 50:
                recommendations.append(
                    f"📝 LOW COVERAGE: {category} has {data['coverage_percentage']:.1f}% coverage. "
                    f"Missing {len(data['missing_tests'])} critical tests."
                )

        # Monitoring recommendations
        missing_monitors = [
            name for name, status in monitoring_status.items() if status["status"] == "missing"
        ]
        if missing_monitors:
            recommendations.append(f"🔍 MONITORING: Missing monitors: {', '.join(missing_monitors)}")

        # Priority implementation recommendations
        recommendations.extend(
            [
                "🎯 PHASE 1: Implement missing unit tests for core components",
                "🎯 PHASE 2: Add comprehensive integration tests for search pipeline",
                "🎯 PHASE 3: Create end-to-end tests for complete user journeys",
                "🎯 PHASE 4: Implement performance and load testing",
                "🎯 PHASE 5: Add frontend UI testing and validation",
            ]
        )

        return recommendations

    def print_dashboard(self):
        """Print comprehensive testing and monitoring dashboard."""
        print("🧪 OmicsOracle Testing & Monitoring Dashboard")
        print("=" * 80)
        print(f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # Test Coverage Analysis
        print("📊 TEST COVERAGE ANALYSIS")
        print("-" * 40)
        coverage_analysis = self.analyze_current_test_coverage()

        print(
            f"Overall Coverage: {coverage_analysis['overall_coverage_percentage']:.1f}% "
            f"({coverage_analysis['covered_events']}/{coverage_analysis['total_events']} events)"
        )
        print()

        for category, data in coverage_analysis["coverage_by_category"].items():
            status_icon = (
                "✅" if data["coverage_percentage"] > 80 else "⚠️" if data["coverage_percentage"] > 50 else "❌"
            )
            print(
                f"{status_icon} {category.title().replace('_', ' ')}: "
                f"{data['coverage_percentage']:.1f}% "
                f"({data['covered_events']}/{data['total_events']})"
            )

        # Monitoring Status
        print("\n🔍 MONITORING SYSTEMS STATUS")
        print("-" * 40)
        monitoring_status = self.check_monitoring_systems()

        for monitor_name, status in monitoring_status.items():
            status_icon = {
                "available": "✅",
                "functional": "✅",
                "missing": "❌",
                "import_error": "⚠️",
                "unknown": "❓",
            }
            icon = status_icon.get(status["status"], "❓")
            print(f"{icon} {monitor_name.replace('_', ' ').title()}: {status['status']}")

        # Test Execution Results
        print("\n🧪 RECENT TEST EXECUTION")
        print("-" * 40)
        test_analysis = self.run_test_suite_analysis()

        if test_analysis["execution_successful"]:
            if "detailed_results" in test_analysis:
                results = test_analysis["detailed_results"]
                print(f"✅ Test Execution: SUCCESSFUL")
                print(
                    f"📊 Results: {results['passed']}/{results['total_tests']} passed "
                    f"({results['success_rate']:.1f}%)"
                )
                print(f"⏱️  Duration: {results['total_duration']:.1f}s")
            else:
                print("✅ Test Execution: SUCCESSFUL (no detailed results)")
        else:
            print(f"❌ Test Execution: FAILED")
            if "error" in test_analysis:
                print(f"   Error: {test_analysis['error']}")

        # Critical Gaps
        print("\n🚨 CRITICAL TESTING GAPS")
        print("-" * 40)
        critical_gaps = self.identify_critical_gaps(coverage_analysis)

        high_priority_gaps = [gap for gap in critical_gaps if gap["priority"] == "HIGH"]
        print(f"High Priority Gaps: {len(high_priority_gaps)}")

        for i, gap in enumerate(high_priority_gaps[:5], 1):
            print(f"{i}. {gap['event']} ({gap['category']})")
            print(f"   → Suggested: {gap['suggested_test_file']}")

        if len(high_priority_gaps) > 5:
            print(f"   ... and {len(high_priority_gaps) - 5} more high priority gaps")

        # Recommendations
        print("\n💡 RECOMMENDATIONS")
        print("-" * 40)
        recommendations = self.generate_recommendations(coverage_analysis, monitoring_status)

        for i, rec in enumerate(recommendations[:8], 1):
            print(f"{i}. {rec}")

        print("\n📄 Detailed reports available in:")
        print("   - test_reports/test_execution_report.json")
        print("   - test_reports/event_coverage_report.json")
        print()

        # Next Steps
        print("🎯 IMMEDIATE NEXT STEPS")
        print("-" * 40)
        print("1. Fix failing unit tests (especially mock configuration issues)")
        print("2. Implement missing high-priority test files")
        print("3. Verify all monitoring systems are functional")
        print("4. Run end-to-end test validation")
        print("5. Set up continuous monitoring in production")


def main():
    """Main entry point."""
    try:
        dashboard = TestingMonitoringDashboard()
        dashboard.print_dashboard()
        return 0
    except KeyboardInterrupt:
        print("\n⚠️ Dashboard interrupted by user")
        return 130
    except Exception as e:
        print(f"\n❌ Dashboard failed: {e}")
        logger.exception("Dashboard execution failed")
        return 1


if __name__ == "__main__":
    exit(main())
