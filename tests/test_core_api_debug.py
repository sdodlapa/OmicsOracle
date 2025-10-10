"""Debug CORE API to see actual responses."""

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from omics_oracle_v2.lib.publications.clients.oa_sources.core_client import COREClient, COREConfig


async def test_core_api():
    """Test CORE API with a known DOI."""
    
    api_key = os.getenv("CORE_API_KEY")
    if not api_key:
        print("ERROR: CORE_API_KEY not set")
        return
    
    print(f"CORE API Key: {api_key[:10]}...")
    print()
    
    config = COREConfig(api_key=api_key)
    
    async with COREClient(config) as client:
        # Test with a known PLOS paper (should be in CORE)
        test_doi = "10.1371/journal.pgen.1011043"
        
        print(f"Testing DOI: {test_doi}")
        print("=" * 80)
        
        # Try the search
        result = await client.get_fulltext_by_doi(test_doi)
        
        if result:
            print("✅ FOUND in CORE!")
            print(f"  Title: {result.get('title')}")
            print(f"  Download URL: {result.get('downloadUrl')}")
            print(f"  Source URLs: {result.get('sourceFulltextUrls')}")
            print(f"  Has full-text: {bool(result.get('fullText'))}")
        else:
            print("❌ NOT FOUND in CORE")
            print()
            
            # Try a different query format
            print("Trying alternate search...")
            results = await client.search_by_title("PLOS Genetics", limit=2)
            if results:
                print(f"✅ Found {len(results)} results by title")
                for i, r in enumerate(results[:2], 1):
                    print(f"  [{i}] {r.get('title', 'No title')[:60]}")
            else:
                print("❌ No results by title either")
                print()
                print("CORE API might have changed or the API key might not have access")


if __name__ == "__main__":
    asyncio.run(test_core_api())
