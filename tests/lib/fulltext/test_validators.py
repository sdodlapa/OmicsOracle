"""
Tests for full-text content validators.

Tests XML and PDF validation with various edge cases.
"""

import hashlib
import pytest
from pathlib import Path

from lib.fulltext.validators import (
    XMLValidator,
    PDFValidator,
    ContentValidator,
    validate_xml_file,
    validate_pdf_file,
)


class TestXMLValidator:
    """Tests for XMLValidator."""

    @pytest.fixture
    def validator(self):
        """Create XMLValidator instance."""
        # Use smaller threshold for tests
        return XMLValidator(min_xml_size=50)

    @pytest.fixture
    def valid_xml(self):
        """Valid PMC XML content."""
        return """<?xml version="1.0"?>
<article>
    <front>
        <article-meta>
            <article-title>Test Article Title</article-title>
            <abstract>
                <p>This is a test abstract with some content.</p>
            </abstract>
        </article-meta>
        <journal-meta>
            <journal-title>Test Journal</journal-title>
        </journal-meta>
    </front>
    <body>
        <sec>
            <title>Introduction</title>
            <p>Some content here.</p>
        </sec>
    </body>
    <back>
        <ref-list>
            <ref id="ref1">
                <element-citation>Test reference</element-citation>
            </ref>
        </ref-list>
    </back>
</article>"""

    @pytest.fixture
    def minimal_xml(self):
        """Minimal valid XML (only article-title)."""
        return """<?xml version="1.0"?>
<article>
    <article-meta>
        <article-title>Minimal Article</article-title>
    </article-meta>
</article>"""

    def test_valid_xml(self, validator, valid_xml):
        """Test validation of complete valid XML."""
        is_valid, metadata, error = validator.validate(valid_xml, "PMC123")

        assert is_valid is True
        assert error is None
        assert metadata["identifier"] == "PMC123"
        assert metadata["size"] > 0
        assert "article-title" in metadata["found_elements"]
        assert "journal-title" in metadata["found_elements"]
        assert "abstract" in metadata["found_elements"]
        assert len(metadata["missing_elements"]) == 0
        assert metadata["quality_score"] > 0.6

    def test_minimal_xml(self, validator, minimal_xml):
        """Test validation of minimal XML (only article-title)."""
        is_valid, metadata, error = validator.validate(minimal_xml, "PMC456")

        assert is_valid is True  # Passes because article-title exists
        assert error is None
        assert "article-title" in metadata["found_elements"]
        assert "journal-title" in metadata["missing_elements"]
        assert "abstract" in metadata["missing_elements"]
        assert metadata["quality_score"] < 0.6  # Lower quality

    def test_missing_article_title(self, validator):
        """Test validation fails without article-title."""
        xml = """<?xml version="1.0"?>
<article>
    <abstract><p>Abstract only</p></abstract>
</article>"""

        is_valid, metadata, error = validator.validate(xml, "PMC789")

        assert is_valid is False
        assert "article-title" in error
        assert "article-title" not in metadata["found_elements"]

    def test_invalid_xml_syntax(self, validator):
        """Test validation fails with malformed XML."""
        xml = """<?xml version="1.0"?>
<article>
    <article-title>Unclosed tag
</article>"""

        is_valid, metadata, error = validator.validate(xml, "PMC999")

        assert is_valid is False
        assert "parse error" in error.lower()

    def test_no_xml_declaration(self, validator):
        """Test validation fails without XML declaration."""
        xml = """<article><article-title>No declaration</article-title></article>"""

        is_valid, metadata, error = validator.validate(xml, "PMC111")

        assert is_valid is False
        assert "XML declaration" in error

    def test_too_small_xml(self):
        """Test validation fails with tiny XML."""
        validator = XMLValidator(min_xml_size=100)  # Higher threshold for this test
        xml = """<?xml version="1.0"?><a/>"""

        is_valid, metadata, error = validator.validate(xml, "PMC222")

        assert is_valid is False
        assert "too small" in error.lower()
        assert metadata["size"] < 100

    def test_quality_score_calculation(self, validator):
        """Test quality score calculation."""
        # High quality: large size, all elements, figures/tables/refs
        rich_xml = """<?xml version="1.0"?>
<article>
    <article-meta>
        <article-title>High Quality Article</article-title>
        <abstract><p>Abstract content here.</p></abstract>
    </article-meta>
    <journal-meta>
        <journal-title>Top Journal</journal-title>
    </journal-meta>
    <body>
        <fig id="fig1"><caption>Figure 1</caption></fig>
        <table-wrap id="table1"><caption>Table 1</caption></table-wrap>
        """ + ("x" * 60000) + """
    </body>
    <back>
        <ref-list>
            <ref id="ref1">Citation 1</ref>
            <ref id="ref2">Citation 2</ref>
        </ref-list>
    </back>
</article>"""

        is_valid, metadata, error = rich_xml_validation = validator.validate(
            rich_xml, "PMC_RICH"
        )

        assert is_valid is True
        assert metadata["quality_score"] > 0.8  # Should be high quality

    def test_custom_required_elements(self):
        """Test validator with custom required elements."""
        validator = XMLValidator(
            min_xml_size=50,
            required_elements=["article-title", "pub-date"]
        )

        xml = """<?xml version="1.0"?>
<article>
    <article-title>Custom Test</article-title>
    <pub-date><year>2024</year></pub-date>
</article>"""

        is_valid, metadata, error = validator.validate(xml, "CUSTOM")

        assert is_valid is True
        assert "article-title" in metadata["found_elements"]
        assert "pub-date" in metadata["found_elements"]
        # abstract not required in this case
        assert "abstract" not in metadata["missing_elements"]


