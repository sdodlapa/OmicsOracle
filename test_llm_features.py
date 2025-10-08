#!/usr/bin/env python3
"""
Phase 4 Day 2: LLM Features Validation

Tests all LLM-powered analysis features with authentication:
1. analyze_with_llm() - Generate insights from papers
2. ask_question() - Q&A system
3. generate_report() - Report generation
4. compare_papers() - Paper comparison

This will reveal actual response structures and help create adapters.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import List

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from omics_oracle_v2.integration import AnalysisClient, SearchClient  # noqa: E402
from omics_oracle_v2.integration.auth import create_test_user  # noqa: E402
from omics_oracle_v2.integration.models import Publication  # noqa: E402


async def get_test_publications(
    query: str = "CRISPR gene editing", max_results: int = 5
) -> List[Publication]:
    """Get real publications for testing"""
    print(f"\n[SETUP] Fetching test publications...")
    print(f"   Query: '{query}'")
    print(f"   Max results: {max_results}")

    async with SearchClient() as search:
        response = await search.search(query, max_results=max_results)
        publications = response.results

    print(f"   Found: {len(publications)} publications")

    if publications:
        print(f"\n   Sample publication:")
        print(f"   - Title: {publications[0].title[:80]}...")
        print(f"   - Authors: {len(publications[0].authors)} authors")
        print(f"   - Year: {publications[0].year}")
        print(f"   - ID: {publications[0].id}")

    return publications


async def test_analyze_with_llm(token: str, query: str, publications: List[Publication]):
    """
    Test LLM analysis feature.

    This is THE KEY FEATURE that was missing from the dashboard!
    Backend endpoint: POST /api/v1/agents/analyze
    """
    print("\n" + "=" * 80)
    print("TEST 1: analyze_with_llm() - LLM Analysis")
    print("=" * 80)

    print(f"\nQuery: '{query}'")
    print(f"Publications to analyze: {len(publications)}")

    async with AnalysisClient(api_key=token) as client:
        try:
            print("\n[REQUEST] Calling analyze_with_llm()...")
            print(f"   - query: {query}")
            print(f"   - results: {len(publications)} publications")
            print(f"   - analysis_type: overview")

            # Call the LLM analysis endpoint
            result = await client.analyze_with_llm(
                query=query, results=publications[:5], analysis_type="overview"  # Use first 5 papers
            )

            print("\n[RESPONSE] Success!")
            print(f"\n   Response type: {type(result)}")
            print(f"   Response attributes: {dir(result)}")

            # Display the analysis
            print("\n" + "-" * 80)
            print("ANALYSIS RESULTS:")
            print("-" * 80)

            if hasattr(result, "overview"):
                print(f"\nOVERVIEW:")
                print(result.overview[:500] + "..." if len(result.overview) > 500 else result.overview)

            if hasattr(result, "key_findings"):
                print(f"\nKEY FINDINGS ({len(result.key_findings)}):")
                for i, finding in enumerate(result.key_findings[:5], 1):
                    print(f"   {i}. {finding}")

            if hasattr(result, "research_gaps"):
                print(f"\nRESEARCH GAPS ({len(result.research_gaps)}):")
                for i, gap in enumerate(result.research_gaps[:3], 1):
                    print(f"   {i}. {gap}")

            if hasattr(result, "recommendations"):
                print(f"\nRECOMMENDATIONS ({len(result.recommendations)}):")
                for i, rec in enumerate(result.recommendations[:3], 1):
                    print(f"   {i}. {rec}")

            if hasattr(result, "confidence"):
                print(f"\nCONFIDENCE: {result.confidence:.2%}")

            if hasattr(result, "model_used"):
                print(f"MODEL USED: {result.model_used}")

            # Save raw response for inspection
            print("\n[DEBUG] Saving raw response...")
            with open("test_llm_analysis_response.json", "w") as f:
                # Try to convert to dict
                if hasattr(result, "model_dump"):
                    json.dump(result.model_dump(), f, indent=2)
                elif hasattr(result, "dict"):
                    json.dump(result.dict(), f, indent=2)
                else:
                    json.dump(str(result), f, indent=2)
            print("   Saved to: test_llm_analysis_response.json")

            return True, result

        except Exception as e:
            print(f"\n[ERROR] analyze_with_llm() failed!")
            print(f"   Error type: {type(e).__name__}")
            print(f"   Error message: {e}")

            # Print full traceback for debugging
            import traceback

            print("\n[TRACEBACK]")
            traceback.print_exc()

            return False, str(e)


async def test_ask_question(token: str, publications: List[Publication]):
    """
    Test Q&A feature.

    Backend endpoint: POST /api/v1/agents/ask
    """
    print("\n" + "=" * 80)
    print("TEST 2: ask_question() - Q&A System")
    print("=" * 80)

    questions = [
        "What are the main applications of CRISPR?",
        "Which studies show the highest efficacy?",
        "What are the limitations of current approaches?",
    ]

    async with AnalysisClient(api_key=token) as client:
        results = []

        for i, question in enumerate(questions, 1):
            print(f"\n[QUESTION {i}] {question}")

            try:
                answer = await client.ask_question(question=question, context=publications[:5])

                print(f"\n[ANSWER]")
                if hasattr(answer, "answer"):
                    print(f"   {answer.answer[:300]}...")

                if hasattr(answer, "confidence"):
                    print(f"\n   Confidence: {answer.confidence:.2%}")

                if hasattr(answer, "sources"):
                    print(f"   Sources: {answer.sources}")

                results.append((True, answer))

            except Exception as e:
                print(f"\n[ERROR] {e}")
                results.append((False, str(e)))

        # Save results
        print("\n[DEBUG] Saving Q&A responses...")
        with open("test_qa_responses.json", "w") as f:
            json.dump([str(r[1]) for r in results], f, indent=2)
        print("   Saved to: test_qa_responses.json")

        success_count = sum(1 for r in results if r[0])
        print(f"\n[SUMMARY] {success_count}/{len(questions)} questions answered successfully")

        return results


async def test_generate_report(token: str, query: str, publications: List[Publication]):
    """
    Test report generation.

    Backend endpoint: POST /api/v1/agents/report
    """
    print("\n" + "=" * 80)
    print("TEST 3: generate_report() - Report Generation")
    print("=" * 80)

    print(f"\nGenerating report for: '{query}'")
    print(f"Using {len(publications)} publications")

    async with AnalysisClient(api_key=token) as client:
        try:
            report = await client.generate_report(query=query, results=publications[:10], format="markdown")

            print("\n[RESPONSE] Report generated successfully!")
            print(f"\n   Report length: {len(report)} characters")
            print(f"   Report type: {type(report)}")

            # Show first part of report
            print("\n" + "-" * 80)
            print("REPORT PREVIEW:")
            print("-" * 80)
            print(report[:1000] + "..." if len(report) > 1000 else report)

            # Save full report
            print("\n[DEBUG] Saving full report...")
            with open("test_generated_report.md", "w") as f:
                f.write(report)
            print("   Saved to: test_generated_report.md")

            return True, report

        except Exception as e:
            print(f"\n[ERROR] generate_report() failed!")
            print(f"   {e}")
            import traceback

            traceback.print_exc()
            return False, str(e)


async def test_compare_papers(token: str, publications: List[Publication]):
    """
    Test paper comparison.

    Backend endpoint: POST /api/v1/agents/compare
    """
    print("\n" + "=" * 80)
    print("TEST 4: compare_papers() - Paper Comparison")
    print("=" * 80)

    if len(publications) < 2:
        print("\n[SKIP] Not enough publications for comparison")
        return False, "Need at least 2 publications"

    # Select 2-3 papers to compare
    paper_ids = [p.id for p in publications[:3] if p.id]

    if not paper_ids:
        print("\n[SKIP] No publication IDs available")
        return False, "No IDs"

    print(f"\nComparing {len(paper_ids)} papers:")
    for i, pub in enumerate(publications[: len(paper_ids)], 1):
        print(f"   {i}. {pub.title[:80]}...")

    async with AnalysisClient(api_key=token) as client:
        try:
            comparison = await client.compare_papers(
                paper_ids=paper_ids, aspects=["methodology", "results", "impact"]
            )

            print("\n[RESPONSE] Comparison successful!")
            print(f"\n   Response type: {type(comparison)}")

            # Display comparison
            if hasattr(comparison, "summary"):
                print(f"\nSUMMARY:")
                print(comparison.summary[:500] + "...")

            if hasattr(comparison, "similarities"):
                print(f"\nSIMILARITIES ({len(comparison.similarities)}):")
                for sim in comparison.similarities[:3]:
                    print(f"   - {sim}")

            if hasattr(comparison, "differences"):
                print(f"\nDIFFERENCES ({len(comparison.differences)}):")
                for diff in comparison.differences[:3]:
                    print(f"   - {diff}")

            # Save comparison
            print("\n[DEBUG] Saving comparison...")
            with open("test_comparison_response.json", "w") as f:
                if hasattr(comparison, "model_dump"):
                    json.dump(comparison.model_dump(), f, indent=2)
                else:
                    json.dump(str(comparison), f, indent=2)
            print("   Saved to: test_comparison_response.json")

            return True, comparison

        except Exception as e:
            print(f"\n[ERROR] compare_papers() failed!")
            print(f"   {e}")
            import traceback

            traceback.print_exc()
            return False, str(e)


async def main():
    """Run all LLM feature tests"""
    print("\n" + "=" * 80)
    print("  PHASE 4 DAY 2: LLM FEATURES VALIDATION")
    print("  Testing all LLM-powered analysis features")
    print("=" * 80)

    # Step 1: Authenticate
    print("\n[STEP 1] Authenticating...")
    try:
        token = await create_test_user()
        print("   Authenticated successfully!")
        print(f"   Token: {token[:30]}...")
    except Exception as e:
        print(f"   Authentication failed: {e}")
        return

    # Step 2: Get test publications
    print("\n[STEP 2] Getting test publications...")
    query = "CRISPR gene editing mechanisms and applications"
    publications = await get_test_publications(query, max_results=10)

    if not publications:
        print("   No publications found - cannot proceed")
        return

    # Step 3: Test all LLM features
    results = {}

    # Test 1: LLM Analysis
    print("\n[STEP 3] Testing LLM features...")
    results["analyze"] = await test_analyze_with_llm(token, query, publications)

    # Test 2: Q&A
    results["qa"] = await test_ask_question(token, publications)

    # Test 3: Report Generation
    results["report"] = await test_generate_report(token, query, publications)

    # Test 4: Paper Comparison
    results["compare"] = await test_compare_papers(token, publications)

    # Summary
    print("\n" + "=" * 80)
    print("  TEST SUMMARY")
    print("=" * 80)

    print(f"\n1. analyze_with_llm(): {'PASS' if results['analyze'][0] else 'FAIL'}")

    qa_success = sum(1 for r in results["qa"] if r[0])
    print(f"2. ask_question(): {qa_success}/3 questions answered")

    print(f"3. generate_report(): {'PASS' if results['report'][0] else 'FAIL'}")
    print(f"4. compare_papers(): {'PASS' if results['compare'][0] else 'FAIL'}")

    # Calculate overall success
    total_tests = 4
    passed_tests = sum(
        [
            1 if results["analyze"][0] else 0,
            1 if qa_success >= 2 else 0,  # At least 2/3 questions
            1 if results["report"][0] else 0,
            1 if results["compare"][0] else 0,
        ]
    )

    print(f"\nOVERALL: {passed_tests}/{total_tests} tests passed ({passed_tests/total_tests*100:.0f}%)")

    print("\n" + "=" * 80)
    print("  FILES GENERATED:")
    print("=" * 80)
    print("  - test_llm_analysis_response.json (analysis structure)")
    print("  - test_qa_responses.json (Q&A responses)")
    print("  - test_generated_report.md (full report)")
    print("  - test_comparison_response.json (comparison structure)")
    print("\n  Review these files to understand actual response structures")
    print("  and create adapters if needed.")
    print("=" * 80)

    if passed_tests == total_tests:
        print("\n  All LLM features are working! Day 2 complete!")
    elif passed_tests >= 2:
        print("\n  Most features working - review failures and create adapters")
    else:
        print("\n  Multiple failures - check backend endpoints and authentication")


if __name__ == "__main__":
    asyncio.run(main())
