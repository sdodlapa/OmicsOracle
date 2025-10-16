"""Full-text enrichment service for OmicsOracle."""

import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from omics_oracle_v2.api.models import DatasetResponse
from omics_oracle_v2.lib.pipelines.citation_discovery import GEOCitationDiscovery
from omics_oracle_v2.lib.pipelines.citation_discovery.clients.config import PubMedConfig
from omics_oracle_v2.lib.pipelines.citation_discovery.clients.pubmed import PubMedClient
from omics_oracle_v2.lib.pipelines.pdf_download import PDFDownloadManager
from omics_oracle_v2.lib.search_engines.geo.models import GEOSeriesMetadata
from omics_oracle_v2.lib.pipelines.storage import get_registry
from omics_oracle_v2.lib.pipelines.text_enrichment import PDFExtractor, get_parsed_cache
from omics_oracle_v2.lib.pipelines.url_collection import FullTextManager, FullTextManagerConfig

logger = logging.getLogger(__name__)


class FulltextService:
    """Service for full-text enrichment of GEO datasets.
    
    Extracted from api/routes/agents.py to improve separation of concerns.
    This service encapsulates all business logic for the /enrich-fulltext endpoint.
    """

    async def enrich_datasets(
        self,
        datasets: List[DatasetResponse],
        max_papers: Optional[int] = None,
        include_citing_papers: bool = True,
        max_citing_papers: int = 5,
        download_original: bool = True,
        include_full_content: bool = True,
    ) -> List[DatasetResponse]:
        """
        Enrich datasets with full-text PDFs and extracted content.
        
        This is the main entry point that contains all the business logic
        from the original /enrich-fulltext endpoint.
        """
        start_time = time.time()

        try:
            # Initialize FullTextManager
            logger.info("Initializing FullTextManager with all sources...")
            fulltext_config = FullTextManagerConfig(
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
            fulltext_manager = FullTextManager(fulltext_config)

            pdf_downloader = PDFDownloadManager(
                max_concurrent=3, max_retries=2, timeout_seconds=30, validate_pdf=True
            )

            pubmed_client = PubMedClient(
                PubMedConfig(email=os.getenv("NCBI_EMAIL", "research@omicsoracle.ai"))
            )

            if not fulltext_manager.initialized:
                await fulltext_manager.initialize()

            enriched_datasets = []

            citation_discovery = None
            if include_citing_papers:
                logger.info("[CITATION] Initializing citation discovery...")
                citation_discovery = GEOCitationDiscovery()
            
            # NOTE: The full implementation would go here
            # For now, returning the datasets as-is to get the structure working
            # The complete logic will be copied from agents.py in the next iteration
            
            return datasets

        finally:
            try:
                if fulltext_manager:
                    await fulltext_manager.cleanup()
                    logger.debug("Cleaned up fulltext_manager resources")
            except Exception as cleanup_error:
                logger.warning(f"Error during cleanup: {cleanup_error}")
