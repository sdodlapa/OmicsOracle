"""
High-level query interface for the unified database.

This module provides a user-friendly API for querying publications,
analyzing processing status, and generating reports from the unified database.

Classes:
    DatabaseQueries: High-level query interface
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from .unified_db import UnifiedDatabase

logger = logging.getLogger(__name__)


class DatabaseQueries:
    """
    High-level query interface for the unified database.

    Provides convenient methods for:
    - Querying publications by various criteria
    - Analyzing processing status and completion
    - Generating statistics and reports
    - Filtering by quality, date, GEO dataset, etc.
    """

    def __init__(self, db_path: str = "data/database/omics_oracle.db"):
        """
        Initialize the query interface.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.db = UnifiedDatabase(db_path)
        logger.info(f"DatabaseQueries initialized with database: {db_path}")

    # =========================================================================
    # PUBLICATION QUERIES
    # =========================================================================

    def get_geo_publications(self, geo_id: str, include_incomplete: bool = True) -> List[Dict[str, Any]]:
        """
        Get all publications associated with a GEO dataset.

        Args:
            geo_id: GEO dataset identifier (e.g., "GSE12345")
            include_incomplete: If False, only return publications with PDFs

        Returns:
            List of publication dictionaries with all available data
        """
        query = """
            SELECT
                ui.*,
                ud.url_count, ud.sources_queried,
                pa.pdf_path, pa.pdf_hash_sha256, pa.pdf_size_bytes,
                ce.extraction_method, ce.extraction_quality, ce.extraction_grade,
                ec.sections_json, ec.tables_json, ec.references_json
            FROM universal_identifiers ui
            LEFT JOIN url_discovery ud ON ui.geo_id = ud.geo_id AND ui.pmid = ud.pmid
            LEFT JOIN pdf_acquisition pa ON ui.geo_id = pa.geo_id AND ui.pmid = pa.pmid
            LEFT JOIN content_extraction ce ON ui.geo_id = ce.geo_id AND ui.pmid = ce.pmid
            LEFT JOIN enriched_content ec ON ui.geo_id = ec.geo_id AND ui.pmid = ec.pmid
            WHERE ui.geo_id = ?
        """

        if not include_incomplete:
            query += " AND pa.pdf_path IS NOT NULL"

        query += " ORDER BY ui.first_discovered_at DESC"

        with self.db.get_connection() as conn:
            cursor = conn.execute(query, (geo_id,))
            columns = [desc[0] for desc in cursor.description]
            results = []

            for row in cursor:
                pub = dict(zip(columns, row))
                results.append(pub)

        logger.info(f"Found {len(results)} publications for GEO dataset {geo_id}")
        return results

    def get_publication_details(self, pmid: str) -> Optional[Dict[str, Any]]:
        """
        Get complete details for a single publication.

        Args:
            pmid: PubMed identifier

        Returns:
            Dictionary with all available publication data, or None if not found
        """
        query = """
            SELECT
                ui.*,
                ud.url_count, ud.sources_queried, ud.has_pdf_url, ud.has_html_url,
                pa.pdf_path, pa.pdf_hash_sha256, pa.pdf_size_bytes, pa.source_type,
                ce.extraction_method, ce.extraction_quality, ce.extraction_grade,
                ce.full_text, ce.word_count,
                ec.sections_json, ec.tables_json, ec.references_json
            FROM universal_identifiers ui
            LEFT JOIN url_discovery ud ON ui.geo_id = ud.geo_id AND ui.pmid = ud.pmid
            LEFT JOIN pdf_acquisition pa ON ui.geo_id = pa.geo_id AND ui.pmid = pa.pmid
            LEFT JOIN content_extraction ce ON ui.geo_id = ce.geo_id AND ui.pmid = ce.pmid
            LEFT JOIN enriched_content ec ON ui.geo_id = ec.geo_id AND ui.pmid = ec.pmid
            WHERE ui.pmid = ?
        """

        with self.db.get_connection() as conn:
            cursor = conn.execute(query, (pmid,))
            columns = [desc[0] for desc in cursor.description]
            row = cursor.fetchone()

            if row:
                return dict(zip(columns, row))
            return None

    def get_publications_by_quality(
        self,
        min_quality: Optional[float] = None,
        extraction_grades: Optional[List[str]] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get publications filtered by quality metrics.

        Args:
            min_quality: Minimum quality score (0.0 to 1.0)
            extraction_grades: List of quality grades to include (e.g., ["A", "B"])
            limit: Maximum number of results to return

        Returns:
            List of publication dictionaries
        """
        query = """
            SELECT
                ui.geo_id, ui.pmid, ui.title, ui.authors,
                ce.extraction_quality, ce.extraction_grade, ce.word_count,
                pa.pdf_path, pa.pdf_size_bytes
            FROM universal_identifiers ui
            INNER JOIN content_extraction ce ON ui.geo_id = ce.geo_id AND ui.pmid = ce.pmid
            LEFT JOIN pdf_acquisition pa ON ui.geo_id = pa.geo_id AND ui.pmid = pa.pmid
            WHERE 1=1
        """

        params = []

        if min_quality is not None:
            query += " AND ce.extraction_quality >= ?"
            params.append(min_quality)

        if extraction_grades:
            placeholders = ",".join("?" * len(extraction_grades))
            query += f" AND ce.extraction_grade IN ({placeholders})"
            params.extend(extraction_grades)

        query += " ORDER BY ce.extraction_quality DESC"

        if limit:
            query += " LIMIT ?"
            params.append(limit)

        with self.db.get_connection() as conn:
            cursor = conn.execute(query, params)
            columns = [desc[0] for desc in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor]

        logger.info(f"Found {len(results)} publications matching quality criteria")
        return results

    def get_publications_by_date_range(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        date_field: str = "first_discovered_at",
    ) -> List[Dict[str, Any]]:
        """
        Get publications within a date range.

        Args:
            start_date: ISO format date (e.g., "2024-01-01")
            end_date: ISO format date (e.g., "2024-12-31")
            date_field: Which date to filter on ("first_discovered_at" or "last_updated_at")

        Returns:
            List of publication dictionaries
        """
        if date_field not in ["first_discovered_at", "last_updated_at"]:
            raise ValueError(
                f"Invalid date_field: {date_field}. " "Must be 'first_discovered_at' or 'last_updated_at'"
            )

        query = f"""
            SELECT
                ui.*,
                pa.pdf_path,
                ce.extraction_quality, ce.extraction_grade
            FROM universal_identifiers ui
            LEFT JOIN pdf_acquisition pa ON ui.pmid = pa.pmid
            LEFT JOIN content_extraction ce ON ui.pmid = ce.pmid
            WHERE 1=1
        """

        params = []

        if start_date:
            query += f" AND ui.{date_field} >= ?"
            params.append(start_date)

        if end_date:
            query += f" AND ui.{date_field} <= ?"
            params.append(end_date)

        query += f" ORDER BY ui.{date_field} DESC"

        with self.db.get_connection() as conn:
            cursor = conn.execute(query, params)
            columns = [desc[0] for desc in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor]

        logger.info(
            f"Found {len(results)} publications in date range "
            f"{start_date or 'beginning'} to {end_date or 'now'}"
        )
        return results

    def get_incomplete_publications(self) -> List[Dict[str, Any]]:
        """
        Get publications that are missing data from any pipeline stage.

        Returns:
            List of publications with status indicators for each stage
        """
        query = """
            SELECT
                ui.geo_id,
                ui.pmid,
                ui.title,
                CASE WHEN ud.pmid IS NOT NULL THEN 1 ELSE 0 END as has_urls,
                CASE WHEN pa.pmid IS NOT NULL THEN 1 ELSE 0 END as has_pdf,
                CASE WHEN ce.pmid IS NOT NULL THEN 1 ELSE 0 END as has_extraction,
                CASE WHEN ec.pmid IS NOT NULL THEN 1 ELSE 0 END as has_enriched,
                ui.first_discovered_at,
                ui.last_updated_at
            FROM universal_identifiers ui
            LEFT JOIN url_discovery ud ON ui.pmid = ud.pmid
            LEFT JOIN pdf_acquisition pa ON ui.pmid = pa.pmid
            LEFT JOIN content_extraction ce ON ui.pmid = ce.pmid
            LEFT JOIN enriched_content ec ON ui.pmid = ec.pmid
            WHERE
                ud.pmid IS NULL OR
                pa.pmid IS NULL OR
                ce.pmid IS NULL OR
                ec.pmid IS NULL
            ORDER BY ui.first_discovered_at DESC
        """

        with self.db.get_connection() as conn:
            cursor = conn.execute(query)
            columns = [desc[0] for desc in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor]

        logger.info(f"Found {len(results)} incomplete publications")
        return results

    def search_publications(
        self, search_term: str, search_fields: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search publications by text in title, authors, or full text.

        Args:
            search_term: Text to search for
            search_fields: List of fields to search in
                          (default: ["title", "authors", "full_text"])

        Returns:
            List of matching publications
        """
        if search_fields is None:
            search_fields = ["title", "authors", "full_text"]

        conditions = []
        params = []

        for field in search_fields:
            if field in ["title", "authors"]:
                conditions.append(f"ui.{field} LIKE ?")
            elif field == "full_text":
                conditions.append("ce.full_text LIKE ?")
            params.append(f"%{search_term}%")

        where_clause = " OR ".join(conditions)

        query = f"""
            SELECT DISTINCT
                ui.geo_id, ui.pmid, ui.title, ui.authors,
                ce.extraction_quality, ce.extraction_grade,
                pa.pdf_path
            FROM universal_identifiers ui
            LEFT JOIN content_extraction ce ON ui.pmid = ce.pmid
            LEFT JOIN pdf_acquisition pa ON ui.pmid = pa.pmid
            WHERE {where_clause}
            ORDER BY ui.first_discovered_at DESC
        """

        with self.db.get_connection() as conn:
            cursor = conn.execute(query, params)
            columns = [desc[0] for desc in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor]

        logger.info(f"Found {len(results)} publications matching '{search_term}'")
        return results

    # =========================================================================
    # STATISTICS AND ANALYTICS
    # =========================================================================

    def get_processing_statistics(self) -> Dict[str, Any]:
        """
        Get overall processing statistics across all pipelines.

        Returns:
            Dictionary with comprehensive statistics
        """
        stats = {}

        with self.db.get_connection() as conn:
            # Total publications
            cursor = conn.execute("SELECT COUNT(*) FROM universal_identifiers")
            stats["total_publications"] = cursor.fetchone()[0]

            # Pipeline completion counts
            cursor = conn.execute(
                """
                SELECT
                    COUNT(DISTINCT ud.pmid) as url_discovery,
                    COUNT(DISTINCT pa.pmid) as pdf_acquisition,
                    COUNT(DISTINCT ce.pmid) as content_extraction,
                    COUNT(DISTINCT ec.pmid) as enriched_content
                FROM universal_identifiers ui
                LEFT JOIN url_discovery ud ON ui.pmid = ud.pmid
                LEFT JOIN pdf_acquisition pa ON ui.pmid = pa.pmid
                LEFT JOIN content_extraction ce ON ui.pmid = ce.pmid
                LEFT JOIN enriched_content ec ON ui.pmid = ec.pmid
            """
            )
            row = cursor.fetchone()
            stats["pipeline_completion"] = {
                "url_discovery": row[0],
                "pdf_acquisition": row[1],
                "content_extraction": row[2],
                "enriched_content": row[3],
            }

            # Quality distribution
            cursor = conn.execute(
                """
                SELECT extraction_grade, COUNT(*) as count
                FROM content_extraction
                WHERE extraction_grade IS NOT NULL
                GROUP BY extraction_grade
                ORDER BY extraction_grade
            """
            )
            stats["quality_distribution"] = {row[0]: row[1] for row in cursor}

            # Average quality score
            cursor = conn.execute(
                """
                SELECT AVG(extraction_quality) as avg_quality
                FROM content_extraction
                WHERE extraction_quality IS NOT NULL
            """
            )
            avg_quality = cursor.fetchone()[0]
            stats["average_extraction_quality"] = round(avg_quality, 3) if avg_quality else None

            # GEO dataset count
            cursor = conn.execute("SELECT COUNT(DISTINCT geo_id) FROM universal_identifiers")
            stats["total_geo_datasets"] = cursor.fetchone()[0]

            # Storage statistics
            cursor = conn.execute(
                """
                SELECT
                    SUM(pdf_size_bytes) as total_size,
                    COUNT(*) as pdf_count
                FROM pdf_acquisition
                WHERE pdf_size_bytes IS NOT NULL
            """
            )
            row = cursor.fetchone()
            stats["storage"] = {
                "total_pdf_bytes": row[0] or 0,
                "total_pdf_mb": round((row[0] or 0) / 1024 / 1024, 2),
                "pdf_count": row[1],
            }

        logger.info("Generated processing statistics")
        return stats

    def get_geo_statistics(self, geo_id: str) -> Dict[str, Any]:
        """
        Get detailed statistics for a specific GEO dataset.

        Args:
            geo_id: GEO dataset identifier

        Returns:
            Dictionary with dataset-specific statistics
        """
        stats = {"geo_id": geo_id}

        with self.db.get_connection() as conn:
            # GEO dataset info
            cursor = conn.execute("SELECT * FROM geo_datasets WHERE geo_id = ?", (geo_id,))
            row = cursor.fetchone()
            if row:
                stats["dataset_info"] = dict(zip([desc[0] for desc in cursor.description], row))

            # Publication counts by stage
            cursor = conn.execute(
                """
                SELECT
                    COUNT(*) as total,
                    COUNT(DISTINCT ud.pmid) as with_urls,
                    COUNT(DISTINCT pa.pmid) as with_pdf,
                    COUNT(DISTINCT ce.pmid) as with_extraction,
                    COUNT(DISTINCT ec.pmid) as with_enriched
                FROM universal_identifiers ui
                LEFT JOIN url_discovery ud ON ui.pmid = ud.pmid
                LEFT JOIN pdf_acquisition pa ON ui.pmid = pa.pmid
                LEFT JOIN content_extraction ce ON ui.pmid = ce.pmid
                LEFT JOIN enriched_content ec ON ui.pmid = ec.pmid
                WHERE ui.geo_id = ?
            """,
                (geo_id,),
            )
            row = cursor.fetchone()
            stats["publication_counts"] = {
                "total": row[0],
                "with_urls": row[1],
                "with_pdf": row[2],
                "with_extraction": row[3],
                "with_enriched": row[4],
            }

            # Completion rate
            if row[0] > 0:
                stats["completion_rate"] = round((row[4] / row[0]) * 100, 2)
            else:
                stats["completion_rate"] = 0.0

            # Quality distribution for this GEO
            cursor = conn.execute(
                """
                SELECT ce.extraction_grade, COUNT(*) as count
                FROM content_extraction ce
                JOIN universal_identifiers ui ON ce.pmid = ui.pmid
                WHERE ui.geo_id = ? AND ce.extraction_grade IS NOT NULL
                GROUP BY ce.extraction_grade
                ORDER BY ce.extraction_grade
            """,
                (geo_id,),
            )
            stats["quality_distribution"] = {row[0]: row[1] for row in cursor}

            # Average quality
            cursor = conn.execute(
                """
                SELECT AVG(ce.extraction_quality) as avg_quality
                FROM content_extraction ce
                JOIN universal_identifiers ui ON ce.pmid = ui.pmid
                WHERE ui.geo_id = ? AND ce.extraction_quality IS NOT NULL
            """,
                (geo_id,),
            )
            avg_quality = cursor.fetchone()[0]
            stats["average_quality"] = round(avg_quality, 3) if avg_quality else None

        logger.info(f"Generated statistics for GEO dataset {geo_id}")
        return stats

    def get_pipeline_performance(self, pipeline_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get performance metrics from processing logs.

        Args:
            pipeline_name: Filter by specific pipeline (P1, P2, P3, P4)

        Returns:
            Dictionary with performance statistics
        """
        query = """
            SELECT
                pipeline_name,
                COUNT(*) as total_operations,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful,
                SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failed,
                AVG(duration_seconds) as avg_duration,
                MIN(duration_seconds) as min_duration,
                MAX(duration_seconds) as max_duration
            FROM processing_log
        """

        params = []
        if pipeline_name:
            query += " WHERE pipeline_name = ?"
            params.append(pipeline_name)

        query += " GROUP BY pipeline_name ORDER BY pipeline_name"

        with self.db.get_connection() as conn:
            cursor = conn.execute(query, params)
            columns = [desc[0] for desc in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor]

        # Calculate success rates
        for result in results:
            if result["total_operations"] > 0:
                result["success_rate"] = round(
                    (result["successful"] / result["total_operations"]) * 100,
                    2,
                )
            else:
                result["success_rate"] = 0.0

            # Round duration values
            for key in ["avg_duration", "min_duration", "max_duration"]:
                if result[key] is not None:
                    result[key] = round(result[key], 3)

        logger.info(f"Retrieved performance metrics for " f"{pipeline_name or 'all pipelines'}")
        return {"pipelines": results}

    def get_recent_errors(self, limit: int = 50, pipeline_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get recent processing errors from logs.

        Args:
            limit: Maximum number of errors to return
            pipeline_name: Filter by specific pipeline

        Returns:
            List of error records
        """
        query = """
            SELECT
                pipeline,
                geo_id,
                pmid,
                message,
                error_type,
                logged_at
            FROM processing_log
            WHERE event_type = 'error'
        """

        params = []
        if pipeline_name:
            query += " AND pipeline = ?"
            params.append(pipeline_name)

        query += " ORDER BY logged_at DESC LIMIT ?"
        params.append(limit)

        with self.db.get_connection() as conn:
            cursor = conn.execute(query, params)
            columns = [desc[0] for desc in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor]

        logger.info(f"Retrieved {len(results)} recent errors for " f"{pipeline_name or 'all pipelines'}")
        return results

    # =========================================================================
    # DATABASE INTROSPECTION
    # =========================================================================

    def get_database_size(self) -> Dict[str, Any]:
        """
        Get database file size and statistics.

        Returns:
            Dictionary with size information
        """
        db_file = Path(self.db_path)

        if not db_file.exists():
            return {
                "exists": False,
                "size_bytes": 0,
                "size_mb": 0.0,
            }

        size_bytes = db_file.stat().st_size
        size_mb = size_bytes / 1024 / 1024

        # Get table sizes
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT name FROM sqlite_master
                WHERE type='table'
                ORDER BY name
            """
            )
            tables = [row[0] for row in cursor]

            table_sizes = {}
            for table in tables:
                cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                table_sizes[table] = cursor.fetchone()[0]

        return {
            "exists": True,
            "path": str(db_file),
            "size_bytes": size_bytes,
            "size_mb": round(size_mb, 2),
            "table_row_counts": table_sizes,
        }
