#!/usr/bin/env python3
"""
OmicsOracle Comprehensive Test Runner

This script runs the complete test suite for the OmicsOracle system,
generating detailed reports and validating all components.

Usage:
    python run_tests.py [--report-dir REPORT_DIR] [--html] [--email EMAIL]
"""

import argparse
import asyncio
import datetime
import json
import logging
import os
import subprocess
import sys
import time
import traceback
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("test_runner")

# Add project root to path
# Set NCBI email for testing
os.environ["NCBI_EMAIL"] = "omicsoracle@example.com"


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="OmicsOracle Comprehensive Test Runner")
    parser.add_argument(
        "--report-dir",
        default="test_reports",
        help="Directory to store test reports",
    )
    parser.add_argument("--html", action="store_true", help="Generate HTML report")
    parser.add_argument("--email", help="Email address to send report to")
    return parser.parse_args()


class TestRunner:
    """Run tests and generate reports."""

    def __init__(self, report_dir="test_reports"):
        """Initialize the test runner."""
        self.report_dir = Path(report_dir)
        self.report_dir.mkdir(exist_ok=True)
        self.start_time = time.time()
        self.results = {}
        self.logs = {}

    async def run_tests(self):
        """Run all tests."""
        logger.info("Starting comprehensive test suite...")

        # Run pipeline initialization tests
        self.results["pipeline_init"] = await self.run_test(
            "pipeline_initialization",
            ["python", "-m", "tests.pipeline.test_initialization"],
        )

        # Run GEO client tests
        self.results["geo_client"] = await self.run_test(
            "geo_client", ["python", "-m", "tests.geo_tools.test_geo_client"]
        )

        # Run API endpoint tests
        self.results["api_endpoints"] = await self.run_test(
            "api_endpoints",
            ["python", "-m", "tests.interface.test_api_endpoints"],
        )

        # Run end-to-end tests
        self.results["e2e_search"] = await self.run_test(
            "e2e_search",
            [
                "python",
                "-m",
                "tests.e2e.test_search_pipeline",
                "--query",
                "dna methylation immune cells",
                "--max-results",
                "5",
            ],
        )

        # Run diagnostics
        self.results["pipeline_diagnostics"] = await self.run_test(
            "pipeline_diagnostics", ["python", "debug_pipeline.py"]
        )

        self.results["ncbi_validation"] = await self.run_test(
            "ncbi_validation", ["python", "validate_ncbi_config.py"]
        )

        # Generate report
        self.generate_report()

        return all(result["success"] for result in self.results.values())

    async def run_test(self, name, command):
        """Run a single test and capture output."""
        logger.info(f"Running {name} test...")

        log_file = self.report_dir / f"{name}_log.txt"
        result_file = self.report_dir / f"{name}_result.json"

        try:
            # Run the command
            start_time = time.time()

            with open(log_file, "w") as log:
                process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                )

                # Capture output
                output = []
                for line in process.stdout:
                    log.write(line)
                    output.append(line.strip())
                    logger.info(f"[{name}] {line.strip()}")

                # Wait for process to complete
                process.wait()

                # Store logs
                self.logs[name] = output

            # Check result
            duration = time.time() - start_time
            success = process.returncode == 0

            # Create result
            result = {
                "name": name,
                "command": " ".join(command),
                "success": success,
                "duration": duration,
                "return_code": process.returncode,
                "timestamp": time.time(),
                "timestamp_readable": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

            # Save result
            with open(result_file, "w") as f:
                json.dump(result, f, indent=2)

            if success:
                logger.info(f"{name} test passed in {duration:.2f}s")
            else:
                logger.error(f"{name} test failed with return code {process.returncode}")

            return result
        except Exception as e:
            logger.error(f"Error running {name} test: {e}")
            logger.error(traceback.format_exc())

            # Create error result
            result = {
                "name": name,
                "command": " ".join(command),
                "success": False,
                "duration": time.time() - start_time,
                "error": str(e),
                "timestamp": time.time(),
                "timestamp_readable": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

            # Save result
            with open(result_file, "w") as f:
                json.dump(result, f, indent=2)

            return result

    def generate_report(self):
        """Generate a comprehensive test report."""
        logger.info("Generating test report...")

        # Calculate overall status
        overall_success = all(result["success"] for result in self.results.values())
        total_duration = time.time() - self.start_time

        # Create report
        report = {
            "timestamp": time.time(),
            "timestamp_readable": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "overall_success": overall_success,
            "total_duration": total_duration,
            "results": self.results,
        }

        # Save report
        report_file = self.report_dir / "test_report.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"Test report saved to {report_file}")

        # Print summary
        logger.info("Test Results Summary:")
        for name, result in self.results.items():
            status = "PASSED" if result["success"] else "FAILED"
            duration = result.get("duration", 0)
            logger.info(f"  {name}: {status} in {duration:.2f}s")

        logger.info(f"Overall: {'PASSED' if overall_success else 'FAILED'} in {total_duration:.2f}s")

        return report

    def generate_html_report(self):
        """Generate an HTML test report."""
        logger.info("Generating HTML test report...")

        # Load report data
        report_file = self.report_dir / "test_report.json"
        with open(report_file, "r") as f:
            report = json.load(f)

        # Create HTML
        html_file = self.report_dir / "test_report.html"
        with open(html_file, "w") as f:
            f.write(
                f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>OmicsOracle Test Report</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
                    h1, h2, h3 {{ color: #333; }}
                    .card {{ background: #f5f5f5; border-radius: 5px; padding: 15px; margin-bottom: 20px; }}
                    .success {{ color: #007700; }}
                    .failure {{ color: #cc0000; }}
                    .test {{ margin-bottom: 15px; padding-bottom: 15px; border-bottom: 1px solid #ddd; }}
                    .test-header {{ display: flex; justify-content: space-between; }}
                    .test-name {{ font-weight: bold; }}
                    .test-status {{ font-weight: bold; }}
                    .test-details {{ margin-top: 10px; font-size: 0.9em; }}
                    .test-command {{ font-family: monospace; background: #eee; padding: 5px; border-radius: 3px; }}
                    .test-log {{ max-height: 200px; overflow-y: auto; background: #eee; padding: 10px; border-radius: 5px; font-family: monospace; font-size: 0.8em; white-space: pre-wrap; }}
                    .summary {{ display: flex; justify-content: space-between; }}
                    .timestamp {{ color: #666; font-size: 0.9em; }}
                </style>
            </head>
            <body>
                <h1>OmicsOracle Test Report</h1>

                <div class="card">
                    <div class="summary">
                        <div>
                            <h2>Summary</h2>
                            <p>
                                Overall Status: <span class="{'success' if report['overall_success'] else 'failure'}">
                                    {'PASSED' if report['overall_success'] else 'FAILED'}
                                </span>
                            </p>
                            <p>Total Duration: {report['total_duration']:.2f}s</p>
                        </div>
                        <div class="timestamp">
                            {report['timestamp_readable']}
                        </div>
                    </div>
                </div>

                <div class="card">
                    <h2>Test Results</h2>

                    {''.join([f'''
                    <div class="test">
                        <div class="test-header">
                            <div class="test-name">{name}</div>
                            <div class="test-status {'success' if result['success'] else 'failure'}">
                                {'PASSED' if result['success'] else 'FAILED'}
                            </div>
                        </div>
                        <div class="test-details">
                            <div>Duration: {result.get('duration', 0):.2f}s</div>
                            <div>Command: <span class="test-command">{result['command']}</span></div>
                            <div>Return Code: {result.get('return_code', 'N/A')}</div>
                            {f'<div>Error: {result["error"]}</div>' if 'error' in result else ''}
                        </div>
                        <div class="test-log">
                            {'<br>'.join(self.logs.get(name, ['No log available']))}
                        </div>
                    </div>
                    ''' for name, result in report['results'].items()])}
                </div>
            </body>
            </html>
            """
            )

        logger.info(f"HTML report saved to {html_file}")
        return html_file


async def main():
    """Main entry point."""
    args = parse_args()

    # Create test runner
    runner = TestRunner(args.report_dir)

    # Run tests
    success = await runner.run_tests()

    # Generate HTML report if requested
    if args.html:
        html_report = runner.generate_html_report()

    # Send email if requested
    if args.email:
        try:
            import smtplib
            from email.mime.application import MIMEApplication
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText

            logger.info(f"Sending report to {args.email}...")

            # Create message
            msg = MIMEMultipart()
            msg["Subject"] = f"OmicsOracle Test Report - {'PASSED' if success else 'FAILED'}"
            msg["From"] = "omicsoracle@example.com"
            msg["To"] = args.email

            # Add text
            text = f"""
            OmicsOracle Test Report

            Overall Status: {'PASSED' if success else 'FAILED'}
            Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

            See attached report for details.
            """
            msg.attach(MIMEText(text))

            # Add JSON report
            report_file = Path(args.report_dir) / "test_report.json"
            with open(report_file, "rb") as f:
                attachment = MIMEApplication(f.read(), Name="test_report.json")
                attachment["Content-Disposition"] = f'attachment; filename="test_report.json"'
                msg.attach(attachment)

            # Add HTML report if generated
            if args.html:
                html_file = Path(args.report_dir) / "test_report.html"
                with open(html_file, "rb") as f:
                    attachment = MIMEApplication(f.read(), Name="test_report.html")
                    attachment["Content-Disposition"] = f'attachment; filename="test_report.html"'
                    msg.attach(attachment)

            # Send email
            # Note: This is a simplified example - in production, use proper SMTP configuration
            # with authentication and secure connection
            smtp = smtplib.SMTP("localhost")
            smtp.sendmail(msg["From"], msg["To"], msg.as_string())
            smtp.quit()

            logger.info("Email sent successfully")
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            logger.error(traceback.format_exc())

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
