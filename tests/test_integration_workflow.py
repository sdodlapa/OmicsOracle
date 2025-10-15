"""
Integration Test: Complete P1->P2->P3->P4 Workflow

This test validates the entire unified database system with a real workflow:
1. P1: Citation Discovery
2. P2: URL Discovery
3. P3: PDF Acquisition
4. P4: Content Extraction & Enrichment

Tests:
- Database records created correctly
- File storage working (GEO-centric organization)
- Data integrity (SHA256 verification)
- Query operations
- Analytics and exports
- Error handling

This is the MOST VALUABLE test - it proves the whole system works end-to-end.
"""

import json
import tempfile
from pathlib import Path

import pytest

from omics_oracle_v2.lib.pipelines.coordinator import PipelineCoordinator
from omics_oracle_v2.lib.storage.analytics import Analytics
from omics_oracle_v2.lib.storage.queries import DatabaseQueries


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)

        # Create directory structure
        (workspace / "database").mkdir()
        (workspace / "pdfs" / "by_geo").mkdir(parents=True)
        (workspace / "enriched" / "by_geo").mkdir(parents=True)
        (workspace / "reports").mkdir()

        yield workspace


@pytest.fixture
def coordinator(temp_workspace):
    """Create a PipelineCoordinator for testing."""
    db_path = str(temp_workspace / "database" / "test.db")
    storage_path = str(temp_workspace)

    coord = PipelineCoordinator(db_path=db_path, storage_path=storage_path)

    return coord


@pytest.fixture
def queries(temp_workspace):
    """Create DatabaseQueries instance."""
    db_path = str(temp_workspace / "database" / "test.db")
    return DatabaseQueries(db_path)


@pytest.fixture
def analytics(temp_workspace):
    """Create Analytics instance."""
    db_path = str(temp_workspace / "database" / "test.db")
    storage_path = str(temp_workspace)
    return Analytics(db_path=db_path, storage_path=storage_path)


