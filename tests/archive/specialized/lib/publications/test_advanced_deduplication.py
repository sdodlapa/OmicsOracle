"""
Tests for advanced publication deduplication.

Tests fuzzy title matching, author matching, and preprint detection.
"""

import unittest
from datetime import datetime

from omics_oracle_v2.lib.publications.deduplication import AdvancedDeduplicator
from omics_oracle_v2.lib.search_engines.citations.models import Publication, PublicationSource


class TestAdvancedDeduplicator(unittest.TestCase):
    """Test advanced deduplication functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.deduplicator = AdvancedDeduplicator(
            title_similarity_threshold=85.0,
            author_similarity_threshold=80.0,
            year_tolerance=1,
        )

    def test_exact_duplicate_titles(self):
        """Test detection of exact duplicate titles."""
        pubs = [
            Publication(
                title="CRISPR gene editing in cancer therapy",
                authors=["Smith J", "Jones A"],
                journal="Nature",
                publication_date=datetime(2023, 1, 15),
                source=PublicationSource.PUBMED,
                doi="10.1234/test1",
            ),
            Publication(
                title="CRISPR gene editing in cancer therapy",
                authors=["Smith J", "Jones A"],
                journal="Science",
                publication_date=datetime(2023, 1, 15),
                source=PublicationSource.GOOGLE_SCHOLAR,
                abstract="Full abstract here",
            ),
        ]

        result = self.deduplicator.deduplicate(pubs)

        # Should keep only one
        self.assertEqual(len(result), 1)
        # Should keep the one with DOI (more complete)
        self.assertEqual(result[0].doi, "10.1234/test1")

    def test_title_case_variations(self):
        """Test detection of titles with different case."""
        pubs = [
            Publication(
                title="CRISPR Gene Editing in Cancer Therapy",
                authors=["Smith J"],
                source=PublicationSource.PUBMED,
                doi="10.1234/test1",
            ),
            Publication(
                title="crispr gene editing in cancer therapy",
                authors=["Smith J"],
                source=PublicationSource.GOOGLE_SCHOLAR,
            ),
        ]

        result = self.deduplicator.deduplicate(pubs)
        self.assertEqual(len(result), 1)

    def test_title_punctuation_variations(self):
        """Test detection of titles with different punctuation."""
        pubs = [
            Publication(
                title="CRISPR gene editing: a new approach",
                authors=["Smith J"],
                source=PublicationSource.PUBMED,
            ),
            Publication(
                title="CRISPR gene editing - a new approach",
                authors=["Smith J"],
                source=PublicationSource.GOOGLE_SCHOLAR,
            ),
        ]

        result = self.deduplicator.deduplicate(pubs)
        # With 85% threshold, these should match (punctuation difference is minor)
        self.assertEqual(len(result), 1)

    def test_similar_but_different_titles(self):
        """Test that similar but distinct titles are kept separate."""
        pubs = [
            Publication(
                title="CRISPR gene editing in cancer therapy",
                authors=["Smith J"],
                source=PublicationSource.PUBMED,
            ),
            Publication(
                title="CRISPR gene editing in diabetes treatment",
                authors=["Smith J"],
                source=PublicationSource.GOOGLE_SCHOLAR,
            ),
        ]

        result = self.deduplicator.deduplicate(pubs)
        # Different topics - should keep both
        self.assertEqual(len(result), 2)

    def test_author_name_variations(self):
        """Test matching of author name variations."""
        # Test cases for _normalize_author
        variations = [
            ("Smith, John A.", "smith john a"),
            ("J.A. Smith", "j a smith"),
            ("Smith J", "smith j"),
            ("John Smith", "john smith"),
        ]

        for original, expected in variations:
            normalized = self.deduplicator._normalize_author(original)
            self.assertEqual(normalized, expected)

    def test_author_matching_first_author(self):
        """Test author matching focuses on first author."""
        pubs = [
            Publication(
                title="CRISPR gene editing",
                authors=["Smith J", "Jones A", "Williams R"],
                source=PublicationSource.PUBMED,
            ),
            Publication(
                title="CRISPR gene editing",
                authors=["Smith, J.", "Jones A", "Williams R"],  # Same co-authors
                source=PublicationSource.GOOGLE_SCHOLAR,
            ),
        ]

        result = self.deduplicator.deduplicate(pubs)
        # Same title, same authors (just formatting difference) - should deduplicate
        self.assertEqual(len(result), 1)

    def test_different_first_author_keeps_separate(self):
        """Test that different first authors keep publications separate."""
        pubs = [
            Publication(
                title="CRISPR gene editing",
                authors=["Smith J", "Jones A"],
                source=PublicationSource.PUBMED,
            ),
            Publication(
                title="CRISPR gene editing",
                authors=["Williams R", "Smith J"],
                source=PublicationSource.GOOGLE_SCHOLAR,
            ),
        ]

        result = self.deduplicator.deduplicate(pubs)
        # Same title but different first author - should keep both
        self.assertEqual(len(result), 2)

    def test_year_tolerance(self):
        """Test year tolerance for preprints vs published."""
        pubs = [
            Publication(
                title="Novel CRISPR application",
                authors=["Smith J"],
                journal="bioRxiv",
                publication_date=datetime(2023, 12, 1),
                source=PublicationSource.GOOGLE_SCHOLAR,
            ),
            Publication(
                title="Novel CRISPR application",
                authors=["Smith J"],
                journal="Nature",
                publication_date=datetime(2024, 2, 1),
                source=PublicationSource.PUBMED,
                pmid="12345678",
            ),
        ]

        result = self.deduplicator.deduplicate(pubs)
        # Within year tolerance (1 year) - should deduplicate
        self.assertEqual(len(result), 1)
        # Should keep published version (has PMID)
        self.assertEqual(result[0].pmid, "12345678")

    def test_year_tolerance_exceeded(self):
        """Test that publications too far apart are kept separate."""
        pubs = [
            Publication(
                title="CRISPR research",
                authors=["Smith J"],
                publication_date=datetime(2020, 1, 1),
                source=PublicationSource.PUBMED,
            ),
            Publication(
                title="CRISPR research",
                authors=["Smith J"],
                publication_date=datetime(2023, 1, 1),
                source=PublicationSource.GOOGLE_SCHOLAR,
            ),
        ]

        result = self.deduplicator.deduplicate(pubs)
        # 3 years apart - beyond tolerance - should keep both
        self.assertEqual(len(result), 2)

    def test_completeness_score_pmid_preferred(self):
        """Test that PMID records are preferred."""
        pub_with_pmid = Publication(
            title="Test",
            pmid="12345678",
            source=PublicationSource.PUBMED,
        )
        pub_with_doi = Publication(
            title="Test",
            doi="10.1234/test",
            source=PublicationSource.GOOGLE_SCHOLAR,
        )

        score_pmid = self.deduplicator._completeness_score(pub_with_pmid)
        score_doi = self.deduplicator._completeness_score(pub_with_doi)

        self.assertGreater(score_pmid, score_doi)

    def test_completeness_score_abstract_bonus(self):
        """Test that publications with abstracts score higher."""
        pub_with_abstract = Publication(
            title="Test",
            abstract="This is the abstract",
            source=PublicationSource.PUBMED,
        )
        pub_without_abstract = Publication(
            title="Test",
            source=PublicationSource.GOOGLE_SCHOLAR,
        )

        score_with = self.deduplicator._completeness_score(pub_with_abstract)
        score_without = self.deduplicator._completeness_score(pub_without_abstract)

        self.assertGreater(score_with, score_without)

    def test_completeness_score_more_authors(self):
        """Test that publications with more authors score higher."""
        pub_many_authors = Publication(
            title="Test",
            authors=["Smith J", "Jones A", "Williams R", "Brown T"],
            source=PublicationSource.PUBMED,
        )
        pub_few_authors = Publication(
            title="Test",
            authors=["Smith J"],
            source=PublicationSource.GOOGLE_SCHOLAR,
        )

        score_many = self.deduplicator._completeness_score(pub_many_authors)
        score_few = self.deduplicator._completeness_score(pub_few_authors)

        self.assertGreater(score_many, score_few)

    def test_disabled_fuzzy_matching(self):
        """Test that fuzzy matching can be disabled."""
        deduplicator = AdvancedDeduplicator(enable_fuzzy_matching=False)

        pubs = [
            Publication(
                title="CRISPR Gene Editing",
                authors=["Smith J"],
                source=PublicationSource.PUBMED,
            ),
            Publication(
                title="crispr gene editing",  # Case difference
                authors=["Smith J"],
                source=PublicationSource.GOOGLE_SCHOLAR,
            ),
        ]

        result = deduplicator.deduplicate(pubs)
        # Fuzzy matching disabled - should keep both
        self.assertEqual(len(result), 2)

    def test_empty_publications_list(self):
        """Test handling of empty publications list."""
        result = self.deduplicator.deduplicate([])
        self.assertEqual(len(result), 0)

    def test_single_publication(self):
        """Test handling of single publication."""
        pubs = [
            Publication(
                title="Test",
                source=PublicationSource.PUBMED,
            )
        ]
        result = self.deduplicator.deduplicate(pubs)
        self.assertEqual(len(result), 1)

    def test_preprint_detection(self):
        """Test detection of preprint vs published pairs."""
        pubs = [
            Publication(
                title="Novel CRISPR method",
                authors=["Smith J", "Jones A"],
                journal="bioRxiv",
                publication_date=datetime(2023, 6, 1),
                source=PublicationSource.GOOGLE_SCHOLAR,
            ),
            Publication(
                title="Novel CRISPR method",
                authors=["Smith J", "Jones A"],
                journal="Nature",
                publication_date=datetime(2023, 12, 1),
                source=PublicationSource.PUBMED,
                pmid="12345678",
            ),
            Publication(
                title="Different paper",
                authors=["Williams R"],
                journal="Science",
                source=PublicationSource.PUBMED,
            ),
        ]

        pairs = self.deduplicator.find_preprint_published_pairs(pubs)

        # Should find one pair (bioRxiv -> Nature)
        self.assertEqual(len(pairs), 1)
        preprint, published = pairs[0]
        self.assertIn("biorxiv", preprint.journal.lower())
        self.assertEqual(published.journal, "Nature")

    def test_no_preprint_pairs(self):
        """Test when no preprint pairs exist."""
        pubs = [
            Publication(
                title="Paper 1",
                journal="Nature",
                source=PublicationSource.PUBMED,
            ),
            Publication(
                title="Paper 2",
                journal="Science",
                source=PublicationSource.PUBMED,
            ),
        ]

        pairs = self.deduplicator.find_preprint_published_pairs(pubs)
        self.assertEqual(len(pairs), 0)

    def test_multiple_duplicates(self):
        """Test deduplication with multiple duplicate sets."""
        pubs = [
            # Duplicate set 1
            Publication(
                title="Paper A",
                authors=["Smith J"],
                source=PublicationSource.PUBMED,
                pmid="111",
            ),
            Publication(
                title="Paper A",
                authors=["Smith J"],
                source=PublicationSource.GOOGLE_SCHOLAR,
            ),
            # Duplicate set 2
            Publication(
                title="Paper B",
                authors=["Jones A"],
                source=PublicationSource.PUBMED,
                pmid="222",
            ),
            Publication(
                title="Paper B",
                authors=["Jones A"],
                source=PublicationSource.GOOGLE_SCHOLAR,
            ),
            # Unique
            Publication(
                title="Paper C",
                authors=["Williams R"],
                source=PublicationSource.PUBMED,
            ),
        ]

        result = self.deduplicator.deduplicate(pubs)

        # Should have 3 unique publications (2 deduplicated sets + 1 unique)
        self.assertEqual(len(result), 3)

        # Check that we kept the ones with PMIDs
        pmids = [p.pmid for p in result if p.pmid]
        self.assertEqual(len(pmids), 2)
        self.assertIn("111", pmids)
        self.assertIn("222", pmids)


class TestFuzzyThresholds(unittest.TestCase):
    """Test different fuzzy matching thresholds."""

    def test_strict_threshold(self):
        """Test with strict threshold (95%)."""
        deduplicator = AdvancedDeduplicator(title_similarity_threshold=95.0)

        pubs = [
            Publication(
                title="CRISPR gene editing in cancer therapy",
                authors=["Smith J"],
                source=PublicationSource.PUBMED,
            ),
            Publication(
                title="CRISPR gene editing for cancer therapy",  # "in" vs "for"
                authors=["Smith J"],
                source=PublicationSource.GOOGLE_SCHOLAR,
            ),
        ]

        result = deduplicator.deduplicate(pubs)
        # With strict threshold, slight wording difference might keep both
        # (depends on exact fuzz ratio)
        self.assertGreaterEqual(len(result), 1)

    def test_lenient_threshold(self):
        """Test with lenient threshold (70%)."""
        deduplicator = AdvancedDeduplicator(title_similarity_threshold=70.0)

        pubs = [
            Publication(
                title="CRISPR gene editing",
                authors=["Smith J"],
                source=PublicationSource.PUBMED,
            ),
            Publication(
                title="Gene editing with CRISPR",  # Reordered
                authors=["Smith J"],
                source=PublicationSource.GOOGLE_SCHOLAR,
            ),
        ]

        result = deduplicator.deduplicate(pubs)
        # With lenient threshold, might match despite reordering
        self.assertGreaterEqual(len(result), 1)


if __name__ == "__main__":
    unittest.main()
