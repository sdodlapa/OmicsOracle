"""
Tests for SearchAgent with semantic search integration.

Run with:
    pytest tests/agents/test_search_agent_semantic.py -v
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from omics_oracle_v2.agents.context import AgentContext
from omics_oracle_v2.agents.models.search import SearchInput
from omics_oracle_v2.agents.search_agent import SearchAgent
from omics_oracle_v2.core.config import GEOSettings, RankingConfig, Settings


class TestSearchAgentSemanticIntegration:
    """Test SearchAgent with semantic search enabled."""

    @pytest.fixture
    def settings(self):
        """Create test settings."""
        return Settings(
            geo=GEOSettings(cache_dir="data/cache"),
            ranking=RankingConfig(),
        )

    @pytest.fixture
    def mock_geo_client(self):
        """Create mock GEO client."""
        mock = MagicMock()

        # Mock search results
        search_result = Mock()
        search_result.total_found = 10
        search_result.geo_ids = ["GSE1", "GSE2", "GSE3"]
        mock.search.return_value = search_result

        # Mock metadata
        def get_metadata(geo_id):
            metadata = Mock()
            metadata.accession = geo_id
            metadata.title = f"Dataset {geo_id}"
            metadata.summary = f"Summary for {geo_id}"
            metadata.organism = "Homo sapiens"
            metadata.sample_count = 50
            metadata.platform = "Illumina"
            metadata.pubmed_id = None
            metadata.submission_date = None
            return metadata

        mock.get_metadata.side_effect = get_metadata
        return mock

    @pytest.fixture
    def mock_semantic_pipeline(self):
        """Create mock semantic search pipeline."""
        from omics_oracle_v2.lib.search.advanced import SearchResult

        mock = MagicMock()

        # Mock search results
        def mock_search(query, top_k=10, return_answer=False):
            return SearchResult(
                query=query,
                expanded_query=f"{query} (expanded)",
                results=[
                    {
                        "id": "GSE100",
                        "text": "Semantic result 1",
                        "metadata": {
                            "id": "GSE100",
                            "title": "Semantic Dataset 1",
                            "summary": "Semantic summary 1",
                            "organism": "Homo sapiens",
                            "sample_count": 100,
                        },
                        "score": 0.95,
                        "semantic_score": 0.90,
                        "keyword_score": 0.05,
                    },
                    {
                        "id": "GSE101",
                        "text": "Semantic result 2",
                        "metadata": {
                            "id": "GSE101",
                            "title": "Semantic Dataset 2",
                            "summary": "Semantic summary 2",
                            "organism": "Mus musculus",
                            "sample_count": 50,
                        },
                        "score": 0.85,
                        "semantic_score": 0.80,
                        "keyword_score": 0.05,
                    },
                ],
                reranked_results=None,
                answer=None,
                citations=[],
                confidence=0.9,
                total_time_ms=100.0,
                cache_hit=False,
            )

        mock.search.side_effect = mock_search

        # Mock vector DB
        mock.vector_db = MagicMock()
        mock.vector_db.size.return_value = 1000
        mock.vector_db.load = MagicMock()

        return mock

    def test_initialization_with_semantic(self, settings):
        """Test agent initialization with semantic search enabled."""
        agent = SearchAgent(settings, enable_semantic=True)

        assert agent._enable_semantic is True
        assert agent._semantic_pipeline is None  # Not initialized until resources init
        assert agent._semantic_index_loaded is False

    def test_initialization_without_semantic(self, settings):
        """Test agent initialization without semantic search."""
        agent = SearchAgent(settings, enable_semantic=False)

        assert agent._enable_semantic is False
        assert agent._semantic_pipeline is None

    @patch("omics_oracle_v2.agents.search_agent.GEOClient")
    @patch("omics_oracle_v2.agents.search_agent.AdvancedSearchPipeline")
    def test_initialize_resources_with_semantic(
        self, mock_pipeline_class, mock_geo_class, settings, mock_semantic_pipeline, tmp_path
    ):
        """Test resource initialization with semantic search."""
        # Setup mocks
        mock_geo_class.return_value = MagicMock()
        mock_pipeline_class.return_value = mock_semantic_pipeline

        # Create dummy index file
        index_path = tmp_path / "data" / "vector_db"
        index_path.mkdir(parents=True)
        (index_path / "geo_index.faiss").touch()

        with patch("omics_oracle_v2.agents.search_agent.Path") as mock_path:
            mock_path.return_value.exists.return_value = True
            mock_path.return_value = index_path / "geo_index.faiss"

            agent = SearchAgent(settings, enable_semantic=True)
            agent._initialize_resources()

            assert agent._semantic_pipeline is not None
            assert mock_pipeline_class.called

    @patch("omics_oracle_v2.agents.search_agent.GEOClient")
    @patch("omics_oracle_v2.agents.search_agent.AdvancedSearchPipeline")
    def test_semantic_search_fallback(self, mock_pipeline_class, mock_geo_class, settings, mock_geo_client):
        """Test fallback to keyword search when semantic index not available."""
        # Setup mocks
        mock_geo_class.return_value = mock_geo_client
        mock_pipeline_class.return_value = MagicMock()

        # No index file available
        with patch("omics_oracle_v2.agents.search_agent.Path") as mock_path:
            mock_path.return_value.exists.return_value = False

            agent = SearchAgent(settings, enable_semantic=True)
            agent._initialize_resources()

            # Should initialize pipeline but not load index
            assert agent._semantic_index_loaded is False

            # Execute search - should fall back to keyword
            input_data = SearchInput(search_terms=["cancer", "RNA-seq"], max_results=10)

            result = agent.execute(input_data)

            # Should use keyword search (GEO client)
            assert mock_geo_client.search.called
            assert result.total_found > 0
            assert "search_mode" in result.filters_applied
            assert result.filters_applied["search_mode"] == "keyword"

    @patch("omics_oracle_v2.agents.search_agent.GEOClient")
    @patch("omics_oracle_v2.agents.search_agent.AdvancedSearchPipeline")
    def test_semantic_search_execution(
        self,
        mock_pipeline_class,
        mock_geo_class,
        settings,
        mock_semantic_pipeline,
        tmp_path,
    ):
        """Test semantic search execution when index is available."""
        # Setup mocks
        mock_geo_class.return_value = MagicMock()
        mock_pipeline_class.return_value = mock_semantic_pipeline

        # Create dummy index
        index_path = tmp_path / "geo_index.faiss"
        index_path.touch()

        with patch("omics_oracle_v2.agents.search_agent.Path") as mock_path:
            mock_path_instance = Mock()
            mock_path_instance.exists.return_value = True
            mock_path.return_value = mock_path_instance

            agent = SearchAgent(settings, enable_semantic=True)
            agent._initialize_resources()
            agent._semantic_index_loaded = True  # Force loaded state

            # Execute search
            input_data = SearchInput(
                search_terms=["cancer", "RNA-seq"],
                original_query="cancer RNA-seq studies",
                max_results=10,
            )

            result = agent.execute(input_data)

            # Should use semantic search
            assert mock_semantic_pipeline.search.called
            assert len(result.datasets) > 0
            assert "search_mode" in result.filters_applied
            assert result.filters_applied["search_mode"] == "semantic"

    def test_enable_semantic_search_runtime(self, settings):
        """Test enabling semantic search at runtime."""
        agent = SearchAgent(settings, enable_semantic=False)

        assert not agent._enable_semantic

        # Enable at runtime
        with patch.object(agent, "_initialize_semantic_search") as mock_init:
            agent.enable_semantic_search(True)

            assert agent._enable_semantic
            assert mock_init.called

        # Disable again
        agent.enable_semantic_search(False)
        assert not agent._enable_semantic

    def test_is_semantic_search_available(self, settings):
        """Test checking semantic search availability."""
        agent = SearchAgent(settings, enable_semantic=False)

        # Not enabled
        assert not agent.is_semantic_search_available()

        # Enabled but not loaded
        agent._enable_semantic = True
        agent._semantic_index_loaded = False
        assert not agent.is_semantic_search_available()

        # Enabled and loaded
        agent._semantic_index_loaded = True
        assert agent.is_semantic_search_available()

    @patch("omics_oracle_v2.agents.search_agent.GEOClient")
    @patch("omics_oracle_v2.agents.search_agent.AdvancedSearchPipeline")
    def test_semantic_filters_application(
        self, mock_pipeline_class, mock_geo_class, settings, mock_semantic_pipeline, mock_geo_client
    ):
        """Test that filters are correctly applied to semantic results."""
        mock_pipeline_class.return_value = mock_semantic_pipeline
        mock_geo_class.return_value = mock_geo_client

        agent = SearchAgent(settings, enable_semantic=True)
        agent._semantic_pipeline = mock_semantic_pipeline
        agent._semantic_index_loaded = True
        agent._geo_client = mock_geo_client

        # Execute search with filters
        input_data = SearchInput(
            search_terms=["cancer"],
            original_query="cancer studies",
            max_results=10,
            min_samples=75,  # Should filter out GSE101 (50 samples)
            organism="Homo sapiens",  # Should filter out Mus musculus
        )
        context = AgentContext(agent_name="test_search_agent")

        # Mock _run_async to avoid async complexity
        agent._run_async = lambda x: x

        result = agent._process(input_data, context)

        # Should have filtered results
        assert len(result.datasets) == 1  # Only GSE100 matches both filters
        assert result.datasets[0].accession == "GSE100"

    @patch("omics_oracle_v2.agents.search_agent.GEOClient")
    def test_cleanup_resources_with_semantic(self, mock_geo_class, settings):
        """Test resource cleanup with semantic search."""
        mock_geo_class.return_value = MagicMock()

        agent = SearchAgent(settings, enable_semantic=True)
        agent._semantic_pipeline = MagicMock()
        agent._semantic_index_loaded = True

        agent._cleanup_resources()

        assert agent._semantic_pipeline is None
        assert agent._semantic_index_loaded is False


class TestSemanticSearchMetrics:
    """Test metrics tracking for semantic search."""

    @patch("omics_oracle_v2.agents.search_agent.AdvancedSearchPipeline")
    def test_semantic_metrics_tracked(self, settings, mock_geo_client, mock_semantic_pipeline):
        """Test that semantic search metrics are tracked."""
        # TODO: Implement metrics tracking test when async execution is simplified
        pass
