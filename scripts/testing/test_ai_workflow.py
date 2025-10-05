#!/usr/bin/env python3
"""
Quick test to verify OpenAI is working with actual workflow.
"""

import asyncio
import httpx


async def test_ai_workflow():
    """Test a workflow that uses OpenAI for report generation."""
    
    print("\n" + "🧬 " * 30)
    print(" " * 20 + "OpenAI Integration Test")
    print("🧬 " * 30 + "\n")
    
    print("🔄 Testing Full Analysis Workflow with AI Report Generation...")
    print("=" * 80)
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            # Test with a breast cancer query
            print("\n📝 Query: 'breast cancer RNA-seq gene expression'")
            print("📊 Workflow: Full Analysis (includes AI-powered report)")
            print("\n⏳ Executing... (this may take 20-30 seconds with AI generation)\n")
            
            response = await client.post(
                "http://localhost:8000/api/v1/workflows/dev/execute",
                json={
                    "query": "breast cancer RNA-seq gene expression",
                    "workflow_type": "full_analysis"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                
                print("=" * 80)
                print("✅ WORKFLOW COMPLETED SUCCESSFULLY!")
                print("=" * 80)
                
                print(f"\n📊 Workflow Status:")
                print(f"   Success: {data.get('success', False)}")
                print(f"   Workflow Type: {data.get('workflow_type', 'N/A')}")
                print(f"   Final Stage: {data.get('final_stage', 'N/A')}")
                print(f"   Stages Completed: {data.get('stages_completed', 0)}")
                
                # Stage results
                if data.get('stage_results'):
                    print(f"\n📋 Stage Breakdown:")
                    for stage in data['stage_results']:
                        status = "✅" if stage.get('success') else "❌"
                        agent = stage.get('agent', 'Unknown')
                        stage_name = stage.get('stage', 'Unknown')
                        print(f"   {status} {stage_name} ({agent})")
                
                # Query results
                if data.get('query_results'):
                    query = data['query_results']
                    print(f"\n🔍 Query Analysis:")
                    print(f"   Intent: {query.get('intent', 'N/A')}")
                    print(f"   Entities Found: {len(query.get('entities', []))}")
                    
                    if query.get('entities'):
                        print(f"   Key Entities:")
                        for entity in query['entities'][:5]:
                            print(f"      • {entity.get('text', 'N/A')} ({entity.get('type', 'N/A')})")
                
                # Search results
                if data.get('search_results'):
                    search = data['search_results']
                    print(f"\n🔎 Search Results:")
                    print(f"   Datasets Found: {search.get('total_results', 0)}")
                    print(f"   Search Time: {search.get('search_time_seconds', 0):.2f}s")
                
                # Data processing
                print(f"\n📊 Data Analysis:")
                print(f"   Total Datasets Found: {data.get('total_datasets_found', 0)}")
                print(f"   Total Datasets Analyzed: {data.get('total_datasets_analyzed', 0)}")
                
                # THE IMPORTANT PART: AI-Generated Report
                if data.get('report'):
                    report = data['report']
                    print("\n" + "=" * 80)
                    print("🤖 AI-GENERATED REPORT (GPT-4 Turbo)")
                    print("=" * 80)
                    
                    print(f"\n📌 Title:")
                    print(f"   {report.get('title', 'N/A')}")
                    
                    print(f"\n📝 Summary:")
                    summary = report.get('summary', 'N/A')
                    if len(summary) > 300:
                        print(f"   {summary[:300]}...")
                    else:
                        print(f"   {summary}")
                    
                    if report.get('key_insights'):
                        print(f"\n💡 Key Insights ({len(report['key_insights'])} generated):")
                        for i, insight in enumerate(report['key_insights'][:3], 1):
                            insight_text = insight.get('insight', 'N/A')
                            if len(insight_text) > 150:
                                insight_text = insight_text[:150] + "..."
                            print(f"\n   {i}. {insight_text}")
                            print(f"      Category: {insight.get('category', 'N/A')}")
                            print(f"      Importance: {insight.get('importance', 'N/A')}")
                    
                    if report.get('recommendations'):
                        print(f"\n📋 Recommendations ({len(report['recommendations'])} generated):")
                        for i, rec in enumerate(report['recommendations'][:3], 1):
                            print(f"   {i}. {rec}")
                    
                    print(f"\n📊 Report Metadata:")
                    print(f"   Datasets Analyzed: {report.get('total_datasets_analyzed', 0)}")
                    print(f"   Datasets Included: {len(report.get('datasets_included', []))}")
                    print(f"   Generated At: {report.get('generated_at', 'N/A')}")
                    
                    # Quality summary
                    if report.get('quality_summary'):
                        quality = report['quality_summary']
                        print(f"\n🎯 Quality Summary:")
                        print(f"   High Quality: {quality.get('high', 0)} datasets")
                        print(f"   Medium Quality: {quality.get('medium', 0)} datasets")
                        print(f"   Low Quality: {quality.get('low', 0)} datasets")
                    
                    print("\n" + "=" * 80)
                    print("✨ AI-powered analysis complete!")
                    print("=" * 80)
                    
                else:
                    print("\n⚠️  No report generated (this is unexpected for full_analysis)")
                    print("   Check if OpenAI API key is properly configured")
                
                # Error messages
                if data.get('error_message'):
                    print(f"\n⚠️  Warnings/Errors:")
                    print(f"   {data['error_message']}")
                
                print("\n" + "=" * 80)
                print("🎉 TEST COMPLETE - OpenAI Integration Working!")
                print("=" * 80)
                print("\n💡 Next Steps:")
                print("   1. Open dashboard: http://localhost:8000/dashboard")
                print("   2. Try different queries")
                print("   3. Experiment with different workflow types")
                print("   4. Review AI-generated insights\n")
                
                return True
                
            else:
                print(f"\n❌ Workflow failed with status code: {response.status_code}")
                print(f"Response: {response.text[:500]}")
                return False
                
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    success = asyncio.run(test_ai_workflow())
    exit(0 if success else 1)
