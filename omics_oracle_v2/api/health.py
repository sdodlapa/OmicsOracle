"""
Health check endpoints for production monitoring.
Week 3 Day 4: Production readiness.
"""

import time
from typing import Any, Dict

start_time = time.time()


def get_health() -> Dict[str, Any]:
    """Basic health check."""
    return {
        "status": "healthy",
        "uptime_seconds": time.time() - start_time,
    }


def get_metrics() -> Dict[str, Any]:
    """System metrics for monitoring."""
    return {
        "status": "healthy",
        "uptime_seconds": time.time() - start_time,
        "version": "0.3.0",
        "features": {
            "geo_search": True,
            "publication_search": True,
            "cache": True,
            "parallel_fetch": True,
        },
    }
