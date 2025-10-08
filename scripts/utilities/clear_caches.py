#!/usr/bin/env python3
"""
Cache Management Utility for OmicsOracle Testing

This script temporarily disables caching for robust testing.
"""

import os
import sqlite3
from pathlib import Path


def clear_all_caches():
    """Clear all cache databases"""
    cache_dir = Path("data/cache")

    if cache_dir.exists():
        for cache_file in cache_dir.glob("*.db"):
            try:
                # Connect and clear the database
                conn = sqlite3.connect(str(cache_file))
                cursor = conn.cursor()

                # Get all table names
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()

                # Clear all tables
                for table in tables:
                    table_name = table[0]
                    cursor.execute(f"DELETE FROM {table_name}")
                    print(f"✅ Cleared table {table_name} in {cache_file.name}")

                conn.commit()
                conn.close()
                print(f"✅ Cleared cache file: {cache_file.name}")

            except Exception as e:
                print(f"❌ Error clearing {cache_file.name}: {e}")
    else:
        print("📁 Cache directory does not exist")


def backup_caches():
    """Backup current caches before clearing"""
    cache_dir = Path("data/cache")
    backup_dir = Path("data/cache_backup")

    if cache_dir.exists():
        backup_dir.mkdir(exist_ok=True)
        for cache_file in cache_dir.glob("*.db"):
            backup_file = backup_dir / f"{cache_file.stem}_backup.db"
            try:
                import shutil

                shutil.copy2(cache_file, backup_file)
                print(f"✅ Backed up {cache_file.name} to {backup_file.name}")
            except Exception as e:
                print(f"❌ Error backing up {cache_file.name}: {e}")


if __name__ == "__main__":
    print("🗑️ OmicsOracle Cache Management")
    print("=" * 40)

    # Backup first
    print("📦 Creating cache backups...")
    backup_caches()

    print("\n🧹 Clearing all caches...")
    clear_all_caches()

    print("\n✅ Cache clearing complete!")
    print("🔄 Restart the futuristic interface for changes to take effect.")
