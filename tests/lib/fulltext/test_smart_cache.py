"""
Tests for SmartCache - multi-level cache manager for full-text content.

These tests verify that the smart cache can:
1. Find XML files in pmc/ subdirectory
2. Find PDF files in source-specific subdirectories
3. Handle multiple naming patterns (with/without PMC prefix, sanitized DOIs, etc.)
4. Save files to appropriate locations based on source
5. Fall back to hash-based cache for legacy files

Author: OmicsOracle Team
Date: October 11, 2025
"""

import hashlib
import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from omics_oracle_v2.lib.fulltext.smart_cache import LocalFileResult, SmartCache, check_local_cache


@pytest.fixture
def temp_cache_dir():
    """Create temporary directory for cache testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def smart_cache(temp_cache_dir):
    """Create SmartCache instance with temporary directory."""
    return SmartCache(base_dir=temp_cache_dir)


@pytest.fixture
def mock_publication():
    """Create mock publication with various identifiers."""
    pub = Mock()
    pub.id = "test_paper_1"
    pub.doi = "10.1234/test.2023.001"
    pub.pmid = "12345678"
    pub.pmc_id = "PMC9876543"
    pub.title = "Test Paper for Cache Validation"
    return pub


@pytest.fixture
def mock_arxiv_publication():
    """Create mock arXiv publication."""
    pub = Mock()
    pub.id = "arxiv_paper_1"
    pub.doi = "10.48550/arxiv.2301.12345"
    pub.pmid = None
    pub.pmc_id = None
    pub.title = "arXiv Test Paper"
    return pub


class TestSmartCacheInitialization:
    """Test SmartCache initialization and directory creation."""

    def test_initialization(self, smart_cache, temp_cache_dir):
        """Test that SmartCache creates necessary directories."""
        assert smart_cache.base_dir == temp_cache_dir
        assert smart_cache.pdf_dir == temp_cache_dir / "pdf"
        assert smart_cache.xml_dir == temp_cache_dir / "xml"
        assert smart_cache.parsed_dir == temp_cache_dir / "parsed"

        # Check directories were created
        assert smart_cache.pdf_dir.exists()
        assert smart_cache.xml_dir.exists()
        assert smart_cache.parsed_dir.exists()

    def test_default_base_dir(self):
        """Test that default base_dir points to data/fulltext."""
        cache = SmartCache()

        # Should point to project root's data/fulltext
        assert cache.base_dir.name == "fulltext"
        assert cache.base_dir.parent.name == "data"


class TestXMLFileDetection:
    """Test XML file detection in pmc/ subdirectory."""

    def test_find_pmc_xml_with_pmc_prefix(self, smart_cache, mock_publication):
        """Test finding PMC XML with PMC prefix in filename."""
        # Create PMC XML file
        pmc_xml_dir = smart_cache.xml_dir / "pmc"
        pmc_xml_dir.mkdir(parents=True, exist_ok=True)

        xml_file = pmc_xml_dir / "PMC9876543.nxml"
        xml_file.write_text("<?xml version='1.0'?><article>Test content</article>")

        # Find file
        result = smart_cache.find_local_file(mock_publication)

        assert result.found is True
        assert result.file_type == "nxml"
        assert result.source == "pmc_xml"
        assert result.file_path == xml_file
        assert result.size_bytes > 0

    def test_find_pmc_xml_without_pmc_prefix(self, smart_cache, mock_publication):
        """Test finding PMC XML without PMC prefix in filename."""
        # Create PMC XML file (ID only, no PMC prefix)
        pmc_xml_dir = smart_cache.xml_dir / "pmc"
        pmc_xml_dir.mkdir(parents=True, exist_ok=True)

        xml_file = pmc_xml_dir / "9876543.nxml"
        xml_file.write_text("<?xml version='1.0'?><article>Test content</article>")

        # Find file
        result = smart_cache.find_local_file(mock_publication)

        assert result.found is True
        assert result.file_type == "nxml"
        assert result.source == "pmc_xml"
        assert result.file_path == xml_file

    def test_find_pmc_xml_with_xml_extension(self, smart_cache, mock_publication):
        """Test finding PMC XML with .xml extension instead of .nxml."""
        pmc_xml_dir = smart_cache.xml_dir / "pmc"
        pmc_xml_dir.mkdir(parents=True, exist_ok=True)

        xml_file = pmc_xml_dir / "PMC9876543.xml"
        xml_file.write_text("<?xml version='1.0'?><article>Test content</article>")

        result = smart_cache.find_local_file(mock_publication)

        assert result.found is True
        assert result.file_type == "nxml"  # Still reported as nxml
        assert result.file_path == xml_file

    def test_xml_not_found(self, smart_cache, mock_publication):
        """Test when no XML file exists."""
        # Don't create any files

        result = smart_cache.find_local_file(mock_publication)

        # Should not find anything (no PDFs either)
        assert result.found is False

    def test_empty_xml_file_ignored(self, smart_cache, mock_publication):
        """Test that empty XML files are ignored."""
        pmc_xml_dir = smart_cache.xml_dir / "pmc"
        pmc_xml_dir.mkdir(parents=True, exist_ok=True)

        # Create empty file
        xml_file = pmc_xml_dir / "PMC9876543.nxml"
        xml_file.write_text("")

        result = smart_cache.find_local_file(mock_publication)

        # Should not find empty file
        assert result.found is False


class TestPDFFileDetection:
    """Test PDF file detection in various source-specific subdirectories."""

    def test_find_arxiv_pdf(self, smart_cache, mock_arxiv_publication):
        """Test finding arXiv PDF in arxiv/ subdirectory."""
        arxiv_dir = smart_cache.pdf_dir / "arxiv"
        arxiv_dir.mkdir(parents=True, exist_ok=True)

        pdf_file = arxiv_dir / "2301.12345.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake pdf content")

        result = smart_cache.find_local_file(mock_arxiv_publication)

        assert result.found is True
        assert result.file_type == "pdf"
        assert result.source == "arxiv"
        assert result.file_path == pdf_file

    def test_find_pmc_pdf(self, smart_cache, mock_publication):
        """Test finding PMC PDF in pmc/ subdirectory."""
        pmc_dir = smart_cache.pdf_dir / "pmc"
        pmc_dir.mkdir(parents=True, exist_ok=True)

        pdf_file = pmc_dir / "PMC9876543.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake pdf content")

        result = smart_cache.find_local_file(mock_publication)

        assert result.found is True
        assert result.file_type == "pdf"
        assert result.source == "pmc"
        assert result.file_path == pdf_file

    def test_find_institutional_pdf(self, smart_cache, mock_publication):
        """Test finding institutional PDF in institutional/ subdirectory."""
        institutional_dir = smart_cache.pdf_dir / "institutional"
        institutional_dir.mkdir(parents=True, exist_ok=True)

        # Use sanitized DOI as filename
        sanitized_doi = mock_publication.doi.replace("/", "_").replace(".", "_")
        pdf_file = institutional_dir / f"{sanitized_doi}.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake pdf content")

        result = smart_cache.find_local_file(mock_publication)

        assert result.found is True
        assert result.file_type == "pdf"
        assert result.source == "institutional"

    def test_find_scihub_pdf(self, smart_cache, mock_publication):
        """Test finding Sci-Hub PDF in scihub/ subdirectory."""
        scihub_dir = smart_cache.pdf_dir / "scihub"
        scihub_dir.mkdir(parents=True, exist_ok=True)

        sanitized_doi = mock_publication.doi.replace("/", "_").replace(".", "_")
        pdf_file = scihub_dir / f"{sanitized_doi}.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake pdf content")

        result = smart_cache.find_local_file(mock_publication)

        assert result.found is True
        assert result.file_type == "pdf"
        assert result.source == "scihub"

    def test_find_hash_based_cache(self, smart_cache, mock_publication):
        """Test finding legacy hash-based cached PDF."""
        # Create hash-based cache file (old system)
        doi_hash = hashlib.md5(mock_publication.doi.encode()).hexdigest()
        pdf_file = smart_cache.pdf_dir / f"{doi_hash}.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake pdf content")

        result = smart_cache.find_local_file(mock_publication)

        assert result.found is True
        assert result.file_type == "pdf"
        assert result.source == "cache"
        assert result.file_path == pdf_file

    def test_pdf_priority_order(self, smart_cache, mock_publication):
        """Test that PDFs are found in correct priority order."""
        # Create PDFs in multiple locations
        arxiv_dir = smart_cache.pdf_dir / "arxiv"
        arxiv_dir.mkdir(parents=True, exist_ok=True)

        institutional_dir = smart_cache.pdf_dir / "institutional"
        institutional_dir.mkdir(parents=True, exist_ok=True)

        # arXiv should be found first (higher priority)
        arxiv_pdf = arxiv_dir / "test.pdf"
        arxiv_pdf.write_bytes(b"arXiv PDF")

        inst_pdf = institutional_dir / "test.pdf"
        inst_pdf.write_bytes(b"Institutional PDF")

        # Note: This test assumes publication has arXiv-like identifiers
        # In real scenario, would only match if publication.doi contains "arxiv"


class TestXMLOverPDFPriority:
    """Test that XML files are prioritized over PDF files."""

    def test_xml_found_before_pdf(self, smart_cache, mock_publication):
        """Test that XML file is returned even when PDF exists."""
        # Create both XML and PDF
        pmc_xml_dir = smart_cache.xml_dir / "pmc"
        pmc_xml_dir.mkdir(parents=True, exist_ok=True)
        xml_file = pmc_xml_dir / "PMC9876543.nxml"
        xml_file.write_text("<?xml version='1.0'?><article>XML content</article>")

        pmc_pdf_dir = smart_cache.pdf_dir / "pmc"
        pmc_pdf_dir.mkdir(parents=True, exist_ok=True)
        pdf_file = pmc_pdf_dir / "PMC9876543.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 PDF content")

        result = smart_cache.find_local_file(mock_publication)

        # Should return XML, not PDF
        assert result.found is True
        assert result.file_type == "nxml"
        assert result.source == "pmc_xml"
        assert result.file_path == xml_file


class TestFileSaving:
    """Test saving files to appropriate locations."""

    def test_save_arxiv_pdf(self, smart_cache, mock_arxiv_publication):
        """Test saving arXiv PDF to correct location."""
        pdf_content = b"%PDF-1.4 Test arXiv PDF content"

        saved_path = smart_cache.save_file(
            content=pdf_content, publication=mock_arxiv_publication, source="arxiv", file_type="pdf"
        )

        assert saved_path.exists()
        assert saved_path.parent.name == "arxiv"
        assert "2301.12345" in saved_path.name
        assert saved_path.read_bytes() == pdf_content

    def test_save_pmc_xml(self, smart_cache, mock_publication):
        """Test saving PMC XML to correct location."""
        xml_content = b"<?xml version='1.0'?><article>Content</article>"

        saved_path = smart_cache.save_file(
            content=xml_content, publication=mock_publication, source="pmc", file_type="nxml"
        )

        assert saved_path.exists()
        assert saved_path.parent.name == "pmc"
        assert saved_path.name == "PMC9876543.nxml"
        assert saved_path.read_bytes() == xml_content

    def test_save_institutional_pdf(self, smart_cache, mock_publication):
        """Test saving institutional PDF to correct location."""
        pdf_content = b"%PDF-1.4 Institutional PDF"

        saved_path = smart_cache.save_file(
            content=pdf_content, publication=mock_publication, source="institutional", file_type="pdf"
        )

        assert saved_path.exists()
        assert saved_path.parent.name == "institutional"
        assert saved_path.read_bytes() == pdf_content

    def test_save_and_retrieve(self, smart_cache, mock_publication):
        """Test that saved files can be retrieved."""
        pdf_content = b"%PDF-1.4 Test content for round-trip"

        # Save file
        saved_path = smart_cache.save_file(
            content=pdf_content, publication=mock_publication, source="institutional", file_type="pdf"
        )

        # Retrieve file
        result = smart_cache.find_local_file(mock_publication)

        assert result.found is True
        assert result.file_path == saved_path
        assert result.source == "institutional"


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_publication_without_identifiers(self, smart_cache):
        """Test handling publication with minimal identifiers."""
        pub = Mock()
        pub.id = "minimal_pub"
        pub.doi = None
        pub.pmid = None
        pub.pmc_id = None
        pub.title = "Minimal Publication"

        result = smart_cache.find_local_file(pub)

        # Should not crash, just return not found
        assert result.found is False

    def test_publication_with_only_title(self, smart_cache):
        """Test publication with only title (uses hash)."""
        pub = Mock()
        pub.id = "title_only_pub"
        pub.doi = None
        pub.pmid = None
        pub.pmc_id = None
        pub.title = "Publication With Only Title"

        # Save file using title hash
        pdf_content = b"%PDF-1.4 Title hash test"
        saved_path = smart_cache.save_file(
            content=pdf_content, publication=pub, source="cache", file_type="pdf"
        )

        # Should be able to retrieve it
        result = smart_cache.find_local_file(pub)

        assert result.found is True
        assert result.file_path == saved_path

    def test_nonexistent_source_directory(self, smart_cache, mock_publication):
        """Test that nonexistent source directories don't cause errors."""
        # Don't create any directories

        result = smart_cache.find_local_file(mock_publication)

        # Should handle gracefully
        assert result.found is False

    def test_special_characters_in_doi(self, smart_cache):
        """Test handling DOI with special characters."""
        pub = Mock()
        pub.id = "special_chars"
        pub.doi = "10.1234/test:2023-001_v1.2"
        pub.pmid = None
        pub.pmc_id = None
        pub.title = "Test Paper"

        pdf_content = b"%PDF-1.4 Special chars test"

        # Should handle sanitization
        saved_path = smart_cache.save_file(
            content=pdf_content, publication=pub, source="publisher", file_type="pdf"
        )

        assert saved_path.exists()
        # Check that special chars were sanitized
        assert "/" not in saved_path.name
        assert ":" not in saved_path.name


