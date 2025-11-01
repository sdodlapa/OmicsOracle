#!/usr/bin/env python3
"""
Direct pipeline test to see what's really being returned
"""

import asyncio
from pathlib import Path

# Add the main project root to path to import existing modules
from src.omics_oracle.core.config import Config
from src.omics_oracle.pipeline.pipeline import OmicsOracle


async def test_pipeline_directly():
    """Test the pipeline directly to see what metadata is returned"""

    print("🔍 Testing OmicsOracle Pipeline Directly")
    print("=" * 50)

    try:
        # Initialize pipeline
        config = Config()
        pipeline = OmicsOracle(config)
        print("✅ Pipeline initialized")

        # Test query
        query = "dna methylation data for bovine embryo development"
        print(f"🔍 Testing query: '{query}'")

        # Process query
        result = await pipeline.process_query(query, max_results=3)

        print(f"\n📊 PIPELINE RESULTS:")
        print(f"   GEO IDs found: {len(result.geo_ids)}")
        print(f"   Metadata entries: {len(result.metadata)}")
        print(f"   AI summaries: {bool(result.ai_summaries)}")

        print(f"\n🆔 GEO IDs: {result.geo_ids[:3]}")

        print(f"\n🔬 METADATA ANALYSIS:")
        for i, metadata in enumerate(result.metadata[:3]):
            print(f"\n   Dataset {i+1}: {result.geo_ids[i] if i < len(result.geo_ids) else 'Unknown'}")
            if metadata:
                print(f"     Metadata keys: {list(metadata.keys())}")
                print(f"     Title: {metadata.get('title', 'MISSING')}")
                print(f"     Summary length: {len(metadata.get('summary', ''))}")
                print(f"     Organism: {metadata.get('organism', 'MISSING')}")
                print(f"     Sample count: {metadata.get('sample_count', 'MISSING')}")
                print(f"     Platform: {metadata.get('platform', 'MISSING')}")
                print(
                    f"     Date fields: submission_date={metadata.get('submission_date', 'MISSING')}, last_update_date={metadata.get('last_update_date', 'MISSING')}"
                )
            else:
                print(f"     ❌ NO METADATA for this dataset!")

        print(f"\n🤖 AI SUMMARIES ANALYSIS:")
        if result.ai_summaries:
            print(f"   AI summary keys: {list(result.ai_summaries.keys())}")
            if "individual_summaries" in result.ai_summaries:
                individual = result.ai_summaries["individual_summaries"]
                print(f"   Individual summaries count: {len(individual)}")
                for item in individual:
                    print(f"     - {item.get('accession', 'Unknown')}: {len(item.get('summary', ''))} chars")
            if "batch_summary" in result.ai_summaries:
                batch = result.ai_summaries["batch_summary"]
                print(f"   Batch summary length: {len(batch)}")
        else:
            print("   ❌ NO AI SUMMARIES!")

    except Exception as e:
        print(f"💥 Pipeline test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_pipeline_directly())
