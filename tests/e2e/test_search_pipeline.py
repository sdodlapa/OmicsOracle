#!/usr/bin/env python3
"""
End-to-End Test for the OmicsOracle Search Pipeline

This script tests the complete search pipeline from start to finish:
1. Pipeline initialization
2. Query processing
3. GEO search
4. Metadata retrieval
5. Summary generation
6. Result formatting
7. Frontend rendering (when run with a browser)

Usage:
    python tests/e2e/test_search_pipeline.py [--headless]
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import time
import traceback
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("e2e_test")

# Add project root to path
# Set NCBI email for testing
os.environ["NCBI_EMAIL"] = "omicsoracle@example.com"

# Try to import required modules
try:
    from Bio import Entrez

    from src.omics_oracle.core.config import Config
    from src.omics_oracle.geo_tools.geo_client import GEOClient
    from src.omics_oracle.pipeline.pipeline import OmicsOracle

    # For browser testing (optional)
    browser_available = False
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.keys import Keys
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.support.ui import WebDriverWait

        browser_available = True
    except ImportError:
        logger.warning("Selenium not available. Browser tests will be skipped.")
except ImportError as e:
    logger.error(f"Required modules not found: {e}")
    sys.exit(1)


class PipelineTestMonitor:
    """Monitor the progress of the pipeline."""

    def __init__(self):
        self.events = []
        self.stages = set()
        self.start_time = time.time()
        self.last_percentage = 0
        self.error_count = 0

    async def progress_callback(self, query_id, event):
        """Progress callback for the pipeline."""
        elapsed = time.time() - self.start_time

        # Add event to list
        self.events.append(
            {
                "timestamp": time.time(),
                "elapsed": elapsed,
                "stage": event.stage,
                "message": event.message,
                "percentage": event.percentage,
                "detail": event.detail,
            }
        )

        # Add stage to set
        self.stages.add(event.stage)

        # Log progress
        if event.percentage > self.last_percentage + 5 or "error" in event.stage.lower():
            logger.info(f"[{elapsed:.2f}s] [{event.stage}] {event.message} ({event.percentage:.1f}%)")
            self.last_percentage = event.percentage

        # Count errors
        if "error" in event.stage.lower() or "failed" in event.stage.lower():
            self.error_count += 1
            logger.error(f"Pipeline error: {event.message}")
            if event.detail:
                logger.error(f"Error detail: {event.detail}")

    def get_summary(self):
        """Get a summary of the progress."""
        return {
            "total_events": len(self.events),
            "stages": list(self.stages),
            "error_count": self.error_count,
            "duration": time.time() - self.start_time,
        }

    def save_events(self, file_path):
        """Save events to a file."""
        with open(file_path, "w") as f:
            json.dump({"events": self.events, "summary": self.get_summary()}, f, indent=2)
        logger.info(f"Saved {len(self.events)} events to {file_path}")


async def test_pipeline_e2e(query, max_results=5):
    """Run an end-to-end test of the search pipeline."""
    logger.info(f"Starting end-to-end test for query: '{query}'")
    logger.info(f"Max results: {max_results}")

    # Initialize monitor
    monitor = PipelineTestMonitor()

    try:
        # 1. Create configuration
        logger.info("1. Creating configuration...")
        config = Config()

        # Ensure NCBI email is set
        if hasattr(config, "ncbi"):
            if not hasattr(config.ncbi, "email") or not config.ncbi.email:
                logger.info("Setting NCBI email in config object")
                setattr(config.ncbi, "email", "omicsoracle@example.com")

        # Set Entrez email
        Entrez.email = "omicsoracle@example.com"
        logger.info(f"Entrez.email set to: {Entrez.email}")

        # 2. Initialize pipeline
        logger.info("2. Initializing pipeline...")
        pipeline = OmicsOracle(config, disable_cache=True)

        if pipeline is None:
            raise Exception("Pipeline initialization failed")

        # Set progress callback
        pipeline.set_progress_callback(monitor.progress_callback)

        # 3. Process query
        logger.info("3. Processing query...")
        query_start = time.time()
        result = await pipeline.process_query(query, max_results=max_results)
        query_duration = time.time() - query_start

        # 4. Analyze results
        logger.info("4. Analyzing results...")
        logger.info(f"Query processed in {query_duration:.2f}s")

        if result is None:
            logger.error("Query result is None")
            return False

        # Check for GEO IDs
        if not hasattr(result, "geo_ids") or not result.geo_ids:
            logger.warning("No GEO IDs found")
            return False

        logger.info(f"Found {len(result.geo_ids)} GEO IDs")

        # Check metadata
        if hasattr(result, "metadata") and result.metadata:
            logger.info(f"Retrieved metadata for {len(result.metadata)} datasets")

            # Check metadata fields for first result
            if len(result.metadata) > 0:
                first_metadata = result.metadata[0]
                logger.info(f"First result: {result.geo_ids[0]}")
                logger.info(f"Title: {first_metadata.get('title', 'N/A')}")
                logger.info(f"Summary available: {'Yes' if first_metadata.get('summary') else 'No'}")
        else:
            logger.warning("No metadata retrieved")

        # Check AI summaries
        if hasattr(result, "ai_summaries") and result.ai_summaries:
            logger.info("AI summaries generated")

            # Check individual summaries
            if "individual_summaries" in result.ai_summaries:
                individual_count = len(result.ai_summaries["individual_summaries"])
                logger.info(f"Found {individual_count} individual AI summaries")
        else:
            logger.warning("No AI summaries generated")

        # 5. Generate report
        logger.info("5. Generating test report...")

        # Progress summary
        progress_summary = monitor.get_summary()
        logger.info(f"Total progress events: {progress_summary['total_events']}")
        logger.info(f"Pipeline stages: {', '.join(progress_summary['stages'])}")
        logger.info(f"Error count: {progress_summary['error_count']}")
        logger.info(f"Total duration: {progress_summary['duration']:.2f}s")

        # Save events to file
        events_file = Path("pipeline_test_events.json")
        monitor.save_events(events_file)

        # Save results to file
        results_file = Path("pipeline_test_results.json")
        with open(results_file, "w") as f:
            # Convert result to dict for JSON serialization
            result_dict = {
                "query": query,
                "max_results": max_results,
                "duration": query_duration,
                "geo_ids": result.geo_ids,
                "metadata_count": len(result.metadata) if result.metadata else 0,
                "has_ai_summaries": result.ai_summaries is not None,
                "intent": result.intent,
                "total_found": len(result.geo_ids),
            }
            json.dump(result_dict, f, indent=2)

        logger.info(f"Results saved to {results_file}")

        # 6. Verify success criteria
        success = len(result.geo_ids) > 0 and progress_summary["error_count"] == 0

        if success:
            logger.info("End-to-end test completed successfully!")
        else:
            logger.warning("End-to-end test completed with issues.")

        return success

    except Exception as e:
        logger.error(f"End-to-end test failed: {e}")
        logger.error(traceback.format_exc())

        # Save events even on failure
        try:
            events_file = Path("pipeline_test_events_error.json")
            monitor.save_events(events_file)
            logger.info(f"Error events saved to {events_file}")
        except Exception as save_error:
            logger.error(f"Failed to save events: {save_error}")

        return False


async def test_browser_interaction(query, headless=True, url="http://localhost:8001"):
    """Test browser interaction with the futuristic interface."""
    if not browser_available:
        logger.warning("Selenium not available. Browser test skipped.")
        return False

    logger.info(f"Starting browser test for query: '{query}'")
    logger.info(f"Headless mode: {headless}")

    try:
        # Configure browser options
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument("--headless")

        # Initialize browser
        logger.info("Initializing browser...")
        driver = webdriver.Chrome(options=options)

        try:
            # Navigate to interface
            logger.info(f"Navigating to {url}...")
            driver.get(url)

            # Wait for page to load
            logger.info("Waiting for page to load...")
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "search-input")))

            # Enter search query
            logger.info(f"Entering search query: '{query}'...")
            search_input = driver.find_element(By.ID, "search-input")
            search_input.clear()
            search_input.send_keys(query)

            # Click search button
            logger.info("Clicking search button...")
            search_button = driver.find_element(By.ID, "search-btn")
            search_button.click()

            # Wait for search to start
            logger.info("Waiting for search to start...")
            try:
                WebDriverWait(driver, 5).until(
                    EC.text_to_be_present_in_element((By.ID, "live-monitor"), "Query monitor ready")
                )
                logger.info("Search started.")
            except Exception as e:
                logger.warning(f"Could not confirm search start: {e}")

            # Wait for results (may take a while)
            logger.info("Waiting for search results (timeout: 180s)...")

            # Take screenshots during search
            screenshots_dir = Path("browser_test_screenshots")
            screenshots_dir.mkdir(exist_ok=True)

            # Take initial screenshot
            driver.save_screenshot(str(screenshots_dir / "01_search_started.png"))

            # Wait up to 3 minutes for results
            try:
                # Either results will appear or an error message
                result_selector = (By.CSS_SELECTOR, ".result-card, .error-message")
                WebDriverWait(driver, 180).until(EC.presence_of_element_located(result_selector))

                # Take screenshot of results
                driver.save_screenshot(str(screenshots_dir / "02_search_completed.png"))

                # Check what we got
                results = driver.find_elements(By.CSS_SELECTOR, ".result-card")
                errors = driver.find_elements(By.CSS_SELECTOR, ".error-message")

                if results:
                    logger.info(f"Search completed with {len(results)} results.")

                    # Check result structure
                    first_result = results[0]

                    # Check for both summary types
                    geo_summary = first_result.find_elements(By.CSS_SELECTOR, ".geo-summary")
                    ai_summary = first_result.find_elements(By.CSS_SELECTOR, ".ai-summary")

                    if geo_summary and ai_summary:
                        logger.info("Both GEO and AI summaries present.")
                    elif geo_summary:
                        logger.warning("Only GEO summary present.")
                    elif ai_summary:
                        logger.warning("Only AI summary present.")
                    else:
                        logger.warning("No summaries present in results.")

                    return True
                elif errors:
                    error_text = errors[0].text
                    logger.warning(f"Search completed with error: {error_text}")
                    return False
                else:
                    logger.warning("Unknown result state.")
                    return False

            except Exception as e:
                logger.error(f"Timeout waiting for results: {e}")
                # Take screenshot of timeout state
                driver.save_screenshot(str(screenshots_dir / "error_timeout.png"))
                return False

        finally:
            # Clean up
            logger.info("Closing browser...")
            driver.quit()

    except Exception as e:
        logger.error(f"Browser test failed: {e}")
        logger.error(traceback.format_exc())
        return False


async def run_complete_e2e_test(
    query="dna methylation immune cells", max_results=5, browser_test=False, headless=True
):
    """Run both pipeline and browser tests."""
    # Run pipeline test
    pipeline_success = await test_pipeline_e2e(query, max_results)

    # Run browser test if requested
    browser_success = False
    if browser_test and pipeline_success:
        browser_success = await test_browser_interaction(query, headless)

    # Overall success
    if browser_test:
        return pipeline_success and browser_success
    else:
        return pipeline_success


if __name__ == "__main__":
    # Parse arguments
    parser = argparse.ArgumentParser(description="End-to-End Test for OmicsOracle Search Pipeline")
    parser.add_argument(
        "--query", type=str, default="dna methylation immune cells", help="Search query to test"
    )
    parser.add_argument("--max-results", type=int, default=5, help="Maximum number of results to retrieve")
    parser.add_argument("--browser", action="store_true", help="Run browser test after pipeline test")
    parser.add_argument("--no-headless", action="store_true", help="Run browser in non-headless mode")

    args = parser.parse_args()

    # Run tests
    success = asyncio.run(
        run_complete_e2e_test(
            query=args.query,
            max_results=args.max_results,
            browser_test=args.browser,
            headless=not args.no_headless,
        )
    )

    # Exit with appropriate code
    sys.exit(0 if success else 1)
