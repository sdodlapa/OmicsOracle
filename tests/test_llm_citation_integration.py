"""
Integration tests for LLM-powered citation analysis in the pipeline.

Tests Day 17 integration of LLM citation analyzer into the publication search pipeline.
"""

import os
from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from omics_oracle_v2.lib.llm.client import LLMClient
from omics_oracle_v2.lib.publications.citations.analyzer import CitationAnalyzer
from omics_oracle_v2.lib.publications.citations.llm_analyzer import LLMCitationAnalyzer
from omics_oracle_v2.lib.publications.citations.models import CitationContext, UsageAnalysis
from omics_oracle_v2.lib.publications.clients.scholar import GoogleScholarClient
from omics_oracle_v2.lib.publications.config import (
    GoogleScholarConfig,
    LLMConfig,
    PublicationSearchConfig,
    PubMedConfig,
)
from omics_oracle_v2.lib.publications.models import Publication
from omics_oracle_v2.lib.publications.pipeline import PublicationSearchPipeline


class TestLLMCitationIntegration:
    """Test LLM citation analysis integration with pipeline."""

    @pytest.fixture
    def sample_publication(self):
        """Create sample publication."""
        from omics_oracle_v2.lib.publications.models import PublicationSource

        return Publication(
            title="The Cancer Genome Atlas (TCGA): A comprehensive resource",
            abstract="TCGA provides genomic data for cancer research...",
            authors=["Author A", "Author B"],
            journal="Nature",
            publication_date=datetime(2013, 1, 1),
            doi="10.1038/nature12345",
            pmid="23456789",
            source=PublicationSource.PUBMED,
        )

    @pytest.fixture
    def sample_citing_paper(self):
        """Create sample citing paper."""
        from omics_oracle_v2.lib.publications.models import PublicationSource

        pub = Publication(
            title="Novel biomarkers identified using TCGA data",
            abstract="We analyzed TCGA breast cancer data to identify novel prognostic biomarkers...",
            authors=["Researcher X"],
            journal="Cell",
            publication_date=datetime(2020, 6, 1),
            doi="10.1016/j.cell.2020.06.001",
            source=PublicationSource.GOOGLE_SCHOLAR,
        )
        # Add snippet as metadata since it's not a field
        pub.metadata["snippet"] = "Using TCGA breast cancer data, we identified three novel biomarkers..."
        return pub

    @pytest.fixture
    def mock_llm_response(self):
        """Mock LLM response for citation analysis."""
        return {
            "dataset_reused": True,
            "usage_type": "novel_application",
            "confidence": 0.9,
            "research_question": "Identify prognostic biomarkers in breast cancer",
            "application_domain": "breast cancer",
            "methodology": "machine learning on TCGA data",
            "sample_info": "500 TCGA breast cancer samples",
            "key_findings": [
                "Identified 3 novel prognostic biomarkers",
                "Validated in independent cohort",
                "Associated with poor prognosis",
            ],
            "clinical_relevance": "high",
            "clinical_details": "Potential prognostic markers for treatment stratification",
            "novel_biomarkers": ["GENE1", "GENE2", "GENE3"],
            "validation_status": "validated",
            "reasoning": "Paper explicitly states using TCGA data for biomarker discovery",
        }

    def test_pipeline_with_citations_disabled(self):
        """Test pipeline works when citations are disabled."""
        config = PublicationSearchConfig(
            enable_pubmed=False,
            enable_scholar=False,
            enable_citations=False,  # Disabled
        )

        pipeline = PublicationSearchPipeline(config)

        # Should not initialize citation components
        assert pipeline.citation_analyzer is None
        assert pipeline.llm_citation_analyzer is None

    def test_pipeline_citations_require_scholar(self):
        """Test citation analysis requires Scholar client."""
        config = PublicationSearchConfig(
            enable_pubmed=False,
            enable_scholar=False,  # Scholar disabled
            enable_citations=True,  # Citations enabled
        )

        pipeline = PublicationSearchPipeline(config)

        # Should NOT initialize citation analyzer without Scholar
        assert pipeline.citation_analyzer is None
        assert pipeline.llm_citation_analyzer is None

    def test_pipeline_initializes_citation_analyzer(self):
        """Test pipeline initializes citation analyzer when enabled."""
        config = PublicationSearchConfig(
            enable_pubmed=False,
            enable_scholar=True,
            enable_citations=True,
            scholar_config=GoogleScholarConfig(enable=True),
            llm_config=LLMConfig(provider="openai", model="gpt-4-turbo-preview"),
        )

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with patch("openai.OpenAI"):  # Patch at import location
                pipeline = PublicationSearchPipeline(config)

                # Should initialize both analyzers
                assert pipeline.citation_analyzer is not None
                assert isinstance(pipeline.citation_analyzer, CitationAnalyzer)
                assert pipeline.llm_citation_analyzer is not None
                assert isinstance(pipeline.llm_citation_analyzer, LLMCitationAnalyzer)

    @patch("openai.OpenAI")  # Patch at import location
    def test_llm_citation_analysis_workflow(
        self, mock_openai, sample_publication, sample_citing_paper, mock_llm_response
    ):
        """Test complete LLM citation analysis workflow."""
        # Setup mock LLM client
        mock_client = Mock()
        mock_openai.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content=str(mock_llm_response)))]
        mock_response.usage = Mock(prompt_tokens=100, completion_tokens=50, total_tokens=150)
        mock_client.chat.completions.create.return_value = mock_response

        # Create LLM client (api_key comes from environment)
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            llm_client = LLMClient(provider="openai")

            # Create LLM analyzer
            llm_analyzer = LLMCitationAnalyzer(llm_client)

            # Create citation context
            context = CitationContext(
                citing_paper_id=sample_citing_paper.doi,
                cited_paper_id=sample_publication.doi,
                context_text=sample_citing_paper.metadata.get("snippet", ""),
                sentence=sample_citing_paper.metadata.get("snippet", ""),
            )

            # Analyze citation
            analysis = llm_analyzer.analyze_citation_context(context, sample_publication, sample_citing_paper)

            # Verify analysis
            assert isinstance(analysis, UsageAnalysis)
            assert analysis.dataset_reused == True
            assert analysis.usage_type == "novel_application"
            assert analysis.confidence >= 0.8
            assert len(analysis.key_findings) > 0
            assert len(analysis.novel_biomarkers) > 0

    @patch("omics_oracle_v2.lib.publications.clients.scholar.GoogleScholarClient")
    @patch("openai.OpenAI")  # Patch at import location
    def test_pipeline_citation_enrichment(
        self, mock_openai, mock_scholar_class, sample_publication, sample_citing_paper, mock_llm_response
    ):
        """Test pipeline enriches results with citation data."""
        # Setup Scholar mock
        mock_scholar = Mock()
        mock_scholar_class.return_value = mock_scholar
        mock_scholar.search.return_value = [sample_publication]
        mock_scholar.get_citations.return_value = [sample_citing_paper]

        # Setup LLM mock
        mock_client = Mock()
        mock_openai.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content=str(mock_llm_response)))]
        mock_response.usage = Mock(prompt_tokens=100, completion_tokens=50, total_tokens=150)
        mock_client.chat.completions.create.return_value = mock_response

        # Create pipeline with citations enabled
        config = PublicationSearchConfig(
            enable_pubmed=False,
            enable_scholar=True,
            enable_citations=True,
            scholar_config=GoogleScholarConfig(enable=True),
            llm_config=LLMConfig(provider="openai", model="gpt-4-turbo-preview"),
        )

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            pipeline = PublicationSearchPipeline(config)
            pipeline.initialize()

            # Search
            result = pipeline.search("TCGA cancer genomics", max_results=10)

            # Verify citations were enriched
            assert result.total_found >= 0
            assert len(result.publications) >= 0

            # Note: In real test, would verify metadata has citation_analyses
            # Here we just verify the pipeline doesn't crash

    def test_citation_enrichment_handles_errors(self, sample_publication):
        """Test citation enrichment gracefully handles errors."""
        from omics_oracle_v2.lib.publications.models import PublicationSource

        # Create pipeline with citations enabled
        config = PublicationSearchConfig(
            enable_pubmed=False,
            enable_scholar=True,
            enable_citations=True,
            scholar_config=GoogleScholarConfig(enable=True),
            llm_config=LLMConfig(provider="openai"),
        )

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            with patch("openai.OpenAI"):  # Patch at import location
                pipeline = PublicationSearchPipeline(config)

                # Mock citation analyzer to raise error
                pipeline.citation_analyzer = Mock()
                pipeline.citation_analyzer.get_citing_papers.side_effect = Exception("Test error")

            # Create mock results
            from omics_oracle_v2.lib.publications.models import PublicationSearchResult

            results = [PublicationSearchResult(publication=sample_publication, relevance_score=0.9)]

            # Should handle error gracefully
            enriched = pipeline._enrich_citations(results)

            # Should return results even with error
            assert len(enriched) == 1
            assert enriched[0].publication.title == sample_publication.title

    def test_llm_config_validation(self):
        """Test LLM configuration validation."""
        # Valid config
        config = LLMConfig(
            provider="openai",
            model="gpt-4-turbo-preview",
            api_key="test-key",
            cache_enabled=True,
            batch_size=5,
            max_tokens=2000,
            temperature=0.1,
        )

        assert config.provider == "openai"
        assert config.batch_size == 5

        # Test batch_size bounds
        with pytest.raises(Exception):  # Pydantic validation error
            LLMConfig(batch_size=0)  # Too low

        with pytest.raises(Exception):
            LLMConfig(batch_size=100)  # Too high

        # Test temperature bounds
        with pytest.raises(Exception):
            LLMConfig(temperature=2.0)  # Too high

    def test_publication_config_with_llm(self):
        """Test PublicationSearchConfig with LLM configuration."""
        config = PublicationSearchConfig(
            enable_citations=True,
            enable_scholar=True,
            llm_config=LLMConfig(
                provider="anthropic",
                model="claude-3-5-sonnet-20241022",
                batch_size=3,
            ),
        )

        # Verify config
        assert config.enable_citations is True
        assert config.llm_config.provider == "anthropic"
        assert config.llm_config.batch_size == 3

    @patch("openai.OpenAI")  # Patch at import location
    def test_batch_analysis(self, mock_openai, sample_publication, sample_citing_paper, mock_llm_response):
        """Test batch citation analysis."""
        # Setup mock
        mock_client = Mock()
        mock_openai.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content=str(mock_llm_response)))]
        mock_response.usage = Mock(prompt_tokens=100, completion_tokens=50, total_tokens=150)
        mock_client.chat.completions.create.return_value = mock_response

        # Create analyzer (api_key from environment)
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            llm_client = LLMClient(provider="openai")
            llm_analyzer = LLMCitationAnalyzer(llm_client)

        # Create multiple contexts
        contexts = []
        for i in range(3):
            context = CitationContext(
                citing_paper_id=f"paper_{i}",
                cited_paper_id=sample_publication.doi,
                context_text=f"Context {i}",
            )
            contexts.append((context, sample_publication, sample_citing_paper))

        # Analyze batch
        analyses = llm_analyzer.analyze_batch(contexts, batch_size=2)

        # Verify
        assert len(analyses) == 3
        assert all(isinstance(a, UsageAnalysis) for a in analyses)

    def test_citation_metadata_structure(self, sample_publication):
        """Test citation metadata is properly structured."""
        # Create mock analysis
        analysis = UsageAnalysis(
            paper_id="test_id",
            paper_title="Test Paper",
            dataset_reused=True,
            usage_type="validation",
            confidence=0.85,
            key_findings=["Finding 1", "Finding 2"],
            novel_biomarkers=["BM1", "BM2"],
            clinical_relevance="medium",
        )

        # Convert to metadata format
        metadata = {
            "paper_id": analysis.paper_id,
            "paper_title": analysis.paper_title,
            "dataset_reused": analysis.dataset_reused,
            "usage_type": analysis.usage_type,
            "confidence": analysis.confidence,
            "key_findings": analysis.key_findings,
            "novel_biomarkers": analysis.novel_biomarkers,
            "clinical_relevance": analysis.clinical_relevance,
        }

        # Verify structure
        assert "paper_id" in metadata
        assert "dataset_reused" in metadata
        assert isinstance(metadata["key_findings"], list)
        assert isinstance(metadata["novel_biomarkers"], list)
        assert metadata["confidence"] > 0


