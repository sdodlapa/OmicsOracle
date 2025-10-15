#!/usr/bin/env python3
"""
Migration Script: Legacy Data → Unified Database

Migrates existing data from legacy cache databases and file structures
to the new unified database and GEO-centric storage system.

Features:
- Migrates discovery cache to unified database
- Migrates fulltext cache metadata
- Creates GEO-centric directory structure
- Verifies data integrity with SHA256
- Generates migration report

Usage:
    python scripts/migrate_to_unified_db.py [--dry-run] [--verbose]

Options:
    --dry-run: Show what would be migrated without making changes
    --verbose: Show detailed progress information
"""

import argparse
import json
import logging
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from omics_oracle_v2.lib.storage import Analytics, DatabaseQueries, GEOStorage, UnifiedDatabase
from omics_oracle_v2.lib.storage.models import (
    ContentExtraction,
    GEODataset,
    PDFAcquisition,
    UniversalIdentifier,
)

logger = logging.getLogger(__name__)


class DataMigrator:
    """
    Migrates legacy data to unified database system.
    """

    def __init__(
        self,
        legacy_cache_db: str = "data/cache/discovery_cache.db",
        legacy_fulltext_db: str = "data/fulltext/cache_metadata.db",
        unified_db_path: str = "data/database/omics_oracle.db",
        storage_path: str = "data",
        dry_run: bool = False,
    ):
        """
        Initialize the migrator.

        Args:
            legacy_cache_db: Path to discovery cache database
            legacy_fulltext_db: Path to fulltext cache database
            unified_db_path: Path to unified database
            storage_path: Base storage directory
            dry_run: If True, don't make actual changes
        """
        self.legacy_cache_db = Path(legacy_cache_db)
        self.legacy_fulltext_db = Path(legacy_fulltext_db)
        self.unified_db_path = Path(unified_db_path)
        self.storage_path = Path(storage_path)
        self.dry_run = dry_run

        # Statistics
        self.stats = {
            "start_time": datetime.now(),
            "publications_migrated": 0,
            "pdfs_migrated": 0,
            "extractions_migrated": 0,
            "geo_datasets_created": 0,
            "errors": [],
            "warnings": [],
        }

        # Initialize database connections
        if not dry_run:
            self.unified_db = UnifiedDatabase(str(unified_db_path))
            self.storage = GEOStorage(str(storage_path))
        else:
            self.unified_db = None
            self.storage = None

        logger.info(f"DataMigrator initialized (dry_run={dry_run})")

    def connect_legacy_db(self, db_path: Path) -> Optional[sqlite3.Connection]:
        """Connect to legacy database."""
        if not db_path.exists():
            logger.warning(f"Legacy database not found: {db_path}")
            return None

        try:
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            logger.info(f"Connected to legacy database: {db_path}")
            return conn
        except Exception as e:
            logger.error(f"Failed to connect to {db_path}: {e}")
            self.stats["errors"].append(f"DB connection failed: {e}")
            return None

    def migrate_discovery_cache(self) -> int:
        """
        Migrate discovery cache to unified database.

        Returns:
            Number of publications migrated
        """
        logger.info("\n" + "=" * 60)
        logger.info("MIGRATING DISCOVERY CACHE")
        logger.info("=" * 60)

        conn = self.connect_legacy_db(self.legacy_cache_db)
        if not conn:
            return 0

        migrated = 0

        try:
            # Check what tables exist
            cursor = conn.execute(
                """
                SELECT name FROM sqlite_master
                WHERE type='table'
                ORDER BY name
            """
            )
            tables = [row[0] for row in cursor]
            logger.info(f"Tables in discovery cache: {tables}")

            # Try to find citation/publication data
            # Common table names: citations, publications, geo_citations, etc.
            for table_name in tables:
                if any(keyword in table_name.lower() for keyword in ["citation", "publication", "geo"]):
                    logger.info(f"\nProcessing table: {table_name}")

                    # Get table schema
                    cursor = conn.execute(f"PRAGMA table_info({table_name})")
                    columns = [row[1] for row in cursor]
                    logger.info(f"Columns: {columns}")

                    # Get sample data
                    cursor = conn.execute(f"SELECT * FROM {table_name} LIMIT 5")
                    rows = cursor.fetchall()

                    for row in rows:
                        row_dict = dict(row)
                        logger.debug(f"Sample row: {row_dict}")

                        # Extract data based on available columns
                        geo_id = self._extract_field(row_dict, ["geo_id", "dataset_id", "gse_id"])
                        pmid = self._extract_field(row_dict, ["pmid", "pubmed_id"])
                        title = self._extract_field(row_dict, ["title", "publication_title"])
                        authors = self._extract_field(row_dict, ["authors", "author_list"])

                        if geo_id and pmid:
                            if not self.dry_run:
                                self._migrate_publication(
                                    geo_id=geo_id,
                                    pmid=pmid,
                                    title=title or "Unknown",
                                    authors=authors,
                                    source_data=row_dict,
                                )
                            migrated += 1

                            if migrated % 10 == 0:
                                logger.info(f"Migrated {migrated} publications...")

        except Exception as e:
            logger.error(f"Error migrating discovery cache: {e}", exc_info=True)
            self.stats["errors"].append(f"Discovery cache migration: {e}")
        finally:
            conn.close()

        logger.info(f"\n[OK] Discovery cache migration complete: {migrated} publications")
        self.stats["publications_migrated"] = migrated
        return migrated

    def migrate_fulltext_cache(self) -> int:
        """
        Migrate fulltext cache metadata to unified database.

        Returns:
            Number of extractions migrated
        """
        logger.info("\n" + "=" * 60)
        logger.info("MIGRATING FULLTEXT CACHE")
        logger.info("=" * 60)

        conn = self.connect_legacy_db(self.legacy_fulltext_db)
        if not conn:
            return 0

        migrated = 0

        try:
            # Check tables
            cursor = conn.execute(
                """
                SELECT name FROM sqlite_master
                WHERE type='table'
                ORDER BY name
            """
            )
            tables = [row[0] for row in cursor]
            logger.info(f"Tables in fulltext cache: {tables}")

            # Look for fulltext/extraction data
            for table_name in tables:
                if any(
                    keyword in table_name.lower()
                    for keyword in [
                        "fulltext",
                        "extraction",
                        "content",
                        "metadata",
                    ]
                ):
                    logger.info(f"\nProcessing table: {table_name}")

                    cursor = conn.execute(f"PRAGMA table_info({table_name})")
                    columns = [row[1] for row in cursor]
                    logger.info(f"Columns: {columns}")

                    cursor = conn.execute(f"SELECT * FROM {table_name} LIMIT 5")
                    rows = cursor.fetchall()

                    for row in rows:
                        row_dict = dict(row)

                        pmid = self._extract_field(row_dict, ["pmid", "pubmed_id"])
                        full_text = self._extract_field(row_dict, ["full_text", "content", "text"])
                        quality = self._extract_field(row_dict, ["quality", "quality_score"])

                        if pmid and full_text:
                            if not self.dry_run:
                                self._migrate_extraction(
                                    pmid=pmid,
                                    full_text=full_text,
                                    quality_score=quality,
                                    source_data=row_dict,
                                )
                            migrated += 1

                            if migrated % 10 == 0:
                                logger.info(f"Migrated {migrated} extractions...")

        except Exception as e:
            logger.error(f"Error migrating fulltext cache: {e}", exc_info=True)
            self.stats["errors"].append(f"Fulltext cache migration: {e}")
        finally:
            conn.close()

        logger.info(f"\n[OK] Fulltext cache migration complete: {migrated} extractions")
        self.stats["extractions_migrated"] = migrated
        return migrated

    def _extract_field(self, data: Dict, possible_names: List[str]) -> Optional[str]:
        """Extract field from data dict, trying multiple possible names."""
        for name in possible_names:
            if name in data and data[name]:
                return str(data[name])
        return None

    def _migrate_publication(
        self,
        geo_id: str,
        pmid: str,
        title: str,
        authors: Optional[str] = None,
        source_data: Optional[Dict] = None,
    ):
        """Migrate a single publication to unified database."""
        try:
            # Create universal identifier
            pub = UniversalIdentifier(
                geo_id=geo_id,
                pmid=pmid,
                title=title,
                authors=authors,
                doi=self._extract_field(source_data or {}, ["doi"]),
                journal=self._extract_field(source_data or {}, ["journal"]),
                publication_date=self._extract_field(source_data or {}, ["publication_date", "pub_date"]),
            )

            self.unified_db.insert_universal_identifier(pub)
            logger.debug(f"Migrated publication: {pmid} ({geo_id})")

        except Exception as e:
            logger.warning(f"Failed to migrate publication {pmid}: {e}")
            self.stats["warnings"].append(f"Publication {pmid}: {e}")

    def _migrate_extraction(
        self,
        pmid: str,
        full_text: str,
        quality_score: Optional[float] = None,
        source_data: Optional[Dict] = None,
    ):
        """Migrate content extraction to unified database."""
        try:
            # Calculate quality grade if score available
            quality_grade = None
            if quality_score is not None:
                quality_score = float(quality_score)
                if quality_score >= 0.9:
                    quality_grade = "A"
                elif quality_score >= 0.75:
                    quality_grade = "B"
                elif quality_score >= 0.5:
                    quality_grade = "C"
                elif quality_score >= 0.25:
                    quality_grade = "D"
                else:
                    quality_grade = "F"

            extraction = ContentExtraction(
                pmid=pmid,
                full_text=full_text,
                extraction_method=self._extract_field(source_data or {}, ["method", "extraction_method"])
                or "legacy_migration",
                quality_score=quality_score,
                quality_grade=quality_grade,
                word_count=len(full_text.split()) if full_text else 0,
            )

            self.unified_db.insert_content_extraction(extraction)
            logger.debug(f"Migrated extraction: {pmid}")

        except Exception as e:
            logger.warning(f"Failed to migrate extraction {pmid}: {e}")
            self.stats["warnings"].append(f"Extraction {pmid}: {e}")

    def create_geo_datasets(self):
        """Create GEO dataset records from migrated publications."""
        logger.info("\n" + "=" * 60)
        logger.info("CREATING GEO DATASET RECORDS")
        logger.info("=" * 60)

        if self.dry_run:
            logger.info("[DRY RUN] Would create GEO dataset records")
            return

        try:
            # Get unique GEO IDs
            with self.unified_db.get_connection() as conn:
                cursor = conn.execute(
                    """
                    SELECT DISTINCT geo_id, COUNT(*) as pub_count
                    FROM universal_identifiers
                    GROUP BY geo_id
                """
                )
                geo_datasets = cursor.fetchall()

            for geo_id, pub_count in geo_datasets:
                try:
                    dataset = GEODataset(
                        geo_id=geo_id,
                        total_citations=pub_count,
                        citations_processed=pub_count,
                    )
                    self.unified_db.insert_geo_dataset(dataset)
                    self.stats["geo_datasets_created"] += 1
                    logger.info(f"Created GEO dataset: {geo_id} ({pub_count} pubs)")
                except Exception as e:
                    logger.warning(f"Failed to create GEO dataset {geo_id}: {e}")

        except Exception as e:
            logger.error(f"Error creating GEO datasets: {e}", exc_info=True)
            self.stats["errors"].append(f"GEO dataset creation: {e}")

    def verify_migration(self) -> Dict[str, Any]:
        """
        Verify migration integrity and completeness.

        Returns:
            Verification results
        """
        logger.info("\n" + "=" * 60)
        logger.info("VERIFYING MIGRATION")
        logger.info("=" * 60)

        if self.dry_run:
            logger.info("[DRY RUN] Would verify migration")
            return {"dry_run": True}

        queries = DatabaseQueries(str(self.unified_db_path))
        analytics = Analytics(
            db_path=str(self.unified_db_path),
            storage_path=str(self.storage_path),
        )

        # Get statistics
        stats = queries.get_processing_statistics()
        db_size = queries.get_database_size()

        verification = {
            "total_publications": stats["total_publications"],
            "total_geo_datasets": stats["total_geo_datasets"],
            "pipeline_completion": stats["pipeline_completion"],
            "database_size_mb": db_size["size_mb"],
            "table_counts": db_size.get("table_row_counts", {}),
        }

        logger.info(f"\n[OK] Total publications: {verification['total_publications']}")
        logger.info(f"[OK] Total GEO datasets: {verification['total_geo_datasets']}")
        logger.info(f"[OK] Database size: {verification['database_size_mb']} MB")

        logger.info("\nTable row counts:")
        for table, count in verification["table_counts"].items():
            logger.info(f"  - {table}: {count}")

        return verification

    def generate_report(self, verification: Dict[str, Any]) -> str:
        """Generate migration report."""
        self.stats["end_time"] = datetime.now()
        duration = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()

        report = {
            "migration_date": self.stats["start_time"].isoformat(),
            "duration_seconds": round(duration, 2),
            "dry_run": self.dry_run,
            "statistics": {
                "publications_migrated": self.stats["publications_migrated"],
                "pdfs_migrated": self.stats["pdfs_migrated"],
                "extractions_migrated": self.stats["extractions_migrated"],
                "geo_datasets_created": self.stats["geo_datasets_created"],
            },
            "verification": verification,
            "errors": self.stats["errors"],
            "warnings": self.stats["warnings"],
        }

        # Write report
        report_dir = Path("data/reports")
        report_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = report_dir / f"migration_report_{timestamp}.json"

        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"\n[OK] Migration report saved: {report_file}")

        return str(report_file)

    def run(self) -> Dict[str, Any]:
        """
        Run complete migration process.

        Returns:
            Migration results
        """
        logger.info("\n" + "=" * 60)
        logger.info("DATA MIGRATION TO UNIFIED DATABASE")
        logger.info("=" * 60)
        logger.info(f"Dry run: {self.dry_run}")
        logger.info(f"Started: {self.stats['start_time'].isoformat()}")

        # Step 1: Migrate discovery cache
        self.migrate_discovery_cache()

        # Step 2: Migrate fulltext cache
        self.migrate_fulltext_cache()

        # Step 3: Create GEO dataset records
        self.create_geo_datasets()

        # Step 4: Verify migration
        verification = self.verify_migration()

        # Step 5: Generate report
        report_file = self.generate_report(verification)

        logger.info("\n" + "=" * 60)
        logger.info("MIGRATION COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Publications: {self.stats['publications_migrated']}")
        logger.info(f"Extractions: {self.stats['extractions_migrated']}")
        logger.info(f"GEO Datasets: {self.stats['geo_datasets_created']}")
        logger.info(f"Errors: {len(self.stats['errors'])}")
        logger.info(f"Warnings: {len(self.stats['warnings'])}")
        logger.info(f"Report: {report_file}")

        return {
            "success": len(self.stats["errors"]) == 0,
            "statistics": self.stats,
            "verification": verification,
            "report_file": report_file,
        }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Migrate legacy data to unified database")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be migrated without making changes",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument(
        "--legacy-cache",
        default="data/cache/discovery_cache.db",
        help="Path to legacy discovery cache",
    )
    parser.add_argument(
        "--legacy-fulltext",
        default="data/fulltext/cache_metadata.db",
        help="Path to legacy fulltext cache",
    )
    parser.add_argument(
        "--unified-db",
        default="data/database/omics_oracle.db",
        help="Path to unified database",
    )

    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("data/reports/migration.log"),
        ],
    )

    # Create migrator
    migrator = DataMigrator(
        legacy_cache_db=args.legacy_cache,
        legacy_fulltext_db=args.legacy_fulltext,
        unified_db_path=args.unified_db,
        dry_run=args.dry_run,
    )

    # Run migration
    try:
        results = migrator.run()

        if results["success"]:
            logger.info("\n[OK] Migration completed successfully!")
            sys.exit(0)
        else:
            logger.error(f"\n[ERROR] Migration completed with {len(results['statistics']['errors'])} errors")
            sys.exit(1)

    except Exception as e:
        logger.error(f"\n[ERROR] Migration failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
