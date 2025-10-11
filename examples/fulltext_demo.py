"""
Demo: End-to-end full-text extraction using pubmed_parser

This demonstrates the complete workflow:
1. Fetch PMC XML from NCBI
2. Extract structured content (authors, figures, tables, references, sections)
3. Display results

Usage:
    python examples/fulltext_demo.py
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.fulltext.content_extractor import ContentExtractor
from lib.fulltext.content_fetcher import ContentFetcher
from lib.fulltext.models import ContentType, FullTextResult, SourceType

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def demo_pmc_extraction():
    """
    Demonstrate PMC full-text extraction with structured parsing.

    Example PMC articles:
    - PMC3166277: BMC Microbiology article (good test case)
    - PMC2228570: Open access article with tables/figures
    - PMC3148254: Another good example
    """

    print("\n" + "=" * 80)
    print("FULL-TEXT EXTRACTION DEMO - Using pubmed_parser")
    print("=" * 80 + "\n")

    # Initialize components
    cache_dir = Path("data/fulltext")
    fetcher = ContentFetcher(
        cache_dir=cache_dir,
        api_key=None,  # Use 3 req/sec without API key
        requests_per_second=3.0,
    )
    extractor = ContentExtractor()

    # Test PMC IDs (known good articles)
    test_pmcs = [
        "PMC3166277",  # BMC Microbiology - bacteriophage study
        "PMC2228570",  # Another good example
    ]

    for pmc_id in test_pmcs:
        print("\n{'='*80}")
        print("Processing: {pmc_id}")
        print("{'='*80}\n")

        try:
            # Step 1: Fetch XML from PMC
            print("[1/3] Fetching XML from PMC...")
            success, xml_content, error = await fetcher.fetch_xml(
                source=SourceType.PMC, identifier=pmc_id, use_cache=True
            )

            if not success:
                print("  ERROR: Failed to fetch - {error}")
                continue

            print("  SUCCESS: Retrieved {len(xml_content):,} bytes")

            # Step 2: Extract structured content
            print("\n[2/3] Extracting structured content...")

            # Get cache path for the XML file
            cache_path = fetcher.get_cache_path(ContentType.XML, SourceType.PMC, pmc_id.replace("PMC", ""))

            structured = extractor.extract_structured_content(xml_content, source_path=str(cache_path))

            if structured is None:
                print("  ERROR: Extraction failed")
                # Try fallback plain text
                print("  Trying fallback plain text extraction...")
                plain_text = extractor.extract_text(xml_content)
                print("  Extracted {len(plain_text):,} characters (plain text)")
                continue

            print("  SUCCESS: Extracted structured content")

            # Step 3: Display results
            print("\n[3/3] RESULTS:")
            print("\n  Title: {structured.title}")
            print("  Journal: {structured.journal}")
            print("  Year: {structured.publication_year}")
            print("  DOI: {structured.doi}")
            print("  PMID: {structured.pmid}")
            print("  PMC: {structured.pmc}")

            print("\n  Abstract: {structured.abstract[:200]}..." if structured.abstract else "  No abstract")

            print("\n  Authors ({len(structured.authors)}):")
            for i, author in enumerate(structured.authors[:5], 1):
                affs = " - {len(author.affiliations)} affiliation(s)" if author.affiliations else ""
                print("    {i}. {author.full_name}{affs}")
            if len(structured.authors) > 5:
                print("    ... and {len(structured.authors) - 5} more")

            print("\n  Keywords ({len(structured.keywords)}):")
            if structured.keywords:
                print("    {', '.join(structured.keywords[:10])}")

            print("\n  Sections ({len(structured.sections)}):")
            for section in structured.sections:
                para_count = len(section.paragraphs)
                print("    - {section.title}: {para_count} paragraph(s)")

            print("\n  Figures: {len(structured.figures)}")
            for fig in structured.figures[:3]:
                print("    - {fig.label}: {fig.caption[:60]}...")

            print("\n  Tables: {len(structured.tables)}")
            for table in structured.tables[:3]:
                cols = len(table.table_columns)
                rows = len(table.table_values)
                print("    - {table.label}: {cols} columns x {rows} rows")

            print("\n  References: {len(structured.references)}")
            for ref in structured.references[:3]:
                print("    - {ref.title[:60]}...")

            # Test utility methods
            print("\n  Utility Methods:")
            methods_text = structured.get_methods_text()
            if methods_text:
                print("    - Methods section: {len(methods_text):,} characters")

            results_text = structured.get_results_text()
            if results_text:
                print("    - Results section: {len(results_text):,} characters")

            full_text = structured.get_full_text()
            print("    - Full text: {len(full_text):,} characters")

            # Calculate quality score
            print("\n  Quality Indicators:")
            indicators = extractor.calculate_quality_score(None, structured, ContentType.XML)
            for key, value in indicators.items():
                print("    - {key}: {value}")

            # Create FullTextResult
            result = FullTextResult(
                success=True,
                content=full_text[:1000],  # First 1000 chars
                structured_content=structured,
                content_type=ContentType.XML,
                source=SourceType.PMC,
                source_url="https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc_id}/",
                has_abstract=indicators["has_abstract"],
                has_methods=indicators["has_methods"],
                has_references=indicators["has_references"],
                has_figures=indicators["has_figures"],
                word_count=indicators["word_count"],
            )

            score = result.calculate_quality_score()
            print("\n  Overall Quality Score: {score:.2f}")

            print("\n  {'='*80}")
            print("  COMPLETE: {pmc_id} processed successfully!")
            print("  {'='*80}\n")

        except Exception as e:
            logger.error("Error processing {pmc_id}: {e}", exc_info=True)
            print("\n  ERROR: {e}\n")


async def main():
    """Run the demo."""
    await demo_pmc_extraction()

    print("\n" + "=" * 80)
    print("DEMO COMPLETE")
    print("=" * 80)
    print("\nKey Features Demonstrated:")
    print("  1. PMC XML fetching with caching and rate limiting")
    print("  2. Structured content extraction using pubmed_parser")
    print("  3. Author extraction with affiliations")
    print("  4. Figure, table, and reference extraction")
    print("  5. Section-based text organization")
    print("  6. Quality scoring")
    print("\nNext Steps:")
    print("  - Integrate with existing FullTextManager")
    print("  - Add PDF parsing (Phase 1C)")
    print("  - Implement Tier 2-4 sources")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
