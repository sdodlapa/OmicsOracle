#!/usr/bin/env python3
"""
Unified Cache Management Utility for OmicsOracle

This script provides a single command-line interface to manage all cache tiers:
- Tier 1 (Hot): Redis cache for GEO metadata and fulltext
- Tier 2 (Warm): SOFT files and compressed parsed cache on disk
- Tier 3 (Cold): External downloads (informational only)

Features:
- Comprehensive cache statistics across all tiers
- Safe cache clearing with dry-run mode by default
- Pattern-based filtering for selective cache management
- Real-time cache monitoring
- Health checks and recommendations
- Integration with existing cache systems

Usage Examples:
    # Show comprehensive cache statistics
    python scripts/cache_manager.py --stats

    # Clear all Redis cache (dry-run preview)
    python scripts/cache_manager.py --clear-redis --dry-run

    # Clear all Redis cache (execute)
    python scripts/cache_manager.py --clear-redis --execute

    # Clear old SOFT files (older than 90 days)
    python scripts/cache_manager.py --clear-soft --max-age-days 90 --execute

    # Clear specific Redis pattern
    python scripts/cache_manager.py --clear-redis --pattern "geo:GSE189*" --execute

    # Clear everything (requires confirmation)
    python scripts/cache_manager.py --clear-all --execute

    # Monitor cache in real-time
    python scripts/cache_manager.py --monitor --interval 60

    # Run health checks
    python scripts/cache_manager.py --health-check

Author: OmicsOracle Team
Date: October 15, 2025
Phase: 5 (Cache Consolidation)
"""

import argparse
import asyncio
import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from omics_oracle_v2.lib.infrastructure.cache.redis_cache import RedisCache
from omics_oracle_v2.lib.pipelines.text_enrichment.parsed_cache import ParsedCache


