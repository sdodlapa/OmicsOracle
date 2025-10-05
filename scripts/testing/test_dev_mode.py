#!/usr/bin/env python3
"""
Quick test of dev mode endpoints
"""

import asyncio
import httpx

BASE_URL = "http://localhost:8000"


async def test_dev_endpoints():
    """Test the development endpoints."""
    async with httpx.AsyncClient() as client:
        print("🧪 Testing OmicsOracle Dev Mode\n")
        print("=" * 60)
        
        # Test 1: Dev status
        print("\n1️⃣  Testing dev status endpoint...")
        try:
            response = await client.get(f"{BASE_URL}/api/v1/workflows/dev/status")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Status: {response.status_code}")
                print(f"   Mode: {data.get('mode')}")
                print(f"   Auth: {data.get('authentication')}")
                print(f"   User: {data.get('mock_user', {}).get('email')}")
                print(f"   Tier: {data.get('mock_user', {}).get('tier')}")
            else:
                print(f"❌ Failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test 2: List workflows
        print("\n2️⃣  Testing workflow listing...")
        try:
            response = await client.get(f"{BASE_URL}/api/v1/workflows/dev/")
            if response.status_code == 200:
                workflows = response.json()
                print(f"✅ Status: {response.status_code}")
                print(f"   Found {len(workflows)} workflows:")
                for wf in workflows:
                    print(f"   - {wf['type']}: {wf['name']}")
            else:
                print(f"❌ Failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test 3: Execute simple workflow
        print("\n3️⃣  Testing workflow execution...")
        print("   Query: 'DNA methylation and HiC joint profiling'")
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/workflows/dev/execute",
                json={
                    "workflow_type": "simple_search",
                    "query": "DNA methylation and HiC joint profiling"
                },
                timeout=60.0
            )
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Status: {response.status_code}")
                print(f"   Success: {data.get('success')}")
                print(f"   Workflow Type: {data.get('workflow_type')}")
                print(f"   Final Stage: {data.get('final_stage')}")
                print(f"   Execution time: {data.get('execution_time_ms', 0)/1000:.2f}s")
                
                # Show results summary
                print(f"\n   📊 Results Summary:")
                print(f"   - Datasets found: {data.get('total_datasets_found', 0)}")
                print(f"   - Datasets analyzed: {data.get('total_datasets_analyzed', 0)}")
                print(f"   - High quality datasets: {data.get('high_quality_datasets', 0)}")
                
                # Show stages
                stages = data.get('stage_results', [])
                if stages:
                    print(f"\n   🔄 Workflow Stages ({data.get('stages_completed', 0)} completed):")
                    for stage in stages:
                        status_emoji = "✅" if stage.get('success') else "❌"
                        print(f"   {status_emoji} {stage.get('stage')}: {stage.get('agent')} ({stage.get('execution_time_ms', 0)/1000:.2f}s)")
                
                # Show report info
                if data.get('report_title'):
                    print(f"\n   � Report: {data.get('report_title')}")
                if data.get('final_report'):
                    report_preview = data['final_report'][:200].replace('\n', ' ')
                    print(f"   Preview: {report_preview}...")
                
            else:
                print(f"❌ Failed: {response.status_code}")
                print(f"   Response: {response.text}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("\n" + "=" * 60)
        print("✨ Testing complete!\n")
        print("Next steps:")
        print("1. Open http://localhost:8000/dashboard in your browser")
        print("2. Enter your query in the search box")
        print("3. Click 'Execute Workflow'")
        print("4. Watch the magic happen! 🎉\n")


if __name__ == "__main__":
    asyncio.run(test_dev_endpoints())
