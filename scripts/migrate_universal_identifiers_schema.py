#!/usr/bin/env python3
"""
Migrate universal_identifiers table to new schema with optional PMID.

OLD SCHEMA:
    pmid TEXT NOT NULL,
    PRIMARY KEY (geo_id, pmid)

NEW SCHEMA:
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pmid TEXT,  -- Optional
    CHECK (pmid IS NOT NULL OR doi IS NOT NULL OR pmc_id IS NOT NULL OR arxiv_id IS NOT NULL)

This migration is necessary because:
1. Not all papers have PMIDs (preprints, DOI-only, etc.)
2. Waterfall PDF download system is designed to work with ANY identifier
3. Universal identifier philosophy: Support maximum paper coverage

Usage:
    python scripts/migrate_universal_identifiers_schema.py
    python scripts/migrate_universal_identifiers_schema.py --dry-run
    python scripts/migrate_universal_identifiers_schema.py --backup-path data/backups/
"""

import argparse
import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

def backup_database(db_path: str, backup_dir: str = "data/backups") -> str:
    """Create backup of database before migration."""
    backup_path = Path(backup_dir)
    backup_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_path / f"omics_oracle_backup_{timestamp}.db"
    
    shutil.copy2(db_path, backup_file)
    print(f"✅ Database backed up to: {backup_file}")
    return str(backup_file)


def migrate_schema(db_path: str, dry_run: bool = False):
    """
    Migrate universal_identifiers table to new schema.
    
    Steps:
    1. Create new table with correct schema
    2. Copy data from old table (only rows with PMID)
    3. Drop old table
    4. Rename new table
    5. Recreate indexes
    """
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n" + "=" * 80)
    print("UNIVERSAL IDENTIFIERS SCHEMA MIGRATION")
    print("=" * 80)
    
    # Step 1: Check current schema
    print("\n[1/6] Checking current schema...")
    cursor.execute("PRAGMA table_info(universal_identifiers)")
    columns = cursor.fetchall()
    
    pmid_col = next((col for col in columns if col[1] == 'pmid'), None)
    if pmid_col:
        is_nullable = pmid_col[3] == 0  # notnull = 0 means nullable
        print(f"   Current PMID column: {'NULLABLE' if is_nullable else 'NOT NULL'}")
        if is_nullable:
            print("   ⚠️  Schema already migrated! Exiting.")
            conn.close()
            return
    
    # Step 2: Count existing rows
    cursor.execute("SELECT COUNT(*) FROM universal_identifiers")
    total_rows = cursor.fetchone()[0]
    print(f"\n[2/6] Found {total_rows} existing records")
    
    cursor.execute("SELECT COUNT(*) FROM universal_identifiers WHERE pmid IS NULL OR pmid = ''")
    null_pmid_count = cursor.fetchone()[0]
    if null_pmid_count > 0:
        print(f"   ⚠️  Warning: {null_pmid_count} rows have NULL/empty PMID (will be preserved)")
    
    if dry_run:
        print("\n🔍 DRY RUN MODE - No changes will be made")
        conn.close()
        return
    
    # Step 3: Create new table with correct schema
    print("\n[3/6] Creating new table with updated schema...")
    cursor.execute("""
        CREATE TABLE universal_identifiers_new (
            -- Auto-incrementing primary key
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            
            -- GEO dataset reference
            geo_id TEXT NOT NULL,
            
            -- Publication identifiers (at least one should be present)
            pmid TEXT,  -- Optional - not all papers have PMIDs
            doi TEXT,
            pmc_id TEXT,
            arxiv_id TEXT,

            -- Publication metadata
            title TEXT,
            authors TEXT,
            journal TEXT,
            publication_year INTEGER,
            publication_date TEXT,

            -- Timestamps
            first_discovered_at TEXT NOT NULL,
            last_updated_at TEXT NOT NULL,

            -- Ensure at least one identifier exists
            CHECK (pmid IS NOT NULL OR doi IS NOT NULL OR pmc_id IS NOT NULL OR arxiv_id IS NOT NULL),
            
            -- Prevent duplicate entries for same paper
            UNIQUE(geo_id, pmid, doi)
        )
    """)
    print("   ✅ New table created")
    
    # Step 4: Copy data from old table
    print("\n[4/6] Copying data from old table...")
    cursor.execute("""
        INSERT INTO universal_identifiers_new 
        (geo_id, pmid, doi, pmc_id, arxiv_id, title, authors, journal, 
         publication_year, publication_date, first_discovered_at, last_updated_at)
        SELECT 
            geo_id, pmid, doi, pmc_id, arxiv_id, title, authors, journal,
            publication_year, publication_date, first_discovered_at, last_updated_at
        FROM universal_identifiers
    """)
    rows_copied = cursor.rowcount
    print(f"   ✅ Copied {rows_copied} rows")
    
    # Step 5: Drop old table and rename new one
    print("\n[5/6] Replacing old table...")
    cursor.execute("DROP TABLE universal_identifiers")
    cursor.execute("ALTER TABLE universal_identifiers_new RENAME TO universal_identifiers")
    print("   ✅ Table replaced")
    
    # Step 6: Recreate indexes
    print("\n[6/6] Recreating indexes...")
    cursor.execute("CREATE INDEX idx_ui_geo_id ON universal_identifiers(geo_id)")
    cursor.execute("CREATE INDEX idx_ui_pmid ON universal_identifiers(pmid)")
    cursor.execute("CREATE INDEX idx_ui_doi ON universal_identifiers(doi)")
    cursor.execute("CREATE INDEX idx_ui_year ON universal_identifiers(publication_year)")
    cursor.execute("CREATE INDEX idx_ui_geo_pmid_composite ON universal_identifiers(geo_id, pmid)")
    print("   ✅ Indexes recreated")
    
    # Commit changes
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 80)
    print("✅ MIGRATION COMPLETE!")
    print("=" * 80)
    print(f"\nMigrated {rows_copied} records")
    print("PMID is now OPTIONAL - papers with only DOI/PMC/arXiv will work")
    print("\nNext steps:")
    print("  1. Restart server: ./start_omics_oracle.sh")
    print("  2. Test auto-discovery with new schema")
    print("  3. Verify papers with DOI-only are stored correctly")
    print()


def main():
    parser = argparse.ArgumentParser(description="Migrate universal_identifiers schema")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default="data/database/omics_oracle.db",
        help="Path to database file"
    )
    parser.add_argument(
        "--backup-path",
        type=str,
        default="data/backups",
        help="Path to backup directory"
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip backup (NOT RECOMMENDED)"
    )
    
    args = parser.parse_args()
    
    # Create backup unless disabled
    if not args.no_backup and not args.dry_run:
        backup_database(args.db_path, args.backup_path)
    
    # Run migration
    migrate_schema(args.db_path, args.dry_run)


if __name__ == "__main__":
    main()
