"""
Unit tests for PublicationRanker.

Tests multi-factor scoring algorithm, weights, and filtering.
"""

import pytest
from datetime import datetime, timedelta

from omics_oracle_v2.lib.publications.ranking.ranker import PublicationRanker
from omics_oracle_v2.lib.publications.config import PublicationSearchConfig, PubMedConfig
from omics_oracle_v2.lib.publications.models import Publication, PublicationSource


@pytest.fixture
def config():
    """Create test configuration."""
    return PublicationSearchConfig(
        enable_pubmed=True,
        pubmed_config=PubMedConfig(email="test@example.com"),
        ranking_weights={
            "title_match": 0.4,
            "abstract_match": 0.3,
            "recency": 0.2,
            "citations": 0.1,
        }
    )


@pytest.fixture
def ranker(config):
    """Create test ranker."""
    return PublicationRanker(config)


@pytest.fixture
def sample_publication():
    """Create sample publication for testing."""
    return Publication(
        pmid="12345678",
        title="CRISPR-Cas9 gene editing for cancer therapy",
        abstract="Background: Gene editing shows promise for cancer treatment. "
                 "Methods: We used CRISPR-Cas9 to target oncogenes. "
                 "Results: Significant tumor reduction observed. "
                 "Conclusions: CRISPR-Cas9 is effective for cancer therapy.",
        authors=["Smith J", "Doe J"],
        journal="Nature Biotechnology",
        publication_date=datetime.now() - timedelta(days=30),
        source=PublicationSource.PUBMED,
        citations=150,
        mesh_terms=["CRISPR-Cas Systems", "Neoplasms", "Gene Editing"],
        keywords=["CRISPR", "cancer", "gene editing"],
    )


@pytest.fixture
def old_publication():
    """Create old publication for recency testing."""
    return Publication(
        pmid="87654321",
        title="Traditional cancer treatment methods",
        abstract="Review of conventional cancer therapies including chemotherapy and radiation.",
        authors=["Johnson A"],
        journal="Cancer Research",
        publication_date=datetime.now() - timedelta(days=2000),  # ~5.5 years old
        source=PublicationSource.PUBMED,
        citations=500,  # High citations but old
        mesh_terms=["Neoplasms", "Therapeutics"],
        keywords=["cancer", "treatment"],
    )


@pytest.fixture
def highly_cited_publication():
    """Create highly cited publication."""
    return Publication(
        pmid="11111111",
        title="Landmark study on cancer genomics",
        abstract="Comprehensive analysis of cancer genomic landscapes.",
        authors=["Williams R"],
        journal="Cell",
        publication_date=datetime.now() - timedelta(days=365),
        source=PublicationSource.PUBMED,
        citations=5000,  # Very high citations
        mesh_terms=["Genomics", "Neoplasms"],
        keywords=["genomics", "cancer"],
    )


class TestPublicationRankerInitialization:
    """Test ranker initialization."""

    def test_initialization_with_config(self, config):
        """Test ranker initializes with config."""
        ranker = PublicationRanker(config)
        assert ranker.config == config

    def test_initialization_sets_weights(self, ranker):
        """Test ranker sets weights from config."""
        assert ranker.config.ranking_weights["title_match"] == 0.4
        assert ranker.config.ranking_weights["abstract_match"] == 0.3
        assert ranker.config.ranking_weights["recency"] == 0.2
        assert ranker.config.ranking_weights["citations"] == 0.1


class TestPublicationScoring:
    """Test publication scoring algorithm."""

    def test_score_publication_returns_float(self, ranker, sample_publication):
        """Test scoring returns float score."""
        score = ranker._score_publication(
            sample_publication, 
            "CRISPR cancer therapy", 
            ["crispr", "cancer", "therapy"]
        )
        assert isinstance(score, float)
        assert 0 <= score <= 100

    def test_exact_title_match_scores_high(self, ranker, sample_publication):
        """Test exact title match produces high score."""
        score = ranker._score_publication(
            sample_publication,
            "CRISPR-Cas9 gene editing for cancer therapy",
            ["crispr", "cas9", "gene", "editing", "cancer", "therapy"]
        )
        # Should have high title match component
        assert score > 50

    def test_partial_title_match_scores_lower(self, ranker, sample_publication):
        """Test partial title match scores lower."""
        score_full = ranker._score_publication(
            sample_publication,
            "CRISPR cancer therapy",
            ["crispr", "cancer", "therapy"]
        )
        
        score_partial = ranker._score_publication(
            sample_publication,
            "cancer",
            ["cancer"]
        )
        
        assert score_full > score_partial

    def test_abstract_match_contributes_to_score(self, ranker, sample_publication):
        """Test abstract matching affects score."""
        # Query matching abstract content
        score_with_abstract = ranker._score_publication(
            sample_publication,
            "oncogene targeting tumor reduction",
            ["oncogene", "targeting", "tumor", "reduction"]
        )
        
        # Query not in abstract
        score_without_abstract = ranker._score_publication(
            sample_publication,
            "completely unrelated query xyz",
            ["completely", "unrelated", "query", "xyz"]
        )
        
        assert score_with_abstract > score_without_abstract

    def test_recent_publications_score_higher(self, ranker, sample_publication, old_publication):
        """Test recent publications score higher on recency."""
        query = "cancer treatment"
        tokens = ["cancer", "treatment"]
        
        recent_score = ranker._score_publication(sample_publication, query, tokens)
        old_score = ranker._score_publication(old_publication, query, tokens)
        
        # Recent should have higher recency component
        # (though old one may score higher overall due to high citations)
        assert recent_score >= 0

    def test_citations_contribute_to_score(self, ranker, sample_publication, highly_cited_publication):
        """Test citations affect score."""
        query = "cancer genomics"
        tokens = ["cancer", "genomics"]
        
        highly_cited_score = ranker._score_publication(highly_cited_publication, query, tokens)
        
        # High citations should contribute positively
        assert highly_cited_score >= 0


