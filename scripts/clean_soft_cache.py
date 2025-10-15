#!/usr/bin/env python3
"""
Clean old GEOparse SOFT files from cache.

GEOparse caches SOFT files indefinitely. This script removes files older
than a specified age (default: 90 days) to free up disk space.

Usage:
    # Dry run (show what would be removed)
    python scripts/clean_soft_cache.py --max-age-days 90

    # Actually remove old files
    python scripts/clean_soft_cache.py --max-age-days 90 --execute

    # Custom cache directory
    python scripts/clean_soft_cache.py --cache-dir /custom/path --execute
"""

import argparse
from datetime import datetime, timedelta
from pathlib import Path


def clean_soft_cache(cache_dir: Path, max_age_days: int = 90, dry_run: bool = True):
    """
    Remove SOFT files older than max_age_days.

    Args:
        cache_dir: Directory containing SOFT files
        max_age_days: Maximum age in days before removal
        dry_run: If True, only show what would be removed (don't actually delete)
    """

    # Find all SOFT files (compressed and uncompressed)
    soft_files = list(cache_dir.glob("GSE*_family.soft.gz")) + list(cache_dir.glob("GSE*_family.soft"))

    if not soft_files:
        print(f"✓ No SOFT files found in {cache_dir}")
        return

    cutoff_date = datetime.now() - timedelta(days=max_age_days)
    removed_count = 0
    kept_count = 0
    total_removed_size = 0
    total_kept_size = 0

    print("=" * 80)
    print(f"GEOparse SOFT File Cleanup")
    print("=" * 80)
    print(f"Cache directory: {cache_dir}")
    print(f"Total SOFT files: {len(soft_files)}")
    print(f"Cutoff date: {cutoff_date.strftime('%Y-%m-%d')} ({max_age_days} days ago)")
    print(f"Mode: {'DRY RUN (no files will be deleted)' if dry_run else 'EXECUTE (files will be deleted)'}")
    print("-" * 80)
    print()

    for soft_file in sorted(soft_files):
        file_mtime = datetime.fromtimestamp(soft_file.stat().st_mtime)
        file_size = soft_file.stat().st_size
        file_age_days = (datetime.now() - file_mtime).days

        if file_mtime < cutoff_date:
            # File is too old, mark for removal
            if dry_run:
                print(f"[WOULD REMOVE] {soft_file.name}")
            else:
                print(f"[REMOVING] {soft_file.name}")
                soft_file.unlink()

            print(f"  Age: {file_age_days} days")
            print(f"  Size: {file_size:,} bytes ({file_size / (1024*1024):.2f} MB)")
            print(f"  Last modified: {file_mtime.strftime('%Y-%m-%d %H:%M:%S')}")
            print()

            removed_count += 1
            total_removed_size += file_size
        else:
            # File is recent enough, keep it
            kept_count += 1
            total_kept_size += file_size

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)

    if removed_count > 0:
        print(f"Files to remove: {removed_count}")
        print(f"  Total size: {total_removed_size / (1024*1024):.2f} MB")
        print(f"  Average age: {max_age_days}+ days")
        print()

    if kept_count > 0:
        print(f"Files to keep: {kept_count}")
        print(f"  Total size: {total_kept_size / (1024*1024):.2f} MB")
        print(f"  Age: < {max_age_days} days")
        print()

    if removed_count == 0:
        print("✓ No files to remove (all are recent or none exist)")
    elif dry_run:
        print(f"⚠️  DRY RUN: No files were actually removed")
        print(f"   Run with --execute to actually remove {removed_count} file(s)")
    else:
        print(f"✓ Successfully removed {removed_count} file(s)")
        print(f"  Freed {total_removed_size / (1024*1024):.2f} MB of disk space")

    print("=" * 80)


def main():
    """Parse arguments and run cleanup."""
    parser = argparse.ArgumentParser(
        description="Clean old GEOparse SOFT files from cache",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show what would be removed (dry run)
  python scripts/clean_soft_cache.py --max-age-days 90

  # Actually remove files older than 90 days
  python scripts/clean_soft_cache.py --max-age-days 90 --execute

  # Remove files older than 30 days (aggressive cleanup)
  python scripts/clean_soft_cache.py --max-age-days 30 --execute

  # Custom cache directory
  python scripts/clean_soft_cache.py --cache-dir /custom/path --execute
        """,
    )

    parser.add_argument(
        "--cache-dir",
        type=str,
        default="data/cache",
        help="Cache directory containing SOFT files (default: data/cache)",
    )

    parser.add_argument(
        "--max-age-days", type=int, default=90, help="Remove files older than this many days (default: 90)"
    )

    parser.add_argument("--execute", action="store_true", help="Actually remove files (default is dry run)")

    args = parser.parse_args()

    cache_dir = Path(args.cache_dir)

    if not cache_dir.exists():
        print(f"Error: Cache directory does not exist: {cache_dir}")
        print(f"Create it or specify a different path with --cache-dir")
        return 1

    if not cache_dir.is_dir():
        print(f"Error: Not a directory: {cache_dir}")
        return 1

    try:
        clean_soft_cache(cache_dir=cache_dir, max_age_days=args.max_age_days, dry_run=not args.execute)
        return 0
    except Exception as e:
        print(f"Error during cleanup: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
