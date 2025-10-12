"""
Tests for content normalizer.

This module tests the ContentNormalizer class which converts various
source formats (JATS XML, PDF, LaTeX) to a unified structure.

Author: OmicsOracle Team
Date: October 11, 2025
"""

import pytest

from omics_oracle_v2.lib.fulltext.normalizer import NORMALIZED_VERSION, ContentNormalizer


@pytest.fixture
def normalizer():
    """Create a ContentNormalizer instance."""
    return ContentNormalizer()


@pytest.fixture
def sample_jats_content():
    """Sample JATS XML content for testing."""
    return {
        "publication_id": "PMC_12345",
        "source_type": "xml",
        "cached_at": "2025-10-11T10:00:00Z",
        "content": {
            "article": {
                "front": {
                    "article-meta": {
                        "title-group": {"article-title": "CRISPR-based Gene Expression Profiling"},
                        "abstract": {
                            "p": [
                                {
                                    "#text": "This study presents a novel approach to gene expression profiling."
                                },
                                {"#text": "We demonstrate the utility of CRISPR technology."},
                            ]
                        },
                    }
                },
                "body": {
                    "sec": [
                        {
                            "@sec-type": "intro",
                            "title": "Introduction",
                            "p": [
                                {
                                    "#text": "Gene expression profiling is crucial for understanding cellular processes."
                                }
                            ],
                        },
                        {
                            "@sec-type": "methods",
                            "title": "Methods",
                            "p": [
                                {"#text": "We used CRISPR-Cas9 for targeted gene editing."},
                                {"#text": "RNA sequencing was performed using Illumina platform."},
                            ],
                        },
                        {
                            "@sec-type": "results",
                            "title": "Results",
                            "p": [{"#text": "We identified 500 differentially expressed genes."}],
                        },
                    ],
                    "table-wrap": [
                        {
                            "@id": "table1",
                            "caption": {"#text": "Differentially expressed genes"},
                            "table": "Gene | Expression | P-value",
                        }
                    ],
                    "fig": [
                        {
                            "@id": "fig1",
                            "caption": {"#text": "Gene expression heatmap"},
                            "graphic": {"@xlink:href": "fig1.png"},
                        }
                    ],
                },
                "back": {
                    "ref-list": {
                        "ref": [
                            {"mixed-citation": "Smith et al. (2024) Nature 580:123-145"},
                            {"mixed-citation": "Jones et al. (2023) Science 379:456-789"},
                        ]
                    }
                },
            }
        },
    }


@pytest.fixture
def sample_pdf_content():
    """Sample PDF content for testing."""
    return {
        "publication_id": "DOI_10.1234",
        "source_type": "pdf",
        "cached_at": "2025-10-11T10:00:00Z",
        "content": {
            "title": "Machine Learning in Genomics",
            "abstract": "This paper reviews machine learning approaches in genomics.",
            "full_text": "Machine Learning in Genomics\n\nThis paper reviews machine learning approaches...",
            "sections": {
                "introduction": "Machine learning has transformed genomics research.",
                "methods": "We analyzed 1000 genomes using deep learning.",
                "results": "Our model achieved 95% accuracy.",
            },
            "tables": [
                {"id": "table1", "caption": "Model performance", "text": "Model | Accuracy | F1-score"}
            ],
            "figures": [{"id": "fig1", "caption": "ROC curve", "file": "roc_curve.png"}],
            "references": ["Reference 1 text", "Reference 2 text"],
        },
    }


@pytest.fixture
def sample_normalized_content():
    """Sample already-normalized content."""
    return {
        "metadata": {
            "publication_id": "PMC_99999",
            "source_format": "pdf",
            "normalized_version": "1.0",
            "normalized_at": "2025-10-11T09:00:00Z",
            "cached_at": "2025-10-11T08:00:00Z",
        },
        "text": {
            "title": "Test Paper",
            "abstract": "Test abstract",
            "full_text": "Test full text",
            "sections": {},
        },
        "tables": [],
        "figures": [],
        "references": [],
        "stats": {"word_count": 100, "table_count": 0, "figure_count": 0, "reference_count": 0},
    }


