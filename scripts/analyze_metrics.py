#!/usr/bin/env python3
"""
Metrics Analysis Script

Analyzes citation discovery metrics from JSONL logs to provide insights on:
- Source performance (success rates, response times)
- Quality validation trends
- Cache effectiveness
- Usage patterns
- Error tracking

Usage:
    python scripts/analyze_metrics.py [--days 7] [--export report.json]
"""

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List


def load_metrics(log_file: str, days: int = 7) -> List[Dict[str, Any]]:
    """Load metrics from JSONL log file"""
    log_path = Path(log_file)

    if not log_path.exists():
        print(f"❌ Metrics log not found: {log_file}")
        return []

    cutoff_time = datetime.now() - timedelta(days=days)
    sessions = []

    try:
        with open(log_path) as f:
            for line_num, line in enumerate(f, 1):
                try:
                    session = json.loads(line.strip())
                    session_time = datetime.fromisoformat(session["timestamp"])

                    if session_time >= cutoff_time:
                        sessions.append(session)

                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    print(f"⚠️  Skipping invalid line {line_num}: {e}")
                    continue

    except Exception as e:
        print(f"❌ Failed to read metrics log: {e}")
        return []

    return sessions


def analyze_source_performance(sessions: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Analyze source performance metrics"""
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

    # Calculate averages and scores
    result = {}
    for source_name, stats in source_stats.items():
        total = stats["total_requests"]
        success_count = stats["successful_requests"]

        result[source_name] = {
            "total_requests": total,
            "success_rate": success_count / total if total > 0 else 0,
            "avg_response_time": stats["total_response_time"] / total if total > 0 else 0,
            "avg_papers_per_request": (
                stats["total_papers_found"] / success_count if success_count > 0 else 0
            ),
            "total_papers_found": stats["total_papers_found"],
            "total_unique_papers": stats["total_unique_papers"],
            "efficiency_score": (
                (stats["total_papers_found"] / success_count) / (stats["total_response_time"] / total)
                if success_count > 0 and stats["total_response_time"] > 0
                else 0
            ),
        }

    return result


def analyze_quality_validation(sessions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze quality validation metrics"""
    quality_sessions = [
        s for s in sessions if s.get("quality_validation") and s["quality_validation"].get("enabled")
    ]

    if not quality_sessions:
        return {"sessions": 0, "message": "No quality validation data"}

    total_excellent = 0
    total_good = 0
    total_acceptable = 0
    total_poor = 0
    total_rejected = 0
    quality_scores = []
    filter_counts = defaultdict(int)

    for session in quality_sessions:
        qv = session["quality_validation"]

        total_excellent += qv.get("excellent", 0)
        total_good += qv.get("good", 0)
        total_acceptable += qv.get("acceptable", 0)
        total_poor += qv.get("poor", 0)
        total_rejected += qv.get("rejected", 0)

        if "avg_score" in qv:
            quality_scores.append(qv["avg_score"])

        if "filter_applied" in qv:
            filter_counts[qv["filter_applied"]] += 1

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
        "filters_applied": dict(filter_counts),
    }


