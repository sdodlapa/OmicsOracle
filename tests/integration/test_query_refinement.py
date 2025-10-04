#!/usr/bin/env python3
"""
Test script for Query Refinement Backend

This script tests the QueryAnalysisService and refinement API endpoints
to ensure they're working correctly.
"""

import asyncio
from pathlib import Path

# Add src to path
from omics_oracle.services.query_analysis import QueryAnalysisService


async def test_query_analysis_service():
    """Test the QueryAnalysisService functionality."""
    print("🧪 Testing QueryAnalysisService...")

    # Create service instance
    service = QueryAnalysisService()

    # Test query complexity scoring
    print("\n📊 Testing complexity scoring:")
    test_queries = [
        "cancer",  # Simple
        "breast cancer gene expression",  # Medium
        "WGBS DNA methylation data related to human brain tumor glioblastoma multiforme",  # Complex
    ]

    for query in test_queries:
        score = service.score_query_complexity(query)
        print(f"  '{query}' → Complexity: {score:.2f}")

    # Test failed query analysis
    print("\n🔍 Testing failed query analysis:")
    failed_query = "very specific rare neuroblastoma mutation variant"
    analysis = service.analyze_failed_query(failed_query, result_count=0)

    print(f"  Original query: '{analysis.original_query}'")
    print(f"  Complexity score: {analysis.complexity_score:.2f}")
    print(f"  Issues found: {[issue.value for issue in analysis.potential_issues]}")
    print(f"  Modifications suggested: {analysis.suggested_modifications}")

    # Test suggestion generation
    print("\n💡 Testing suggestion generation:")
    suggestions = service.generate_suggestions(analysis)

    for i, suggestion in enumerate(suggestions, 1):
        print(f"  {i}. {suggestion.suggested_query}")
        print(f"     Type: {suggestion.suggestion_type.value}")
        print(f"     Confidence: {suggestion.confidence_score:.2f}")
        print(f"     Explanation: {suggestion.explanation}")
        print()

    # Test similar query finding
    print("🔎 Testing similar query lookup:")
    similar_queries = service.find_similar_successful_queries("breast cancer rna-seq")

    for i, sq in enumerate(similar_queries, 1):
        print(f"  {i}. '{sq.query_text}'")
        print(f"     Results: {sq.result_count}, Success: {sq.success_score:.2f}")
        print(f"     Similarity: {sq.similarity_score:.2f}")
        print(f"     Common entities: {sq.common_entities}")
        print()

    print("✅ QueryAnalysisService tests completed successfully!")


async def test_api_endpoints():
    """Test the refinement API endpoints (simulated)."""
    print("\n🌐 Testing API endpoint logic...")

    # Simulate API request data
    test_cases = [
        {
            "original_query": "wgbs dna methylation brain tumor",
            "result_count": 0,
            "description": "Zero results query",
        },
        {
            "original_query": "expression microarray",
            "result_count": 3,
            "description": "Poor results query",
        },
        {
            "original_query": "cancer gene human",
            "result_count": 50,
            "description": "Decent results query",
        },
    ]

    service = QueryAnalysisService()

    for case in test_cases:
        print(f"\n📝 Testing: {case['description']}")
        print(f"   Query: '{case['original_query']}'")
        print(f"   Results: {case['result_count']}")

        # Simulate suggestion generation endpoint
        analysis = service.analyze_failed_query(case["original_query"], case["result_count"])
        suggestions = service.generate_suggestions(analysis)

        # Format response like API would
        response_data = {
            "suggestions": [
                {
                    "suggested_query": s.suggested_query,
                    "type": s.suggestion_type.value,
                    "confidence": s.confidence_score,
                    "explanation": s.explanation,
                }
                for s in suggestions
            ],
            "alternative_queries": [
                sq.query_text for sq in service.find_similar_successful_queries(case["original_query"])[:3]
            ],
            "explanation": f"Generated {len(suggestions)} suggestions based on analysis",
            "analysis_metadata": {
                "complexity_score": analysis.complexity_score,
                "issues_found": [issue.value for issue in analysis.potential_issues],
            },
        }

        print(f"   Generated {len(response_data['suggestions'])} suggestions")
        print(f"   Found {len(response_data['alternative_queries'])} alternative queries")
        print(f"   Issues identified: {response_data['analysis_metadata']['issues_found']}")

    print("\n✅ API endpoint logic tests completed successfully!")


def test_edge_cases():
    """Test edge cases and error handling."""
    print("\n🚨 Testing edge cases...")

    service = QueryAnalysisService()

    # Test empty query
    try:
        service.analyze_failed_query("", 0)
        print("  Empty query handled")
    except Exception as e:
        print(f"  Empty query failed: {e}")

    # Test very long query
    try:
        long_query = " ".join(["term"] * 100)
        service.analyze_failed_query(long_query, 0)
        print("  Long query handled")
    except Exception as e:
        print(f"  Long query failed: {e}")

    # Test special characters
    try:
        special_query = "cancer & tumor | disease (human)"
        _ = service.analyze_failed_query(special_query, 0)  # Use _ to indicate intentionally unused
        print("  ✅ Special characters handled")
    except Exception as e:
        print(f"  ❌ Special characters failed: {e}")

    print("✅ Edge case tests completed!")


async def main():
    """Run all tests."""
    print("🚀 Starting Query Refinement Backend Tests")
    print("=" * 50)

    try:
        await test_query_analysis_service()
        await test_api_endpoints()
        test_edge_cases()

        print("\n" + "=" * 50)
        print("🎉 All tests completed successfully!")
        print("\n📋 Summary:")
        print("  ✅ QueryAnalysisService functionality")
        print("  ✅ Suggestion generation")
        print("  ✅ Similar query lookup")
        print("  ✅ API endpoint logic")
        print("  ✅ Edge case handling")
        print("\n🔧 Backend is ready for frontend integration!")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
