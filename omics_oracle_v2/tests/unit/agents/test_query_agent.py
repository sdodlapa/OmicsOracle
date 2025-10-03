"""Tests for Query Agent."""

import pytest

from omics_oracle_v2.agents import QueryAgent
from omics_oracle_v2.agents.base import AgentState
from omics_oracle_v2.agents.models import QueryInput, QueryIntent, QueryOutput
from omics_oracle_v2.core.config import Settings
from omics_oracle_v2.lib.nlp.models import EntityType


class TestQueryInput:
    """Test QueryInput model."""

    def test_valid_input(self):
        """Test creating valid query input."""
        query_input = QueryInput(query="Find TP53 mutations in breast cancer")

        assert query_input.query == "Find TP53 mutations in breast cancer"
        assert query_input.max_entities == 100  # default
        assert query_input.include_synonyms is True  # default

    def test_input_with_custom_params(self):
        """Test query input with custom parameters."""
        query_input = QueryInput(query="Test query", max_entities=50, include_synonyms=False)

        assert query_input.query == "Test query"
        assert query_input.max_entities == 50
        assert query_input.include_synonyms is False

    def test_empty_query_validation(self):
        """Test that empty query fails validation."""
        with pytest.raises(ValueError):
            QueryInput(query="")


class TestQueryAgent:
    """Test QueryAgent functionality."""

    @pytest.fixture
    def settings(self):
        """Create test settings."""
        return Settings()

    @pytest.fixture
    def agent(self, settings):
        """Create QueryAgent instance."""
        return QueryAgent(settings)

    def test_agent_creation(self, settings):
        """Test creating QueryAgent."""
        agent = QueryAgent(settings)

        assert agent.agent_name == "QueryAgent"
        assert agent.state == AgentState.IDLE
        assert agent._ner is None

    def test_agent_initialization(self, agent):
        """Test agent initialization."""
        agent.initialize()

        assert agent.state == AgentState.READY
        assert agent._ner is not None

    def test_input_validation_empty_query(self, agent):
        """Test validation rejects empty query."""
        agent.initialize()
        query_input = QueryInput(query="   ")  # Whitespace only

        result = agent.execute(query_input)

        assert result.success is False
        assert "empty" in result.error.lower()

    def test_input_validation_too_long(self, agent):
        """Test validation rejects overly long query."""
        agent.initialize()
        long_query = "a" * 10001  # Over 10000 char limit
        query_input = QueryInput(query=long_query)

        result = agent.execute(query_input)

        assert result.success is False
        assert "too long" in result.error.lower()

    def test_simple_query_processing(self, agent):
        """Test processing a simple query."""
        query_input = QueryInput(query="Find TP53 datasets")

        result = agent.execute(query_input)

        assert result.success is True
        assert result.state == AgentState.COMPLETED
        assert result.output is not None

        output = result.output
        assert output.original_query == "Find TP53 datasets"
        assert output.intent in QueryIntent
        assert isinstance(output.entities, list)
        assert isinstance(output.search_terms, list)
        assert isinstance(output.entity_counts, dict)
        assert 0.0 <= output.confidence <= 1.0

    def test_query_with_biomedical_entities(self, agent):
        """Test query with clear biomedical entities."""
        query_input = QueryInput(query="Find datasets about TP53 mutations in breast cancer")

        result = agent.execute(query_input)

        assert result.success is True
        output = result.output

        # Should detect search intent
        assert output.intent == QueryIntent.SEARCH

        # Should extract entities
        assert len(output.entities) > 0

        # Should have search terms
        assert len(output.search_terms) > 0

        # Should have some biomedical entities
        has_gene = output.has_entity_type(EntityType.GENE)
        has_disease = output.has_entity_type(EntityType.DISEASE)
        assert has_gene or has_disease

        # Higher confidence with specific biomedical terms
        assert output.confidence > 0.5

    def test_intent_detection_search(self, agent):
        """Test detecting search intent."""
        query_input = QueryInput(query="Find datasets with TP53")

        result = agent.execute(query_input)

        assert result.success is True
        assert result.output.intent == QueryIntent.SEARCH

    def test_intent_detection_analyze(self, agent):
        """Test detecting analyze intent."""
        query_input = QueryInput(query="Analyze expression patterns in GSE12345")

        result = agent.execute(query_input)

        assert result.success is True
        assert result.output.intent == QueryIntent.ANALYZE

    def test_intent_detection_summarize(self, agent):
        """Test detecting summarize intent."""
        query_input = QueryInput(query="Provide a summary of TP53 research")

        result = agent.execute(query_input)

        assert result.success is True
        assert result.output.intent == QueryIntent.SUMMARIZE

    def test_intent_detection_compare(self, agent):
        """Test detecting compare intent."""
        query_input = QueryInput(query="Compare TP53 and BRCA1 datasets")

        result = agent.execute(query_input)

        assert result.success is True
        assert result.output.intent == QueryIntent.COMPARE

    def test_entity_counts(self, agent):
        """Test entity counting by type."""
        query_input = QueryInput(query="Find TP53 and BRCA1 in breast cancer")

        result = agent.execute(query_input)

        assert result.success is True
        output = result.output

        # Should have entity counts
        assert isinstance(output.entity_counts, dict)
        assert len(output.entity_counts) > 0

    def test_search_terms_generation(self, agent):
        """Test search term generation."""
        query_input = QueryInput(query="TP53 mutations")

        result = agent.execute(query_input)

        assert result.success is True
        output = result.output

        # Should generate search terms
        assert len(output.search_terms) > 0

        # Search terms should be strings
        assert all(isinstance(term, str) for term in output.search_terms)

        # Should not have duplicates
        assert len(output.search_terms) == len(set(output.search_terms))

    def test_get_entities_by_type(self, agent):
        """Test filtering entities by type."""
        query_input = QueryInput(query="TP53 mutations in breast cancer")

        result = agent.execute(query_input)

        assert result.success is True
        output = result.output

        # Get genes
        genes = output.get_entities_by_type(EntityType.GENE)
        assert isinstance(genes, list)

        # Get diseases
        diseases = output.get_entities_by_type(EntityType.DISEASE)
        assert isinstance(diseases, list)

    def test_suggestions_for_vague_query(self, agent):
        """Test suggestions for vague queries."""
        query_input = QueryInput(query="cancer")

        result = agent.execute(query_input)

        assert result.success is True
        output = result.output

        # Should provide suggestions for improvement
        # May or may not have suggestions depending on entities found
        assert isinstance(output.suggestions, list)

    def test_multiple_queries(self, agent):
        """Test processing multiple queries with same agent."""
        queries = [
            "Find TP53 datasets",
            "Analyze breast cancer data",
            "Compare TP53 and BRCA1",
        ]

        for query_text in queries:
            query_input = QueryInput(query=query_text)
            result = agent.execute(query_input)

            assert result.success is True
            assert result.output.original_query == query_text

    def test_context_metrics(self, agent):
        """Test that agent sets appropriate context metrics."""
        query_input = QueryInput(query="Find TP53 in breast cancer")

        result = agent.execute(query_input)

        assert result.success is True

        # Check context has metrics
        context = agent.context
        assert context is not None
        assert "query_length" in context.metrics
        assert "detected_intent" in context.metrics
        assert "entities_extracted" in context.metrics
        assert "search_terms_generated" in context.metrics
        assert "confidence" in context.metrics

    def test_cleanup(self, agent):
        """Test agent cleanup."""
        agent.initialize()
        assert agent._ner is not None

        agent.cleanup()

        assert agent.state == AgentState.IDLE
        assert agent._ner is None


