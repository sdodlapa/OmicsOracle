"""
Citation Filtering Utilities

Simple filters for publications based on recency, citations, etc.
NO LLM analysis - pure data filtering.
"""

from datetime import datetime
from typing import List, Optional

from omics_oracle_v2.lib.search_engines.citations.models import Publication


def filter_by_year_range(
    publications: List[Publication], min_year: Optional[int] = None, max_year: Optional[int] = None
) -> List[Publication]:
    """
    Filter publications by publication year range.

    Args:
        publications: List of publications to filter
        min_year: Minimum publication year (inclusive), None for no lower bound
        max_year: Maximum publication year (inclusive), None for no upper bound

    Returns:
        Filtered list of publications

    Example:
        >>> # Get papers from 2020-2025
        >>> recent = filter_by_year_range(papers, min_year=2020, max_year=2025)
    """
    filtered = []

    for pub in publications:
        if not pub.publication_date:
            continue

        year = pub.publication_date.year

        # Check min_year
        if min_year is not None and year < min_year:
            continue

        # Check max_year
        if max_year is not None and year > max_year:
            continue

        filtered.append(pub)

    return filtered


def filter_recent_publications(publications: List[Publication], years_back: int = 5) -> List[Publication]:
    """
    Filter publications to only recent ones (last N years).

    Args:
        publications: List of publications to filter
        years_back: Number of years back from current year (default: 5)

    Returns:
        Publications from the last N years

    Example:
        >>> # Get papers from last 5 years
        >>> recent = filter_recent_publications(papers, years_back=5)
    """
    current_year = datetime.now().year
    min_year = current_year - years_back

    return filter_by_year_range(publications, min_year=min_year, max_year=current_year)


def filter_by_citation_count(
    publications: List[Publication], min_citations: Optional[int] = None, max_citations: Optional[int] = None
) -> List[Publication]:
    """
    Filter publications by citation count.

    Args:
        publications: List of publications to filter
        min_citations: Minimum citation count (inclusive)
        max_citations: Maximum citation count (inclusive)

    Returns:
        Filtered list of publications

    Example:
        >>> # Get highly cited papers (100+ citations)
        >>> highly_cited = filter_by_citation_count(papers, min_citations=100)
    """
    filtered = []

    for pub in publications:
        citations = pub.citations or 0

        # Check min_citations
        if min_citations is not None and citations < min_citations:
            continue

        # Check max_citations
        if max_citations is not None and citations > max_citations:
            continue

        filtered.append(pub)

    return filtered


def rank_by_citations_and_recency(
    publications: List[Publication], citation_weight: float = 0.7, recency_weight: float = 0.3
) -> List[Publication]:
    """
    Rank publications by combination of citations and recency.

    Args:
        publications: List of publications to rank
        citation_weight: Weight for citation score (0-1, default: 0.7)
        recency_weight: Weight for recency score (0-1, default: 0.3)

    Returns:
        Publications sorted by combined score (highest first)

    Example:
        >>> # Rank balancing citations (70%) and recency (30%)
        >>> ranked = rank_by_citations_and_recency(papers)
    """
    current_year = datetime.now().year

    # Find max citations for normalization
    max_citations = max((p.citations or 0 for p in publications), default=1)

    def calculate_score(pub: Publication) -> float:
        # Citation score (normalized 0-1)
        citation_score = (pub.citations or 0) / max_citations if max_citations > 0 else 0

        # Recency score (0-1, where 1 = current year)
        if pub.publication_date:
            years_old = current_year - pub.publication_date.year
            # Decay over 10 years
            recency_score = max(0, 1 - (years_old / 10))
        else:
            recency_score = 0

        # Combined score
        return (citation_weight * citation_score) + (recency_weight * recency_score)

    # Sort by score (highest first)
    return sorted(publications, key=calculate_score, reverse=True)