class TestContentNormalizer:
    """Test ContentNormalizer class."""

    def test_normalizer_initialization(self, normalizer):
        """Test normalizer can be created."""
        assert normalizer is not None

    def test_is_normalized_detects_normalized(self, normalizer, sample_normalized_content):
        """Test that already-normalized content is detected."""
        assert normalizer._is_normalized(sample_normalized_content) is True

    def test_is_normalized_detects_non_normalized(self, normalizer, sample_jats_content):
        """Test that non-normalized content is detected."""
        assert normalizer._is_normalized(sample_jats_content) is False

    def test_normalize_already_normalized(self, normalizer, sample_normalized_content):
        """Test that normalizing already-normalized content returns it unchanged."""
        result = normalizer.normalize(sample_normalized_content)
        assert result == sample_normalized_content

    def test_normalize_jats_basic(self, normalizer, sample_jats_content):
        """Test basic JATS normalization."""
        result = normalizer.normalize(sample_jats_content)

        # Check metadata
        assert result["metadata"]["publication_id"] == "PMC_12345"
        assert result["metadata"]["source_format"] == "jats_xml"
        assert result["metadata"]["normalized_version"] == NORMALIZED_VERSION
        assert "normalized_at" in result["metadata"]

        # Check structure
        assert "text" in result
        assert "tables" in result
        assert "figures" in result
        assert "references" in result
        assert "stats" in result

    def test_normalize_jats_title(self, normalizer, sample_jats_content):
        """Test JATS title extraction."""
        result = normalizer.normalize(sample_jats_content)
        assert result["text"]["title"] == "CRISPR-based Gene Expression Profiling"

    def test_normalize_jats_abstract(self, normalizer, sample_jats_content):
        """Test JATS abstract extraction."""
        result = normalizer.normalize(sample_jats_content)
        abstract = result["text"]["abstract"]

        assert "novel approach" in abstract
        assert "CRISPR technology" in abstract

    def test_normalize_jats_sections(self, normalizer, sample_jats_content):
        """Test JATS section extraction."""
        result = normalizer.normalize(sample_jats_content)
        sections = result["text"]["sections"]

        # Check section names are normalized
        assert "introduction" in sections
        assert "methods" in sections
        assert "results" in sections

        # Check content
        assert "Gene expression profiling" in sections["introduction"]
        assert "CRISPR-Cas9" in sections["methods"]
        assert "500 differentially expressed genes" in sections["results"]

    def test_normalize_jats_tables(self, normalizer, sample_jats_content):
        """Test JATS table extraction."""
        result = normalizer.normalize(sample_jats_content)
        tables = result["tables"]

        assert len(tables) == 1
        assert tables[0]["id"] == "table1"
        assert "Differentially expressed genes" in tables[0]["caption"]

    def test_normalize_jats_figures(self, normalizer, sample_jats_content):
        """Test JATS figure extraction."""
        result = normalizer.normalize(sample_jats_content)
        figures = result["figures"]

        assert len(figures) == 1
        assert figures[0]["id"] == "fig1"
        assert "heatmap" in figures[0]["caption"]
        assert figures[0]["file"] == "fig1.png"

    def test_normalize_jats_references(self, normalizer, sample_jats_content):
        """Test JATS reference extraction."""
        result = normalizer.normalize(sample_jats_content)
        references = result["references"]

        assert len(references) == 2
        assert "Smith et al." in references[0]
        assert "Jones et al." in references[1]

    def test_normalize_jats_full_text(self, normalizer, sample_jats_content):
        """Test JATS full text building."""
        result = normalizer.normalize(sample_jats_content)
        full_text = result["text"]["full_text"]

        # Should include title, abstract, and sections
        assert "CRISPR-based" in full_text
        assert "novel approach" in full_text
        assert "Gene expression profiling" in full_text
        assert "CRISPR-Cas9" in full_text

    def test_normalize_jats_stats(self, normalizer, sample_jats_content):
        """Test JATS statistics calculation."""
        result = normalizer.normalize(sample_jats_content)
        stats = result["stats"]

        assert stats["table_count"] == 1
        assert stats["figure_count"] == 1
        assert stats["reference_count"] == 2
        assert stats["has_methods"] is True
        assert stats["has_results"] is True
        assert stats["word_count"] > 0

    def test_normalize_pdf_basic(self, normalizer, sample_pdf_content):
        """Test basic PDF normalization."""
        result = normalizer.normalize(sample_pdf_content)

        # Check metadata
        assert result["metadata"]["publication_id"] == "DOI_10.1234"
        assert result["metadata"]["source_format"] == "pdf"
        assert result["metadata"]["normalized_version"] == NORMALIZED_VERSION

        # Check structure
        assert "text" in result
        assert "tables" in result
        assert "figures" in result
        assert "references" in result
        assert "stats" in result

    def test_normalize_pdf_content(self, normalizer, sample_pdf_content):
        """Test PDF content extraction."""
        result = normalizer.normalize(sample_pdf_content)

        assert result["text"]["title"] == "Machine Learning in Genomics"
        assert "machine learning approaches" in result["text"]["abstract"]
        assert "introduction" in result["text"]["sections"]
        assert "methods" in result["text"]["sections"]

    def test_normalize_pdf_tables(self, normalizer, sample_pdf_content):
        """Test PDF table normalization."""
        result = normalizer.normalize(sample_pdf_content)
        tables = result["tables"]

        assert len(tables) == 1
        assert tables[0]["id"] == "table1"
        assert "Model performance" in tables[0]["caption"]

    def test_normalize_pdf_figures(self, normalizer, sample_pdf_content):
        """Test PDF figure normalization."""
        result = normalizer.normalize(sample_pdf_content)
        figures = result["figures"]

        assert len(figures) == 1
        assert figures[0]["id"] == "fig1"
        assert "ROC curve" in figures[0]["caption"]

    def test_normalize_section_name_variations(self, normalizer):
        """Test section name normalization handles variations."""
        assert normalizer._normalize_section_name("Introduction") == "introduction"
        assert normalizer._normalize_section_name("METHODS") == "methods"
        assert normalizer._normalize_section_name("Materials and Methods") == "methods"
        assert normalizer._normalize_section_name("Results") == "results"
        assert normalizer._normalize_section_name("Discussion") == "discussion"
        assert normalizer._normalize_section_name("Conclusions") == "conclusions"
        assert normalizer._normalize_section_name("Summary") == "conclusions"

    def test_clean_text_removes_whitespace(self, normalizer):
        """Test text cleaning removes excessive whitespace."""
        text = "  This   has    too   much    whitespace  "
        cleaned = normalizer._clean_text(text)
        assert cleaned == "This has too much whitespace"

    def test_clean_text_handles_empty(self, normalizer):
        """Test text cleaning handles empty input."""
        assert normalizer._clean_text("") == ""
        assert normalizer._clean_text(None) == ""

    def test_build_full_text(self, normalizer):
        """Test full text building from components."""
        title = "Test Title"
        abstract = "Test abstract"
        sections = {"introduction": "Intro text", "methods": "Methods text", "results": "Results text"}

        full_text = normalizer._build_full_text(title, abstract, sections)

        assert "Test Title" in full_text
        assert "Test abstract" in full_text
        assert "Intro text" in full_text
        assert "Methods text" in full_text
        assert "Results text" in full_text

    def test_calculate_stats(self, normalizer):
        """Test statistics calculation."""
        full_text = "This is a test text with multiple words."
        sections = {"methods": "Methods section", "results": "Results section"}
        tables = [{"id": "t1"}, {"id": "t2"}]
        figures = [{"id": "f1"}]
        references = ["ref1", "ref2", "ref3"]

        stats = normalizer._calculate_stats(full_text, sections, tables, figures, references)

        assert stats["word_count"] == len(full_text.split())
        assert stats["table_count"] == 2
        assert stats["figure_count"] == 1
        assert stats["reference_count"] == 3
        assert stats["has_methods"] is True
        assert stats["has_results"] is True
        assert stats["has_discussion"] is False

    def test_normalize_unknown_format(self, normalizer):
        """Test normalization of unknown format falls back to PDF."""
        content = {
            "publication_id": "TEST_123",
            "source_type": "unknown_format",
            "cached_at": "2025-10-11T10:00:00Z",
            "content": {
                "title": "Test",
                "abstract": "Test abstract",
                "full_text": "Test text",
                "sections": {},
                "tables": [],
                "figures": [],
                "references": [],
            },
        }

        result = normalizer.normalize(content)

        # Should still normalize
        assert result["metadata"]["publication_id"] == "TEST_123"
        assert "normalized_version" in result["metadata"]

    def test_normalize_idempotent(self, normalizer, sample_jats_content):
        """Test that normalizing twice gives the same result."""
        result1 = normalizer.normalize(sample_jats_content)
        result2 = normalizer.normalize(result1)

        # Should be the same (already normalized)
        assert result1 == result2

    def test_normalize_preserves_original_cache_time(self, normalizer, sample_jats_content):
        """Test that normalization preserves original cache timestamp."""
        result = normalizer.normalize(sample_jats_content)

        assert result["metadata"]["cached_at"] == sample_jats_content["cached_at"]
        # But has new normalized_at
        assert "normalized_at" in result["metadata"]


