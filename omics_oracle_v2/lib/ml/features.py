"""
Feature extraction for ML models.

Extracts features from Publication objects for:
- Citation prediction
- Trend analysis
- Recommendation systems
"""

import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np

from omics_oracle_v2.lib.publications.models import Publication

logger = logging.getLogger(__name__)


class FeatureExtractor:
    """Extract features from publications for ML models."""

    def __init__(self):
        """Initialize feature extractor."""
        self.feature_names = []

    def extract_features(self, publication: Publication) -> Dict[str, Any]:
        """
        Extract all features from a publication.

        Args:
            publication: Publication object

        Returns:
            Dictionary of feature name -> value
        """
        features = {}

        # Temporal features
        features.update(self._extract_temporal_features(publication))

        # Author features
        features.update(self._extract_author_features(publication))

        # Content features
        features.update(self._extract_content_features(publication))

        # Metadata features
        features.update(self._extract_metadata_features(publication))

        # Citation features
        features.update(self._extract_citation_features(publication))

        return features

    def extract_features_batch(self, publications: List[Publication]) -> List[Dict[str, Any]]:
        """
        Extract features from multiple publications.

        Args:
            publications: List of Publication objects

        Returns:
            List of feature dictionaries
        """
        return [self.extract_features(pub) for pub in publications]

    def features_to_array(
        self, features: Dict[str, Any], feature_names: Optional[List[str]] = None
    ) -> np.ndarray:
        """
        Convert feature dict to numpy array.

        Args:
            features: Feature dictionary
            feature_names: Ordered list of feature names to extract

        Returns:
            Numpy array of feature values
        """
        if feature_names is None:
            feature_names = sorted(features.keys())

        values = []
        for name in feature_names:
            value = features.get(name, 0)
            # Convert boolean to int
            if isinstance(value, bool):
                value = int(value)
            values.append(value)

        return np.array(values, dtype=np.float32)

    def _extract_temporal_features(self, publication: Publication) -> Dict[str, Any]:
        """Extract time-related features."""
        features = {}

        # Get year from publication_date
        year = None
        if publication.publication_date:
            year = publication.publication_date.year

        if year:
            features["publication_year"] = year
            current_year = datetime.now().year
            features["years_since_publication"] = current_year - year
            features["is_recent"] = int((current_year - year) <= 2)
            features["publication_decade"] = (year // 10) * 10
        else:
            features["publication_year"] = 0
            features["years_since_publication"] = 0
            features["is_recent"] = 0
            features["publication_decade"] = 0

        return features

    def _extract_author_features(self, publication: Publication) -> Dict[str, Any]:
        """Extract author-related features."""
        features = {}

        if publication.authors and len(publication.authors) > 0:
            num_authors = len(publication.authors)
            features["num_authors"] = num_authors
            features["has_multiple_authors"] = int(num_authors > 1)
            features["has_many_authors"] = int(num_authors > 5)

            # Estimate author collaboration
            features["author_collaboration_score"] = min(num_authors / 10.0, 1.0)
        else:
            features["num_authors"] = 0
            features["has_multiple_authors"] = 0
            features["has_many_authors"] = 0
            features["author_collaboration_score"] = 0.0

        return features

    def _extract_content_features(self, publication: Publication) -> Dict[str, Any]:
        """Extract content-related features."""
        features = {}

        # Title features
        if publication.title:
            features["title_length"] = len(publication.title)
            features["title_word_count"] = len(publication.title.split())
            features["title_has_question"] = int("?" in publication.title)
            features["title_has_colon"] = int(":" in publication.title)
        else:
            features["title_length"] = 0
            features["title_word_count"] = 0
            features["title_has_question"] = 0
            features["title_has_colon"] = 0

        # Abstract features
        if publication.abstract:
            features["abstract_length"] = len(publication.abstract)
            features["abstract_word_count"] = len(publication.abstract.split())
            features["has_abstract"] = 1

            # Count sentences
            sentences = re.split(r"[.!?]+", publication.abstract)
            features["abstract_sentence_count"] = len([s for s in sentences if s.strip()])

            # Calculate readability (simple word length average)
            words = publication.abstract.split()
            if words:
                features["abstract_avg_word_length"] = sum(len(w) for w in words) / len(words)
            else:
                features["abstract_avg_word_length"] = 0.0
        else:
            features["abstract_length"] = 0
            features["abstract_word_count"] = 0
            features["has_abstract"] = 0
            features["abstract_sentence_count"] = 0
            features["abstract_avg_word_length"] = 0.0

        return features

    def _extract_metadata_features(self, publication: Publication) -> Dict[str, Any]:
        """Extract metadata features."""
        features = {}

        # DOI and identifiers
        features["has_doi"] = int(bool(publication.doi))
        features["has_pmid"] = int(bool(publication.pmid))

        # Journal/source
        if publication.journal:
            features["has_journal"] = 1
            features["journal_name_length"] = len(publication.journal)
        else:
            features["has_journal"] = 0
            features["journal_name_length"] = 0

        # Publication type
        if hasattr(publication, "publication_type") and publication.publication_type:
            features["is_review"] = int("review" in publication.publication_type.lower())
            features["is_clinical_trial"] = int("clinical trial" in publication.publication_type.lower())
        else:
            features["is_review"] = 0
            features["is_clinical_trial"] = 0

        return features

    def _extract_citation_features(self, publication: Publication) -> Dict[str, Any]:
        """Extract citation-related features."""
        features = {}

        if publication.citations is not None and publication.citations > 0:
            features["citation_count"] = publication.citations
            features["has_citations"] = 1

            # Citation velocity (citations per year)
            if publication.publication_date:
                years = datetime.now().year - publication.publication_date.year
                if years > 0:
                    features["citations_per_year"] = publication.citations / years
                else:
                    features["citations_per_year"] = publication.citations
            else:
                features["citations_per_year"] = 0.0
        else:
            features["citation_count"] = 0
            features["has_citations"] = 0
            features["citations_per_year"] = 0.0

        return features

    def get_feature_names(self) -> List[str]:
        """
        Get list of all feature names.

        Returns:
            Sorted list of feature names
        """
        # Extract from a dummy publication to get all feature names
        dummy_pub = Publication(
            pmid="dummy",
            title="Dummy Title",
            authors="Author One, Author Two",
            year=2020,
            abstract="This is a dummy abstract for feature extraction.",
            journal="Dummy Journal",
            doi="10.1234/dummy",
        )

        features = self.extract_features(dummy_pub)
        return sorted(features.keys())

    def get_feature_importance_names(self) -> Dict[str, str]:
        """
        Get human-readable names for features.

        Returns:
            Dictionary of feature_name -> human_readable_name
        """
        return {
            "publication_year": "Publication Year",
            "years_since_publication": "Years Since Publication",
            "is_recent": "Recent Publication (<=2 years)",
            "publication_decade": "Publication Decade",
            "num_authors": "Number of Authors",
            "has_multiple_authors": "Has Multiple Authors",
            "has_many_authors": "Has Many Authors (>5)",
            "author_collaboration_score": "Author Collaboration Score",
            "title_length": "Title Length (chars)",
            "title_word_count": "Title Word Count",
            "title_has_question": "Title Has Question Mark",
            "title_has_colon": "Title Has Colon",
            "abstract_length": "Abstract Length (chars)",
            "abstract_word_count": "Abstract Word Count",
            "has_abstract": "Has Abstract",
            "abstract_sentence_count": "Abstract Sentence Count",
            "abstract_avg_word_length": "Abstract Avg Word Length",
            "has_doi": "Has DOI",
            "has_pmid": "Has PMID",
            "has_journal": "Has Journal",
            "journal_name_length": "Journal Name Length",
            "is_review": "Is Review Article",
            "is_clinical_trial": "Is Clinical Trial",
            "citation_count": "Current Citation Count",
            "has_citations": "Has Citations",
            "citations_per_year": "Citations Per Year",
        }
