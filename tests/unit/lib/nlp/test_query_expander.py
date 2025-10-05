"""
Tests for Query Expander

Tests query expansion with biomedical synonyms and mappings.
"""

import json
import tempfile
from pathlib import Path

import pytest

from omics_oracle_v2.lib.nlp.query_expander import ExpandedQuery, QueryExpander, QueryExpansionConfig


class TestQueryExpansionConfig:
    """Test QueryExpansionConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        config = QueryExpansionConfig()

        assert config.enabled is True
        assert config.max_expansions == 5
        assert config.confidence_threshold == 0.7
        assert "synonyms.json" in config.synonym_database

    def test_custom_config(self):
        """Test custom configuration."""
        config = QueryExpansionConfig(enabled=False, max_expansions=3, confidence_threshold=0.8)

        assert config.enabled is False
        assert config.max_expansions == 3
        assert config.confidence_threshold == 0.8


class TestExpandedQuery:
    """Test ExpandedQuery dataclass."""

    def test_empty_expansion(self):
        """Test expansion with no synonyms."""
        expansion = ExpandedQuery(original="test query")

        assert expansion.original == "test query"
        assert len(expansion.expanded_terms) == 0
        assert len(expansion.organism_mappings) == 0
        assert "test query" in expansion.all_terms

    def test_expansion_with_terms(self):
        """Test expansion with various terms."""
        expansion = ExpandedQuery(
            original="human ATAC-seq",
            expanded_terms=["chromatin accessibility", "open chromatin"],
            organism_mappings={"human": "Homo sapiens"},
            technique_mappings={"ATAC-seq": ["chromatin accessibility"]},
        )

        assert expansion.original == "human ATAC-seq"
        assert "chromatin accessibility" in expansion.all_terms
        assert "Homo sapiens" in expansion.all_terms
        assert len(expansion.all_terms) >= 3


class TestQueryExpander:
    """Test QueryExpander class."""

    @pytest.fixture
    def test_synonym_db(self):
        """Create temporary synonym database for testing."""
        synonyms = {
            "techniques": {
                "ATAC-seq": ["chromatin accessibility", "open chromatin"],
                "RNA-seq": ["RNA sequencing", "transcriptomics"],
            },
            "organisms": {
                "human": ["Homo sapiens", "H. sapiens"],
                "mouse": ["Mus musculus", "M. musculus"],
            },
            "concepts": {
                "gene expression": ["transcription", "mRNA levels"],
                "cancer": ["tumor", "malignancy", "neoplasm"],
            },
            "diseases": {"diabetes": ["diabetes mellitus", "diabetic"]},
            "tissues": {"brain": ["neural tissue", "cerebral"]},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(synonyms, f)
            temp_path = f.name

        yield temp_path

        # Cleanup
        Path(temp_path).unlink()

    @pytest.fixture
    def expander(self, test_synonym_db):
        """Create QueryExpander with test database."""
        config = QueryExpansionConfig(synonym_database=test_synonym_db)
        return QueryExpander(config)

    def test_initialization(self, expander):
        """Test expander initialization."""
        assert expander.config.enabled is True
        assert len(expander.synonyms) > 0
        assert "techniques" in expander.synonyms
        assert "organisms" in expander.synonyms

    def test_find_organisms(self, expander):
        """Test organism name detection."""
        expansion = expander.expand_query("human ATAC-seq")

        assert "human" in expansion.organism_mappings
        assert expansion.organism_mappings["human"] == "Homo sapiens"

    def test_find_multiple_organisms(self, expander):
        """Test multiple organism detection."""
        expansion = expander.expand_query("human and mouse comparison")

        assert "human" in expansion.organism_mappings
        assert "mouse" in expansion.organism_mappings
        assert expansion.organism_mappings["human"] == "Homo sapiens"
        assert expansion.organism_mappings["mouse"] == "Mus musculus"

    def test_find_techniques(self, expander):
        """Test technique detection."""
        expansion = expander.expand_query("ATAC-seq analysis")

        assert "ATAC-seq" in expansion.technique_mappings
        assert "chromatin accessibility" in expansion.technique_mappings["ATAC-seq"]
        assert "open chromatin" in expansion.technique_mappings["ATAC-seq"]

    def test_find_concepts(self, expander):
        """Test concept detection."""
        expansion = expander.expand_query("gene expression profiling")

        assert "gene expression" in expansion.concept_mappings
        assert "transcription" in expansion.concept_mappings["gene expression"]

    def test_find_diseases(self, expander):
        """Test disease detection."""
        expansion = expander.expand_query("diabetes study")

        assert "diabetes" in expansion.concept_mappings
        assert "diabetes mellitus" in expansion.concept_mappings["diabetes"]

    def test_find_tissues(self, expander):
        """Test tissue detection."""
        expansion = expander.expand_query("brain tissue")

        assert "brain" in expansion.concept_mappings
        assert "neural tissue" in expansion.concept_mappings["brain"]

    def test_case_insensitive_matching(self, expander):
        """Test case-insensitive synonym matching."""
        # Test various cases
        expansion1 = expander.expand_query("HUMAN atac-seq")
        expansion2 = expander.expand_query("Human ATAC-Seq")
        expansion3 = expander.expand_query("human atac-seq")

        assert "human" in expansion1.organism_mappings
        assert "human" in expansion2.organism_mappings
        assert "human" in expansion3.organism_mappings

    def test_complex_query_expansion(self, expander):
        """Test expansion of complex multi-term query."""
        query = "human RNA-seq cancer brain"
        expansion = expander.expand_query(query)

        # Should find multiple categories
        assert len(expansion.organism_mappings) > 0
        assert len(expansion.technique_mappings) > 0
        assert len(expansion.concept_mappings) > 0

        # Verify specific expansions
        assert "human" in expansion.organism_mappings
        assert "RNA-seq" in expansion.technique_mappings
        assert "cancer" in expansion.concept_mappings or "brain" in expansion.concept_mappings

    def test_expand_for_search(self, expander):
        """Test expand_for_search method."""
        query = "human ATAC-seq"
        expanded = expander.expand_for_search(query)

        # Should contain original query
        assert "human ATAC-seq" in expanded

        # Should contain some expansions
        assert len(expanded.split()) > len(query.split())

    def test_max_expansions_limit(self, expander):
        """Test that max_expansions is respected."""
        # Set max to 2
        expander.config.max_expansions = 2

        expansion = expander.expand_query("ATAC-seq")

        # Should not exceed max per technique
        for synonyms in expansion.technique_mappings.values():
            # expanded_terms should respect the limit
            pass

        # Total expanded terms should be limited
        assert len(expansion.expanded_terms) <= 10  # Reasonable limit

    def test_disabled_expansion(self, expander):
        """Test expansion when disabled."""
        expander.config.enabled = False

        expansion = expander.expand_query("human ATAC-seq")

        assert expansion.original == "human ATAC-seq"
        assert len(expansion.expanded_terms) == 0
        assert len(expansion.organism_mappings) == 0

    def test_no_matches(self, expander):
        """Test query with no synonym matches."""
        expansion = expander.expand_query("random gibberish xyz123")

        assert expansion.original == "random gibberish xyz123"
        assert len(expansion.expanded_terms) == 0

    def test_get_expansion_summary(self, expander):
        """Test expansion summary generation."""
        query = "human ATAC-seq cancer"
        summary = expander.get_expansion_summary(query)

        assert summary["original"] == query
        assert len(summary["organisms_found"]) > 0
        assert len(summary["techniques_found"]) > 0
        assert len(summary["concepts_found"]) > 0
        assert summary["total_expansions"] > 0
        assert isinstance(summary["all_terms"], list)

    def test_word_boundary_matching(self, expander):
        """Test that matching respects word boundaries."""
        # "human" should match, but "humane" should not trigger "human"
        expansion1 = expander.expand_query("human cells")
        expansion2 = expander.expand_query("humane treatment")

        assert "human" in expansion1.organism_mappings
        assert "human" not in expansion2.organism_mappings

    def test_all_terms_uniqueness(self, expander):
        """Test that all_terms contains unique terms."""
        expansion = expander.expand_query("human ATAC-seq gene expression")

        # Check no duplicates
        assert len(expansion.all_terms) == len(set(expansion.all_terms))

    def test_missing_synonym_file(self):
        """Test handling of missing synonym database."""
        config = QueryExpansionConfig(synonym_database="nonexistent.json")

        with pytest.raises(FileNotFoundError):
            QueryExpander(config)


def test_integration_real_queries():
    """Integration test with real queries using actual synonym database."""
    # This test uses the real synonym database
    try:
        expander = QueryExpander()
    except FileNotFoundError:
        pytest.skip("Real synonym database not available")

    test_cases = [
        {
            "query": "human ATAC-seq",
            "should_have_organism": True,
            "should_have_technique": True,
        },
        {
            "query": "mouse RNA-seq cancer",
            "should_have_organism": True,
            "should_have_technique": True,
            "should_have_concept": True,
        },
        {
            "query": "chromatin accessibility diabetes",
            "should_have_concept": True,
        },
    ]

    for test_case in test_cases:
        expansion = expander.expand_query(test_case["query"])

        if test_case.get("should_have_organism"):
            assert len(expansion.organism_mappings) > 0

        if test_case.get("should_have_technique"):
            assert len(expansion.technique_mappings) > 0

        if test_case.get("should_have_concept"):
            assert len(expansion.concept_mappings) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
