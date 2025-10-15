"""
Advanced deduplication for publications.

This module provides sophisticated deduplication beyond simple ID matching:
- Fuzzy title matching (handles typos, formatting)
- Author name matching (handles variations)
- Year + venue matching (preprints vs published)
- Similarity scoring for near-duplicates

Week 3 Day 14 implementation.
"""

from datetime import datetime
from typing import List, Tuple

from fuzzywuzzy import fuzz

from omics_oracle_v2.lib.search_engines.citations.models import Publication


class AdvancedDeduplicator:
    """
    Advanced publication deduplication using fuzzy matching.

    Handles cases where publications are duplicates but have:
    - Different formatting in titles (case, punctuation)
    - Typos or OCR errors in titles
    - Author name variations (J. Smith vs Smith, J.)
    - Same content in different venues (preprint vs published)
    """

    def __init__(
        self,
        title_similarity_threshold: float = 85.0,
        author_similarity_threshold: float = 80.0,
        year_tolerance: int = 1,
        enable_fuzzy_matching: bool = True,
    ):
        """
        Initialize advanced deduplicator.

        Args:
            title_similarity_threshold: Minimum fuzzy ratio for title match (0-100)
            author_similarity_threshold: Minimum fuzzy ratio for author match (0-100)
            year_tolerance: Max year difference for same publication (e.g., preprint in 2023, published 2024)
            enable_fuzzy_matching: Enable/disable fuzzy matching (for performance)
        """
        self.title_threshold = title_similarity_threshold
        self.author_threshold = author_similarity_threshold
        self.year_tolerance = year_tolerance
        self.enable_fuzzy = enable_fuzzy_matching

    def deduplicate(self, publications: List[Publication]) -> List[Publication]:
        """
        Remove duplicates using fuzzy matching.

        Process:
        1. First pass: Remove exact ID duplicates (PMID, PMCID, DOI)
        2. Second pass: Fuzzy title + author matching
        3. Third pass: Preprint vs published detection

        Args:
            publications: List of publications to deduplicate

        Returns:
            Deduplicated list (keeps most complete record for each duplicate set)
        """
        if not publications:
            return []

        # Pass 1: ID-based deduplication (handled by pipeline)
        # This method assumes ID deduplication already done

        if not self.enable_fuzzy:
            return publications

        # Pass 2: Fuzzy matching
        unique_pubs = []
        duplicate_indices = set()

        for i, pub1 in enumerate(publications):
            if i in duplicate_indices:
                continue  # Already marked as duplicate

            # Check against remaining publications
            for j in range(i + 1, len(publications)):
                if j in duplicate_indices:
                    continue

                pub2 = publications[j]

                # Check if they're duplicates
                if self._are_duplicates(pub1, pub2):
                    # Keep the more complete record
                    if self._is_more_complete(pub1, pub2):
                        duplicate_indices.add(j)
                    else:
                        duplicate_indices.add(i)
                        break  # pub1 is less complete, move to next

            # Add if not marked as duplicate
            if i not in duplicate_indices:
                unique_pubs.append(pub1)

        duplicates_removed = len(publications) - len(unique_pubs)
        if duplicates_removed > 0:
            print(
                f"Advanced deduplication removed {duplicates_removed} additional duplicates"
            )

        return unique_pubs

    def _are_duplicates(self, pub1: Publication, pub2: Publication) -> bool:
        """
        Determine if two publications are duplicates using fuzzy matching.

        Args:
            pub1: First publication
            pub2: Second publication

        Returns:
            True if publications are likely duplicates
        """
        # Must have titles to compare
        if not pub1.title or not pub2.title:
            return False

        # 1. Check title similarity
        title_ratio = fuzz.ratio(pub1.title.lower().strip(), pub2.title.lower().strip())

        if title_ratio < self.title_threshold:
            return False  # Titles too different

        # 2. Check author similarity (if available)
        if pub1.authors and pub2.authors:
            if not self._authors_match(pub1.authors, pub2.authors):
                return False  # Different authors

        # 3. Check publication year (if available)
        if pub1.publication_date and pub2.publication_date:
            if not self._years_match(pub1.publication_date, pub2.publication_date):
                return False  # Published too far apart

        # All checks passed - likely duplicate
        return True

    def _authors_match(self, authors1: List[str], authors2: List[str]) -> bool:
        """
        Check if author lists match (with fuzzy matching for name variations).

        Handles:
        - "Smith J" vs "J Smith" vs "Smith, J." vs "J. Smith"
        - First author match (most important)
        - Overall author list similarity

        Args:
            authors1: First author list
            authors2: Second author list

        Returns:
            True if authors match
        """
        if not authors1 or not authors2:
            return True  # Can't compare, assume match

        # Normalize author names
        norm_authors1 = [self._normalize_author(a) for a in authors1]
        norm_authors2 = [self._normalize_author(a) for a in authors2]

        # Check first author (most important)
        if norm_authors1 and norm_authors2:
            first_author_ratio = fuzz.ratio(norm_authors1[0], norm_authors2[0])
            if first_author_ratio < self.author_threshold:
                return False  # First author doesn't match

        # Check overall author list similarity
        # Use token_sort_ratio for order-independent matching
        authors_str1 = " ".join(norm_authors1[:5])  # Use first 5 authors
        authors_str2 = " ".join(norm_authors2[:5])
        author_list_ratio = fuzz.token_sort_ratio(authors_str1, authors_str2)

        return author_list_ratio >= self.author_threshold

    def _normalize_author(self, author: str) -> str:
        """
        Normalize author name for comparison.

        Examples:
        - "Smith, John A." -> "smith john a"
        - "J.A. Smith" -> "j a smith"
        - "Smith J" -> "smith j"

        Args:
            author: Author name string

        Returns:
            Normalized author name
        """
        # Remove punctuation
        normalized = author.lower()
        for char in ",.;:":
            normalized = normalized.replace(char, " ")

        # Collapse multiple spaces
        normalized = " ".join(normalized.split())

        return normalized

    def _years_match(self, date1: datetime, date2: datetime) -> bool:
        """
        Check if publication years are within tolerance.

        Allows for:
        - Preprints published in different year
        - Date entry errors
        - Year-end publications

        Args:
            date1: First publication date
            date2: Second publication date

        Returns:
            True if years are within tolerance
        """
        year_diff = abs(date1.year - date2.year)
        return year_diff <= self.year_tolerance

    def _is_more_complete(self, pub1: Publication, pub2: Publication) -> bool:
        """
        Determine which publication record is more complete.

        Prefers records with:
        1. PMID > DOI only > No ID
        2. Abstract present
        3. More authors
        4. More metadata

        Args:
            pub1: First publication
            pub2: Second publication

        Returns:
            True if pub1 is more complete than pub2
        """
        score1 = self._completeness_score(pub1)
        score2 = self._completeness_score(pub2)

        return score1 >= score2

    def _completeness_score(self, pub: Publication) -> int:
        """
        Calculate completeness score for a publication.

        Args:
            pub: Publication to score

        Returns:
            Completeness score (higher = more complete)
        """
        score = 0

        # IDs (most important)
        if pub.pmid:
            score += 100  # PMID is gold standard
        if pub.pmcid:
            score += 50
        if pub.doi:
            score += 30

        # Content
        if pub.abstract:
            score += 20
        if pub.authors:
            score += len(pub.authors) * 2  # More authors = better
        if pub.journal:
            score += 10
        if pub.publication_date:
            score += 10

        # Metadata
        if pub.mesh_terms:
            score += 15
        if pub.keywords:
            score += 10
        if pub.citations and pub.citations > 0:
            score += 5

        return score

    def find_preprint_published_pairs(
        self, publications: List[Publication]
    ) -> List[Tuple[Publication, Publication]]:
        """
        Find pairs of (preprint, published) versions of the same work.

        Useful for:
        - Linking preprints to final versions
        - Citation analysis (aggregate citations)
        - Version tracking

        Args:
            publications: List of publications to analyze

        Returns:
            List of (preprint, published) tuples
        """
        pairs = []

        preprint_venues = {"biorxiv", "medrxiv", "arxiv", "preprint"}

        for i, pub1 in enumerate(publications):
            # Check if preprint
            if not pub1.journal:
                continue

            is_preprint1 = any(
                venue in pub1.journal.lower() for venue in preprint_venues
            )

            if not is_preprint1:
                continue  # Not a preprint

            # Look for published version
            for pub2 in publications[i + 1 :]:
                if not pub2.journal:
                    continue

                is_preprint2 = any(
                    venue in pub2.journal.lower() for venue in preprint_venues
                )

                if is_preprint2:
                    continue  # Both preprints

                # Check if same work
                if self._are_duplicates(pub1, pub2):
                    pairs.append((pub1, pub2))
                    break  # Found published version

        return pairs
