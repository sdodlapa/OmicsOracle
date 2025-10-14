#!/usr/bin/env python
"""
Citation Discovery Cache Management CLI

Manage the citation discovery cache: view stats, cleanup expired entries, invalidate cache, etc.

Usage:
    python manage_discovery_cache.py stats
    python manage_discovery_cache.py cleanup
    python manage_discovery_cache.py invalidate GSE12345
    python manage_discovery_cache.py clear --force
"""

import argparse
import sys
from pathlib import Path

from omics_oracle_v2.lib.pipelines.citation_discovery.cache import (
    DiscoveryCache,
    get_cache_info,
)


def print_stats(cache: DiscoveryCache):
    """Print cache statistics"""
    stats = cache.get_stats()
    print("\n📊 Cache Statistics")
    print("=" * 50)
    print(f"Total queries:      {stats.total_queries}")
    print(f"Cache hits:         {stats.hits}")
    print(f"Cache misses:       {stats.misses}")
    print(f"Hit rate:           {stats.hit_rate:.2%}")
    print(f"Memory entries:     {stats.memory_entries}")
    print(f"Disk entries:       {stats.disk_entries}")

    # Get detailed info
    info = get_cache_info(cache.db_path)
    print(f"\nActive entries:     {info.get('active_entries', 0)}")
    print(f"Expired entries:    {info.get('expired_entries', 0)}")
    print(f"Total size:         {info.get('size_mb', 0):.2f} MB")

    top_entries = info.get("top_entries", [])
    if top_entries:
        print("\n🔝 Most Accessed:")
        for entry in top_entries[:5]:
            print(f"  {entry['geo_id']:<15} {entry['hits']:>5} hits")


def cleanup_expired(cache: DiscoveryCache):
    """Remove expired cache entries"""
    print("\n🧹 Cleaning up expired entries...")
    count = cache.cleanup_expired()
    print(f"✓ Removed {count} expired entries")

    stats = cache.get_stats()
    print(f"Remaining entries: {stats.disk_entries}")


def invalidate_entry(cache: DiscoveryCache, geo_id: str):
    """Invalidate cache for specific GEO ID"""
    print(f"\n🗑️  Invalidating cache for {geo_id}...")
    count = cache.invalidate(geo_id)
    print(f"✓ Removed {count} entries")


def clear_all(cache: DiscoveryCache, force: bool = False):
    """Clear all cache entries"""
    if not force:
        response = input("\n⚠️  Are you sure you want to clear ALL cache? (yes/no): ")
        if response.lower() != "yes":
            print("Cancelled")
            return

    print("\n🗑️  Clearing ALL cache entries...")
    cache.clear_all()
    print("✓ Cache cleared")


def main():
    parser = argparse.ArgumentParser(
        description="Manage citation discovery cache",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s stats                    Show cache statistics
  %(prog)s cleanup                  Remove expired entries
  %(prog)s invalidate GSE12345      Invalidate cache for GSE12345
  %(prog)s clear --force            Clear all cache (dangerous!)
        """,
    )

    parser.add_argument("command", choices=["stats", "cleanup", "invalidate", "clear"], help="Command to execute")

    parser.add_argument("geo_id", nargs="?", help="GEO ID (for invalidate command)")

    parser.add_argument("--db-path", help="Path to cache database", default=None)

    parser.add_argument("--force", action="store_true", help="Skip confirmation prompts")

    args = parser.parse_args()

    # Initialize cache
    cache = DiscoveryCache(db_path=args.db_path)

    # Execute command
    if args.command == "stats":
        print_stats(cache)

    elif args.command == "cleanup":
        cleanup_expired(cache)

    elif args.command == "invalidate":
        if not args.geo_id:
            print("Error: GEO ID required for invalidate command")
            print("Usage: manage_discovery_cache.py invalidate GSE12345")
            sys.exit(1)
        invalidate_entry(cache, args.geo_id)

    elif args.command == "clear":
        clear_all(cache, force=args.force)

    print()


if __name__ == "__main__":
    main()
