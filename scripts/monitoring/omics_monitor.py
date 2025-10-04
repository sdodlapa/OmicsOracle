#!/usr/bin/env python3
"""
OmicsOracle Diagnostics and Monitoring Tool

This script provides a unified interface for:
1. Running diagnostic tests on the OmicsOracle pipeline
2. Monitoring the pipeline in real-time
3. Testing components individually
4. Validating end-to-end search functionality

Usage:
    python omics_monitor.py [command] [options]

Commands:
    test          Run tests on specific components
    monitor       Start monitoring the OmicsOracle pipeline
    validate      Validate end-to-end search functionality
    diagnose      Run diagnostics on specific components
    check         Check system health
    help          Show this help message
"""

import argparse
import asyncio
import importlib
import json
import logging
import os
import sys
import time
import traceback
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("omics_monitor")

# Add project root to path
# Set NCBI email for testing
os.environ["NCBI_EMAIL"] = "omicsoracle@example.com"


def setup_argparse():
    """Set up command-line argument parsing."""
    parser = argparse.ArgumentParser(description="OmicsOracle Diagnostics and Monitoring Tool")

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Test command
    test_parser = subparsers.add_parser("test", help="Run tests on specific components")
    test_parser.add_argument(
        "component",
        choices=["pipeline", "geo", "api", "websocket", "frontend", "all"],
        help="Component to test",
    )
    test_parser.add_argument(
        "--query",
        default="dna methylation immune cells",
        help="Query to use for testing",
    )
    test_parser.add_argument(
        "--max-results",
        type=int,
        default=5,
        help="Maximum number of results to retrieve",
    )

    # Monitor command
    monitor_parser = subparsers.add_parser("monitor", help="Start monitoring the OmicsOracle pipeline")
    monitor_parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port to run the monitoring server on",
    )

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate end-to-end search functionality")
    validate_parser.add_argument(
        "--query",
        default="dna methylation immune cells",
        help="Query to use for validation",
    )
    validate_parser.add_argument(
        "--max-results",
        type=int,
        default=5,
        help="Maximum number of results to retrieve",
    )
    validate_parser.add_argument("--browser", action="store_true", help="Run browser tests")

    # Diagnose command
    diagnose_parser = subparsers.add_parser("diagnose", help="Run diagnostics on specific components")
    diagnose_parser.add_argument(
        "component",
        choices=["pipeline", "geo", "api", "all"],
        help="Component to diagnose",
    )

    # Check command
    check_parser = subparsers.add_parser("check", help="Check system health")

    return parser


async def test_pipeline(args):
    """Run tests on the pipeline component."""
    logger.info("Testing pipeline component...")

    try:
        # Import and run pipeline tests
        from tests.pipeline.test_initialization import test_pipeline_components

        result = await test_pipeline_components()

        if result:
            logger.info("Pipeline tests passed!")
            return True
        else:
            logger.error("Pipeline tests failed!")
            return False
    except Exception as e:
        logger.error(f"Error running pipeline tests: {e}")
        logger.error(traceback.format_exc())
        return False


async def test_geo(args):
    """Run tests on the GEO client component."""
    logger.info("Testing GEO client component...")

    try:
        # Import and run GEO client tests
        from tests.geo_tools.test_geo_client import test_geo_client_components

        result = await test_geo_client_components()

        if result:
            logger.info("GEO client tests passed!")
            return True
        else:
            logger.error("GEO client tests failed!")
            return False
    except Exception as e:
        logger.error(f"Error running GEO client tests: {e}")
        logger.error(traceback.format_exc())
        return False


def test_api(args):
    """Run tests on the API component."""
    logger.info("Testing API component...")

    try:
        # Import and run API tests
        from tests.interface.test_api_endpoints import test_api_endpoints

        # Run without client (will create its own)
        test_api_endpoints(None)

        logger.info("API tests passed!")
        return True
    except Exception as e:
        logger.error(f"Error running API tests: {e}")
        logger.error(traceback.format_exc())
        return False


async def test_websocket(args):
    """Run tests on the WebSocket component."""
    logger.info("Testing WebSocket component...")

    try:
        # Import and run WebSocket tests
        from tests.interface.test_api_endpoints import test_websocket_connection

        result = await test_websocket_connection()

        if result:
            logger.info("WebSocket tests passed!")
            return True
        else:
            logger.error("WebSocket tests failed or server not running!")
            return False
    except Exception as e:
        logger.error(f"Error running WebSocket tests: {e}")
        logger.error(traceback.format_exc())
        return False


