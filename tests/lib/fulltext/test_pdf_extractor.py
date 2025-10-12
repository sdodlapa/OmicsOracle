"""
Tests for PDF extraction functionality.

Tests the PDFExtractor class which parses PDF files using:
- camelot-py for table extraction
- PyMuPDF for text/image extraction
- pdfplumber as fallback
"""

from pathlib import Path

import pytest

from lib.fulltext.pdf_extractor import PDFExtractor, extract_tables_from_pdf, extract_text_from_pdf


class TestPDFExtractor:
    """Tests for PDFExtractor class."""

    @pytest.fixture
    def extractor(self):
        """Create PDFExtractor instance."""
        return PDFExtractor()

    @pytest.fixture
    def sample_pdf(self):
        """Get path to sample PDF for testing."""
        # Use the arXiv PDF we downloaded earlier
        pdf_path = Path("data/fulltext/pdfs/056d82a155cf5a0b8ab7c0882f607d36.pdf")
        if pdf_path.exists():
            return pdf_path
        # Fallback: try to find any PDF
        pdf_dir = Path("data/fulltext/pdfs")
        if pdf_dir.exists():
            pdfs = list(pdf_dir.glob("*.pdf"))
            if pdfs:
                return pdfs[0]
        pytest.skip("No sample PDF available for testing")

    def test_extractor_initialization(self, extractor):
        """Test PDFExtractor initializes with library checks."""
        assert extractor is not None

        # Check capabilities
        capabilities = extractor.get_capabilities()
        assert isinstance(capabilities, dict)
        assert "camelot_available" in capabilities
        assert "pymupdf_available" in capabilities
        assert "pdfplumber_available" in capabilities

    def test_capabilities(self, extractor):
        """Test capability detection."""
        caps = extractor.get_capabilities()

        # At least PyMuPDF should be available (we installed it)
        # camelot might not be if test environment is minimal
        assert "can_extract_text" in caps
        assert "can_extract_tables" in caps
        assert "can_extract_images" in caps

    def test_extract_text(self, extractor, sample_pdf):
        """Test text extraction from PDF."""
        text = extractor.extract_text(sample_pdf)

        assert isinstance(text, str)
        assert len(text) > 0, "Should extract some text"
        assert "page" in text.lower() or len(text) > 100, "Should have substantial content"

    def test_extract_text_convenience(self, sample_pdf):
        """Test convenience function for text extraction."""
        text = extract_text_from_pdf(sample_pdf)

        assert isinstance(text, str)
        assert len(text) > 0

    def test_extract_tables(self, extractor, sample_pdf):
        """Test table extraction from PDF."""
        tables = extractor.extract_tables(sample_pdf, method="auto")

        assert isinstance(tables, list)
        # May or may not find tables depending on PDF content
        # Just verify it doesn't crash

    def test_extract_tables_camelot_stream(self, extractor, sample_pdf):
        """Test camelot stream method specifically."""
        if not extractor.camelot_available:
            pytest.skip("camelot not available")

        tables = extractor.extract_tables(sample_pdf, method="stream")

        assert isinstance(tables, list)
        # If we got tables, verify structure
        if tables:
            table = tables[0]
            assert hasattr(table, "table_columns")
            assert hasattr(table, "table_values")
            assert hasattr(table, "metadata")
            assert table.metadata.get("method") == "stream"

    def test_extract_tables_camelot_lattice(self, extractor, sample_pdf):
        """Test camelot lattice method specifically."""
        if not extractor.camelot_available:
            pytest.skip("camelot not available")

        tables = extractor.extract_tables(sample_pdf, method="lattice")

        assert isinstance(tables, list)
        # Lattice may find 0 tables if no borders

    def test_extract_tables_pdfplumber(self, extractor, sample_pdf):
        """Test pdfplumber fallback method."""
        if not extractor.pdfplumber_available:
            pytest.skip("pdfplumber not available")

        tables = extractor.extract_tables(sample_pdf, method="pdfplumber")

        assert isinstance(tables, list)

    def test_extract_tables_convenience(self, sample_pdf):
        """Test convenience function for table extraction."""
        tables = extract_tables_from_pdf(sample_pdf)

        assert isinstance(tables, list)

    def test_extract_images(self, extractor, sample_pdf, tmp_path):
        """Test image extraction from PDF."""
        if not extractor.pymupdf_available:
            pytest.skip("PyMuPDF not available")

        images = extractor.extract_images(sample_pdf, output_dir=tmp_path)

        assert isinstance(images, list)
        # May or may not have images depending on PDF

        # If images extracted, verify files were saved
        if images:
            figure = images[0]
            assert hasattr(figure, "graphic_ref")
            # Check if file exists if path was provided
            if figure.graphic_ref:
                assert Path(figure.graphic_ref).exists()

    def test_extract_structured_content(self, extractor, sample_pdf):
        """Test full structured content extraction."""
        content = extractor.extract_structured_content(sample_pdf, extract_tables=True, extract_images=False)

        assert content is not None
        assert hasattr(content, "sections")
        assert hasattr(content, "tables")
        assert hasattr(content, "figures")

        # Should have at least one section
        assert len(content.sections) > 0

        # Verify methods work
        full_text = content.get_full_text()
        assert isinstance(full_text, str)
        assert len(full_text) > 0

    def test_section_parsing(self, extractor):
        """Test section parsing from text."""
        sample_text = """
        Abstract
        This is the abstract section.

        Introduction
        This is the introduction.

        Methods
        This is the methods section.

        Results
        This is the results section.

        Conclusion
        This is the conclusion.
        """

        sections = extractor._parse_sections_from_text(sample_text)

        assert len(sections) > 0

        # Should detect multiple sections
        section_titles = [s.title.lower() for s in sections]
        assert any("abstract" in title for title in section_titles)

    def test_nonexistent_pdf(self, extractor):
        """Test handling of nonexistent PDF file."""
        fake_path = Path("nonexistent.pdf")

        text = extractor.extract_text(fake_path)
        assert text == ""

        tables = extractor.extract_tables(fake_path)
        assert tables == []

        images = extractor.extract_images(fake_path)
        assert images == []

    def test_extract_with_table_extraction_disabled(self, extractor, sample_pdf):
        """Test extraction with tables disabled (faster)."""
        content = extractor.extract_structured_content(sample_pdf, extract_tables=False, extract_images=False)

        assert content is not None
        assert len(content.tables) == 0  # Should be empty when disabled
        assert len(content.sections) > 0  # Should still have text


