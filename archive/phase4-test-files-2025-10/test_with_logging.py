"""
Debug test - using integration layer with logging
"""
import asyncio
import logging

from omics_oracle_v2.integration import SearchClient

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)


async def test_with_logging():
    """Test SearchClient with debug logging enabled"""
    print("\n" + "=" * 80)
    print("TESTING WITH DEBUG LOGGING")
    print("=" * 80)

    async with SearchClient() as client:
        print("\n[TEST] Searching for 'CRISPR'")
        try:
            results = await client.search(query="CRISPR", databases=["pubmed"], max_results=3)
            print("\n[OK] Search successful!")
            print(f"Total results: {results.metadata.total_results}")
            print(f"Results count: {len(results.results)}")
            if results.results:
                print(f"First result: {results.results[0].title[:100]}...")
        except Exception as e:
            print(f"\n[ERROR] {e}")
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_with_logging())
