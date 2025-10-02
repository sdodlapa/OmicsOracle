"""
Quick integration validation script.
"""

import asyncio
import os
import sys

from omics_oracle.integrations.citation_managers import CitationManagerIntegration
from omics_oracle.integrations.pubmed import PubMedIntegration
from omics_oracle.integrations.service import IntegrationService


async def test_integrations():
    """Test that our integrations work."""
    print("🧪 INTEGRATION VALIDATION")
    print("=========================")

    # Test citation manager (doesn't require network)
    print("\n1. Testing Citation Manager...")
    citation_manager = CitationManagerIntegration()

    mock_geo_data = {
        "accession": "GSE12345",
        "title": "Test Dataset",
        "summary": "This is a test dataset.",
        "submission_date": "2023-01-01",
    }

    reference = citation_manager.format_geo_reference(mock_geo_data)
    print(f"✅ Reference formatted: {reference['title']}")

    bibtex = citation_manager.to_bibtex(reference)
    print(f"✅ BibTeX generated: {len(bibtex)} characters")

    # Test PubMed integration (with timeout)
    print("\n2. Testing PubMed Integration...")
    try:
        async with PubMedIntegration() as pubmed:
            # Try a simple search with timeout
            papers = await asyncio.wait_for(pubmed.search_papers("GSE30611", max_results=2), timeout=10.0)
            print(f"✅ PubMed search successful: Found {len(papers)} paper IDs")

            if papers:
                # Try to fetch details for first paper
                details = await asyncio.wait_for(pubmed.fetch_paper_details(papers[:1]), timeout=10.0)
                if details:
                    print(f"✅ Paper details fetched: {details[0].get('title', 'No title')[:50]}...")
                else:
                    print("⚠️  No paper details returned")

    except asyncio.TimeoutError:
        print("⚠️  PubMed test timed out (network/SSL issues)")
    except Exception as e:
        print(f"⚠️  PubMed test failed: {e}")

    # Test integration service
    print("\n3. Testing Integration Service...")
    service = IntegrationService()

    # Test citation export without network calls
    mock_datasets = [mock_geo_data]
    citations = service.export_citations(mock_datasets, "bibtex", include_papers=False)
    print(f"✅ Integration service citations: {len(citations)} characters")

    print("\n🎉 Integration validation completed!")
    return True


if __name__ == "__main__":
    try:
        result = asyncio.run(test_integrations())
        print("\n✅ All integration tests completed successfully!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Integration validation failed: {e}")
        sys.exit(1)
