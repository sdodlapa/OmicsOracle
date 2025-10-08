"""
Quick validation test for updated SearchClient
"""
import asyncio

from omics_oracle_v2.integration import SearchClient


async def test_search():
    """Test the updated search client"""
    print("\n" + "=" * 80)
    print("TESTING UPDATED SEARCH CLIENT")
    print("=" * 80)

    async with SearchClient() as client:
        print("\n[TEST 1] Basic search for 'CRISPR'")
        try:
            results = await client.search(query="CRISPR", databases=["pubmed"], max_results=5)
            print("  [OK] Search completed!")
            print(f"  [OK] Response type: {type(results)}")
            print(f"  [OK] Response data: {results}")
        except Exception as e:
            print(f"  [ERROR] {e}")
            import traceback

            traceback.print_exc()

        print("\n[TEST 2] Semantic search")
        try:
            results = await client.search(
                query="gene therapy", databases=["pubmed", "semantic_scholar"], max_results=3
            )
            print("  [OK] Semantic search completed!")
            print(f"  [OK] Results: {results}")
        except Exception as e:
            print(f"  [ERROR] {e}")


if __name__ == "__main__":
    asyncio.run(test_search())