class TestQueryIntent:
    """Test QueryIntent enum."""

    def test_intent_values(self):
        """Test all intent values are defined."""
        assert QueryIntent.SEARCH == "search"
        assert QueryIntent.ANALYZE == "analyze"
        assert QueryIntent.SUMMARIZE == "summarize"
        assert QueryIntent.COMPARE == "compare"
        assert QueryIntent.UNKNOWN == "unknown"


class TestQueryOutput:
    """Test QueryOutput model."""

    def test_output_creation(self):
        """Test creating query output."""
        from omics_oracle_v2.lib.nlp.models import Entity

        entities = [
            Entity(
                text="TP53",
                entity_type=EntityType.GENE,
                start=0,
                end=4,
                confidence=0.95,
            )
        ]

        output = QueryOutput(
            original_query="Find TP53",
            intent=QueryIntent.SEARCH,
            entities=entities,
            search_terms=["TP53"],
            entity_counts={"gene": 1},
            confidence=0.9,
        )

        assert output.original_query == "Find TP53"
        assert output.intent == QueryIntent.SEARCH
        assert len(output.entities) == 1
        assert output.confidence == 0.9

    def test_has_entity_type(self):
        """Test checking if output has specific entity type."""
        from omics_oracle_v2.lib.nlp.models import Entity

        entities = [
            Entity(
                text="TP53",
                entity_type=EntityType.GENE,
                start=0,
                end=4,
            )
        ]

        output = QueryOutput(
            original_query="Test",
            intent=QueryIntent.SEARCH,
            entities=entities,
            search_terms=[],
        )

        assert output.has_entity_type(EntityType.GENE) is True
        assert output.has_entity_type(EntityType.DISEASE) is False
