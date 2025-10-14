"""
Metrics Logger for Citation Discovery

Provides append-only JSON logging of discovery sessions for:
- Production monitoring (source performance, errors)
- Quality insights (validation trends, false positives)
- Cache effectiveness analysis
- Usage pattern tracking
- Historical debugging context

Log Format: JSONL (JSON Lines - one JSON object per line)
Storage: data/analytics/metrics_log.jsonl

Usage:
    logger = MetricsLogger()

    # Log discovery session
    logger.log_discovery_session({
        "geo_id": "GSE52564",
        "sources": {...},
        "quality_validation": {...},
        "cache": {...}
    })

    # Analyze logs
    stats = logger.get_recent_stats(days=7)
"""

import json
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class MetricsLogger:
    """
    Append-only metrics logger for citation discovery sessions

    Features:
    - Simple JSONL format (one JSON per line)
    - No database overhead (just file append)
    - Easy to analyze with standard tools (jq, Python, etc.)
    - Automatic log rotation (optional)
    - Built-in analysis methods
    """

    def __init__(
        self,
        log_file: str = "data/analytics/metrics_log.jsonl",
        enable_logging: bool = True,
        auto_rotate: bool = False,
        max_log_size_mb: int = 100,
    ):
        """
        Initialize metrics logger

        Args:
            log_file: Path to JSONL log file
            enable_logging: Enable/disable logging
            auto_rotate: Automatically rotate logs when size exceeds max
            max_log_size_mb: Maximum log file size before rotation
        """
        self.log_file = Path(log_file)
        self.enable_logging = enable_logging
        self.auto_rotate = auto_rotate
        self.max_log_size_mb = max_log_size_mb

        if self.enable_logging:
            # Create directory if needed
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            logger.info(f"MetricsLogger initialized: {self.log_file}")

    def log_discovery_session(
        self,
        geo_id: str,
        sources: Dict[str, Dict[str, Any]],
        deduplication: Optional[Dict[str, Any]] = None,
        quality_validation: Optional[Dict[str, Any]] = None,
        cache: Optional[Dict[str, Any]] = None,
        errors: Optional[List[Dict[str, Any]]] = None,
        custom_data: Optional[Dict[str, Any]] = None,
    ):
        """
        Log a citation discovery session

        Args:
            geo_id: GEO dataset ID
            sources: Per-source metrics (success, time, papers found, etc.)
            deduplication: Deduplication stats (total_raw, total_unique, etc.)
            quality_validation: Quality assessment results
            cache: Cache hit/miss info
            errors: List of errors encountered
            custom_data: Any additional custom metrics
        """
        if not self.enable_logging:
            return

        # Build session record
        session_data = {
            "timestamp": datetime.now().isoformat(),
            "geo_id": geo_id,
            "sources": sources,
        }

        # Add optional data
        if deduplication:
            session_data["deduplication"] = deduplication

        if quality_validation:
            session_data["quality_validation"] = quality_validation

        if cache:
            session_data["cache"] = cache

        if errors:
            session_data["errors"] = errors

        if custom_data:
            session_data["custom"] = custom_data

        # Check for log rotation
        if self.auto_rotate:
            self._rotate_if_needed()

        # Append to log (atomic write)
        try:
            with open(self.log_file, "a") as f:
                f.write(json.dumps(session_data) + "\n")

            logger.debug(f"✓ Logged discovery session for {geo_id}")

        except Exception as e:
            logger.warning(f"Failed to log metrics: {e}")

    def _rotate_if_needed(self):
        """Rotate log file if it exceeds max size"""
        if not self.log_file.exists():
            return

        # Check file size
        size_mb = self.log_file.stat().st_size / (1024 * 1024)

        if size_mb > self.max_log_size_mb:
            # Rotate: rename current to .1, .2, etc.
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_name = f"{self.log_file.stem}_{timestamp}.jsonl"
            archive_path = self.log_file.parent / archive_name

            self.log_file.rename(archive_path)
            logger.info(f"Rotated metrics log: {archive_path} ({size_mb:.1f}MB)")

    def get_recent_sessions(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Get sessions from the last N days

        Args:
            days: Number of days to look back

        Returns:
            List of session dictionaries
        """
        if not self.log_file.exists():
            return []

        cutoff_time = datetime.now() - timedelta(days=days)
        sessions = []

        try:
            with open(self.log_file) as f:
                for line in f:
                    try:
                        session = json.loads(line.strip())
                        session_time = datetime.fromisoformat(session["timestamp"])

                        if session_time >= cutoff_time:
                            sessions.append(session)

                    except (json.JSONDecodeError, KeyError, ValueError) as e:
                        logger.warning(f"Failed to parse log line: {e}")
                        continue

        except Exception as e:
            logger.error(f"Failed to read metrics log: {e}")

        return sessions

    def get_source_stats(self, days: int = 7) -> Dict[str, Dict[str, Any]]:
        """
        Get aggregated source performance statistics

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary with per-source stats
        """
        sessions = self.get_recent_sessions(days)

        # Aggregate by source
        source_stats = defaultdict(
            lambda: {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "total_response_time": 0.0,
                "total_papers_found": 0,
                "total_unique_papers": 0,
            }
        )

        for session in sessions:
            for source_name, source_data in session.get("sources", {}).items():
                stats = source_stats[source_name]

                stats["total_requests"] += 1

                if source_data.get("success", False):
                    stats["successful_requests"] += 1
                    stats["total_papers_found"] += source_data.get("papers_found", 0)
                    stats["total_unique_papers"] += source_data.get("unique_papers", 0)
                else:
                    stats["failed_requests"] += 1

                stats["total_response_time"] += source_data.get("response_time", 0)

        # Calculate averages
        result = {}
        for source_name, stats in source_stats.items():
            total = stats["total_requests"]
            result[source_name] = {
                "total_requests": total,
                "success_rate": stats["successful_requests"] / total if total > 0 else 0,
                "avg_response_time": stats["total_response_time"] / total if total > 0 else 0,
                "avg_papers_per_request": (
                    stats["total_papers_found"] / stats["successful_requests"]
                    if stats["successful_requests"] > 0
                    else 0
                ),
                "total_papers_found": stats["total_papers_found"],
                "total_unique_papers": stats["total_unique_papers"],
            }

        return result

    def get_quality_stats(self, days: int = 7) -> Dict[str, Any]:
        """
        Get quality validation statistics

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary with quality metrics
        """
        sessions = self.get_recent_sessions(days)

        # Filter sessions with quality validation
        quality_sessions = [
            s for s in sessions if s.get("quality_validation") and s["quality_validation"].get("enabled")
        ]

        if not quality_sessions:
            return {"sessions": 0, "message": "No quality validation data"}

        # Aggregate quality scores
        total_excellent = 0
        total_good = 0
        total_acceptable = 0
        total_poor = 0
        total_rejected = 0
        quality_scores = []

        for session in quality_sessions:
            qv = session["quality_validation"]

            total_excellent += qv.get("excellent", 0)
            total_good += qv.get("good", 0)
            total_acceptable += qv.get("acceptable", 0)
            total_poor += qv.get("poor", 0)
            total_rejected += qv.get("rejected", 0)

            if "avg_score" in qv:
                quality_scores.append(qv["avg_score"])

        total_papers = total_excellent + total_good + total_acceptable + total_poor + total_rejected

        return {
            "sessions": len(quality_sessions),
            "total_papers_assessed": total_papers,
            "distribution": {
                "excellent": total_excellent,
                "good": total_good,
                "acceptable": total_acceptable,
                "poor": total_poor,
                "rejected": total_rejected,
            },
            "percentages": {
                "excellent": total_excellent / total_papers * 100 if total_papers > 0 else 0,
                "good": total_good / total_papers * 100 if total_papers > 0 else 0,
                "acceptable": total_acceptable / total_papers * 100 if total_papers > 0 else 0,
                "poor": total_poor / total_papers * 100 if total_papers > 0 else 0,
                "rejected": total_rejected / total_papers * 100 if total_papers > 0 else 0,
            },
            "avg_quality_score": sum(quality_scores) / len(quality_scores) if quality_scores else 0,
        }

    def get_cache_stats(self, days: int = 7) -> Dict[str, Any]:
        """
        Get cache effectiveness statistics

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary with cache metrics
        """
        sessions = self.get_recent_sessions(days)

        cache_hits = sum(1 for s in sessions if s.get("cache", {}).get("hit", False))
        cache_misses = len(sessions) - cache_hits

        return {
            "total_queries": len(sessions),
            "cache_hits": cache_hits,
            "cache_misses": cache_misses,
            "hit_rate": cache_hits / len(sessions) * 100 if sessions else 0,
        }

    def get_top_datasets(self, days: int = 7, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get most frequently searched datasets

        Args:
            days: Number of days to analyze
            limit: Maximum number of datasets to return

        Returns:
            List of datasets with search counts
        """
        sessions = self.get_recent_sessions(days)

        # Count by geo_id
        dataset_counts = defaultdict(int)
        for session in sessions:
            dataset_counts[session["geo_id"]] += 1

        # Sort by count
        top_datasets = sorted(dataset_counts.items(), key=lambda x: x[1], reverse=True)[:limit]

        return [{"geo_id": geo_id, "search_count": count} for geo_id, count in top_datasets]

    def get_error_summary(self, days: int = 7) -> Dict[str, Any]:
        """
        Get error statistics

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary with error metrics
        """
        sessions = self.get_recent_sessions(days)

        # Aggregate errors
        error_counts = defaultdict(int)
        total_errors = 0

        for session in sessions:
            errors = session.get("errors", [])
            total_errors += len(errors)

            for error in errors:
                error_type = error.get("type", "unknown")
                error_counts[error_type] += 1

        return {
            "total_sessions": len(sessions),
            "sessions_with_errors": sum(1 for s in sessions if s.get("errors")),
            "total_errors": total_errors,
            "errors_by_type": dict(error_counts),
        }

    def print_summary(self, days: int = 7):
        """
        Print a formatted summary of recent metrics

        Args:
            days: Number of days to analyze
        """
        sessions = self.get_recent_sessions(days)

        if not sessions:
            print(f"No metrics data found for the last {days} days")
            return

        print("\n" + "=" * 80)
        print(f"📊 METRICS SUMMARY (Last {days} days)")
        print("=" * 80)

        print(f"\nTotal Sessions: {len(sessions)}")

        # Source performance
        print("\n--- SOURCE PERFORMANCE ---")
        source_stats = self.get_source_stats(days)
        for source_name, stats in sorted(source_stats.items()):
            print(f"\n{source_name}:")
            print(f"  Requests: {stats['total_requests']}")
            print(f"  Success Rate: {stats['success_rate']:.1%}")
            print(f"  Avg Response Time: {stats['avg_response_time']:.2f}s")
            print(
                f"  Papers Found: {stats['total_papers_found']} total, {stats['total_unique_papers']} unique"
            )
            print(f"  Avg Papers/Request: {stats['avg_papers_per_request']:.1f}")

        # Quality validation
        print("\n--- QUALITY VALIDATION ---")
        quality_stats = self.get_quality_stats(days)
        if "message" in quality_stats:
            print(f"  {quality_stats['message']}")
        else:
            print(f"  Sessions with validation: {quality_stats['sessions']}")
            print(f"  Total papers assessed: {quality_stats['total_papers_assessed']}")
            print(f"  Distribution:")
            for level, pct in quality_stats["percentages"].items():
                count = quality_stats["distribution"][level]
                print(f"    {level.capitalize()}: {count} ({pct:.1f}%)")
            print(f"  Average quality score: {quality_stats['avg_quality_score']:.3f}")

        # Cache effectiveness
        print("\n--- CACHE EFFECTIVENESS ---")
        cache_stats = self.get_cache_stats(days)
        print(f"  Total queries: {cache_stats['total_queries']}")
        print(f"  Cache hits: {cache_stats['cache_hits']}")
        print(f"  Cache misses: {cache_stats['cache_misses']}")
        print(f"  Hit rate: {cache_stats['hit_rate']:.1f}%")

        # Top datasets
        print("\n--- TOP DATASETS ---")
        top_datasets = self.get_top_datasets(days, limit=10)
        for i, dataset in enumerate(top_datasets, 1):
            print(f"  {i}. {dataset['geo_id']}: {dataset['search_count']} searches")

        # Errors
        print("\n--- ERROR SUMMARY ---")
        error_stats = self.get_error_summary(days)
        print(f"  Sessions with errors: {error_stats['sessions_with_errors']}")
        print(f"  Total errors: {error_stats['total_errors']}")
        if error_stats["errors_by_type"]:
            print("  Errors by type:")
            for error_type, count in sorted(
                error_stats["errors_by_type"].items(), key=lambda x: x[1], reverse=True
            ):
                print(f"    {error_type}: {count}")
        else:
            print("  No errors recorded ✓")

        print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    # Example usage
    logger = MetricsLogger()

    # Simulate logging a session
    logger.log_discovery_session(
        geo_id="GSE52564",
        sources={
            "OpenAlex": {
                "success": True,
                "response_time": 1.2,
                "papers_found": 50,
                "unique_papers": 30,
            },
            "Semantic Scholar": {
                "success": True,
                "response_time": 0.8,
                "papers_found": 45,
                "unique_papers": 20,
            },
        },
        deduplication={"total_raw": 250, "total_unique": 188, "duplicate_rate": 0.248},
        quality_validation={
            "enabled": True,
            "excellent": 32,
            "good": 32,
            "acceptable": 122,
            "poor": 0,
            "rejected": 2,
            "avg_score": 0.622,
        },
        cache={"hit": False, "strategy": "fresh"},
        errors=[],
    )

    # Print summary
    logger.print_summary(days=7)
