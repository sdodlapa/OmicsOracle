"""
Unit tests for GEO search agent + synonym expansion integration (Phase 2C).

Tests the integration of query preprocessing (NER + synonym expansion)
with the GEO SearchAgent for improved search results.
"""

from unittest.mock import Mock, patch

import pytest

from omics_oracle_v2.agents.search_agent import SearchAgent
from omics_oracle_v2.lib.nlp.models import Entity, EntityType


class TestSearchAgentPreprocessingIntegration:
    """Test query preprocessing integration in SearchAgent."""

    @pytest.fixture
    def mock_geo_client(self):
        """Create mock GEO client."""
        client = Mock()
        client.search_series = Mock(return_value=[])
        return client

    @pytest.fixture
    def search_agent(self, mock_geo_client):
        """Create SearchAgent with preprocessing enabled."""
        from omics_oracle_v2.core.config import Settings

        settings = Settings()
        with patch("omics_oracle_v2.agents.search_agent.GEOClient", return_value=mock_geo_client):
            agent = SearchAgent(
                settings=settings,
                enable_query_preprocessing=True,
                enable_semantic=False,  # Disable for focused testing
                enable_publications=False,
            )
            agent.initialize()  # Initialize resources
            yield agent
            agent.cleanup()

    @pytest.fixture
    def search_agent_no_preprocessing(self, mock_geo_client):
        """Create SearchAgent with preprocessing disabled."""
        from omics_oracle_v2.core.config import Settings

        settings = Settings()
        with patch("omics_oracle_v2.agents.search_agent.GEOClient", return_value=mock_geo_client):
            agent = SearchAgent(
                settings=settings,
                enable_query_preprocessing=False,
                enable_semantic=False,
                enable_publications=False,
            )
            agent.initialize()  # Initialize resources
            yield agent
            agent.cleanup()

    def test_preprocessing_pipeline_initialization(self, search_agent):
        """Test that preprocessing pipeline initializes correctly."""
        assert search_agent._preprocessing_pipeline is not None

        # Verify it's a PublicationSearchPipeline
        from omics_oracle_v2.lib.pipelines.publication_pipeline import PublicationSearchPipeline

        assert isinstance(search_agent._preprocessing_pipeline, PublicationSearchPipeline)

        # Verify synonym expander is loaded
        if hasattr(search_agent._preprocessing_pipeline, "_synonym_expander"):
            assert search_agent._preprocessing_pipeline._synonym_expander is not None

    def test_preprocessing_disabled(self, search_agent_no_preprocessing):
        """Test that preprocessing can be disabled."""
        assert search_agent_no_preprocessing._preprocessing_pipeline is None

    def test_build_geo_query_from_preprocessed_techniques(self, search_agent):
        """Test building GEO query with technique entities."""
        # The expanded query already contains synonyms from preprocessing
        expanded_query = "RNA-seq OR transcriptome sequencing OR RNA sequencing"
        entities_by_type = {
            EntityType.TECHNIQUE: [Entity(text="RNA-seq", entity_type=EntityType.TECHNIQUE, start=0, end=7)]
        }

        query = search_agent._build_geo_query_from_preprocessed(expanded_query, entities_by_type)

        # Should contain the expanded query (which has all synonyms)
        assert "RNA-seq" in query
        assert "transcriptome sequencing" in query
        assert "RNA sequencing" in query
        assert " OR " in query

    def test_build_geo_query_with_organism_filter(self, search_agent):
        """Test building GEO query with organism filter."""
        expanded_query = "RNA-seq"
        entities_by_type = {
            EntityType.TECHNIQUE: [Entity(text="RNA-seq", entity_type=EntityType.TECHNIQUE, start=0, end=7)],
            EntityType.ORGANISM: [
                Entity(text="Homo sapiens", entity_type=EntityType.ORGANISM, start=8, end=20)
            ],
        }

        query = search_agent._build_geo_query_from_preprocessed(expanded_query, entities_by_type)

        # Should contain organism with GEO [Organism] tag
        assert "[Organism]" in query
        assert "Homo sapiens" in query
        assert " AND " in query  # Techniques AND organism

    def test_build_geo_query_with_tissue_filter(self, search_agent):
        """Test building GEO query with tissue/cell type filter."""
        expanded_query = "RNA-seq"
        entities_by_type = {
            EntityType.TECHNIQUE: [Entity(text="RNA-seq", entity_type=EntityType.TECHNIQUE, start=0, end=7)],
            EntityType.TISSUE: [Entity(text="liver", entity_type=EntityType.TISSUE, start=8, end=13)],
        }

        query = search_agent._build_geo_query_from_preprocessed(expanded_query, entities_by_type)

        # Should contain tissue term
        assert "liver" in query
        assert " AND " in query  # Techniques AND tissue

    def test_build_geo_query_with_disease_filter(self, search_agent):
        """Test building GEO query with disease filter."""
        expanded_query = "RNA-seq"
        entities_by_type = {
            EntityType.TECHNIQUE: [Entity(text="RNA-seq", entity_type=EntityType.TECHNIQUE, start=0, end=7)],
            EntityType.DISEASE: [Entity(text="cancer", entity_type=EntityType.DISEASE, start=8, end=14)],
        }

        query = search_agent._build_geo_query_from_preprocessed(expanded_query, entities_by_type)

        # Should contain disease term
        assert "cancer" in query
        assert " AND " in query  # Techniques AND disease

    def test_build_geo_query_complex_multifilter(self, search_agent):
        """Test building GEO query with multiple entity types."""
        expanded_query = "RNA-seq OR transcriptome sequencing"
        entities_by_type = {
            EntityType.TECHNIQUE: [
                Entity(
                    text="RNA-seq",
                    entity_type=EntityType.TECHNIQUE,
                    start=0,
                    end=7,
                    metadata={"synonyms": ["transcriptome sequencing"]},
                )
            ],
            EntityType.ORGANISM: [Entity(text="mouse", entity_type=EntityType.ORGANISM, start=8, end=13)],
            EntityType.TISSUE: [Entity(text="brain", entity_type=EntityType.TISSUE, start=14, end=19)],
            EntityType.DISEASE: [
                Entity(text="Alzheimer's disease", entity_type=EntityType.DISEASE, start=20, end=39)
            ],
        }

        query = search_agent._build_geo_query_from_preprocessed(expanded_query, entities_by_type)

        # Should contain all components
        assert "RNA-seq" in query
        assert "mouse" in query or "[Organism]" in query
        assert "brain" in query
        assert "Alzheimer" in query
        assert " AND " in query

    def test_build_geo_query_no_entities_fallback(self, search_agent):
        """Test fallback when no entities are found."""
        expanded_query = "some generic search"
        entities_by_type = {}  # No entities

        query = search_agent._build_geo_query_from_preprocessed(expanded_query, entities_by_type)

        # Should return expanded query as fallback
        assert query == expanded_query

    def test_multi_word_terms_in_query(self, search_agent):
        """Test that multi-word terms are handled in query."""
        # Expanded query may or may not have quotes - that's determined by preprocessing
        expanded_query = "single-cell RNA-seq"
        entities_by_type = {
            EntityType.TECHNIQUE: [
                Entity(text="single-cell RNA-seq", entity_type=EntityType.TECHNIQUE, start=0, end=19)
            ]
        }

        query = search_agent._build_geo_query_from_preprocessed(expanded_query, entities_by_type)

        # Should contain the term (with or without quotes)
        assert "single-cell RNA-seq" in query


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
