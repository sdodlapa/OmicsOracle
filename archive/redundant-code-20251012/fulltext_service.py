"""
Full-Text Enrichment Service

Background service for downloading, parsing, and normalizing full-text papers
from PubMed Central and other sources.

Week 2 Day 5 - Full-Text AI Analysis Integration
"""

import asyncio
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from omics_oracle_v2.api.models.responses import DatasetResponse, FullTextContent
from omics_oracle_v2.lib.fulltext.manager import FullTextManager, FullTextManagerConfig
from omics_oracle_v2.lib.fulltext.normalizer import ContentNormalizer
from omics_oracle_v2.lib.fulltext.parsed_cache import ParsedCache
from omics_oracle_v2.lib.publications.models import Publication, PublicationSource

logger = logging.getLogger(__name__)


class FullTextService:
    """
    Service for managing full-text downloads and parsing.

    Provides async methods to enrich datasets with full-text content from
    linked publications (PubMed/PMC).
    """

    def __init__(self):
        """Initialize the full-text service."""
        # Use FullTextManager for downloads with COMPREHENSIVE fallback chain
        # Priority order: Institutional → Cache → PMC → Unpaywall → CORE → OpenAlex → bioRxiv → Sci-Hub → LibGen
        fulltext_config = FullTextManagerConfig(
            enable_institutional=True,  # Priority 0: Georgia Tech & Old Dominion access (HIGHEST quality)
            enable_pmc=True,  # Priority 1: PubMed Central (6M free articles)
            enable_unpaywall=True,  # Priority 2: Unpaywall OA aggregator (25-30% coverage)
            enable_core=True,  # Priority 3: CORE academic repository (10-15% additional)
            enable_openalex=True,  # Priority 4: OpenAlex OA metadata
            enable_biorxiv=True,  # Priority 5: bioRxiv/medRxiv preprints
            enable_arxiv=True,  # Priority 6: arXiv preprints
            enable_crossref=True,  # Priority 7: Crossref publisher links
            enable_scihub=True,  # Priority 8: Sci-Hub (gray area - user requested)
            enable_libgen=True,  # Priority 9: LibGen (gray area - last fallback)
            # Configuration
            unpaywall_email=os.getenv("UNPAYWALL_EMAIL", "research@omicsoracle.ai"),
            core_api_key=os.getenv("CORE_API_KEY"),
            scihub_use_proxy=False,  # Set to True if using Tor/proxy
            libgen_use_proxy=False,
            timeout_per_source=30,  # 30s per source before moving to next
        )
        self.fulltext_manager = FullTextManager(fulltext_config)
        self.normalizer = ContentNormalizer()
        self.cache = ParsedCache()
        logger.info("FullTextService initialized with ALL download sources (Institutional + OA + Sci-Hub)")

    async def enrich_dataset_with_fulltext(
        self, dataset: DatasetResponse, max_papers: int = 3
    ) -> DatasetResponse:
        """
        Download and parse PDFs for a dataset's linked publications.

        This method:
        1. Takes PMIDs from dataset.pubmed_ids
        2. Downloads PDFs using FullTextManager
        3. Parses and normalizes content
        4. Caches for future use
        5. Returns dataset with fulltext field populated

        Args:
            dataset: Dataset with pubmed_ids
            max_papers: Maximum number of papers to download (default: 3)

        Returns:
            Dataset with fulltext field populated
        """
        if not dataset.pubmed_ids:
            dataset.fulltext_status = "no_pmids"
            logger.warning(f"Dataset {dataset.geo_id} has no PubMed IDs")
            return dataset

        dataset.fulltext_status = "downloading"
        fulltext_list = []

        try:
            # Limit to max_papers to avoid token limits
            pmids_to_fetch = dataset.pubmed_ids[:max_papers]
            logger.info(
                f"Enriching {dataset.geo_id} with full-text from "
                f"{len(pmids_to_fetch)} PMIDs: {pmids_to_fetch}"
            )

            # Initialize manager if needed
            if not self.fulltext_manager.initialized:
                await self.fulltext_manager.initialize()

            # CRITICAL FIX: Fetch FULL publication metadata (DOI, PMC ID, etc.) from PubMed
            # instead of creating minimal Publication objects
            logger.info(f"Fetching full metadata for {len(pmids_to_fetch)} PMIDs from PubMed...")
            from omics_oracle_v2.lib.publications.clients.pubmed import PubMedClient, PubMedConfig

            pubmed_client = PubMedClient(PubMedConfig(email="omicsoracle@research.ai"))
            publications = []

            for pmid in pmids_to_fetch:
                try:
                    # Fetch complete publication metadata (includes DOI, PMC ID, journal, authors, etc.)
                    pub = pubmed_client.fetch_by_id(pmid)

                    if pub:
                        publications.append(pub)
                        logger.info(
                            f"✅ Fetched metadata for PMID {pmid}: "
                            f"DOI={pub.doi}, PMC={pub.pmcid}, Journal={pub.journal}"
                        )
                    else:
                        logger.warning(f"⚠️ Could not fetch metadata for PMID {pmid}")
                        # Create minimal fallback
                        publications.append(
                            Publication(
                                pmid=pmid,
                                title=f"Publication {pmid}",
                                source=PublicationSource.PUBMED,
                            )
                        )
                except Exception as e:
                    logger.error(f"Error fetching metadata for PMID {pmid}: {e}")
                    # Create minimal fallback
                    publications.append(
                        Publication(
                            pmid=pmid,
                            title=f"Publication {pmid}",
                            source=PublicationSource.PUBMED,
                        )
                    )

            logger.info(
                f"Retrieved {len(publications)} publication objects with full metadata "
                f"(DOIs: {sum(1 for p in publications if p.doi)}, "
                f"PMC IDs: {sum(1 for p in publications if p.pmcid)})"
            )

            # ============================================================================
            # USE BATCH PROCESSING (same as PublicationSearchPipeline - WORKING CODE!)
            # This runs downloads CONCURRENTLY with semaphore control (much faster!)
            # ============================================================================
            logger.info(f"🚀 Batch downloading full-text for {len(publications)} publications (concurrent)...")
            fulltext_results = await self.fulltext_manager.get_fulltext_batch(publications)

            # Log statistics (same as pipeline)
            success_count = sum(1 for r in fulltext_results if r.success)
            stats = self.fulltext_manager.get_statistics()
            logger.info(
                f"Full-text batch download: {success_count}/{len(publications)} "
                f"publications ({stats.get('success_rate', 'N/A')} success rate)"
            )
            logger.info(f"Sources used: {stats.get('by_source', {})}")

            # Process results
            for pub, result in zip(publications, fulltext_results):
                try:
                    if result.success and result.pdf_path:
                        pdf_path = Path(result.pdf_path)

                        if pdf_path.exists():
                            # Get parsed content (uses cache if available)
                            parsed = await self.fulltext_manager.get_parsed_content(pub)

                            if parsed and parsed.get("title"):
                                # Extract sections
                                fulltext_list.append(
                                    FullTextContent(
                                        pmid=pub.pmid,
                                        title=parsed.get("title", ""),
                                        abstract=parsed.get("abstract", ""),
                                        methods=parsed.get("methods", ""),
                                        results=parsed.get("results", ""),
                                        discussion=parsed.get("discussion", ""),
                                        introduction=parsed.get("introduction", ""),
                                        conclusion=parsed.get("conclusion", ""),
                                        references=parsed.get("references", []),
                                        figures_captions=parsed.get("figures", []),
                                        tables_captions=parsed.get("tables", []),
                                        format=parsed.get("format", "unknown"),
                                        parse_date=datetime.now().isoformat(),
                                    )
                                )
                                logger.info(
                                    f"✅ Parsed {pub.pmid} successfully from {result.source.value} "
                                    f"(format: {parsed.get('format', 'unknown')})"
                                )
                            else:
                                logger.warning(f"⚠️ Failed to parse {pub.pmid} - empty or invalid content")
                        else:
                            logger.warning(f"⚠️ PDF path doesn't exist: {pdf_path}")
                    elif result.success and result.url:
                        # We have a URL but no downloaded PDF - create minimal content
                        logger.info(f"📄 Got URL for {pub.pmid} from {result.source.value} (no PDF)")
                        fulltext_list.append(
                            FullTextContent(
                                pmid=pub.pmid,
                                title=pub.title or "Unknown",
                                abstract="",
                                methods="",
                                results="",
                                discussion="",
                                introduction="",
                                conclusion="",
                                references=[],
                                figures_captions=[],
                                tables_captions=[],
                                format="url_only",
                                parse_date=datetime.now().isoformat(),
                            )
                        )
                    else:
                        logger.warning(f"❌ Failed to download PDF for PMID {pub.pmid}: {result.error}")

                except Exception as e:
                    logger.error(f"❌ Failed to process PMID {pub.pmid}: {e}", exc_info=True)
                    continue

            # Update dataset
            dataset.fulltext = fulltext_list
            dataset.fulltext_count = len(fulltext_list)

            # Set status based on results
            if len(fulltext_list) == 0:
                dataset.fulltext_status = "failed"
                logger.warning(f"No full-text content retrieved for {dataset.geo_id}")
            elif len(fulltext_list) < len(pmids_to_fetch):
                dataset.fulltext_status = "partial"
                logger.info(
                    f"Partial success for {dataset.geo_id}: "
                    f"{len(fulltext_list)}/{len(pmids_to_fetch)} papers"
                )
            else:
                dataset.fulltext_status = "available"
                logger.info(f"Full success for {dataset.geo_id}: " f"{len(fulltext_list)} papers retrieved")

            logger.info(
                f"Enrichment complete for {dataset.geo_id}: "
                f"{len(fulltext_list)} full-text papers out of {len(pmids_to_fetch)} PMIDs"
            )

        except Exception as e:
            logger.error(f"Failed to enrich {dataset.geo_id}: {e}", exc_info=True)
            dataset.fulltext_status = "failed"
            dataset.fulltext = []
            dataset.fulltext_count = 0

        return dataset

    async def enrich_datasets_batch(
        self, datasets: List[DatasetResponse], max_papers_per_dataset: int = 3
    ) -> List[DatasetResponse]:
        """
        Enrich multiple datasets with full-text in parallel.

        This method processes multiple datasets concurrently to speed up
        the enrichment process. Each dataset is enriched independently.

        Args:
            datasets: List of datasets to enrich
            max_papers_per_dataset: Max papers per dataset (default: 3)

        Returns:
            List of enriched datasets (same order as input)
        """
        logger.info(
            f"Starting batch enrichment of {len(datasets)} datasets "
            f"(max {max_papers_per_dataset} papers each)"
        )

        # Create enrichment tasks for all datasets
        tasks = [self.enrich_dataset_with_fulltext(ds, max_papers_per_dataset) for ds in datasets]

        # Run all tasks concurrently
        enriched_datasets = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle any exceptions from tasks
        results = []
        for i, result in enumerate(enriched_datasets):
            if isinstance(result, Exception):
                logger.error(f"Failed to enrich dataset {i}: {result}", exc_info=result)
                # Return original dataset with failed status
                datasets[i].fulltext_status = "failed"
                results.append(datasets[i])
            else:
                results.append(result)

        success_count = sum(1 for ds in results if ds.fulltext_status == "available")
        partial_count = sum(1 for ds in results if ds.fulltext_status == "partial")
        failed_count = sum(1 for ds in results if ds.fulltext_status == "failed")

        logger.info(
            f"Batch enrichment complete: {success_count} full, "
            f"{partial_count} partial, {failed_count} failed"
        )

        return results

    def get_fulltext_summary(self, dataset: DatasetResponse) -> str:
        """
        Get a brief summary of full-text availability for a dataset.

        Args:
            dataset: Dataset to summarize

        Returns:
            Human-readable status string
        """
        if dataset.fulltext_status == "not_downloaded":
            return "Full-text not downloaded"
        elif dataset.fulltext_status == "downloading":
            return "Downloading full-text..."
        elif dataset.fulltext_status == "no_pmids":
            return "No PubMed IDs available"
        elif dataset.fulltext_status == "failed":
            return "Full-text download failed"
        elif dataset.fulltext_status == "partial":
            return f"{dataset.fulltext_count} of {len(dataset.pubmed_ids)} papers available"
        elif dataset.fulltext_status == "available":
            return f"{dataset.fulltext_count} full-text papers available"
        else:
            return f"Status: {dataset.fulltext_status}"
