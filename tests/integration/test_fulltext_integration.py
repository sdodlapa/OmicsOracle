#!/usr/bin/env python3
"""
Test Full-Text AI Analysis Integration

This script tests the complete flow:
1. Search for datasets
2. Enrich with full-text
3. Analyze with AI
"""

import asyncio
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from omics_oracle_v2.api.models.responses import DatasetResponse
from omics_oracle_v2.services.fulltext_service import FullTextService


async def test_fulltext_enrichment():
    """Test full-text enrichment with a real dataset."""
    
    print("=" * 60)
    print("Full-Text Enrichment Integration Test")
    print("=" * 60)
    
    # Create a mock dataset with known PMIDs
    test_dataset = DatasetResponse(
        geo_id="GSE306759",
        title="Effect of palmitate on hepatocyte function",
        summary="This study examines the effects of palmitate treatment on hepatocytes...",
        organism="Homo sapiens",
        sample_count=8,
        platform="GPL34281",
        relevance_score=0.95,
        match_reasons=["Contains keyword: palmitate", "High sample count"],
        pubmed_ids=["38287617"],  # Real PMID from this dataset
    )
    
    print(f"\n1. Test Dataset:")
    print(f"   GEO ID: {test_dataset.geo_id}")
    print(f"   Title: {test_dataset.title}")
    print(f"   PMIDs: {test_dataset.pubmed_ids}")
    print(f"   Full-text Status: {test_dataset.fulltext_status}")
    
    # Initialize service
    print(f"\n2. Initializing FullTextService...")
    service = FullTextService()
    
    # Enrich dataset
    print(f"\n3. Enriching dataset with full-text (this may take 10-30 seconds)...")
    enriched = await service.enrich_dataset_with_fulltext(test_dataset, max_papers=1)
    
    # Display results
    print(f"\n4. Results:")
    print(f"   Full-text Status: {enriched.fulltext_status}")
    print(f"   Full-text Count: {enriched.fulltext_count}")
    
    if enriched.fulltext:
        for i, ft in enumerate(enriched.fulltext, 1):
            print(f"\n   Paper {i}:")
            print(f"   - PMID: {ft.pmid}")
            print(f"   - Title: {ft.title[:100]}...")
            print(f"   - Format: {ft.format}")
            print(f"   - Abstract: {len(ft.abstract)} chars")
            print(f"   - Methods: {len(ft.methods)} chars")
            print(f"   - Results: {len(ft.results)} chars")
            print(f"   - Discussion: {len(ft.discussion)} chars")
            
            if ft.methods:
                print(f"\n   Methods Preview:")
                print(f"   {ft.methods[:300]}...")
    else:
        print(f"   ⚠️ No full-text content retrieved")
        print(f"   Possible reasons:")
        print(f"   - PDF not available in PMC")
        print(f"   - Parsing failed")
        print(f"   - Network issues")
    
    print(f"\n5. Summary:")
    summary = service.get_fulltext_summary(enriched)
    print(f"   {summary}")
    
    print("\n" + "=" * 60)
    if enriched.fulltext_count > 0:
        print("✅ TEST PASSED - Full-text enrichment working!")
    else:
        print("⚠️ TEST WARNING - No full-text retrieved (may be expected)")
    print("=" * 60)
    
    return enriched


async def test_batch_enrichment():
    """Test batch enrichment with multiple datasets."""
    
    print("\n" + "=" * 60)
    print("Batch Enrichment Test")
    print("=" * 60)
    
    # Create multiple test datasets
    datasets = [
        DatasetResponse(
            geo_id="GSE306759",
            title="Effect of palmitate on hepatocytes",
            summary="Study on palmitate effects...",
            organism="Homo sapiens",
            sample_count=8,
            platform="GPL34281",
            relevance_score=0.95,
            match_reasons=["High relevance"],
            pubmed_ids=["38287617"],
        ),
        DatasetResponse(
            geo_id="GSE306760",
            title="RNA-seq of liver samples",
            summary="Transcriptome analysis...",
            organism="Homo sapiens",
            sample_count=12,
            platform="GPL24676",
            relevance_score=0.85,
            match_reasons=["Relevant"],
            pubmed_ids=[],  # No PMIDs - should handle gracefully
        ),
    ]
    
    print(f"\n1. Testing batch enrichment of {len(datasets)} datasets")
    
    service = FullTextService()
    enriched = await service.enrich_datasets_batch(datasets, max_papers_per_dataset=1)
    
    print(f"\n2. Results:")
    for ds in enriched:
        print(f"   - {ds.geo_id}: {ds.fulltext_status} ({ds.fulltext_count} papers)")
    
    success_count = sum(1 for ds in enriched if ds.fulltext_count > 0)
    print(f"\n3. Summary: {success_count}/{len(enriched)} datasets enriched")
    
    return enriched


if __name__ == "__main__":
    # Run tests
    print("\nStarting Full-Text Integration Tests...\n")
    
    # Test 1: Single dataset enrichment
    enriched_dataset = asyncio.run(test_fulltext_enrichment())
    
    # Test 2: Batch enrichment
    print("\n" + "=" * 60 + "\n")
    enriched_batch = asyncio.run(test_batch_enrichment())
    
    print("\n\n🎉 All tests complete!")
    print("\nNext steps:")
    print("1. Open http://localhost:8000/dashboard")
    print("2. Search for 'breast cancer RNA-seq'")
    print("3. Watch for full-text status indicators")
    print("4. Click 'AI Analysis' to see richer insights")
