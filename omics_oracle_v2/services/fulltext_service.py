"""
Full-Text Enrichment Service

Orchestrates PDF download and content extraction for GEO datasets.
Handles citation discovery, URL collection, PDF acquisition, and text parsing.

This service provides the business logic for the /enrich-fulltext endpoint,
extracted from api/routes/agents.py to improve separation of concerns.
"""

import logging
import time
from typing import Dict, List, Optional

from omics_oracle_v2.api.models.responses import DatasetResponse
from omics_oracle_v2.lib.pipelines import PipelineCoordinator
from omics_oracle_v2.lib.pipelines.citation_discovery.clients.config import PubMedConfig
from omics_oracle_v2.lib.pipelines.citation_discovery.clients.pubmed import PubMedClient
from omics_oracle_v2.lib.pipelines.citation_discovery.geo_discovery import (
    GEOCitationDiscovery,
)
from omics_oracle_v2.lib.pipelines.pdf_download import PDFDownloadManager
from omics_oracle_v2.lib.pipelines.url_collection import (
    FullTextManager,
    FullTextManagerConfig,
)

import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from omics_oracle_v2.api.models.responses import DatasetResponse
from omics_oracle_v2.lib.pipelines import PipelineCoordinator
from omics_oracle_v2.lib.pipelines.citation_discovery.clients.config import \
    PubMedConfig
from omics_oracle_v2.lib.pipelines.citation_discovery.clients.pubmed import \
    PubMedClient
from omics_oracle_v2.lib.pipelines.citation_discovery.geo_discovery import \
    GEOCitationDiscovery
from omics_oracle_v2.lib.pipelines.pdf_download import PDFDownloadManager
from omics_oracle_v2.lib.pipelines.storage import get_registry
from omics_oracle_v2.lib.pipelines.text_enrichment import (PDFExtractor,
                                                           get_parsed_cache)
from omics_oracle_v2.lib.pipelines.url_collection import (
    FullTextManager, FullTextManagerConfig)
from omics_oracle_v2.lib.search_engines.geo.models import GEOSeriesMetadata

logger = logging.getLogger(__name__)


