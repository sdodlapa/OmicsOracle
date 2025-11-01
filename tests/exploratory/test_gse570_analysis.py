#!/usr/bin/env python3
"""Test AI Analysis for GSE570 to debug the failure."""

import asyncio
import json

import httpx


async def test_gse570_analysis():
    """Test AI analysis for GSE570."""

    base_url = "http://localhost:8000"

    # Build dataset with all required fields
    dataset = {
        "geo_id": "GSE570",
        "title": "HeLa CD4+ transfection",
        "organism": "Homo sapiens",
        "sample_count": 6,
        "summary": "Expression profiles of HeLa CD4+ cells transfected with epitope-tagged eTat plasmid, or parental plasmid pCep4.",
        "relevance_score": 0.1,
        "match_reasons": ["Dataset title contains relevant terms"],
        "pubmed_ids": [],  # Will be loaded from database
        "fulltext": [],
    }

    request_body = {
        "datasets": [dataset],
        "query": "HIV latency reactivation",
        "max_datasets": 1,
        "max_papers_per_dataset": 5,
    }

    print("Sending AI Analysis request for GSE570...")
    print(f"Request: {json.dumps(request_body, indent=2)}")

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{base_url}/api/agents/analyze", json=request_body
            )

            print(f"\nStatus: {response.status_code}")

            if response.status_code != 200:
                print(f"Error: {response.text}")
                return None

            result = response.json()
            print(f"Success: {result.get('success')}")
            print(f"Execution time: {result.get('execution_time_ms', 0):.0f} ms")

            # Check for insights
            if result.get("insights"):
                print(f"\nInsights ({len(result['insights'])}):")
                for insight in result["insights"][:3]:
                    print(f"  • {insight}")

            return result

    except Exception as e:
        print(f"Exception: {e}")
        import traceback

        traceback.print_exc()
        return None


if __name__ == "__main__":
    asyncio.run(test_gse570_analysis())
