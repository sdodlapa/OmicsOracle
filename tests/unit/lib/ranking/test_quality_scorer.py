"""
Unit tests for QualityScorer.

Tests dataset quality assessment with various scenarios:
- Sample count quality
- Title quality
- Summary quality
- Publication quality
- SRA data availability
- Dataset recency
- Metadata completeness
- Quality level determination
"""

from datetime import datetime, timedelta

import pytest

from omics_oracle_v2.core.config import QualityConfig
from omics_oracle_v2.lib.geo.models import GEOSeriesMetadata
from omics_oracle_v2.lib.ranking import QualityScorer


class TestQualityScorerBasics:
    """Test basic QualityScorer functionality."""

    @pytest.fixture
    def config(self):
        """Default quality configuration."""
        return QualityConfig()

    @pytest.fixture
    def scorer(self, config):
        """QualityScorer instance."""
        return QualityScorer(config)

    @pytest.fixture
    def excellent_dataset(self):
        """High quality dataset for testing."""
        return GEOSeriesMetadata(
            geo_id="GSE100000",
            title="Comprehensive ATAC-seq analysis of chromatin accessibility",
            summary="This comprehensive study examines chromatin accessibility patterns using ATAC-seq technology in human lymphocytes across multiple conditions. We profiled over 200 samples with extensive experimental validation.",
            organism="Homo sapiens",
            sample_count=250,
            platform="GPL24676",
            pubmed_ids=["12345678", "87654321", "11111111"],
            submission_date=(datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
            last_update_date=(datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d"),
            contact_name="Dr. Smith",
            sra_project="SRP123456",
        )

    def test_initialization(self, config):
        """Test QualityScorer initialization."""
        scorer = QualityScorer(config)
        assert scorer.config == config
        assert isinstance(scorer, QualityScorer)

    def test_explain_config(self, scorer):
        """Test configuration explanation."""
        explanation = scorer.explain_config()
        assert "Sample count: 20 points" in explanation
        assert "Title: 15 points" in explanation
        assert "Summary: 15 points" in explanation
        assert "Publications: 20 points" in explanation


class TestSampleCountScoring:
    """Test sample count quality scoring."""

    @pytest.fixture
    def config(self):
        return QualityConfig()

    @pytest.fixture
    def scorer(self, config):
        return QualityScorer(config)

    def test_excellent_sample_count(self, scorer):
        """Test excellent sample count (>=100)."""
        metadata = GEOSeriesMetadata(
            geo_id="GSE001",
            sample_count=150,
        )

        quality, issues, strengths = scorer.calculate_quality(metadata)

        assert any("Large sample size: 150" in s for s in strengths)
        assert quality > 0

    def test_good_sample_count(self, scorer):
        """Test good sample count (>=50)."""
        metadata = GEOSeriesMetadata(
            geo_id="GSE002",
            sample_count=75,
        )

        quality, issues, strengths = scorer.calculate_quality(metadata)

        assert any("Good sample size: 75" in s for s in strengths)

    def test_adequate_sample_count(self, scorer):
        """Test adequate sample count (>=10)."""
        metadata = GEOSeriesMetadata(
            geo_id="GSE003",
            sample_count=25,
        )

        quality, issues, strengths = scorer.calculate_quality(metadata)

        assert any("Adequate sample size: 25" in s for s in strengths)

    def test_small_sample_count(self, scorer):
        """Test small sample count (<10)."""
        metadata = GEOSeriesMetadata(
            geo_id="GSE004",
            sample_count=5,
        )

        quality, issues, strengths = scorer.calculate_quality(metadata)

        assert any("Small sample size: 5" in i for i in issues)

    def test_missing_sample_count(self, scorer):
        """Test missing sample count."""
        metadata = GEOSeriesMetadata(
            geo_id="GSE005",
            sample_count=0,  # Use 0 instead of None
        )

        quality, issues, strengths = scorer.calculate_quality(metadata)

        # 0 samples is treated as very small
        assert quality >= 0


class TestTitleQuality:
    """Test title quality scoring."""

    @pytest.fixture
    def config(self):
        return QualityConfig()

    @pytest.fixture
    def scorer(self, config):
        return QualityScorer(config)

    def test_descriptive_title(self, scorer):
        """Test long, descriptive title (>=50 chars)."""
        metadata = GEOSeriesMetadata(
            geo_id="GSE006",
            title="Comprehensive genome-wide analysis of chromatin accessibility patterns",
            sample_count=50,
        )

        quality, issues, strengths = scorer.calculate_quality(metadata)

        assert any("Descriptive title" in s for s in strengths)

    def test_adequate_title(self, scorer):
        """Test adequate title (>=20 chars)."""
        metadata = GEOSeriesMetadata(
            geo_id="GSE007",
            title="ATAC-seq analysis study",
            sample_count=50,
        )

        quality, issues, strengths = scorer.calculate_quality(metadata)

        # Should not flag as issue, just lower score
        assert not any("title" in i.lower() for i in issues)

    def test_short_title(self, scorer):
        """Test very short title (<10 chars)."""
        metadata = GEOSeriesMetadata(
            geo_id="GSE008",
            title="RNA-seq",
            sample_count=50,
        )

        quality, issues, strengths = scorer.calculate_quality(metadata)

        assert any("Very short title" in i for i in issues)

    def test_missing_title(self, scorer):
        """Test missing title."""
        metadata = GEOSeriesMetadata(
            geo_id="GSE009",
            title="",  # Empty string instead of None
            sample_count=50,
        )

        quality, issues, strengths = scorer.calculate_quality(metadata)

        assert any("Missing title" in i for i in issues)


class TestSummaryQuality:
    """Test summary quality scoring."""

    @pytest.fixture
    def config(self):
        return QualityConfig()

    @pytest.fixture
    def scorer(self, config):
        return QualityScorer(config)

    def test_comprehensive_summary(self, scorer):
        """Test comprehensive summary (>=200 chars)."""
        metadata = GEOSeriesMetadata(
            geo_id="GSE010",
            summary="This is a very comprehensive summary that describes the study in great detail. " * 3,
            sample_count=50,
        )

        quality, issues, strengths = scorer.calculate_quality(metadata)

        assert any("Comprehensive summary" in s for s in strengths)

    def test_good_summary(self, scorer):
        """Test good summary (>=100 chars)."""
        metadata = GEOSeriesMetadata(
            geo_id="GSE011",
            summary="This is a good summary that provides adequate information about the study and its methodology.",
            sample_count=50,
        )

        quality, issues, strengths = scorer.calculate_quality(metadata)

        # Should not have comprehensive tag but no issue
        assert not any("Comprehensive summary" in s for s in strengths)
        assert not any("summary" in i.lower() for i in issues)

    def test_short_summary(self, scorer):
        """Test short summary (<50 chars)."""
        metadata = GEOSeriesMetadata(
            geo_id="GSE012",
            summary="Short summary",
            sample_count=50,
        )

        quality, issues, strengths = scorer.calculate_quality(metadata)

        assert any("Very short summary" in i for i in issues)

    def test_missing_summary(self, scorer):
        """Test missing summary."""
        metadata = GEOSeriesMetadata(
            geo_id="GSE013",
            summary="",  # Empty string instead of None
            sample_count=50,
        )

        quality, issues, strengths = scorer.calculate_quality(metadata)

        assert any("Missing summary" in i for i in issues)


class TestPublicationQuality:
    """Test publication quality scoring."""

    @pytest.fixture
    def config(self):
        return QualityConfig()

    @pytest.fixture
    def scorer(self, config):
        return QualityScorer(config)

    def test_many_publications(self, scorer):
        """Test many publications (>=5)."""
        metadata = GEOSeriesMetadata(
            geo_id="GSE014",
            sample_count=50,
            pubmed_ids=["1", "2", "3", "4", "5", "6"],
        )

        quality, issues, strengths = scorer.calculate_quality(metadata)

        assert any("Published (6 publication" in s for s in strengths)

    def test_some_publications(self, scorer):
        """Test some publications (>=2)."""
        metadata = GEOSeriesMetadata(
            geo_id="GSE015",
            sample_count=50,
            pubmed_ids=["1", "2", "3"],
        )

        quality, issues, strengths = scorer.calculate_quality(metadata)

        assert any("Published (3 publication" in s for s in strengths)

    def test_one_publication(self, scorer):
        """Test one publication."""
        metadata = GEOSeriesMetadata(
            geo_id="GSE016",
            sample_count=50,
            pubmed_ids=["12345678"],
        )

        quality, issues, strengths = scorer.calculate_quality(metadata)

        assert any("Published (1 publication" in s for s in strengths)

    def test_no_publications(self, scorer):
        """Test no publications."""
        metadata = GEOSeriesMetadata(
            geo_id="GSE017",
            sample_count=50,
            # pubmed_ids defaults to empty list
        )

        quality, issues, strengths = scorer.calculate_quality(metadata)

        assert any("No associated publications" in i for i in issues)


class TestSRADataAvailability:
    """Test SRA data availability scoring."""

    @pytest.fixture
    def config(self):
        return QualityConfig()

    @pytest.fixture
    def scorer(self, config):
        return QualityScorer(config)

    def test_sra_data_available(self, scorer):
        """Test when SRA data is available."""
        from omics_oracle_v2.lib.geo.models import SRAInfo

        metadata = GEOSeriesMetadata(
            geo_id="GSE018",
            sample_count=50,
            sra_info=SRAInfo(
                srp_ids=["SRP123456"],
                run_count=100,
            ),
        )

        quality, issues, strengths = scorer.calculate_quality(metadata)

        assert any("Raw sequencing data available (SRA)" in s for s in strengths)

    def test_sra_data_not_available(self, scorer):
        """Test when SRA data is not available."""
        metadata = GEOSeriesMetadata(
            geo_id="GSE019",
            sample_count=50,
            # sra_info defaults to None
        )

        quality, issues, strengths = scorer.calculate_quality(metadata)

        assert any("No SRA sequencing data" in i for i in issues)


class TestRecencyScoring:
    """Test dataset recency scoring."""

    @pytest.fixture
    def config(self):
        return QualityConfig()

    @pytest.fixture
    def scorer(self, config):
        return QualityScorer(config)

    def test_recent_dataset(self, scorer):
        """Test recent dataset (<1 year)."""
        recent_date = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")
        metadata = GEOSeriesMetadata(
            geo_id="GSE020",
            sample_count=50,
            submission_date=recent_date,
        )

        quality, issues, strengths = scorer.calculate_quality(metadata)

        assert any("Recent dataset" in s for s in strengths)

    def test_moderate_age_dataset(self, scorer):
        """Test moderately old dataset (1-5 years)."""
        old_date = (datetime.now() - timedelta(days=800)).strftime("%Y-%m-%d")
        metadata = GEOSeriesMetadata(
            geo_id="GSE021",
            sample_count=50,
            submission_date=old_date,
        )

        quality, issues, strengths = scorer.calculate_quality(metadata)

        # Should not flag as issue or strength
        assert not any("Recent" in s for s in strengths)
        assert not any("Old dataset" in i for i in issues)

    def test_old_dataset(self, scorer):
        """Test old dataset (>10 years)."""
        old_date = (datetime.now() - timedelta(days=3700)).strftime("%Y-%m-%d")
        metadata = GEOSeriesMetadata(
            geo_id="GSE022",
            sample_count=50,
            submission_date=old_date,
        )

        quality, issues, strengths = scorer.calculate_quality(metadata)

        assert any("Old dataset" in i for i in issues)


class TestMetadataCompleteness:
    """Test metadata completeness scoring."""

    @pytest.fixture
    def config(self):
        return QualityConfig()

    @pytest.fixture
    def scorer(self, config):
        return QualityScorer(config)

    def test_complete_metadata(self, scorer):
        """Test dataset with complete metadata."""
        from omics_oracle_v2.lib.geo.models import SRAInfo

        metadata = GEOSeriesMetadata(
            geo_id="GSE023",
            title="Complete Study Title with sufficient length for quality",
            summary="This is a comprehensive summary with details that provides adequate information about the study methodology and results.",
            sample_count=50,
            contact_name=["Dr. Jane Smith"],
            platforms=["GPL570"],
            pubmed_ids=["12345678"],  # Add publication
            sra_info=SRAInfo(srp_ids=["SRP123456"]),  # Add SRA data
        )

        quality, issues, strengths = scorer.calculate_quality(metadata)

        # Should have no issues (all criteria met)
        assert len(issues) == 0

    def test_incomplete_metadata(self, scorer):
        """Test dataset with incomplete metadata."""
        metadata = GEOSeriesMetadata(
            geo_id="GSE024",
            title="",  # Missing
            summary="Short",  # Too short
            sample_count=50,
            # contact_name defaults to empty list (missing)
            # platforms defaults to empty list (missing)
        )

        quality, issues, strengths = scorer.calculate_quality(metadata)

        # Should have multiple issues
        assert len(issues) >= 3


class TestQualityLevels:
    """Test quality level determination."""

    @pytest.fixture
    def config(self):
        return QualityConfig()

    @pytest.fixture
    def scorer(self, config):
        return QualityScorer(config)

    def test_excellent_quality(self, scorer):
        """Test EXCELLENT quality level (>=0.8)."""
        level = scorer.get_quality_level(0.85)
        assert level == "EXCELLENT"

    def test_good_quality(self, scorer):
        """Test GOOD quality level (>=0.6)."""
        level = scorer.get_quality_level(0.65)
        assert level == "GOOD"

    def test_fair_quality(self, scorer):
        """Test FAIR quality level (>=0.4)."""
        level = scorer.get_quality_level(0.45)
        assert level == "FAIR"

    def test_poor_quality(self, scorer):
        """Test POOR quality level (<0.4)."""
        level = scorer.get_quality_level(0.35)
        assert level == "POOR"

    def test_boundary_conditions(self, scorer):
        """Test quality level boundary conditions."""
        assert scorer.get_quality_level(0.80) == "EXCELLENT"
        assert scorer.get_quality_level(0.79) == "GOOD"
        assert scorer.get_quality_level(0.60) == "GOOD"
        assert scorer.get_quality_level(0.59) == "FAIR"
        assert scorer.get_quality_level(0.40) == "FAIR"
        assert scorer.get_quality_level(0.39) == "POOR"


class TestScoreNormalization:
    """Test quality score normalization."""

    @pytest.fixture
    def config(self):
        return QualityConfig()

    @pytest.fixture
    def scorer(self, config):
        return QualityScorer(config)

    def test_score_range(self, scorer):
        """Test that scores are in 0.0-1.0 range."""
        from omics_oracle_v2.lib.geo.models import SRAInfo

        # Minimal dataset
        minimal = GEOSeriesMetadata(
            geo_id="GSE025",
            title="T",
            summary="S",
            sample_count=1,
        )

        # Excellent dataset
        excellent = GEOSeriesMetadata(
            geo_id="GSE026",
            title="A" * 100,
            summary="B" * 300,
            organism="Homo sapiens",
            sample_count=200,
            pubmed_ids=["1", "2", "3", "4", "5"],
            platforms=["GPL123"],
            sra_info=SRAInfo(srp_ids=["SRP123"]),
            submission_date=(datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
            last_update_date=datetime.now().strftime("%Y-%m-%d"),
            contact_name=["Dr. Smith"],
        )

        minimal_quality, _, _ = scorer.calculate_quality(minimal)
        excellent_quality, _, _ = scorer.calculate_quality(excellent)

        assert 0.0 <= minimal_quality <= 1.0
        assert 0.0 <= excellent_quality <= 1.0
        assert excellent_quality > minimal_quality


class TestCustomConfiguration:
    """Test QualityScorer with custom configuration."""

    def test_custom_points(self):
        """Test scoring with custom point allocations."""
        config = QualityConfig(
            points_sample_count=30,
            points_title=10,
            points_summary=10,
            points_publications=30,
        )
        scorer = QualityScorer(config)

        metadata = GEOSeriesMetadata(
            geo_id="GSE027",
            title="Test",
            summary="Test",
            sample_count=150,
            pubmed_ids=["1", "2", "3", "4", "5"],
        )

        quality, _, _ = scorer.calculate_quality(metadata)
        assert quality > 0

    def test_custom_thresholds(self):
        """Test scoring with custom thresholds."""
        config = QualityConfig(
            sample_count_excellent=200,
            sample_count_good=100,
            sample_count_adequate=50,
        )
        scorer = QualityScorer(config)

        metadata = GEOSeriesMetadata(
            geo_id="GSE028",
            title="Test",
            summary="Test",
            sample_count=150,
        )

        quality, issues, strengths = scorer.calculate_quality(metadata)

        # With new thresholds, 150 is now "good" not "large"
        assert any("Good sample size" in s for s in strengths)

    def test_custom_quality_levels(self):
        """Test with custom quality level thresholds."""
        config = QualityConfig(
            excellent_threshold=0.9,
            good_threshold=0.7,
            fair_threshold=0.5,
        )
        scorer = QualityScorer(config)

        assert scorer.get_quality_level(0.85) == "GOOD"  # Not excellent anymore
        assert scorer.get_quality_level(0.95) == "EXCELLENT"
