"""
Test the third-party integrations.
"""

import asyncio
import os

# Add the src directory to the path
from omics_oracle.integrations.citation_managers import CitationManagerIntegration
from omics_oracle.integrations.pubmed import PubMedIntegration


async def test_pubmed_integration() -> None:
    """Test PubMed integration with a known GEO dataset."""
    print("Testing PubMed integration...")

    async with PubMedIntegration() as pubmed:
        # Test with a well-known GEO dataset
        papers = await pubmed.get_related_papers(
            "GSE30611",
            "RNA-seq of coding RNA from tissue samples",
            max_results=3,
        )

        print(f"Found {len(papers)} related papers for GSE30611:")
        for i, paper in enumerate(papers, 1):
            print(f"\n{i}. {paper.get('title', 'No title')}")
            print(f"   Authors: {', '.join(paper.get('authors', [])[:3])}")
            print(f"   Journal: {paper.get('journal', 'Unknown')}")
            print(f"   Year: {paper.get('year', 'Unknown')}")
            print(f"   PMID: {paper.get('pmid', 'Unknown')}")
            if paper.get("abstract"):
                abstract_preview = (
                    paper["abstract"][:200] + "..." if len(paper["abstract"]) > 200 else paper["abstract"]
                )
                print(f"   Abstract: {abstract_preview}")


def test_citation_manager() -> None:
    """Test citation manager integration."""
    print("\n" + "=" * 50)
    print("Testing Citation Manager integration...")

    # Mock GEO dataset data
    mock_geo_data = {
        "accession": "GSE30611",
        "title": "RNA-seq of coding RNA from tissue samples",
        "summary": "This dataset contains RNA sequencing data from various tissue samples to study gene expression patterns.",
        "submission_date": "2011-06-15",
    }

    citation_manager = CitationManagerIntegration()

    # Format as reference
    reference = citation_manager.format_geo_reference(mock_geo_data)
    print(f"\nFormatted reference: {reference['title']}")

    # Test BibTeX export
    print("\nBibTeX format:")
    bibtex = citation_manager.to_bibtex(reference)
    print(bibtex)

    # Test RIS export
    print("\nRIS format:")
    ris = citation_manager.to_ris(reference)
    print(ris)

    # Test CSL-JSON export
    print("\nCSL-JSON format:")
    csl_json = citation_manager.to_csl_json(reference)
    print(csl_json)


if __name__ == "__main__":
    print("OmicsOracle Third-Party Integrations Test")
    print("=" * 50)

    # Test PubMed integration
    try:
        asyncio.run(test_pubmed_integration())
    except Exception as e:
        print(f"PubMed integration test failed: {e}")

    # Test citation manager
    try:
        test_citation_manager()
    except Exception as e:
        print(f"Citation manager test failed: {e}")

    print("\n" + "=" * 50)
    print("Integration tests completed!")
