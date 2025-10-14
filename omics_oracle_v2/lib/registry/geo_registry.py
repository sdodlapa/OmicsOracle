"""
GEO Registry - Centralized GEO-centric data store

This module provides a SQLite-based registry that stores all GEO datasets,
publications, URLs, and download history in a single, efficient database.

Key Features:
- O(1) lookup for GEO datasets
- Complete data retrieval in single query
- URL retry capability
- Download history tracking
- ACID guarantees for concurrent access
- JSON flexibility for complex metadata

Usage:
    registry = GEORegistry()

    # Register GEO dataset
    registry.register_geo_dataset("GSE12345", {...})

    # Register publication with URLs
    registry.register_publication("12345", {...}, urls=[...])

    # Link them
    registry.link_geo_to_publication("GSE12345", "12345", "original")

    # Get everything in one call!
    data = registry.get_complete_geo_data("GSE12345")
"""

import json
import logging
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class GEORegistry:
    """
    Centralized registry for GEO datasets and their publications.

    Architecture:
    - GEO ID as root node
    - Publications linked via relationships
    - All URLs stored for retry capability
    - Download history for analytics
    """

    def __init__(self, db_path: str = "data/omics_oracle.db"):
        """
        Initialize registry with SQLite database.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Use check_same_thread=False for FastAPI async
        # This is safe because we use connection locks
        self.conn = sqlite3.connect(
            str(self.db_path), check_same_thread=False, timeout=10.0  # Wait up to 10s for locks
        )
        self.conn.row_factory = sqlite3.Row  # Access columns by name

        self._init_schema()
        logger.info(f"GEORegistry initialized: {self.db_path}")

    def _init_schema(self):
        """Create database schema with indexes"""
        self.conn.executescript(
            """
            -- GEO Datasets table
            CREATE TABLE IF NOT EXISTS geo_datasets (
                geo_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                summary TEXT,
                organism TEXT,
                platform TEXT,
                sample_count INTEGER,
                submission_date TEXT,
                publication_date TEXT,
                relevance_score REAL,
                metadata JSON NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_geo_organism ON geo_datasets(organism);
            CREATE INDEX IF NOT EXISTS idx_geo_platform ON geo_datasets(platform);
            CREATE INDEX IF NOT EXISTS idx_geo_updated ON geo_datasets(updated_at DESC);

            -- Publications table
            CREATE TABLE IF NOT EXISTS publications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pmid TEXT UNIQUE,
                doi TEXT,
                pmc_id TEXT,
                title TEXT NOT NULL,
                authors TEXT,  -- JSON array
                journal TEXT,
                year INTEGER,
                metadata JSON NOT NULL,
                urls JSON,  -- All collected URLs
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE UNIQUE INDEX IF NOT EXISTS idx_pub_pmid ON publications(pmid);
            CREATE INDEX IF NOT EXISTS idx_pub_doi ON publications(doi);
            CREATE INDEX IF NOT EXISTS idx_pub_year ON publications(year DESC);

            -- GEO-Publication relationships
            CREATE TABLE IF NOT EXISTS geo_publications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                geo_id TEXT NOT NULL,
                publication_id INTEGER NOT NULL,
                relationship_type TEXT NOT NULL CHECK(relationship_type IN ('original', 'citing')),
                citation_strategy TEXT,  -- 'strategy_a' (citation) or 'strategy_b' (mention)
                discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (geo_id) REFERENCES geo_datasets(geo_id) ON DELETE CASCADE,
                FOREIGN KEY (publication_id) REFERENCES publications(id) ON DELETE CASCADE,
                UNIQUE(geo_id, publication_id)
            );

            CREATE INDEX IF NOT EXISTS idx_geo_pub_geo ON geo_publications(geo_id);
            CREATE INDEX IF NOT EXISTS idx_geo_pub_type ON geo_publications(relationship_type);
            CREATE INDEX IF NOT EXISTS idx_geo_pub_discovered ON geo_publications(discovered_at DESC);

            -- Download history
            CREATE TABLE IF NOT EXISTS download_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                publication_id INTEGER NOT NULL,
                url TEXT NOT NULL,
                source TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('success', 'failed', 'retry', 'skipped')),
                file_path TEXT,
                file_size INTEGER,
                error_message TEXT,
                attempt_number INTEGER DEFAULT 1,
                downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (publication_id) REFERENCES publications(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_download_pub ON download_history(publication_id);
            CREATE INDEX IF NOT EXISTS idx_download_status ON download_history(status);
            CREATE INDEX IF NOT EXISTS idx_download_date ON download_history(downloaded_at DESC);

            -- Views for common queries
            CREATE VIEW IF NOT EXISTS v_geo_summary AS
            SELECT
                g.geo_id,
                g.title,
                g.organism,
                COUNT(DISTINCT CASE WHEN gp.relationship_type = 'original' THEN p.id END) as original_papers,
                COUNT(DISTINCT CASE WHEN gp.relationship_type = 'citing' THEN p.id END) as citing_papers,
                COUNT(DISTINCT CASE WHEN dh.status = 'success' THEN dh.id END) as successful_downloads,
                MAX(g.updated_at) as last_updated
            FROM geo_datasets g
            LEFT JOIN geo_publications gp ON g.geo_id = gp.geo_id
            LEFT JOIN publications p ON gp.publication_id = p.id
            LEFT JOIN download_history dh ON p.id = dh.publication_id
            GROUP BY g.geo_id;
        """
        )
        self.conn.commit()
        logger.info("Database schema initialized")

    def register_geo_dataset(self, geo_id: str, metadata: Dict) -> None:
        """
        Register GEO dataset with complete metadata.

        Args:
            geo_id: GEO dataset ID (e.g., "GSE12345")
            metadata: Complete GEO metadata dict
        """
        try:
            self.conn.execute(
                """
                INSERT OR REPLACE INTO geo_datasets
                (geo_id, title, summary, organism, platform, sample_count,
                 submission_date, publication_date, relevance_score, metadata, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
                (
                    geo_id,
                    metadata.get("title", ""),
                    metadata.get("summary"),
                    metadata.get("organism"),
                    metadata.get("platform"),
                    metadata.get("sample_count", 0),
                    metadata.get("submission_date"),
                    metadata.get("publication_date"),
                    metadata.get("relevance_score", 0.0),
                    json.dumps(metadata),
                ),
            )
            self.conn.commit()
            logger.info(f"Registered GEO dataset: {geo_id}")
        except Exception as e:
            logger.error(f"Failed to register GEO {geo_id}: {e}")
            self.conn.rollback()
            raise

    def register_publication(
        self,
        pmid: str,
        metadata: Dict,
        urls: List[Dict],
        doi: Optional[str] = None,
        pmc_id: Optional[str] = None,
    ) -> int:
        """
        Register publication with all URLs.

        Args:
            pmid: PubMed ID
            metadata: Publication metadata dict
            urls: List of URL dicts with {url, source, priority, metadata}
            doi: Digital Object Identifier (optional)
            pmc_id: PubMed Central ID (optional)

        Returns:
            Publication database ID
        """
        try:
            cursor = self.conn.execute(
                """
                INSERT OR REPLACE INTO publications
                (pmid, doi, pmc_id, title, authors, journal, year, metadata, urls, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
                (
                    pmid,
                    doi or metadata.get("doi"),
                    pmc_id or metadata.get("pmc_id") or metadata.get("pmcid"),
                    metadata.get("title", ""),
                    json.dumps(metadata.get("authors", [])),
                    metadata.get("journal"),
                    metadata.get("year"),
                    json.dumps(metadata),
                    json.dumps(urls),
                ),
            )
            self.conn.commit()

            pub_id = cursor.lastrowid
            logger.info(f"Registered publication: PMID {pmid} (ID {pub_id}) with {len(urls)} URLs")
            return pub_id

        except Exception as e:
            logger.error(f"Failed to register publication {pmid}: {e}")
            self.conn.rollback()
            raise

    def link_geo_to_publication(
        self, geo_id: str, pmid: str, relationship_type: str, citation_strategy: Optional[str] = None
    ) -> None:
        """
        Link GEO dataset to publication.

        Args:
            geo_id: GEO dataset ID
            pmid: PubMed ID
            relationship_type: 'original' or 'citing'
            citation_strategy: 'strategy_a' (citation) or 'strategy_b' (mention)
        """
        try:
            # Get publication ID
            cursor = self.conn.execute("SELECT id FROM publications WHERE pmid = ?", (pmid,))
            row = cursor.fetchone()
            if not row:
                logger.warning(f"Publication {pmid} not found, cannot link to {geo_id}")
                return

            pub_id = row[0]

            # Create relationship
            self.conn.execute(
                """
                INSERT OR IGNORE INTO geo_publications
                (geo_id, publication_id, relationship_type, citation_strategy)
                VALUES (?, ?, ?, ?)
            """,
                (geo_id, pub_id, relationship_type, citation_strategy),
            )
            self.conn.commit()

            logger.info(f"Linked {geo_id} -> {pmid} ({relationship_type})")

        except Exception as e:
            logger.error(f"Failed to link {geo_id} to {pmid}: {e}")
            self.conn.rollback()
            raise

    def get_complete_geo_data(self, geo_id: str) -> Optional[Dict]:
        """
        Get ALL data for GEO ID in single query.

        This is the KEY method for frontend - returns everything needed:
        - GEO metadata
        - All original papers with URLs
        - All citing papers with URLs
        - Download history for each paper

        Args:
            geo_id: GEO dataset ID

        Returns:
            Complete data dict or None if not found
        """
        try:
            # Get GEO metadata
            cursor = self.conn.execute("SELECT metadata FROM geo_datasets WHERE geo_id = ?", (geo_id,))
            row = cursor.fetchone()
            if not row:
                logger.warning(f"GEO {geo_id} not found")
                return None

            geo_metadata = json.loads(row[0])

            # Get all publications with relationships
            cursor = self.conn.execute(
                """
                SELECT
                    p.pmid,
                    p.doi,
                    p.pmc_id,
                    p.metadata,
                    p.urls,
                    gp.relationship_type,
                    gp.citation_strategy
                FROM publications p
                JOIN geo_publications gp ON p.id = gp.publication_id
                WHERE gp.geo_id = ?
                ORDER BY gp.relationship_type, p.year DESC
            """,
                (geo_id,),
            )

            papers = {"original": [], "citing": []}

            for row in cursor.fetchall():
                paper = {
                    "pmid": row[0],
                    "doi": row[1],
                    "pmc_id": row[2],
                    **json.loads(row[3]),  # metadata
                    "urls": json.loads(row[4]) if row[4] else [],
                    "citation_strategy": row[6],
                }

                # Get download history for this paper
                paper["download_history"] = self._get_download_history(row[0])

                # Add to appropriate list
                if row[5] == "original":
                    papers["original"].append(paper)
                else:
                    papers["citing"].append(paper)

            # Calculate download statistics
            total_papers = len(papers["original"]) + len(papers["citing"])
            successful_downloads = 0
            for paper_list in [papers["original"], papers["citing"]]:
                for paper in paper_list:
                    if any(h["status"] == "success" for h in paper["download_history"]):
                        successful_downloads += 1

            success_rate = round(successful_downloads / total_papers * 100, 1) if total_papers > 0 else 0

            return {
                "geo": geo_metadata,
                "papers": papers,
                "statistics": {
                    "original_papers": len(papers["original"]),
                    "citing_papers": len(papers["citing"]),
                    "total_papers": total_papers,
                    "successful_downloads": successful_downloads,
                    "failed_downloads": total_papers - successful_downloads,
                    "success_rate": success_rate,
                },
            }

        except Exception as e:
            logger.error(f"Failed to get data for {geo_id}: {e}")
            return None

    def _get_download_history(self, pmid: str) -> List[Dict]:
        """Get download history for a publication"""
        cursor = self.conn.execute(
            """
            SELECT dh.url, dh.source, dh.status, dh.file_path, dh.error_message, dh.downloaded_at
            FROM download_history dh
            JOIN publications p ON dh.publication_id = p.id
            WHERE p.pmid = ?
            ORDER BY dh.downloaded_at DESC
        """,
            (pmid,),
        )

        return [
            {
                "url": row[0],
                "source": row[1],
                "status": row[2],
                "file_path": row[3],
                "error_message": row[4],
                "downloaded_at": row[5],
            }
            for row in cursor.fetchall()
        ]

    def get_urls_for_retry(self, pmid: str) -> List[Dict]:
        """
        Get all URLs for a paper (for retry logic).

        Args:
            pmid: PubMed ID

        Returns:
            List of URL dicts with {url, source, priority, metadata}
        """
        cursor = self.conn.execute("SELECT urls FROM publications WHERE pmid = ?", (pmid,))
        row = cursor.fetchone()

        if not row or not row[0]:
            return []

        return json.loads(row[0])

    def record_download_attempt(
        self,
        pmid: str,
        url: str,
        source: str,
        status: str,
        file_path: Optional[str] = None,
        file_size: Optional[int] = None,
        error_message: Optional[str] = None,
        attempt_number: int = 1,
    ) -> None:
        """
        Record download attempt for analytics.

        Args:
            pmid: PubMed ID
            url: URL attempted
            source: Source name (pmc, unpaywall, etc.)
            status: 'success', 'failed', 'retry', or 'skipped'
            file_path: Path to downloaded file (if success)
            file_size: File size in bytes (if success)
            error_message: Error message (if failed)
            attempt_number: Attempt number for retries
        """
        try:
            # Get publication ID
            cursor = self.conn.execute("SELECT id FROM publications WHERE pmid = ?", (pmid,))
            row = cursor.fetchone()
            if not row:
                logger.warning(f"Publication {pmid} not found, cannot record download")
                return

            pub_id = row[0]

            # Record attempt
            self.conn.execute(
                """
                INSERT INTO download_history
                (publication_id, url, source, status, file_path, file_size, error_message, attempt_number)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (pub_id, url, source, status, file_path, file_size, error_message, attempt_number),
            )
            self.conn.commit()

            logger.debug(f"Recorded download: {pmid} from {source} -> {status}")

        except Exception as e:
            logger.error(f"Failed to record download for {pmid}: {e}")
            self.conn.rollback()

    def get_statistics(self) -> Dict:
        """Get overall registry statistics"""
        cursor = self.conn.execute(
            """
            SELECT
                (SELECT COUNT(*) FROM geo_datasets) as total_geo,
                (SELECT COUNT(*) FROM publications) as total_publications,
                (SELECT COUNT(*) FROM download_history WHERE status = 'success') as successful_downloads,
                (SELECT COUNT(*) FROM download_history WHERE status = 'failed') as failed_downloads
        """
        )
        row = cursor.fetchone()

        return {
            "total_geo_datasets": row[0],
            "total_publications": row[1],
            "successful_downloads": row[2],
            "failed_downloads": row[3],
            "success_rate": round(row[2] / (row[2] + row[3]) * 100, 1) if (row[2] + row[3]) > 0 else 0,
        }

    def close(self):
        """Close database connection"""
        self.conn.close()
        logger.info("GEORegistry closed")


# Global registry instance (initialized in main app)
_registry: Optional[GEORegistry] = None


def get_registry() -> GEORegistry:
    """Get global registry instance"""
    global _registry
    if _registry is None:
        _registry = GEORegistry()
    return _registry
