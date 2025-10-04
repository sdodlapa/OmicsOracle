"""Tests for Search Agent."""

import pytest

from omics_oracle_v2.agents import SearchAgent
from omics_oracle_v2.agents.base import AgentState
from omics_oracle_v2.agents.models.search import RankedDataset, SearchInput, SearchOutput
from omics_oracle_v2.core.config import Settings
from omics_oracle_v2.lib.geo.models import GEOSeriesMetadata


class TestSearchInput:
    """Test SearchInput model."""

    def test_valid_input(self):
        """Test valid search input."""
        search_input = SearchInput(search_terms=["TP53", "breast cancer"], max_results=100)
        assert search_input.search_terms == ["TP53", "breast cancer"]
        assert search_input.max_results == 100

    def test_empty_search_terms(self):
        """Test that empty search terms raise error."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            SearchInput(search_terms=[])

    def test_whitespace_only_terms(self):
        """Test that whitespace-only terms are removed."""
        with pytest.raises(ValueError, match="search_terms cannot contain only empty strings"):
            SearchInput(search_terms=["  ", "\t", "\n"])

    def test_default_max_results(self):
        """Test default max_results."""
        search_input = SearchInput(search_terms=["TP53"])
        assert search_input.max_results == 50

    def test_optional_filters(self):
        """Test optional filter parameters."""
        search_input = SearchInput(
            search_terms=["TP53"],
            organism="Homo sapiens",
            study_type="Expression profiling by array",
            min_samples=10,
        )
        assert search_input.organism == "Homo sapiens"
        assert search_input.study_type == "Expression profiling by array"
        assert search_input.min_samples == 10


class TestSearchAgent:
    """Test SearchAgent functionality."""

    @pytest.fixture
    def settings(self):
        """Create test settings."""
        settings = Settings()
        # Configure GEO client email (required for NCBI API)
        settings.geo.ncbi_email = "test@example.com"
        # Disable SSL verification for tests (may have cert issues)
        settings.geo.verify_ssl = False
        return settings

    @pytest.fixture
    def agent(self, settings):
        """Create SearchAgent instance."""
        return SearchAgent(settings)

    def test_agent_initialization(self, agent):
        """Test agent can be initialized."""
        assert agent is not None
        assert agent.state == AgentState.IDLE

    def test_simple_search(self, agent):
        """Test basic search execution."""
        search_input = SearchInput(search_terms=["TP53"], max_results=10)
        result = agent.execute(search_input)

        assert result.success is True
        assert result.output is not None
        assert isinstance(result.output, SearchOutput)
        assert len(result.output.datasets) > 0
        assert result.output.total_found >= len(result.output.datasets)

    def test_multi_term_search(self, agent):
        """Test search with multiple terms."""
        search_input = SearchInput(search_terms=["TP53", "breast cancer"], max_results=20)
        result = agent.execute(search_input)

        assert result.success is True
        assert len(result.output.search_terms_used) == 2
        assert "TP53" in result.output.search_terms_used
        assert "breast cancer" in result.output.search_terms_used

    def test_organism_filter(self, agent):
        """Test filtering by organism."""
        search_input = SearchInput(search_terms=["gene expression"], organism="Homo sapiens", max_results=10)
        result = agent.execute(search_input)

        assert result.success is True
        assert result.output.filters_applied.get("organism") == "Homo sapiens"

    def test_min_samples_filter(self, agent):
        """Test filtering by minimum samples."""
        search_input = SearchInput(search_terms=["cancer"], min_samples=50, max_results=10)
        result = agent.execute(search_input)

        assert result.success is True
        # All returned datasets should have >= 50 samples
        for ranked_dataset in result.output.datasets:
            if ranked_dataset.dataset.sample_count:
                assert ranked_dataset.dataset.sample_count >= 50

    def test_study_type_filter(self, agent):
        """Test filtering by study type."""
        search_input = SearchInput(
            search_terms=["cancer"], study_type="Expression profiling by array", max_results=10
        )
        result = agent.execute(search_input)

        assert result.success is True
        assert result.output.filters_applied.get("study_type") == "Expression profiling by array"

    def test_relevance_ranking(self, agent):
        """Test that results are ranked by relevance."""
        search_input = SearchInput(search_terms=["TP53", "mutation"], max_results=20)
        result = agent.execute(search_input)

        assert result.success is True
        datasets = result.output.datasets

        if len(datasets) > 1:
            # Check scores are in descending order
            scores = [d.relevance_score for d in datasets]
            assert scores == sorted(scores, reverse=True)

            # Check all scores are between 0.0 and 1.0
            for score in scores:
                assert 0.0 <= score <= 1.0

    def test_match_reasons(self, agent):
        """Test that match reasons are provided."""
        search_input = SearchInput(search_terms=["cancer"], max_results=5)
        result = agent.execute(search_input)

        assert result.success is True
        # Each ranked dataset should have match reasons
        for ranked_dataset in result.output.datasets:
            assert len(ranked_dataset.match_reasons) > 0

    def test_get_top_datasets(self, agent):
        """Test getting top N datasets."""
        search_input = SearchInput(search_terms=["gene"], max_results=20)
        result = agent.execute(search_input)

        assert result.success is True
        top_5 = result.output.get_top_datasets(5)

        assert len(top_5) <= 5
        # Should be sorted by score
        if len(top_5) > 1:
            scores = [d.relevance_score for d in top_5]
            assert scores == sorted(scores, reverse=True)

    def test_filter_by_score(self, agent):
        """Test filtering datasets by minimum score."""
        search_input = SearchInput(search_terms=["cancer"], max_results=20)
        result = agent.execute(search_input)

        assert result.success is True
        high_quality = result.output.filter_by_score(0.5)

        # All results should have score >= 0.5
        for dataset in high_quality:
            assert dataset.relevance_score >= 0.5

    def test_empty_results_handling(self, agent):
        """Test handling of searches with no results."""
        # Use very specific/unlikely search terms
        search_input = SearchInput(search_terms=["xyzabcnonexistentterm123456"], max_results=10)
        result = agent.execute(search_input)

        assert result.success is True
        # May have 0 results or very few
        assert result.output.total_found >= 0

    def test_context_metrics(self, agent):
        """Test that context metrics are recorded."""
        search_input = SearchInput(search_terms=["TP53"], max_results=10)
        result = agent.execute(search_input)

        assert result.success is True
        assert result.metadata.get("search_terms_count") == 1
        assert "raw_results_count" in result.metadata
        assert "filtered_results_count" in result.metadata

    def test_agent_cleanup(self, agent):
        """Test agent initialization and resource management."""
        search_input = SearchInput(search_terms=["cancer"], max_results=5)
        result = agent.execute(search_input)

        assert result.success is True
        # Agent maintains resources after execution
        assert agent._geo_client is not None
        # Verify GEO client is properly initialized
        assert agent._geo_client.ncbi_client is not None


class TestRankedDataset:
    """Test RankedDataset model."""

    def test_create_ranked_dataset(self):
        """Test creating a ranked dataset."""
        dataset = GEOSeriesMetadata(
            geo_id="GSE123456",
            title="Test Dataset",
            summary="Test summary",
            organism="Homo sapiens",
            sample_count=100,
        )
        ranked = RankedDataset(
            dataset=dataset, relevance_score=0.85, match_reasons=["Title match", "Organism match"]
        )

        assert ranked.dataset.geo_id == "GSE123456"
        assert ranked.relevance_score == 0.85
        assert len(ranked.match_reasons) == 2


class TestSearchOutput:
    """Test SearchOutput model."""

    def test_create_search_output(self):
        """Test creating search output."""
        dataset1 = GEOSeriesMetadata(
            geo_id="GSE1",
            title="Dataset 1",
            summary="Summary 1",
            organism="Homo sapiens",
            sample_count=50,
        )
        dataset2 = GEOSeriesMetadata(
            geo_id="GSE2",
            title="Dataset 2",
            summary="Summary 2",
            organism="Mus musculus",
            sample_count=100,
        )

        ranked1 = RankedDataset(dataset=dataset1, relevance_score=0.8, match_reasons=["Title match"])
        ranked2 = RankedDataset(dataset=dataset2, relevance_score=0.9, match_reasons=["Summary match"])

        output = SearchOutput(
            datasets=[ranked1, ranked2],
            total_found=2,
            search_terms_used=["cancer"],
            filters_applied={"organism": "Homo sapiens"},
        )

        assert len(output.datasets) == 2
        assert output.total_found == 2
        assert output.search_terms_used == ["cancer"]
        assert output.filters_applied["organism"] == "Homo sapiens"