class CacheManager:
    """Unified cache management for all OmicsOracle cache tiers."""

    def __init__(self, verbose: bool = False):
        """
        Initialize cache manager.

        Args:
            verbose: Enable verbose logging
        """
        self.verbose = verbose
        self.cache_dir = Path("data/cache")
        self.fulltext_dir = Path("data/fulltext/parsed")

        # Initialize Redis connection (with graceful fallback)
        self.redis_cache = None
        try:
            self.redis_cache = RedisCache(
                host="localhost",
                port=6379,
                db=0,
                prefix="omics",
                default_ttl=2592000,  # 30 days
                enabled=True,
            )
            if self.verbose:
                print("[INFO] Redis connection established")
        except Exception as e:
            print(f"[WARNING] Failed to connect to Redis: {e}")
            print("[WARNING] Redis-related operations will be skipped")

        # Initialize ParsedCache (with graceful fallback)
        self.parsed_cache = None
        try:
            self.parsed_cache = ParsedCache(use_redis_hot_tier=True)
            if self.verbose:
                print("[INFO] ParsedCache initialized")
        except Exception as e:
            print(f"[WARNING] Failed to initialize ParsedCache: {e}")
            print("[WARNING] ParsedCache statistics will be unavailable")

    async def get_comprehensive_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics across all cache tiers.

        Returns:
            Dictionary with statistics for all cache systems
        """
        stats = {
            "timestamp": datetime.now().isoformat(),
            "redis": await self._get_redis_stats(),
            "soft_files": self._get_soft_stats(),
            "parsed_cache": self._get_parsed_cache_stats(),
            "summary": {},
        }

        # Calculate summary
        total_size_mb = (
            stats["redis"]["estimated_memory_mb"]
            + stats["soft_files"]["total_size_mb"]
            + stats["parsed_cache"]["total_size_mb"]
        )

        stats["summary"] = {
            "total_cache_size_mb": round(total_size_mb, 2),
            "total_entries": (
                stats["redis"]["total_keys"]
                + stats["soft_files"]["file_count"]
                + stats["parsed_cache"]["entry_count"]
            ),
            "cache_tiers_active": sum(
                [
                    1 if stats["redis"]["available"] else 0,
                    1,  # SOFT files always available
                    1 if stats["parsed_cache"]["available"] else 0,
                ]
            ),
        }

        return stats

    async def _get_redis_stats(self) -> Dict[str, Any]:
        """Get Redis cache statistics."""
        if not self.redis_cache:
            return {
                "available": False,
                "total_keys": 0,
                "geo_metadata_keys": 0,
                "fulltext_keys": 0,
                "estimated_memory_mb": 0,
                "error": "Redis not available",
            }

        try:
            # Count keys by pattern
            all_keys = await self._get_redis_keys("omics*")
            geo_keys = [k for k in all_keys if "geo:" in k or "search:" in k]
            fulltext_keys = [k for k in all_keys if "fulltext:" in k or "parsed:" in k]

            # Estimate memory usage (rough estimate: 30KB per key average)
            estimated_memory_mb = len(all_keys) * 30 / 1024

            return {
                "available": True,
                "total_keys": len(all_keys),
                "geo_metadata_keys": len(geo_keys),
                "fulltext_keys": len(fulltext_keys),
                "estimated_memory_mb": round(estimated_memory_mb, 2),
                "sample_keys": all_keys[:5] if all_keys else [],
            }
        except Exception as e:
            return {
                "available": False,
                "total_keys": 0,
                "geo_metadata_keys": 0,
                "fulltext_keys": 0,
                "estimated_memory_mb": 0,
                "error": str(e),
            }

    def _get_soft_stats(self) -> Dict[str, Any]:
        """Get SOFT file cache statistics."""
        try:
            if not self.cache_dir.exists():
                return {
                    "available": True,
                    "file_count": 0,
                    "total_size_mb": 0,
                    "oldest_file": None,
                    "newest_file": None,
                    "files_by_age": {"0-30_days": 0, "30-90_days": 0, "90+_days": 0},
                }

            # Find SOFT files
            soft_files = list(self.cache_dir.glob("GSE*_family.soft.gz"))

            if not soft_files:
                return {
                    "available": True,
                    "file_count": 0,
                    "total_size_mb": 0,
                    "oldest_file": None,
                    "newest_file": None,
                    "files_by_age": {"0-30_days": 0, "30-90_days": 0, "90+_days": 0},
                }

            # Calculate sizes
            total_size = sum(f.stat().st_size for f in soft_files)

            # Find oldest/newest
            oldest = min(soft_files, key=lambda f: f.stat().st_mtime)
            newest = max(soft_files, key=lambda f: f.stat().st_mtime)

            # Categorize by age
            now = datetime.now()
            files_by_age = {"0-30_days": 0, "30-90_days": 0, "90+_days": 0}

            for f in soft_files:
                age_days = (now - datetime.fromtimestamp(f.stat().st_mtime)).days
                if age_days <= 30:
                    files_by_age["0-30_days"] += 1
                elif age_days <= 90:
                    files_by_age["30-90_days"] += 1
                else:
                    files_by_age["90+_days"] += 1

            return {
                "available": True,
                "file_count": len(soft_files),
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "oldest_file": {
                    "name": oldest.name,
                    "age_days": (now - datetime.fromtimestamp(oldest.stat().st_mtime)).days,
                    "size_mb": round(oldest.stat().st_size / (1024 * 1024), 2),
                },
                "newest_file": {
                    "name": newest.name,
                    "age_days": (now - datetime.fromtimestamp(newest.stat().st_mtime)).days,
                    "size_mb": round(newest.stat().st_size / (1024 * 1024), 2),
                },
                "files_by_age": files_by_age,
            }
        except Exception as e:
            return {
                "available": False,
                "error": str(e),
            }

    def _get_parsed_cache_stats(self) -> Dict[str, Any]:
        """Get parsed cache statistics."""
        if not self.parsed_cache:
            return {
                "available": False,
                "entry_count": 0,
                "total_size_mb": 0,
                "error": "ParsedCache not available",
            }

        try:
            # Try to get stats from ParsedCache
            stats = self.parsed_cache.get_stats()
            return {
                "available": True,
                "entry_count": stats.get("total_entries", 0),
                "total_size_mb": round(stats.get("total_size_mb", 0), 2),
                "compressed_entries": stats.get("compressed_entries", 0),
                "uncompressed_entries": stats.get("uncompressed_entries", 0),
            }
        except Exception as e:
            # Fallback: manually count files
            try:
                if not self.fulltext_dir.exists():
                    return {
                        "available": True,
                        "entry_count": 0,
                        "total_size_mb": 0,
                    }

                files = list(self.fulltext_dir.rglob("*.json*"))
                total_size = sum(f.stat().st_size for f in files)

                return {
                    "available": True,
                    "entry_count": len(files),
                    "total_size_mb": round(total_size / (1024 * 1024), 2),
                    "note": "Fallback statistics (ParsedCache unavailable)",
                }
            except Exception as fallback_error:
                return {
                    "available": False,
                    "error": f"Primary error: {e}, Fallback error: {fallback_error}",
                }

    async def _get_redis_keys(self, pattern: str) -> List[str]:
        """
        Get Redis keys matching pattern.

        Args:
            pattern: Redis key pattern (e.g., "omics*")

        Returns:
            List of matching keys
        """
        if not self.redis_cache:
            return []

        try:
            # Use Redis SCAN for safe iteration (doesn't block)
            keys = []
            cursor = 0

            while True:
                # Note: RedisCache might not expose SCAN directly
                # Fallback to getting all keys with the pattern
                try:
                    # Try to use the cache's built-in method
                    result = await self.redis_cache.keys(pattern)
                    return result if result else []
                except AttributeError:
                    # If keys() method doesn't exist, return empty
                    if self.verbose:
                        print("[WARNING] Redis keys() method not available")
                    return []
        except Exception as e:
            if self.verbose:
                print(f"[ERROR] Failed to get Redis keys: {e}")
            return []

    async def clear_redis(
        self,
        pattern: str = "*",
        dry_run: bool = True,
        force: bool = False,
    ) -> Dict[str, Any]:
        """
        Clear Redis cache keys matching pattern.

        Args:
            pattern: Key pattern to match (default: "*" for all)
            dry_run: If True, only preview changes (default: True)
            force: Skip confirmation prompts

        Returns:
            Dictionary with operation results
        """
        if not self.redis_cache:
            return {
                "success": False,
                "error": "Redis not available",
                "keys_deleted": 0,
            }

        try:
            # Build full pattern
            full_pattern = f"omics*{pattern}" if not pattern.startswith("omics") else pattern

            # Get matching keys
            keys = await self._get_redis_keys(full_pattern)

            if not keys:
                return {
                    "success": True,
                    "message": f"No keys found matching pattern: {full_pattern}",
                    "keys_deleted": 0,
                }

            # Dry run - just preview
            if dry_run:
                return {
                    "success": True,
                    "dry_run": True,
                    "message": f"Would delete {len(keys)} Redis keys",
                    "pattern": full_pattern,
                    "keys_to_delete": len(keys),
                    "sample_keys": keys[:10],
                }

            # Confirmation prompt (unless forced)
            if not force:
                print(f"\n⚠️  WARNING: About to delete {len(keys)} Redis keys!")
                print(f"Pattern: {full_pattern}")
                print(f"Sample keys: {keys[:5]}")
                response = input("\nType 'yes' to confirm: ")
                if response.lower() != "yes":
                    return {
                        "success": False,
                        "message": "Operation cancelled by user",
                        "keys_deleted": 0,
                    }

            # Execute deletion
            deleted_count = 0
            for key in keys:
                try:
                    await self.redis_cache.delete(key)
                    deleted_count += 1
                except Exception as e:
                    if self.verbose:
                        print(f"[ERROR] Failed to delete key {key}: {e}")

            return {
                "success": True,
                "message": f"Successfully deleted {deleted_count} Redis keys",
                "keys_deleted": deleted_count,
                "pattern": full_pattern,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "keys_deleted": 0,
            }

    def clear_soft_files(
        self,
        max_age_days: int = 90,
        dry_run: bool = True,
        force: bool = False,
    ) -> Dict[str, Any]:
        """
        Clear SOFT files older than specified age.

        Args:
            max_age_days: Maximum age in days (default: 90)
            dry_run: If True, only preview changes (default: True)
            force: Skip confirmation prompts

        Returns:
            Dictionary with operation results
        """
        try:
            if not self.cache_dir.exists():
                return {
                    "success": True,
                    "message": "No SOFT cache directory found",
                    "files_deleted": 0,
                }

            # Find SOFT files
            soft_files = list(self.cache_dir.glob("GSE*_family.soft.gz"))

            if not soft_files:
                return {
                    "success": True,
                    "message": "No SOFT files found",
                    "files_deleted": 0,
                }

            # Filter by age
            cutoff = datetime.now() - timedelta(days=max_age_days)
            old_files = [f for f in soft_files if datetime.fromtimestamp(f.stat().st_mtime) < cutoff]

            if not old_files:
                return {
                    "success": True,
                    "message": f"No SOFT files older than {max_age_days} days",
                    "files_deleted": 0,
                }

            # Calculate total size
            total_size_mb = sum(f.stat().st_size for f in old_files) / (1024 * 1024)

            # Dry run - just preview
            if dry_run:
                return {
                    "success": True,
                    "dry_run": True,
                    "message": f"Would delete {len(old_files)} SOFT files ({total_size_mb:.2f} MB)",
                    "max_age_days": max_age_days,
                    "files_to_delete": len(old_files),
                    "size_to_free_mb": round(total_size_mb, 2),
                    "sample_files": [f.name for f in old_files[:5]],
                }

            # Confirmation prompt (unless forced)
            if not force:
                print(f"\n⚠️  WARNING: About to delete {len(old_files)} SOFT files ({total_size_mb:.2f} MB)!")
                print(f"Max age: {max_age_days} days")
                print(f"Sample files: {[f.name for f in old_files[:3]]}")
                response = input("\nType 'yes' to confirm: ")
                if response.lower() != "yes":
                    return {
                        "success": False,
                        "message": "Operation cancelled by user",
                        "files_deleted": 0,
                    }

            # Execute deletion
            deleted_count = 0
            for f in old_files:
                try:
                    f.unlink()
                    deleted_count += 1
                except Exception as e:
                    if self.verbose:
                        print(f"[ERROR] Failed to delete {f.name}: {e}")

            return {
                "success": True,
                "message": f"Successfully deleted {deleted_count} SOFT files ({total_size_mb:.2f} MB)",
                "files_deleted": deleted_count,
                "size_freed_mb": round(total_size_mb, 2),
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "files_deleted": 0,
            }

    async def clear_all(self, dry_run: bool = True, force: bool = False) -> Dict[str, Any]:
        """
        Clear all caches.

        Args:
            dry_run: If True, only preview changes (default: True)
            force: Skip confirmation prompts

        Returns:
            Dictionary with operation results
        """
        results = {
            "redis": await self.clear_redis(pattern="*", dry_run=dry_run, force=force),
            "soft_files": self.clear_soft_files(max_age_days=0, dry_run=dry_run, force=force),
        }

        return {
            "success": all(r["success"] for r in results.values()),
            "results": results,
        }

    async def health_check(self) -> Dict[str, Any]:
        """
        Run comprehensive health checks on cache system.

        Returns:
            Dictionary with health check results
        """
        stats = await self.get_comprehensive_stats()

        checks = {
            "timestamp": datetime.now().isoformat(),
            "checks": [],
            "overall_status": "healthy",
        }

        # Check 1: Redis connectivity
        if stats["redis"]["available"]:
            checks["checks"].append(
                {
                    "name": "Redis Connection",
                    "status": "✅ PASS",
                    "message": f"Redis is available with {stats['redis']['total_keys']} keys",
                }
            )
        else:
            checks["checks"].append(
                {
                    "name": "Redis Connection",
                    "status": "⚠️  WARNING",
                    "message": "Redis is not available",
                }
            )
            checks["overall_status"] = "degraded"

        # Check 2: Total cache size
        total_size = stats["summary"]["total_cache_size_mb"]
        if total_size < 1000:  # < 1GB
            checks["checks"].append(
                {
                    "name": "Cache Size",
                    "status": "✅ PASS",
                    "message": f"Total cache size is reasonable: {total_size:.2f} MB",
                }
            )
        elif total_size < 5000:  # < 5GB
            checks["checks"].append(
                {
                    "name": "Cache Size",
                    "status": "⚠️  WARNING",
                    "message": f"Cache size is growing: {total_size:.2f} MB (consider cleanup)",
                }
            )
            checks["overall_status"] = "degraded"
        else:  # > 5GB
            checks["checks"].append(
                {
                    "name": "Cache Size",
                    "status": "❌ FAIL",
                    "message": f"Cache size is too large: {total_size:.2f} MB (cleanup recommended!)",
                }
            )
            checks["overall_status"] = "unhealthy"

        # Check 3: Old SOFT files
        soft_stats = stats["soft_files"]
        if soft_stats["available"] and soft_stats.get("files_by_age"):
            old_files = soft_stats["files_by_age"].get("90+_days", 0)
            if old_files == 0:
                checks["checks"].append(
                    {
                        "name": "SOFT File Age",
                        "status": "✅ PASS",
                        "message": "No SOFT files older than 90 days",
                    }
                )
            elif old_files < 10:
                checks["checks"].append(
                    {
                        "name": "SOFT File Age",
                        "status": "⚠️  WARNING",
                        "message": f"{old_files} SOFT files older than 90 days (cleanup recommended)",
                    }
                )
            else:
                checks["checks"].append(
                    {
                        "name": "SOFT File Age",
                        "status": "❌ FAIL",
                        "message": f"{old_files} SOFT files older than 90 days (cleanup needed!)",
                    }
                )
                checks["overall_status"] = "degraded"

        # Check 4: ParsedCache availability
        if stats["parsed_cache"]["available"]:
            checks["checks"].append(
                {
                    "name": "ParsedCache",
                    "status": "✅ PASS",
                    "message": f"ParsedCache is available with {stats['parsed_cache']['entry_count']} entries",
                }
            )
        else:
            checks["checks"].append(
                {
                    "name": "ParsedCache",
                    "status": "⚠️  WARNING",
                    "message": "ParsedCache is not available",
                }
            )

        return checks

    async def monitor(self, interval: int = 60, iterations: int = 0):
        """
        Monitor cache statistics in real-time.

        Args:
            interval: Seconds between updates (default: 60)
            iterations: Number of iterations (0 = infinite)
        """
        print(f"\n🔍 Cache Monitor (updating every {interval}s, Ctrl+C to stop)\n")
        print("=" * 80)

        iteration = 0
        try:
            while iterations == 0 or iteration < iterations:
                stats = await self.get_comprehensive_stats()

                timestamp = datetime.now().strftime("%H:%M:%S")
                redis_keys = stats["redis"]["total_keys"]
                redis_mb = stats["redis"]["estimated_memory_mb"]
                soft_files = stats["soft_files"]["file_count"]
                soft_mb = stats["soft_files"]["total_size_mb"]
                parsed_entries = stats["parsed_cache"]["entry_count"]
                parsed_mb = stats["parsed_cache"]["total_size_mb"]
                total_mb = stats["summary"]["total_cache_size_mb"]

                print(
                    f"[{timestamp}] Redis: {redis_keys} keys ({redis_mb:.1f} MB) | "
                    f"SOFT: {soft_files} files ({soft_mb:.1f} MB) | "
                    f"Parsed: {parsed_entries} entries ({parsed_mb:.1f} MB) | "
                    f"Total: {total_mb:.1f} MB"
                )

                iteration += 1
                if iterations == 0 or iteration < iterations:
                    await asyncio.sleep(interval)

        except KeyboardInterrupt:
            print("\n\n✅ Monitoring stopped by user")


def print_stats(stats: Dict[str, Any]):
    """Pretty print cache statistics."""
    print("\n" + "=" * 80)
    print("📊 OMICSORACLE CACHE STATISTICS")
    print("=" * 80)

    # Redis Cache
    print("\n🔥 TIER 1: REDIS HOT CACHE")
    print("-" * 80)
    if stats["redis"]["available"]:
        print(f"  Status:           ✅ Available")
        print(f"  Total Keys:       {stats['redis']['total_keys']:,}")
        print(f"  GEO Metadata:     {stats['redis']['geo_metadata_keys']:,} keys")
        print(f"  Fulltext:         {stats['redis']['fulltext_keys']:,} keys")
        print(f"  Estimated Memory: {stats['redis']['estimated_memory_mb']:.2f} MB")
        if stats["redis"].get("sample_keys"):
            print(f"  Sample Keys:      {stats['redis']['sample_keys'][:3]}")
    else:
        print(f"  Status:           ❌ Not Available")
        print(f"  Error:            {stats['redis'].get('error', 'Unknown')}")

    # SOFT Files
    print("\n💾 TIER 2: DISK WARM CACHE (SOFT Files)")
    print("-" * 80)
    if stats["soft_files"]["available"]:
        print(f"  Status:           ✅ Available")
        print(f"  File Count:       {stats['soft_files']['file_count']:,}")
        print(f"  Total Size:       {stats['soft_files']['total_size_mb']:.2f} MB")

        if stats["soft_files"]["file_count"] > 0:
            print(f"  Age Distribution:")
            print(f"    0-30 days:      {stats['soft_files']['files_by_age']['0-30_days']} files")
            print(f"    30-90 days:     {stats['soft_files']['files_by_age']['30-90_days']} files")
            print(f"    90+ days:       {stats['soft_files']['files_by_age']['90+_days']} files")

            print(f"  Oldest File:      {stats['soft_files']['oldest_file']['name']}")
            print(f"    Age:            {stats['soft_files']['oldest_file']['age_days']} days")
            print(f"    Size:           {stats['soft_files']['oldest_file']['size_mb']:.2f} MB")
    else:
        print(f"  Status:           ❌ Not Available")
        print(f"  Error:            {stats['soft_files'].get('error', 'Unknown')}")

    # Parsed Cache
    print("\n📄 TIER 2: DISK WARM CACHE (Parsed Fulltext)")
    print("-" * 80)
    if stats["parsed_cache"]["available"]:
        print(f"  Status:           ✅ Available")
        print(f"  Entry Count:      {stats['parsed_cache']['entry_count']:,}")
        print(f"  Total Size:       {stats['parsed_cache']['total_size_mb']:.2f} MB")
        if stats["parsed_cache"].get("compressed_entries") is not None:
            print(f"  Compressed:       {stats['parsed_cache']['compressed_entries']:,} entries")
            print(f"  Uncompressed:     {stats['parsed_cache']['uncompressed_entries']:,} entries")
    else:
        print(f"  Status:           ❌ Not Available")
        print(f"  Error:            {stats['parsed_cache'].get('error', 'Unknown')}")

    # Summary
    print("\n📈 SUMMARY")
    print("-" * 80)
    print(f"  Total Cache Size: {stats['summary']['total_cache_size_mb']:.2f} MB")
    print(f"  Total Entries:    {stats['summary']['total_entries']:,}")
    print(f"  Active Tiers:     {stats['summary']['cache_tiers_active']}/3")
    print(f"  Timestamp:        {stats['timestamp']}")
    print("\n" + "=" * 80 + "\n")


def print_health_check(health: Dict[str, Any]):
    """Pretty print health check results."""
    print("\n" + "=" * 80)
    print("🏥 CACHE HEALTH CHECK")
    print("=" * 80)

    # Overall status
    status_emoji = {
        "healthy": "✅",
        "degraded": "⚠️ ",
        "unhealthy": "❌",
    }
    print(
        f"\nOverall Status: {status_emoji.get(health['overall_status'], '❓')} {health['overall_status'].upper()}"
    )
    print(f"Timestamp:      {health['timestamp']}")

    # Individual checks
    print("\nChecks:")
    print("-" * 80)
    for check in health["checks"]:
        print(f"  {check['status']} {check['name']}")
        print(f"     {check['message']}")

    print("\n" + "=" * 80 + "\n")


async def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Unified Cache Management for OmicsOracle",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show cache statistics
  python scripts/cache_manager.py --stats

  # Clear Redis cache (preview)
  python scripts/cache_manager.py --clear-redis --dry-run

  # Clear Redis cache (execute)
  python scripts/cache_manager.py --clear-redis --execute

  # Clear old SOFT files
  python scripts/cache_manager.py --clear-soft --max-age-days 90 --execute

  # Clear specific pattern
  python scripts/cache_manager.py --clear-redis --pattern "geo:GSE189*" --execute

  # Monitor in real-time
  python scripts/cache_manager.py --monitor --interval 30

  # Health check
  python scripts/cache_manager.py --health-check
        """,
    )

    # Actions
    parser.add_argument("--stats", action="store_true", help="Show comprehensive cache statistics")
    parser.add_argument("--health-check", action="store_true", help="Run cache health checks")
    parser.add_argument("--monitor", action="store_true", help="Monitor cache in real-time")
    parser.add_argument("--clear-redis", action="store_true", help="Clear Redis cache")
    parser.add_argument("--clear-soft", action="store_true", help="Clear SOFT files")
    parser.add_argument("--clear-all", action="store_true", help="Clear all caches (requires confirmation)")

    # Options
    parser.add_argument("--pattern", default="*", help="Redis key pattern to match (default: *)")
    parser.add_argument(
        "--max-age-days", type=int, default=90, help="Maximum age for SOFT files in days (default: 90)"
    )
    parser.add_argument(
        "--interval", type=int, default=60, help="Monitor update interval in seconds (default: 60)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without executing (default for clear operations)",
    )
    parser.add_argument("--execute", action="store_true", help="Execute changes (opposite of --dry-run)")
    parser.add_argument("--force", action="store_true", help="Skip confirmation prompts")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")

    args = parser.parse_args()

    # Determine dry_run mode (default is True unless --execute is specified)
    dry_run = not args.execute if (args.clear_redis or args.clear_soft or args.clear_all) else False

    # Initialize manager
    manager = CacheManager(verbose=args.verbose)

    # Execute actions
    try:
        if args.stats:
            stats = await manager.get_comprehensive_stats()
            if args.json:
                print(json.dumps(stats, indent=2))
            else:
                print_stats(stats)

        elif args.health_check:
            health = await manager.health_check()
            if args.json:
                print(json.dumps(health, indent=2))
            else:
                print_health_check(health)

        elif args.monitor:
            await manager.monitor(interval=args.interval)

        elif args.clear_redis:
            result = await manager.clear_redis(pattern=args.pattern, dry_run=dry_run, force=args.force)
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                if result["success"]:
                    if result.get("dry_run"):
                        print(f"\n✅ DRY RUN: {result['message']}")
                        print(f"   Pattern: {result['pattern']}")
                        print(f"   Keys to delete: {result['keys_to_delete']}")
                        if result.get("sample_keys"):
                            print(f"   Sample keys: {result['sample_keys'][:5]}")
                        print(f"\n💡 Run with --execute to actually delete\n")
                    else:
                        print(f"\n✅ {result['message']}\n")
                else:
                    print(f"\n❌ Error: {result.get('error', result.get('message'))}\n")

        elif args.clear_soft:
            result = manager.clear_soft_files(
                max_age_days=args.max_age_days, dry_run=dry_run, force=args.force
            )
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                if result["success"]:
                    if result.get("dry_run"):
                        print(f"\n✅ DRY RUN: {result['message']}")
                        print(f"   Max age: {result['max_age_days']} days")
                        print(f"   Files to delete: {result['files_to_delete']}")
                        print(f"   Size to free: {result['size_to_free_mb']:.2f} MB")
                        if result.get("sample_files"):
                            print(f"   Sample files: {result['sample_files'][:3]}")
                        print(f"\n💡 Run with --execute to actually delete\n")
                    else:
                        print(f"\n✅ {result['message']}\n")
                else:
                    print(f"\n❌ Error: {result.get('error', result.get('message'))}\n")

        elif args.clear_all:
            result = await manager.clear_all(dry_run=dry_run, force=args.force)
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                print(f"\n{'✅' if result['success'] else '❌'} Clear All Results:")
                print(f"  Redis: {result['results']['redis']['message']}")
                print(f"  SOFT Files: {result['results']['soft_files']['message']}")
                print()

        else:
            # No action specified - show help
            parser.print_help()
            print("\n💡 Tip: Start with --stats to see current cache state\n")

    except KeyboardInterrupt:
        print("\n\n✅ Operation cancelled by user\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}\n")
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
