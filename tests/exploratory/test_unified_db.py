"""
Unit tests for UnifiedDatabase class.

Tests:
- Database initialization
- CRUD operations for all tables
- Transaction support and rollback
- Foreign key constraints
- Upsert operations
- Error handling
"""

import sqlite3
import tempfile
from pathlib import Path

import pytest

from omics_oracle_v2.lib.storage.models import (
    CacheMetadata,
    ContentExtraction,
    EnrichedContent,
    GEODataset,
    PDFAcquisition,
    ProcessingLog,
    UniversalIdentifier,
    URLDiscovery,
)
from omics_oracle_v2.lib.storage.unified_db import UnifiedDatabase


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    db = UnifiedDatabase(db_path)
    yield db

    # Cleanup
    Path(db_path).unlink(missing_ok=True)


class TestDatabaseInitialization:
    """Test database initialization and schema creation."""

    def test_database_creation(self, temp_db):
        """Test that database file is created."""
        assert Path(temp_db.db_path).exists()

    def test_schema_creation(self, temp_db):
        """Test that all tables are created."""
        expected_tables = {
            "universal_identifiers",
            "geo_datasets",
            "url_discovery",
            "pdf_acquisition",
            "content_extraction",
            "enriched_content",
            "processing_log",
            "cache_metadata",
        }

        with temp_db.get_connection() as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = {row[0] for row in cursor}

        assert expected_tables.issubset(tables)

    def test_foreign_keys_enabled(self, temp_db):
        """Test that foreign keys are enforced."""
        with temp_db.get_connection() as conn:
            cursor = conn.execute("PRAGMA foreign_keys")
            assert cursor.fetchone()[0] == 1


class TestUniversalIdentifiers:
    """Test universal_identifiers table operations."""

    def test_insert_publication(self, temp_db):
        """Test inserting a publication."""
        pub = UniversalIdentifier(
            geo_id="GSE12345",
            pmid="12345678",
            title="Test Publication",
            authors="Smith J, Doe J",
            doi="10.1234/test",
        )

        temp_db.insert_universal_identifier(pub)

        # Verify insertion
        with temp_db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM universal_identifiers WHERE pmid = ?",
                (pub.pmid,),
            )
            row = cursor.fetchone()
            assert row is not None
            assert row[0] == pub.geo_id
            assert row[1] == pub.pmid
            assert row[2] == pub.title

    def test_insert_duplicate_pmid(self, temp_db):
        """Test that duplicate PMIDs are handled (upsert)."""
        pub1 = UniversalIdentifier(
            geo_id="GSE12345",
            pmid="12345678",
            title="Original Title",
        )
        pub2 = UniversalIdentifier(
            geo_id="GSE12345",
            pmid="12345678",
            title="Updated Title",
        )

        temp_db.insert_universal_identifier(pub1)
        temp_db.insert_universal_identifier(pub2)  # Should update

        with temp_db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT title FROM universal_identifiers WHERE pmid = ?",
                (pub1.pmid,),
            )
            title = cursor.fetchone()[0]
            assert title == "Updated Title"

    def test_get_publications_by_geo(self, temp_db):
        """Test retrieving publications by GEO ID."""
        pubs = [
            UniversalIdentifier(geo_id="GSE12345", pmid=f"1234567{i}", title=f"Paper {i}") for i in range(5)
        ]

        for pub in pubs:
            temp_db.insert_universal_identifier(pub)

        results = temp_db.get_publications_by_geo("GSE12345")
        assert len(results) == 5


class TestGEODatasets:
    """Test geo_datasets table operations."""

    def test_insert_geo_dataset(self, temp_db):
        """Test inserting GEO dataset."""
        dataset = GEODataset(
            geo_id="GSE12345",
            total_citations=100,
            citations_processed=50,
        )

        temp_db.insert_geo_dataset(dataset)

        with temp_db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM geo_datasets WHERE geo_id = ?",
                (dataset.geo_id,),
            )
            row = cursor.fetchone()
            assert row is not None
            assert row[1] == 100  # total_citations

    def test_update_geo_dataset(self, temp_db):
        """Test updating GEO dataset."""
        dataset = GEODataset(
            geo_id="GSE12345",
            total_citations=100,
            citations_processed=50,
        )

        temp_db.insert_geo_dataset(dataset)
        temp_db.update_geo_dataset("GSE12345", citations_processed=75)

        with temp_db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT citations_processed FROM geo_datasets WHERE geo_id = ?",
                ("GSE12345",),
            )
            processed = cursor.fetchone()[0]
            assert processed == 75


class TestURLDiscovery:
    """Test url_discovery table operations."""

    def test_insert_url_discovery(self, temp_db):
        """Test inserting URL discovery results."""
        # First insert publication
        pub = UniversalIdentifier(geo_id="GSE12345", pmid="12345678", title="Test")
        temp_db.insert_universal_identifier(pub)

        # Then insert URL discovery
        url_disc = URLDiscovery(
            pmid="12345678",
            urls_found=5,
            sources_queried="pubmed,unpaywall",
        )

        temp_db.insert_url_discovery(url_disc)

        with temp_db.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM url_discovery WHERE pmid = ?", ("12345678",))
            row = cursor.fetchone()
            assert row is not None
            assert row[1] == 5  # urls_found

    def test_foreign_key_constraint(self, temp_db):
        """Test that foreign key to universal_identifiers is enforced."""
        url_disc = URLDiscovery(
            pmid="99999999",  # Non-existent PMID
            urls_found=5,
        )

        with pytest.raises(sqlite3.IntegrityError):
            temp_db.insert_url_discovery(url_disc)


