#!/usr/bin/env python3
"""
GEOCache Performance Benchmark Script

Measures performance of the new 2-tier GEOCache (Redis + UnifiedDB) architecture.

Performance Targets:
- Cache hit (Redis):  < 1ms
- Cache miss (UnifiedDB): < 50ms  
- Write-through: < 10ms
- Hit rate: > 80%

Usage:
    python scripts/benchmark_geocache.py
    python scripts/benchmark_geocache.py --iterations 1000
    python scripts/benchmark_geocache.py --compare-old  # Requires old GEORegistry DB

Author: OmicsOracle Development Team
Date: October 15, 2025
"""

import argparse
import asyncio
import json
import logging
import statistics
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

from omics_oracle_v2.lib.pipelines.storage.registry import GEORegistry, create_geo_cache
from omics_oracle_v2.lib.pipelines.storage.unified_db import UnifiedDatabase

logging.basicConfig(
    level=logging.WARNING,  # Suppress INFO logs during benchmarks
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """Results from a single benchmark operation."""
    operation: str
    min_ms: float
    max_ms: float
    mean_ms: float
    median_ms: float
    p95_ms: float
    p99_ms: float
    std_dev_ms: float
    total_ops: int
    success_rate: float
    
    def meets_target(self, target_ms: float) -> bool:
        """Check if mean latency meets target."""
        return self.mean_ms <= target_ms
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class CachePerformanceReport:
    """Complete performance report for GEOCache."""
    timestamp: str
    cache_hit_result: BenchmarkResult
    cache_miss_result: BenchmarkResult
    write_through_result: Optional[BenchmarkResult]
    hit_rate: float
    redis_available: bool
    targets_met: Dict[str, bool]
    recommendations: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp,
            "cache_hit": self.cache_hit_result.to_dict(),
            "cache_miss": self.cache_miss_result.to_dict(),
            "write_through": self.write_through_result.to_dict() if self.write_through_result else None,
            "hit_rate_percent": round(self.hit_rate * 100, 2),
            "redis_available": self.redis_available,
            "targets_met": self.targets_met,
            "recommendations": self.recommendations
        }


