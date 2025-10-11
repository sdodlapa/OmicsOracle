"""
GEO Citation Tracking - Find Recent Papers Citing GEO Datasets

This example shows how to:
1. Fetch GEO dataset metadata
2. Find papers citing the dataset
3. Filter for recent papers (2020-2025)
4. Rank by relevance
5. Download PDFs

Usage:
    python examples/geo_citation_tracking.py GSE103322
    python examples/geo_citation_tracking.py GSE103322 --max-papers 10 --download-pdfs
"""

import argparse
import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from omics_oracle_v2.lib.citations.discovery.geo_discovery import GEOCitationDiscovery
from omics_oracle_v2.lib.citations.filters import filter_by_year_range, rank_by_citations_and_recency
from omics_oracle_v2.lib.geo.fetcher import GEOFetcher
from omics_oracle_v2.lib.publications.models import Publication

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def find_recent_citing_papers(
    geo_id: str, min_year: int = 2020, max_year: int = 2025, max_papers: int = 20
) -> List[Publication]:
    """
    Find recent papers citing a GEO dataset.

    Args:
        geo_id: GEO accession (e.g., GSE103322)
        min_year: Minimum publication year
        max_year: Maximum publication year
        max_papers: Maximum papers to return

    Returns:
        List of recent citing publications, ranked by relevance
    """

    print(f"\n{'='*80}")
    print(f"GEO CITATION TRACKING: {geo_id}")
    print(f"Year range: {min_year}-{max_year}")
    print(f"Max papers: {max_papers}")
    print(f"{'='*80}\n")

    # Step 1: Fetch GEO metadata
    logger.info(f"Step 1: Fetching GEO metadata for {geo_id}...")
    geo_fetcher = GEOFetcher()
    metadata = await geo_fetcher.fetch_geo_series(geo_id)

    print(f"✓ Dataset: {metadata.title}")
    print(f"  Accession: {metadata.geo_id}")
    print(f"  Original papers: {len(metadata.pubmed_ids)} PMIDs")
    if metadata.submission_date:
        print(f"  Submitted: {metadata.submission_date.strftime('%Y-%m-%d')}")
    if metadata.pubmed_ids:
        print(f"  Primary PMID: {metadata.pubmed_ids[0]}")

    # Step 2: Find all citing papers
    logger.info("Step 2: Finding papers that cite this dataset...")
    discovery = GEOCitationDiscovery()
    result = await discovery.find_citing_papers(metadata, max_results=200)

    print(f"\n✓ Found {len(result.citing_papers)} total citing papers")
    print(f"  Strategy A (citing original paper): {len(result.strategy_breakdown['strategy_a'])} papers")
    print(f"  Strategy B (mentioning GEO ID): {len(result.strategy_breakdown['strategy_b'])} papers")

    if not result.citing_papers:
        print("\n⚠ No citing papers found. This dataset may be very new or not widely cited yet.")
        return []

    # Step 3: Filter for recent papers
    logger.info(f"Step 3: Filtering to {min_year}-{max_year}...")
    recent_papers = filter_by_year_range(result.citing_papers, min_year=min_year, max_year=max_year)

    print(f"\n✓ {len(recent_papers)} papers from {min_year}-{max_year}")

    if not recent_papers:
        print(f"\n⚠ No papers found in year range {min_year}-{max_year}")
        print("Try expanding the year range (e.g., --min-year 2015)")
        return []

    # Step 4: Rank by citations + recency
    logger.info("Step 4: Ranking by relevance (citations + recency)...")
    ranked_papers = rank_by_citations_and_recency(recent_papers, citation_weight=0.7, recency_weight=0.3)[
        :max_papers
    ]

    print(f"\n✓ Selected top {len(ranked_papers)} papers")

    # Step 5: Display results
    print(f"\n{'='*80}")
    print(f"TOP {len(ranked_papers)} RECENT PAPERS CITING {geo_id}")
    print(f"{'='*80}\n")

    for i, paper in enumerate(ranked_papers, 1):
        print(f"{i}. {paper.title}")

        # Authors
        if paper.authors:
            author_str = ", ".join(paper.authors[:3])
            if len(paper.authors) > 3:
                author_str += f" et al. ({len(paper.authors)} authors)"
            print(f"   Authors: {author_str}")

        # Year and citations
        year_str = paper.publication_date.year if paper.publication_date else "Unknown"
        cite_str = f"{paper.citations} citations" if paper.citations else "No citation data"
        print(f"   Year: {year_str} | {cite_str}")

        # Identifiers
        if paper.doi:
            print(f"   DOI: {paper.doi}")
        elif paper.pmid:
            print(f"   PMID: {paper.pmid}")

        # Full-text access
        if paper.metadata and paper.metadata.get("fulltext_url"):
            print(f"   ✓ Full-text available")

        print()

    return ranked_papers