class TestPDFValidator:
    """Tests for PDFValidator."""

    @pytest.fixture
    def validator(self):
        """Create PDFValidator instance."""
        # Use smaller thresholds for tests
        return PDFValidator(min_pdf_size=100, max_pdf_size=104857600)

    @pytest.fixture
    def valid_pdf(self):
        """Valid minimal PDF content."""
        # Minimal valid PDF structure
        pdf = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>
endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
trailer
<< /Size 4 /Root 1 0 R >>
startxref
190
%%EOF"""
        return pdf

    def test_valid_pdf(self, validator, valid_pdf):
        """Test validation of valid PDF."""
        is_valid, metadata, error = validator.validate(valid_pdf, "arxiv_123")

        assert is_valid is True
        assert error is None
        assert metadata["identifier"] == "arxiv_123"
        assert metadata["size"] > validator.min_pdf_size
        assert metadata["pdf_version"] == "1.4"
        assert metadata["encrypted"] is False
        assert "sha256" in metadata
        assert len(metadata["sha256"]) == 64  # SHA256 hex length

    def test_pdf_version_detection(self, validator):
        """Test PDF version is detected correctly."""
        pdf_15 = b"%PDF-1.5\n" + b"x" * 20000 + b"\n%%EOF"

        is_valid, metadata, error = validator.validate(pdf_15, "test")

        assert is_valid is True
        assert metadata["pdf_version"] == "1.5"

    def test_too_small_pdf(self):
        """Test validation fails with tiny PDF."""
        validator = PDFValidator(min_pdf_size=1000)  # Higher threshold for this test
        pdf = b"%PDF-1.4\n%%EOF"

        is_valid, metadata, error = validator.validate(pdf, "tiny")

        assert is_valid is False
        assert "too small" in error.lower()

    def test_too_large_pdf(self, validator):
        """Test validation fails with huge PDF."""
        # 101MB PDF (over limit)
        huge_pdf = b"%PDF-1.4\n" + b"x" * 105000000

        is_valid, metadata, error = validator.validate(huge_pdf, "huge")

        assert is_valid is False
        assert "too large" in error.lower()

    def test_missing_pdf_header(self):
        """Test validation fails without %PDF header."""
        validator = PDFValidator(min_pdf_size=20)  # Small threshold
        not_pdf = b"This is not a PDF file\n%%EOF" + b"x" * 100  # Make it big enough

        is_valid, metadata, error = validator.validate(not_pdf, "fake")

        assert is_valid is False
        assert "PDF header" in error or "%PDF" in error

    def test_missing_eof_marker(self, validator):
        """Test validation fails without %%EOF."""
        truncated = b"%PDF-1.4\n" + b"x" * 20000  # No EOF

        is_valid, metadata, error = validator.validate(truncated, "truncated")

        assert is_valid is False
        assert "EOF" in error or "truncated" in error.lower()

    def test_encrypted_pdf_warning(self, validator, caplog):
        """Test encrypted PDF is detected."""
        encrypted = (
            b"%PDF-1.4\n"
            + b"/Encrypt << /Filter /Standard >>\n"
            + b"x" * 20000
            + b"\n%%EOF"
        )

        is_valid, metadata, error = validator.validate(encrypted, "encrypted")

        assert is_valid is True  # Still valid
        assert metadata["encrypted"] is True
        # Check log warning
        assert any("encrypted" in record.message.lower() for record in caplog.records)

    def test_sha256_hash(self, validator, valid_pdf):
        """Test SHA256 hash is calculated correctly."""
        is_valid, metadata, error = validator.validate(valid_pdf, "hash_test")

        expected_hash = hashlib.sha256(valid_pdf).hexdigest()
        assert metadata["sha256"] == expected_hash


class TestContentValidator:
    """Tests for ContentValidator (unified interface)."""

    @pytest.fixture
    def validator(self):
        """Create ContentValidator instance."""
        # Use smaller thresholds for tests
        return ContentValidator(min_xml_size=50, min_pdf_size=100)

    def test_validate_xml_through_unified_interface(self, validator):
        """Test XML validation through ContentValidator."""
        xml = """<?xml version="1.0"?>
<article>
    <article-title>Unified Test</article-title>
    <journal-title>Test Journal</journal-title>
    <abstract><p>Abstract</p></abstract>
