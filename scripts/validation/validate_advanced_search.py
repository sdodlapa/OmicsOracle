#!/usr/bin/env python3
"""
OmicsOracle Advanced Search Features Validation

This script validates the advanced search features, including semantic ranking,
result clustering, and query reformulation suggestions.
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from tabulate import tabulate

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Add project root to path
try:
    from src.omics_oracle.search.advanced_search_enhancer import AdvancedSearchEnhancer
except ImportError:
    logger.error("Failed to import AdvancedSearchEnhancer. Make sure the path is correct.")
    sys.exit(1)


class AdvancedSearchValidator:
    """Validates advanced search features functionality."""

    def __init__(self):
        """Initialize the advanced search validator."""
        self.enhancer = AdvancedSearchEnhancer()
        self.results_dir = Path("test_reports")
        self.results_dir.mkdir(exist_ok=True)

        # Test data
        self.test_cases = self._generate_test_cases()

    def _generate_test_cases(self) -> List[Dict[str, Any]]:
        """
        Generate test cases for validation.

        Returns:
            List of test case dictionaries
        """
        test_cases = []

        # Test case 1: Basic query with all components
        test_cases.append(
            {
                "name": "complete_query",
                "query": "human liver cancer RNA-seq",
                "results": [
                    {
                        "id": "GSE123456",
                        "title": "RNA-seq analysis of liver cancer in human patients",
                        "metadata": {
                            "organism": "human",
                            "tissue": "liver",
                            "disease": "hepatocellular carcinoma",
                            "data_type": "RNA-seq",
                            "study_type": "expression profiling",
                        },
                    },
                    {
                        "id": "GSE789012",
                        "title": "Gene expression in liver cancer progression",
                        "metadata": {
                            "organism": "human",
                            "tissue": "liver",
                            "disease": "liver cancer",
                            "data_type": "microarray",
                            "study_type": "expression profiling",
                        },
                    },
                    {
                        "id": "GSE345678",
                        "title": "Transcriptome analysis of normal liver tissue",
                        "metadata": {
                            "organism": "human",
                            "tissue": "liver",
                            "disease": "normal",
                            "data_type": "RNA-seq",
                            "study_type": "expression profiling",
                        },
                    },
                ],
            }
        )

        # Test case 2: Query missing data type
        test_cases.append(
            {
                "name": "missing_data_type",
                "query": "brain tumor",
                "results": [
                    {
                        "id": "GSE222333",
                        "title": "RNA-seq of brain tumor samples",
                        "metadata": {
                            "organism": "human",
                            "tissue": "brain",
                            "disease": "glioblastoma",
                            "data_type": "RNA-seq",
                            "study_type": "expression profiling",
                        },
                    },
                    {
                        "id": "GSE444555",
                        "title": "Single-cell analysis of brain tumors",
                        "metadata": {
                            "organism": "human",
                            "tissue": "brain",
                            "disease": "glioma",
                            "data_type": "single cell",
                            "study_type": "expression profiling",
                        },
                    },
                ],
            }
        )

        # Test case 3: Query with diverse result types for clustering
        test_cases.append(
            {
                "name": "diverse_results",
                "query": "cancer methylation",
                "results": [
                    {
                        "id": "GSE111222",
                        "title": "DNA methylation in breast cancer",
                        "metadata": {
                            "organism": "human",
                            "tissue": "breast",
                            "disease": "breast cancer",
                            "data_type": "methylation array",
                            "study_type": "methylation profiling",
                        },
                    },
                    {
                        "id": "GSE333444",
                        "title": "Methylation patterns in lung cancer",
                        "metadata": {
                            "organism": "human",
                            "tissue": "lung",
                            "disease": "lung cancer",
                            "data_type": "methylation array",
                            "study_type": "methylation profiling",
                        },
                    },
                    {
                        "id": "GSE555666",
                        "title": "Methylation changes in mouse cancer models",
                        "metadata": {
                            "organism": "mouse",
                            "tissue": "liver",
                            "disease": "cancer",
                            "data_type": "methylation array",
                            "study_type": "methylation profiling",
                        },
                    },
                    {
                        "id": "GSE777888",
                        "title": "Methylome analysis of colon cancer",
                        "metadata": {
                            "organism": "human",
                            "tissue": "colon",
                            "disease": "colon cancer",
                            "data_type": "methylation sequencing",
                            "study_type": "methylation profiling",
                        },
                    },
                ],
            }
        )

        return test_cases

    def validate_semantic_ranking(self) -> Dict[str, Any]:
        """
        Validate the semantic ranking feature.

        Returns:
            Validation results for semantic ranking
        """
        logger.info("Validating semantic ranking...")

        validation_results = {
            "feature": "semantic_ranking",
            "test_cases": [],
            "passed": 0,
            "failed": 0,
        }

        for test_case in self.test_cases:
            case_result = {
                "name": test_case["name"],
                "query": test_case["query"],
                "success": False,
                "notes": [],
            }

            try:
                # Apply semantic ranking
                ranked_results = self.enhancer.add_semantic_ranking(
                    test_case["results"].copy(), test_case["query"]
                )

                # Validate results
                if len(ranked_results) != len(test_case["results"]):
                    case_result["notes"].append("Result count changed after ranking")
                elif not all("semantic_score" in r for r in ranked_results):
                    case_result["notes"].append("Not all results have semantic scores")
                else:
                    # Check if results are sorted by semantic score
                    scores = [r.get("semantic_score", 0) for r in ranked_results]
                    if scores != sorted(scores, reverse=True):
                        case_result["notes"].append("Results not properly sorted by semantic score")
                    else:
                        case_result["success"] = True
                        case_result["notes"].append(f"Scores range: {min(scores):.2f} to {max(scores):.2f}")

            except Exception as e:
                case_result["success"] = False
                case_result["notes"].append(f"Error: {str(e)}")

            validation_results["test_cases"].append(case_result)
            if case_result["success"]:
                validation_results["passed"] += 1
            else:
                validation_results["failed"] += 1

        return validation_results

    def validate_result_clustering(self) -> Dict[str, Any]:
        """
        Validate the result clustering feature.

        Returns:
            Validation results for result clustering
        """
        logger.info("Validating result clustering...")

        validation_results = {
            "feature": "result_clustering",
            "test_cases": [],
            "passed": 0,
            "failed": 0,
        }

        for test_case in self.test_cases:
            case_result = {
                "name": test_case["name"],
                "query": test_case["query"],
                "success": False,
                "notes": [],
            }

            try:
                # Apply clustering
                clustered_results = self.enhancer.cluster_results(test_case["results"].copy())

                # Validate results
                if "clusters" not in clustered_results:
                    case_result["notes"].append("No clusters in result")
                elif not isinstance(clustered_results["clusters"], list):
                    case_result["notes"].append("Clusters not returned as a list")
                elif len(test_case["results"]) >= 3 and len(clustered_results["clusters"]) == 0:
                    case_result["notes"].append("No clusters found for a query with diverse results")
                else:
                    case_result["success"] = True
                    case_result["notes"].append(f"Found {len(clustered_results['clusters'])} clusters")

                    # Additional checks for the diverse results test case
                    if test_case["name"] == "diverse_results" and len(clustered_results["clusters"]) < 2:
                        case_result["notes"].append("Expected multiple clusters for diverse results")
                        case_result["success"] = False

            except Exception as e:
                case_result["success"] = False
                case_result["notes"].append(f"Error: {str(e)}")

            validation_results["test_cases"].append(case_result)
            if case_result["success"]:
                validation_results["passed"] += 1
            else:
                validation_results["failed"] += 1

        return validation_results

    def validate_query_reformulation(self) -> Dict[str, Any]:
        """
        Validate the query reformulation feature.

        Returns:
            Validation results for query reformulation
        """
        logger.info("Validating query reformulation...")

        validation_results = {
            "feature": "query_reformulation",
            "test_cases": [],
            "passed": 0,
            "failed": 0,
        }

        for test_case in self.test_cases:
            case_result = {
                "name": test_case["name"],
                "query": test_case["query"],
                "success": False,
                "notes": [],
            }

            try:
                # Generate reformulations
                reformulations = self.enhancer.generate_query_reformulations(test_case["query"])

                # Validate results
                if not isinstance(reformulations, list):
                    case_result["notes"].append("Reformulations not returned as a list")
                elif test_case["name"] == "missing_data_type" and len(reformulations) == 0:
                    case_result["notes"].append("No reformulations suggested for query missing data type")
                else:
                    case_result["success"] = True
                    case_result["notes"].append(f"Generated {len(reformulations)} reformulations")

                    # Check reformulation structure
                    for ref in reformulations:
                        if not all(k in ref for k in ["query", "explanation", "confidence"]):
                            case_result["notes"].append("Reformulation missing required fields")
                            case_result["success"] = False
                            break

            except Exception as e:
                case_result["success"] = False
                case_result["notes"].append(f"Error: {str(e)}")

            validation_results["test_cases"].append(case_result)
            if case_result["success"]:
                validation_results["passed"] += 1
            else:
                validation_results["failed"] += 1

        return validation_results

    def validate_full_enhancement_pipeline(self) -> Dict[str, Any]:
        """
        Validate the full enhancement pipeline.

        Returns:
            Validation results for the full pipeline
        """
        logger.info("Validating full enhancement pipeline...")

        validation_results = {
            "feature": "full_pipeline",
            "test_cases": [],
            "passed": 0,
            "failed": 0,
        }

        for test_case in self.test_cases:
            case_result = {
                "name": test_case["name"],
                "query": test_case["query"],
                "success": False,
                "notes": [],
            }

            try:
                # Apply full enhancement pipeline
                enhanced_results = self.enhancer.enhance_search_results(
                    test_case["results"].copy(), test_case["query"]
                )

                # Validate results
                if "results" not in enhanced_results:
                    case_result["notes"].append("No results in enhanced output")
                elif "enhancements" not in enhanced_results:
                    case_result["notes"].append("No enhancements listed in output")
                else:
                    case_result["success"] = True

                    # Check which enhancements were applied
                    applied = enhanced_results["enhancements"]
                    case_result["notes"].append(f"Applied enhancements: {', '.join(applied)}")

                    # Additional checks
                    if "semantic_ranking" in applied:
                        if not all("semantic_score" in r for r in enhanced_results["results"]):
                            case_result["notes"].append("Semantic ranking claimed but scores missing")
                            case_result["success"] = False

                    if "clustering" in applied and "clusters" not in enhanced_results:
                        case_result["notes"].append("Clustering claimed but clusters missing")
                        case_result["success"] = False

                    if "query_reformulations" in applied and "query_reformulations" not in enhanced_results:
                        case_result["notes"].append("Query reformulations claimed but missing")
                        case_result["success"] = False

            except Exception as e:
                case_result["success"] = False
                case_result["notes"].append(f"Error: {str(e)}")

            validation_results["test_cases"].append(case_result)
            if case_result["success"]:
                validation_results["passed"] += 1
            else:
                validation_results["failed"] += 1

        return validation_results

    def run_all_validations(self) -> Dict[str, Any]:
        """
        Run all validation tests.

        Returns:
            Complete validation results
        """
        all_results = {
            "timestamp": datetime.now().isoformat(),
            "validations": {},
        }

        # Run individual feature validations
        all_results["validations"]["semantic_ranking"] = self.validate_semantic_ranking()
        all_results["validations"]["result_clustering"] = self.validate_result_clustering()
        all_results["validations"]["query_reformulation"] = self.validate_query_reformulation()
        all_results["validations"]["full_pipeline"] = self.validate_full_enhancement_pipeline()

        # Calculate overall results
        total_passed = sum(v["passed"] for v in all_results["validations"].values())
        total_tests = sum(v["passed"] + v["failed"] for v in all_results["validations"].values())

        all_results["summary"] = {
            "total_tests": total_tests,
            "passed": total_passed,
            "failed": total_tests - total_passed,
            "success_rate": (total_passed / total_tests) if total_tests > 0 else 0,
        }

        return all_results

    def generate_report(self, results: Dict[str, Any]) -> str:
        """
        Generate a human-readable validation report.

        Args:
            results: Validation results

        Returns:
            Markdown formatted report
        """
        report = []

        # Header
        report.append("# OmicsOracle Advanced Search Features Validation Report")
        report.append(f"Generated: {results['timestamp']}")
        report.append("")

        # Summary
        summary = results["summary"]
        report.append("## Summary")
        report.append(f"**Tests Run:** {summary['total_tests']}")
        report.append(f"**Passed:** {summary['passed']} ({summary['success_rate']*100:.1f}%)")
        report.append(f"**Failed:** {summary['failed']}")
        report.append("")

        # Feature validations
        report.append("## Feature Validations")

        for feature, validation in results["validations"].items():
            report.append(f"### {feature.replace('_', ' ').title()}")

            # Feature summary
            total = validation["passed"] + validation["failed"]
            pass_rate = (validation["passed"] / total) if total > 0 else 0
            status = "✅ PASSED" if pass_rate == 1.0 else "⚠️ PARTIAL" if pass_rate > 0 else "❌ FAILED"

            report.append(f"**Status:** {status}")
            report.append(
                f"**Tests:** {total}, **Passed:** {validation['passed']}, **Failed:** {validation['failed']}"
            )
            report.append("")

            # Test case details
            report.append("#### Test Cases")

            test_table = []
            for case in validation["test_cases"]:
                status = "✅ Pass" if case["success"] else "❌ Fail"
                notes = "; ".join(case["notes"])
                test_table.append([case["name"], case["query"], status, notes])

            report.append(
                tabulate(
                    test_table,
                    headers=["Test Case", "Query", "Status", "Notes"],
                    tablefmt="pipe",
                )
            )
            report.append("")

        return "\n".join(report)

    def save_validation_results(self, results: Dict[str, Any]) -> Dict[str, Path]:
        """
        Save validation results to files.

        Args:
            results: Validation results

        Returns:
            Dictionary with paths to generated files
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_files = {}

        # Save raw results as JSON
        json_path = self.results_dir / f"advanced_search_validation_{timestamp}.json"
        with open(json_path, "w") as f:
            json.dump(results, f, indent=2)
        output_files["json"] = json_path
        logger.info(f"Saved raw validation results to {json_path}")

        # Save formatted report as Markdown
        report = self.generate_report(results)
        md_path = self.results_dir / f"advanced_search_validation_report_{timestamp}.md"
        with open(md_path, "w") as f:
            f.write(report)
        output_files["markdown"] = md_path
        logger.info(f"Saved formatted report to {md_path}")

        return output_files