class GeoCacheBenchmark:
    """Benchmark suite for GEOCache performance testing."""
    
    def __init__(self, iterations: int = 100):
        """
        Initialize benchmark suite.
        
        Args:
            iterations: Number of iterations per benchmark
        """
        self.iterations = iterations
        self.registry = None
        self.unified_db = None
        self.sample_geo_ids: List[str] = []
        
    async def setup(self):
        """Set up test environment."""
        logger.warning("Setting up benchmark environment...")
        
        # Initialize registry
        self.registry = GEORegistry()
        self.unified_db = UnifiedDatabase("data/database/omics_oracle.db")
        
        # Get sample GEO IDs from database
        self.sample_geo_ids = self._get_sample_geo_ids()
        
        if not self.sample_geo_ids:
            logger.error("No GEO datasets found in UnifiedDB!")
            logger.error("Please run data migration first: python scripts/migrate_georegistry_to_unified.py")
            raise ValueError("No test data available")
        
        logger.warning(f"Found {len(self.sample_geo_ids)} GEO datasets for testing")
        
        # Warm up cache with first few entries
        logger.warning("Warming up cache...")
        for geo_id in self.sample_geo_ids[:5]:
            await self.registry.get_complete_geo_data(geo_id)
        
        logger.warning("✓ Setup complete\n")
    
    def _get_sample_geo_ids(self, limit: int = 50) -> List[str]:
        """Get sample GEO IDs from UnifiedDB for testing."""
        try:
            cursor = self.unified_db.conn.cursor()
            cursor.execute("""
                SELECT DISTINCT geo_id 
                FROM geo_datasets 
                WHERE geo_id LIKE 'GSE%'
                LIMIT ?
            """, (limit,))
            return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to fetch sample GEO IDs: {e}")
            return []
    
    async def benchmark_cache_hit(self) -> BenchmarkResult:
        """
        Benchmark cache hit performance (Redis hot-tier).
        
        Target: < 1ms mean latency
        """
        logger.warning(f"Benchmarking cache hits ({self.iterations} iterations)...")
        
        timings = []
        successes = 0
        
        # Pre-populate cache
        geo_id = self.sample_geo_ids[0]
        await self.registry.get_complete_geo_data(geo_id)
        
        # Benchmark repeated hits
        for i in range(self.iterations):
            start = time.perf_counter()
            
            try:
                result = await self.registry.get_complete_geo_data(geo_id)
                if result is not None:
                    successes += 1
            except Exception as e:
                logger.error(f"Cache hit failed: {e}")
            
            elapsed_ms = (time.perf_counter() - start) * 1000
            timings.append(elapsed_ms)
        
        return self._create_result("cache_hit", timings, successes)
    
    async def benchmark_cache_miss(self) -> BenchmarkResult:
        """
        Benchmark cache miss performance (UnifiedDB warm-tier).
        
        Target: < 50ms mean latency
        """
        logger.warning(f"Benchmarking cache misses ({self.iterations} iterations)...")
        
        timings = []
        successes = 0
        
        # Use different GEO IDs to ensure cache misses
        geo_ids_to_test = self.sample_geo_ids[:self.iterations]
        
        for geo_id in geo_ids_to_test:
            # Invalidate cache to force miss
            await self.registry.invalidate_cache(geo_id)
            
            start = time.perf_counter()
            
            try:
                result = await self.registry.get_complete_geo_data(geo_id)
                if result is not None:
                    successes += 1
            except Exception as e:
                logger.error(f"Cache miss failed for {geo_id}: {e}")
            
            elapsed_ms = (time.perf_counter() - start) * 1000
            timings.append(elapsed_ms)
        
        return self._create_result("cache_miss", timings, successes)
    
    async def benchmark_concurrent_access(self, concurrent_requests: int = 10) -> BenchmarkResult:
        """
        Benchmark concurrent cache access.
        
        Simulates multiple API requests hitting the cache simultaneously.
        """
        logger.warning(f"Benchmarking concurrent access ({concurrent_requests} parallel requests)...")
        
        timings = []
        successes = 0
        
        geo_id = self.sample_geo_ids[0]
        
        # Ensure it's cached
        await self.registry.get_complete_geo_data(geo_id)
        
        # Run concurrent requests
        for batch in range(self.iterations // concurrent_requests):
            start = time.perf_counter()
            
            # Create concurrent tasks
            tasks = [
                self.registry.get_complete_geo_data(geo_id)
                for _ in range(concurrent_requests)
            ]
            
            try:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                successes += sum(1 for r in results if r is not None and not isinstance(r, Exception))
            except Exception as e:
                logger.error(f"Concurrent access failed: {e}")
            
            elapsed_ms = (time.perf_counter() - start) * 1000
            timings.append(elapsed_ms)
        
        return self._create_result("concurrent_access", timings, successes)
    
    async def measure_hit_rate(self, num_requests: int = 200) -> float:
        """
        Measure cache hit rate over realistic usage pattern.
        
        Simulates: 80% requests to popular datasets, 20% to long-tail.
        
        Target: > 80% hit rate
        """
        logger.warning(f"Measuring cache hit rate ({num_requests} requests)...")
        
        hits = 0
        
        # 80/20 distribution: 80% popular, 20% long-tail
        popular_ids = self.sample_geo_ids[:5]  # Top 5 popular datasets
        longtail_ids = self.sample_geo_ids[5:25]  # Less popular datasets
        
        for i in range(num_requests):
            # 80% chance of popular dataset
            if i % 5 < 4:
                geo_id = popular_ids[i % len(popular_ids)]
            else:
                geo_id = longtail_ids[i % len(longtail_ids)]
            
            # Check cache stats before request
            stats_before = await self.registry.get_stats()
            cache_hits_before = stats_before.get("cache_hits", 0)
            
            # Make request
            await self.registry.get_complete_geo_data(geo_id)
            
            # Check if it was a hit
            stats_after = await self.registry.get_stats()
            cache_hits_after = stats_after.get("cache_hits", 0)
            
            if cache_hits_after > cache_hits_before:
                hits += 1
        
        hit_rate = hits / num_requests
        logger.warning(f"✓ Hit rate: {hit_rate*100:.1f}% ({hits}/{num_requests})\n")
        
        return hit_rate
    
    def _create_result(self, operation: str, timings: List[float], successes: int) -> BenchmarkResult:
        """Create benchmark result from timing data."""
        timings_sorted = sorted(timings)
        
        return BenchmarkResult(
            operation=operation,
            min_ms=round(min(timings), 3),
            max_ms=round(max(timings), 3),
            mean_ms=round(statistics.mean(timings), 3),
            median_ms=round(statistics.median(timings), 3),
            p95_ms=round(timings_sorted[int(len(timings) * 0.95)], 3),
            p99_ms=round(timings_sorted[int(len(timings) * 0.99)], 3),
            std_dev_ms=round(statistics.stdev(timings), 3) if len(timings) > 1 else 0,
            total_ops=len(timings),
            success_rate=round(successes / len(timings) * 100, 2)
        )
    
    async def run_all_benchmarks(self) -> CachePerformanceReport:
        """Run complete benchmark suite and generate report."""
        await self.setup()
        
        # Run benchmarks
        cache_hit_result = await self.benchmark_cache_hit()
        cache_miss_result = await self.benchmark_cache_miss()
        concurrent_result = await self.benchmark_concurrent_access()
        hit_rate = await self.measure_hit_rate()
        
        # Check if Redis is available
        stats = await self.registry.get_stats()
        redis_available = stats.get("redis_available", False)
        
        # Evaluate targets
        targets_met = {
            "cache_hit_under_1ms": cache_hit_result.meets_target(1.0),
            "cache_miss_under_50ms": cache_miss_result.meets_target(50.0),
            "hit_rate_over_80pct": hit_rate >= 0.80,
            "concurrent_under_10ms": concurrent_result.meets_target(10.0)
        }
        
        # Generate recommendations
        recommendations = []
        
        if not targets_met["cache_hit_under_1ms"]:
            recommendations.append(
                f"⚠️ Cache hit latency ({cache_hit_result.mean_ms}ms) exceeds 1ms target. "
                "Consider: (1) Check Redis performance, (2) Reduce serialization overhead."
            )
        
        if not targets_met["cache_miss_under_50ms"]:
            recommendations.append(
                f"⚠️ Cache miss latency ({cache_miss_result.mean_ms}ms) exceeds 50ms target. "
                "Consider: (1) Optimize UnifiedDB query, (2) Add database indexes."
            )
        
        if not targets_met["hit_rate_over_80pct"]:
            recommendations.append(
                f"⚠️ Hit rate ({hit_rate*100:.1f}%) below 80% target. "
                "Consider: (1) Increase Redis TTL, (2) Pre-warm cache for popular datasets."
            )
        
        if all(targets_met.values()):
            recommendations.append("✅ All performance targets met! Cache is operating optimally.")
        
        # Create report
        report = CachePerformanceReport(
            timestamp=datetime.now().isoformat(),
            cache_hit_result=cache_hit_result,
            cache_miss_result=cache_miss_result,
            write_through_result=concurrent_result,
            hit_rate=hit_rate,
            redis_available=redis_available,
            targets_met=targets_met,
            recommendations=recommendations
        )
        
        return report


def print_report(report: CachePerformanceReport):
    """Print formatted performance report."""
    print("\n" + "=" * 80)
    print("GEOCache Performance Benchmark Report")
    print("=" * 80)
    print(f"Timestamp: {report.timestamp}")
    print(f"Redis Available: {'✅ Yes' if report.redis_available else '❌ No (using fallback)'}")
    print()
    
    # Cache Hit Performance
    print("📊 Cache Hit Performance (Redis Hot-Tier)")
    print("-" * 80)
    hit = report.cache_hit_result
    target_symbol = "✅" if hit.meets_target(1.0) else "❌"
    print(f"  {target_symbol} Mean Latency:   {hit.mean_ms:>8.3f} ms  (target: < 1ms)")
    print(f"     Median:          {hit.median_ms:>8.3f} ms")
    print(f"     P95:             {hit.p95_ms:>8.3f} ms")
    print(f"     P99:             {hit.p99_ms:>8.3f} ms")
    print(f"     Min/Max:         {hit.min_ms:>8.3f} / {hit.max_ms:.3f} ms")
    print(f"     Std Dev:         {hit.std_dev_ms:>8.3f} ms")
    print(f"     Total Ops:       {hit.total_ops:>8,}")
    print(f"     Success Rate:    {hit.success_rate:>8.2f}%")
    print()
    
    # Cache Miss Performance
    print("📊 Cache Miss Performance (UnifiedDB Warm-Tier)")
    print("-" * 80)
    miss = report.cache_miss_result
    target_symbol = "✅" if miss.meets_target(50.0) else "❌"
    print(f"  {target_symbol} Mean Latency:   {miss.mean_ms:>8.3f} ms  (target: < 50ms)")
    print(f"     Median:          {miss.median_ms:>8.3f} ms")
    print(f"     P95:             {miss.p95_ms:>8.3f} ms")
    print(f"     P99:             {miss.p99_ms:>8.3f} ms")
    print(f"     Min/Max:         {miss.min_ms:>8.3f} / {miss.max_ms:.3f} ms")
    print(f"     Std Dev:         {miss.std_dev_ms:>8.3f} ms")
    print(f"     Total Ops:       {miss.total_ops:>8,}")
    print(f"     Success Rate:    {miss.success_rate:>8.2f}%")
    print()
    
    # Concurrent Access
    if report.write_through_result:
        print("📊 Concurrent Access Performance")
        print("-" * 80)
        conc = report.write_through_result
        target_symbol = "✅" if conc.meets_target(10.0) else "❌"
        print(f"  {target_symbol} Mean Latency:   {conc.mean_ms:>8.3f} ms  (target: < 10ms)")
        print(f"     Median:          {conc.median_ms:>8.3f} ms")
        print(f"     P95:             {conc.p95_ms:>8.3f} ms")
        print(f"     Total Ops:       {conc.total_ops:>8,}")
        print()
    
    # Hit Rate
    print("📊 Cache Hit Rate")
    print("-" * 80)
    hit_rate_pct = report.hit_rate * 100
    target_symbol = "✅" if report.hit_rate >= 0.80 else "❌"
    print(f"  {target_symbol} Hit Rate:        {hit_rate_pct:>8.2f}%  (target: > 80%)")
    print()
    
    # Targets Summary
    print("🎯 Performance Targets")
    print("-" * 80)
    for target, met in report.targets_met.items():
        symbol = "✅" if met else "❌"
        print(f"  {symbol} {target.replace('_', ' ').title()}")
    print()
    
    # Recommendations
    print("💡 Recommendations")
    print("-" * 80)
    for rec in report.recommendations:
        print(f"  {rec}")
    print()
    
    print("=" * 80)


def save_report(report: CachePerformanceReport, output_path: Path):
    """Save report to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(report.to_dict(), f, indent=2)
    
    print(f"📄 Report saved to: {output_path}")


async def main():
    """Run benchmark suite."""
    parser = argparse.ArgumentParser(description="Benchmark GEOCache performance")
    parser.add_argument(
        "--iterations", 
        type=int, 
        default=100,
        help="Number of iterations per benchmark (default: 100)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/reports/geocache_benchmark.json",
        help="Output path for JSON report"
    )
    
    args = parser.parse_args()
    
    print("\n🚀 Starting GEOCache Performance Benchmark Suite...")
    print(f"   Iterations per test: {args.iterations}")
    print()
    
    # Run benchmarks
    benchmark = GeoCacheBenchmark(iterations=args.iterations)
    
    try:
        report = await benchmark.run_all_benchmarks()
        
        # Print results
        print_report(report)
        
        # Save to file
        output_path = Path(args.output)
        save_report(report, output_path)
        
        # Exit code based on targets
        if all(report.targets_met.values()):
            print("✅ All performance targets met!")
            return 0
        else:
            print("⚠️  Some performance targets not met. See recommendations above.")
            return 1
        
    except ValueError as e:
        logger.error(f"Benchmark failed: {e}")
        print("\n❌ Benchmark failed. Please ensure data migration has been completed.")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
