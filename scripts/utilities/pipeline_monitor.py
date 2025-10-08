#!/usr/bin/env python
"""
OmicsOracle Pipeline Monitor

This tool monitors the entire search pipeline from query to result rendering,
capturing data at each step to help identify mapping and content issues.

Usage:
    python pipeline_monitor.py --query "your search query"

The tool will:
1. Log the original query
2. Capture API request
3. Capture raw API response
4. Track dataset mapping between backend and frontend
5. Save a detailed report for analysis
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime
from urllib.parse import quote

import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("pipeline_monitor.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("pipeline_monitor")


class PipelineMonitor:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = "pipeline_reports"
        os.makedirs(self.output_dir, exist_ok=True)

        # Create a session to maintain cookies/state
        self.session = requests.Session()

        # Import visualization libraries if available
        try:
            import matplotlib.pyplot as plt

            self.visualization_available = True
        except ImportError:
            self.visualization_available = False
            logger.warning("Matplotlib not available. Visualizations will be skipped.")

        logger.info(f"Pipeline monitor initialized with base URL: {self.base_url}")

    def monitor_search_pipeline(self, query, max_results=None, search_type="comprehensive"):
        """Run the complete monitoring process for a search query"""
        logger.info(f"Starting pipeline monitor for query: '{query}'")

        # Step 1: Record query information
        query_info = {
            "original_query": query,
            "max_results_requested": max_results,
            "search_type": search_type,
            "timestamp": self.timestamp,
        }

        # Step 2: Check API health
        health_status = self.check_api_health()

        # Step 3: Make the API request and capture response
        start_time = time.time()
        api_response = self.make_api_request(query, max_results, search_type)
        request_time = time.time() - start_time

        # Step 4: Analyze response data
        analysis = self.analyze_response(api_response, query_info)

        # Step 5: Generate and save report
        report = {
            "query_info": query_info,
            "health_status": health_status,
            "request_time_seconds": request_time,
            "api_response": api_response,
            "analysis": analysis,
        }

        self.save_report(report)
        logger.info(
            f"Pipeline monitoring complete. Report saved to {self.output_dir}/{self.timestamp}_report.json"
        )

        # Print summary to console
        self.print_summary(report)

        return report

    def check_api_health(self):
        """Check the health of the API"""
        try:
            response = self.session.get(f"{self.base_url}/api/health")
            return response.json()
        except Exception as e:
            logger.error(f"Error checking API health: {str(e)}")
            return {"status": "error", "error": str(e)}

    def make_api_request(self, query, max_results=None, search_type="comprehensive"):
        """Make the search API request and return the response"""
        try:
            payload = {
                "query": query,
                "search_type": search_type,
                "disable_cache": True,
                "timestamp": int(time.time() * 1000),
            }

            if max_results is not None:
                payload["max_results"] = max_results

            logger.info(f"Making API request with payload: {payload}")

            response = self.session.post(
                f"{self.base_url}/api/search",
                headers={
                    "Content-Type": "application/json",
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0",
                },
                json=payload,
            )

            # Log response status
            logger.info(f"API response status: {response.status_code}")

            # Try to parse JSON response
            try:
                return response.json()
            except json.JSONDecodeError:
                logger.error(f"Failed to decode JSON response. Raw response: {response.text[:500]}...")
                return {
                    "error": "Invalid JSON response",
                    "raw_response": response.text[:2000],
                }

        except Exception as e:
            logger.error(f"Error making API request: {str(e)}")
            return {"error": str(e)}

    def analyze_response(self, response, query_info):
        """Analyze the API response for potential issues"""
        analysis = {
            "potential_issues": [],
            "dataset_mapping_check": [],
            "result_count_analysis": {},
            "recommended_fixes": [],
        }

        # Check if there was an error
        if "error" in response:
            analysis["potential_issues"].append(f"API error: {response.get('error')}")
            return analysis

        # Check result count consistency
        result_count = len(response.get("results", []))
        total_found = response.get("total_found", 0)

        analysis["result_count_analysis"] = {
            "results_returned": result_count,
            "total_found_reported": total_found,
            "max_results_requested": query_info.get("max_results_requested"),
        }

        if result_count != total_found and result_count == 10:
            issue = (
                f"Result count mismatch: API returned exactly 10 results but reports {total_found} total matches. "
                f"This suggests hardcoded result limit."
            )
            analysis["potential_issues"].append(issue)
            analysis["recommended_fixes"].append(
                {
                    "file": "interfaces/futuristic/static/js/main_clean.js",
                    "issue": "Hardcoded max_results limit of 10",
                    "fix": "Update the API request to allow for a configurable max_results value",
                }
            )
            analysis["recommended_fixes"].append(
                {
                    "file": "interfaces/futuristic/templates/index.html",
                    "issue": "No UI control for result count",
                    "fix": "Add a dropdown or slider to allow users to control how many results to display",
                }
            )

        # Check dataset mapping
        if "results" in response:
            for i, dataset in enumerate(response["results"]):
                # Capture key fields for each dataset
                mapping_check = {
                    "index": i,
                    "geo_id": dataset.get("geo_id", "MISSING"),
                    "title_length": len(dataset.get("title", "")) if dataset.get("title") else 0,
                    "summary_length": len(dataset.get("summary", "")) if dataset.get("summary") else 0,
                    "ai_insights_length": len(dataset.get("ai_insights", ""))
                    if dataset.get("ai_insights")
                    else 0,
                    "fields_present": [k for k in dataset.keys()],
                    "fields_missing": [],
                }

                # Check for expected fields
                expected_fields = [
                    "geo_id",
                    "title",
                    "summary",
                    "ai_insights",
                    "publication_date",
                ]
                for field in expected_fields:
                    if field not in dataset:
                        mapping_check["fields_missing"].append(field)

                # Check for potential issues in this dataset
                issues = []

                if not dataset.get("geo_id"):
                    issues.append("Missing GEO ID")

                if not dataset.get("title"):
                    issues.append("Missing title")

                if not dataset.get("summary") and not dataset.get("ai_insights"):
                    issues.append("Missing both summary and AI insights")

                # Check for suspiciously short text that might indicate truncation
                if dataset.get("summary") and len(dataset.get("summary")) < 50:
                    issues.append(f"Suspiciously short summary ({len(dataset.get('summary'))} chars)")

                if dataset.get("ai_insights") and len(dataset.get("ai_insights")) < 100:
                    issues.append(f"Suspiciously short AI insights ({len(dataset.get('ai_insights'))} chars)")

                # Check for duplicate content across datasets
                for j, other_dataset in enumerate(response["results"]):
                    if i != j:
                        if dataset.get("summary") and dataset.get("summary") == other_dataset.get("summary"):
                            issues.append(f"Duplicate summary with dataset at index {j}")

                        if dataset.get("ai_insights") and dataset.get("ai_insights") == other_dataset.get(
                            "ai_insights"
                        ):
                            issues.append(f"Duplicate AI insights with dataset at index {j}")

                mapping_check["issues"] = issues
                if issues:
                    analysis["potential_issues"].append(
                        f"Dataset {dataset.get('geo_id', f'at index {i}')} has issues: {', '.join(issues)}"
                    )

                analysis["dataset_mapping_check"].append(mapping_check)

        # Analyze metadata for missing datasets or inconsistencies
        if "metadata" in response and "datasets" in response.get("metadata", {}):
            api_dataset_count = len(response.get("metadata", {}).get("datasets", []))
            results_count = len(response.get("results", []))

            if api_dataset_count != results_count:
                analysis["potential_issues"].append(
                    f"Dataset count mismatch: API metadata shows {api_dataset_count} datasets but results contains {results_count}"
                )

        return analysis

    def save_report(self, report):
        """Save the monitoring report to a file"""
        filename = f"{self.output_dir}/{self.timestamp}_report.json"
        with open(filename, "w") as f:
            json.dump(report, f, indent=2)

        # Also save a simplified event timeline for easier analysis
        self.save_event_timeline(report)

    def save_event_timeline(self, report):
        """Extract and save a simplified event timeline from the report"""
        timeline = {
            "query": report["query_info"]["original_query"],
            "timestamp": report["query_info"]["timestamp"],
            "api_health": report["health_status"].get("status", "unknown"),
            "request_time": report["request_time_seconds"],
            "results_returned": len(report["api_response"].get("results", [])),
            "total_found": report["api_response"].get("total_found", 0),
            "potential_issues": report["analysis"]["potential_issues"],
        }

        filename = f"{self.output_dir}/{self.timestamp}_timeline.json"
        with open(filename, "w") as f:
            json.dump(timeline, f, indent=2)

    def print_summary(self, report):
        """Print a human-readable summary of the monitoring results"""
        print("\n" + "=" * 80)
        print(f"PIPELINE MONITOR SUMMARY FOR: '{report['query_info']['original_query']}'")
        print("=" * 80)

        print(f"\nAPI Health: {report['health_status'].get('status', 'unknown')}")
        print(f"Request Time: {report['request_time_seconds']:.2f} seconds")
        print(f"Results Returned: {len(report['api_response'].get('results', []))}")
        print(f"Total Results Reported by API: {report['api_response'].get('total_found', 0)}")

        if report["analysis"]["potential_issues"]:
            print("\nPOTENTIAL ISSUES DETECTED:")
            for i, issue in enumerate(report["analysis"]["potential_issues"]):
                print(f"{i+1}. {issue}")
        else:
            print("\nNo potential issues detected.")

        if "recommended_fixes" in report["analysis"] and report["analysis"]["recommended_fixes"]:
            print("\nRECOMMENDED FIXES:")
            for i, fix in enumerate(report["analysis"]["recommended_fixes"]):
                print(f"{i+1}. File: {fix['file']}")
                print(f"   Issue: {fix['issue']}")
                print(f"   Fix: {fix['fix']}")
                print()

        print(
            "\nDetailed report saved to:",
            f"{self.output_dir}/{self.timestamp}_report.json",
        )

        # Generate visualization if available
        if self.visualization_available and len(report["api_response"].get("results", [])) > 0:
            try:
                self.generate_visualizations(report)
                print(
                    "Visualizations saved to:",
                    f"{self.output_dir}/{self.timestamp}_visualizations.png",
                )
            except Exception as e:
                logger.error(f"Error generating visualizations: {str(e)}")

        print("=" * 80)

    def generate_visualizations(self, report):
        """Generate visualizations for the report data"""
        if not self.visualization_available:
            return

        import matplotlib.pyplot as plt
        import numpy as np

        # Create a figure with multiple subplots
        fig, axs = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle(
            f'Pipeline Analysis for Query: "{report["query_info"]["original_query"]}"',
            fontsize=16,
        )

        # Plot 1: Result counts
        axs[0, 0].bar(
            ["Results Returned", "Total Reported"],
            [
                len(report["api_response"].get("results", [])),
                report["api_response"].get("total_found", 0),
            ],
        )
        axs[0, 0].set_title("Result Counts")
        axs[0, 0].set_ylabel("Count")

        # Plot 2: Content lengths
        if "results" in report["api_response"] and len(report["api_response"]["results"]) > 0:
            summary_lengths = [len(d.get("summary", "")) for d in report["api_response"]["results"]]
            ai_lengths = [len(d.get("ai_insights", "")) for d in report["api_response"]["results"]]

            x = np.arange(len(summary_lengths))
            width = 0.35

            axs[0, 1].bar(x - width / 2, summary_lengths, width, label="Summary Length")
            axs[0, 1].bar(x + width / 2, ai_lengths, width, label="AI Insights Length")
            axs[0, 1].set_title("Content Lengths by Dataset")
            axs[0, 1].set_xlabel("Dataset Index")
            axs[0, 1].set_ylabel("Character Count")
            axs[0, 1].legend()

            # Set x-ticks to be integers
            axs[0, 1].set_xticks(x)

        # Plot 3: Issues by dataset
        if "dataset_mapping_check" in report["analysis"]:
            datasets = [
                d.get("geo_id", f"Dataset {i}")
                for i, d in enumerate(report["analysis"]["dataset_mapping_check"])
            ]
            issue_counts = [len(d.get("issues", [])) for d in report["analysis"]["dataset_mapping_check"]]

            axs[1, 0].bar(range(len(datasets)), issue_counts)
            axs[1, 0].set_title("Issues by Dataset")
            axs[1, 0].set_xlabel("Dataset")
            axs[1, 0].set_ylabel("Issue Count")

            # Only show x labels if there are few datasets
            if len(datasets) <= 10:
                axs[1, 0].set_xticks(range(len(datasets)))
                axs[1, 0].set_xticklabels(datasets, rotation=45, ha="right")

        # Plot 4: Field presence
        if (
            "dataset_mapping_check" in report["analysis"]
            and len(report["analysis"]["dataset_mapping_check"]) > 0
        ):
            all_fields = set()
            for dataset in report["analysis"]["dataset_mapping_check"]:
                all_fields.update(dataset.get("fields_present", []))

            field_counts = {field: 0 for field in all_fields}
            for dataset in report["analysis"]["dataset_mapping_check"]:
                for field in dataset.get("fields_present", []):
                    field_counts[field] += 1

            fields = list(field_counts.keys())
            counts = [field_counts[field] for field in fields]

            axs[1, 1].bar(range(len(fields)), counts)
            axs[1, 1].set_title("Field Presence Across Datasets")
            axs[1, 1].set_xlabel("Field")
            axs[1, 1].set_ylabel("Dataset Count")
            axs[1, 1].set_xticks(range(len(fields)))
            axs[1, 1].set_xticklabels(fields, rotation=45, ha="right")

        plt.tight_layout()
        plt.savefig(f"{self.output_dir}/{self.timestamp}_visualizations.png", dpi=300)
        plt.close()

    def get_frontend_html(self):
        """Retrieve the frontend HTML to analyze frontend components"""
        try:
            response = self.session.get(f"{self.base_url}/")
            return response.text
        except Exception as e:
            logger.error(f"Error retrieving frontend HTML: {str(e)}")
            return None

    def analyze_field_consistency(self, results):
        """Analyze field consistency across all datasets"""
        if not results:
            return {"consistent_fields": [], "inconsistent_fields": {}}

        # Count presence of each field
        field_presence = {}
        all_fields = set()

        for dataset in results:
            dataset_fields = set(dataset.keys())
            all_fields.update(dataset_fields)

            for field in dataset_fields:
                if field not in field_presence:
                    field_presence[field] = 0
                field_presence[field] += 1

        # Categorize fields
        consistent_fields = []
        inconsistent_fields = {}

        for field, count in field_presence.items():
            if count == len(results):
                consistent_fields.append(field)
            else:
                inconsistent_fields[field] = count

        return {
            "consistent_fields": consistent_fields,
            "inconsistent_fields": inconsistent_fields,
        }

    def save_mapping_diagnosis(self, fields_analysis, report):
        """Save detailed mapping diagnosis information"""
        diagnosis = {
            "timestamp": self.timestamp,
            "query": report["query_info"]["original_query"],
            "field_consistency": fields_analysis,
        }

        # Save full field information for every dataset
        if "results" in report["api_response"] and report["api_response"]["results"]:
            diagnosis["dataset_fields"] = {}
            for i, dataset in enumerate(report["api_response"]["results"]):
                diagnosis["dataset_fields"][f"dataset_{i}"] = {
                    "geo_id": dataset.get("geo_id", "UNKNOWN"),
                    "fields_present": list(dataset.keys()),
                }

        # Save diagnosis report
        with open(f"{self.output_dir}/mapping_diagnosis_{self.timestamp}.json", "w") as f:
            json.dump(diagnosis, f, indent=2)

    def compare_search_results(self, report1, report2):
        """Compare search results between two different endpoints"""
        results1 = report1["api_response"].get("results", [])
        results2 = report2["api_response"].get("results", [])

        comparison = {
            "timestamp": self.timestamp,
            "query": report1["query_info"]["original_query"],
            "result_count_1": len(results1),
            "result_count_2": len(results2),
            "matching_datasets": 0,
            "different_fields": [],
            "dataset_comparisons": [],
        }

        # Find matching datasets by GEO ID
        geo_id_map = {}
        for i, dataset in enumerate(results1):
            geo_id = dataset.get("geo_id")
            if geo_id:
                geo_id_map[geo_id] = i

        # Compare matching datasets
        for i, dataset in enumerate(results2):
            geo_id = dataset.get("geo_id")
            if not geo_id or geo_id not in geo_id_map:
                continue

            comparison["matching_datasets"] += 1
            match_idx = geo_id_map[geo_id]
            matching_dataset = results1[match_idx]

            # Compare fields
            dataset_diff = {"geo_id": geo_id, "different_fields": []}

            # Find common fields
            common_fields = set(dataset.keys()) & set(matching_dataset.keys())

            for field in common_fields:
                # Skip complex comparison for large text fields
                if (
                    field in ["summary", "ai_insights"]
                    and isinstance(dataset.get(field), str)
                    and isinstance(matching_dataset.get(field), str)
                ):
                    # Just compare lengths for large text fields
                    len1 = len(matching_dataset.get(field))
                    len2 = len(dataset.get(field))

                    if abs(len1 - len2) > min(len1, len2) * 0.1:  # More than 10% difference
                        dataset_diff["different_fields"].append(field)
                        if field not in comparison["different_fields"]:
                            comparison["different_fields"].append(field)
                else:
                    # Direct comparison for other fields
                    if dataset.get(field) != matching_dataset.get(field):
                        dataset_diff["different_fields"].append(field)
                        if field not in comparison["different_fields"]:
                            comparison["different_fields"].append(field)

            comparison["dataset_comparisons"].append(dataset_diff)

        return comparison


def main():
    parser = argparse.ArgumentParser(description="Monitor the OmicsOracle search pipeline")
    parser.add_argument("--query", required=True, help="The search query to monitor")
    parser.add_argument("--max-results", type=int, help="Maximum number of results to request")
    parser.add_argument(
        "--search-type",
        default="comprehensive",
        choices=["comprehensive", "quick", "detailed"],
        help="Type of search to perform",
    )
    parser.add_argument(
        "--api-url",
        default="http://localhost:8000",
        help="Base URL for the API",
    )
    parser.add_argument(
        "--compare-versions",
        action="store_true",
        help="Compare against a different version/endpoint",
    )
    parser.add_argument(
        "--compare-url",
        default="http://localhost:5000",
        help="Base URL for comparison API endpoint",
    )
    parser.add_argument(
        "--diagnose-mapping",
        action="store_true",
        help="Perform deep analysis of dataset mapping issues",
    )

    args = parser.parse_args()

    monitor = PipelineMonitor(base_url=args.api_url)

    # Standard monitoring
    report = monitor.monitor_search_pipeline(args.query, args.max_results, args.search_type)

    # Additional diagnostics if requested
    if args.diagnose_mapping:
        print("\n" + "=" * 80)
        print("RUNNING DETAILED MAPPING DIAGNOSIS")
        print("=" * 80)

        try:
            # Get frontend HTML to analyze frontend/backend mapping
            html = monitor.get_frontend_html()
            if html:
                print("\nAnalyzing frontend/backend integration...")
                # Here we could parse the HTML and JavaScript to detect mapping issues

            # Analyze response data in more detail
            if "results" in report["api_response"] and report["api_response"]["results"]:
                print("\nAnalyzing dataset field consistency...")

                # Check field consistency across all datasets
                fields_analysis = monitor.analyze_field_consistency(report["api_response"]["results"])

                print(
                    f"Found {len(fields_analysis['consistent_fields'])} consistent fields across all datasets"
                )
                print(f"Found {len(fields_analysis['inconsistent_fields'])} inconsistent fields")

                if fields_analysis["inconsistent_fields"]:
                    print("\nInconsistent fields detected:")
                    for field, presence in fields_analysis["inconsistent_fields"].items():
                        print(
                            f"  - {field}: present in {presence}/{len(report['api_response']['results'])} datasets"
                        )

                # Save diagnostic data
                monitor.save_mapping_diagnosis(fields_analysis, report)

        except Exception as e:
            print(f"Error during mapping diagnosis: {str(e)}")

    # Compare with different endpoint if requested
    if args.compare_versions:
        print("\n" + "=" * 80)
        print(f"COMPARING WITH ALTERNATE ENDPOINT: {args.compare_url}")
        print("=" * 80)

        try:
            compare_monitor = PipelineMonitor(base_url=args.compare_url)
            compare_report = compare_monitor.monitor_search_pipeline(
                args.query, args.max_results, args.search_type
            )

            # Compare the two reports
            print("\nComparing search results between endpoints...")
            result_diff = monitor.compare_search_results(report, compare_report)

            print(
                f"Results count: {len(report['api_response'].get('results', []))} vs {len(compare_report['api_response'].get('results', []))}"
            )
            print(f"Fields with differences: {len(result_diff['different_fields'])}")

            if result_diff["different_fields"]:
                print("\nKey differences detected:")
                for field in result_diff["different_fields"][:5]:  # Show only first 5 differences
                    print(f"  - {field}")

            # Save comparison report
            with open(f"{monitor.output_dir}/comparison_{monitor.timestamp}.json", "w") as f:
                json.dump(result_diff, f, indent=2)

        except Exception as e:
            print(f"Error during comparison: {str(e)}")


if __name__ == "__main__":
    main()