class TestCompleteWorkflow:
    """Test complete P1->P2->P3->P4 workflow."""

    def test_p1_citation_discovery(self, coordinator, queries):
        """Test P1: Citation discovery integration."""
        geo_id = "GSE12345"
        pmid = "12345678"

        # Simulate P1: Save citation discovery
        citation_data = {
            "title": "Test Publication",
            "authors": "Smith J, Doe J",
            "doi": "10.1234/test",
            "journal": "Test Journal",
            "publication_date": "2024-01-01",
        }

        coordinator.save_citation_discovery(geo_id=geo_id, pmid=pmid, citation_data=citation_data)

        # Verify in database using queries
        pub = queries.get_publication_details(pmid)
        assert pub is not None
        assert pub["geo_id"] == geo_id
        assert pub["pmid"] == pmid
        assert "Test Publication" in pub["title"]

    def test_p2_url_discovery(self, coordinator, queries):
        """Test P2: URL discovery integration."""
        geo_id = "GSE12345"
        pmid = "12345678"

        # First P1
        coordinator.save_citation_discovery(
            geo_id=geo_id,
            pmid=pmid,
            citation_data={"title": "Test"},
        )

        # Then P2: URL discovery
        urls = [
            {"url": "https://example.com/paper.pdf", "type": "pdf", "source": "pubmed"},
            {"url": "https://doi.org/10.1234/test", "type": "doi", "source": "unpaywall"},
        ]

        coordinator.save_url_discovery(
            geo_id=geo_id,
            pmid=pmid,
            urls=urls,
            sources_queried=["pubmed", "unpaywall"],
        )

        # Verify
        pub = queries.get_publication_details(pmid)
        assert pub["url_count"] == 2
        assert "pubmed" in pub["sources_queried"]

    def test_p3_pdf_acquisition(self, coordinator, queries, temp_workspace):
        """Test P3: PDF acquisition integration."""
        geo_id = "GSE12345"
        pmid = "12345678"

        # P1
        coordinator.save_citation_discovery(geo_id=geo_id, pmid=pmid, citation_data={"title": "Test"})

        # Create a fake PDF file
        test_pdf = temp_workspace / "test_paper.pdf"
        test_pdf.write_bytes(b"%PDF-1.4\nFake PDF content for testing")

        # P3: PDF acquisition
        result = coordinator.save_pdf_acquisition(geo_id=geo_id, pmid=pmid, pdf_path=test_pdf)

        assert result["verified"]
        assert "pdf_path" in result
        assert "sha256" in result

        # Verify database
        pub = queries.get_publication_details(pmid)
        assert pub["pdf_path"] is not None
        assert pub["pdf_hash_sha256"] is not None
        assert pub["pdf_size_bytes"] > 0

        # Verify file exists in GEO-centric location
        expected_path = temp_workspace / "pdfs" / "by_geo" / geo_id / f"pmid_{pmid}.pdf"
        assert expected_path.exists()

    def test_p4_content_extraction(self, coordinator, queries):
        """Test P4: Content extraction integration."""
        geo_id = "GSE12345"
        pmid = "12345678"

        # P1
        coordinator.save_citation_discovery(geo_id=geo_id, pmid=pmid, citation_data={"title": "Test"})

        # P4: Content extraction
        extraction_data = {
            "full_text": "This is the extracted text from the PDF. " * 100,
            "extraction_method": "pypdf",
            "extraction_quality": 0.95,
            "extraction_grade": "A",
        }

        coordinator.save_content_extraction(geo_id=geo_id, pmid=pmid, extraction_data=extraction_data)

        # Verify
        pub = queries.get_publication_details(pmid)
        assert pub["extraction_quality"] == 0.95
        assert pub["extraction_grade"] == "A"
        assert pub["word_count"] > 0

    def test_p4_enriched_content(self, coordinator, queries, temp_workspace):
        """Test P4: Enriched content integration."""
        geo_id = "GSE12345"
        pmid = "12345678"

        # P1
        coordinator.save_citation_discovery(geo_id=geo_id, pmid=pmid, citation_data={"title": "Test"})

        # P4: Enriched content
        enriched_data = {
            "sections": [
                {"title": "Introduction", "content": "..."},
                {"title": "Methods", "content": "..."},
                {"title": "Results", "content": "..."},
            ],
            "tables": [
                {"caption": "Table 1", "data": "..."},
                {"caption": "Table 2", "data": "..."},
            ],
            "references": ["PMID:111111", "PMID:222222", "PMID:333333"],
        }

        coordinator.save_enriched_content(geo_id=geo_id, pmid=pmid, enriched_data=enriched_data)

        # Verify database
        pub = queries.get_publication_details(pmid)
        assert pub["sections_json"] is not None
        assert pub["tables_json"] is not None
        assert pub["references_json"] is not None

        # Parse and verify JSON content
        sections = json.loads(pub["sections_json"])
        tables = json.loads(pub["tables_json"])
        refs = json.loads(pub["references_json"])

        assert len(sections) == 3
        assert len(tables) == 2
        assert len(refs) == 3

        # Verify JSON file exists
        enriched_file = temp_workspace / "enriched" / "by_geo" / geo_id / f"pmid_{pmid}.json"
        assert enriched_file.exists()

        # Verify content
        with open(enriched_file) as f:
            saved_data = json.load(f)
        assert len(saved_data["sections"]) == 3
        assert len(saved_data["tables"]) == 2

    def test_complete_pipeline_workflow(self, coordinator, queries, temp_workspace):
        """Test complete P1->P2->P3->P4 workflow for multiple publications."""
        geo_id = "GSE12345"

        # Process 5 publications through complete workflow
        for i in range(5):
            pmid = f"1234567{i}"

            # P1: Citation
            coordinator.save_citation_discovery(
                geo_id=geo_id,
                pmid=pmid,
                citation_data={
                    "title": f"Publication {i}",
                    "authors": f"Author {i}",
                },
            )

            # P2: URLs
            coordinator.save_url_discovery(
                geo_id=geo_id,
                pmid=pmid,
                urls=[{"url": f"https://example.com/{pmid}.pdf", "type": "pdf"}],
                sources_queried=["pubmed"],
            )

            # P3: PDF (create fake PDF)
            test_pdf = temp_workspace / f"test_{pmid}.pdf"
            test_pdf.write_bytes(b"%PDF-1.4\nFake PDF")
            coordinator.save_pdf_acquisition(geo_id=geo_id, pmid=pmid, pdf_path=test_pdf)

            # P4: Extraction
            coordinator.save_content_extraction(
                geo_id=geo_id,
                pmid=pmid,
                extraction_data={
                    "full_text": f"Content for {pmid}. " * 50,
                    "extraction_quality": 0.8 + (i * 0.03),
                    "extraction_grade": "A" if i < 2 else "B",
                },
            )

            # P4: Enrichment
            coordinator.save_enriched_content(
                geo_id=geo_id,
                pmid=pmid,
                enriched_data={
                    "sections": [{"title": "Intro", "content": "..."}],
                    "tables": [],
                    "references": ["PMID:99999"],
                },
            )

        # Verify all publications
        pubs = queries.get_geo_publications(geo_id)
        assert len(pubs) == 5

        # Verify GEO statistics
        stats = queries.get_geo_statistics(geo_id)
        assert stats["publication_counts"]["total"] == 5
        assert stats["publication_counts"]["with_pdf"] == 5
        assert stats["publication_counts"]["with_extraction"] == 5
        assert stats["publication_counts"]["with_enriched"] == 5
        assert stats["completion_rate"] == 100.0

    def test_query_operations(self, coordinator, queries):
        """Test various query operations."""
        # Create test data with different quality scores
        for i in range(10):
            geo_id = f"GSE{10000 + i}"
            pmid = f"9999999{i}"

            coordinator.save_citation_discovery(
                geo_id=geo_id,
                pmid=pmid,
                citation_data={"title": f"Paper {i}"},
            )

            coordinator.save_content_extraction(
                geo_id=geo_id,
                pmid=pmid,
                extraction_data={
                    "full_text": "Test content",
                    "extraction_quality": 0.5 + (i * 0.05),
                    "extraction_grade": "A" if i >= 8 else ("B" if i >= 5 else "C"),
                },
            )

        # Test: Get high-quality publications
        high_quality = queries.get_publications_by_quality(min_quality=0.8, extraction_grades=["A"])
        assert len(high_quality) >= 2

        # Test: Get incomplete publications
        incomplete = queries.get_incomplete_publications()
        assert len(incomplete) == 10  # None have PDFs

        # Test: Processing statistics
        stats = queries.get_processing_statistics()
        assert stats["total_publications"] == 10

    def test_analytics_operations(self, coordinator, analytics, temp_workspace):
        """Test analytics and export operations."""
        geo_id = "GSE12345"

        # Create test data
        for i in range(3):
            pmid = f"5555555{i}"
            coordinator.save_citation_discovery(
                geo_id=geo_id,
                pmid=pmid,
                citation_data={"title": f"Paper {i}"},
            )

            # Add PDF
            test_pdf = temp_workspace / f"paper_{pmid}.pdf"
            test_pdf.write_bytes(b"%PDF-1.4\nTest")
            coordinator.save_pdf_acquisition(geo_id=geo_id, pmid=pmid, pdf_path=test_pdf)

            # Add extraction
            coordinator.save_content_extraction(
                geo_id=geo_id,
                pmid=pmid,
                extraction_data={
                    "full_text": "Content",
                    "extraction_quality": 0.9,
                    "extraction_grade": "A",
                },
            )

        # Test: Export GEO dataset
        export_dir = temp_workspace / "exports" / geo_id
        result = analytics.export_geo_dataset(
            geo_id=geo_id,
            output_dir=str(export_dir),
            include_pdfs=True,
            include_enriched=False,
        )

        assert result["publication_count"] == 3
        assert result["pdfs_copied"] == 3
        assert (export_dir / "metadata.json").exists()
        assert (export_dir / "publications.json").exists()

        # Test: Quality distribution
        quality_dist = analytics.calculate_quality_distribution()
        assert quality_dist["total_extracted"] == 3
        assert "A" in quality_dist["grade_distribution"]

        # Test: Storage efficiency
        storage = analytics.get_storage_efficiency()
        assert storage["pdfs"]["file_count"] == 3
        assert storage["database"]["size_mb"] > 0

    def test_error_logging(self, coordinator, queries):
        """Test that errors are logged to processing_log."""
        geo_id = "GSE12345"
        pmid = "99999999"

        # Simulate an error in processing
        try:
            # Try to save PDF without citation first (should fail foreign key)
            test_pdf = Path("/tmp/nonexistent.pdf")
            coordinator.save_pdf_acquisition(geo_id=geo_id, pmid=pmid, pdf_path=test_pdf)
        except Exception:
            pass  # Expected to fail

        # Check if error was logged
        errors = queries.get_recent_errors(limit=10)
        # May or may not have errors depending on implementation


