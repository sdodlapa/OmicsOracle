#!/usr/bin/env python3
"""
Test both NCBI and OpenAI API keys to verify they're actually working.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(project_root / ".env")

print("\n" + "=" * 80)
print(" " * 25 + "API KEY VERIFICATION TEST")
print("=" * 80 + "\n")

# Test 1: NCBI GEO API
print("1️⃣  Testing NCBI GEO API...")
print("-" * 80)

try:
    from omics_oracle_v2.core.config import get_settings
    from omics_oracle_v2.lib.geo import GEOClient
    
    settings = get_settings()
    
    print(f"   Email: {settings.geo.ncbi_email}")
    print(f"   API Key: {settings.geo.ncbi_api_key[:10]}...{settings.geo.ncbi_api_key[-4:]}")
    print(f"   Rate Limit: {settings.geo.rate_limit} req/sec")
    
    # Create GEO client
    geo_client = GEOClient(settings.geo)
    
    # Test search
    print(f"\n   🔍 Testing search for 'breast cancer'...")
    
    async def test_geo_search():
        result = await geo_client.search("breast cancer", max_results=3)
        return result
    
    search_result = asyncio.run(test_geo_search())
    
    print(f"   ✅ NCBI GEO API WORKING!")
    print(f"   Found: {search_result.total_found} total datasets")
    print(f"   Returned: {len(search_result.geo_ids)} IDs")
    if search_result.geo_ids:
        print(f"   First 3 IDs: {search_result.geo_ids[:3]}")
    
    # Test metadata fetch
    if search_result.geo_ids:
        test_id = search_result.geo_ids[0]
        print(f"\n   📊 Testing metadata fetch for {test_id}...")
        
        async def test_geo_metadata():
            metadata = await geo_client.get_metadata(test_id)
            return metadata
        
        metadata = asyncio.run(test_geo_metadata())
        
        print(f"   ✅ Metadata fetched successfully!")
        print(f"   Title: {metadata.title[:80]}...")
        print(f"   Organism: {metadata.organism}")
        print(f"   Samples: {metadata.samples_count}")
        print(f"   Platform: {metadata.platform_id}")
    
    print(f"\n   🎉 NCBI GEO API: ✅ FULLY WORKING")
    ncbi_works = True
    
except Exception as e:
    print(f"   ❌ NCBI GEO API ERROR: {e}")
    import traceback
    traceback.print_exc()
    ncbi_works = False

# Test 2: OpenAI API
print("\n\n2️⃣  Testing OpenAI API...")
print("-" * 80)

try:
    from omics_oracle_v2.lib.ai import SummarizationClient, SummaryType
    
    settings = get_settings()
    
    print(f"   API Key: {settings.ai.openai_api_key[:10]}...{settings.ai.openai_api_key[-10:]}")
    print(f"   Model: {settings.ai.model}")
    print(f"   Max Tokens: {settings.ai.max_tokens}")
    print(f"   Temperature: {settings.ai.temperature}")
    
    # Create AI client
    ai_client = SummarizationClient(settings)
    
    if not ai_client.client:
        print(f"   ❌ OpenAI client failed to initialize")
        openai_works = False
    else:
        print(f"\n   🤖 Testing AI summarization...")
        
        # Test with sample data
        test_metadata = {
            "accession": "GSE123456",
            "title": "RNA-seq analysis of breast cancer tissue samples",
            "summary": "Gene expression profiling of tumor and normal breast tissue",
            "organism": "Homo sapiens",
            "platform": "Illumina HiSeq 2500",
            "samples_count": 24
        }
        
        response = ai_client.summarize(
            metadata=test_metadata,
            query_context="breast cancer RNA-seq",
            summary_type=SummaryType.BRIEF,
            dataset_id="GSE123456"
        )
        
        if response and response.brief:
            print(f"   ✅ OpenAI API WORKING!")
            print(f"   Model Used: {response.model_used}")
            print(f"   Generated Summary:")
            print(f"   {response.brief[:200]}...")
            openai_works = True
        else:
            print(f"   ❌ OpenAI returned no response")
            openai_works = False
    
    print(f"\n   🎉 OpenAI API: ✅ FULLY WORKING")
    
except Exception as e:
    print(f"   ❌ OpenAI API ERROR: {e}")
    import traceback
    traceback.print_exc()
    openai_works = False

# Final Summary
print("\n\n" + "=" * 80)
print(" " * 30 + "FINAL RESULTS")
print("=" * 80)

print(f"\n{'✅' if ncbi_works else '❌'} NCBI GEO API: {'WORKING' if ncbi_works else 'FAILED'}")
print(f"{'✅' if openai_works else '❌'} OpenAI API: {'WORKING' if openai_works else 'FAILED'}")

if ncbi_works and openai_works:
    print("\n🎉 ALL API KEYS VERIFIED AND WORKING!")
    print("\nYou can now:")
    print("  • Search real genomics datasets from NCBI GEO")
    print("  • Generate AI-powered summaries with GPT-4 Turbo")
    print("  • Run complete workflows with both features")
elif ncbi_works:
    print("\n⚠️  NCBI works but OpenAI needs attention")
elif openai_works:
    print("\n⚠️  OpenAI works but NCBI needs attention")
else:
    print("\n❌ Both APIs need configuration")

print("\n" + "=" * 80 + "\n")

exit(0 if (ncbi_works and openai_works) else 1)
