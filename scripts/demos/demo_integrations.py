"""
Demo of OmicsOracle third-party integrations.

This script demonstrates how to use the PubMed and citation manager integrations
to enrich GEO dataset information with related research papers and export citations.
"""

import asyncio
import os

# Add the src directory to the path
from omics_oracle.integrations.service import IntegrationService


async def demo_integration_service() -> None:
    """Demonstrate the integration service functionality."""
    print("OmicsOracle Integration Service Demo")
    print("=" * 50)

    # Mock GEO datasets for demo
    mock_datasets = [
        {
            "accession": "GSE30611",
            "title": "RNA-seq of coding RNA from tissue samples",
            "summary": "RNA sequencing data from various tissue samples to study gene expression patterns.",
            "submission_date": "2011-06-15",
            "organism": "Homo sapiens",
            "platform": "GPL11154",
        },
        {
            "accession": "GSE48558",
            "title": "Genome-wide analysis of transcription factor binding",
            "summary": "ChIP-seq analysis of transcription factor binding sites in human cells.",
            "submission_date": "2013-07-20",
            "organism": "Homo sapiens",
            "platform": "GPL16791",
        },
    ]

    # Initialize integration service
    service = IntegrationService()

    print("1. Enriching datasets with related papers...")
    print("-" * 30)

    # Enrich datasets (this will try to fetch papers but may fail due to SSL/network issues)
    enriched_datasets = await service.batch_enrich_datasets(mock_datasets, include_papers=True, max_papers=3)

    for dataset in enriched_datasets:
        print(f"\nDataset: {dataset['accession']}")
        print(f"Title: {dataset['title']}")
        print(f"Related papers found: {len(dataset.get('related_papers', []))}")

        # Show first paper if available
        papers = dataset.get("related_papers", [])
        if papers:
            first_paper = papers[0]
            print(f"  First paper: {first_paper.get('title', 'No title')}")
            print(f"  Authors: {', '.join(first_paper.get('authors', [])[:2])}")
            print(f"  PMID: {first_paper.get('pmid', 'Unknown')}")

    print("\n" + "=" * 50)
    print("2. Generating citations in different formats...")
    print("-" * 30)

    # Generate BibTeX citations
    print("\nBibTeX Format:")
    print("-" * 15)
    bibtex_citations = service.export_citations(enriched_datasets, format_type="bibtex", include_papers=True)
    print(bibtex_citations)

    # Generate RIS citations
    print("\nRIS Format:")
    print("-" * 10)
    ris_citations = service.export_citations(enriched_datasets, format_type="ris", include_papers=True)
    print(ris_citations)

    # Save citations to files
    print("\n" + "=" * 50)
    print("3. Saving citations to files...")
    print("-" * 30)

    with open("geo_datasets.bib", "w") as f:
        f.write(bibtex_citations)
    print("✓ Saved BibTeX citations to 'geo_datasets.bib'")

    with open("geo_datasets.ris", "w") as f:
        f.write(ris_citations)
    print("✓ Saved RIS citations to 'geo_datasets.ris'")

    # Generate CSL-JSON for modern reference managers
    csl_json = service.export_citations(enriched_datasets, format_type="csl-json", include_papers=True)
    with open("geo_datasets.json", "w") as f:
        f.write(csl_json)
    print("✓ Saved CSL-JSON citations to 'geo_datasets.json'")

    print("\n" + "=" * 50)
    print("4. Integration Service Summary")
    print("-" * 30)
    print(f"✓ Processed {len(enriched_datasets)} datasets")
    print("✓ Generated citations in 3 formats (BibTeX, RIS, CSL-JSON)")
    print("✓ Saved citation files for import into reference managers")
    print("\nThe integration service provides:")
    print("  • Automatic paper discovery via PubMed search")
    print("  • Multiple citation export formats")
    print("  • Batch processing of multiple datasets")
    print("  • Error handling for network/API issues")

    print("\n" + "=" * 50)
    print("Demo completed successfully!")


if __name__ == "__main__":
    asyncio.run(demo_integration_service())
