"""
GEO Citation Collection Pipeline

End-to-end pipeline: Query → GEO → Citations → PDFs

NO LLM ANALYSIS - Pure data collection phase.
Phase 7 will add LLM analysis of collected papers.
"""

import json
import logging
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from omics_oracle_v2.lib.geo.client import GEOClient
from omics_oracle_v2.lib.geo.models import GEOSeriesMetadata
from omics_oracle_v2.lib.geo.query_builder import GEOQueryBuilder
from omics_oracle_v2.lib.nlp.synonym_expansion import SynonymExpander
from omics_oracle_v2.lib.citations.discovery.geo_discovery import (
    GEOCitationDiscovery,
)
from omics_oracle_v2.lib.fulltext.manager import FullTextManager, FullTextManagerConfig
from omics_oracle_v2.lib.publications.models import Publication
from omics_oracle_v2.lib.storage.pdf.download_manager import PDFDownloadManager

logger = logging.getLogger(__name__)


@dataclass
class GEOCitationConfig:
    """Configuration for GEO citation pipeline"""

    # GEO search
    geo_max_results: int = 10
    geo_min_samples: int = 10
    enable_synonym_expansion: bool = True

    # Citation discovery
    citation_max_results: int = 100
    use_citation_strategy: bool = True  # Papers citing original publication
    use_mention_strategy: bool = True  # Papers mentioning GEO ID

    # Full-text retrieval
    enable_institutional: bool = True
    enable_unpaywall: bool = True
    enable_core: bool = True
    enable_scihub: bool = False  # Optional: disable for legal-only
    enable_libgen: bool = False

    # PDF download
    download_pdfs: bool = True
    max_concurrent_downloads: int = 5
    pdf_validation: bool = True
    max_retries: int = 3

    # Storage
    output_dir: Path = Path("data/geo_citation_collections")
    organize_by_geo_id: bool = True


@dataclass
class CollectionResult:
    """Results from GEO citation collection pipeline"""

    query: str
    timestamp: str
    datasets_found: List[GEOSeriesMetadata] = field(default_factory=list)
    total_citing_papers: int = 0
    citing_papers: List[Publication] = field(default_factory=list)
    fulltext_coverage: float = 0.0
    fulltext_by_source: Dict[str, int] = field(default_factory=dict)
    pdfs_downloaded: int = 0
    download_report: Optional[Dict] = None
    collection_dir: Optional[Path] = None
    duration_seconds: float = 0.0

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "query": self.query,
            "timestamp": self.timestamp,
            "datasets_found": [
                {"geo_id": ds.geo_id, "title": ds.title, "pmid": ds.pmid} for ds in self.datasets_found
            ],
            "total_citing_papers": self.total_citing_papers,
            "fulltext_coverage": self.fulltext_coverage,
            "fulltext_by_source": self.fulltext_by_source,
            "pdfs_downloaded": self.pdfs_downloaded,
            "download_report": self.download_report,
            "collection_dir": str(self.collection_dir) if self.collection_dir else None,
            "duration_seconds": self.duration_seconds,
        }


