"""
Utility functions for AI summarization.

Provides helpers for metadata cleaning, token estimation, and text processing.
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def prepare_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clean and prepare metadata for LLM processing.

    Args:
        metadata: Raw metadata dictionary

    Returns:
        Cleaned metadata with standardized fields
    """
    # Handle case where metadata might be a string
    if isinstance(metadata, str):
        return {
            "accession": "Unknown",
            "title": metadata[:200] if len(metadata) > 200 else str(metadata),
            "summary": str(metadata),
            "type": "Unknown",
            "organism": "Unknown",
            "platform": "Unknown",
            "sample_count": 0,
            "submission_date": "",
            "last_update_date": "",
        }

    # Extract key fields and clean them
    cleaned = {
        "accession": metadata.get("accession", metadata.get("geo_id", "Unknown")),
        "title": metadata.get("title", metadata.get("name", "")),
        "summary": metadata.get("summary", metadata.get("description", "")),
        "type": metadata.get("type", metadata.get("study_type", "")),
        "organism": metadata.get("organism", metadata.get("species", "")),
        "platform": metadata.get("platform", metadata.get("technology", "")),
        "sample_count": len(metadata.get("samples", [])),
        "submission_date": metadata.get("submission_date", metadata.get("date", "")),
        "last_update_date": metadata.get("last_update_date", ""),
    }

    # Add sample information if available
    samples = metadata.get("samples", [])
    if samples and isinstance(samples, list):
        sample_titles = []
        for s in samples[:5]:  # Limit to first 5 samples
            if isinstance(s, dict):
                sample_titles.append(s.get("title", s.get("name", "")))
            elif isinstance(s, str):
                sample_titles.append(s)
        if sample_titles:
            cleaned["sample_examples"] = sample_titles

    return cleaned


def estimate_tokens(text: str) -> int:
    """
    Estimate token count for text.

    Uses approximate 1.3 tokens per word ratio (common for English).

    Args:
        text: Input text

    Returns:
        Estimated token count
    """
    if not text:
        return 0
    # Rough estimate: ~1.3 tokens per word for English text
    word_count = len(text.split())
    return int(word_count * 1.3)


def extract_technical_details(metadata: Dict[str, Any]) -> str:
    """
    Extract technical details from metadata.

    Args:
        metadata: Cleaned metadata dictionary

    Returns:
        Formatted technical details string or empty if no details
    """
    technical_info = []

    if metadata.get("platform") and metadata["platform"] != "Unknown":
        technical_info.append(f"Platform: {metadata['platform']}")

    if metadata.get("sample_count") and metadata["sample_count"] > 0:
        technical_info.append(f"Samples: {metadata['sample_count']}")

    if metadata.get("organism") and metadata["organism"] != "Unknown":
        technical_info.append(f"Organism: {metadata['organism']}")

    if metadata.get("submission_date"):
        technical_info.append(f"Submitted: {metadata['submission_date']}")

    return " | ".join(technical_info) if technical_info else ""


def aggregate_batch_statistics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregate statistics from multiple dataset results.

    Args:
        results: List of dataset result dictionaries

    Returns:
        Dictionary with aggregated statistics
    """
    if not results:
        return {
            "total_datasets": 0,
            "total_samples": 0,
            "organisms": [],
            "platforms": [],
            "study_types": [],
        }

    organisms = set()
    platforms = set()
    types = set()
    total_samples = 0

    for result in results:
        metadata = result.get("metadata", {})

        if metadata.get("organism"):
            organisms.add(metadata["organism"])

        if metadata.get("platform"):
            platforms.add(metadata["platform"])

        if metadata.get("type"):
            types.add(metadata["type"])

        # Count samples
        samples = metadata.get("samples", [])
        if isinstance(samples, list):
            total_samples += len(samples)
        elif isinstance(samples, int):
            total_samples += samples

    return {
        "total_datasets": len(results),
        "total_samples": total_samples,
        "organisms": sorted(list(organisms)),
        "platforms": sorted(list(platforms)),
        "study_types": sorted(list(types)),
    }


def truncate_text(text: str, max_length: int = 1000, suffix: str = "...") -> str:
    """
    Truncate text to maximum length.

    Args:
        text: Input text
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated text
    """
    if not text or len(text) <= max_length:
        return text

    return text[: max_length - len(suffix)] + suffix
