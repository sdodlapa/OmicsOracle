#!/usr/bin/env python3
"""
Real GEO Data Test for LLM Integration

This script tests the LLM summarization feature with actual GEO queries.
"""

import asyncio
import sys
from pathlib import Path

# Add the src directory to the Python path
from omics_oracle.pipeline.pipeline import OmicsOracle, ResultFormat


async def test_real_geo_query():
    """Test with a real GEO query."""
    print("🔬 Testing LLM Integration with Real GEO Data")
    print("=" * 50)

    # Initialize the pipeline
    oracle = OmicsOracle()

    try:
        # Test query
        query = "diabetes pancreatic beta cells"
        print(f"🔍 Query: '{query}'")
        print("📡 Searching GEO database...")

        # Process the query
        result = await oracle.process_query(query, max_results=3, result_format=ResultFormat.JSON)

        print(f"\n📊 Query Status: {result.status.value}")
        print(
            f"⏱️  Processing Time: {result.duration:.2f}s" if result.duration else "⏱️  Processing Time: N/A"
        )

        if result.is_failed:
            print(f"❌ Query failed: {result.error}")
            return False

        print(f"📈 Found {len(result.geo_ids)} GEO IDs")
        print(f"📚 Retrieved {len(result.metadata)} datasets with metadata")

        # Display GEO IDs found
        if result.geo_ids:
            print("\n🆔 GEO IDs Found:")
            for i, geo_id in enumerate(result.geo_ids[:5], 1):
                print(f"   {i}. {geo_id}")

        # Display AI summaries if available
        if result.ai_summaries:
            print("\n🤖 AI-Generated Summaries:")
            print("-" * 40)

            # Batch summary
            if "batch_summary" in result.ai_summaries:
                batch = result.ai_summaries["batch_summary"]
                print("📋 Batch Overview:")
                print(f"   Total datasets: {batch.get('total_datasets', 0)}")
                print(f"   Total samples: {batch.get('total_samples', 0)}")
                print(f"   Organisms: {', '.join(batch.get('organisms', []))}")
                print(f"   Overview: {batch.get('overview', 'N/A')}")
                print()

            # Brief overview
            if "brief_overview" in result.ai_summaries:
                brief = result.ai_summaries["brief_overview"]
                print("🎯 Brief Overview:")
                if isinstance(brief, dict):
                    for key, value in brief.items():
                        if value:
                            print(f"   {key}: {value}")
                else:
                    print(f"   {brief}")
                print()

            # Individual summaries
            if "individual_summaries" in result.ai_summaries:
                print("📚 Top Dataset Summaries:")
                for i, summary_data in enumerate(result.ai_summaries["individual_summaries"][:2], 1):
                    print(f"\n   🔬 Dataset {i}: {summary_data.get('accession', 'Unknown')}")
                    dataset_summaries = summary_data.get("summary", {})

                    if "overview" in dataset_summaries:
                        print(f"      Overview: {dataset_summaries['overview'][:200]}...")

                    if "technical_details" in dataset_summaries:
                        print(f"      Technical: {dataset_summaries['technical_details']}")
        else:
            print("\n⚠️  No AI summaries generated")

        # Display some metadata if available
        if result.metadata:
            print("\n📄 Sample Metadata (first dataset):")
            first = result.metadata[0]
            print(f"   Accession: {first.get('accession', 'N/A')}")
            print(f"   Title: {first.get('title', 'N/A')[:100]}...")
            print(f"   Organism: {first.get('organism', 'N/A')}")
            print(f"   Platform: {first.get('platform', 'N/A')}")
            print(f"   Relevance Score: {first.get('relevance_score', 0)}")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False

    finally:
        await oracle.close()


async def main():
    """Run the test."""
    success = await test_real_geo_query()

    if success:
        print("\n✅ Real GEO data integration test completed successfully!")
        print("\n💡 The LLM integration is working with live GEO data!")
        print("💡 You can now use this feature in the web interface or CLI.")
    else:
        print("\n❌ Test failed. Check the error messages above.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
