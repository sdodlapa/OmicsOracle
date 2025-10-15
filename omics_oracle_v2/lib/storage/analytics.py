"""
Analytics and export utilities for the unified database.

This module provides methods for:
- Exporting GEO datasets
- Generating reports and visualizations
- Analyzing quality and performance trends

Classes:
    Analytics: Analytics and export interface
"""

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .geo_storage import GEOStorage
from .queries import DatabaseQueries
from .unified_db import UnifiedDatabase

logger = logging.getLogger(__name__)


class Analytics:
    """
    Analytics and export interface for the unified database.

    Provides methods for:
    - Exporting complete GEO datasets
    - Generating quality reports
    - Analyzing processing trends
    - Creating summary statistics
    """

    def __init__(
        self,
        db_path: str = "data/database/omics_oracle.db",
        storage_path: str = "data",
    ):
        """
        Initialize the analytics interface.

        Args:
            db_path: Path to the SQLite database file
            storage_path: Base path for file storage
        """
        self.db_path = db_path
        self.storage_path = Path(storage_path)
        self.db = UnifiedDatabase(db_path)
        self.queries = DatabaseQueries(db_path)
        self.storage = GEOStorage(storage_path)
        logger.info(f"Analytics initialized with database: {db_path}")

    # =========================================================================
    # EXPORT OPERATIONS
    # =========================================================================

    def export_geo_dataset(
        self,
        geo_id: str,
        output_dir: str,
        include_pdfs: bool = True,
        include_enriched: bool = True,
    ) -> Dict[str, Any]:
        """
        Export all data for a GEO dataset to a directory.

        Creates a structured export with:
        - metadata.json: Dataset and publication metadata
        - publications.json: All publication records
        - pdfs/: PDF files (if requested)
        - enriched/: Enriched content JSON files (if requested)

        Args:
            geo_id: GEO dataset identifier
            output_dir: Directory to export to
            include_pdfs: Whether to copy PDF files
            include_enriched: Whether to copy enriched content

        Returns:
            Dictionary with export summary
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"Exporting GEO dataset {geo_id} to {output_dir}")

        # Get all data
        publications = self.queries.get_geo_publications(geo_id, include_incomplete=True)
        stats = self.queries.get_geo_statistics(geo_id)

        # Create metadata file
        metadata = {
            "geo_id": geo_id,
            "export_date": datetime.now().isoformat(),
            "statistics": stats,
            "publication_count": len(publications),
        }

        metadata_file = output_path / "metadata.json"
        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)

        # Export publications data
        pubs_file = output_path / "publications.json"
        with open(pubs_file, "w") as f:
            json.dump(publications, f, indent=2)

        export_summary = {
            "geo_id": geo_id,
            "output_directory": str(output_path),
            "publication_count": len(publications),
            "files_created": ["metadata.json", "publications.json"],
            "pdfs_copied": 0,
            "enriched_copied": 0,
        }

        # Copy PDFs if requested
        if include_pdfs:
            pdf_dir = output_path / "pdfs"
            pdf_dir.mkdir(exist_ok=True)

            for pub in publications:
                if pub.get("pdf_path"):
                    pdf_path = Path(pub["pdf_path"])
                    if pdf_path.exists():
                        dest = pdf_dir / pdf_path.name
                        shutil.copy2(pdf_path, dest)
                        export_summary["pdfs_copied"] += 1

        # Copy enriched content if requested
        if include_enriched:
            enriched_dir = output_path / "enriched"
            enriched_dir.mkdir(exist_ok=True)

            for pub in publications:
                pmid = pub["pmid"]
                enriched_data = self.storage.get_enriched(geo_id, pmid)
                if enriched_data:
                    enriched_file = enriched_dir / f"pmid_{pmid}.json"
                    with open(enriched_file, "w") as f:
                        json.dump(enriched_data, f, indent=2)
                    export_summary["enriched_copied"] += 1

        logger.info(
            f"Export complete: {export_summary['publication_count']} "
            f"publications, {export_summary['pdfs_copied']} PDFs, "
            f"{export_summary['enriched_copied']} enriched files"
        )

        return export_summary

    def export_quality_report(self, output_file: str, min_quality: Optional[float] = None) -> Dict[str, Any]:
        """
        Generate a quality report for all extracted content.

        Args:
            output_file: Path to write the report JSON
            min_quality: Minimum quality score to include

        Returns:
            Dictionary with report summary
        """
        logger.info(f"Generating quality report: {output_file}")

        # Get publications by quality
        publications = self.queries.get_publications_by_quality(min_quality=min_quality)

        # Calculate statistics
        extraction_qualitys = [p["extraction_quality"] for p in publications if p["extraction_quality"]]

        report = {
            "generated_at": datetime.now().isoformat(),
            "total_publications": len(publications),
            "statistics": {
                "average_quality": (
                    round(sum(extraction_qualitys) / len(extraction_qualitys), 3)
                    if extraction_qualitys
                    else None
                ),
                "min_quality": min(extraction_qualitys) if extraction_qualitys else None,
                "max_quality": max(extraction_qualitys) if extraction_qualitys else None,
            },
            "publications": publications,
        }

        # Add grade distribution
        grade_dist = {}
        for pub in publications:
            grade = pub.get("extraction_grade")
            if grade:
                grade_dist[grade] = grade_dist.get(grade, 0) + 1
        report["grade_distribution"] = grade_dist

        # Write report
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"Quality report written: {len(publications)} publications")

        return {
            "output_file": str(output_path),
            "publication_count": len(publications),
            "statistics": report["statistics"],
            "grade_distribution": report["grade_distribution"],
        }

    def export_processing_summary(self, output_file: str) -> Dict[str, Any]:
        """
        Generate a comprehensive processing summary report.

        Args:
            output_file: Path to write the summary JSON

        Returns:
            Dictionary with summary information
        """
        logger.info(f"Generating processing summary: {output_file}")

        report = {
            "generated_at": datetime.now().isoformat(),
            "overall_statistics": self.queries.get_processing_statistics(),
            "pipeline_performance": self.queries.get_pipeline_performance(),
            "database_info": self.queries.get_database_size(),
        }

        # Get GEO dataset summaries
        with self.db.get_connection() as conn:
            cursor = conn.execute("SELECT DISTINCT geo_id FROM universal_identifiers")
            geo_ids = [row[0] for row in cursor]

        report["geo_datasets"] = {}
        for geo_id in geo_ids:
            report["geo_datasets"][geo_id] = self.queries.get_geo_statistics(geo_id)

        # Write report
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"Processing summary written: {len(geo_ids)} GEO datasets")

        return {
            "output_file": str(output_path),
            "geo_dataset_count": len(geo_ids),
            "total_publications": report["overall_statistics"]["total_publications"],
        }

    # =========================================================================
    # ANALYSIS OPERATIONS
    # =========================================================================

    def calculate_quality_distribution(self) -> Dict[str, Any]:
        """
        Calculate detailed quality distribution across all content.

        Returns:
            Dictionary with quality statistics and distributions
        """
        stats = self.queries.get_processing_statistics()

        # Get detailed score distribution
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT
                    extraction_quality,
                    extraction_grade,
                    COUNT(*) as count
                FROM content_extraction
                WHERE extraction_quality IS NOT NULL
                GROUP BY extraction_quality, extraction_grade
                ORDER BY extraction_quality DESC
            """
            )

            score_distribution = []
            for row in cursor:
                score_distribution.append(
                    {
                        "extraction_quality": row[0],
                        "extraction_grade": row[1],
                        "count": row[2],
                    }
                )

        # Calculate percentiles
        cursor = conn.execute(
            """
            SELECT extraction_quality
            FROM content_extraction
            WHERE extraction_quality IS NOT NULL
            ORDER BY extraction_quality
        """
        )
        scores = [row[0] for row in cursor]

        percentiles = {}
        if scores:
            percentiles = {
                "p25": scores[len(scores) // 4],
                "p50": scores[len(scores) // 2],
                "p75": scores[(3 * len(scores)) // 4],
                "p90": scores[(9 * len(scores)) // 10],
                "p95": scores[(95 * len(scores)) // 100],
            }

        return {
            "grade_distribution": stats.get("quality_distribution", {}),
            "average_score": stats.get("average_extraction_quality"),
            "score_distribution": score_distribution,
            "percentiles": percentiles,
            "total_extracted": len(scores),
        }

    def analyze_pipeline_trends(self, days: int = 30) -> Dict[str, List[Dict[str, Any]]]:
        """
        Analyze processing trends over time.

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary with daily processing statistics per pipeline
        """
        from datetime import timedelta

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        query = """
            SELECT
                DATE(created_at) as date,
                pipeline_name,
                COUNT(*) as operations,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful,
                AVG(duration_seconds) as avg_duration
            FROM processing_log
            WHERE created_at >= ?
            GROUP BY DATE(created_at), pipeline_name
            ORDER BY date DESC, pipeline_name
        """

        with self.db.get_connection() as conn:
            cursor = conn.execute(query, (start_date.isoformat(),))
            columns = [desc[0] for desc in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor]

        # Organize by pipeline
        trends = {}
        for row in results:
            pipeline = row["pipeline_name"]
            if pipeline not in trends:
                trends[pipeline] = []

            trends[pipeline].append(
                {
                    "date": row["date"],
                    "operations": row["operations"],
                    "successful": row["successful"],
                    "success_rate": round((row["successful"] / row["operations"]) * 100, 2),
                    "avg_duration": (round(row["avg_duration"], 3) if row["avg_duration"] else None),
                }
            )

        logger.info(f"Analyzed {days}-day trends for all pipelines")
        return trends

    def identify_quality_issues(self, threshold: float = 0.5) -> List[Dict[str, Any]]:
        """
        Identify publications with quality issues.

        Args:
            threshold: Quality score threshold (publications below are flagged)

        Returns:
            List of publications with quality issues
        """
        query = """
            SELECT
                ui.geo_id,
                ui.pmid,
                ui.title,
                ce.extraction_quality,
                ce.extraction_grade,
                ce.word_count,
                ce.extraction_method,
                pa.pdf_path
            FROM universal_identifiers ui
            JOIN content_extraction ce ON ui.pmid = ce.pmid
            LEFT JOIN pdf_acquisition pa ON ui.pmid = pa.pmid
            WHERE ce.extraction_quality < ?
            ORDER BY ce.extraction_quality ASC
        """

        with self.db.get_connection() as conn:
            cursor = conn.execute(query, (threshold,))
            columns = [desc[0] for desc in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor]

        logger.info(f"Identified {len(results)} publications with quality < {threshold}")
        return results

    def get_storage_efficiency(self) -> Dict[str, Any]:
        """
        Analyze storage efficiency and file organization.

        Returns:
            Dictionary with storage statistics
        """
        # Get database size
        db_size = self.queries.get_database_size()

        # Calculate filesystem statistics
        pdf_base = self.storage_path / "pdfs" / "by_geo"
        enriched_base = self.storage_path / "enriched" / "by_geo"

        pdf_stats = {"total_bytes": 0, "file_count": 0, "geo_count": 0}
        enriched_stats = {"total_bytes": 0, "file_count": 0, "geo_count": 0}

        if pdf_base.exists():
            for geo_dir in pdf_base.iterdir():
                if geo_dir.is_dir():
                    pdf_stats["geo_count"] += 1
                    for pdf_file in geo_dir.glob("*.pdf"):
                        pdf_stats["file_count"] += 1
                        pdf_stats["total_bytes"] += pdf_file.stat().st_size

        if enriched_base.exists():
            for geo_dir in enriched_base.iterdir():
                if geo_dir.is_dir():
                    enriched_stats["geo_count"] += 1
                    for json_file in geo_dir.glob("*.json"):
                        enriched_stats["file_count"] += 1
                        enriched_stats["total_bytes"] += json_file.stat().st_size

        return {
            "database": {
                "size_bytes": db_size["size_bytes"],
                "size_mb": db_size["size_mb"],
                "table_counts": db_size.get("table_row_counts", {}),
            },
            "pdfs": {
                "total_bytes": pdf_stats["total_bytes"],
                "total_mb": round(pdf_stats["total_bytes"] / 1024 / 1024, 2),
                "file_count": pdf_stats["file_count"],
                "geo_dataset_count": pdf_stats["geo_count"],
            },
            "enriched": {
                "total_bytes": enriched_stats["total_bytes"],
                "total_mb": round(enriched_stats["total_bytes"] / 1024 / 1024, 2),
                "file_count": enriched_stats["file_count"],
                "geo_dataset_count": enriched_stats["geo_count"],
            },
            "total_storage_mb": round(
                (db_size["size_bytes"] + pdf_stats["total_bytes"] + enriched_stats["total_bytes"])
                / 1024
                / 1024,
                2,
            ),
        }

    # =========================================================================
    # VERIFICATION AND INTEGRITY
    # =========================================================================

    def verify_data_integrity(self, geo_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Verify data integrity across database and filesystem.

        Args:
            geo_id: Optional GEO ID to check (checks all if None)

        Returns:
            Dictionary with verification results
        """
        logger.info(f"Verifying data integrity for " f"{geo_id if geo_id else 'all datasets'}")

        results = {
            "verified_at": datetime.now().isoformat(),
            "issues": [],
            "summary": {
                "total_checked": 0,
                "pdfs_verified": 0,
                "pdfs_failed": 0,
                "missing_files": 0,
                "orphaned_records": 0,
            },
        }

        # Get publications to check
        if geo_id:
            publications = self.queries.get_geo_publications(geo_id, include_incomplete=False)
        else:
            with self.db.get_connection() as conn:
                cursor = conn.execute(
                    """
                    SELECT ui.geo_id, ui.pmid, pa.pdf_path, pa.sha256
                    FROM universal_identifiers ui
                    JOIN pdf_acquisition pa ON ui.pmid = pa.pmid
                """
                )
                columns = [desc[0] for desc in cursor.description]
                publications = [dict(zip(columns, row)) for row in cursor]

        results["summary"]["total_checked"] = len(publications)

        # Verify each publication
        for pub in publications:
            pdf_path = pub.get("pdf_path")
            expected_hash = pub.get("sha256")
            pmid = pub["pmid"]
            pub_geo_id = pub["geo_id"]

            if not pdf_path:
                results["issues"].append(
                    {
                        "type": "missing_record",
                        "geo_id": pub_geo_id,
                        "pmid": pmid,
                        "message": "No PDF path in database",
                    }
                )
                results["summary"]["orphaned_records"] += 1
                continue

            # Check file exists
            file_path = Path(pdf_path)
            if not file_path.exists():
                results["issues"].append(
                    {
                        "type": "missing_file",
                        "geo_id": pub_geo_id,
                        "pmid": pmid,
                        "path": str(file_path),
                        "message": "PDF file not found on filesystem",
                    }
                )
                results["summary"]["missing_files"] += 1
                continue

            # Verify hash if available
            if expected_hash:
                verification = self.storage.verify_pdf(pub_geo_id, pmid)
                if verification["verified"]:
                    results["summary"]["pdfs_verified"] += 1
                else:
                    results["issues"].append(
                        {
                            "type": "hash_mismatch",
                            "geo_id": pub_geo_id,
                            "pmid": pmid,
                            "path": str(file_path),
                            "expected_hash": expected_hash,
                            "actual_hash": verification.get("actual_hash"),
                            "message": "PDF hash does not match expected value",
                        }
                    )
                    results["summary"]["pdfs_failed"] += 1

        logger.info(
            f"Integrity check complete: "
            f"{results['summary']['pdfs_verified']} verified, "
            f"{len(results['issues'])} issues found"
        )

        return results