async def test_frontend(args):
    """Run tests on the frontend component."""
    logger.info("Testing frontend component...")

    try:
        # Import and run frontend tests
        from tests.e2e.test_search_pipeline import test_browser_interaction

        result = await test_browser_interaction(args.query)

        if result:
            logger.info("Frontend tests passed!")
            return True
        else:
            logger.error("Frontend tests failed or server not running!")
            return False
    except Exception as e:
        logger.error(f"Error running frontend tests: {e}")
        logger.error(traceback.format_exc())
        return False


async def test_all(args):
    """Run all tests."""
    logger.info("Running all tests...")

    results = {}

    # Run pipeline tests
    results["pipeline"] = await test_pipeline(args)

    # Run GEO client tests
    results["geo"] = await test_geo(args)

    # Run API tests
    results["api"] = test_api(args)

    # Skip WebSocket and frontend tests if pipeline tests failed
    if results["pipeline"]:
        # Run WebSocket tests
        results["websocket"] = await test_websocket(args)

        # Run frontend tests
        results["frontend"] = await test_frontend(args)
    else:
        logger.warning("Skipping WebSocket and frontend tests due to pipeline failure")
        results["websocket"] = False
        results["frontend"] = False

    # Print summary
    logger.info("Test Results Summary:")
    for component, success in results.items():
        status = "PASSED" if success else "FAILED"
        logger.info(f"  {component}: {status}")

    # Overall success
    overall = all(results.values())
    if overall:
        logger.info("All tests passed!")
    else:
        logger.error("Some tests failed!")

    return overall


async def validate_search(args):
    """Validate end-to-end search functionality."""
    logger.info("Validating end-to-end search functionality...")

    try:
        # Import and run end-to-end tests
        from tests.e2e.test_search_pipeline import run_complete_e2e_test

        result = await run_complete_e2e_test(
            query=args.query,
            max_results=args.max_results,
            browser_test=args.browser,
        )

        if result:
            logger.info("Validation passed!")
            return True
        else:
            logger.error("Validation failed!")
            return False
    except Exception as e:
        logger.error(f"Error running validation: {e}")
        logger.error(traceback.format_exc())
        return False


async def diagnose_pipeline(args):
    """Run diagnostics on the pipeline component."""
    logger.info("Running pipeline diagnostics...")

    try:
        # Import and run pipeline diagnostics
        debug_pipeline_path = project_root / "debug_pipeline.py"

        if debug_pipeline_path.exists():
            logger.info("Running debug_pipeline.py...")

            # Execute the script
            os.system(f"python {debug_pipeline_path}")

            logger.info("Pipeline diagnostics complete!")
            return True
        else:
            logger.error("debug_pipeline.py not found!")
            return False
    except Exception as e:
        logger.error(f"Error running pipeline diagnostics: {e}")
        logger.error(traceback.format_exc())
        return False


async def diagnose_geo(args):
    """Run diagnostics on the GEO client component."""
    logger.info("Running GEO client diagnostics...")

    try:
        # Import and run GEO client diagnostics
        validate_ncbi_path = project_root / "validate_ncbi_config.py"

        if validate_ncbi_path.exists():
            logger.info("Running validate_ncbi_config.py...")

            # Execute the script
            os.system(f"python {validate_ncbi_path}")

            logger.info("GEO client diagnostics complete!")
            return True
        else:
            logger.error("validate_ncbi_config.py not found!")
            return False
    except Exception as e:
        logger.error(f"Error running GEO client diagnostics: {e}")
        logger.error(traceback.format_exc())
        return False


async def diagnose_api(args):
    """Run diagnostics on the API component."""
    logger.info("Running API diagnostics...")

    try:
        # Check if server is running
        import requests

        try:
            response = requests.get("http://localhost:8001/api/health")
            status = response.json()

            logger.info("API health check:")
            logger.info(f"  Status: {status.get('status', 'unknown')}")
            logger.info(f"  Pipeline available: {status.get('pipeline_available', False)}")
            logger.info(f"  Message: {status.get('message', 'No message')}")

            if "pipeline_info" in status:
                pipeline_info = status["pipeline_info"]
                logger.info("Pipeline info:")
                for key, value in pipeline_info.items():
                    logger.info(f"  {key}: {value}")

            if "environment" in status:
                env_info = status["environment"]
                logger.info("Environment info:")
                for key, value in env_info.items():
                    logger.info(f"  {key}: {value}")

            return True
        except requests.RequestException as e:
            logger.error(f"Could not connect to API: {e}")
            logger.info("Is the server running on port 8001?")
            return False
    except Exception as e:
        logger.error(f"Error running API diagnostics: {e}")
        logger.error(traceback.format_exc())
        return False


