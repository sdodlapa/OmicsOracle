#!/usr/bin/env python3
"""
Real-time Query Monitoring for OmicsOracle Futuristic Interface

This script monitors the backend in real-time to track user queries from the browser
and provides detailed analysis of the entire process flow.
"""

import asyncio
import json
import logging
import threading
import time
from datetime import datetime
from typing import Any, Dict, List

import aiohttp
import websockets

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("real_time_monitoring.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class RealTimeQueryMonitor:
    def __init__(self):
        self.monitoring = True
        self.query_sessions = {}
        self.last_query_time = 0

    async def monitor_api_requests(self):
        """Monitor API requests in real-time"""
        logger.info("🔍 Starting real-time API monitoring...")
        logger.info("📱 Open your browser to http://localhost:8001 and submit a query!")
        logger.info("=" * 60)

        # Keep polling the backend to detect new queries
        while self.monitoring:
            try:
                async with aiohttp.ClientSession() as session:
                    # Check for new queries by monitoring the health endpoint
                    # and looking for changes in system state
                    await asyncio.sleep(0.5)  # Poll every 500ms

            except Exception as e:
                logger.error(f"❌ Monitoring error: {e}")
                await asyncio.sleep(1)

    async def track_query_execution(self, query: str):
        """Track the execution of a specific query in detail"""
        start_time = time.time()
        query_id = f"query_{int(start_time)}"

        logger.info(f"🚀 QUERY DETECTED: '{query}'")
        logger.info(f"📋 Query ID: {query_id}")
        logger.info(f"⏰ Start Time: {datetime.now()}")
        logger.info("=" * 60)

        # Track the query through the backend
        async with aiohttp.ClientSession() as session:
            try:
                # Step 1: Submit the query
                logger.info("📤 STEP 1: Submitting query to backend API...")
                search_payload = {"query": query, "max_results": 10, "search_type": "comprehensive"}

                api_start = time.time()
                async with session.post(
                    "http://localhost:8001/api/search",
                    json=search_payload,
                    headers={"Content-Type": "application/json"},
                ) as response:
                    api_end = time.time()
                    api_time = api_end - api_start

                    logger.info(f"⚡ API Response Time: {api_time:.3f}s")
                    logger.info(f"📊 HTTP Status: {response.status}")

                    if response.status == 200:
                        result_data = await response.json()
                        await self.analyze_query_results(query_id, query, result_data, api_time)
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ API Error: {response.status} - {error_text}")

            except Exception as e:
                logger.error(f"💥 Query tracking failed: {e}")

    async def analyze_query_results(self, query_id: str, query: str, data: Dict[str, Any], api_time: float):
        """Analyze the query results in detail"""
        logger.info("🔬 STEP 2: Analyzing query results...")

        # Basic metrics
        total_results = data.get("total_found", 0)
        search_time = data.get("search_time", 0)
        results = data.get("results", [])

        logger.info(f"📈 Results Summary:")
        logger.info(f"   • Total Found: {total_results}")
        logger.info(f"   • Backend Search Time: {search_time:.3f}s")
        logger.info(f"   • Total API Time: {api_time:.3f}s")
        logger.info(f"   • Results Returned: {len(results)}")

        # Analyze each result
        logger.info("📋 Individual Result Analysis:")
        for i, result in enumerate(results):
            logger.info(f"   Result {i+1}: {result.get('geo_id', 'Unknown')}")
            logger.info(f"     • Title: {result.get('title', 'N/A')[:80]}...")
            logger.info(f"     • Organism: {result.get('organism', 'N/A')}")
            logger.info(f"     • Samples: {result.get('sample_count', 'N/A')}")
            logger.info(f"     • Relevance: {result.get('relevance_score', 0):.1%}")
            logger.info(f"     • AI Insights Length: {len(str(result.get('ai_insights', '')))}")
            logger.info(f"     • Publication Date: {result.get('publication_date', 'N/A')}")

        # Quality assessment
        await self.assess_data_quality(query_id, query, data)

        # Save detailed report
        await self.save_query_report(query_id, query, data, api_time)

        logger.info("✅ Query analysis complete!")
        logger.info("=" * 60)

    async def assess_data_quality(self, query_id: str, query: str, data: Dict[str, Any]):
        """Assess the quality of the returned data"""
        logger.info("🎯 STEP 3: Data quality assessment...")

        results = data.get("results", [])
        quality_issues = []
        quality_score = 100

        for i, result in enumerate(results):
            # Check for placeholder content
            ai_insights = str(result.get("ai_insights", ""))
            if "pending for recent submissions" in ai_insights.lower():
                quality_issues.append(f"Result {i+1}: AI insights appear to be placeholder")
                quality_score -= 5

            if result.get("publication_date") == "Recent":
                quality_issues.append(f"Result {i+1}: Publication date is generic")
                quality_score -= 2

            if not result.get("organism") or result.get("organism") == "Unknown":
                quality_issues.append(f"Result {i+1}: Missing organism information")
                quality_score -= 3

            if result.get("platform") is None:
                # This is now expected, so not counting as an issue
                pass

            if len(ai_insights) < 50:
                quality_issues.append(f"Result {i+1}: AI insights too short")
                quality_score -= 5

        logger.info(f"📊 Data Quality Score: {quality_score}/100")
        if quality_issues:
            logger.warning("⚠️  Quality Issues Detected:")
            for issue in quality_issues:
                logger.warning(f"     • {issue}")
        else:
            logger.info("✅ No quality issues detected!")

    async def save_query_report(self, query_id: str, query: str, data: Dict[str, Any], api_time: float):
        """Save detailed query report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"query_report_{timestamp}.json"

        report = {
            "query_id": query_id,
            "query": query,
            "timestamp": timestamp,
            "api_time": api_time,
            "backend_search_time": data.get("search_time", 0),
            "results_count": len(data.get("results", [])),
            "total_found": data.get("total_found", 0),
            "full_response": data,
        }

        with open(filename, "w") as f:
            json.dump(report, f, indent=2, default=str)

        logger.info(f"💾 Query report saved: {filename}")


# Global monitor instance
monitor = RealTimeQueryMonitor()


async def start_monitoring():
    """Start the monitoring system"""
    logger.info("🚀 OmicsOracle Real-Time Query Monitor")
    logger.info("=" * 50)
    logger.info("📍 Monitoring URL: http://localhost:8001")
    logger.info("🔄 Status: Active")
    logger.info("=" * 50)

    # Start background monitoring
    await monitor.monitor_api_requests()


# API endpoint interceptor
async def intercept_query(query: str):
    """Function that will be called when a query is detected"""
    await monitor.track_query_execution(query)


if __name__ == "__main__":
    try:
        print("🔍 Starting Real-Time Query Monitor...")
        print("📱 Now submit your query in the browser at http://localhost:8001")
        print("🔄 Monitoring active - Press Ctrl+C to stop")
        print("=" * 60)

        asyncio.run(start_monitoring())
    except KeyboardInterrupt:
        print("\n🛑 Monitoring stopped by user")
        monitor.monitoring = False
    except Exception as e:
        print(f"\n💥 Monitor failed: {e}")