class GEOCitationPipeline:
    """
    End-to-end pipeline for GEO citation collection.

    Flow:
    1. [Optional] Expand query with synonyms
    2. Search GEO for relevant datasets
    3. Discover papers citing those datasets
    4. Collect full-text URLs (optimized waterfall)
    5. Download PDFs
    6. Generate comprehensive report

    NO LLM analysis - pure collection.
    """

    def __init__(self, config: Optional[GEOCitationConfig] = None):
        self.config = config or GEOCitationConfig()

        # Initialize components
        self.geo_client = GEOClient()
        self.citation_discovery = GEOCitationDiscovery()

        # Full-text manager with optimized config (use .env for API keys)
        fulltext_config = FullTextManagerConfig(
            enable_institutional=self.config.enable_institutional,
            enable_unpaywall=self.config.enable_unpaywall,
            enable_core=self.config.enable_core,
            enable_scihub=self.config.enable_scihub,
            enable_libgen=self.config.enable_libgen,
            core_api_key=os.getenv("CORE_API_KEY"),
            unpaywall_email=os.getenv("NCBI_EMAIL", "sdodl001@odu.edu"),
        )
        self.fulltext_manager = FullTextManager(fulltext_config)

        # PDF downloader
        if self.config.download_pdfs:
            self.pdf_manager = PDFDownloadManager(
                max_concurrent=self.config.max_concurrent_downloads,
                max_retries=self.config.max_retries,
                validate_pdf=self.config.pdf_validation,
            )

        # Synonym expander (optional)
        if self.config.enable_synonym_expansion:
            self.synonym_expander = SynonymExpander()

    async def collect(
        self, query: str, max_datasets: Optional[int] = None, max_citing_papers: Optional[int] = None
    ) -> CollectionResult:
        """
        Run the complete collection pipeline.

        Args:
            query: Research query (e.g., "breast cancer RNA-seq")
            max_datasets: Max GEO datasets to process
            max_citing_papers: Max citing papers per dataset

        Returns:
            CollectionResult with all collected data
        """
        start_time = datetime.now()
        logger.info(f"=" * 80)
        logger.info(f"GEO CITATION COLLECTION PIPELINE")
        logger.info(f"=" * 80)
        logger.info(f"Query: {query}")
        logger.info(f"")

        # Step 1: Optimize query for GEO search
        logger.info("Step 1: Optimizing query for comprehensive GEO search...")
        query_builder = GEOQueryBuilder()
        optimized_query = query_builder.build_query(query, mode="balanced")
        logger.info(f"  Original: {query}")
        logger.info(f"  Optimized: {optimized_query}")

        # Step 2: Search GEO
        logger.info("Step 2: Searching GEO datasets...")
        max_geo = max_datasets or self.config.geo_max_results
        search_result = await self.geo_client.search(
            optimized_query, max_results=max_geo  # Use optimized query
        )
        logger.info(f"  Found {search_result.total_found} GEO series (fetching {len(search_result.geo_ids)})")

        if not search_result.geo_ids:
            logger.warning("No GEO datasets found. Exiting.")
            return CollectionResult(
                query=query,
                timestamp=datetime.now().isoformat(),
                duration_seconds=(datetime.now() - start_time).total_seconds(),
            )

        # Fetch metadata for found datasets
        logger.info("Step 2b: Fetching GEO metadata...")
        datasets_dict = await self.geo_client.batch_get_metadata(search_result.geo_ids, max_concurrent=5)
        # Filter out any None results
        datasets = [d for d in datasets_dict.values() if d is not None]
        logger.info(f"  Retrieved metadata for {len(datasets)} datasets")

        # Step 3: Discover citing papers
        logger.info("Step 3: Discovering citing papers...")
        all_citing_papers: List[Publication] = []
        citation_results = []

        max_citing = max_citing_papers or self.config.citation_max_results

        for dataset in datasets:
            logger.info(f"  Processing {dataset.geo_id}...")
            citation_result = await self.citation_discovery.find_citing_papers(
                dataset, max_results=max_citing
            )
            citation_results.append(citation_result)
            all_citing_papers.extend(citation_result.citing_papers)

        # Deduplicate papers
        unique_papers = self._deduplicate_papers(all_citing_papers)
        logger.info(f"  Total unique citing papers: {len(unique_papers)}")

        # Step 4: Collect full-text URLs
        logger.info("Step 4: Collecting full-text URLs (optimized waterfall)...")
        papers_with_fulltext = await self.fulltext_manager.get_fulltext_batch(unique_papers)

        # Calculate coverage
        fulltext_count = sum(1 for p in papers_with_fulltext if p.fulltext_url)
        fulltext_coverage = fulltext_count / len(papers_with_fulltext) if papers_with_fulltext else 0
        logger.info(
            f"  Full-text coverage: {fulltext_coverage:.1%} ({fulltext_count}/{len(papers_with_fulltext)})"
        )

        # Count by source
        source_counts = {}
        for paper in papers_with_fulltext:
            if hasattr(paper, "fulltext_source") and paper.fulltext_source:
                source_counts[paper.fulltext_source] = source_counts.get(paper.fulltext_source, 0) + 1

        # Step 5: Download PDFs
        download_report_dict = None
        pdfs_downloaded = 0
        collection_dir = None

        if self.config.download_pdfs:
            logger.info("Step 5: Downloading PDFs...")

            # Create output directory
            collection_dir = self._create_collection_dir(query)
            pdf_dir = collection_dir / "pdfs"

            # Download PDFs
            papers_to_download = [p for p in papers_with_fulltext if p.fulltext_url]
            if papers_to_download:
                download_report = await self.pdf_manager.download_batch(papers_to_download, pdf_dir)
                pdfs_downloaded = download_report.successful
                download_report_dict = asdict(download_report)
                logger.info(f"  Downloaded: {pdfs_downloaded} PDFs ({download_report.total_size_mb:.2f} MB)")
            else:
                logger.warning("  No PDFs to download (no full-text URLs)")

            # Save metadata
            await self._save_metadata(
                collection_dir, query, datasets, unique_papers, citation_results, download_report_dict
            )

        # Generate result
        duration = (datetime.now() - start_time).total_seconds()

        result = CollectionResult(
            query=query,
            timestamp=datetime.now().isoformat(),
            datasets_found=datasets,
            total_citing_papers=len(unique_papers),
            citing_papers=unique_papers,
            fulltext_coverage=fulltext_coverage,
            fulltext_by_source=source_counts,
            pdfs_downloaded=pdfs_downloaded,
            download_report=download_report_dict,
            collection_dir=collection_dir,
            duration_seconds=duration,
        )

        logger.info(f"")
        logger.info(f"=" * 80)
        logger.info(f"COLLECTION COMPLETE")
        logger.info(f"=" * 80)
        logger.info(f"Duration: {duration:.1f}s")
        logger.info(f"GEO datasets: {len(datasets)}")
        logger.info(f"Citing papers: {len(unique_papers)}")
        logger.info(f"Full-text coverage: {fulltext_coverage:.1%}")
        logger.info(f"PDFs downloaded: {pdfs_downloaded}")
        if collection_dir:
            logger.info(f"Collection saved to: {collection_dir}")
        logger.info(f"")

        return result

    def _deduplicate_papers(self, papers: List[Publication]) -> List[Publication]:
        """Deduplicate papers by PMID or DOI"""
        seen = set()
        unique = []

        for paper in papers:
            key = paper.pmid or paper.doi or paper.title
            if key and key not in seen:
                seen.add(key)
                unique.append(paper)

        return unique

    def _create_collection_dir(self, query: str) -> Path:
        """Create directory for this collection"""
        # Clean query for directory name
        clean_query = "".join(c if c.isalnum() or c in "_ " else "_" for c in query)
        clean_query = clean_query[:50].strip()  # Limit length

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dir_name = f"{clean_query}_{timestamp}"

        collection_dir = self.config.output_dir / dir_name
        collection_dir.mkdir(parents=True, exist_ok=True)

        return collection_dir

    async def _save_metadata(
        self,
        collection_dir: Path,
        query: str,
        datasets: List[GEOSeriesMetadata],
        citing_papers: List[Publication],
        citation_results: List,
        download_report: Optional[dict],
    ):
        """Save collection metadata as JSON files"""

        # Save GEO datasets
        geo_data = [
            {
                "geo_id": ds.geo_id,
                "title": ds.title,
                "summary": ds.summary,
                "pubmed_ids": ds.pubmed_ids,  # Fixed: use pubmed_ids (list) not pmid
                "sample_count": ds.sample_count,  # Fixed: sample_count not samples_count
            }
            for ds in datasets
        ]
        with open(collection_dir / "geo_datasets.json", "w") as f:
            json.dump(geo_data, f, indent=2)

        # Save citing papers
        papers_data = [
            {
                "pmid": p.pmid,
                "doi": p.doi,
                "title": p.title,
                "authors": p.authors,
                "journal": p.journal,
                "year": p.year,
                "fulltext_url": p.fulltext_url,
                "fulltext_source": getattr(p, "fulltext_source", None),
            }
            for p in citing_papers
        ]
        with open(collection_dir / "citing_papers.json", "w") as f:
            json.dump(papers_data, f, indent=2)

        # Save collection report
        report = {
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "datasets_found": len(datasets),
            "citing_papers_found": len(citing_papers),
            "download_report": download_report,
        }
        with open(collection_dir / "collection_report.json", "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"✓ Metadata saved to {collection_dir}")
