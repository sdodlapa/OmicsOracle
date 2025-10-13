"""
Unit tests for RAG pipeline.

Tests cover:
- Configuration
- Context extraction
- Prompt building
- LLM integration (mocked)
- Answer validation
- Citation formatting
- Caching
- Error handling
"""

import tempfile

import pytest

from omics_oracle_v2.lib.rag.pipeline import (
    Citation,
    LLMProvider,
    MockLLMClient,
    RAGConfig,
    RAGPipeline,
    RAGResponse,
)


class TestRAGConfig:
    """Test RAG configuration."""

    def test_default_config(self):
        """Test default configuration values."""
        config = RAGConfig()

        assert config.llm_provider == LLMProvider.OPENAI
        assert config.model_name == "gpt-4o-mini"
        assert config.temperature == 0.3
        assert config.max_tokens == 1000
        assert config.max_context_docs == 5
        assert config.max_context_tokens == 3000
        assert config.citation_style == "inline"
        assert config.cache_enabled is True

    def test_custom_config(self):
        """Test custom configuration."""
        config = RAGConfig(
            llm_provider=LLMProvider.MOCK,
            model_name="gpt-4",
            temperature=0.7,
            max_context_docs=10,
            citation_style="footnote",
            cache_enabled=False,
        )

        assert config.llm_provider == LLMProvider.MOCK
        assert config.model_name == "gpt-4"
        assert config.temperature == 0.7
        assert config.max_context_docs == 10
        assert config.citation_style == "footnote"
        assert config.cache_enabled is False


class TestCitation:
    """Test Citation class."""

    def test_citation_creation(self):
        """Test creating a citation."""
        citation = Citation(
            doc_id="GSE123",
            title="Test Study",
            score=0.95,
            excerpt="This is a test excerpt...",
            metadata={"accession": "GSE123"},
        )

        assert citation.doc_id == "GSE123"
        assert citation.title == "Test Study"
        assert citation.score == 0.95
        assert "test excerpt" in citation.excerpt
        assert citation.metadata["accession"] == "GSE123"

    def test_inline_format(self):
        """Test inline citation formatting."""
        citation = Citation(doc_id="GSE123", title="Test Study", score=0.95, excerpt="Test")

        # Without score
        formatted = citation.format("inline", include_score=False)
        assert formatted == "[GSE123]"

        # With score
        formatted = citation.format("inline", include_score=True)
        assert "[GSE123]" in formatted
        assert "0.95" in formatted

    def test_footnote_format(self):
        """Test footnote citation formatting."""
        citation = Citation(doc_id="GSE123", title="Test Study", score=0.95, excerpt="Test")

        # Without score
        formatted = citation.format("footnote", include_score=False)
        assert "[GSE123]" in formatted
        assert "Test Study" in formatted
        assert "0.95" not in formatted

        # With score
        formatted = citation.format("footnote", include_score=True)
        assert "[GSE123]" in formatted
        assert "Test Study" in formatted
        assert "0.95" in formatted


class TestRAGResponse:
    """Test RAG response."""

    def test_response_creation(self):
        """Test creating a response."""
        citations = [
            Citation("doc1", "Title 1", 0.9, "Excerpt 1"),
            Citation("doc2", "Title 2", 0.8, "Excerpt 2"),
        ]

        response = RAGResponse(
            query="What is ATAC-seq?",
            answer="ATAC-seq is a technique...",
            citations=citations,
            confidence=0.85,
            context_used=2,
            tokens_used=150,
            cached=False,
        )

        assert response.query == "What is ATAC-seq?"
        assert "ATAC-seq" in response.answer
        assert len(response.citations) == 2
        assert response.confidence == 0.85
        assert response.context_used == 2
        assert response.tokens_used == 150
        assert response.cached is False

    def test_to_dict(self):
        """Test converting response to dictionary."""
        citations = [Citation("doc1", "Title", 0.9, "Excerpt")]

        response = RAGResponse(
            query="Test query",
            answer="Test answer",
            citations=citations,
            confidence=0.9,
            context_used=1,
            tokens_used=50,
        )

        result = response.to_dict()

        assert result["query"] == "Test query"
        assert result["answer"] == "Test answer"
        assert len(result["citations"]) == 1
        assert result["confidence"] == 0.9
        assert "timestamp" in result