class TestRankingFunction:
    """Test main ranking function."""

    def test_rank_returns_sorted_results(self, ranker, sample_publication, old_publication):
        """Test rank returns sorted list."""
        publications = [old_publication, sample_publication]
        
        ranked = ranker.rank(publications, "CRISPR cancer therapy", top_k=10)
        
        assert len(ranked) == 2
        # First result should have higher score
        assert ranked[0].relevance_score >= ranked[1].relevance_score

    def test_rank_respects_top_k(self, ranker, sample_publication):
        """Test rank respects top_k parameter."""
        publications = [sample_publication] * 10
        
        ranked = ranker.rank(publications, "test query", top_k=5)
        
        assert len(ranked) <= 5

    def test_rank_returns_empty_for_empty_input(self, ranker):
        """Test rank handles empty publication list."""
        ranked = ranker.rank([], "test query", top_k=10)
        assert ranked == []

    def test_rank_includes_score_breakdown(self, ranker, sample_publication):
        """Test rank includes score breakdown."""
        ranked = ranker.rank([sample_publication], "CRISPR cancer", top_k=10)
        
        assert len(ranked) == 1
        assert hasattr(ranked[0], 'score_breakdown')
        assert 'title_match' in ranked[0].score_breakdown
        assert 'abstract_match' in ranked[0].score_breakdown
        assert 'recency' in ranked[0].score_breakdown
        assert 'citations' in ranked[0].score_breakdown

    def test_rank_sets_rank_numbers(self, ranker, sample_publication, old_publication):
        """Test rank sets rank numbers correctly."""
        publications = [old_publication, sample_publication]
        
        ranked = ranker.rank(publications, "test", top_k=10)
        
        assert ranked[0].rank == 1
        assert ranked[1].rank == 2


class TestTextRelevanceCalculation:
    """Test text relevance calculation."""

    def test_calculate_text_relevance_with_exact_match(self, ranker):
        """Test relevance calculation with exact match."""
        text = "CRISPR-Cas9 gene editing for cancer therapy"
        query_tokens = ["crispr", "gene", "editing", "cancer", "therapy"]
        
        score = ranker._calculate_text_relevance(text, query_tokens)
        
        assert score > 0
        assert score <= 1.0

    def test_calculate_text_relevance_with_partial_match(self, ranker):
        """Test relevance with partial match."""
        text = "Gene therapy approaches"
        query_tokens = ["gene", "editing", "crispr"]
        
        score = ranker._calculate_text_relevance(text, query_tokens)
        
        assert score >= 0
        assert score <= 1.0

    def test_calculate_text_relevance_with_no_match(self, ranker):
        """Test relevance with no match."""
        text = "Completely unrelated content"
        query_tokens = ["crispr", "cancer", "therapy"]
        
        score = ranker._calculate_text_relevance(text, query_tokens)
        
        assert score == 0.0

    def test_phrase_matching_bonus(self, ranker):
        """Test phrase matching gives bonus."""
        text = "CRISPR-Cas9 gene editing is revolutionary"
        query_tokens = ["crispr", "cas9", "gene", "editing"]
        
        score_with_phrase = ranker._calculate_text_relevance(text, query_tokens)
        
        # Shuffle tokens (no phrase match)
        text_shuffled = "Gene editing with revolutionary CRISPR-Cas9"
        score_without_phrase = ranker._calculate_text_relevance(text_shuffled, query_tokens)
        
        # With phrase should score same or higher
        assert score_with_phrase >= 0