class TestPDFTableQuality:
    """Tests for table extraction quality (if we have known test PDFs)."""

    @pytest.fixture
    def arxiv_pdf(self):
        """Get the arXiv PDF we tested earlier."""
        pdf_path = Path("data/fulltext/pdfs/056d82a155cf5a0b8ab7c0882f607d36.pdf")
        if not pdf_path.exists():
            pytest.skip("arXiv test PDF not available")
        return pdf_path

    def test_arxiv_table_extraction(self, arxiv_pdf):
        """Test table extraction on known arXiv PDF."""
        extractor = PDFExtractor()

        if not extractor.camelot_available:
            pytest.skip("camelot not available")

        # We know this PDF has 5 tables extractable via stream
        tables = extractor.extract_tables(arxiv_pdf, method="stream")

        # Should find at least some tables
        # (exact count may vary depending on camelot settings)
        assert len(tables) > 0, "Should find at least one table"

        # Verify table structure
        table = tables[0]
        assert table.table_columns is not None
        assert table.table_values is not None
        assert len(table.table_values) > 0, "Table should have data rows"

        # Check metadata
        assert table.metadata is not None
        assert "accuracy" in table.metadata
        assert "page" in table.metadata

        # Accuracy should be high (>90%)
        accuracy = table.metadata.get("accuracy", 0)
        assert accuracy > 90, f"Table accuracy {accuracy}% should be >90%"


@pytest.mark.integration
class TestPDFIntegration:
    """Integration tests for PDF extraction with full pipeline."""

    def test_pdf_to_structured_content(self):
        """Test complete PDF → FullTextContent pipeline."""
        pdf_path = Path("data/fulltext/pdfs/056d82a155cf5a0b8ab7c0882f607d36.pdf")

        if not pdf_path.exists():
            pytest.skip("Test PDF not available")

        extractor = PDFExtractor()
        content = extractor.extract_structured_content(pdf_path, extract_tables=True, extract_images=False)

        # Verify complete structure
        assert content.title is not None  # May be empty for PDFs
        assert content.sections is not None
        assert content.tables is not None
        assert content.figures is not None

        # Should extract meaningful content
        full_text = content.get_full_text()
        assert len(full_text) > 1000, "Should extract substantial text"

        # Check quality indicators
        assert len(content.sections) > 0, "Should have sections"

    def test_quality_score_calculation(self):
        """Test that quality scores are calculated correctly."""
        pdf_path = Path("data/fulltext/pdfs/056d82a155cf5a0b8ab7c0882f607d36.pdf")

        if not pdf_path.exists():
            pytest.skip("Test PDF not available")

        # Use the integration function
        import asyncio

        from lib.fulltext.manager_integration import try_pdf_extraction

        result = asyncio.run(try_pdf_extraction(pdf_path, extract_tables=True))

        if result.success:
            assert result.quality_score is not None
            assert 0.0 <= result.quality_score <= 1.0
            assert result.word_count > 0
