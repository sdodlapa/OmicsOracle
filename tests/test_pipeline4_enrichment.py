"""
Comprehensive Tests for Pipeline 4 (Text Enrichment)

Tests all enrichers and the full pipeline with real PDFs.
"""

from pathlib import Path

import pytest

from omics_oracle_v2.lib.pipelines.text_enrichment import (
    BatchProcessor,
    ChatGPTFormatter,
    PDFExtractor,
    QualityScorer,
    ReferenceParser,
    SectionDetector,
    TableExtractor,
    process_pdfs_batch,
)


class TestSectionDetector:
    """Test section detection."""

    def test_basic_sections(self):
        """Test basic section detection."""
        detector = SectionDetector()

        sample_text = """
Title of Paper

Abstract
This is the abstract of the paper.

Introduction
This is the introduction section.

Methods
This describes the methodology.

Results
These are the results.

Discussion
Discussion of findings.

References
1. First reference
2. Second reference
"""

        result = detector.detect_sections(sample_text, title="Title of Paper")

        assert result.title == "Title of Paper"
        assert result.abstract is not None
        assert "introduction" in result.sections
        assert "methods" in result.sections
        assert "results" in result.sections
        assert "discussion" in result.sections
        assert "references" in result.sections

    def test_no_sections(self):
        """Test fallback when no sections detected."""
        detector = SectionDetector()

        plain_text = "This is just plain text without any section headers."

        result = detector.detect_sections(plain_text)

        assert "full_text" in result.sections
        assert result.full_text == plain_text


class TestTableExtractor:
    """Test table extraction."""

    @pytest.mark.skipif(not Path("data/test_pdfs").exists(), reason="No test PDFs available")
    def test_table_detection(self):
        """Test table caption detection."""
        extractor = TableExtractor()

        # Test with actual PDF if available
        test_pdfs = list(Path("data/test_pdfs").glob("*.pdf"))
        if test_pdfs:
            result = extractor.extract_tables(test_pdfs[0])
            assert result.method == "text_detection"
            # Tables may or may not exist
            assert isinstance(result.tables, list)


class TestReferenceParser:
    """Test reference parsing."""

    def test_reference_parsing(self):
        """Test parsing of bibliography section."""
        parser = ReferenceParser()

        ref_text = """
1. Smith J, Doe A (2020) First paper title. Nature 123:456-789. DOI: 10.1038/nature123. PMID: 12345678
2. Johnson B (2021) Second paper. Science 456:123-456.
3. Williams C et al. (2022) Third paper with DOI. Cell 789:111-222. DOI: 10.1016/cell.2022.01.001
"""

        result = parser.parse_references(ref_text)

        assert result.reference_count >= 3
        assert len(result.dois_found) >= 2
        assert len(result.pmids_found) >= 1
        assert result.references[0].number == 1


class TestChatGPTFormatter:
    """Test ChatGPT formatting."""

    def test_formatting(self):
        """Test content formatting for ChatGPT."""
        formatter = ChatGPTFormatter()

        # Create mock section data
        from omics_oracle_v2.lib.pipelines.text_enrichment.enrichers.section_detector import Section

        sections = {
            "abstract": Section("abstract", "Abstract", "This is abstract text", 0, 100),
            "introduction": Section("introduction", "Introduction", "Intro text here", 100, 200),
            "methods": Section("methods", "Methods", "Methods details", 200, 300),
        }

        formatted = formatter.format(
            text="Full paper text",
            title="Test Paper",
            sections=sections,
            metadata={"doi": "10.1234/test", "year": 2024},
        )

        assert formatted.title == "Test Paper"
        assert formatted.doi == "10.1234/test"
        assert formatted.year == 2024
        assert "abstract" in formatted.sections
        assert "introduction" in formatted.sections

        # Test prompt generation
        prompt = formatter.format_for_prompt(formatted)
        assert "# Test Paper" in prompt
        assert "DOI: 10.1234/test" in prompt