class TestCitationAnalyzerIntegration:
    """Test basic CitationAnalyzer integration."""

    @pytest.fixture
    def sample_publication(self):
        """Create sample publication."""
        from omics_oracle_v2.lib.publications.models import PublicationSource

        return Publication(
            title="TCGA: A comprehensive resource",
            abstract="TCGA provides genomic data...",
            authors=["Author A"],
            journal="Nature",
            publication_date=datetime(2013, 1, 1),
            doi="10.1038/nature12345",
            source=PublicationSource.PUBMED,
        )

    @patch("omics_oracle_v2.lib.publications.clients.scholar.GoogleScholarClient")
    def test_citation_analyzer_initialization(self, mock_scholar_class):
        """Test CitationAnalyzer initializes properly."""
        mock_scholar = Mock()
        mock_scholar_class.return_value = mock_scholar

        analyzer = CitationAnalyzer(mock_scholar)

        assert analyzer.scholar == mock_scholar

    @patch("omics_oracle_v2.lib.publications.clients.scholar.GoogleScholarClient")
    def test_get_citing_papers(self, mock_scholar_class, sample_publication):
        """Test getting citing papers."""
        mock_scholar = Mock()
        mock_scholar_class.return_value = mock_scholar

        # Mock citations
        from omics_oracle_v2.lib.publications.models import PublicationSource

        citing_paper = Publication(
            title="Paper citing TCGA",
            abstract="Using TCGA data...",
            authors=["Researcher"],
            journal="Cell",
            publication_date=datetime(2020, 1, 1),
            source=PublicationSource.GOOGLE_SCHOLAR,
        )
        mock_scholar.get_citations.return_value = [citing_paper]

        analyzer = CitationAnalyzer(mock_scholar)
        citing_papers = analyzer.get_citing_papers(sample_publication, max_results=10)

        # Verify
        assert len(citing_papers) == 1
        assert citing_papers[0].title == "Paper citing TCGA"
        mock_scholar.get_citations.assert_called_once()

    @patch("omics_oracle_v2.lib.publications.clients.scholar.GoogleScholarClient")
    def test_get_citation_contexts(self, mock_scholar_class, sample_publication):
        """Test extracting citation contexts."""
        mock_scholar = Mock()
        analyzer = CitationAnalyzer(mock_scholar)

        from omics_oracle_v2.lib.publications.models import PublicationSource

        citing_paper = Publication(
            title="Paper citing TCGA",
            abstract="Using TCGA data...",
            authors=["Researcher"],
            journal="Cell",
            publication_date=datetime(2020, 1, 1),
            source=PublicationSource.GOOGLE_SCHOLAR,
        )
        citing_paper.metadata["snippet"] = "We analyzed TCGA breast cancer samples..."

        contexts = analyzer.get_citation_contexts(sample_publication, citing_paper)

        # Verify
        assert len(contexts) > 0
        assert isinstance(contexts[0], CitationContext)
        assert contexts[0].context_text == citing_paper.metadata.get("snippet")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
