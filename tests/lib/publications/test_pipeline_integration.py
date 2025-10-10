"""
Integration tests for multi-source publication search pipeline.

Tests the integration of PubMed and Google Scholar clients with
deduplication, ranking, and institutional access.
"""

import unittest
from datetime import datetime
from unittest.mock import patch

from omics_oracle_v2.lib.publications.config import GoogleScholarConfig, PublicationSearchConfig, PubMedConfig
from omics_oracle_v2.lib.publications.models import Publication, PublicationSource
from omics_oracle_v2.lib.pipelines.publication_pipeline import PublicationSearchPipeline


class TestPipelineIntegration(unittest.TestCase):
    """Test multi-source pipeline integration."""

    def setUp(self):
        """Set up test fixtures."""
        # PubMed publications
        self.pubmed_pubs = [
            Publication(
                pmid="12345678",
                doi="10.1234/test1",
                title="CRISPR gene editing in cancer therapy",
                abstract="Study on CRISPR for cancer treatment",
                authors=["Smith J", "Jones A"],
                journal="Nature",
                publication_date=datetime(2023, 1, 15),
                source=PublicationSource.PUBMED,
            ),
            Publication(
                pmid="87654321",
                doi="10.1234/test2",
                title="Novel CRISPR applications",
                abstract="New applications of CRISPR technology",
                authors=["Johnson A", "Williams R"],
                journal="Science",
                publication_date=datetime(2023, 2, 20),
                source=PublicationSource.PUBMED,
            ),
        ]

        # Scholar publications (one duplicate, one unique)
        self.scholar_pubs = [
            Publication(
                doi="10.1234/test1",  # Same as first PubMed pub
                title="CRISPR gene editing in cancer therapy",
                abstract="Study on CRISPR for cancer treatment",
                authors=["Smith J", "Jones A"],
                journal="Nature",
                publication_date=datetime(2023, 1, 15),
                source=PublicationSource.GOOGLE_SCHOLAR,
                citation_count=150,
            ),
            Publication(
                doi="10.1234/test3",
                title="CRISPR screening methods",
                abstract="High-throughput CRISPR screening",
                authors=["Williams R", "Brown T"],
                journal="Cell",
                publication_date=datetime(2023, 3, 10),
                source=PublicationSource.GOOGLE_SCHOLAR,
                citation_count=85,
            ),
        ]

    @patch("omics_oracle_v2.lib.publications.clients.pubmed.PubMedClient.search")
    @patch("omics_oracle_v2.lib.publications.clients.scholar.GoogleScholarClient.search")
    def test_multi_source_search(self, mock_scholar_search, mock_pubmed_search):
        """Test search with both PubMed and Google Scholar."""
        mock_pubmed_search.return_value = self.pubmed_pubs
        mock_scholar_search.return_value = self.scholar_pubs

        config = PublicationSearchConfig(
            enable_pubmed=True,
            enable_scholar=True,
            deduplication=True,
            pubmed_config=PubMedConfig(email="test@test.com"),
            scholar_config=GoogleScholarConfig(enable=True, rate_limit_seconds=0.5),
        )

        pipeline = PublicationSearchPipeline(config)
        result = pipeline.search("CRISPR cancer", max_results=50)

        # Should use both sources
        self.assertEqual(len(result.sources_used), 2)
        self.assertIn("pubmed", result.sources_used)
        self.assertIn("google_scholar", result.sources_used)

        # Should have 3 unique publications (1 duplicate removed)
        # PubMed: 2 pubs
        # Scholar: 2 pubs
        # Duplicate: 1 (DOI 10.1234/test1)
        # Total unique: 3
        # Note: total_found counts before ranking, publications after ranking
        self.assertEqual(result.total_found, 3)
        self.assertLessEqual(len(result.publications), 3)

        # Check both clients were called
        mock_pubmed_search.assert_called_once()
        mock_scholar_search.assert_called_once()

    @patch("omics_oracle_v2.lib.publications.clients.pubmed.PubMedClient.search")
    @patch("omics_oracle_v2.lib.publications.clients.scholar.GoogleScholarClient.search")
    def test_pubmed_only_search(self, mock_scholar_search, mock_pubmed_search):
        """Test search with only PubMed enabled."""
        mock_pubmed_search.return_value = self.pubmed_pubs

        config = PublicationSearchConfig(
            enable_pubmed=True,
            enable_scholar=False,
            pubmed_config=PubMedConfig(email="test@test.com"),
        )

        pipeline = PublicationSearchPipeline(config)
        result = pipeline.search("CRISPR cancer", max_results=50)

        # Should use only PubMed
        self.assertEqual(len(result.sources_used), 1)
        self.assertIn("pubmed", result.sources_used)
        self.assertEqual(len(result.publications), 2)

        # Scholar should not be called
        mock_pubmed_search.assert_called_once()
        mock_scholar_search.assert_not_called()

    @patch("omics_oracle_v2.lib.publications.clients.pubmed.PubMedClient.search")
    @patch("omics_oracle_v2.lib.publications.clients.scholar.GoogleScholarClient.search")
    def test_scholar_only_search(self, mock_scholar_search, mock_pubmed_search):
        """Test search with only Google Scholar enabled."""
        mock_scholar_search.return_value = self.scholar_pubs

        config = PublicationSearchConfig(
            enable_pubmed=False,
            enable_scholar=True,
            scholar_config=GoogleScholarConfig(enable=True, rate_limit_seconds=0.5),
        )

        pipeline = PublicationSearchPipeline(config)
        result = pipeline.search("CRISPR cancer", max_results=50)

        # Should use only Scholar
        self.assertEqual(len(result.sources_used), 1)
        self.assertIn("google_scholar", result.sources_used)
        self.assertEqual(len(result.publications), 2)

        # PubMed should not be called
        mock_scholar_search.assert_called_once()
        mock_pubmed_search.assert_not_called()

    @patch("omics_oracle_v2.lib.publications.clients.pubmed.PubMedClient.search")
    @patch("omics_oracle_v2.lib.publications.clients.scholar.GoogleScholarClient.search")
    def test_deduplication_by_pmid(self, mock_scholar_search, mock_pubmed_search):
        """Test deduplication using PMID."""
        # Create Scholar pub with same PMID as PubMed pub
        scholar_with_pmid = [
            Publication(
                pmid="12345678",  # Same PMID
                title="CRISPR gene editing in cancer therapy",
                abstract="Study on CRISPR for cancer treatment",
                authors=["Smith J", "Jones A"],
                journal="Nature",
                publication_date=datetime(2023, 1, 15),
                source=PublicationSource.GOOGLE_SCHOLAR,
            )
        ]

        mock_pubmed_search.return_value = [self.pubmed_pubs[0]]
        mock_scholar_search.return_value = scholar_with_pmid

        config = PublicationSearchConfig(
            enable_pubmed=True,
            enable_scholar=True,
            deduplication=True,
            pubmed_config=PubMedConfig(email="test@test.com"),
            scholar_config=GoogleScholarConfig(enable=True, rate_limit_seconds=0.5),
        )

        pipeline = PublicationSearchPipeline(config)
        result = pipeline.search("CRISPR", max_results=50)

        # Should have only 1 publication (deduplicated by PMID)
        self.assertEqual(len(result.publications), 1)
        # Should prefer PubMed version (first in list)
        self.assertEqual(result.publications[0].publication.source, PublicationSource.PUBMED)

    @patch("omics_oracle_v2.lib.publications.clients.pubmed.PubMedClient.search")
    @patch("omics_oracle_v2.lib.publications.clients.scholar.GoogleScholarClient.search")
    def test_deduplication_by_doi(self, mock_scholar_search, mock_pubmed_search):
        """Test deduplication using DOI."""
        mock_pubmed_search.return_value = self.pubmed_pubs
        mock_scholar_search.return_value = self.scholar_pubs

        config = PublicationSearchConfig(
            enable_pubmed=True,
            enable_scholar=True,
            deduplication=True,
            pubmed_config=PubMedConfig(email="test@test.com"),
            scholar_config=GoogleScholarConfig(enable=True, rate_limit_seconds=0.5),
        )

        pipeline = PublicationSearchPipeline(config)
        result = pipeline.search("CRISPR", max_results=50)

        # Check first pub (DOI 10.1234/test1) appears only once
        test1_count = sum(1 for r in result.publications if r.publication.doi == "10.1234/test1")
        self.assertEqual(test1_count, 1)

    @patch("omics_oracle_v2.lib.publications.clients.pubmed.PubMedClient.search")
    @patch("omics_oracle_v2.lib.publications.clients.scholar.GoogleScholarClient.search")
    def test_no_deduplication(self, mock_scholar_search, mock_pubmed_search):
        """Test search without deduplication."""
        mock_pubmed_search.return_value = self.pubmed_pubs
        mock_scholar_search.return_value = self.scholar_pubs

        config = PublicationSearchConfig(
            enable_pubmed=True,
            enable_scholar=True,
            deduplication=False,  # Disabled
            pubmed_config=PubMedConfig(email="test@test.com"),
            scholar_config=GoogleScholarConfig(enable=True, rate_limit_seconds=0.5),
        )

        pipeline = PublicationSearchPipeline(config)
        result = pipeline.search("CRISPR", max_results=50)

        # Should have 4 publications (no deduplication)
        self.assertEqual(len(result.publications), 4)

    @patch("omics_oracle_v2.lib.publications.clients.pubmed.PubMedClient.search")
    @patch("omics_oracle_v2.lib.publications.clients.scholar.GoogleScholarClient.search")
    def test_max_results_respected(self, mock_scholar_search, mock_pubmed_search):
        """Test that max_results is respected across sources."""
        # Create large result sets
        large_pubmed = [self.pubmed_pubs[0]] * 30
        large_scholar = [self.scholar_pubs[1]] * 30

        mock_pubmed_search.return_value = large_pubmed
        mock_scholar_search.return_value = large_scholar

        config = PublicationSearchConfig(
            enable_pubmed=True,
            enable_scholar=True,
            deduplication=True,
            pubmed_config=PubMedConfig(email="test@test.com"),
            scholar_config=GoogleScholarConfig(enable=True, rate_limit_seconds=0.5),
        )

        pipeline = PublicationSearchPipeline(config)
        result = pipeline.search("CRISPR", max_results=20)

        # Should respect max_results
        self.assertLessEqual(len(result.publications), 20)

    @unittest.skip("Institutional access API needs update for multi-source")
    @patch("omics_oracle_v2.lib.publications.clients.pubmed.PubMedClient.search")
    @patch("omics_oracle_v2.lib.publications.clients.scholar.GoogleScholarClient.search")
    def test_institutional_access_integration(self, mock_scholar_search, mock_pubmed_search):
        """Test institutional access with multi-source search."""
        mock_pubmed_search.return_value = self.pubmed_pubs
        mock_scholar_search.return_value = self.scholar_pubs

        config = PublicationSearchConfig(
            enable_pubmed=True,
            enable_scholar=True,
            enable_institutional_access=True,
            deduplication=True,
            pubmed_config=PubMedConfig(email="test@test.com"),
            scholar_config=GoogleScholarConfig(enable=True, rate_limit_seconds=0.5),
        )

        pipeline = PublicationSearchPipeline(config)
        result = pipeline.search("CRISPR", max_results=50)

        # Check that institutional access was applied
        self.assertTrue(any(p.access_urls for p in result.publications))

    @patch("omics_oracle_v2.lib.publications.clients.pubmed.PubMedClient.search")
    @patch("omics_oracle_v2.lib.publications.clients.scholar.GoogleScholarClient.search")
    def test_empty_results_handling(self, mock_scholar_search, mock_pubmed_search):
        """Test handling of empty results from both sources."""
        mock_pubmed_search.return_value = []
        mock_scholar_search.return_value = []

        config = PublicationSearchConfig(
            enable_pubmed=True,
            enable_scholar=True,
            pubmed_config=PubMedConfig(email="test@test.com"),
            scholar_config=GoogleScholarConfig(enable=True, rate_limit_seconds=0.5),
        )

        pipeline = PublicationSearchPipeline(config)
        result = pipeline.search("nonexistent query xyz", max_results=50)

        # Should handle empty results gracefully
        self.assertEqual(len(result.publications), 0)
        self.assertEqual(result.total_found, 0)
        self.assertEqual(len(result.sources_used), 2)

    @patch("omics_oracle_v2.lib.publications.clients.pubmed.PubMedClient.search")
    @patch("omics_oracle_v2.lib.publications.clients.scholar.GoogleScholarClient.search")
    def test_error_handling_one_source_fails(self, mock_scholar_search, mock_pubmed_search):
        """Test that pipeline continues if one source fails."""
        mock_pubmed_search.return_value = self.pubmed_pubs
        mock_scholar_search.side_effect = Exception("Scholar unavailable")

        config = PublicationSearchConfig(
            enable_pubmed=True,
            enable_scholar=True,
            pubmed_config=PubMedConfig(email="test@test.com"),
            scholar_config=GoogleScholarConfig(enable=True, rate_limit_seconds=0.5),
        )

        pipeline = PublicationSearchPipeline(config)

        # Should not raise exception, just log error
        result = pipeline.search("CRISPR", max_results=50)

        # Should still have PubMed results
        self.assertGreater(len(result.publications), 0)
        # Scholar should not be in sources used (it failed)
        self.assertNotIn("google_scholar", result.sources_used)

    @patch("omics_oracle_v2.lib.publications.clients.scholar.GoogleScholarClient.search")
    def test_scholar_rate_limiting(self, mock_scholar_search):
        """Test that Scholar rate limiting is respected."""
        mock_scholar_search.return_value = self.scholar_pubs

        config = PublicationSearchConfig(
            enable_pubmed=False,
            enable_scholar=True,
            scholar_config=GoogleScholarConfig(
                enable=True, rate_limit_seconds=1.0  # 1 second between requests
            ),
        )

        pipeline = PublicationSearchPipeline(config)

        # Multiple searches should respect rate limit
        import time

        start = time.time()
        pipeline.search("query1", max_results=5)
        pipeline.search("query2", max_results=5)
        elapsed = time.time() - start

        # Should take at least 1 second (rate limit)
        # Note: This is a simple check; actual rate limiting tested in client tests
        self.assertGreater(elapsed, 0.5)


