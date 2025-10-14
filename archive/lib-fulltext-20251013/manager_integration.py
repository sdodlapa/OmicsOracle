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
from lib.fulltext.models import ContentType
from lib.fulltext.models import FullTextResult as NewFullTextResult
from lib.fulltext.models import SourceType

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


async def try_pdf_extraction(
    pdf_path: Path,
    extract_tables: bool = True,
    extract_images: bool = False,
    image_output_dir: Optional[Path] = None,
) -> NewFullTextResult:
    """
    Try to extract structured content from PDF.

    This is the PDF equivalent of try_pmc_xml_extraction().
    Uses camelot for tables (99-100% accuracy), PyMuPDF for text/images.

    Args:
        pdf_path: Path to PDF file
        extract_tables: Extract tables using camelot/pdfplumber
        extract_images: Extract embedded images
        image_output_dir: Directory to save extracted images

    Returns:
        NewFullTextResult with structured_content if successful
    """
    from lib.fulltext.pdf_extractor import PDFExtractor

    if not isinstance(pdf_path, Path):
        pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        return NewFullTextResult(
            success=False,
            error_message=f"PDF not found: {pdf_path}",
        )

    logger.info(f"Attempting PDF extraction for: {pdf_path.name}")

    try:
        # Initialize extractor
        extractor = PDFExtractor()

        # Check capabilities
        capabilities = extractor.get_capabilities()
        if not capabilities["can_extract_text"]:
            return NewFullTextResult(
                success=False,
                error_message="PyMuPDF not available - cannot extract PDF content",
            )

        # Extract structured content
        structured = extractor.extract_structured_content(
            pdf_path,
            extract_tables=extract_tables,
            extract_images=extract_images,
            image_output_dir=image_output_dir,
        )

        if structured is None:
            return NewFullTextResult(
                success=False,
                error_message="PDF extraction returned no content",
            )

        # Calculate quality indicators
        full_text = structured.get_full_text()
        indicators = {
            "has_abstract": bool(structured.abstract),
            "has_methods": bool(structured.get_methods_text()),
            "has_references": len(structured.references) > 0,
            "has_figures": len(structured.figures) > 0,
            "word_count": len(full_text.split()),
            "table_count": len(structured.tables),
            "image_count": len(structured.figures),
        }

        # Create result
        result = NewFullTextResult(
            success=True,
            content=full_text[:10000],  # First 10K chars for quick access
            structured_content=structured,
            content_type=ContentType.PDF,
            source=SourceType.PDF,
            source_url=str(pdf_path),
            has_abstract=indicators["has_abstract"],
            has_methods=indicators["has_methods"],
            has_references=indicators["has_references"],
            has_figures=indicators["has_figures"],
            word_count=indicators["word_count"],
        )

        result.quality_score = result.calculate_quality_score()

        logger.info(
            f"{pdf_path.name}: SUCCESS - {indicators['table_count']} tables, "
            f"{indicators['image_count']} images, "
            f"{len(structured.sections)} sections, "
            f"quality={result.quality_score:.2f}"
        )

        return result

    except Exception as e:
        logger.error(f"PDF extraction error for {pdf_path.name}: {e}", exc_info=True)
        return NewFullTextResult(
            success=False,
            error_message=f"Extraction error: {str(e)}",
            source=SourceType.PDF,
        )


def add_pdf_extraction_support(
    manager, cache_dir: Path = Path("data/fulltext"), extract_images: bool = False
):
    """
    Add PDF parsing support to existing FullTextManager.

    This extends the manager to parse PDFs when they're downloaded,
    not just return the URL/path. Provides structured extraction
    for PDF-only papers (arXiv, preprints, paywalled papers).

    Args:
        manager: Existing FullTextManager instance
        cache_dir: Directory for caching files
        extract_images: Whether to extract images (slower, uses more disk)

    Example:
        >>> manager = FullTextManager()
        >>> add_pmc_xml_support(manager)
        >>> add_pdf_extraction_support(manager)
        >>> await manager.initialize()
        >>> result = await manager.get_fulltext(publication)
        >>> # Now includes structured_content for PDFs!
    """

    async def _try_pdf_parse(self, pdf_path: Path):
        """
        Try to parse PDF content.

        This is added as a method to FullTextManager.
        """
        from omics_oracle_v2.lib.fulltext.manager import FullTextResult

        # Use the standalone function
        image_dir = cache_dir / "images" if extract_images else None

        new_result = await try_pdf_extraction(
            pdf_path, extract_tables=True, extract_images=extract_images, image_output_dir=image_dir
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
                "table_count": len(new_result.structured_content.tables),
                "image_count": len(new_result.structured_content.figures),
                "structured_content": new_result.structured_content,  # Full structured data
                "extraction_method": "pdf_parsed",
            }

            return FullTextResult(
                success=True,
                source="pdf_parsed",  # New source type
                content=new_result.content,
                pdf_path=pdf_path,
                metadata=metadata,
            )
        else:
            return FullTextResult(success=False, error=new_result.error_message)

    # Add method to manager
    manager._try_pdf_parse = _try_pdf_parse.__get__(manager, type(manager))

    logger.info("PDF extraction support added to FullTextManager")

    # Enhance get_fulltext to parse PDFs
    original_get_fulltext = manager.get_fulltext

    async def get_fulltext_enhanced(self, publication):
        """
        Enhanced get_fulltext with PMC XML priority + PDF parsing.

        Waterfall:
        1. PMC XML (if pmc_id available) → structured extraction
        2. Original waterfall → PDF URL/download
        3. PDF parsing (if PDF obtained) → structured extraction
        """
        if not self.initialized:
            await self.initialize()

        # Priority 0: Try PMC XML first (if available and integrated)
        pmc_id = getattr(publication, "pmc_id", None) or getattr(publication, "pmc", None)

        if pmc_id and hasattr(self, "_try_pmc_xml"):
            logger.debug(f"Trying PMC XML extraction for {pmc_id}")
            result = await self._try_pmc_xml(publication)
            if result.success:
                logger.info(f"✓ SUCCESS: PMC XML extraction for {pmc_id}")
                return result
            else:
                logger.debug(f"PMC XML failed: {result.error}")

        # Priority 1-8: Try original waterfall (gets PDF URL/path)
        logger.debug("Trying original waterfall (institutional, unpaywall, etc.)")
        result = await original_get_fulltext(publication)

        # Priority 9: If we got a PDF, try to parse it (NEW)
        if result.success and result.pdf_path:
            logger.debug(f"PDF obtained, attempting structured extraction: {result.pdf_path}")
            parsed = await self._try_pdf_parse(Path(result.pdf_path))

            if parsed.success:
                # Merge structured content into original result
                result.metadata = result.metadata or {}
                result.metadata.update(parsed.metadata)
                result.content = parsed.content

                logger.info(
                    f"✓ SUCCESS: PDF parsed - {parsed.metadata.get('table_count', 0)} tables, "
                    f"{parsed.metadata.get('image_count', 0)} images, "
                    f"quality={parsed.metadata.get('quality_score', 0):.2f}"
                )
            else:
                logger.debug(f"PDF parsing failed: {parsed.error}")
                # Still return original result with URL/path

        return result

    manager.get_fulltext = get_fulltext_enhanced.__get__(manager, type(manager))

    logger.info("FullTextManager waterfall enhanced with PDF parsing")


# For backwards compatibility with existing code
__all__ = [
    "try_pmc_xml_extraction",
    "try_pdf_extraction",
    "add_pmc_xml_support",
    "add_pdf_extraction_support",
]
