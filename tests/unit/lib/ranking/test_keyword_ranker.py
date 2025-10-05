"""
Unit tests for KeywordRanker.

Tests keyword-based relevance ranking with various scenarios:
- Title matches
- Summary matches
- Organism filtering
- Sample count bonuses
- Edge cases and boundary conditions
"""

import pytest

from omics_oracle_v2.core.config import RankingConfig
from omics_oracle_v2.lib.geo.models import GEOSeriesMetadata
from omics_oracle_v2.lib.ranking import KeywordRanker


class TestKeywordRankerBasics:
    """Test basic KeywordRanker functionality."""

    @pytest.fixture
    def config(self):
        """Default ranking configuration."""
        return RankingConfig()

    @pytest.fixture
    def ranker(self, config):
        """KeywordRanker instance."""
        return KeywordRanker(config)

    @pytest.fixture
    def sample_dataset(self):
        """Sample GEO dataset for testing."""
        return GEOSeriesMetadata(
            geo_id="GSE123456",
            title="ATAC-seq analysis of chromatin accessibility in human cells",
            summary="This study examines chromatin accessibility using ATAC-seq in human lymphocytes",
            organism="Homo sapiens",
            sample_count=120,
            platform="GPL24676",
            submission_date="2024-01-15",
            last_update_date="2024-01-20",
        )

    def test_initialization(self, config):
        """Test KeywordRanker initialization."""
        ranker = KeywordRanker(config)
        assert ranker.config == config
        assert isinstance(ranker, KeywordRanker)

    def test_explain_config(self, ranker):
        """Test configuration explanation."""
        explanation = ranker.explain_config()
        assert "Title weight: 0.40" in explanation
        assert "Summary weight: 0.30" in explanation
        assert "Organism bonus: 0.15" in explanation
        assert "Sample count bonus: 0.15" in explanation


class TestTitleMatching:
    """Test title-based relevance scoring."""

    @pytest.fixture
    def config(self):
        return RankingConfig()

    @pytest.fixture
    def ranker(self, config):
        return KeywordRanker(config)

    def test_single_title_match(self, ranker):
        """Test single keyword match in title."""
        dataset = GEOSeriesMetadata(
            geo_id="GSE001",
            title="ATAC-seq analysis",
            summary="Some summary",
            organism="Homo sapiens",
            sample_count=50,
        )

        score, reasons = ranker.calculate_relevance(dataset, ["ATAC-seq"])

        assert score > 0
        assert any("Title matches 1 search term" in r for r in reasons)
        assert score >= 0.2  # At least one match * multiplier

    def test_multiple_title_matches(self, ranker):
        """Test multiple keyword matches in title."""
        dataset = GEOSeriesMetadata(
            geo_id="GSE002",
            title="ATAC-seq chromatin accessibility analysis",
            summary="Some summary",
            organism="Homo sapiens",
            sample_count=50,
        )

        score, reasons = ranker.calculate_relevance(dataset, ["ATAC-seq", "chromatin", "accessibility"])

        assert score > 0
        assert any("Title matches 3 search term" in r for r in reasons)
        # Max title weight is 0.4
        title_component = min(0.4, 3 * 0.2)
        assert score >= title_component

    def test_case_insensitive_matching(self, ranker):
        """Test case-insensitive keyword matching."""
        dataset = GEOSeriesMetadata(
            geo_id="GSE003",
            title="atac-seq CHROMATIN Accessibility",
            summary="Some summary",
            organism="Homo sapiens",
            sample_count=50,
        )

        score1, _ = ranker.calculate_relevance(dataset, ["ATAC-SEQ"])
        score2, _ = ranker.calculate_relevance(dataset, ["atac-seq"])
        score3, _ = ranker.calculate_relevance(dataset, ["AtAc-SeQ"])

        assert score1 == score2 == score3

    def test_no_title_match(self, ranker):
        """Test when no keywords match in title."""
        dataset = GEOSeriesMetadata(
            geo_id="GSE004",
            title="RNA-seq gene expression",
            summary="Some summary",
            organism="Homo sapiens",
            sample_count=50,
        )

        score, reasons = ranker.calculate_relevance(dataset, ["ATAC-seq"])

        # Should have minimal score (just sample bonus)
        assert score > 0
        assert any("Good sample size" in r for r in reasons)

    def test_title_max_weight_cap(self, ranker):
        """Test that title score is capped at max weight."""
        dataset = GEOSeriesMetadata(
            geo_id="GSE005",
            title="ATAC ATAC ATAC ATAC ATAC",  # 5 matches
            summary="Some summary",
            organism="Homo sapiens",
            sample_count=50,
        )

        score, _ = ranker.calculate_relevance(dataset, ["ATAC"])

        # Should be capped at 0.4 (max title weight)
        assert score <= 0.4 + 0.15  # +0.15 for sample count bonus