def main():
    """Main function to run the advanced search validator."""
    parser = argparse.ArgumentParser(description="OmicsOracle Advanced Search Features Validation")
    parser.add_argument(
        "--feature",
        choices=[
            "semantic_ranking",
            "clustering",
            "reformulation",
            "full_pipeline",
            "all",
        ],
        default="all",
        help="Specific feature to validate",
    )

    args = parser.parse_args()

    validator = AdvancedSearchValidator()

    if args.feature == "semantic_ranking":
        results = {
            "timestamp": datetime.now().isoformat(),
            "validations": {"semantic_ranking": validator.validate_semantic_ranking()},
            "summary": {"feature": "semantic_ranking"},
        }
    elif args.feature == "clustering":
        results = {
            "timestamp": datetime.now().isoformat(),
            "validations": {"result_clustering": validator.validate_result_clustering()},
            "summary": {"feature": "result_clustering"},
        }
    elif args.feature == "reformulation":
        results = {
            "timestamp": datetime.now().isoformat(),
            "validations": {"query_reformulation": validator.validate_query_reformulation()},
            "summary": {"feature": "query_reformulation"},
        }
    elif args.feature == "full_pipeline":
        results = {
            "timestamp": datetime.now().isoformat(),
            "validations": {"full_pipeline": validator.validate_full_enhancement_pipeline()},
            "summary": {"feature": "full_pipeline"},
        }
    else:  # all
        results = validator.run_all_validations()

    # Calculate summary for individual feature validations
    if "feature" in results["summary"]:
        feature = results["summary"]["feature"]
        validation = results["validations"][feature]
        total = validation["passed"] + validation["failed"]

        results["summary"] = {
            "total_tests": total,
            "passed": validation["passed"],
            "failed": validation["failed"],
            "success_rate": (validation["passed"] / total) if total > 0 else 0,
        }

    # Save results
    output_files = validator.save_validation_results(results)

    print("\n🔍 Advanced Search Feature Validation Complete")
    print("===========================================")

    summary = results["summary"]
    print(f"Tests Run: {summary['total_tests']}")
    print(f"Passed: {summary['passed']} ({summary['success_rate']*100:.1f}%)")
    print(f"Failed: {summary['failed']}")
    print("")

    print(f"📊 Report: {output_files['markdown']}")
    print(f"📋 Raw Data: {output_files['json']}")


if __name__ == "__main__":
    main()