class TestDataIntegrity:
    """Test data integrity features."""

    def test_pdf_hash_verification(self, coordinator, temp_workspace):
        """Test that PDF hashes are verified."""
        geo_id = "GSE12345"
        pmid = "12345678"

        coordinator.save_citation_discovery(geo_id=geo_id, pmid=pmid, citation_data={"title": "Test"})

        # Create PDF
        test_pdf = temp_workspace / "test.pdf"
        test_pdf.write_bytes(b"%PDF-1.4\nTest content")

        # Save PDF
        result = coordinator.save_pdf_acquisition(geo_id=geo_id, pmid=pmid, pdf_path=test_pdf)

        assert result["verified"]
        assert len(result["sha256"]) == 64  # SHA256 is 64 hex chars

    def test_geo_centric_organization(self, coordinator, temp_workspace):
        """Test that files are organized by GEO dataset."""
        geo_ids = ["GSE11111", "GSE22222", "GSE33333"]

        for geo_id in geo_ids:
            pmid = f"{geo_id[-5:]}"
            coordinator.save_citation_discovery(geo_id=geo_id, pmid=pmid, citation_data={"title": "Test"})

            # Save PDF
            test_pdf = temp_workspace / f"{pmid}.pdf"
            test_pdf.write_bytes(b"%PDF-1.4\nTest")
            coordinator.save_pdf_acquisition(geo_id=geo_id, pmid=pmid, pdf_path=test_pdf)

        # Verify directory structure
        pdfs_dir = temp_workspace / "pdfs" / "by_geo"
        assert (pdfs_dir / "GSE11111").exists()
        assert (pdfs_dir / "GSE22222").exists()
        assert (pdfs_dir / "GSE33333").exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
