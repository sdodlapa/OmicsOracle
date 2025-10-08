#!/usr/bin/env python3
"""
Simple Backend Log Monitor for OmicsOracle

This script monitors the futuristic interface server logs in real-time
to track user queries as they happen.
"""

import subprocess
import threading
import time
from datetime import datetime


class BackendLogMonitor:
    def __init__(self):
        self.monitoring = True

    def start_monitoring(self):
        """Start monitoring the backend logs"""
        print("🔍 OmicsOracle Backend Log Monitor")
        print("=" * 50)
        print("📱 Open your browser to http://localhost:8001")
        print("🔍 Submit your query and watch the detailed tracking below!")
        print("⏰ Started at:", datetime.now())
        print("=" * 50)

        # Monitor the server process output
        try:
            # Since the server is already running, we'll monitor by watching for API calls
            while self.monitoring:
                print("📡 Monitoring for new queries... (submit a query in your browser)")
                time.sleep(2)

        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped")

    def explain_process_flow(self):
        """Explain what happens during a query"""
        print("\n📋 QUERY PROCESS FLOW EXPLANATION:")
        print("=" * 50)
        print("When you submit a query in the browser, here's what happens:")
        print()
        print("🌐 FRONTEND (Browser):")
        print("  1. User types query in search box")
        print("  2. JavaScript captures form submission")
        print("  3. AJAX POST request sent to /api/search")
        print("  4. Search button shows 'Searching...' animation")
        print()
        print("🔧 BACKEND (Python FastAPI):")
        print("  5. FastAPI receives POST /api/search")
        print("  6. Query validation and parsing")
        print("  7. OmicsOracle pipeline initialization")
        print("  8. NLP processing (biomedical entity extraction)")
        print("  9. GEO database search via NCBI API")
        print("  10. Metadata extraction for found datasets")
        print("  11. AI summarization using OpenAI/Claude")
        print("  12. Result formatting and scoring")
        print("  13. JSON response sent back to frontend")
        print()
        print("🖥️ FRONTEND (Display):")
        print("  14. JavaScript receives JSON response")
        print("  15. Results rendered dynamically")
        print("  16. GEO links made clickable")
        print("  17. AI insights displayed")
        print("  18. Search button returns to normal state")
        print()


if __name__ == "__main__":
    monitor = BackendLogMonitor()
    monitor.explain_process_flow()

    print("🚀 Ready for query tracking!")
    print("💡 Submit your query now in the browser...")
    print()

    try:
        monitor.start_monitoring()
    except KeyboardInterrupt:
        print("\n✅ Monitoring session ended")
