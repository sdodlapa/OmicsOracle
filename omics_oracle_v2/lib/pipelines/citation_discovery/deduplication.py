"""
Smart deduplication for citation discovery.

This module provides advanced deduplication beyond simple PMID/DOI matching:
- Fuzzy title matching (handles typos, formatting differences)
- Author similarity (same authors = likely duplicate)
- Journal/venue matching
- Publication date proximity
- Configurable similarity thresholds
"""

import logging
import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Dict, List, Optional, Set, Tuple

from omics_oracle_v2.lib.search_engines.citations.models import Publication

logger = logging.getLogger(__name__)


@dataclass
class DeduplicationConfig:
    """Configuration for deduplication"""

    # Title matching
    title_similarity_threshold: float = 0.85  # 85% similarity to be considered duplicate
    title_ignore_case: bool = True
    title_ignore_punctuation: bool = True

    # Author matching
    author_match_threshold: float = 0.7  # 70% of authors must match
    author_min_overlap: int = 2  # At least 2 authors must overlap

    # Other fields
    use_doi: bool = True
    use_pmid: bool = True
    use_title: bool = True
    use_authors: bool = True
    use_year: bool = True  # If years differ by >1, probably not duplicate

    # Strategy
    strict_mode: bool = False  # If True, requires multiple signals to confirm duplicate


@dataclass
class DeduplicationStats:
    """Statistics from deduplication"""

    total_papers: int = 0
    unique_papers: int = 0
    duplicates_removed: int = 0
    removed_by_pmid: int = 0
    removed_by_doi: int = 0
    removed_by_title: int = 0
    removed_by_authors: int = 0
    removed_by_multiple_signals: int = 0

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "total_papers": self.total_papers,
            "unique_papers": self.unique_papers,
            "duplicates_removed": self.duplicates_removed,
            "removed_by_pmid": self.removed_by_pmid,
            "removed_by_doi": self.removed_by_doi,
            "removed_by_title": self.removed_by_title,
            "removed_by_authors": self.removed_by_authors,
            "removed_by_multiple_signals": self.removed_by_multiple_signals,
            "dedup_rate": (
                f"{(self.duplicates_removed / self.total_papers * 100):.1f}%"
                if self.total_papers > 0
                else "0%"
            ),
        }


