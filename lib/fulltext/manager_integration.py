"""
Integration layer: New structured full-text components with existing FullTextManager

This module provides helper methods to integrate the new structured content
extraction (lib/fulltext/) with the existing OmicsOracle FullTextManager.

Usage:
    # Option 1: Add as methods to existing FullTextManager
    from lib.fulltext.manager_integration import add_pmc_xml_support
    manager = FullTextManager()
    add_pmc_xml_support(manager)

    # Option 2: Use standalone helper
    from lib.fulltext.manager_integration import try_pmc_xml_extraction
    result = await try_pmc_xml_extraction(publication, cache_dir="data/fulltext")
"""

import logging
from pathlib import Path
from typing import Optional

from lib.fulltext.content_extractor import ContentExtractor
from lib.fulltext.content_fetcher import ContentFetcher
from lib.fulltext.models import (
    ContentType,
    FullTextResult as NewFullTextResult,
    SourceType,
)

logger = logging.getLogger(__name__)


async def try_pmc_xml_extraction(
    publication,
    cache_dir: Path = Path("data/fulltext"),
    api_key: Optional[str] = None,
) -> NewFullTextResult:
    """
    Try to fetch and extract structured content from PMC XML.

    This is a standalone function that can be called independently or
    integrated into FullTextManager.

    Args:
        publication: Publication object with pmc_id attribute
        cache_dir: Directory for caching XML files
        api_key: Optional NCBI API key (10 req/sec vs 3 without)

    Returns:
        NewFullTextResult with structured_content if successful
    """
    # Check if publication has PMC ID
    pmc_id = getattr(publication, "pmc_id", None) or getattr(publication, "pmc", None)

    if not pmc_id:
        return NewFullTextResult(
            success=False,
            error_message="No PMC ID available",
        )

    logger.info(f"Attempting PMC XML extraction for: {pmc_id}")

    try:
        # Initialize fetcher and extractor
        fetcher = ContentFetcher(
            cache_dir=cache_dir,
            api_key=api_key,
            requests_per_second=10.0 if api_key else 3.0,
        )

        extractor = ContentExtractor()

        # Step 1: Fetch XML from PMC
        success, xml_content, error = await fetcher.fetch_xml(
            source=SourceType.PMC,
            identifier=pmc_id,
            use_cache=True,
        )

        if not success:
            return NewFullTextResult(
                success=False,
                error_message=f"PMC XML fetch failed: {error}",
                source=SourceType.PMC,
            )

        # Step 2: Extract structured content
        cache_path = fetcher.get_cache_path(
            ContentType.XML,
            SourceType.PMC,
            pmc_id.replace("PMC", ""),
        )

        structured = extractor.extract_structured_content(
            xml_content,
            source_path=str(cache_path),
        )

        if structured is None:
            # Fallback to plain text
            logger.warning(f"{pmc_id}: Structured extraction failed, using plain text")
            plain_text = extractor.extract_text(xml_content)

            return NewFullTextResult(
                success=True,
                content=plain_text,
                structured_content=None,
                content_type=ContentType.XML,
                source=SourceType.PMC,
                source_url=f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc_id}/",
                quality_score=0.5,  # Lower score for plain text
            )

        # Step 3: Calculate quality indicators
        indicators = extractor.calculate_quality_score(xml_content, structured, ContentType.XML)

        # Step 4: Create result
        full_text = structured.get_full_text()

        result = NewFullTextResult(
            success=True,
            content=full_text[:10000],  # First 10K chars for quick access
            structured_content=structured,
            content_type=ContentType.XML,
            source=SourceType.PMC,
            source_url=f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc_id}/",
            has_abstract=indicators["has_abstract"],
            has_methods=indicators["has_methods"],
            has_references=indicators["has_references"],
            has_figures=indicators["has_figures"],
            word_count=indicators["word_count"],
        )

        result.quality_score = result.calculate_quality_score()

        logger.info(
            f"{pmc_id}: SUCCESS - {len(structured.authors)} authors, "
            f"{len(structured.sections)} sections, "
            f"{len(structured.references)} refs, "
            f"quality={result.quality_score:.2f}"
        )

        return result

    except Exception as e:
        logger.error(f"PMC XML extraction error for {pmc_id}: {e}", exc_info=True)
        return NewFullTextResult(
            success=False,
            error_message=f"Extraction error: {str(e)}",
            source=SourceType.PMC,
        )


def add_pmc_xml_support(manager, cache_dir: Path = Path("data/fulltext")):
    """
    Add PMC XML extraction support to existing FullTextManager.

    This monkey-patches the manager to add _try_pmc_xml() method and
    updates the waterfall to include PMC XML as Priority 0.

    Args:
        manager: Existing FullTextManager instance
        cache_dir: Directory for caching XML files

    Example:
        >>> manager = FullTextManager()
        >>> add_pmc_xml_support(manager)
        >>> await manager.initialize()
        >>> result = await manager.get_fulltext(publication)
    """

    async def _try_pmc_xml(self, publication):
        """
        Try to fetch and extract PMC XML content.

        This is added as a method to FullTextManager.
        """
        from omics_oracle_v2.lib.fulltext.manager import FullTextResult

        # Use the standalone function
        new_result = await try_pmc_xml_extraction(
            publication,
            cache_dir=cache_dir,
            api_key=None,  # TODO: Get from config
        )

        # Convert new FullTextResult to old FullTextResult
        if new_result.success:
            # Store structured content in metadata for downstream use
            metadata = {
                "quality_score": new_result.quality_score,
                "has_abstract": new_result.has_abstract,
                "has_methods": new_result.has_methods,
                "has_references": new_result.has_references,
                "has_figures": new_result.has_figures,
                "word_count": new_result.word_count,
                "structured_content": new_result.structured_content,  # Full structured data
            }

            return FullTextResult(
                success=True,
                source="pmc_xml",  # New source type
                content=new_result.content,
                url=new_result.source_url,
                metadata=metadata,
            )
        else:
            return FullTextResult(
                success=False,
                error=new_result.error_message,
            )

    # Add method to manager
    manager._try_pmc_xml = _try_pmc_xml.__get__(manager, type(manager))

    logger.info("PMC XML support added to FullTextManager")

    # Update waterfall (if you want to modify get_fulltext dynamically)
    # This is optional - alternatively, user can manually update their waterfall
    original_get_fulltext = manager.get_fulltext

    async def get_fulltext_with_pmc(self, publication):
        """Enhanced get_fulltext with PMC XML as Priority 0."""
        if not self.initialized:
            await self.initialize()

        # Try PMC XML first
        pmc_id = getattr(publication, "pmc_id", None) or getattr(publication, "pmc", None)

        if pmc_id:
            result = await self._try_pmc_xml(publication)
            if result.success:
                logger.info(f"SUCCESS: Got structured PMC XML for {pmc_id}")
                return result

        # Fall back to original waterfall
        return await original_get_fulltext(publication)

    manager.get_fulltext = get_fulltext_with_pmc.__get__(manager, type(manager))

    logger.info("FullTextManager waterfall updated with PMC XML priority")


# For backwards compatibility with existing code
__all__ = [
    "try_pmc_xml_extraction",
    "add_pmc_xml_support",
]