async def diagnose_all(args):
    """Run all diagnostics."""
    logger.info("Running all diagnostics...")

    results = {}

    # Run pipeline diagnostics
    results["pipeline"] = await diagnose_pipeline(args)

    # Run GEO client diagnostics
    results["geo"] = await diagnose_geo(args)

    # Run API diagnostics
    results["api"] = await diagnose_api(args)

    # Print summary
    logger.info("Diagnostics Results Summary:")
    for component, success in results.items():
        status = "SUCCESS" if success else "FAILURE"
        logger.info(f"  {component}: {status}")

    # Overall success
    overall = all(results.values())
    if overall:
        logger.info("All diagnostics passed!")
    else:
        logger.error("Some diagnostics failed!")

    return overall


async def check_system_health(args):
    """Check overall system health."""
    logger.info("Checking system health...")

    try:
        # Check API health
        import requests

        try:
            response = requests.get("http://localhost:8001/api/health")
            health_status = response.json()

            # Check pipeline
            if health_status.get("pipeline_available", False):
                logger.info("Pipeline is available")

                # Check for critical components
                pipeline_info = health_status.get("pipeline_info", {})
                if pipeline_info.get("critical_components_ready", False):
                    logger.info("Critical components are ready")

                    # Run a basic search to verify
                    search_response = requests.post(
                        "http://localhost:8001/api/search",
                        json={
                            "query": "test",
                            "max_results": 1,
                            "search_type": "comprehensive",
                        },
                    )

                    if search_response.status_code == 200:
                        logger.info("Search is working")
                        return True
                    else:
                        logger.error(f"Search returned status {search_response.status_code}")
                        return False
                else:
                    logger.error("Critical components are not ready")
                    return False
            else:
                logger.error("Pipeline is not available")
                return False
        except requests.RequestException as e:
            logger.error(f"Could not connect to API: {e}")
            logger.info("Is the server running on port 8001?")
            return False
    except Exception as e:
        logger.error(f"Error checking system health: {e}")
        logger.error(traceback.format_exc())
        return False


