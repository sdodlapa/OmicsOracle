"""
Test AnalysisClient against live backend
"""
import asyncio

from omics_oracle_v2.integration import AnalysisClient, SearchClient


async def test_analysis_client():
    """Test all AnalysisClient methods"""
    print("\n" + "=" * 80)
    print("TESTING ANALYSIS CLIENT")
    print("=" * 80)

    # First, get some search results to use as context
    print("\n[SETUP] Getting search results for context...")
    async with SearchClient() as search:
        search_results = await search.search(query="CRISPR", max_results=5)
        print(f"  [OK] Got {len(search_results.results)} results for testing")

    async with AnalysisClient() as client:
        # Test 1: LLM Analysis
        print("\n[TEST 1] LLM Analysis - analyze_with_llm()")
        try:
            analysis = await client.analyze_with_llm(
                query="CRISPR gene editing", results=search_results.results[:3]
            )
            print("  [OK] Analysis completed!")
            print(f"  Response type: {type(analysis)}")
            print(f"  Response keys: {list(analysis.keys())[:5] if isinstance(analysis, dict) else 'N/A'}")
        except Exception as e:
            print(f"  [ERROR] {e}")
            import traceback

            traceback.print_exc()

        # Test 2: Q&A System
        print("\n[TEST 2] Q&A System - ask_question()")
        try:
            answer = await client.ask_question(
                question="What are the main applications of CRISPR?", context=search_results.results[:3]
            )
            print("  [OK] Q&A completed!")
            print(f"  Response type: {type(answer)}")
            print(f"  Response preview: {str(answer)[:200]}...")
        except Exception as e:
            print(f"  [ERROR] {e}")
            import traceback

            traceback.print_exc()

        # Test 3: Generate Report
        print("\n[TEST 3] Report Generation - generate_report()")
        try:
            report = await client.generate_report(query="CRISPR", results=search_results.results[:3])
            print("  [OK] Report generated!")
            print(f"  Response type: {type(report)}")
        except Exception as e:
            print(f"  [ERROR] {e}")
            import traceback

            traceback.print_exc()

        # Test 4: Trend Analysis
        print("\n[TEST 4] Trend Analysis - get_trends()")
        try:
            trends = await client.get_trends(results=search_results.results[:5])
            print("  [OK] Trends retrieved!")
            print(f"  Response type: {type(trends)}")
        except Exception as e:
            print(f"  [ERROR] {e}")
            import traceback

            traceback.print_exc()

        # Test 5: Citation Network
        print("\n[TEST 5] Citation Network - get_network()")
        try:
            network = await client.get_network(results=search_results.results[:3])
            print("  [OK] Citation network retrieved!")
            print(f"  Response type: {type(network)}")
        except Exception as e:
            print(f"  [ERROR] {e}")
            import traceback

            traceback.print_exc()

        # Test 6: Citation Analysis
        print("\n[TEST 6] Citation Analysis - get_citation_analysis()")
        try:
            if search_results.results:
                pub_id = search_results.results[0].id
                metrics = await client.get_citation_analysis(pub_id=pub_id)
                print("  [OK] Citation metrics retrieved!")
                print(f"  Response type: {type(metrics)}")
        except Exception as e:
            print(f"  [ERROR] {e}")
            import traceback

            traceback.print_exc()

        # Test 7: Biomarker Analysis
        print("\n[TEST 7] Biomarker Analysis - get_biomarker_analysis()")
        try:
            biomarkers = await client.get_biomarker_analysis(results=search_results.results[:3])
            print("  [OK] Biomarkers extracted!")
            print(f"  Response type: {type(biomarkers)}")
        except Exception as e:
            print(f"  [ERROR] {e}")
            import traceback

            traceback.print_exc()

    print("\n" + "=" * 80)
    print("ANALYSIS CLIENT TESTING COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_analysis_client())
