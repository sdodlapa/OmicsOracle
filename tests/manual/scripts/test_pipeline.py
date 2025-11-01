"""
Simple test to verify the OmicsOracle pipeline works.
"""

import asyncio
from pathlib import Path

# Add src to path
# Import project modules after path setup  # noqa: E402
from omics_oracle.core.config import Config  # noqa: E402
from omics_oracle.pipeline import OmicsOracle  # noqa: E402


async def test_pipeline():
    """Test basic pipeline functionality."""
    print("Testing OmicsOracle Pipeline...")

    # Initialize pipeline
    config = Config()
    oracle = OmicsOracle(config)

    print(f"Pipeline initialized with config: {config.ncbi.email}")

    try:
        # Test a simple query
        query = "BRCA1 breast cancer studies"
        print(f"Processing query: {query}")

        result = await oracle.process_query(query=query, max_results=5, include_sra=False)

        print("Query processed successfully!")
        print(f"Status: {result.status}")
        print(f"Intent: {result.intent}")
        print(f"Entities found: {len(result.entities)}")
        print(f"GEO IDs found: {len(result.geo_ids)}")
        print(f"Metadata processed: {len(result.metadata)}")
        print(f"Duration: {result.duration:.2f}s")

        if result.entities:
            print("\nDetected entities:")
            for entity_type, entities in result.entities.items():
                if entities:
                    print(f"  {entity_type}: {[e['text'] for e in entities]}")

        if result.geo_ids:
            print(f"\nFirst few GEO IDs: {result.geo_ids[:3]}")

        if result.metadata:
            print("\nTop result:")
            top_result = result.metadata[0]
            print(f"  ID: {top_result.get('accession', 'Unknown')}")
            print(f"  Title: {top_result.get('title', 'No title')[:100]}...")
            print(f"  Score: {top_result.get('relevance_score', 0)}")

        print("\nOK Pipeline test completed successfully!")

    except Exception as e:
        print(f"Pipeline test failed: {str(e)}")
        import traceback

        traceback.print_exc()

    finally:
        await oracle.close()


if __name__ == "__main__":
    asyncio.run(test_pipeline())
