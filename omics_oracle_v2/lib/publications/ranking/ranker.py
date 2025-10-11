"""
Publication ranking with multi-factor relevance scoring.

This ranker scores publications based on:
- Title relevance (40%)
- Abstract relevance (30%)
- Recency (20%)
- Citation count (10%)
"""

import logging
import math
import re
from datetime import datetime
from typing import Dict, List, Set, Tuple

from omics_oracle_v2.lib.publications.config import PublicationSearchConfig
from omics_oracle_v2.lib.publications.models import Publication, PublicationSearchResult

logger = logging.getLogger(__name__)


class PublicationRanker:
    """
    Multi-factor publication ranking system.

    Scoring factors:
    1. Title Match (40%): TF-IDF based title relevance
    2. Abstract Match (30%): TF-IDF based abstract relevance
    3. Recency (20%): Time-based decay scoring
    4. Citations (10%): Log-scaled citation count

    Example:
        >>> config = PublicationSearchConfig()
        >>> ranker = PublicationRanker(config)
        >>> scored = ranker.rank(publications, "cancer genomics")
    """

    def __init__(self, config: PublicationSearchConfig):
        """
        Initialize ranker with configuration.

        Args:
            config: Publication search configuration with ranking weights
        """
        self.config = config
        self.weights = config.ranking_weights

        # Validate weights
        if not (0.99 <= sum(self.weights.values()) <= 1.01):
            logger.warning(f"Ranking weights sum to {sum(self.weights.values())}, " "should be 1.0")

    def rank(
        self, publications: List[Publication], query: str, top_k: int = None
    ) -> List[PublicationSearchResult]:
        """
        Rank publications by relevance to query.

        Args:
            publications: List of publications to rank
            query: Search query
            top_k: Return only top K results (optional)

        Returns:
            List of PublicationSearchResult objects, sorted by relevance
        """
        if not publications:
            return []

        # Tokenize query
        query_tokens = self._tokenize(query)

        # Score each publication
        scored_results = []
        for pub in publications:
            score, breakdown, matches = self._score_publication(pub, query, query_tokens)

            result = PublicationSearchResult(
                publication=pub,
                relevance_score=score,
                score_breakdown=breakdown,
                query_matches=matches,
            )
            scored_results.append(result)

        # Sort by score (descending)
        scored_results.sort(key=lambda x: x.relevance_score, reverse=True)

        # Assign ranks
        for i, result in enumerate(scored_results, 1):
            result.rank = i

        # Apply top-k if specified
        if top_k:
            scored_results = scored_results[:top_k]

        logger.info(
            f"Ranked {len(scored_results)} publications "
            f"(top score: {scored_results[0].relevance_score:.2f})"
        )

        return scored_results

    def _score_publication(
        self, publication: Publication, query: str, query_tokens: Set[str]
    ) -> Tuple[float, Dict[str, float], List[str]]:
        """
        Calculate relevance score for a single publication.

        Args:
            publication: Publication to score
            query: Original query string
            query_tokens: Tokenized query terms

        Returns:
            Tuple of (total_score, score_breakdown, matched_terms)
        """
        breakdown = {}
        matches = []

        # 1. Title relevance (40%)
        title_score = self._calculate_text_relevance(publication.title or "", query_tokens, matches)
        breakdown["title_match"] = title_score * self.weights["title_match"]

        # 2. Abstract relevance (30%)
        abstract_score = self._calculate_text_relevance(publication.abstract or "", query_tokens, matches)
        breakdown["abstract_match"] = abstract_score * self.weights["abstract_match"]

        # 3. Recency score (20%)
        recency_score = self._calculate_recency_score(publication.publication_date)
        breakdown["recency"] = recency_score * self.weights["recency"]

        # 4. Citation score (10%)
        citation_score = self._calculate_citation_score(publication.citations or 0)
        breakdown["citations"] = citation_score * self.weights["citations"]

        # Total score (0-100)
        total_score = sum(breakdown.values()) * 100

        # Remove duplicates from matches
        matches = list(set(matches))

        return total_score, breakdown, matches

    def _calculate_text_relevance(self, text: str, query_tokens: Set[str], matches: List[str]) -> float:
        """
        Calculate text relevance using TF-IDF-inspired scoring.

        Args:
            text: Text to score (title or abstract)
            query_tokens: Query terms
            matches: List to append matched terms to

        Returns:
            Relevance score (0.0-1.0)
        """
        if not text or not query_tokens:
            return 0.0

        text_lower = text.lower()
        text_tokens = self._tokenize(text)

        # Count matches
        match_count = 0
        term_frequencies = {}

        for token in query_tokens:
            if token in text_tokens:
                match_count += 1
                matches.append(token)

                # Calculate term frequency
                tf = text_lower.count(token) / len(text_tokens)
                term_frequencies[token] = tf

        if match_count == 0:
            return 0.0

        # Base score: fraction of query terms matched
        coverage_score = match_count / len(query_tokens)

        # Boost for higher term frequencies
        if term_frequencies:
            avg_tf = sum(term_frequencies.values()) / len(term_frequencies)
            tf_boost = min(avg_tf * 2, 0.5)  # Up to 0.5 boost
        else:
            tf_boost = 0.0

        # Boost for exact phrase matches
        phrase_boost = 0.0
        if len(query_tokens) > 1:
            # Check for consecutive tokens
            query_phrases = self._extract_phrases(" ".join(query_tokens))
            for phrase in query_phrases:
                if phrase in text_lower:
                    phrase_boost = 0.3
                    break

        # Combine scores
        final_score = min(coverage_score + tf_boost + phrase_boost, 1.0)

        return final_score

    def _calculate_recency_score(self, pub_date: datetime = None) -> float:
        """
        Calculate recency score with exponential decay and bonus for very recent papers.

        Args:
            pub_date: Publication date

        Returns:
            Recency score (0.0-1.0+), can exceed 1.0 for very recent papers
        """
        if not pub_date:
            return 0.3  # Default for unknown dates

        # Calculate age in years
        now = datetime.now()
        age_years = (now - pub_date).days / 365.25

        # Recency bonus for papers from last 2 years (2023-2025)
        if age_years <= 2.0:
            # Extra boost for very recent papers
            # 0 years → 1.3, 1 year → 1.15, 2 years → 1.0
            recency_bonus = 1.0 + (0.3 * (2.0 - age_years) / 2.0)
            return recency_bonus

        # Exponential decay for older papers: score = e^(-age/decay_rate)
        decay_rate = 5.0  # Half-life of ~3.5 years (reaches 0.5 at 3.5 years)
        score = math.exp(-age_years / decay_rate)

        # Ensure minimum value for very old papers
        return max(0.1, min(1.0, score))

    def _calculate_citation_score(self, citations: int) -> float:
        """
        Calculate citation score with smart dampening for highly-cited papers.

        Strategy:
        - 0-100 citations: Linear scaling (standard papers)
        - 100-1,000 citations: Square root scaling (high-impact papers)
        - 1,000+ citations: Logarithmic scaling (foundational/review papers)

        This ensures:
        - Recent relevant papers score competitively
        - Classic papers don't dominate purely on citation count
        - Foundational papers still recognized but not overwhelming

        Examples:
        - 0 citations    → 0.00 score
        - 50 citations   → 0.50 score (linear)
        - 100 citations  → 0.60 score (transition)
        - 500 citations  → 0.73 score (sqrt dampening)
        - 1,000 citations → 0.80 score (log dampening)
        - 5,000 citations → 0.86 score
        - 10,000 citations → 0.89 score
        - 30,000 citations → 0.93 score (HOMA-IR paper from log)

        Args:
            citations: Citation count

        Returns:
            Citation score (0.0-1.0)
        """
        if citations <= 0:
            return 0.0

        # Linear range: 0-100 citations
        if citations <= 100:
            # 0.0 to 0.60 score
            return (citations / 100) * 0.60

        # Square root range: 100-1,000 citations
        elif citations <= 1000:
            # 0.60 to 0.80 score
            normalized = (citations - 100) / 900  # 0-1 range
            sqrt_score = math.sqrt(normalized)  # Dampened 0-1
            return 0.60 + (sqrt_score * 0.20)

        # Logarithmic range: 1,000+ citations
        else:
            # 0.80 to 1.0 score (asymptotic approach)
            # Using log10 for intuitive scaling:
            # 1,000 → 3.0, 10,000 → 4.0, 100,000 → 5.0
            log_citations = math.log10(citations)
            log_1000 = 3.0  # log10(1000)
            log_100000 = 5.0  # Practical maximum

            # Normalize to 0-1 range
            normalized = (log_citations - log_1000) / (log_100000 - log_1000)
            normalized = min(normalized, 1.0)  # Cap at 1.0

            return 0.80 + (normalized * 0.20)

    def _tokenize(self, text: str) -> Set[str]:
        """
        Tokenize text into terms.

        Args:
            text: Text to tokenize

        Returns:
            Set of lowercase tokens
        """
        if not text:
            return set()

        # Convert to lowercase
        text = text.lower()

        # Remove special characters, keep alphanumeric and spaces
        text = re.sub(r"[^a-z0-9\s]", " ", text)

        # Split and filter short tokens
        tokens = [t for t in text.split() if len(t) >= 2]  # Min 2 characters

        # Remove common stop words
        stop_words = {
            "the",
            "is",
            "at",
            "which",
            "on",
            "a",
            "an",
            "as",
            "are",
            "was",
            "were",
            "been",
            "be",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "must",
            "can",
            "of",
            "for",
            "in",
            "to",
            "and",
            "or",
        }
        tokens = [t for t in tokens if t not in stop_words]

        return set(tokens)

    def _extract_phrases(self, text: str, max_length: int = 3) -> List[str]:
        """
        Extract n-gram phrases from text.

        Args:
            text: Text to extract phrases from
            max_length: Maximum phrase length (words)

        Returns:
            List of phrases
        """
        words = text.split()
        phrases = []

        for n in range(2, min(max_length + 1, len(words) + 1)):
            for i in range(len(words) - n + 1):
                phrase = " ".join(words[i : i + n])
                phrases.append(phrase)

        return phrases

    def filter_by_score(
        self, results: List[PublicationSearchResult], min_score: float
    ) -> List[PublicationSearchResult]:
        """
        Filter results by minimum relevance score.

        Args:
            results: Scored results
            min_score: Minimum relevance score

        Returns:
            Filtered results
        """
        return [r for r in results if r.relevance_score >= min_score]

    def get_score_statistics(self, results: List[PublicationSearchResult]) -> Dict[str, float]:
        """
        Calculate scoring statistics.

        Args:
            results: Scored results

        Returns:
            Dictionary of statistics
        """
        if not results:
            return {}

        scores = [r.relevance_score for r in results]

        return {
            "mean": sum(scores) / len(scores),
            "median": sorted(scores)[len(scores) // 2],
            "min": min(scores),
            "max": max(scores),
            "std": math.sqrt(sum((s - sum(scores) / len(scores)) ** 2 for s in scores) / len(scores)),
        }
