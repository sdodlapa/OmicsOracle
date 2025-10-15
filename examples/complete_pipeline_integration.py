"""
Complete Pipeline Integration Example

Demonstrates how to use PipelineCoordinator with all 4 pipelines.
Shows the unified database + storage system in action.

Usage:
    python examples/complete_pipeline_integration.py
"""

import logging
from pathlib import Path

from omics_oracle_v2.lib.pipelines import (
    FullTextManager,
    GEOCitationDiscovery,
    PDFDownloadManager,
    PDFExtractor,
    PipelineCoordinator,
)

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def process_complete_workflow(geo_id: str):
    """
    Complete workflow: P1 -> P2 -> P3 -> P4 with unified database.

    Args:
        geo_id: GEO dataset ID to process
    """
    # Initialize coordinator
    coordinator = PipelineCoordinator(db_path="data/database/omics_oracle.db", storage_path="data")

    logger.info(f"=" * 80)
    logger.info(f"Processing GEO Dataset: {geo_id}")
    logger.info(f"=" * 80)

    # =========================================================================
    # PIPELINE 1: Citation Discovery
    # =========================================================================
    logger.info("\n[P1] Starting Citation Discovery...")

    discovery = GEOCitationDiscovery()
    citations = discovery.get_citations_for_geo(geo_id, max_results=10)

    # Save to database
    for citation in citations:
        try:
            pmid = citation.get("pmid")
            if not pmid:
                continue

            # Save citation data
            coordinator.save_citation_discovery(geo_id=geo_id, pmid=pmid, citation_data=citation)

            logger.info(f"  [OK] Saved citation: {pmid} - {citation.get('title', 'N/A')[:50]}")

        except Exception as e:
            logger.error(f"  [ERROR] Error saving citation {pmid}: {e}")

    # Update GEO dataset metadata
    geo_metadata = discovery.get_geo_metadata(geo_id)
    coordinator.update_geo_dataset(geo_id, metadata=geo_metadata)

    logger.info(f"[P1] Complete: {len(citations)} citations saved")

    # =========================================================================
    # PIPELINE 2: URL Discovery
    # =========================================================================
    logger.info("\n[P2] Starting URL Discovery...")

    url_manager = FullTextManager()

    for citation in citations:
        pmid = citation.get("pmid")
        if not pmid:
            continue

        try:
            # Get all URLs
            urls = url_manager.get_all_fulltext_urls(
                pmid=pmid,
                doi=citation.get("doi"),
                pmc_id=citation.get("pmc_id"),
                title=citation.get("title"),
            )

            # Format URLs for database
            url_list = [
                {
                    "url": url.get("url"),
                    "type": url.get("type"),
                    "source": url.get("source"),
                    "priority": url.get("priority"),
                }
                for url in urls
            ]

            # Save to database
            sources_queried = list(set(u.get("source") for u in url_list))
            coordinator.save_url_discovery(
                geo_id=geo_id, pmid=pmid, urls=url_list, sources_queried=sources_queried
            )

            logger.info(f"  [OK] Found {len(url_list)} URLs for {pmid}")

        except Exception as e:
            logger.error(f"  [ERROR] Error finding URLs for {pmid}: {e}")

    logger.info(f"[P2] Complete: URL discovery done")

    # =========================================================================
    # PIPELINE 3: PDF Download
    # =========================================================================
    logger.info("\n[P3] Starting PDF Download...")

    pdf_manager = PDFDownloadManager()

    for citation in citations:
        pmid = citation.get("pmid")
        if not pmid:
            continue

        try:
            # Get URL discovery results
            url_discovery = coordinator.db.get_url_discovery(geo_id, pmid)
            if not url_discovery:
                logger.warning(f"  [WARN]  No URLs found for {pmid}")
                continue

            # Download PDF
            pdf_path = pdf_manager.download_pdf(
                pmid=pmid,
                doi=citation.get("doi"),
                pmc_id=citation.get("pmc_id"),
                title=citation.get("title"),
            )

            if pdf_path and Path(pdf_path).exists():
                # Save to GEO-organized storage + database
                pdf_info = coordinator.save_pdf_acquisition(
                    geo_id=geo_id,
                    pmid=pmid,
                    pdf_path=Path(pdf_path),
                    source_url=url_discovery.urls_json,  # Could extract best URL
                    source_type="waterfall",
                    download_method="direct",
                )

                logger.info(f"  [OK] Downloaded PDF for {pmid} ({pdf_info['size_bytes']} bytes)")
            else:
                logger.warning(f"  [WARN]  No PDF available for {pmid}")

        except Exception as e:
            logger.error(f"  [ERROR] Error downloading PDF for {pmid}: {e}")

    logger.info(f"[P3] Complete: PDF downloads done")

    # =========================================================================
    # PIPELINE 4: Content Extraction
    # =========================================================================
    logger.info("\n[P4] Starting Content Extraction...")

    extractor = PDFExtractor()

    for citation in citations:
        pmid = citation.get("pmid")
        if not pmid:
            continue

        try:
            # Get PDF path from storage
            pdf_path = coordinator.storage.get_pdf_path(geo_id, pmid)
            if not pdf_path:
                logger.warning(f"  [WARN]  No PDF stored for {pmid}")
                continue

            # Extract basic content
            text = extractor.extract_text(str(pdf_path))
            page_count = extractor.get_page_count(str(pdf_path))

            if text:
                # Calculate metrics
                word_count = len(text.split())
                char_count = len(text)

                # Basic quality assessment
                quality = min(1.0, word_count / 5000)  # Simple quality metric
                grade = "A" if quality > 0.8 else ("B" if quality > 0.6 else "C")

                # Save basic extraction
                coordinator.save_content_extraction(
                    geo_id=geo_id,
                    pmid=pmid,
                    extraction_data={
                        "full_text": text,
                        "page_count": page_count,
                        "word_count": word_count,
                        "char_count": char_count,
                        "quality": quality,
                        "grade": grade,
                        "has_readable_text": True,
                        "extractor_used": "PDFExtractor",
                    },
                )

                logger.info(f"  [OK] Extracted content for {pmid} ({word_count} words, grade: {grade})")

                # TODO: Add enrichers (sections, tables, references)
                # For now, just save basic enrichment
                coordinator.save_enriched_content(
                    geo_id=geo_id,
                    pmid=pmid,
                    enriched_data={
                        "sections": [],  # Would use SectionDetector
                        "tables": [],  # Would use TableExtractor
                        "references": [],  # Would use ReferenceParser
                        "enrichers_applied": [],
                    },
                )

            else:
                logger.warning(f"  [WARN]  No text extracted for {pmid}")

        except Exception as e:
            logger.error(f"  [ERROR] Error extracting content for {pmid}: {e}")

    logger.info(f"[P4] Complete: Content extraction done")

    # =========================================================================
    # SUMMARY
    # =========================================================================
    logger.info("\n" + "=" * 80)
    logger.info("PROCESSING SUMMARY")
    logger.info("=" * 80)

    progress = coordinator.get_geo_progress(geo_id)
    logger.info(f"GEO Dataset: {geo_id}")
    logger.info(f"  Total Publications: {progress['total_publications']}")
    logger.info(f"  Citations Saved:    {progress['citations']}")
    logger.info(f"  URLs Found:         {progress['urls']}")
    logger.info(f"  PDFs Downloaded:    {progress['pdfs']}")
    logger.info(f"  Content Extracted:  {progress['extracted']}")
    logger.info(f"  Enriched Papers:    {progress['enriched']}")
    logger.info(f"  Completion Rate:    {progress['completion_rate']:.1f}%")

    stats = coordinator.db.get_database_statistics()
    logger.info(f"\nDatabase Statistics:")
    logger.info(f"  Total Publications: {stats['total_publications']}")
    logger.info(f"  PDFs Downloaded:    {stats['pdfs_downloaded']}")
    logger.info(f"  Content Extracted:  {stats['content_extracted']}")
    logger.info(f"  High Quality:       {stats['high_quality_papers']}")

    logger.info("\n[OK] Complete workflow finished!")


if __name__ == "__main__":
    # Example: Process a GEO dataset
    GEO_ID = "GSE12345"  # Replace with actual GEO ID

    try:
        process_complete_workflow(GEO_ID)
    except KeyboardInterrupt:
        logger.info("\n\n[WARN]  Processing interrupted by user")
    except Exception as e:
        logger.error(f"\n\n[ERROR] Error: {e}", exc_info=True)
