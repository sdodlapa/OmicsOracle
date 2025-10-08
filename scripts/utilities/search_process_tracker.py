#!/usr/bin/env python3
"""
Comprehensive Search Process Tracker for OmicsOracle Futuristic Interface

This script tracks the entire search process from query input to frontend display,
capturing every event and analyzing data quality to ensure no fallback/placeholder data.
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("search_process_analysis.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8001"
TEST_QUERY = "dna methylation data for human brain cancer tissue"


class SearchProcessTracker:
    def __init__(self):
        self.events = []
        self.start_time = None
        self.analysis_results = {}

    def log_event(self, event_type: str, data: Any, timestamp: float = None):
        """Log an event with timestamp and data"""
        if timestamp is None:
            timestamp = time.time()

        event = {
            "timestamp": timestamp,
            "event_type": event_type,
            "data": data,
            "relative_time": timestamp - self.start_time if self.start_time else 0,
        }
        self.events.append(event)
        logger.info(f"📝 {event_type}: {data}")

    def analyze_data_quality(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the quality of data to detect placeholders/fallbacks"""
        quality_report = {
            "has_real_geo_data": True,
            "has_real_ai_summaries": True,
            "placeholder_indicators": [],
            "data_completeness": {},
            "suspicious_patterns": [],
        }

        # Check for placeholder/fallback indicators
        placeholder_patterns = [
            "pending for recent submissions",
            "metadata may be pending",
            "fallback data",
            "mock data",
            "placeholder",
            "test data",
            "default summary",
            "no summary available",
        ]

        if "results" in data:
            for i, result in enumerate(data["results"]):
                result_analysis = {
                    "geo_id": result.get("geo_id", "MISSING"),
                    "has_title": bool(result.get("title")),
                    "has_summary": bool(result.get("summary")),
                    "has_ai_insights": bool(result.get("ai_insights")),
                    "organism_valid": result.get("organism") not in [None, "", "Unknown", "N/A"],
                    "date_valid": result.get("publication_date") not in [None, "", "Unknown", "Recent"],
                    "sample_count_valid": isinstance(result.get("sample_count"), int)
                    and result.get("sample_count", 0) > 0,
                }

                # Check for placeholder text in summaries and AI insights
                summary_text = str(result.get("summary", "")).lower()
                ai_text = str(result.get("ai_insights", "")).lower()

                for pattern in placeholder_patterns:
                    if pattern in summary_text:
                        quality_report["placeholder_indicators"].append(
                            f"Result {i}: Summary contains '{pattern}'"
                        )
                    if pattern in ai_text:
                        quality_report["placeholder_indicators"].append(
                            f"Result {i}: AI insights contains '{pattern}'"
                        )

                # Check for suspicious patterns
                if result.get("relevance_score", 0) > 1.0:
                    quality_report["suspicious_patterns"].append(
                        f"Result {i}: Relevance score > 1.0 ({result.get('relevance_score')})"
                    )

                if result.get("title", "").startswith("GSE"):
                    quality_report["suspicious_patterns"].append(
                        f"Result {i}: Title starts with GSE (may be ID instead of title)"
                    )

                quality_report["data_completeness"][f"result_{i}"] = result_analysis

        # Overall quality assessment
        quality_report["has_real_geo_data"] = len(quality_report["placeholder_indicators"]) == 0
        quality_report["has_real_ai_summaries"] = not any(
            "AI insights contains" in indicator for indicator in quality_report["placeholder_indicators"]
        )

        return quality_report

    async def track_full_search_process(self):
        """Track the complete search process with detailed monitoring"""
        self.start_time = time.time()
        self.log_event("PROCESS_START", f"Starting comprehensive search tracking for query: '{TEST_QUERY}'")

        async with aiohttp.ClientSession() as session:
            try:
                # Step 1: Test interface availability
                self.log_event("STEP_1", "Testing interface availability")
                async with session.get(BASE_URL) as response:
                    if response.status != 200:
                        self.log_event("ERROR", f"Interface not available: {response.status}")
                        return False
                    self.log_event("SUCCESS", "Interface is available")

                # Step 2: Prepare search request
                self.log_event("STEP_2", "Preparing search request")
                search_payload = {"query": TEST_QUERY, "max_results": 10, "search_type": "comprehensive"}
                self.log_event("PAYLOAD", search_payload)

                # Step 3: Send search request with timing
                self.log_event("STEP_3", "Sending search request to API")
                search_start = time.time()

                async with session.post(
                    f"{BASE_URL}/api/search",
                    json=search_payload,
                    headers={"Content-Type": "application/json"},
                ) as response:
                    search_end = time.time()
                    api_response_time = search_end - search_start

                    self.log_event("API_TIMING", f"API response time: {api_response_time:.3f}s")

                    if response.status != 200:
                        error_text = await response.text()
                        self.log_event("ERROR", f"API request failed: {response.status} - {error_text}")
                        return False

                    # Step 4: Analyze API response
                    self.log_event("STEP_4", "Analyzing API response")
                    result_data = await response.json()

                    # Log raw response structure
                    self.log_event(
                        "RAW_RESPONSE_STRUCTURE",
                        {
                            "query": result_data.get("query"),
                            "total_found": result_data.get("total_found"),
                            "search_time": result_data.get("search_time"),
                            "results_count": len(result_data.get("results", [])),
                            "has_timestamp": "timestamp" in result_data,
                        },
                    )

                    # Step 5: Deep analysis of each result
                    self.log_event("STEP_5", "Performing deep analysis of search results")

                    for i, result in enumerate(result_data.get("results", [])):
                        self.log_event(
                            f"RESULT_{i}_ANALYSIS",
                            {
                                "geo_id": result.get("geo_id"),
                                "title_length": len(result.get("title", "")),
                                "summary_length": len(result.get("summary", "")),
                                "ai_insights_length": len(result.get("ai_insights", "")),
                                "organism": result.get("organism"),
                                "sample_count": result.get("sample_count"),
                                "platform": result.get("platform"),
                                "relevance_score": result.get("relevance_score"),
                                "publication_date": result.get("publication_date"),
                                "has_geo_link": bool(result.get("geo_id")),
                            },
                        )

                        # Log first 200 characters of summary and AI insights for quality check
                        summary_preview = (
                            result.get("summary", "")[:200] + "..."
                            if len(result.get("summary", "")) > 200
                            else result.get("summary", "")
                        )
                        ai_preview = (
                            result.get("ai_insights", "")[:200] + "..."
                            if len(result.get("ai_insights", "")) > 200
                            else result.get("ai_insights", "")
                        )

                        self.log_event(
                            f"RESULT_{i}_CONTENT_PREVIEW",
                            {"summary_preview": summary_preview, "ai_insights_preview": ai_preview},
                        )

                    # Step 6: Data quality analysis
                    self.log_event("STEP_6", "Performing data quality analysis")
                    quality_report = self.analyze_data_quality(result_data)
                    self.log_event("QUALITY_REPORT", quality_report)

                    # Step 7: Save detailed results
                    self.log_event("STEP_7", "Saving detailed analysis results")
                    await self.save_analysis_results(result_data, quality_report)

                    # Step 8: Frontend rendering test
                    self.log_event("STEP_8", "Testing frontend rendering")
                    await self.test_frontend_rendering(session)

                    self.log_event(
                        "PROCESS_COMPLETE", f"Total process time: {time.time() - self.start_time:.3f}s"
                    )
                    return True

            except Exception as e:
                self.log_event("FATAL_ERROR", f"Process failed with exception: {str(e)}")
                return False

    async def save_analysis_results(self, api_data: Dict[str, Any], quality_report: Dict[str, Any]):
        """Save comprehensive analysis results to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save raw API response
        with open(f"api_response_{timestamp}.json", "w") as f:
            json.dump(api_data, f, indent=2, default=str)

        # Save quality report
        with open(f"quality_report_{timestamp}.json", "w") as f:
            json.dump(quality_report, f, indent=2, default=str)

        # Save event timeline
        with open(f"event_timeline_{timestamp}.json", "w") as f:
            json.dump(self.events, f, indent=2, default=str)

        self.log_event("FILES_SAVED", f"Analysis files saved with timestamp {timestamp}")

    async def test_frontend_rendering(self, session):
        """Test that frontend can properly render the data"""
        try:
            # Test CSS loading
            async with session.get(f"{BASE_URL}/static/css/main_clean.css") as response:
                if response.status == 200:
                    self.log_event("FRONTEND_CSS", "CSS loads successfully")
                else:
                    self.log_event("FRONTEND_ERROR", f"CSS failed to load: {response.status}")

            # Test JavaScript loading
            async with session.get(f"{BASE_URL}/static/js/main_clean.js") as response:
                if response.status == 200:
                    js_content = await response.text()
                    # Check for important functions
                    has_search_function = "performSearch" in js_content
                    has_render_function = "renderSearchResults" in js_content
                    self.log_event(
                        "FRONTEND_JS",
                        {
                            "status": "loaded",
                            "has_search_function": has_search_function,
                            "has_render_function": has_render_function,
                            "size_kb": len(js_content) / 1024,
                        },
                    )
                else:
                    self.log_event("FRONTEND_ERROR", f"JavaScript failed to load: {response.status}")

        except Exception as e:
            self.log_event("FRONTEND_ERROR", f"Frontend test failed: {str(e)}")


async def main():
    """Main execution function"""
    print("🔍 OmicsOracle Search Process Comprehensive Tracker")
    print("=" * 60)
    print(f"📝 Query: '{TEST_QUERY}'")
    print(f"🕒 Started at: {datetime.now()}")
    print("=" * 60)

    tracker = SearchProcessTracker()
    success = await tracker.track_full_search_process()

    if success:
        print("\n✅ Search process tracking completed successfully!")
        print("📊 Check the generated files for detailed analysis:")
        print("   - search_process_analysis.log (detailed log)")
        print("   - api_response_*.json (raw API data)")
        print("   - quality_report_*.json (data quality analysis)")
        print("   - event_timeline_*.json (complete event timeline)")
    else:
        print("\n❌ Search process tracking failed!")
        print("📋 Check search_process_analysis.log for error details")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Tracking interrupted by user")
    except Exception as e:
        print(f"\n💥 Fatal error: {e}")