class TestRAGPipeline:
    """Test RAG pipeline."""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def mock_search_results(self):
        """Create mock search results."""
        return [
            {
                "id": "GSE123001",
                "text": "ATAC-seq analysis of chromatin accessibility in human T cells.",
                "score": 0.95,
                "metadata": {
                    "title": "Chromatin dynamics",
                    "accession": "GSE123001",
                    "technique": "ATAC-seq",
                },
            },
            {
                "id": "GSE123002",
                "text": "RNA-seq profiling of gene expression in cancer cells.",
                "score": 0.80,
                "metadata": {
                    "title": "Cancer transcriptomics",
                    "accession": "GSE123002",
                    "technique": "RNA-seq",
                },
            },
        ]

    def test_pipeline_initialization(self, temp_cache_dir):
        """Test pipeline initialization."""
        config = RAGConfig(llm_provider=LLMProvider.MOCK, cache_dir=temp_cache_dir)

        pipeline = RAGPipeline(config)

        assert pipeline.config.llm_provider == LLMProvider.MOCK
        assert len(pipeline._cache) == 0

    def test_extract_context(self, temp_cache_dir, mock_search_results):
        """Test context extraction from search results."""
        config = RAGConfig(llm_provider=LLMProvider.MOCK, max_context_docs=2, cache_dir=temp_cache_dir)

        pipeline = RAGPipeline(config)
        context, citations = pipeline._extract_context(mock_search_results)

        # Should extract 2 documents
        assert len(citations) == 2
        assert citations[0].doc_id == "GSE123001"
        assert citations[1].doc_id == "GSE123002"

        # Context should contain both texts
        assert "ATAC-seq" in context
        assert "RNA-seq" in context

        # Should have citation markers
        assert "[GSE123001]" in context
        assert "[GSE123002]" in context

    def test_extract_context_limit(self, temp_cache_dir, mock_search_results):
        """Test context extraction respects document limit."""
        config = RAGConfig(
            llm_provider=LLMProvider.MOCK, max_context_docs=1, cache_dir=temp_cache_dir  # Only 1 doc
        )

        pipeline = RAGPipeline(config)
        context, citations = pipeline._extract_context(mock_search_results)

        # Should only extract 1 document
        assert len(citations) == 1
        assert citations[0].doc_id == "GSE123001"

    def test_build_prompt(self, temp_cache_dir):
        """Test prompt building."""
        config = RAGConfig(llm_provider=LLMProvider.MOCK, cache_dir=temp_cache_dir)

        pipeline = RAGPipeline(config)

        query = "What is ATAC-seq?"
        context = "[GSE123] ATAC-seq is a technique for chromatin accessibility."

        prompt = pipeline._build_prompt(query, context)

        assert query in prompt
        assert context in prompt
        assert "biomedical research assistant" in prompt.lower()
        assert "cite sources" in prompt.lower()

    def test_mock_llm_client(self):
        """Test mock LLM client."""
        client = MockLLMClient()

        prompt = "What is ATAC-seq used for?"
        answer, tokens = client.generate(prompt)

        assert "ATAC-seq" in answer
        assert tokens > 0
        assert "[doc_" in answer  # Should have citations

    def test_validate_answer_good(self, temp_cache_dir):
        """Test answer validation for good answer."""
        config = RAGConfig(llm_provider=LLMProvider.MOCK, cache_dir=temp_cache_dir)

        pipeline = RAGPipeline(config)

        answer = (
            "ATAC-seq is used for chromatin accessibility [doc1] and identifies regulatory elements [doc2]."
        )
        citations = [Citation("doc1", "Study 1", 0.9, "Excerpt"), Citation("doc2", "Study 2", 0.8, "Excerpt")]

        confidence = pipeline._validate_answer(answer, citations)

        # Should have high confidence (uses citations, good length)
        assert confidence > 0.7

    def test_validate_answer_no_citations(self, temp_cache_dir):
        """Test answer validation when citations not used."""
        config = RAGConfig(llm_provider=LLMProvider.MOCK, cache_dir=temp_cache_dir, require_citations=True)

        pipeline = RAGPipeline(config)

        answer = "ATAC-seq is a useful technique for studying chromatin."
        citations = [Citation("doc1", "Study", 0.9, "Excerpt")]

        confidence = pipeline._validate_answer(answer, citations)

        # Should have lower confidence (no citations used)
        assert confidence < 0.5

    def test_validate_answer_uncertain(self, temp_cache_dir):
        """Test answer validation for uncertain answer."""
        config = RAGConfig(llm_provider=LLMProvider.MOCK, cache_dir=temp_cache_dir)

        pipeline = RAGPipeline(config)

        answer = "I don't know based on the provided context."
        citations = []

        confidence = pipeline._validate_answer(answer, citations)

        # Should have very low confidence
        assert confidence < 0.4

    def test_generate_answer(self, temp_cache_dir, mock_search_results):
        """Test generating an answer."""
        config = RAGConfig(llm_provider=LLMProvider.MOCK, cache_dir=temp_cache_dir, max_context_docs=2)

        pipeline = RAGPipeline(config)

        query = "What is ATAC-seq used for?"
        response = pipeline.generate_answer(query, mock_search_results)

        assert response.query == query
        assert len(response.answer) > 0
        assert len(response.citations) == 2
        assert response.confidence > 0
        assert response.tokens_used > 0
        assert response.cached is False

    def test_generate_answer_caching(self, temp_cache_dir, mock_search_results):
        """Test response caching."""
        config = RAGConfig(llm_provider=LLMProvider.MOCK, cache_dir=temp_cache_dir, cache_enabled=True)

        pipeline = RAGPipeline(config)

        query = "What is ATAC-seq?"

        # First call - not cached
        response1 = pipeline.generate_answer(query, mock_search_results)
        assert response1.cached is False

        # Second call - should be cached
        response2 = pipeline.generate_answer(query, mock_search_results)
        assert response2.cached is True
        assert response2.answer == response1.answer

    def test_generate_answer_cache_disabled(self, temp_cache_dir, mock_search_results):
        """Test with caching disabled."""
        config = RAGConfig(llm_provider=LLMProvider.MOCK, cache_dir=temp_cache_dir, cache_enabled=False)

        pipeline = RAGPipeline(config)

        query = "What is ATAC-seq?"

        response1 = pipeline.generate_answer(query, mock_search_results)
        response2 = pipeline.generate_answer(query, mock_search_results)

        # Both should not be cached
        assert response1.cached is False
        assert response2.cached is False

    def test_generate_answer_empty_results(self, temp_cache_dir):
        """Test with empty search results."""
        config = RAGConfig(llm_provider=LLMProvider.MOCK, cache_dir=temp_cache_dir)

        pipeline = RAGPipeline(config)

        with pytest.raises(ValueError, match="No search results"):
            pipeline.generate_answer("Test query", [])

    def test_cache_persistence(self, temp_cache_dir, mock_search_results):
        """Test cache persistence across pipeline instances."""
        config = RAGConfig(llm_provider=LLMProvider.MOCK, cache_dir=temp_cache_dir)

        # First pipeline - generate and cache
        pipeline1 = RAGPipeline(config)
        query = "What is ATAC-seq?"
        response1 = pipeline1.generate_answer(query, mock_search_results)

        # Second pipeline - should load from cache
        pipeline2 = RAGPipeline(config)
        response2 = pipeline2.generate_answer(query, mock_search_results)

        assert response2.cached is True
        assert response2.answer == response1.answer

    def test_clear_cache(self, temp_cache_dir, mock_search_results):
        """Test clearing the cache."""
        config = RAGConfig(llm_provider=LLMProvider.MOCK, cache_dir=temp_cache_dir)

        pipeline = RAGPipeline(config)

        # Generate and cache
        query = "What is ATAC-seq?"
        pipeline.generate_answer(query, mock_search_results)
        assert len(pipeline._cache) > 0

        # Clear cache
        pipeline.clear_cache()
        assert len(pipeline._cache) == 0

    def test_get_stats(self, temp_cache_dir):
        """Test getting pipeline stats."""
        config = RAGConfig(llm_provider=LLMProvider.MOCK, model_name="test-model", cache_dir=temp_cache_dir)

        pipeline = RAGPipeline(config)
        stats = pipeline.get_stats()

        assert stats["provider"] == "mock"
        assert stats["model"] == "test-model"
        assert stats["cache_size"] == 0
        assert stats["cache_enabled"] is True

    def test_different_queries_different_cache(self, temp_cache_dir, mock_search_results):
        """Test that different queries have different cache entries."""
        config = RAGConfig(llm_provider=LLMProvider.MOCK, cache_dir=temp_cache_dir)

        pipeline = RAGPipeline(config)

        # Generate two different queries
        response1 = pipeline.generate_answer("Query 1", mock_search_results)
        response2 = pipeline.generate_answer("Query 2", mock_search_results)

        # Both should not be cached on first call
        assert response1.cached is False
        assert response2.cached is False

        # Cache should have 2 entries
        assert len(pipeline._cache) == 2


class TestIntegration:
    """Integration tests (skipped by default)."""

    @pytest.mark.skip(reason="Requires OpenAI API key")
    def test_openai_integration(self, temp_cache_dir):
        """Test integration with OpenAI API."""
        config = RAGConfig(llm_provider=LLMProvider.OPENAI, cache_dir=temp_cache_dir)

        pipeline = RAGPipeline(config)

        search_results = [
            {
                "id": "GSE123",
                "text": "ATAC-seq identifies open chromatin regions.",
                "score": 0.95,
                "metadata": {"title": "ATAC-seq study"},
            }
        ]

        response = pipeline.generate_answer("What does ATAC-seq identify?", search_results)

        assert len(response.answer) > 0
        assert response.confidence > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
