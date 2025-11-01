"""
Tests for ML features module.

Tests:
- Feature extraction
- Feature array conversion
- Batch processing
- Edge cases
"""

from omics_oracle_v2.lib.ml.features import FeatureExtractor
from omics_oracle_v2.lib.search_engines.citations.models import Publication


class TestFeatureExtractor:
    """Test feature extraction."""

    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = FeatureExtractor()

        self.sample_pub = Publication(
            pmid="12345678",
            title="Machine learning in biomedical research: A review",
            authors="Smith J, Johnson A, Williams B",
            year=2022,
            abstract="This paper reviews machine learning applications in biomedical research.",
            journal="Nature Reviews",
            doi="10.1038/test",
        )

    def test_extract_temporal_features(self):
        """Test temporal feature extraction."""
        features = self.extractor.extract_features(self.sample_pub)

        assert "publication_year" in features
        assert features["publication_year"] == 2022
        assert "years_since_publication" in features
        assert features["years_since_publication"] >= 0
        assert "is_recent" in features
        assert isinstance(features["is_recent"], int)

    def test_extract_author_features(self):
        """Test author feature extraction."""
        features = self.extractor.extract_features(self.sample_pub)

        assert "num_authors" in features
        assert features["num_authors"] == 3
        assert "has_multiple_authors" in features
        assert features["has_multiple_authors"] == 1

    def test_extract_content_features(self):
        """Test content feature extraction."""
        features = self.extractor.extract_features(self.sample_pub)

        assert "title_length" in features
        assert features["title_length"] > 0
        assert "abstract_length" in features
        assert features["abstract_length"] > 0
        assert "has_abstract" in features
        assert features["has_abstract"] == 1

    def test_extract_metadata_features(self):
        """Test metadata feature extraction."""
        features = self.extractor.extract_features(self.sample_pub)

        assert "has_doi" in features
        assert features["has_doi"] == 1
        assert "has_pmid" in features
        assert features["has_pmid"] == 1
        assert "has_journal" in features
        assert features["has_journal"] == 1

    def test_missing_data_handling(self):
        """Test feature extraction with missing data."""
        minimal_pub = Publication(
            pmid="87654321",
            title="Test",
            year=2020,
        )

        features = self.extractor.extract_features(minimal_pub)

        # Should handle missing fields gracefully
        assert features["num_authors"] == 0
        assert features["has_abstract"] == 0
        assert features["has_journal"] == 0
        assert features["has_doi"] == 0

    def test_features_to_array(self):
        """Test conversion of features to array."""
        features = self.extractor.extract_features(self.sample_pub)
        feature_names = sorted(features.keys())

        array = self.extractor.features_to_array(features, feature_names)

        assert array.shape[0] == len(feature_names)
        assert array.dtype == "float32"

    def test_batch_extraction(self):
        """Test batch feature extraction."""
        pubs = [
            self.sample_pub,
            Publication(
                pmid="11111111",
                title="Another paper",
                authors="Doe J",
                year=2023,
            ),
        ]

        features_list = self.extractor.extract_features_batch(pubs)

        assert len(features_list) == 2
        assert all(isinstance(f, dict) for f in features_list)

    def test_get_feature_names(self):
        """Test getting all feature names."""
        names = self.extractor.get_feature_names()

        assert len(names) > 0
        assert all(isinstance(n, str) for n in names)
        assert "publication_year" in names
        assert "num_authors" in names

    def test_get_feature_importance_names(self):
        """Test getting human-readable feature names."""
        readable = self.extractor.get_feature_importance_names()

        assert isinstance(readable, dict)
        assert "publication_year" in readable
        assert readable["publication_year"] == "Publication Year"
