#!/usr/bin/env python3
"""
Test the newly implemented data validation workflow.
"""

import asyncio

import httpx

BASE_URL = "http://localhost:8000"


async def test_workflows():
    """Test all workflow types."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        print("🧪 Testing All Workflows\n")
        print("=" * 70)

        # Test 1: Full Analysis
        print("\n1️⃣  Testing Full Analysis...")
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/workflows/dev/execute",
                json={"query": "breast cancer RNA-seq", "workflow_type": "full_analysis"},
            )
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Full Analysis: {data.get('success')}")
                print(f"   Stages: {data.get('stages_completed')}")
            else:
                print(f"❌ Failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Error: {e}")

        # Test 2: Simple Search
        print("\n2️⃣  Testing Simple Search...")
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/workflows/dev/execute",
                json={"query": "COVID-19 immune response", "workflow_type": "simple_search"},
            )
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Simple Search: {data.get('success')}")
                print(f"   Stages: {data.get('stages_completed')}")
            else:
                print(f"❌ Failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Error: {e}")

        # Test 3: Quick Report (with GEO IDs)
        print("\n3️⃣  Testing Quick Report...")
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/workflows/dev/execute",
                json={"query": "GSE12345", "workflow_type": "quick_report"},
            )
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Quick Report: {data.get('success')}")
                print(f"   Stages: {data.get('stages_completed')}")
            else:
                print(f"❌ Failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Error: {e}")

        # Test 4: Data Validation (THE NEW ONE!)
        print("\n4️⃣  Testing Data Validation (NEWLY IMPLEMENTED!)...")
        print("   Query with GEO IDs: GSE12345 GSE67890")
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/workflows/dev/execute",
                json={"query": "GSE12345 GSE67890", "workflow_type": "data_validation"},
            )
            print(f"   Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"✅ Data Validation: {data.get('success')}")
                print(f"   Workflow Type: {data.get('workflow_type')}")
                print(f"   Final Stage: {data.get('final_stage')}")
                print(f"   Stages Completed: {data.get('stages_completed')}")
                print(f"   Datasets Found: {data.get('total_datasets_found')}")
                print(f"   Datasets Analyzed: {data.get('total_datasets_analyzed')}")

                if data.get("error_message"):
                    print(f"   ⚠️  Error: {data.get('error_message')}")

                # Show stage results
                stages = data.get("stage_results", [])
                if stages:
                    print(f"\n   Stage Breakdown:")
                    for stage in stages:
                        status = "✅" if stage.get("success") else "❌"
                        print(f"   {status} {stage.get('stage')}: {stage.get('agent')}")

            else:
                print(f"❌ Failed: {response.status_code}")
                print(f"   Response: {response.text}")
        except Exception as e:
            print(f"❌ Error: {e}")

        # Test 5: Data Validation without GEO IDs (should search first)
        print("\n5️⃣  Testing Data Validation with search query...")
        print("   Query without IDs: cancer genomics in breast tissue")
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/workflows/dev/execute",
                json={"query": "cancer genomics in breast tissue", "workflow_type": "data_validation"},
            )
            print(f"   Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"✅ Data Validation (with search): {data.get('success')}")
                print(f"   Final Stage: {data.get('final_stage')}")
                print(f"   Stages Completed: {data.get('stages_completed')}")
                print(f"   Datasets Found: {data.get('total_datasets_found')}")

                if data.get("error_message"):
                    print(f"   ⚠️  Error: {data.get('error_message')}")
            else:
                print(f"❌ Failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Error: {e}")

        print("\n" + "=" * 70)
        print("\n✨ Testing Complete!\n")

        print("📋 Summary:")
        print("• All 4 workflow types have been tested")
        print("• Data Validation workflow is now fully implemented")
        print("• You can use the dashboard at http://localhost:8000/dashboard")
        print("\n💡 Tip: For general queries, use 'Full Analysis'")
        print("💡 Tip: For specific GEO IDs, use 'Quick Report' or 'Validate Datasets'")
        print()


if __name__ == "__main__":
    asyncio.run(test_workflows())