async def download_pdfs(
    papers: List[Publication],
    geo_id: str,
    original_paper_pmid: Optional[str] = None,
    output_dir: Optional[str] = None,
):
    """
    Download PDFs for papers, organized by GEO dataset.

    Args:
        papers: Publications to download (citing papers)
        geo_id: GEO dataset ID (e.g., GSE103322)
        original_paper_pmid: PMID of original dataset paper (if available)
        output_dir: Override output directory (optional)
    """
    if not papers:
        logger.warning("No papers to download")
        return []

    try:
        from omics_oracle_v2.lib.storage.pdf.download_manager import PDFDownloadManager

        # Create GEO-specific directory structure
        if output_dir is None:
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = f"data/geo_citation_collections/{geo_id}_{timestamp}"

        # Create output directory with subdirectories
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Separate directories for original vs citing papers
        citing_dir = output_path / "citing_papers"
        citing_dir.mkdir(exist_ok=True)

        logger.info(f"Step 5: Downloading PDFs to {output_dir}...")
        print(f"\n{'='*80}")
        print(f"DOWNLOADING PDFs FOR {geo_id}")
        print(f"{'='*80}\n")
        print(f"Collection directory: {output_path}")
        print(f"Citing papers: {len(papers)} PDFs\n")

        # Initialize downloader
        downloader = PDFDownloadManager(
            max_concurrent=5, max_retries=3, timeout_seconds=30, validate_pdf=True
        )

        # Download citing papers
        download_report = await downloader.download_batch(publications=papers, output_dir=citing_dir)

        # Display results
        successful = download_report.successful if hasattr(download_report, "successful") else []
        failed = download_report.failed if hasattr(download_report, "failed") else []

        print(f"✓ Downloaded {len(successful)}/{len(papers)} citing papers")

        if successful:
            print(f"\nSuccessful downloads (citing papers):")
            for result in successful[:10]:  # Show first 10
                if hasattr(result, "pdf_path"):
                    print(f"  ✓ {Path(result.pdf_path).name}")
            if len(successful) > 10:
                print(f"  ... and {len(successful) - 10} more")

        if failed:
            print(f"\n⚠ Failed downloads ({len(failed)}):")
            for result in failed[:5]:  # Show first 5
                if hasattr(result, "publication"):
                    pub = result.publication
                    error = result.error if hasattr(result, "error") else "Unknown error"
                    print(f"  ✗ {pub.title[:60]}...")
                    print(f"    Error: {error}")
            if len(failed) > 5:
                print(f"  ... and {len(failed) - 5} more failures")

        # Save metadata
        import json

        metadata = {
            "geo_id": geo_id,
            "timestamp": datetime.now().isoformat(),
            "citing_papers_downloaded": len(successful),
            "citing_papers_failed": len(failed),
            "total_papers": len(papers),
        }

        with open(output_path / "download_metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)

        print(f"\n📁 Collection saved to: {output_path.absolute()}")
        print(f"   └── citing_papers/ ({len(successful)} PDFs)")

        return successful

    except ImportError:
        logger.warning("PDF downloader not available - skipping PDF downloads")
        print("\n⚠ PDF download functionality not available")
        print("Install required dependencies or check PDFDownloadManager implementation")
        return []
    except Exception as e:
        logger.error(f"PDF download failed: {e}", exc_info=True)
        print(f"\n✗ PDF download failed: {e}")
        return []


def main():
    """Command-line interface."""
    parser = argparse.ArgumentParser(
        description="Find recent papers citing GEO datasets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Find recent papers citing GSE103322
  python examples/geo_citation_tracking.py GSE103322

  # Get top 10 papers from 2022-2025
  python examples/geo_citation_tracking.py GSE103322 --min-year 2022 --max-papers 10

  # Download PDFs
  python examples/geo_citation_tracking.py GSE103322 --download-pdfs

  # Full workflow with custom parameters
  python examples/geo_citation_tracking.py GSE103322 \\
      --min-year 2020 \\
      --max-year 2025 \\
      --max-papers 20 \\
      --download-pdfs \\
      --output-dir ./pdfs/gse103322
        """,
    )

    parser.add_argument("geo_id", help="GEO accession ID (e.g., GSE103322, GSE12345)")
    parser.add_argument("--min-year", type=int, default=2020, help="Minimum publication year (default: 2020)")
    parser.add_argument("--max-year", type=int, default=2025, help="Maximum publication year (default: 2025)")
    parser.add_argument("--max-papers", type=int, default=20, help="Maximum papers to return (default: 20)")
    parser.add_argument("--download-pdfs", action="store_true", help="Download PDFs for found papers")
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Override output directory (default: auto-generated with GEO ID and timestamp)",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Run async function
    try:
        papers = asyncio.run(
            find_recent_citing_papers(
                geo_id=args.geo_id, min_year=args.min_year, max_year=args.max_year, max_papers=args.max_papers
            )
        )

        # Download PDFs if requested and papers found
        if args.download_pdfs and papers:
            asyncio.run(download_pdfs(papers=papers, geo_id=args.geo_id, output_dir=args.output_dir))

        # Summary
        print(f"\n{'='*80}")
        print("SUMMARY")
        print(f"{'='*80}")
        print(f"GEO Dataset: {args.geo_id}")
        print(f"Papers found: {len(papers)}")
        print(f"Year range: {args.min_year}-{args.max_year}")
        if args.download_pdfs and papers:
            if args.output_dir:
                print(f"PDFs location: {args.output_dir}")
            else:
                print(f"PDFs location: data/geo_citation_collections/{args.geo_id}_TIMESTAMP/")
        print(f"{'='*80}\n")

    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted by user (Ctrl+C)")
        return 1
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        print(f"\n✗ Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
