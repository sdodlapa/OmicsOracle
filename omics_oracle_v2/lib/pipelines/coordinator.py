"""
Unified Pipeline Coordinator

Coordinates all pipelines (P1->P2->P3->P4) with unified database and storage.
Provides high-level interface for complete publication processing.

Example:
    coordinator = PipelineCoordinator(
        db_path="data/database/omics_oracle.db",
        storage_path="data"
    )

    # Process single publication
    result = coordinator.process_publication(
        geo_id="GSE12345",
        pmid="12345678"
    )

    # Process entire GEO dataset
    results = coordinator.process_geo_dataset("GSE12345")
"""

import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional

from omics_oracle_v2.lib.storage import (
    ContentExtraction,
    EnrichedContent,
    GEODataset,
    GEOStorage,
    PDFAcquisition,
    UnifiedDatabase,
    UniversalIdentifier,
    URLDiscovery,
    now_iso,
)

logger = logging.getLogger(__name__)


class PipelineCoordinator:
    """
    Coordinates all pipelines with unified database and storage.

    Manages the complete flow:
    P1 (Citation Discovery) -> P2 (URL Discovery) ->
    P3 (PDF Acquisition) -> P4 (Content Extraction)

    Features:
    - Automatic database recording
    - GEO-centric file organization
    - Transaction support
    - Error handling and logging
    - Progress tracking
    """

    def __init__(
        self,
        db_path: str | Path = "data/database/omics_oracle.db",
        storage_path: str | Path = "data",
    ):
        """
        Initialize coordinator.

        Args:
            db_path: Path to unified database
            storage_path: Base path for file storage
        """
        self.db = UnifiedDatabase(db_path)
        self.storage = GEOStorage(storage_path)

        logger.info(
            f"Initialized PipelineCoordinator\n" f"  Database: {db_path}\n" f"  Storage:  {storage_path}"
        )

    # =========================================================================
    # PIPELINE 1: Citation Discovery
    # =========================================================================

    def save_citation_discovery(
        self,
        geo_id: str,
        pmid: str,
        citation_data: Dict,
    ) -> None:
        """
        Save citation discovery results to database.

        Args:
            geo_id: GEO dataset ID
            pmid: PubMed ID
            citation_data: Citation data from P1
                Expected keys: title, authors, journal, year, doi, pmc_id, etc.
        """
        start_time = time.time()

        try:
            # Create universal identifier
            identifier = UniversalIdentifier(
                geo_id=geo_id,
                pmid=pmid,
                doi=citation_data.get("doi"),
                pmc_id=citation_data.get("pmc_id"),
                arxiv_id=citation_data.get("arxiv_id"),
                title=citation_data.get("title"),
                authors=json.dumps(citation_data.get("authors", [])),
                journal=citation_data.get("journal"),
                publication_year=citation_data.get("year"),
                publication_date=citation_data.get("publication_date"),
            )

            # Save to database
            self.db.insert_universal_identifier(identifier)

            # Log success
            duration_ms = int((time.time() - start_time) * 1000)
            self.db.log_event(
                geo_id=geo_id,
                pmid=pmid,
                pipeline="P1",
                event_type="success",
                message=f"Saved citation: {citation_data.get('title', 'N/A')[:50]}",
                duration_ms=duration_ms,
            )

            logger.info(f"Saved citation discovery: {geo_id}/{pmid}")

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            self.db.log_event(
                geo_id=geo_id,
                pmid=pmid,
                pipeline="P1",
                event_type="error",
                message=str(e),
                duration_ms=duration_ms,
                error_type=type(e).__name__,
                error_traceback=str(e),
            )
            logger.error(f"Error saving citation: {e}")
            raise

    def update_geo_dataset(
        self,
        geo_id: str,
        metadata: Optional[Dict] = None,
    ) -> None:
        """
        Update GEO dataset metadata.

        Args:
            geo_id: GEO dataset ID
            metadata: GEO metadata (title, summary, organism, platform)
        """
        if metadata is None:
            metadata = {}

        dataset = GEODataset(
            geo_id=geo_id,
            title=metadata.get("title"),
            summary=metadata.get("summary"),
            organism=metadata.get("organism"),
            platform=metadata.get("platform"),
        )

        self.db.insert_geo_dataset(dataset)
        logger.info(f"Updated GEO dataset: {geo_id}")

    # =========================================================================
    # PIPELINE 2: URL Discovery
    # =========================================================================

    def save_url_discovery(
        self,
        geo_id: str,
        pmid: str,
        urls: List[Dict],
        sources_queried: List[str],
    ) -> None:
        """
        Save URL discovery results to database.

        Args:
            geo_id: GEO dataset ID
            pmid: PubMed ID
            urls: List of URL objects with metadata
            sources_queried: List of source names queried
        """
        start_time = time.time()

        try:
            # Count URLs by source
            pubmed_urls = sum(1 for u in urls if u.get("source") == "pubmed")
            unpaywall_urls = sum(1 for u in urls if u.get("source") == "unpaywall")
            europepmc_urls = sum(1 for u in urls if u.get("source") == "europepmc")
            other_urls = len(urls) - pubmed_urls - unpaywall_urls - europepmc_urls

            # Determine best URL type
            has_pdf = any(u.get("type") == "pdf" for u in urls)
            has_html = any(u.get("type") == "html" for u in urls)
            best_url_type = "pdf" if has_pdf else ("html" if has_html else "none")

            # Create discovery record
            discovery = URLDiscovery(
                geo_id=geo_id,
                pmid=pmid,
                urls_json=json.dumps(urls),
                sources_queried=json.dumps(sources_queried),
                url_count=len(urls),
                pubmed_urls=pubmed_urls,
                unpaywall_urls=unpaywall_urls,
                europepmc_urls=europepmc_urls,
                other_urls=other_urls,
                has_pdf_url=has_pdf,
                has_html_url=has_html,
                best_url_type=best_url_type,
            )

            # Save to database
            self.db.insert_url_discovery(discovery)

            # Log success
            duration_ms = int((time.time() - start_time) * 1000)
            self.db.log_event(
                geo_id=geo_id,
                pmid=pmid,
                pipeline="P2",
                event_type="success",
                message=f"Found {len(urls)} URLs from {len(sources_queried)} sources",
                duration_ms=duration_ms,
            )

            logger.info(f"Saved URL discovery: {geo_id}/{pmid} ({len(urls)} URLs)")

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            self.db.log_event(
                geo_id=geo_id,
                pmid=pmid,
                pipeline="P2",
                event_type="error",
                message=str(e),
                duration_ms=duration_ms,
                error_type=type(e).__name__,
            )
            logger.error(f"Error saving URL discovery: {e}")
            raise

    # =========================================================================
    # PIPELINE 3: PDF Acquisition
    # =========================================================================

    def save_pdf_acquisition(
        self,
        geo_id: str,
        pmid: str,
        pdf_path: Path,
        source_url: Optional[str] = None,
        source_type: Optional[str] = None,
        download_method: Optional[str] = None,
    ) -> Dict:
        """
        Save PDF to storage and record in database.

        Args:
            geo_id: GEO dataset ID
            pmid: PubMed ID
            pdf_path: Path to downloaded PDF
            source_url: URL where PDF was downloaded from
            source_type: Source type (pubmed, unpaywall, europepmc, manual)
            download_method: Method used (direct, selenium, manual)

        Returns:
            Dictionary with save results
        """
        start_time = time.time()

        try:
            # Save PDF to GEO-organized storage
            pdf_info = self.storage.save_pdf(
                geo_id=geo_id, pmid=pmid, source_path=pdf_path, verify_after_save=True
            )

            # Create acquisition record
            acquisition = PDFAcquisition(
                geo_id=geo_id,
                pmid=pmid,
                pdf_path=pdf_info["pdf_path"],
                pdf_hash_sha256=pdf_info["sha256"],
                pdf_size_bytes=pdf_info["size_bytes"],
                source_url=source_url,
                source_type=source_type,
                download_method=download_method,
                status="downloaded" if pdf_info["verified"] else "failed",
                verified_at=now_iso() if pdf_info["verified"] else None,
            )

            # Save to database
            self.db.insert_pdf_acquisition(acquisition)

            # Log success
            duration_ms = int((time.time() - start_time) * 1000)
            self.db.log_event(
                geo_id=geo_id,
                pmid=pmid,
                pipeline="P3",
                event_type="success",
                message=f"Saved PDF ({pdf_info['size_bytes']} bytes)",
                duration_ms=duration_ms,
            )

            logger.info(f"Saved PDF: {geo_id}/{pmid} ({pdf_info['size_bytes']} bytes)")

            return pdf_info

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            self.db.log_event(
                geo_id=geo_id,
                pmid=pmid,
                pipeline="P3",
                event_type="error",
                message=str(e),
                duration_ms=duration_ms,
                error_type=type(e).__name__,
            )
            logger.error(f"Error saving PDF: {e}")
            raise

    # =========================================================================
    # PIPELINE 4: Content Extraction
    # =========================================================================

    def save_content_extraction(
        self,
        geo_id: str,
        pmid: str,
        extraction_data: Dict,
    ) -> None:
        """
        Save basic content extraction results.

        Args:
            geo_id: GEO dataset ID
            pmid: PubMed ID
            extraction_data: Extraction data from P4
                Expected keys: full_text, page_count, word_count, quality, grade, etc.
        """
        start_time = time.time()

        try:
            # Create extraction record
            extraction = ContentExtraction(
                geo_id=geo_id,
                pmid=pmid,
                full_text=extraction_data.get("full_text"),
                page_count=extraction_data.get("page_count"),
                word_count=extraction_data.get("word_count"),
                char_count=extraction_data.get("char_count"),
                extractor_used=extraction_data.get("extractor_used", "pypdf"),
                extraction_method=extraction_data.get("method", "text"),
                extraction_quality=extraction_data.get("quality"),
                extraction_grade=extraction_data.get("grade"),
                has_readable_text=extraction_data.get("has_readable_text", False),
                needs_ocr=extraction_data.get("needs_ocr", False),
            )

            # Save to database
            self.db.insert_content_extraction(extraction)

            # Log success
            duration_ms = int((time.time() - start_time) * 1000)
            self.db.log_event(
                geo_id=geo_id,
                pmid=pmid,
                pipeline="P4",
                event_type="success",
                message=f"Extracted {extraction_data.get('word_count', 0)} words (grade: {extraction_data.get('grade', 'N/A')})",
                duration_ms=duration_ms,
            )

            logger.info(
                f"Saved content extraction: {geo_id}/{pmid} "
                f"({extraction_data.get('word_count', 0)} words)"
            )

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            self.db.log_event(
                geo_id=geo_id,
                pmid=pmid,
                pipeline="P4",
                event_type="error",
                message=str(e),
                duration_ms=duration_ms,
                error_type=type(e).__name__,
            )
            logger.error(f"Error saving content extraction: {e}")
            raise

    def save_enriched_content(
        self,
        geo_id: str,
        pmid: str,
        enriched_data: Dict,
    ) -> None:
        """
        Save enriched content (sections, tables, references, etc.).

        Args:
            geo_id: GEO dataset ID
            pmid: PubMed ID
            enriched_data: Enriched data from P4
                Expected keys: sections, tables, references, chatgpt_prompt, etc.
        """
        start_time = time.time()

        try:
            # Create enriched content record
            enriched = EnrichedContent(
                geo_id=geo_id,
                pmid=pmid,
                sections_json=json.dumps(enriched_data.get("sections", [])),
                tables_json=json.dumps(enriched_data.get("tables", [])),
                references_json=json.dumps(enriched_data.get("references", [])),
                figures_json=json.dumps(enriched_data.get("figures", [])),
                chatgpt_prompt=enriched_data.get("chatgpt_prompt"),
                chatgpt_metadata=json.dumps(enriched_data.get("chatgpt_metadata", {})),
                grobid_xml=enriched_data.get("grobid_xml"),
                grobid_tei_json=json.dumps(enriched_data.get("grobid_tei", {}))
                if enriched_data.get("grobid_tei")
                else None,
                enrichers_applied=json.dumps(enriched_data.get("enrichers_applied", [])),
                enrichment_quality=enriched_data.get("enrichment_quality"),
            )

            # Save to database
            self.db.insert_enriched_content(enriched)

            # Also save as JSON backup
            self.storage.save_enriched(geo_id, pmid, enriched_data)

            # Log success
            duration_ms = int((time.time() - start_time) * 1000)
            enrichers_count = len(enriched_data.get("enrichers_applied", []))
            self.db.log_event(
                geo_id=geo_id,
                pmid=pmid,
                pipeline="P4",
                event_type="success",
                message=f"Applied {enrichers_count} enrichers",
                duration_ms=duration_ms,
            )

            logger.info(f"Saved enriched content: {geo_id}/{pmid} ({enrichers_count} enrichers)")

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            self.db.log_event(
                geo_id=geo_id,
                pmid=pmid,
                pipeline="P4",
                event_type="error",
                message=str(e),
                duration_ms=duration_ms,
                error_type=type(e).__name__,
            )
            logger.error(f"Error saving enriched content: {e}")
            raise

    # =========================================================================
    # HIGH-LEVEL OPERATIONS
    # =========================================================================

    def get_publication_status(self, geo_id: str, pmid: str) -> Dict:
        """
        Get complete processing status for a publication.

        Returns:
            Dictionary with status for each pipeline stage
        """
        return {
            "geo_id": geo_id,
            "pmid": pmid,
            "citation": self.db.get_universal_identifier(geo_id, pmid) is not None,
            "urls": self.db.get_url_discovery(geo_id, pmid) is not None,
            "pdf": self.db.get_pdf_acquisition(geo_id, pmid) is not None,
            "extraction": self.db.get_content_extraction(geo_id, pmid) is not None,
            "enriched": self.db.get_enriched_content(geo_id, pmid) is not None,
        }

    def get_geo_progress(self, geo_id: str) -> Dict:
        """
        Get processing progress for a GEO dataset.

        Returns:
            Dictionary with counts for each stage
        """
        pubs = self.db.get_publications_by_geo(geo_id)
        total = len(pubs)

        if total == 0:
            return {
                "geo_id": geo_id,
                "total_publications": 0,
                "citations": 0,
                "urls": 0,
                "pdfs": 0,
                "extracted": 0,
                "enriched": 0,
            }

        # Count completions for each stage
        urls_count = sum(1 for p in pubs if self.db.get_url_discovery(geo_id, p.pmid))
        pdfs_count = sum(1 for p in pubs if self.db.get_pdf_acquisition(geo_id, p.pmid))
        extracted_count = sum(1 for p in pubs if self.db.get_content_extraction(geo_id, p.pmid))
        enriched_count = sum(1 for p in pubs if self.db.get_enriched_content(geo_id, p.pmid))

        return {
            "geo_id": geo_id,
            "total_publications": total,
            "citations": total,  # All have citations if in database
            "urls": urls_count,
            "pdfs": pdfs_count,
            "extracted": extracted_count,
            "enriched": enriched_count,
            "completion_rate": (enriched_count / total * 100) if total > 0 else 0.0,
        }