class TestSummaryMatching:
    """Test summary-based relevance scoring."""

    @pytest.fixture
    def config(self):
        return RankingConfig()

    @pytest.fixture
    def ranker(self, config):
        return KeywordRanker(config)

    def test_single_summary_match(self, ranker):
        """Test single keyword match in summary."""
        dataset = GEOSeriesMetadata(
            geo_id="GSE006",
            title="Gene expression",
            summary="This study uses ATAC-seq to analyze chromatin",
            organism="Homo sapiens",
            sample_count=50,
        )

        score, reasons = ranker.calculate_relevance(dataset, ["ATAC-seq"])

        assert score > 0
        assert any("Summary matches 1 search term" in r for r in reasons)

    def test_summary_and_title_combined(self, ranker):
        """Test scoring when both title and summary match."""
        dataset = GEOSeriesMetadata(
            geo_id="GSE007",
            title="ATAC-seq analysis",
            summary="This study examines chromatin accessibility",
            organism="Homo sapiens",
            sample_count=50,
        )

        score, reasons = ranker.calculate_relevance(dataset, ["ATAC-seq", "chromatin"])

        assert score > 0
        assert any("Title" in r for r in reasons)
        assert any("Summary" in r for r in reasons)
        # Should have both title and summary components
        assert score >= 0.2 + 0.15  # title match + summary match


class TestOrganismMatching:
    """Test organism-based filtering and bonuses."""

    @pytest.fixture
    def config(self):
        return RankingConfig()

    @pytest.fixture
    def ranker(self, config):
        return KeywordRanker(config)

    def test_organism_match(self, ranker):
        """Test organism match bonus."""
        dataset = GEOSeriesMetadata(
            geo_id="GSE008",
            title="Gene expression",
            summary="Some summary",
            organism="Homo sapiens",
            sample_count=50,
        )

        score, reasons = ranker.calculate_relevance(dataset, ["gene"], organism="Homo sapiens")

        assert any("Organism matches" in r for r in reasons)
        # Should include organism bonus
        assert score >= 0.15

    def test_organism_no_match(self, ranker):
        """Test when organism doesn't match."""
        dataset = GEOSeriesMetadata(
            geo_id="GSE009",
            title="Gene expression",
            summary="Some summary",
            organism="Mus musculus",
            sample_count=50,
        )

        score, reasons = ranker.calculate_relevance(dataset, ["gene"], organism="Homo sapiens")

        assert not any("Organism matches" in r for r in reasons)

    def test_partial_organism_match(self, ranker):
        """Test partial organism name matching."""
        dataset = GEOSeriesMetadata(
            geo_id="GSE010",
            title="Gene expression",
            summary="Some summary",
            organism="Homo sapiens sapiens",
            sample_count=50,
        )

        score, reasons = ranker.calculate_relevance(dataset, ["gene"], organism="Homo sapiens")

        assert any("Organism matches" in r for r in reasons)


