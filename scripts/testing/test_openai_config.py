#!/usr/bin/env python3
"""
Test OpenAI API configuration and connectivity.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    env_file = project_root / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        print(f"📁 Loaded environment from: {env_file}")
    else:
        print(f"⚠️  .env file not found at: {env_file}")
except ImportError:
    print("⚠️  python-dotenv not installed, relying on pydantic to load .env")

from omics_oracle_v2.core.config import get_settings
from omics_oracle_v2.lib.ai import SummarizationClient, SummaryType


def test_configuration():
    """Test that OpenAI configuration is loaded correctly."""
    print("🔧 Testing OpenAI Configuration")
    print("=" * 70)
    
    # Load settings
    settings = get_settings()
    
    print("\n📋 Configuration Status:")
    print(f"  API Key Set: {'✅ Yes' if settings.ai.openai_api_key else '❌ No'}")
    
    if settings.ai.openai_api_key:
        # Mask the key for security
        key = settings.ai.openai_api_key
        masked_key = f"{key[:10]}...{key[-10:]}" if len(key) > 20 else "***"
        print(f"  API Key: {masked_key}")
    
    print(f"  Model: {settings.ai.model}")
    print(f"  Max Tokens: {settings.ai.max_tokens}")
    print(f"  Temperature: {settings.ai.temperature}")
    print(f"  Timeout: {settings.ai.timeout}s")
    
    print("\n🔍 Environment Variables:")
    print(f"  OMICS_AI_OPENAI_API_KEY: {'✅ Set' if os.getenv('OMICS_AI_OPENAI_API_KEY') else '❌ Not Set'}")
    print(f"  OPENAI_API_KEY: {'✅ Set' if os.getenv('OPENAI_API_KEY') else '❌ Not Set'}")
    print(f"  OMICS_AI_MODEL: {os.getenv('OMICS_AI_MODEL', 'Not Set')}")
    
    return settings


async def test_openai_client():
    """Test OpenAI client initialization and basic functionality."""
    print("\n\n🤖 Testing OpenAI Client")
    print("=" * 70)
    
    settings = get_settings()
    
    try:
        # Initialize client
        client = SummarizationClient(settings)
        
        if not client.client:
            print("❌ OpenAI client not initialized")
            print("   Check if OMICS_AI_OPENAI_API_KEY is set correctly")
            return False
        
        print("✅ OpenAI client initialized successfully")
        print(f"   Model: {settings.ai.model}")
        
        # Test with sample genomics metadata
        print("\n📊 Testing with Sample Genomics Dataset...")
        sample_metadata = {
            "accession": "GSE123456",
            "title": "RNA-seq analysis of breast cancer tissue samples",
            "summary": "Gene expression profiling of tumor and normal breast tissue using RNA-seq",
            "organism": "Homo sapiens",
            "platform": "Illumina HiSeq 2500",
            "samples_count": 48,
            "study_type": "Expression profiling by high throughput sequencing",
        }
        
        print("\n🔄 Generating AI summary (this may take a few seconds)...")
        response = client.summarize(
            metadata=sample_metadata,
            query_context="breast cancer RNA-seq",
            summary_type=SummaryType.BRIEF,
            dataset_id="GSE123456"
        )
        
        if response:
            print("\n✅ AI Summary Generated Successfully!")
            print("\n" + "=" * 70)
            print("📝 GENERATED SUMMARY:")
            print("=" * 70)
            
            if response.brief:
                print(f"\n{response.brief}")
            
            if response.overview:
                print(f"\nOverview:\n{response.overview}")
            
            print("\n" + "=" * 70)
            print(f"Model Used: {response.model_used}")
            if hasattr(response, 'tokens_estimated'):
                print(f"Tokens Estimated: {response.tokens_estimated}")
            print("=" * 70)
            
            return True
        else:
            print("❌ Failed to generate summary")
            return False
            
    except Exception as e:
        print(f"❌ Error testing OpenAI client: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_full_workflow():
    """Test a complete workflow with OpenAI integration."""
    print("\n\n🔬 Testing Full Workflow with OpenAI")
    print("=" * 70)
    
    import httpx
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as http_client:
            print("\n🚀 Executing workflow with AI report generation...")
            
            response = await http_client.post(
                "http://localhost:8000/api/v1/workflows/dev/execute",
                json={
                    "query": "breast cancer RNA-seq GSE123456",
                    "workflow_type": "quick_report"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"\n✅ Workflow completed: {data.get('success')}")
                
                # Check if report was generated
                if data.get('report'):
                    report = data['report']
                    print(f"\n📊 Report Generated:")
                    print(f"   Title: {report.get('title', 'N/A')}")
                    print(f"   Summary: {report.get('summary', 'N/A')[:200]}...")
                    print(f"   Datasets Analyzed: {report.get('total_datasets_analyzed', 0)}")
                    
                    if report.get('key_insights'):
                        print(f"\n💡 Key Insights ({len(report['key_insights'])} found):")
                        for insight in report['key_insights'][:3]:
                            print(f"   • {insight.get('insight', 'N/A')}")
                    
                    return True
                else:
                    print("⚠️  Workflow succeeded but no report generated")
                    return False
            else:
                print(f"❌ Workflow failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Error in workflow test: {e}")
        return False


async def main():
    """Run all tests."""
    print("\n" + "🧬 " * 20)
    print(" " * 15 + "OPENAI CONFIGURATION TEST SUITE")
    print("🧬 " * 20 + "\n")
    
    # Test 1: Configuration
    settings = test_configuration()
    
    if not settings.ai.openai_api_key:
        print("\n" + "=" * 70)
        print("⚠️  WARNING: No OpenAI API key found!")
        print("=" * 70)
        print("\nTo configure OpenAI:")
        print("1. Check that .env file contains OMICS_AI_OPENAI_API_KEY")
        print("2. Make sure the key is valid (not expired or revoked)")
        print("3. Restart the server to pick up the new configuration")
        print("\nCurrent .env location: /Users/sanjeevadodlapati/Downloads/Repos/OmicsOracle/.env")
        return
    
    # Test 2: Client initialization and AI generation
    client_success = await test_openai_client()
    
    # Test 3: Full workflow (only if server is running)
    print("\n" + "=" * 70)
    user_input = input("\n🌐 Test full workflow with server? (requires server running) [y/N]: ")
    
    if user_input.lower() in ['y', 'yes']:
        await test_full_workflow()
    else:
        print("⏭️  Skipping workflow test")
    
    # Summary
    print("\n\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    print(f"✅ Configuration: Loaded")
    print(f"{'✅' if client_success else '❌'} OpenAI Client: {'Working' if client_success else 'Failed'}")
    print("=" * 70)
    
    if client_success:
        print("\n🎉 SUCCESS! OpenAI is configured and working!")
        print("\n💡 Next Steps:")
        print("   1. Use the dashboard at http://localhost:8000/dashboard")
        print("   2. Select 'Quick Report' or 'Full Analysis' workflow")
        print("   3. Enter a query like 'breast cancer RNA-seq'")
        print("   4. AI-powered reports will be generated automatically!")
    else:
        print("\n⚠️  OpenAI client test failed. Check the error messages above.")
    
    print("\n" + "🧬 " * 20 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