async def run_monitoring_server(args):
    """Run a monitoring server."""
    logger.info(f"Starting monitoring server on port {args.port}...")

    try:
        # Import FastAPI and monitoring modules
        import uvicorn
        from fastapi import FastAPI
        from fastapi.responses import JSONResponse
        from fastapi.staticfiles import StaticFiles

        # Import monitoring modules
        from src.omics_oracle.monitoring.api_monitor import get_api_stats
        from src.omics_oracle.monitoring.pipeline_monitor import get_monitor as get_pipeline_monitor

        # Create monitoring app
        app = FastAPI(
            title="OmicsOracle Monitoring",
            description="Monitoring interface for OmicsOracle",
            version="1.0.0",
        )

        # Create monitoring directory
        monitoring_dir = Path("monitoring")
        monitoring_dir.mkdir(exist_ok=True)

        # Create HTML file
        html_file = monitoring_dir / "index.html"
        with open(html_file, "w") as f:
            f.write(
                """
            <!DOCTYPE html>
            <html>
            <head>
                <title>OmicsOracle Monitoring</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
                    h1, h2 { color: #333; }
                    .card { background: #f5f5f5; border-radius: 5px; padding: 15px; margin-bottom: 20px; }
                    .stat { margin-bottom: 10px; }
                    .label { font-weight: bold; display: inline-block; width: 200px; }
                    .value { display: inline-block; }
                    .error { color: #cc0000; }
                    .success { color: #007700; }
                    pre { background: #eee; padding: 10px; border-radius: 5px; overflow-x: auto; }
                </style>
                <script>
                    // Auto-refresh every 5 seconds
                    setInterval(function() {
                        fetchData();
                    }, 5000);

                    function fetchData() {
                        fetch('/api/status')
                            .then(response => response.json())
                            .then(data => {
                                document.getElementById('status').innerHTML = JSON.stringify(data, null, 2);

                                // Update pipeline status
                                document.getElementById('pipeline-status').innerText =
                                    data.pipeline ? data.pipeline.query_count + ' queries processed' : 'Not available';

                                // Update API status
                                document.getElementById('api-status').innerText =
                                    data.api ? data.api.request_count + ' requests processed' : 'Not available';

                                // Update last refresh
                                document.getElementById('last-refresh').innerText = new Date().toLocaleTimeString();
                            })
                            .catch(error => {
                                console.error('Error fetching status:', error);
                                document.getElementById('status').innerHTML = 'Error fetching status: ' + error;
                            });
                    }

                    // Initial fetch
                    document.addEventListener('DOMContentLoaded', fetchData);
                </script>
            </head>
            <body>
                <h1>OmicsOracle Monitoring</h1>

                <div class="card">
                    <h2>System Status</h2>
                    <div class="stat">
                        <span class="label">Pipeline Status:</span>
                        <span class="value" id="pipeline-status">Loading...</span>
                    </div>
                    <div class="stat">
                        <span class="label">API Status:</span>
                        <span class="value" id="api-status">Loading...</span>
                    </div>
                    <div class="stat">
                        <span class="label">Last Refresh:</span>
                        <span class="value" id="last-refresh">Loading...</span>
                    </div>
                </div>

                <div class="card">
                    <h2>Detailed Status</h2>
                    <pre id="status">Loading...</pre>
                </div>
            </body>
            </html>
            """
            )

        # Mount static files
        app.mount(
            "/",
            StaticFiles(directory=str(monitoring_dir), html=True),
            name="static",
        )

        @app.get("/api/status")
        async def get_status():
            """Get current system status."""
            try:
                # Get pipeline stats
                pipeline_stats = get_pipeline_monitor().get_summary()

                # Get API stats
                api_stats = get_api_stats()

                # Get WebSocket stats (if available)
                websocket_stats = {}
                try:
                    # Try to import WebSocket monitor
                    from src.omics_oracle.monitoring.websocket_monitor import (
                        get_monitor as get_websocket_monitor,
                    )

                    websocket_stats = get_websocket_monitor().get_stats()
                except (ImportError, AttributeError):
                    pass

                # Build status response
                status = {
                    "timestamp": time.time(),
                    "timestamp_readable": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "pipeline": pipeline_stats,
                    "api": api_stats,
                    "websocket": websocket_stats,
                }

                return JSONResponse(status)
            except Exception as e:
                logger.error(f"Error getting status: {e}")
                return JSONResponse(
                    {
                        "error": str(e),
                        "timestamp": time.time(),
                        "timestamp_readable": time.strftime("%Y-%m-%d %H:%M:%S"),
                    }
                )

        # Run server
        logger.info(f"Monitoring server running at http://localhost:{args.port}")
        logger.info("Press Ctrl+C to stop")
        uvicorn.run(app, host="0.0.0.0", port=args.port)

        return True
    except Exception as e:
        logger.error(f"Error running monitoring server: {e}")
        logger.error(traceback.format_exc())
        return False


def main():
    """Main entry point."""
    parser = setup_argparse()
    args = parser.parse_args()

    if args.command is None or args.command == "help":
        parser.print_help()
        return 0

    try:
        if args.command == "test":
            if args.component == "pipeline":
                result = asyncio.run(test_pipeline(args))
            elif args.component == "geo":
                result = asyncio.run(test_geo(args))
            elif args.component == "api":
                result = test_api(args)
            elif args.component == "websocket":
                result = asyncio.run(test_websocket(args))
            elif args.component == "frontend":
                result = asyncio.run(test_frontend(args))
            elif args.component == "all":
                result = asyncio.run(test_all(args))
            else:
                logger.error(f"Unknown component: {args.component}")
                return 1
        elif args.command == "monitor":
            result = asyncio.run(run_monitoring_server(args))
        elif args.command == "validate":
            result = asyncio.run(validate_search(args))
        elif args.command == "diagnose":
            if args.component == "pipeline":
                result = asyncio.run(diagnose_pipeline(args))
            elif args.component == "geo":
                result = asyncio.run(diagnose_geo(args))
            elif args.component == "api":
                result = asyncio.run(diagnose_api(args))
            elif args.component == "all":
                result = asyncio.run(diagnose_all(args))
            else:
                logger.error(f"Unknown component: {args.component}")
                return 1
        elif args.command == "check":
            result = asyncio.run(check_system_health(args))
        else:
            logger.error(f"Unknown command: {args.command}")
            parser.print_help()
            return 1

        return 0 if result else 1
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        logger.error(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
