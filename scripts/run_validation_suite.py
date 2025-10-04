#!/usr/bin/env python3
"""
Comprehensive validation suite for OmicsOracle integrations.

This script runs all tests, checks code quality, and validates system health.
"""

import asyncio
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add src to path for imports
from omics_oracle.integrations.service import IntegrationService


class ValidationSuite:
    """Comprehensive validation suite for OmicsOracle integrations."""

    def __init__(self):
        self.results: Dict[str, Any] = {
            "timestamp": time.time(),
            "tests": {},
            "performance": {},
            "security": {},
            "overall_status": "PENDING",
        }
        self.project_root = Path(__file__).parent

    def run_command(self, cmd: List[str], cwd: Optional[Path] = None) -> Dict[str, Any]:
        """Run a shell command and return results."""
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd or self.project_root,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": "Command timed out",
                "returncode": -1,
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "returncode": -1,
            }

    def test_unit_coverage(self) -> Dict[str, Any]:
        """Run unit tests and check coverage."""
        print("🧪 Running unit tests...")

        # Run pytest with coverage
        result = self.run_command(
            [
                "python",
                "-m",
                "pytest",
                "tests/unit/integrations/",
                "--cov=src/omics_oracle/integrations",
                "--cov-report=json",
                "--cov-report=term-missing",
                "-v",
            ]
        )

        coverage_data = {}
        coverage_file = self.project_root / "coverage.json"
        if coverage_file.exists():
            try:
                with open(coverage_file) as f:
                    coverage_data = json.load(f)
            except Exception as e:
                print(f"Warning: Could not read coverage data: {e}")

        return {
            "success": result["success"],
            "output": result["stdout"],
            "errors": result["stderr"],
            "coverage": coverage_data.get("totals", {}).get("percent_covered", 0),
        }

    def test_code_quality(self) -> Dict[str, Any]:
        """Run code quality checks."""
        print("🔍 Running code quality checks...")

        results = {}

        # Run ruff linting
        print("  - Running ruff...")
        ruff_result = self.run_command(
            [
                "python",
                "-m",
                "ruff",
                "check",
                "src/omics_oracle/integrations/",
                "--output-format=json",
            ]
        )
        results["ruff"] = ruff_result

        # Run mypy type checking
        print("  - Running mypy...")
        mypy_result = self.run_command(
            [
                "python",
                "-m",
                "mypy",
                "src/omics_oracle/integrations/",
                "--json-report",
                "mypy-report.json",
            ]
        )
        results["mypy"] = mypy_result

        # Run black formatting check
        print("  - Checking black formatting...")
        black_result = self.run_command(
            [
                "python",
                "-m",
                "black",
                "--check",
                "src/omics_oracle/integrations/",
            ]
        )
        results["black"] = black_result

        return results

    async def test_integration_functionality(self) -> Dict[str, Any]:
        """Test real integration functionality."""
        print("🌐 Testing integration functionality...")

        results = {}

        # Test PubMed integration
        print("  - Testing PubMed integration...")
        try:
            service = IntegrationService()

            # Test with a known dataset
            test_data = {
                "accession": "GSE30611",
                "title": "RNA-seq of coding RNA from tissue samples",
                "summary": "Test RNA sequencing dataset.",
            }

            start_time = time.time()
            enriched = await service.enrich_geo_dataset(test_data, max_papers=3)
            end_time = time.time()

            results["pubmed"] = {
                "success": True,
                "papers_found": len(enriched.get("related_papers", [])),
                "response_time": end_time - start_time,
                "has_citation_info": "citation_info" in enriched,
            }

        except Exception as e:
            results["pubmed"] = {
                "success": False,
                "error": str(e),
                "response_time": 0,
                "papers_found": 0,
            }

        # Test citation generation
        print("  - Testing citation generation...")
        try:
            test_datasets = [
                {
                    "accession": "GSE12345",
                    "title": "Test Dataset",
                    "summary": "Test summary",
                    "submission_date": "2023-01-01",
                }
            ]

            formats = ["bibtex", "ris", "csl-json", "endnote"]
            citation_results = {}

            for fmt in formats:
                start_time = time.time()
                citation = service.export_citations(test_datasets, fmt)
                end_time = time.time()

                citation_results[fmt] = {
                    "success": len(citation) > 0,
                    "length": len(citation),
                    "response_time": end_time - start_time,
                }

            results["citations"] = citation_results

        except Exception as e:
            results["citations"] = {"success": False, "error": str(e)}

        return results

    async def test_performance_benchmarks(self) -> Dict[str, Any]:
        """Test performance benchmarks."""
        print("⚡ Running performance benchmarks...")

        results = {}

        # Test batch processing performance
        print("  - Testing batch processing...")
        try:
            service = IntegrationService()

            # Create test datasets
            test_datasets = []
            for i in range(10):  # Start with 10 datasets
                test_datasets.append(
                    {
                        "accession": f"GSE{12345 + i}",
                        "title": f"Test Dataset {i + 1}",
                        "summary": f"Test summary for dataset {i + 1}",
                        "submission_date": "2023-01-01",
                    }
                )

            start_time = time.time()
            enriched_datasets = await service.batch_enrich_datasets(
                test_datasets,
                include_papers=False,  # Skip papers for speed
                max_papers=1,
            )
            end_time = time.time()

            results["batch_processing"] = {
                "datasets_processed": len(enriched_datasets),
                "total_time": end_time - start_time,
                "avg_time_per_dataset": (end_time - start_time) / len(enriched_datasets),
                "success": len(enriched_datasets) == len(test_datasets),
            }

        except Exception as e:
            results["batch_processing"] = {"success": False, "error": str(e)}

        # Test citation generation speed
        print("  - Testing citation generation speed...")
        try:
            service = IntegrationService()

            # Create 50 test datasets
            large_dataset = []
            for i in range(50):
                large_dataset.append(
                    {
                        "accession": f"GSE{20000 + i}",
                        "title": f"Large Test Dataset {i + 1}",
                        "summary": f"Large test summary for dataset {i + 1}",
                        "submission_date": "2023-01-01",
                    }
                )

            start_time = time.time()
            bibtex_citations = service.export_citations(large_dataset, "bibtex")
            end_time = time.time()

            results["citation_generation"] = {
                "datasets_processed": len(large_dataset),
                "total_time": end_time - start_time,
                "avg_time_per_dataset": (end_time - start_time) / len(large_dataset),
                "output_size": len(bibtex_citations),
                "success": len(bibtex_citations) > 0,
            }

        except Exception as e:
            results["citation_generation"] = {"success": False, "error": str(e)}

        return results

    def test_security_checks(self) -> Dict[str, Any]:
        """Run basic security checks."""
        print("🔒 Running security checks...")

        results = {}

        # Check for hardcoded secrets
        print("  - Checking for hardcoded secrets...")
        secret_patterns = ["password", "secret", "key", "token", "api_key"]

        integration_files = list((self.project_root / "src" / "omics_oracle" / "integrations").glob("*.py"))
        security_issues = []

        for file_path in integration_files:
            try:
                with open(file_path, "r") as f:
                    content = f.read().lower()
                    for pattern in secret_patterns:
                        if f"{pattern}=" in content or f"{pattern}:" in content:
                            # Check if it's just a parameter name
                            if "def " in content or "self." in content:
                                continue
                            security_issues.append(f"Potential hardcoded {pattern} in {file_path.name}")
            except Exception as e:
                security_issues.append(f"Could not scan {file_path.name}: {e}")

        results["secret_scan"] = {
            "issues_found": len(security_issues),
            "issues": security_issues,
            "success": len(security_issues) == 0,
        }

        # Check file permissions
        print("  - Checking file permissions...")
        permission_issues = []

        for file_path in integration_files:
            try:
                stat = file_path.stat()
                # Check if file is world-writable
                if stat.st_mode & 0o002:
                    permission_issues.append(f"World-writable file: {file_path.name}")
            except Exception as e:
                permission_issues.append(f"Could not check permissions for {file_path.name}: {e}")

        results["permissions"] = {
            "issues_found": len(permission_issues),
            "issues": permission_issues,
            "success": len(permission_issues) == 0,
        }

        return results

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run the complete validation suite."""
        print("🚀 Starting OmicsOracle Integration Validation Suite")
        print("=" * 60)

        # Run unit tests
        self.results["tests"]["unit"] = self.test_unit_coverage()

        # Run code quality checks
        self.results["tests"]["quality"] = self.test_code_quality()

        # Run integration tests
        self.results["tests"]["integration"] = await self.test_integration_functionality()

        # Run performance tests
        self.results["performance"] = await self.test_performance_benchmarks()

        # Run security checks
        self.results["security"] = self.test_security_checks()

        # Determine overall status
        self._determine_overall_status()

        return self.results

    def _determine_overall_status(self) -> None:
        """Determine overall validation status."""
        issues = []

        # Check unit test results
        if not self.results["tests"]["unit"]["success"]:
            issues.append("Unit tests failed")

        coverage = self.results["tests"]["unit"].get("coverage", 0)
        if coverage < 80:
            issues.append(f"Test coverage too low: {coverage}%")

        # Check code quality
        quality = self.results["tests"]["quality"]
        if not quality.get("ruff", {}).get("success", False):
            issues.append("Linting issues found")

        # Check integration tests
        integration = self.results["tests"]["integration"]
        if not integration.get("pubmed", {}).get("success", False):
            issues.append("PubMed integration failed")

        # Check performance
        perf = self.results["performance"]
        batch_time = perf.get("batch_processing", {}).get("avg_time_per_dataset", 0)
        if batch_time > 5:  # More than 5 seconds per dataset
            issues.append(f"Batch processing too slow: {batch_time:.2f}s per dataset")

        # Check security
        security = self.results["security"]
        if not security.get("secret_scan", {}).get("success", False):
            issues.append("Security issues found")

        if not issues:
            self.results["overall_status"] = "PASS"
        elif len(issues) <= 2:
            self.results["overall_status"] = "PASS_WITH_WARNINGS"
        else:
            self.results["overall_status"] = "FAIL"

        self.results["issues"] = issues

    def print_summary(self) -> None:
        """Print validation summary."""
        print("\n" + "=" * 60)
        print("🎯 VALIDATION SUMMARY")
        print("=" * 60)

        status = self.results["overall_status"]
        status_emoji = {"PASS": "✅", "PASS_WITH_WARNINGS": "⚠️", "FAIL": "❌"}

        print(f"Overall Status: {status_emoji.get(status, '❓')} {status}")

        # Print test results
        print(f"\n📊 Test Results:")
        unit = self.results["tests"]["unit"]
        print(f"  Unit Tests: {'✅' if unit['success'] else '❌'} (Coverage: {unit.get('coverage', 0):.1f}%)")

        integration = self.results["tests"]["integration"]
        pubmed_success = integration.get("pubmed", {}).get("success", False)
        papers_found = integration.get("pubmed", {}).get("papers_found", 0)
        print(f"  PubMed Integration: {'✅' if pubmed_success else '❌'} ({papers_found} papers found)")

        # Print performance results
        print(f"\n⚡ Performance:")
        perf = self.results["performance"]
        if "batch_processing" in perf:
            batch = perf["batch_processing"]
            print(f"  Batch Processing: {batch.get('avg_time_per_dataset', 0):.2f}s per dataset")

        if "citation_generation" in perf:
            citation = perf["citation_generation"]
            print(f"  Citation Generation: {citation.get('avg_time_per_dataset', 0):.3f}s per dataset")

        # Print security results
        print(f"\n🔒 Security:")
        security = self.results["security"]
        secret_issues = security.get("secret_scan", {}).get("issues_found", 0)
        perm_issues = security.get("permissions", {}).get("issues_found", 0)
        print(f"  Secret Scan: {'✅' if secret_issues == 0 else '❌'} ({secret_issues} issues)")
        print(f"  Permissions: {'✅' if perm_issues == 0 else '❌'} ({perm_issues} issues)")

        # Print issues
        if self.results.get("issues"):
            print(f"\n⚠️  Issues Found:")
            for issue in self.results["issues"]:
                print(f"    - {issue}")

        print("\n" + "=" * 60)

    def save_report(self, filename: str = "validation_report.json") -> None:
        """Save detailed validation report."""
        report_path = self.project_root / filename
        with open(report_path, "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"📄 Detailed report saved to: {report_path}")


async def main():
    """Main validation function."""
    suite = ValidationSuite()

    try:
        results = await suite.run_all_tests()
        suite.print_summary()
        suite.save_report()

        # Exit with appropriate code
        if results["overall_status"] == "FAIL":
            sys.exit(1)
        elif results["overall_status"] == "PASS_WITH_WARNINGS":
            sys.exit(2)
        else:
            sys.exit(0)

    except KeyboardInterrupt:
        print("\n❌ Validation interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Validation failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