</article>"""

        is_valid, metadata, error = validator.validate_xml(xml, "PMC_UNIFIED")

        assert is_valid is True
        assert metadata["identifier"] == "PMC_UNIFIED"

    def test_validate_pdf_through_unified_interface(self, validator):
        """Test PDF validation through ContentValidator."""
        pdf = b"%PDF-1.4\n" + b"x" * 20000 + b"\n%%EOF"

        is_valid, metadata, error = validator.validate_pdf(pdf, "arxiv_unified")

        assert is_valid is True
        assert metadata["identifier"] == "arxiv_unified"

    def test_validate_and_report_xml(self, validator):
        """Test validate_and_report for XML."""
        xml = """<?xml version="1.0"?>
<article>
    <article-title>Report Test</article-title>
    <abstract><p>Abstract</p></abstract>
</article>""".encode("utf-8")

        is_valid, report = validator.validate_and_report(xml, "xml", "PMC_REPORT")

        assert is_valid is True
        assert report["valid"] is True
        assert report["content_type"] == "xml"
        assert report["identifier"] == "PMC_REPORT"
        assert "quality_score" in report
        assert "error" not in report

    def test_validate_and_report_pdf(self, validator):
        """Test validate_and_report for PDF."""
        pdf = b"%PDF-1.4\n" + b"x" * 20000 + b"\n%%EOF"

        is_valid, report = validator.validate_and_report(pdf, "pdf", "arxiv_report")

        assert is_valid is True
        assert report["valid"] is True
        assert report["content_type"] == "pdf"
        assert report["pdf_version"] == "1.4"
        assert "error" not in report

    def test_validate_and_report_invalid_utf8(self, validator):
        """Test validate_and_report with invalid UTF-8 XML."""
        invalid_xml = b"\xff\xfe<?xml"  # Invalid UTF-8

        is_valid, report = validator.validate_and_report(
            invalid_xml, "xml", "BAD_ENCODING"
        )

        assert is_valid is False
        assert report["valid"] is False
        assert "UTF-8" in report["error"]

    def test_validate_and_report_unknown_type(self, validator):
        """Test validate_and_report with unknown content type."""
        content = b"some content"

        is_valid, report = validator.validate_and_report(content, "unknown", "TEST")

        assert is_valid is False
        assert report["valid"] is False
        assert "Unknown content type" in report["error"]


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_validate_xml_file(self, tmp_path):
        """Test validate_xml_file function."""
        xml_file = tmp_path / "test.xml"
        xml_content = """<?xml version="1.0"?>
<article>
    <article-title>File Test</article-title>
    <journal-title>Test Journal</journal-title>
    <abstract><p>Abstract</p></abstract>
</article>"""
        xml_file.write_text(xml_content)

        # Use lower threshold for test
        is_valid, report = validate_xml_file(xml_file, min_xml_size=50)

        assert is_valid is True
        assert report["file"] == str(xml_file)
        assert "article-title" in report["found_elements"]

    def test_validate_pdf_file(self, tmp_path):
        """Test validate_pdf_file function."""
        pdf_file = tmp_path / "test.pdf"
        pdf_content = b"%PDF-1.4\n" + b"x" * 20000 + b"\n%%EOF"
        pdf_file.write_bytes(pdf_content)

        is_valid, report = validate_pdf_file(pdf_file)

        assert is_valid is True
        assert report["file"] == str(pdf_file)
        assert report["pdf_version"] == "1.4"


# Integration test with real files
@pytest.mark.integration
class TestRealFileValidation:
    """Integration tests with real downloaded files."""

    def test_validate_real_pmc_xml(self):
        """Test validation of real PMC XML files (if they exist)."""
        xml_dir = Path("data/fulltext/xml/pmc")

        if not xml_dir.exists():
            pytest.skip("PMC XML files not downloaded")

        xml_files = list(xml_dir.glob("*.nxml"))
        if not xml_files:
            pytest.skip("No PMC XML files found")

        validator = XMLValidator()
        results = []

        for xml_file in xml_files:
            with open(xml_file, "r", encoding="utf-8") as f:
                xml_content = f.read()

            is_valid, metadata, error = validator.validate(xml_content, xml_file.stem)
            results.append((xml_file.name, is_valid, metadata.get("quality_score", 0)))

        # At least one should be valid
        assert any(valid for _, valid, _ in results)

        # Print results
        for name, valid, quality in results:
            print(f"{name}: valid={valid}, quality={quality:.2f}")

    def test_validate_real_pdfs(self):
        """Test validation of real PDF files (if they exist)."""
        pdf_dir = Path("data/fulltext/pdf/arxiv")

        if not pdf_dir.exists():
            pytest.skip("PDF files not downloaded")

        pdf_files = list(pdf_dir.glob("*.pdf"))
        if not pdf_files:
            pytest.skip("No PDF files found")

        validator = PDFValidator()
        results = []

        for pdf_file in pdf_files:
            with open(pdf_file, "rb") as f:
                pdf_content = f.read()

            is_valid, metadata, error = validator.validate(pdf_content, pdf_file.stem)
            results.append(
                (pdf_file.name, is_valid, metadata.get("size", 0) / 1024 / 1024)
            )

        # All should be valid
        assert all(valid for _, valid, _ in results)

        # Print results
        for name, valid, size_mb in results:
            print(f"{name}: valid={valid}, size={size_mb:.1f}MB")