class FullTextEnrichmentService:
    """
    Service for enriching datasets with full-text PDFs and content extraction.

    Coordinates:
    - P1: Citation discovery (original + citing papers)
    - P2: URL collection from multiple sources
    - P3: PDF download with waterfall fallback
    - P4: Content extraction and parsing

    Results are stored in UnifiedDatabase via PipelineCoordinator.
    """

    def __init__(self, coordinator: PipelineCoordinator = None):
        """
        Initialize service.

        Args:
            coordinator: Optional PipelineCoordinator (creates default if None)
        """
        self.coordinator = coordinator or PipelineCoordinator()
        self.logger = logger

    async def enrich_datasets(
        self,
        datasets: List[DatasetResponse],
        max_papers: Optional[int] = None,
        include_citing_papers: bool = False,
        max_citing_papers: int = 5,
        download_original: bool = True,
        include_full_content: bool = True,
    ) -> List[DatasetResponse]:
        """
        Enrich datasets with full-text content.

        Args:
            datasets: Datasets to enrich
            max_papers: Max original papers per dataset
            include_citing_papers: Whether to include citing papers
            max_citing_papers: Max citing papers per dataset
            download_original: Whether to download original papers
            include_full_content: Whether to include full parsed content

        Returns:
            Enriched datasets with fulltext information
        """
        start_time = time.time()

        # Initialize pipeline components
        fulltext_manager = await self._init_fulltext_manager()
        pdf_downloader = self._init_pdf_downloader()
        pubmed_client = self._init_pubmed_client()
        citation_discovery = GEOCitationDiscovery() if include_citing_papers else None

        enriched_datasets = []

        try:
            for dataset in datasets:
                self.logger.info(f"\n{'='*80}")
                self.logger.info(
                    f"Processing {dataset.geo_id}: {dataset.title[:60]}..."
                )
                self.logger.info(f"{'='*80}\n")

                if not dataset.pubmed_ids:
                    self.logger.warning(f"Dataset {dataset.geo_id} has no PubMed IDs")
                    enriched_datasets.append(dataset)
                    continue

                # Process this dataset
                enriched = await self._process_single_dataset(
                    dataset=dataset,
                    fulltext_manager=fulltext_manager,
                    pdf_downloader=pdf_downloader,
                    pubmed_client=pubmed_client,
                    citation_discovery=citation_discovery,
                    max_papers=max_papers,
                    max_citing_papers=max_citing_papers,
                    download_original=download_original,
                    include_full_content=include_full_content,
                )

                enriched_datasets.append(enriched)

            execution_time_ms = (time.time() - start_time) * 1000
            self.logger.info(
                f"Enriched {len(enriched_datasets)} datasets in {execution_time_ms:.2f}ms"
            )

            return enriched_datasets

        finally:
            # Cleanup resources
            if fulltext_manager:
                await fulltext_manager.cleanup()

    async def _process_single_dataset(
        self,
        dataset: DatasetResponse,
        fulltext_manager: FullTextManager,
        pdf_downloader: PDFDownloadManager,
        pubmed_client: PubMedClient,
        citation_discovery: Optional[GEOCitationDiscovery],
        max_papers: Optional[int],
        max_citing_papers: int,
        download_original: bool,
        include_full_content: bool,
    ) -> DatasetResponse:
        """
        Process a single dataset through the enrichment pipeline.

        This method implements the core business logic extracted from
        the /enrich-fulltext endpoint in api/routes/agents.py.
        """
        # Step 1: Gather papers (original + citing)
        papers_to_download = await self._gather_papers(
            dataset=dataset,
            pubmed_client=pubmed_client,
            citation_discovery=citation_discovery,
            max_papers=max_papers,
            max_citing_papers=max_citing_papers,
            download_original=download_original,
        )

        total_papers = len(papers_to_download["original"]) + len(
            papers_to_download["citing"]
        )

        if total_papers == 0:
            self.logger.warning(f"[SKIP] No papers to download for {dataset.geo_id}")
            return dataset

        self.logger.info(
            f"[DOWNLOAD] Total papers: {total_papers} "
            f"(original={len(papers_to_download['original'])}, "
            f"citing={len(papers_to_download['citing'])})"
        )

        # Step 2: Download PDFs with waterfall fallback
        download_results = await self._download_pdfs(
            geo_id=dataset.geo_id,
            papers_to_download=papers_to_download,
            fulltext_manager=fulltext_manager,
            pdf_downloader=pdf_downloader,
        )

        # Step 3: Parse PDFs and build fulltext data
        dataset = await self._parse_and_attach_content(
            dataset=dataset,
            papers_to_download=papers_to_download,
            download_results=download_results,
            total_papers=total_papers,
            include_full_content=include_full_content,
        )

        # Step 4: Save comprehensive metadata
        await self._save_metadata(
            dataset=dataset,
            papers_to_download=papers_to_download,
            download_results=download_results,
            total_papers=total_papers,
        )

        # Step 5: Update registry for frontend access
        await self._update_registry(
            dataset=dataset,
            papers_to_download=papers_to_download,
        )

        # Step 6: Update dataset metrics
        self._update_dataset_metrics(
            dataset=dataset,
            papers_to_download=papers_to_download,
            download_results=download_results,
        )

        return dataset

    async def _gather_papers(
        self,
        dataset: DatasetResponse,
        pubmed_client: PubMedClient,
        citation_discovery: Optional[GEOCitationDiscovery],
        max_papers: Optional[int],
        max_citing_papers: int,
        download_original: bool,
    ) -> Dict[str, List]:
        """
        Gather original and citing papers for dataset.

        Returns:
            Dict with 'original' and 'citing' paper lists
        """
        # Implementation continues in next part...
        papers = {"original": [], "citing": []}

        # TODO: Complete implementation
        return papers

    # Additional helper methods will be added...

    async def _init_fulltext_manager(self) -> FullTextManager:
        """Initialize FullTextManager with all sources."""
        import os

        config = FullTextManagerConfig(
            enable_institutional=True,
            enable_pmc=True,
            enable_unpaywall=True,
            enable_openalex=True,
            enable_core=True,
            enable_biorxiv=True,
            enable_arxiv=True,
            enable_crossref=True,
            enable_scihub=True,
            enable_libgen=True,
            download_pdfs=False,
            unpaywall_email=os.getenv("UNPAYWALL_EMAIL", "research@omicsoracle.ai"),
            core_api_key=os.getenv("CORE_API_KEY"),
        )

        manager = FullTextManager(config)
        if not manager.initialized:
            await manager.initialize()

        return manager

    def _init_pdf_downloader(self) -> PDFDownloadManager:
        """Initialize PDFDownloadManager."""
        return PDFDownloadManager(
            max_concurrent=3, max_retries=2, timeout_seconds=30, validate_pdf=True
        )

    def _init_pubmed_client(self) -> PubMedClient:
        """Initialize PubMed client."""
        import os

        return PubMedClient(
            PubMedConfig(email=os.getenv("NCBI_EMAIL", "research@omicsoracle.ai"))
        )