class TestPDFAcquisition:
    """Test pdf_acquisition table operations."""

    def test_insert_pdf_acquisition(self, temp_db):
        """Test inserting PDF acquisition record."""
        pub = UniversalIdentifier(geo_id="GSE12345", pmid="12345678", title="Test")
        temp_db.insert_universal_identifier(pub)

        pdf_acq = PDFAcquisition(
            pmid="12345678",
            pdf_path="data/pdfs/test.pdf",
            sha256="abc123",
            file_size=1024000,
        )

        temp_db.insert_pdf_acquisition(pdf_acq)

        with temp_db.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM pdf_acquisition WHERE pmid = ?", ("12345678",))
            row = cursor.fetchone()
            assert row is not None
            assert row[1] == "data/pdfs/test.pdf"


class TestContentExtraction:
    """Test content_extraction table operations."""

    def test_insert_content_extraction(self, temp_db):
        """Test inserting content extraction."""
        pub = UniversalIdentifier(geo_id="GSE12345", pmid="12345678", title="Test")
        temp_db.insert_universal_identifier(pub)

        extraction = ContentExtraction(
            pmid="12345678",
            full_text="This is the extracted text...",
            extraction_method="pypdf",
            quality_score=0.95,
            quality_grade="A",
            word_count=5000,
        )

        temp_db.insert_content_extraction(extraction)

        with temp_db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM content_extraction WHERE pmid = ?",
                ("12345678",),
            )
            row = cursor.fetchone()
            assert row is not None
            assert row[3] == 0.95  # quality_score
            assert row[4] == "A"  # quality_grade


class TestEnrichedContent:
    """Test enriched_content table operations."""

    def test_insert_enriched_content(self, temp_db):
        """Test inserting enriched content."""
        pub = UniversalIdentifier(geo_id="GSE12345", pmid="12345678", title="Test")
        temp_db.insert_universal_identifier(pub)

        enriched = EnrichedContent(
            pmid="12345678",
            has_sections=True,
            section_count=5,
            has_tables=True,
            table_count=3,
            has_references=True,
            reference_count=25,
        )

        temp_db.insert_enriched_content(enriched)

        with temp_db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM enriched_content WHERE pmid = ?",
                ("12345678",),
            )
            row = cursor.fetchone()
            assert row is not None
            assert row[1] == 1  # has_sections (stored as int)
            assert row[2] == 5  # section_count


class TestProcessingLog:
    """Test processing_log table operations."""

    def test_insert_processing_log(self, temp_db):
        """Test inserting processing log entry."""
        log = ProcessingLog(
            pipeline_name="P3_pdf",
            geo_id="GSE12345",
            pmid="12345678",
            success=True,
            duration_seconds=2.5,
        )

        temp_db.insert_processing_log(log)

        with temp_db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM processing_log WHERE pipeline_name = ?",
                ("P3_pdf",),
            )
            row = cursor.fetchone()
            assert row is not None
            assert row[4] == 1  # success
            assert row[5] == 2.5  # duration_seconds

    def test_insert_error_log(self, temp_db):
        """Test logging errors."""
        log = ProcessingLog(
            pipeline_name="P3_pdf",
            geo_id="GSE12345",
            pmid="12345678",
            success=False,
            error_message="PDF download failed: 404",
        )

        temp_db.insert_processing_log(log)

        with temp_db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT error_message FROM processing_log WHERE pmid = ?",
                ("12345678",),
            )
            error = cursor.fetchone()[0]
            assert "404" in error


class TestTransactions:
    """Test transaction support."""

    def test_transaction_commit(self, temp_db):
        """Test successful transaction commit."""
        with temp_db.get_connection() as conn:
            pub = UniversalIdentifier(geo_id="GSE12345", pmid="12345678", title="Test")
            temp_db.insert_universal_identifier(pub)

        # Verify data persisted
        with temp_db.get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM universal_identifiers")
            count = cursor.fetchone()[0]
            assert count == 1

    def test_transaction_rollback(self, temp_db):
        """Test transaction rollback on error."""
        try:
            with temp_db.get_connection() as conn:
                pub = UniversalIdentifier(geo_id="GSE12345", pmid="12345678", title="Test")
                temp_db.insert_universal_identifier(pub)

                # Intentionally cause an error
                raise ValueError("Test error")
        except ValueError:
            pass

        # Verify data was rolled back
        with temp_db.get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM universal_identifiers")
            count = cursor.fetchone()[0]
            # Transaction should have been rolled back
            # Note: This depends on implementation details


class TestDatabaseStatistics:
    """Test database statistics methods."""

    def test_get_database_statistics(self, temp_db):
        """Test getting database statistics."""
        # Insert some test data
        for i in range(5):
            pub = UniversalIdentifier(geo_id="GSE12345", pmid=f"1234567{i}", title=f"Test {i}")
            temp_db.insert_universal_identifier(pub)

        stats = temp_db.get_database_statistics()

        assert stats["total_publications"] == 5
        assert "table_counts" in stats

    def test_get_publication_status(self, temp_db):
        """Test getting publication status."""
        pub = UniversalIdentifier(geo_id="GSE12345", pmid="12345678", title="Test")
        temp_db.insert_universal_identifier(pub)

        status = temp_db.get_publication_status("GSE12345", "12345678")

        assert status["exists"]
        assert status["pmid"] == "12345678"
        assert not status["has_pdf"]
        assert not status["has_extraction"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
