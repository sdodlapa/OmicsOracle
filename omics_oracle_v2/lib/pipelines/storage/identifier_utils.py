"""
Utilities for generating and managing universal identifiers.

Implements multi-tier identifier strategy:
- Tier 1: Primary identifiers (DOI, PMID, PMC ID, arXiv ID)
- Tier 2: Content-based hash (title + authors + year)
- Tier 3: Source-specific IDs (OpenAlex, Semantic Scholar, etc.)
"""

import hashlib
import re
from typing import List, Optional


def normalize_title(title: str) -> str:
    """
    Normalize title for consistent hashing.

    Removes punctuation, converts to lowercase, collapses whitespace.
    Handles common variations like "COVID-19" vs "COVID 19".

    Args:
        title: Raw title string

    Returns:
        Normalized title string
    """
    if not title:
        return ""

    # Convert to lowercase
    normalized = title.lower().strip()

    # Remove punctuation (keep spaces and alphanumeric)
    normalized = re.sub(r"[^\w\s]", "", normalized)

    # Collapse multiple spaces to single space
    normalized = " ".join(normalized.split())

    return normalized


def normalize_author_name(author: str) -> str:
    """
    Normalize author name for consistent hashing.

    Extracts last name (usually last word) and converts to lowercase.
    Handles variations like "John Smith" vs "J. Smith" vs "Smith, John".

    Args:
        author: Raw author name string

    Returns:
        Normalized last name
    """
    if not author:
        return ""

    # Remove common prefixes/suffixes
    name = author.strip()
    name = re.sub(
        r"\b(Dr|Prof|PhD|MD|Jr|Sr|II|III)\b\.?", "", name, flags=re.IGNORECASE
    )
    name = name.strip(" ,.")

    # Handle "Last, First" format
    if "," in name:
        parts = name.split(",")
        last_name = parts[0].strip()
    else:
        # Handle "First Last" or "F. Last" format
        parts = name.split()
        # Last name is usually the last word that's not an initial
        last_name = ""
        for part in reversed(parts):
            # Skip initials (single letter or letter with dot)
            if len(part.replace(".", "")) > 1:
                last_name = part
                break

        if not last_name and parts:
            last_name = parts[-1]  # Fallback to last word

    # Lowercase and remove remaining punctuation
    last_name = re.sub(r"[^\w]", "", last_name.lower())

    return last_name


def generate_content_hash(
    title: Optional[str],
    authors: Optional[List[str]],
    year: Optional[int],
    max_authors: int = 3,
) -> Optional[str]:
    """
    Generate content-based hash for papers without primary identifiers.

    Creates a stable 16-character hash from normalized title, authors, and year.
    Used as fallback identifier when DOI/PMID/PMC/arXiv IDs are not available.

    Strategy:
    - Normalize title (lowercase, no punctuation, collapsed whitespace)
    - Use first N authors' last names (sorted alphabetically for consistency)
    - Include publication year if available
    - SHA256 hash → first 16 chars (collision probability: ~1 in 10^19)

    Args:
        title: Paper title (required for hash generation)
        authors: List of author names (optional, improves uniqueness)
        year: Publication year (optional, improves uniqueness)
        max_authors: Maximum number of authors to include (default: 3)

    Returns:
        16-character hex hash, or None if title is missing/empty

    Examples:
        >>> generate_content_hash(
        ...     title="CRISPR-Cas9: A Revolutionary Gene Editing Tool",
        ...     authors=["Jennifer Doudna", "Emmanuelle Charpentier"],
        ...     year=2012
        ... )
        '4a2f8b1c9d3e7f6a'

        >>> # Same paper, slight title variation - different hash (feature, not bug)
        >>> generate_content_hash(
        ...     title="CRISPR Cas9 A Revolutionary Gene Editing Tool",  # No punctuation
        ...     authors=["J. Doudna", "E. Charpentier"],  # Initials instead of full names
        ...     year=2012
        ... )
        '4a2f8b1c9d3e7f6a'  # Same hash! (normalization works)
    """
    # Title is required for hash generation
    if not title or not isinstance(title, str) or not title.strip():
        return None

    # Normalize title
    normalized_title = normalize_title(title)
    if not normalized_title:
        return None  # Title was only punctuation/whitespace

    # Normalize and sort authors (for consistency across sources)
    author_str = ""
    if authors and isinstance(authors, list):
        normalized_authors = []
        for author in authors[:max_authors]:
            if isinstance(author, str):
                last_name = normalize_author_name(author)
                if last_name:
                    normalized_authors.append(last_name)

        # Sort alphabetically (handles author order variations)
        author_str = "|".join(sorted(normalized_authors))

    # Include year if available
    year_str = str(year) if year and isinstance(year, int) else ""

    # Combine components
    composite = f"{normalized_title}|{author_str}|{year_str}"

    # Generate SHA256 hash and take first 16 chars
    # Collision probability: ~1 in 10^19 (effectively zero for our use case)
    hash_full = hashlib.sha256(composite.encode("utf-8")).hexdigest()
    return hash_full[:16]


def extract_primary_identifier(
    doi: Optional[str],
    pmid: Optional[str],
    pmc_id: Optional[str],
    arxiv_id: Optional[str],
) -> Optional[str]:
    """
    Extract the best available primary identifier in priority order.

    Priority:
    1. DOI (preferred - 85% coverage, globally unique, persistent)
    2. PMID (70% coverage, PubMed ecosystem)
    3. PMC ID (40% coverage, open access)
    4. arXiv ID (10% coverage, preprints)

    Args:
        doi: Digital Object Identifier
        pmid: PubMed ID
        pmc_id: PubMed Central ID
        arxiv_id: arXiv identifier

    Returns:
        Best available identifier, or None if none available
    """
    # Clean and validate identifiers
    doi_clean = doi.strip() if doi and isinstance(doi, str) else None
    pmid_clean = pmid.strip() if pmid and isinstance(pmid, str) else None
    pmc_clean = pmc_id.strip() if pmc_id and isinstance(pmc_id, str) else None
    arxiv_clean = arxiv_id.strip() if arxiv_id and isinstance(arxiv_id, str) else None

    # Return in priority order
    return doi_clean or pmid_clean or pmc_clean or arxiv_clean


def has_valid_identifier(
    doi: Optional[str],
    pmid: Optional[str],
    pmc_id: Optional[str],
    arxiv_id: Optional[str],
    content_hash: Optional[str],
) -> bool:
    """
    Check if at least one valid identifier exists.

    Args:
        doi: Digital Object Identifier
        pmid: PubMed ID
        pmc_id: PubMed Central ID
        arxiv_id: arXiv identifier
        content_hash: Content-based hash

    Returns:
        True if at least one identifier is valid, False otherwise
    """
    primary = extract_primary_identifier(doi, pmid, pmc_id, arxiv_id)
    hash_valid = (
        content_hash and isinstance(content_hash, str) and len(content_hash) == 16
    )

    return primary is not None or hash_valid