class SmartDeduplicator:
    """
    Smart deduplication for publications.

    Uses multiple signals to detect duplicates:
    1. Exact PMID/DOI match (highest confidence)
    2. Fuzzy title similarity (handles variations)
    3. Author overlap (same authors = likely same paper)
    4. Combined signals (title + authors + year)

    Example:
        >>> config = DeduplicationConfig(title_similarity_threshold=0.85)
        >>> deduplicator = SmartDeduplicator(config)
        >>> unique_papers = deduplicator.deduplicate(papers)
        >>> stats = deduplicator.get_stats()
    """

    def __init__(self, config: Optional[DeduplicationConfig] = None):
        self.config = config or DeduplicationConfig()
        self.stats = DeduplicationStats()

        # Tracking
        self._seen_pmids: Set[str] = set()
        self._seen_dois: Set[str] = set()
        self._seen_titles: Dict[str, Publication] = {}  # normalized_title -> publication
        self._seen_author_sets: List[Tuple[Set[str], Publication]] = []

    def deduplicate(self, publications: List[Publication]) -> List[Publication]:
        """
        Deduplicate a list of publications.

        Args:
            publications: List of Publication objects

        Returns:
            Deduplicated list of Publication objects
        """
        self.stats.total_papers = len(publications)
        unique_papers: List[Publication] = []

        logger.info(f"Deduplicating {len(publications)} papers...")

        for pub in publications:
            if self._is_duplicate(pub, unique_papers):
                self.stats.duplicates_removed += 1
                logger.debug(f"Removed duplicate: {pub.title[:60]}...")
            else:
                unique_papers.append(pub)
                self._record_publication(pub)

        self.stats.unique_papers = len(unique_papers)

        logger.info(
            f"Deduplication complete: {self.stats.total_papers} → "
            f"{self.stats.unique_papers} papers "
            f"({self.stats.duplicates_removed} duplicates removed)"
        )

        return unique_papers

    def _is_duplicate(self, pub: Publication, existing_papers: List[Publication]) -> bool:
        """
        Check if publication is a duplicate.

        Uses multiple signals in order of confidence:
        1. PMID match (100% confidence)
        2. DOI match (100% confidence)
        3. Title similarity (high confidence)
        4. Author overlap + year (medium confidence)
        5. Multiple weak signals (combined confidence)

        Args:
            pub: Publication to check
            existing_papers: List of already processed unique papers

        Returns:
            True if duplicate, False if unique
        """
        signals = []  # Track which signals indicate duplicate

        # 1. Check PMID (highest confidence)
        if self.config.use_pmid and pub.pmid:
            if pub.pmid in self._seen_pmids:
                self.stats.removed_by_pmid += 1
                logger.debug(f"Duplicate PMID: {pub.pmid}")
                return True
            signals.append("pmid_unique")

        # 2. Check DOI (highest confidence)
        if self.config.use_doi and pub.doi:
            normalized_doi = self._normalize_doi(pub.doi)
            if normalized_doi in self._seen_dois:
                self.stats.removed_by_doi += 1
                logger.debug(f"Duplicate DOI: {pub.doi}")
                return True
            signals.append("doi_unique")

        # 3. Check title similarity (high confidence)
        if self.config.use_title and pub.title:
            normalized_title = self._normalize_title(pub.title)

            for seen_title, seen_pub in self._seen_titles.items():
                similarity = self._title_similarity(normalized_title, seen_title)

                if similarity >= self.config.title_similarity_threshold:
                    # High title similarity - likely duplicate
                    logger.debug(
                        f"Duplicate title (similarity={similarity:.2f}): "
                        f"{pub.title[:60]}... vs {seen_pub.title[:60]}..."
                    )
                    self.stats.removed_by_title += 1
                    signals.append("title_match")

                    # Check year to confirm (if available)
                    if self.config.use_year:
                        pub_year = pub.publication_date.year if pub.publication_date else None
                        seen_year = seen_pub.publication_date.year if seen_pub.publication_date else None
                        
                        if pub_year and seen_year:
                            if abs(pub_year - seen_year) <= 1:
                                # Same year ±1 + high title similarity = definitely duplicate
                                return True
                            else:
                                # Different years but similar titles - might be revision/erratum
                                logger.debug(
                                    f"Title match but different years: {pub_year} vs {seen_year}"
                                )
                                continue

                    return True  # No year info, trust title similarity

        # 4. Check author overlap (medium confidence)
        if self.config.use_authors and pub.authors:
            author_set = self._normalize_authors(pub.authors)

            for seen_authors, seen_pub in self._seen_author_sets:
                overlap = len(author_set & seen_authors)
                total = len(author_set | seen_authors)

                if total == 0:
                    continue

                overlap_ratio = overlap / total

                # High author overlap + similar year = likely duplicate
                if overlap >= self.config.author_min_overlap and overlap_ratio >= self.config.author_match_threshold:
                    signals.append("author_match")

                    # Check year to confirm
                    if self.config.use_year:
                        pub_year = pub.publication_date.year if pub.publication_date else None
                        seen_year = seen_pub.publication_date.year if seen_pub.publication_date else None
                        
                        if pub_year and seen_year:
                            if abs(pub_year - seen_year) <= 1:
                                logger.debug(
                                    f"Duplicate authors (overlap={overlap}/{total}={overlap_ratio:.2f}): "
                                    f"{pub.title[:60]}..."
                                )
                                self.stats.removed_by_authors += 1
                                return True

        # 5. Multiple weak signals (combined confidence)
        if self.config.strict_mode:
            # In strict mode, need multiple signals to confirm duplicate
            weak_signals = [s for s in signals if s in ["author_match", "title_match"]]
            if len(weak_signals) >= 2:
                logger.debug(
                    f"Duplicate by multiple signals ({weak_signals}): " f"{pub.title[:60]}..."
                )
                self.stats.removed_by_multiple_signals += 1
                return True

        return False  # Not a duplicate

    def _record_publication(self, pub: Publication):
        """Record publication for future duplicate detection"""
        if pub.pmid:
            self._seen_pmids.add(pub.pmid)

        if pub.doi:
            self._seen_dois.add(self._normalize_doi(pub.doi))

        if pub.title:
            normalized_title = self._normalize_title(pub.title)
            self._seen_titles[normalized_title] = pub

        if pub.authors:
            author_set = self._normalize_authors(pub.authors)
            self._seen_author_sets.append((author_set, pub))

    def _normalize_title(self, title: str) -> str:
        """Normalize title for comparison"""
        normalized = title

        if self.config.title_ignore_case:
            normalized = normalized.lower()

        if self.config.title_ignore_punctuation:
            # Remove punctuation and extra whitespace
            normalized = re.sub(r"[^\w\s]", " ", normalized)
            normalized = re.sub(r"\s+", " ", normalized).strip()

        return normalized

    def _normalize_doi(self, doi: str) -> str:
        """Normalize DOI for comparison"""
        # Remove common prefixes and normalize
        doi = doi.lower().strip()
        doi = re.sub(r"^(doi:|https?://doi.org/|https?://dx.doi.org/)", "", doi)
        return doi.strip()

    def _normalize_authors(self, authors: List[str]) -> Set[str]:
        """Normalize author names for comparison"""
        normalized = set()

        for author in authors:
            # Extract last name (usually after comma or last word)
            if "," in author:
                last_name = author.split(",")[0].strip().lower()
            else:
                # Take last word as last name
                parts = author.strip().split()
                last_name = parts[-1].lower() if parts else ""

            if last_name:
                normalized.add(last_name)

        return normalized

    def _title_similarity(self, title1: str, title2: str) -> float:
        """
        Calculate similarity between two titles.

        Uses SequenceMatcher for fuzzy matching.

        Args:
            title1: First title (normalized)
            title2: Second title (normalized)

        Returns:
            Similarity score between 0.0 and 1.0
        """
        return SequenceMatcher(None, title1, title2).ratio()

    def get_stats(self) -> DeduplicationStats:
        """Get deduplication statistics"""
        return self.stats

    def reset(self):
        """Reset deduplicator state"""
        self.stats = DeduplicationStats()
        self._seen_pmids.clear()
        self._seen_dois.clear()
        self._seen_titles.clear()
        self._seen_author_sets.clear()


def deduplicate_publications(
    publications: List[Publication], config: Optional[DeduplicationConfig] = None
) -> Tuple[List[Publication], DeduplicationStats]:
    """
    Convenience function to deduplicate publications.

    Args:
        publications: List of publications to deduplicate
        config: Optional deduplication configuration

    Returns:
        Tuple of (unique_publications, stats)

    Example:
        >>> unique, stats = deduplicate_publications(papers)
        >>> print(f"Removed {stats.duplicates_removed} duplicates")
    """
    deduplicator = SmartDeduplicator(config)
    unique = deduplicator.deduplicate(publications)
    stats = deduplicator.get_stats()
    return unique, stats
