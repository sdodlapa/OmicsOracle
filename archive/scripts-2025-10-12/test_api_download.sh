#!/bin/bash
# Test the actual API endpoint that the frontend uses

echo "Testing /api/agents/enrich-fulltext endpoint with PMID 39997216"
echo "================================================================"

curl -X POST http://localhost:8000/api/agents/enrich-fulltext?max_papers=1 \
  -H "Content-Type: application/json" \
  -d '[{
    "geo_id": "GSE_TEST",
    "title": "Test Dataset",
    "summary": "Test",
    "organism": "Homo sapiens",
    "pubmed_ids": ["39997216"],
    "relevance_score": 1.0,
    "samples_count": 1,
    "platform": "Test",
    "submission_date": "2025-01-01"
  }]' 2>&1 | python -m json.tool

echo ""
echo "================================================================"
echo "Check the response above:"
echo "- fulltext_status should be 'success' or 'partial'"
echo "- fulltext_count should be > 0"
echo "- fulltext array should contain the paper data"
echo "================================================================"