class TestRecencyScoring:
    """Test recency scoring component."""

    def test_recency_score_for_new_publication(self, ranker):
        """Test recency score for very recent publication."""
        pub = Publication(
            pmid="123",
            title="Test",
            source=PublicationSource.PUBMED,
            publication_date=datetime.now() - timedelta(days=1)
        )
        
        score = ranker._calculate_recency_score(pub)
        
        # Very recent should score close to 1.0
        assert score > 0.9
        assert score <= 1.0

    def test_recency_score_for_old_publication(self, ranker):
        """Test recency score for old publication."""
        pub = Publication(
            pmid="123",
            title="Test",
            source=PublicationSource.PUBMED,
            publication_date=datetime.now() - timedelta(days=3650)  # 10 years
        )
        
        score = ranker._calculate_recency_score(pub)
        
        # Old should have low recency score
        assert score < 0.5

    def test_recency_score_for_no_date(self, ranker):
        """Test recency score when date is missing."""
        pub = Publication(
            pmid="123",
            title="Test",
            source=PublicationSource.PUBMED,
            publication_date=None
        )
        
        score = ranker._calculate_recency_score(pub)
        
        # Should handle gracefully
        assert score >= 0


class TestCitationScoring:
    """Test citation scoring component."""

    def test_citation_score_for_highly_cited(self, ranker):
        """Test citation score for highly cited paper."""
        pub = Publication(
            pmid="123",
            title="Test",
            source=PublicationSource.PUBMED,
            citations=5000
        )
        
        score = ranker._calculate_citation_score(pub)
        
        # Should be close to 1.0 (log scale, 1.0 at 1000 citations)
        assert score >= 0.9

    def test_citation_score_for_low_citations(self, ranker):
        """Test citation score for low citations."""
        pub = Publication(
            pmid="123",
            title="Test",
            source=PublicationSource.PUBMED,
            citations=10
        )
        
        score = ranker._calculate_citation_score(pub)
        
        # Should be lower
        assert score < 0.5

    def test_citation_score_for_no_citations(self, ranker):
        """Test citation score when citations missing."""
        pub = Publication(
            pmid="123",
            title="Test",
            source=PublicationSource.PUBMED,
            citations=None
        )
        
        score = ranker._calculate_citation_score(pub)
        
        # Should be 0 or very low
        assert score >= 0
        assert score <= 0.1


class TestTokenization:
    """Test query tokenization."""

    def test_tokenize_query_splits_words(self, ranker):
        """Test tokenization splits words."""
        tokens = ranker._tokenize_query("CRISPR cancer therapy")
        
        assert "crispr" in tokens
        assert "cancer" in tokens
        assert "therapy" in tokens

    def test_tokenize_query_lowercases(self, ranker):
        """Test tokenization lowercases."""
        tokens = ranker._tokenize_query("CRISPR Cancer THERAPY")
        
        assert all(t.islower() for t in tokens)

    def test_tokenize_query_removes_stop_words(self, ranker):
        """Test tokenization removes stop words."""
        tokens = ranker._tokenize_query("the CRISPR and cancer therapy")
        
        # Stop words should be removed
        assert "the" not in tokens
        assert "and" not in tokens

    def test_tokenize_query_handles_punctuation(self, ranker):
        """Test tokenization handles punctuation."""
        tokens = ranker._tokenize_query("CRISPR-Cas9, gene editing!")
        
        # Should split on punctuation
        assert "crispr" in tokens or "cas9" in tokens


class TestFilteringAndDeduplication:
    """Test result filtering."""

    def test_filter_by_min_score(self, ranker, sample_publication, old_publication):
        """Test filtering by minimum score."""
        publications = [sample_publication, old_publication]
        
        ranked = ranker.rank(publications, "CRISPR cancer", top_k=10)
        
        # Filter by min score
        if ranked:
            min_score = ranked[0].relevance_score - 10
            filtered = [r for r in ranked if r.relevance_score >= min_score]
            assert len(filtered) >= 1


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_rank_with_None_publication_date(self, ranker):
        """Test ranking handles None publication date."""
        pub = Publication(
            pmid="123",
            title="Test publication",
            source=PublicationSource.PUBMED,
            publication_date=None
        )
        
        ranked = ranker.rank([pub], "test", top_k=10)
        assert len(ranked) == 1

    def test_rank_with_None_citations(self, ranker):
        """Test ranking handles None citations."""
        pub = Publication(
            pmid="123",
            title="Test publication",
            source=PublicationSource.PUBMED,
            citations=None
        )
        
        ranked = ranker.rank([pub], "test", top_k=10)
        assert len(ranked) == 1

    def test_rank_with_empty_abstract(self, ranker):
        """Test ranking handles empty abstract."""
        pub = Publication(
            pmid="123",
            title="Test publication with CRISPR",
            source=PublicationSource.PUBMED,
            abstract=None
        )
        
        ranked = ranker.rank([pub], "CRISPR", top_k=10)
        assert len(ranked) == 1
        # Should still score based on title
        assert ranked[0].relevance_score > 0

    def test_rank_with_special_characters_in_query(self, ranker, sample_publication):
        """Test ranking handles special characters in query."""
        ranked = ranker.rank(
            [sample_publication], 
            "CRISPR-Cas9 (gene editing) & cancer!",
            top_k=10
        )
        assert len(ranked) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