class TestNormalizerEdgeCases:
    """Test edge cases and error handling."""

    def test_jats_missing_fields(self, normalizer):
        """Test JATS normalization with missing fields."""
        minimal_jats = {
            "publication_id": "PMC_MIN",
            "source_type": "xml",
            "cached_at": "2025-10-11T10:00:00Z",
            "content": {"article": {}},  # Minimal structure
        }

        # Should not crash
        result = normalizer.normalize(minimal_jats)

        assert result["metadata"]["publication_id"] == "PMC_MIN"
        # Should have empty but valid structure
        assert "text" in result
        assert isinstance(result["tables"], list)
        assert isinstance(result["figures"], list)

    def test_pdf_missing_fields(self, normalizer):
        """Test PDF normalization with missing fields."""
        minimal_pdf = {
            "publication_id": "PDF_MIN",
            "source_type": "pdf",
            "cached_at": "2025-10-11T10:00:00Z",
            "content": {},  # Empty content
        }

        # Should not crash
        result = normalizer.normalize(minimal_pdf)

        assert result["metadata"]["publication_id"] == "PDF_MIN"
        assert "text" in result

    def test_empty_sections(self, normalizer):
        """Test handling of empty sections."""
        content = {
            "publication_id": "EMPTY",
            "source_type": "pdf",
            "cached_at": "2025-10-11T10:00:00Z",
            "content": {"sections": {}},
        }

        result = normalizer.normalize(content)

        assert result["text"]["sections"] == {}
        assert result["stats"]["has_methods"] is False

    def test_malformed_tables(self, normalizer):
        """Test handling of malformed table data."""
        content = {
            "publication_id": "BAD_TABLE",
            "source_type": "pdf",
            "cached_at": "2025-10-11T10:00:00Z",
            "content": {"tables": ["just a string", None, {"incomplete": "table"}]},
        }

        # Should handle gracefully
        result = normalizer.normalize(content)

        # Tables should be normalized or filtered
        assert isinstance(result["tables"], list)


# Integration test
@pytest.mark.asyncio
async def test_parsed_cache_integration():
    """Test integration between ParsedCache and ContentNormalizer."""
    import tempfile
    from pathlib import Path

    from omics_oracle_v2.lib.fulltext.parsed_cache import ParsedCache

    # Create temporary cache directory
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = ParsedCache(cache_dir=Path(tmpdir))

        # Save JATS content
        jats_content = {
            "title": "Test Paper",
            "abstract": "Test abstract",
            "sections": {"methods": "Test methods"},
            "tables": [],
            "figures": [],
            "references": [],
        }

        await cache.save(
            publication_id="TEST_JATS",
            content=jats_content,
            source_type="xml",
            quality_score=0.95,
        )

        # Get in normalized format
        normalized = await cache.get_normalized("TEST_JATS")

        # Should be normalized
        assert normalized is not None
        assert "normalized_version" in normalized.get("metadata", {})
        # Source format gets normalized to "jats_xml"
        assert normalized["metadata"]["source_format"] == "jats_xml"

        # Second access should use cached normalized version
        normalized2 = await cache.get_normalized("TEST_JATS")
        assert normalized2 is not None
        assert normalized2["metadata"]["normalized_version"] == normalized["metadata"]["normalized_version"]