class TestPDFExtractor:
    """Test full PDF extraction with enrichment."""

    @pytest.mark.skipif(not Path("data/test_pdfs").exists(), reason="No test PDFs available")
    def test_extraction_basic(self):
        """Test basic extraction without enrichment."""
        extractor = PDFExtractor(enable_enrichment=False)

        test_pdfs = list(Path("data/test_pdfs").glob("*.pdf"))
        if not test_pdfs:
            pytest.skip("No test PDFs found")

        result = extractor.extract_text(test_pdfs[0])

        assert result is not None
        assert "full_text" in result
        assert "page_count" in result
        assert result["page_count"] > 0

    @pytest.mark.skipif(not Path("data/test_pdfs").exists(), reason="No test PDFs available")
    def test_extraction_with_enrichment(self):
        """Test extraction with all enrichers."""
        extractor = PDFExtractor(enable_enrichment=True)

        test_pdfs = list(Path("data/test_pdfs").glob("*.pdf"))
        if not test_pdfs:
            pytest.skip("No test PDFs found")

        metadata = {
            "title": "Test Paper",
            "doi": "10.1234/test",
            "pmid": "12345678",
        }

        result = extractor.extract_text(test_pdfs[0], metadata=metadata)

        assert result is not None
        assert "sections" in result
        assert "chatgpt_formatted" in result
        assert "quality_score" in result
        assert 0.0 <= result["quality_score"] <= 1.0


class TestQualityScorer:
    """Test quality scoring."""

    def test_quality_scoring(self):
        """Test quality metric calculation."""
        # Mock enriched content
        enriched = {
            "full_text": "x" * 15000,  # Good length
            "text_length": 15000,
            "sections": {
                "abstract": "Abstract text",
                "introduction": "Intro",
                "methods": "Methods",
                "results": "Results",
                "discussion": "Discussion",
            },
            "abstract": "Abstract text here",
            "table_count": 3,
            "reference_count": 25,
        }

        metrics = QualityScorer.score_content(enriched)

        assert metrics.total_score > 0.7  # Should be high quality
        assert metrics.grade in ["A", "B"]
        assert metrics.text_length_score > 0.5
        assert metrics.section_score > 0.5
        assert metrics.abstract_score > 0.5

    def test_quality_filtering(self):
        """Test filtering by quality."""
        enriched_list = [
            {
                "text_length": 15000,
                "sections": {"intro": "x"},
                "abstract": "y",
                "table_count": 2,
                "reference_count": 20,
            },
            {"text_length": 500, "sections": {}, "abstract": None, "table_count": 0, "reference_count": 0},
        ]

        filtered = QualityScorer.filter_by_quality(enriched_list, min_score=0.5)

        # Only high-quality paper should pass
        assert len(filtered) < len(enriched_list)


class TestBatchProcessor:
    """Test batch processing."""

    @pytest.mark.asyncio
    @pytest.mark.skipif(not Path("data/test_pdfs").exists(), reason="No test PDFs available")
    async def test_batch_processing(self):
        """Test batch PDF processing."""
        test_pdfs = list(Path("data/test_pdfs").glob("*.pdf"))[:5]  # Limit to 5 PDFs

        if not test_pdfs:
            pytest.skip("No test PDFs found")

        processor = BatchProcessor(max_concurrent=3, enable_enrichment=True)

        result = await processor.process_batch(test_pdfs)

        assert result.total_pdfs == len(test_pdfs)
        assert result.successful + result.failed == result.total_pdfs
        assert result.success_rate >= 0.0
        assert result.processing_time > 0.0

    @pytest.mark.asyncio
    @pytest.mark.skipif(not Path("data/test_pdfs").exists(), reason="No test PDFs available")
    async def test_batch_convenience_function(self):
        """Test convenience batch function."""
        test_pdfs = list(Path("data/test_pdfs").glob("*.pdf"))[:3]

        if not test_pdfs:
            pytest.skip("No test PDFs found")

        result = await process_pdfs_batch(test_pdfs, max_concurrent=2)

        assert result.total_pdfs == len(test_pdfs)
        assert isinstance(result.results, list)


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
