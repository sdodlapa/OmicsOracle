"""
Unified Database Manager

GEO-centric SQLite database for all OmicsOracle data.
Provides transaction support, CRUD operations, and type-safe interfaces.
"""

import logging
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import (
    CacheMetadata,
    ContentExtraction,
    EnrichedContent,
    GEODataset,
    PDFAcquisition,
    ProcessingLog,
    UniversalIdentifier,
    URLDiscovery,
    expires_at_iso,
    now_iso,
)

logger = logging.getLogger(__name__)


class UnifiedDatabase:
    """
    Unified GEO-centric database manager.

    Features:
    - Connection pooling with context manager
    - Transaction support (atomic operations)
    - Type-safe CRUD operations
    - Automatic schema initialization
    - Foreign key constraint enforcement

    Example:
        db = UnifiedDatabase("data/database/omics_oracle.db")

        # Insert publication
        pub = UniversalIdentifier(
            geo_id="GSE12345",
            pmid="12345678",
            title="Example Paper"
        )
        db.insert_universal_identifier(pub)

        # Query by GEO
        pubs = db.get_publications_by_geo("GSE12345")
    """

    def __init__(self, db_path: str | Path):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file (will be created if not exists)
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize schema
        self._initialize_schema()

        logger.info(f"Initialized UnifiedDatabase at {self.db_path}")

    @contextmanager
    def _get_connection(self):
        """
        Get database connection with automatic cleanup (private).

        Yields:
            sqlite3.Connection: Database connection
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row  # Enable dict-like row access
        conn.execute("PRAGMA foreign_keys = ON")  # Enforce foreign keys
        try:
            yield conn
        finally:
            conn.close()

    @contextmanager
    def get_connection(self):
        """
        Get database connection with automatic cleanup (public API).

        Yields:
            sqlite3.Connection: Database connection
        """
        with self._get_connection() as conn:
            yield conn

    @contextmanager
    def transaction(self):
        """
        Transaction context manager with automatic commit/rollback.

        Example:
            with db.transaction() as conn:
                db.insert_universal_identifier(pub1)
                db.insert_universal_identifier(pub2)
                # Both commits together or both rollback on error

        Yields:
            sqlite3.Connection: Database connection in transaction
        """
        with self._get_connection() as conn:
            try:
                yield conn
                conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error(f"Transaction rolled back: {e}")
                raise

    def _initialize_schema(self):
        """
        Initialize database schema from schema.sql.
        
        Raises:
            FileNotFoundError: If schema.sql not found
            sqlite3.Error: If schema execution fails
        """
        schema_path = Path(__file__).parent / "schema.sql"
        
        if not schema_path.exists():
            error_msg = f"CRITICAL: Schema file not found at {schema_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        try:
            with open(schema_path) as f:
                schema_sql = f.read()
            
            logger.info(f"Initializing database schema from {schema_path}")
            
            with self._get_connection() as conn:
                conn.executescript(schema_sql)
                conn.commit()

            logger.info("✅ Database schema initialized successfully")
            
        except sqlite3.Error as e:
            error_msg = f"CRITICAL: Failed to initialize database schema: {e}"
            logger.error(error_msg, exc_info=True)
            raise RuntimeError(error_msg) from e
        except Exception as e:
            error_msg = f"CRITICAL: Unexpected error during schema initialization: {e}"
            logger.error(error_msg, exc_info=True)
            raise

    # =========================================================================
    # UNIVERSAL IDENTIFIERS - Central Hub
    # =========================================================================

    def insert_universal_identifier(
        self, identifier: UniversalIdentifier, conn: Optional[sqlite3.Connection] = None
    ) -> None:
        """
        Insert or update universal identifier.

        Args:
            identifier: UniversalIdentifier object
            conn: Optional connection (for transactions)
        """
        now = now_iso()
        if not identifier.first_discovered_at:
            identifier.first_discovered_at = now
        identifier.last_updated_at = now

        sql = """
            INSERT INTO universal_identifiers (
                geo_id, pmid, doi, pmc_id, arxiv_id,
                title, authors, journal, publication_year, publication_date,
                first_discovered_at, last_updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(geo_id, pmid) DO UPDATE SET
                doi = COALESCE(excluded.doi, doi),
                pmc_id = COALESCE(excluded.pmc_id, pmc_id),
                arxiv_id = COALESCE(excluded.arxiv_id, arxiv_id),
                title = COALESCE(excluded.title, title),
                authors = COALESCE(excluded.authors, authors),
                journal = COALESCE(excluded.journal, journal),
                publication_year = COALESCE(excluded.publication_year, publication_year),
                publication_date = COALESCE(excluded.publication_date, publication_date),
                last_updated_at = excluded.last_updated_at
        """

        values = (
            identifier.geo_id,
            identifier.pmid,
            identifier.doi,
            identifier.pmc_id,
            identifier.arxiv_id,
            identifier.title,
            identifier.authors,
            identifier.journal,
            identifier.publication_year,
            identifier.publication_date,
            identifier.first_discovered_at,
            identifier.last_updated_at,
        )

        if conn:
            conn.execute(sql, values)
        else:
            with self._get_connection() as conn:
                conn.execute(sql, values)
                conn.commit()

    def get_universal_identifier(self, geo_id: str, pmid: str) -> Optional[UniversalIdentifier]:
        """
        Get universal identifier by GEO ID and PMID.

        Args:
            geo_id: GEO dataset ID
            pmid: PubMed ID

        Returns:
            UniversalIdentifier object or None
        """
        sql = "SELECT * FROM universal_identifiers WHERE geo_id = ? AND pmid = ?"

        with self._get_connection() as conn:
            row = conn.execute(sql, (geo_id, pmid)).fetchone()

        if row:
            return UniversalIdentifier(**dict(row))
        return None

    def get_publications_by_geo(self, geo_id: str) -> List[UniversalIdentifier]:
        """
        Get all publications for a GEO dataset.

        Args:
            geo_id: GEO dataset ID

        Returns:
            List of UniversalIdentifier objects
        """
        sql = "SELECT * FROM universal_identifiers WHERE geo_id = ? ORDER BY pmid"

        with self._get_connection() as conn:
            rows = conn.execute(sql, (geo_id,)).fetchall()

        return [UniversalIdentifier(**dict(row)) for row in rows]

    # =========================================================================
    # GEO DATASETS
    # =========================================================================

    def insert_geo_dataset(self, dataset: GEODataset, conn: Optional[sqlite3.Connection] = None) -> None:
        """Insert or update GEO dataset."""
        now = now_iso()
        if not dataset.created_at:
            dataset.created_at = now
        dataset.last_processed_at = now

        sql = """
            INSERT INTO geo_datasets (
                geo_id, title, summary, organism, platform,
                publication_count, pdfs_downloaded, pdfs_extracted, avg_extraction_quality,
                created_at, last_processed_at, status, error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(geo_id) DO UPDATE SET
                title = COALESCE(excluded.title, title),
                summary = COALESCE(excluded.summary, summary),
                organism = COALESCE(excluded.organism, organism),
                platform = COALESCE(excluded.platform, platform),
                publication_count = excluded.publication_count,
                pdfs_downloaded = excluded.pdfs_downloaded,
                pdfs_extracted = excluded.pdfs_extracted,
                avg_extraction_quality = excluded.avg_extraction_quality,
                last_processed_at = excluded.last_processed_at,
                status = excluded.status,
                error_message = excluded.error_message
        """

        values = (
            dataset.geo_id,
            dataset.title,
            dataset.summary,
            dataset.organism,
            dataset.platform,
            dataset.publication_count,
            dataset.pdfs_downloaded,
            dataset.pdfs_extracted,
            dataset.avg_extraction_quality,
            dataset.created_at,
            dataset.last_processed_at,
            dataset.status,
            dataset.error_message,
        )

        if conn:
            conn.execute(sql, values)
        else:
            with self._get_connection() as conn:
                conn.execute(sql, values)
                conn.commit()

    def get_geo_dataset(self, geo_id: str) -> Optional[GEODataset]:
        """Get GEO dataset by ID."""
        sql = "SELECT * FROM geo_datasets WHERE geo_id = ?"

        with self._get_connection() as conn:
            row = conn.execute(sql, (geo_id,)).fetchone()

        if row:
            return GEODataset(**dict(row))
        return None

    # =========================================================================
    # URL DISCOVERY (Pipeline 2)
    # =========================================================================

    def insert_url_discovery(self, discovery: URLDiscovery, conn: Optional[sqlite3.Connection] = None) -> int:
        """Insert URL discovery results. Returns row ID."""
        if not discovery.discovered_at:
            discovery.discovered_at = now_iso()

        sql = """
            INSERT INTO url_discovery (
                geo_id, pmid, urls_json, sources_queried, url_count,
                pubmed_urls, unpaywall_urls, europepmc_urls, other_urls,
                has_pdf_url, has_html_url, best_url_type, discovered_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        values = (
            discovery.geo_id,
            discovery.pmid,
            discovery.urls_json,
            discovery.sources_queried,
            discovery.url_count,
            discovery.pubmed_urls,
            discovery.unpaywall_urls,
            discovery.europepmc_urls,
            discovery.other_urls,
            discovery.has_pdf_url,
            discovery.has_html_url,
            discovery.best_url_type,
            discovery.discovered_at,
        )

        if conn:
            cursor = conn.execute(sql, values)
            return cursor.lastrowid
        else:
            with self._get_connection() as conn:
                cursor = conn.execute(sql, values)
                conn.commit()
                return cursor.lastrowid

    def get_url_discovery(self, geo_id: str, pmid: str) -> Optional[URLDiscovery]:
        """Get URL discovery results for a publication."""
        sql = """
            SELECT * FROM url_discovery
            WHERE geo_id = ? AND pmid = ?
            ORDER BY discovered_at DESC LIMIT 1
        """

        with self._get_connection() as conn:
            row = conn.execute(sql, (geo_id, pmid)).fetchone()

        if row:
            return URLDiscovery(**dict(row))
        return None

    # =========================================================================
    # PDF ACQUISITION (Pipeline 3)
    # =========================================================================

    def insert_pdf_acquisition(
        self, acquisition: PDFAcquisition, conn: Optional[sqlite3.Connection] = None
    ) -> int:
        """Insert PDF acquisition record. Returns row ID."""
        if not acquisition.downloaded_at:
            acquisition.downloaded_at = now_iso()

        sql = """
            INSERT INTO pdf_acquisition (
                geo_id, pmid, pdf_path, pdf_hash_sha256, pdf_size_bytes,
                source_url, source_type, download_method, status, error_message,
                downloaded_at, verified_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        values = (
            acquisition.geo_id,
            acquisition.pmid,
            acquisition.pdf_path,
            acquisition.pdf_hash_sha256,
            acquisition.pdf_size_bytes,
            acquisition.source_url,
            acquisition.source_type,
            acquisition.download_method,
            acquisition.status,
            acquisition.error_message,
            acquisition.downloaded_at,
            acquisition.verified_at,
        )

        if conn:
            cursor = conn.execute(sql, values)
            return cursor.lastrowid
        else:
            with self._get_connection() as conn:
                cursor = conn.execute(sql, values)
                conn.commit()
                return cursor.lastrowid

    def get_pdf_acquisition(self, geo_id: str, pmid: str) -> Optional[PDFAcquisition]:
        """Get PDF acquisition record for a publication."""
        sql = """
            SELECT * FROM pdf_acquisition
            WHERE geo_id = ? AND pmid = ?
            ORDER BY downloaded_at DESC LIMIT 1
        """

        with self._get_connection() as conn:
            row = conn.execute(sql, (geo_id, pmid)).fetchone()

        if row:
            return PDFAcquisition(**dict(row))
        return None

    # =========================================================================
    # CONTENT EXTRACTION (Pipeline 4 Basic)
    # =========================================================================

    def insert_content_extraction(
        self, extraction: ContentExtraction, conn: Optional[sqlite3.Connection] = None
    ) -> int:
        """Insert content extraction record. Returns row ID."""
        if not extraction.extracted_at:
            extraction.extracted_at = now_iso()

        sql = """
            INSERT INTO content_extraction (
                geo_id, pmid, full_text, page_count, word_count, char_count,
                extractor_used, extraction_method, extraction_quality, extraction_grade,
                has_readable_text, needs_ocr, extracted_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        values = (
            extraction.geo_id,
            extraction.pmid,
            extraction.full_text,
            extraction.page_count,
            extraction.word_count,
            extraction.char_count,
            extraction.extractor_used,
            extraction.extraction_method,
            extraction.extraction_quality,
            extraction.extraction_grade,
            extraction.has_readable_text,
            extraction.needs_ocr,
            extraction.extracted_at,
        )

        if conn:
            cursor = conn.execute(sql, values)
            return cursor.lastrowid
        else:
            with self._get_connection() as conn:
                cursor = conn.execute(sql, values)
                conn.commit()
                return cursor.lastrowid

    def get_content_extraction(self, geo_id: str, pmid: str) -> Optional[ContentExtraction]:
        """Get content extraction record for a publication."""
        sql = """
            SELECT * FROM content_extraction
            WHERE geo_id = ? AND pmid = ?
            ORDER BY extracted_at DESC LIMIT 1
        """

        with self._get_connection() as conn:
            row = conn.execute(sql, (geo_id, pmid)).fetchone()

        if row:
            return ContentExtraction(**dict(row))
        return None

    # =========================================================================
    # ENRICHED CONTENT (Pipeline 4 Advanced)
    # =========================================================================

    def insert_enriched_content(
        self, enriched: EnrichedContent, conn: Optional[sqlite3.Connection] = None
    ) -> int:
        """Insert enriched content record. Returns row ID."""
        if not enriched.enriched_at:
            enriched.enriched_at = now_iso()

        sql = """
            INSERT INTO enriched_content (
                geo_id, pmid, sections_json, tables_json, references_json, figures_json,
                chatgpt_prompt, chatgpt_metadata, grobid_xml, grobid_tei_json,
                enrichers_applied, enrichment_quality, enriched_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        values = (
            enriched.geo_id,
            enriched.pmid,
            enriched.sections_json,
            enriched.tables_json,
            enriched.references_json,
            enriched.figures_json,
            enriched.chatgpt_prompt,
            enriched.chatgpt_metadata,
            enriched.grobid_xml,
            enriched.grobid_tei_json,
            enriched.enrichers_applied,
            enriched.enrichment_quality,
            enriched.enriched_at,
        )

        if conn:
            cursor = conn.execute(sql, values)
            return cursor.lastrowid
        else:
            with self._get_connection() as conn:
                cursor = conn.execute(sql, values)
                conn.commit()
                return cursor.lastrowid

    def get_enriched_content(self, geo_id: str, pmid: str) -> Optional[EnrichedContent]:
        """Get enriched content record for a publication."""
        sql = """
            SELECT * FROM enriched_content
            WHERE geo_id = ? AND pmid = ?
            ORDER BY enriched_at DESC LIMIT 1
        """

        with self._get_connection() as conn:
            row = conn.execute(sql, (geo_id, pmid)).fetchone()

        if row:
            return EnrichedContent(**dict(row))
        return None

    # =========================================================================
    # PROCESSING LOG
    # =========================================================================

    def log_event(
        self,
        geo_id: str,
        pipeline: str,
        event_type: str,
        pmid: Optional[str] = None,
        message: Optional[str] = None,
        duration_ms: Optional[int] = None,
        error_type: Optional[str] = None,
        error_traceback: Optional[str] = None,
        conn: Optional[sqlite3.Connection] = None,
    ) -> int:
        """
        Log a processing event.

        Args:
            geo_id: GEO dataset ID
            pipeline: 'P1', 'P2', 'P3', 'P4', 'system'
            event_type: 'start', 'success', 'error', 'retry', 'skip'
            pmid: Optional PMID
            message: Optional message
            duration_ms: Optional duration in milliseconds
            error_type: Optional error type
            error_traceback: Optional error traceback
            conn: Optional connection (for transactions)

        Returns:
            Row ID of log entry
        """
        sql = """
            INSERT INTO processing_log (
                geo_id, pmid, pipeline, event_type, message,
                duration_ms, error_type, error_traceback, logged_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        values = (
            geo_id,
            pmid,
            pipeline,
            event_type,
            message,
            duration_ms,
            error_type,
            error_traceback,
            now_iso(),
        )

        if conn:
            cursor = conn.execute(sql, values)
            return cursor.lastrowid
        else:
            with self._get_connection() as conn:
                cursor = conn.execute(sql, values)
                conn.commit()
                return cursor.lastrowid

    def get_processing_logs(
        self,
        geo_id: Optional[str] = None,
        pipeline: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[ProcessingLog]:
        """
        Get processing logs with optional filters.

        Args:
            geo_id: Filter by GEO ID
            pipeline: Filter by pipeline
            event_type: Filter by event type
            limit: Maximum number of logs

        Returns:
            List of ProcessingLog objects
        """
        conditions = []
        values = []

        if geo_id:
            conditions.append("geo_id = ?")
            values.append(geo_id)
        if pipeline:
            conditions.append("pipeline = ?")
            values.append(pipeline)
        if event_type:
            conditions.append("event_type = ?")
            values.append(event_type)

        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
        sql = f"""
            SELECT * FROM processing_log
            {where_clause}
            ORDER BY logged_at DESC LIMIT ?
        """
        values.append(limit)

        with self._get_connection() as conn:
            rows = conn.execute(sql, tuple(values)).fetchall()

        return [ProcessingLog(**dict(row)) for row in rows]

    # =========================================================================
    # CACHE METADATA
    # =========================================================================

    def insert_cache_metadata(self, cache: CacheMetadata, conn: Optional[sqlite3.Connection] = None) -> int:
        """Insert cache metadata record. Returns row ID."""
        now = now_iso()
        if not cache.created_at:
            cache.created_at = now
        if not cache.updated_at:
            cache.updated_at = now
        if not cache.expires_at:
            cache.expires_at = expires_at_iso(cache.ttl_days)

        sql = """
            INSERT INTO cache_metadata (
                cache_key, cache_type, geo_id, pmid,
                file_path, file_size_bytes, file_hash_sha256,
                ttl_days, expires_at, is_valid, last_accessed_at,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(cache_key) DO UPDATE SET
                updated_at = excluded.updated_at,
                last_accessed_at = excluded.last_accessed_at,
                is_valid = excluded.is_valid
        """

        values = (
            cache.cache_key,
            cache.cache_type,
            cache.geo_id,
            cache.pmid,
            cache.file_path,
            cache.file_size_bytes,
            cache.file_hash_sha256,
            cache.ttl_days,
            cache.expires_at,
            cache.is_valid,
            cache.last_accessed_at,
            cache.created_at,
            cache.updated_at,
        )

        if conn:
            cursor = conn.execute(sql, values)
            return cursor.lastrowid
        else:
            with self._get_connection() as conn:
                cursor = conn.execute(sql, values)
                conn.commit()
                return cursor.lastrowid

    def get_cache_metadata(self, cache_key: str) -> Optional[CacheMetadata]:
        """Get cache metadata by key."""
        sql = "SELECT * FROM cache_metadata WHERE cache_key = ?"

        with self._get_connection() as conn:
            row = conn.execute(sql, (cache_key,)).fetchone()

        if row:
            return CacheMetadata(**dict(row))
        return None

    # =========================================================================
    # STATISTICS & ANALYTICS
    # =========================================================================

    def get_geo_statistics(self, geo_id: str) -> Dict[str, Any]:
        """
        Get comprehensive statistics for a GEO dataset.

        Returns:
            Dictionary with publication counts, quality metrics, etc.
        """
        sql = "SELECT * FROM v_geo_statistics WHERE geo_id = ?"

        with self._get_connection() as conn:
            row = conn.execute(sql, (geo_id,)).fetchone()

        if row:
            return dict(row)
        return {}

    def get_database_statistics(self) -> Dict[str, Any]:
        """Get overall database statistics."""
        with self._get_connection() as conn:
            stats = {
                "total_publications": conn.execute("SELECT COUNT(*) FROM universal_identifiers").fetchone()[
                    0
                ],
                "total_geo_datasets": conn.execute("SELECT COUNT(*) FROM geo_datasets").fetchone()[0],
                "pdfs_downloaded": conn.execute(
                    "SELECT COUNT(*) FROM pdf_acquisition WHERE status = 'downloaded'"
                ).fetchone()[0],
                "content_extracted": conn.execute("SELECT COUNT(*) FROM content_extraction").fetchone()[0],
                "enriched_papers": conn.execute("SELECT COUNT(*) FROM enriched_content").fetchone()[0],
                "high_quality_papers": conn.execute(
                    "SELECT COUNT(*) FROM content_extraction WHERE extraction_grade IN ('A', 'B')"
                ).fetchone()[0],
            }

        return stats

    def get_complete_geo_data(self, geo_id: str) -> Optional[Dict[str, Any]]:
        """
        Get complete GEO dataset metadata in single query (warm-tier for GEOCache).
        
        This method aggregates all GEO-centric data from UnifiedDatabase:
        - GEO dataset metadata (geo_datasets table)
        - All publications linked to this GEO (universal_identifiers)
        - PDF acquisition history for each publication
        - Content extraction results
        - Statistics and quality metrics
        
        Args:
            geo_id: GEO accession ID (e.g., "GSE123456")
        
        Returns:
            Complete GEO data dict with structure:
            {
                "geo": {...},  # GEO dataset metadata
                "papers": {
                    "original": [...],  # Publications with URLs
                    "citing": []  # Future: citing papers
                },
                "statistics": {...}  # Counts and quality metrics
            }
            Or None if GEO not found
        
        Example:
            >>> data = db.get_complete_geo_data("GSE123456")
            >>> print(data["geo"]["title"])
            >>> print(len(data["papers"]["original"]))
        """
        with self._get_connection() as conn:
            # Get GEO dataset metadata
            geo_row = conn.execute(
                "SELECT * FROM geo_datasets WHERE geo_id = ?",
                (geo_id,)
            ).fetchone()
            
            if not geo_row:
                logger.debug(f"GEO dataset not found: {geo_id}")
                return None
            
            geo_data = dict(geo_row)
            
            # Get all publications for this GEO
            pub_rows = conn.execute(
                """
                SELECT *
                FROM universal_identifiers
                WHERE geo_id = ?
                ORDER BY pmid
                """,
                (geo_id,)
            ).fetchall()
            
            papers = []
            for pub_row in pub_rows:
                pub_dict = dict(pub_row)
                
                # Get PDF acquisition history
                pdf_rows = conn.execute(
                    """
                    SELECT status, pdf_path, pdf_size_bytes, downloaded_at, error_message
                    FROM pdf_acquisition
                    WHERE geo_id = ? AND pmid = ?
                    ORDER BY downloaded_at DESC
                    """,
                    (geo_id, pub_dict.get("pmid"))
                ).fetchall()
                
                pub_dict["download_history"] = [dict(row) for row in pdf_rows]
                
                # Get content extraction if exists
                extraction_row = conn.execute(
                    """
                    SELECT extraction_grade, extraction_quality, extraction_method, extracted_at
                    FROM content_extraction
                    WHERE geo_id = ? AND pmid = ?
                    ORDER BY extracted_at DESC
                    LIMIT 1
                    """,
                    (geo_id, pub_dict.get("pmid"))
                ).fetchone()
                
                if extraction_row:
                    pub_dict["extraction"] = dict(extraction_row)
                
                papers.append(pub_dict)
            
            # Calculate statistics
            total_papers = len(papers)
            successful_downloads = sum(
                1 for p in papers
                if any(h["status"] == "downloaded" for h in p.get("download_history", []))
            )
            extracted_papers = sum(
                1 for p in papers
                if p.get("extraction") is not None
            )
            
            success_rate = (
                round(successful_downloads / total_papers * 100, 1)
                if total_papers > 0
                else 0
            )
            
            return {
                "geo": geo_data,
                "papers": {
                    "original": papers,  # All papers from universal_identifiers are "original"
                    "citing": []  # Future: implement citation discovery
                },
                "statistics": {
                    "original_papers": total_papers,
                    "citing_papers": 0,
                    "total_papers": total_papers,
                    "successful_downloads": successful_downloads,
                    "failed_downloads": total_papers - successful_downloads,
                    "extracted_papers": extracted_papers,
                    "success_rate": success_rate,
                }
            }