def analyze_cache_effectiveness(sessions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze cache performance"""
    cache_hits = sum(1 for s in sessions if s.get("cache", {}).get("hit", False))
    cache_misses = len(sessions) - cache_hits

    return {
        "total_queries": len(sessions),
        "cache_hits": cache_hits,
        "cache_misses": cache_misses,
        "hit_rate": cache_hits / len(sessions) * 100 if sessions else 0,
    }


def analyze_usage_patterns(sessions: List[Dict[str, Any]], top_n: int = 10) -> Dict[str, Any]:
    """Analyze usage patterns"""
    dataset_counts = defaultdict(int)
    hourly_distribution = defaultdict(int)

    for session in sessions:
        dataset_counts[session["geo_id"]] += 1

        timestamp = datetime.fromisoformat(session["timestamp"])
        hourly_distribution[timestamp.hour] += 1

    top_datasets = sorted(dataset_counts.items(), key=lambda x: x[1], reverse=True)[:top_n]

    return {
        "unique_datasets": len(dataset_counts),
        "total_searches": len(sessions),
        "top_datasets": [{"geo_id": geo_id, "count": count} for geo_id, count in top_datasets],
        "hourly_distribution": dict(sorted(hourly_distribution.items())),
    }


def analyze_errors(sessions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze error patterns"""
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


def print_report(
    sessions: List[Dict[str, Any]],
    days: int,
    source_stats: Dict,
    quality_stats: Dict,
    cache_stats: Dict,
    usage_stats: Dict,
    error_stats: Dict,
):
    """Print formatted analysis report"""
    print("\n" + "=" * 80)
    print(f"📊 CITATION DISCOVERY METRICS REPORT (Last {days} days)")
    print("=" * 80)

    print(f"\n📈 OVERVIEW")
    print(f"  Total Sessions: {len(sessions)}")
    print(f"  Unique Datasets: {usage_stats['unique_datasets']}")
    print(f"  Date Range: {datetime.now() - timedelta(days=days)} to {datetime.now()}")

    # Source Performance
    print(f"\n🔍 SOURCE PERFORMANCE")
    print(f"{'Source':<20} {'Requests':<10} {'Success':<10} {'Avg Time':<12} {'Papers/Req':<12} {'Efficiency':<12}")
    print("-" * 80)

    for source_name, stats in sorted(source_stats.items()):
        print(
            f"{source_name:<20} "
            f"{stats['total_requests']:<10} "
            f"{stats['success_rate']*100:>6.1f}%   "
            f"{stats['avg_response_time']:>8.2f}s    "
            f"{stats['avg_papers_per_request']:>8.1f}     "
            f"{stats['efficiency_score']:>8.2f}"
        )

    # Quality Validation
    print(f"\n✅ QUALITY VALIDATION")
    if quality_stats.get("message"):
        print(f"  {quality_stats['message']}")
    else:
        print(f"  Sessions Validated: {quality_stats['sessions']}")
        print(f"  Papers Assessed: {quality_stats['total_papers_assessed']}")
        print(f"\n  Distribution:")
        for level in ["excellent", "good", "acceptable", "poor", "rejected"]:
            count = quality_stats["distribution"][level]
            pct = quality_stats["percentages"][level]
            print(f"    {level.capitalize():<12} {count:>6} ({pct:>5.1f}%)")
        print(f"\n  Average Quality Score: {quality_stats['avg_quality_score']:.3f}")

        if quality_stats.get("filters_applied"):
            print(f"\n  Filters Applied:")
            for filter_level, count in quality_stats["filters_applied"].items():
                print(f"    {filter_level}: {count} sessions")

    # Cache Effectiveness
    print(f"\n💾 CACHE EFFECTIVENESS")
    print(f"  Total Queries: {cache_stats['total_queries']}")
    print(f"  Cache Hits: {cache_stats['cache_hits']}")
    print(f"  Cache Misses: {cache_stats['cache_misses']}")
    print(f"  Hit Rate: {cache_stats['hit_rate']:.1f}%")

    # Usage Patterns
    print(f"\n📊 USAGE PATTERNS")
    print(f"  Top {len(usage_stats['top_datasets'])} Datasets:")
    for i, dataset in enumerate(usage_stats["top_datasets"], 1):
        print(f"    {i}. {dataset['geo_id']}: {dataset['count']} searches")

    print(f"\n  Hourly Distribution:")
    hours = usage_stats["hourly_distribution"]
    if hours:
        max_count = max(hours.values())
        for hour in range(24):
            count = hours.get(hour, 0)
            bar = "█" * int(count / max_count * 30) if max_count > 0 else ""
            print(f"    {hour:02d}:00 {bar} ({count})")

    # Errors
    print(f"\n⚠️  ERROR SUMMARY")
    print(f"  Sessions with Errors: {error_stats['sessions_with_errors']}")
    print(f"  Total Errors: {error_stats['total_errors']}")

    if error_stats["errors_by_type"]:
        print(f"  Errors by Type:")
        for error_type, count in sorted(
            error_stats["errors_by_type"].items(), key=lambda x: x[1], reverse=True
        ):
            print(f"    {error_type}: {count}")
    else:
        print(f"  ✅ No errors recorded")

    print("\n" + "=" * 80 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Analyze citation discovery metrics")
    parser.add_argument(
        "--log-file",
        default="data/analytics/metrics_log.jsonl",
        help="Path to metrics log file (default: data/analytics/metrics_log.jsonl)",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days to analyze (default: 7)",
    )
    parser.add_argument(
        "--export",
        help="Export analysis to JSON file",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="Number of top datasets to show (default: 10)",
    )

    args = parser.parse_args()

    # Load metrics
    print(f"Loading metrics from {args.log_file}...")
    sessions = load_metrics(args.log_file, args.days)

    if not sessions:
        print(f"\n⚠️  No metrics found for the last {args.days} days")
        sys.exit(1)

    print(f"✓ Loaded {len(sessions)} sessions")

    # Analyze metrics
    source_stats = analyze_source_performance(sessions)
    quality_stats = analyze_quality_validation(sessions)
    cache_stats = analyze_cache_effectiveness(sessions)
    usage_stats = analyze_usage_patterns(sessions, args.top)
    error_stats = analyze_errors(sessions)

    # Print report
    print_report(sessions, args.days, source_stats, quality_stats, cache_stats, usage_stats, error_stats)

    # Export if requested
    if args.export:
        export_data = {
            "generated_at": datetime.now().isoformat(),
            "days_analyzed": args.days,
            "total_sessions": len(sessions),
            "source_performance": source_stats,
            "quality_validation": quality_stats,
            "cache_effectiveness": cache_stats,
            "usage_patterns": usage_stats,
            "errors": error_stats,
        }

        export_path = Path(args.export)
        export_path.parent.mkdir(parents=True, exist_ok=True)

        with open(export_path, "w") as f:
            json.dump(export_data, f, indent=2)

        print(f"✓ Exported analysis to {export_path}")


if __name__ == "__main__":
    main()