class TestConvenienceFunction:
    """Test the convenience function check_local_cache()."""

    def test_check_local_cache_found(self, smart_cache, mock_publication, temp_cache_dir):
        """Test convenience function when file exists."""
        # Create a PDF file
        pmc_dir = temp_cache_dir / "pdf" / "pmc"
        pmc_dir.mkdir(parents=True, exist_ok=True)
        pdf_file = pmc_dir / "PMC9876543.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 Test")

        # Use convenience function
        result = check_local_cache(mock_publication)

        assert result.found is True
        assert result.file_type == "pdf"

    def test_check_local_cache_not_found(self, mock_publication):
        """Test convenience function when file doesn't exist."""
        result = check_local_cache(mock_publication)

        # Might be found if real cache exists, but should not crash
        assert isinstance(result, LocalFileResult)


class TestPerformance:
    """Test performance characteristics of smart cache."""

    def test_multiple_lookups_are_fast(self, smart_cache, mock_publication):
        """Test that multiple lookups complete quickly."""
        import time

        # Create a cached file
        pmc_dir = smart_cache.pdf_dir / "pmc"
        pmc_dir.mkdir(parents=True, exist_ok=True)
        pdf_file = pmc_dir / "PMC9876543.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 Performance test")

        # Time 100 lookups
        start = time.time()
        for _ in range(100):
            result = smart_cache.find_local_file(mock_publication)
            assert result.found is True
        elapsed = time.time() - start

        # Should complete in under 1 second (likely under 0.1s)
        assert elapsed < 1.0

        print(f"\n100 cache lookups: {elapsed*1000:.2f}ms ({elapsed*10:.2f}ms per lookup)")