class TestSampleCountBonus:
    """Test sample count bonus scoring."""

    @pytest.fixture
    def config(self):
        return RankingConfig()

    @pytest.fixture
    def ranker(self, config):
        return KeywordRanker(config)

    def test_large_sample_count(self, ranker):
        """Test bonus for large sample count (>=100)."""
        dataset = GEOSeriesMetadata(
            geo_id="GSE011",
            title="Gene expression",
            summary="Some summary",
            organism="Homo sapiens",
            sample_count=150,
        )

        score, reasons = ranker.calculate_relevance(dataset, ["gene"])

        assert any("Large sample size" in r for r in reasons)
        assert score >= 0.15  # Full bonus

    def test_medium_sample_count(self, ranker):
        """Test bonus for medium sample count (>=50)."""
        dataset = GEOSeriesMetadata(
            geo_id="GSE012",
            title="Gene expression",
            summary="Some summary",
            organism="Homo sapiens",
            sample_count=75,
        )

        score, reasons = ranker.calculate_relevance(dataset, ["gene"])

        assert any("Good sample size" in r for r in reasons)

    def test_small_sample_count(self, ranker):
        """Test bonus for small sample count (>=10)."""
        dataset = GEOSeriesMetadata(
            geo_id="GSE013",
            title="Gene expression",
            summary="Some summary",
            organism="Homo sapiens",
            sample_count=15,
        )

        score, reasons = ranker.calculate_relevance(dataset, ["gene"])

        assert any("Adequate sample size" in r for r in reasons)

    def test_very_small_sample_count(self, ranker):
        """Test no bonus for very small sample count (<10)."""
        dataset = GEOSeriesMetadata(
            geo_id="GSE014",
            title="Gene expression",
            summary="Some summary",
            organism="Homo sapiens",
            sample_count=5,
        )

        score, reasons = ranker.calculate_relevance(dataset, ["gene"])

        assert not any("sample size" in r.lower() for r in reasons)


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.fixture
    def config(self):
        return RankingConfig()

    @pytest.fixture
    def ranker(self, config):
        return KeywordRanker(config)

    def test_empty_title(self, ranker):
        """Test dataset with empty title."""
        dataset = GEOSeriesMetadata(
            geo_id="GSE015",
            title="",
            summary="ATAC-seq analysis",
            organism="Homo sapiens",
            sample_count=50,
        )

        score, reasons = ranker.calculate_relevance(dataset, ["ATAC-seq"])

        assert score > 0  # Should still score based on summary

    def test_empty_summary(self, ranker):
        """Test dataset with empty summary."""
        dataset = GEOSeriesMetadata(
            geo_id="GSE016",
            title="ATAC-seq analysis",
            summary="",
            organism="Homo sapiens",
            sample_count=50,
        )

        score, reasons = ranker.calculate_relevance(dataset, ["ATAC-seq"])

        assert score > 0  # Should still score based on title

    def test_no_sample_count(self, ranker):
        """Test dataset with no sample count."""
        dataset = GEOSeriesMetadata(
            geo_id="GSE017",
            title="ATAC-seq analysis",
            summary="Some summary",
            organism="Homo sapiens",
            sample_count=0,
        )

        score, reasons = ranker.calculate_relevance(dataset, ["ATAC-seq"])

        assert score > 0
        assert not any("sample" in r.lower() for r in reasons)

    def test_empty_search_terms(self, ranker):
        """Test with empty search terms list."""
        dataset = GEOSeriesMetadata(
            geo_id="GSE018",
            title="ATAC-seq analysis",
            summary="Some summary",
            organism="Homo sapiens",
            sample_count=50,
        )

        score, reasons = ranker.calculate_relevance(dataset, [])

        # Should return minimal score (0.1 base + sample bonus)
        assert score >= 0.1
        assert any("General database match" in r for r in reasons)

    def test_score_normalization(self, ranker):
        """Test that scores are normalized to 0.0-1.0."""
        dataset = GEOSeriesMetadata(
            geo_id="GSE019",
            title="ATAC-seq chromatin accessibility epigenetics",
            summary="ATAC-seq chromatin accessibility epigenetics analysis",
            organism="Homo sapiens",
            sample_count=150,
        )

        score, _ = ranker.calculate_relevance(
            dataset, ["ATAC-seq", "chromatin", "accessibility", "epigenetics"], organism="Homo sapiens"
        )

        assert 0.0 <= score <= 1.0


class TestCustomConfiguration:
    """Test KeywordRanker with custom configuration."""

    def test_custom_weights(self):
        """Test ranking with custom weights."""
        config = RankingConfig(
            keyword_title_weight=0.5,
            keyword_summary_weight=0.2,
            keyword_organism_bonus=0.2,
            keyword_sample_count_bonus=0.1,
        )
        ranker = KeywordRanker(config)

        dataset = GEOSeriesMetadata(
            geo_id="GSE020",
            title="ATAC-seq analysis",
            summary="Some summary",
            organism="Homo sapiens",
            sample_count=50,
        )

        score, _ = ranker.calculate_relevance(dataset, ["ATAC-seq"])

        # Should use custom weights
        assert score > 0

    def test_custom_thresholds(self):
        """Test ranking with custom sample count thresholds."""
        config = RankingConfig(
            sample_count_large=200,
            sample_count_medium=100,
            sample_count_small=50,
        )
        ranker = KeywordRanker(config)

        dataset = GEOSeriesMetadata(
            geo_id="GSE021",
            title="Gene expression",
            summary="Some summary",
            organism="Homo sapiens",
            sample_count=150,
        )

        score, reasons = ranker.calculate_relevance(dataset, ["gene"])

        # With new thresholds, 150 is now "good" not "large"
        assert any("Good sample size" in r for r in reasons)