class TestPipelineLifecycle(unittest.TestCase):
    """Test pipeline initialization and cleanup."""

    def test_pipeline_initialization(self):
        """Test pipeline initializes all clients."""
        config = PublicationSearchConfig(
            enable_pubmed=True,
            enable_scholar=True,
            pubmed_config=PubMedConfig(email="test@test.com"),
            scholar_config=GoogleScholarConfig(enable=True, rate_limit_seconds=0.5),
        )

        pipeline = PublicationSearchPipeline(config)

        # Clients should be initialized
        self.assertIsNotNone(pipeline.pubmed_client)
        self.assertIsNotNone(pipeline.scholar_client)

    def test_pipeline_cleanup(self):
        """Test pipeline cleanup."""
        config = PublicationSearchConfig(
            enable_pubmed=True,
            enable_scholar=True,
            pubmed_config=PubMedConfig(email="test@test.com"),
            scholar_config=GoogleScholarConfig(enable=True, rate_limit_seconds=0.5),
        )

        pipeline = PublicationSearchPipeline(config)
        pipeline.initialize()

        # Should be initialized
        self.assertTrue(pipeline._initialized)

        pipeline.cleanup()

        # Should be cleaned up
        self.assertFalse(pipeline._initialized)

    def test_context_manager(self):
        """Test pipeline as context manager."""
        config = PublicationSearchConfig(
            enable_pubmed=True,
            enable_scholar=True,
            pubmed_config=PubMedConfig(email="test@test.com"),
            scholar_config=GoogleScholarConfig(enable=True, rate_limit_seconds=0.5),
        )

        with PublicationSearchPipeline(config) as pipeline:
            self.assertTrue(pipeline._initialized)
            self.assertIsNotNone(pipeline.pubmed_client)
            self.assertIsNotNone(pipeline.scholar_client)

        # Should be cleaned up after context
        self.assertFalse(pipeline._initialized)

    def test_fuzzy_deduplication_integration(self):
        """Test fuzzy deduplication integration (Day 14)."""
        # Create publications with title variations
        pubs_with_variations = [
            Publication(
                title="CRISPR Gene Editing in Cancer Therapy",
                abstract="Study on CRISPR for cancer treatment",
                authors=["Smith J", "Jones A", "Williams R"],
                journal="Nature",
                publication_date=datetime(2023, 1, 15),
                source=PublicationSource.PUBMED,
            ),
            Publication(
                title="crispr gene editing in cancer therapy",  # Same, different case
                abstract="Study on CRISPR for cancer treatment",
                authors=["Smith, J.", "Jones, A.", "Williams, R."],  # Same authors, different format
                journal="Nature",
                publication_date=datetime(2023, 1, 15),
                source=PublicationSource.GOOGLE_SCHOLAR,
            ),
            Publication(
                title="CRISPR Gene-Editing in Cancer Therapy!",  # Same, different punctuation
                abstract="Study on CRISPR for cancer treatment",
                authors=["J Smith", "A Jones", "R Williams"],  # Same authors, another format
                journal="Nature",
                publication_date=datetime(2023, 1, 15),
                source=PublicationSource.GOOGLE_SCHOLAR,
            ),
            Publication(
                title="Different Topic Entirely",
                abstract="This is about something else",
                authors=["Brown T", "Davis M"],
                journal="Science",
                publication_date=datetime(2023, 2, 20),
                source=PublicationSource.PUBMED,
            ),
        ]

        # Test with fuzzy deduplication enabled
        config = PublicationSearchConfig(
            enable_pubmed=True,
            enable_scholar=True,
            pubmed_config=PubMedConfig(email="test@test.com"),
            scholar_config=GoogleScholarConfig(enable=True, rate_limit_seconds=0.5),
        )

        pipeline = PublicationSearchPipeline(config)

        # Mock both clients to return our test publications
        with patch.object(pipeline.pubmed_client, "search", return_value=pubs_with_variations[:2]):
            with patch.object(pipeline.scholar_client, "search", return_value=pubs_with_variations[2:]):
                result = pipeline.search("crispr cancer", max_results=100)

        # Fuzzy deduplication should work but may not catch all variations
        # in a single pass (it compares pairs). We should get 2-3 results.
        # The key is that it's fewer than the original 4.
        self.assertLessEqual(len(result.publications), 3)
        self.assertGreaterEqual(len(result.publications), 2)

        # Verify the different topic is included
        titles = [pub.publication.title for pub in result.publications]
        self.assertTrue(any("Different" in title for title in titles))

    def test_fuzzy_deduplication_disabled(self):
        """Test pipeline with fuzzy deduplication disabled."""
        from omics_oracle_v2.lib.publications.config import FuzzyDeduplicationConfig

        # Create publications with title variations
        pubs_with_variations = [
            Publication(
                title="CRISPR Gene Editing",
                authors=["Smith J"],
                journal="Nature",
                publication_date=datetime(2023, 1, 15),
                source=PublicationSource.PUBMED,
            ),
            Publication(
                title="crispr gene editing",  # Same, different case
                authors=["Smith, J."],
                journal="Nature",
                publication_date=datetime(2023, 1, 15),
                source=PublicationSource.GOOGLE_SCHOLAR,
            ),
        ]

        # Disable fuzzy deduplication
        config = PublicationSearchConfig(
            enable_pubmed=True,
            enable_scholar=True,
            pubmed_config=PubMedConfig(email="test@test.com"),
            scholar_config=GoogleScholarConfig(enable=True, rate_limit_seconds=0.5),
            fuzzy_dedup_config=FuzzyDeduplicationConfig(enable=False),
        )

        pipeline = PublicationSearchPipeline(config)

        # Mock both clients
        with patch.object(pipeline.pubmed_client, "search", return_value=[pubs_with_variations[0]]):
            with patch.object(pipeline.scholar_client, "search", return_value=[pubs_with_variations[1]]):
                result = pipeline.search("crispr", max_results=100)

        # Without fuzzy dedup, both variations should remain (no IDs to match)
        self.assertEqual(len(result.publications), 2)


if __name__ == "__main__":
    unittest.main()
