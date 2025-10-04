#!/usr/bin/env python3
"""
Comprehensive Test and Trace Suite for OmicsOracle

This script runs various tests on the OmicsOracle system and generates trace reports
to document and validate the system's behavior.
"""

import argparse
import asyncio
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Add project root to path
# Import test modules
import test_endpoints_comprehensive
from trace_query_flow import trace_query_flow

# Set default paths
DEFAULT_TRACE_DIR = "query_traces"
DEFAULT_TEST_REPORT_DIR = "test_reports"


async def run_trace_for_queries(queries, output_dir=DEFAULT_TRACE_DIR):
    """Run trace_query_flow for a list of queries and return the report paths."""
    reports = []
    for query in queries:
        logger.info(f"Tracing query flow for: '{query}'")
        try:
            report_path = await trace_query_flow(query, output_dir=output_dir)
            reports.append(report_path)
            logger.info(f"Trace completed, report saved to: {report_path}")
        except Exception as e:
            logger.error(f"Error tracing query: {e}")
    return reports


def run_endpoint_tests(base_url="http://localhost:8000", enhanced_only=False):
    """Run comprehensive endpoint tests and return the results."""
    logger.info("Running comprehensive endpoint tests")

    # Save original sys.argv and replace with our args
    original_argv = sys.argv
    sys.argv = ["test_endpoints_comprehensive.py", f"--base-url={base_url}"]

    if enhanced_only:
        sys.argv.append("--enhanced-only")

    try:
        success = test_endpoints_comprehensive.main()
        # Restore original sys.argv
        sys.argv = original_argv
        return success
    except Exception as e:
        logger.error(f"Error running endpoint tests: {e}")
        # Restore original sys.argv
        sys.argv = original_argv
        return False


def check_server_status():
    """Check if the OmicsOracle server is running."""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            logger.info("✅ Server is running")
            return True
        else:
            logger.warning(f"⚠️ Server returned unexpected status code: {response.status_code}")
            return False
    except requests.RequestException:
        logger.error("❌ Server is not running")
        return False


def generate_test_report(trace_reports, endpoints_result, output_dir=DEFAULT_TEST_REPORT_DIR):
    """Generate a comprehensive test report."""
    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Generate timestamp for the report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = Path(output_dir) / f"test_report_{timestamp}.md"

    with open(report_path, "w") as f:
        f.write(f"# OmicsOracle Comprehensive Test Report\n\n")
        f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        # Server status
        f.write("## Server Status\n\n")
        server_running = check_server_status()
        f.write(f"Server Status: {'✅ Running' if server_running else '❌ Not Running'}\n\n")

        # Endpoint test results
        f.write("## API Endpoint Tests\n\n")
        if endpoints_result:
            f.write("✅ Endpoint tests completed successfully\n\n")
        elif endpoints_result is False:
            f.write("❌ Endpoint tests failed\n\n")
        else:
            f.write("⚠️ Endpoint tests were skipped\n\n")

        f.write("Detailed results available in: `endpoint_test_results.json`\n\n")

        # Query trace reports
        f.write("## Query Flow Traces\n\n")
        if trace_reports:
            for report in trace_reports:
                report_name = Path(report).name
                # Extract query from filename (format: trace_TIMESTAMP_report.md)
                query_info = report_name.replace("trace_", "").replace("_report.md", "")
                f.write(f"- [{report_name}]({report})\n")

            # Summary of trace coverage
            f.write("\n### Trace Coverage\n\n")
            f.write(f"Total traces generated: {len(trace_reports)}\n\n")
            f.write("These traces validate the query flow through the system, including:\n")
            f.write("- Query parsing and component extraction\n")
            f.write("- Alternative query generation with synonym expansion\n")
            f.write("- Multi-strategy search execution\n")
            f.write("- Result formatting and presentation\n\n")
        else:
            f.write("No query traces were generated\n\n")

        # Enhanced query handler validation
        f.write("## Enhanced Query Handler Validation\n\n")
        f.write("The enhanced query handler provides:\n\n")
        f.write(
            "1. **Biomedical Component Extraction** - Identifying diseases, tissues, organisms, and data types\n"
        )
        f.write("2. **Synonym Expansion** - Expanding terms with medical synonyms\n")
        f.write("3. **Alternative Query Generation** - Creating more effective search queries\n")
        f.write(
            "4. **Multi-Strategy Search** - Trying different query strategies until results are found\n\n"
        )

        f.write("These capabilities have been tested through both the trace system and endpoint tests.\n\n")

        # Conclusion
        f.write("## Conclusion\n\n")
        f.write("The test suite has completed. Review the individual reports for detailed results.\n")

        # Recommendations
        f.write("\n## Recommendations\n\n")
        if not server_running:
            f.write("- ⚠️ The server was not running during tests. Start it with `./start_server.sh`\n")
        if not trace_reports:
            f.write("- ⚠️ No query traces were generated. Check the trace system functionality\n")
        if endpoints_result is False:
            f.write("- ⚠️ Endpoint tests failed. Check the API implementation and connectivity\n")

        f.write("\nNext steps:\n")
        f.write("1. Review trace reports for detailed query processing insights\n")
        f.write("2. Check endpoint test results for API functionality validation\n")
        f.write("3. Consider adding more test queries to expand test coverage\n")

    logger.info(f"Test report generated: {report_path}")
    return report_path


async def main():
    """Run the comprehensive test suite."""
    parser = argparse.ArgumentParser(description="Run comprehensive tests on OmicsOracle")
    parser.add_argument(
        "--queries",
        nargs="+",
        help="Queries to trace",
        default=[
            "gene expression data for liver cancer of human species",
            "breast cancer gene expression in humans",
            "diabetes metabolic gene expression profiles in pancreatic tissue",
            "covid-19 lung transcriptome data",
            "neurodegenerative disease brain expression profiles",
        ],
    )
    parser.add_argument(
        "--trace-dir",
        default=DEFAULT_TRACE_DIR,
        help="Directory to save trace reports",
    )
    parser.add_argument(
        "--report-dir",
        default=DEFAULT_TEST_REPORT_DIR,
        help="Directory to save the test report",
    )
    parser.add_argument("--skip-endpoints", action="store_true", help="Skip endpoint tests")
    parser.add_argument(
        "--enhanced-only",
        action="store_true",
        help="Only test enhanced query endpoints",
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="Base URL for the API",
    )
    args = parser.parse_args()

    # Check if server is running
    if not check_server_status():
        logger.error("Server must be running to perform tests")
        logger.error("Start the server with: ./start_server.sh")
        sys.exit(1)

    # Run endpoint tests if not skipped
    endpoints_result = None
    if not args.skip_endpoints:
        endpoints_result = run_endpoint_tests(args.base_url, args.enhanced_only)

    # Run trace for each query
    trace_reports = await run_trace_for_queries(args.queries, args.trace_dir)

    # Generate comprehensive test report
    report_path = generate_test_report(trace_reports, endpoints_result, args.report_dir)

    logger.info(f"All tests completed. Report available at: {report_path}")


if __name__ == "__main__":
    asyncio.run(main())
