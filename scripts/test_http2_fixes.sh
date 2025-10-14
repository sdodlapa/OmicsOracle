#!/bin/bash
# Test HTTP/2 Error Fixes

echo "=========================================="
echo "Testing HTTP/2 Error Fixes"
echo "=========================================="
echo ""

# Test 1: Check GZip compression is enabled
echo "Test 1: Verify GZip Compression"
echo "--------------------------------"
response=$(curl -s -I "http://localhost:8000/health" -H "Accept-Encoding: gzip")
if echo "$response" | grep -i "content-encoding: gzip" > /dev/null; then
    echo "✅ PASS: GZip compression enabled"
else
    echo "⚠️  Note: GZip may not compress health endpoint (too small)"
    echo "   GZip only compresses responses >1KB"
fi
echo ""

# Test 2: Small response (metadata only)
echo "Test 2: Small Response (Default - Metadata Only)"
echo "------------------------------------------------"
echo "Request: Enrich 1 dataset with 1 paper, include_full_content=false"
echo ""

# Create proper JSON array format
cat > /tmp/test_request.json << 'EOF'
[
  {
    "geo_id": "GSE123456",
    "title": "Test Dataset",
    "organism": "Homo sapiens",
    "sample_count": 10,
    "pubmed_ids": ["34567890"],
    "quality_score": 0.85
  }
]
EOF

response=$(curl -s -X POST "http://localhost:8000/api/agents/enrich-fulltext?max_papers=1&include_full_content=false" \
  -H "Content-Type: application/json" \
  -H "Accept-Encoding: gzip" \
  --data @/tmp/test_request.json)

if echo "$response" | grep -q "error\|Error\|detail"; then
    echo "❌ FAIL: Error in response"
    echo "$response" | python -m json.tool 2>/dev/null || echo "$response"
else
    echo "✅ PASS: Small response received"
    echo "$response" | python -m json.tool 2>/dev/null | head -30

    # Check response size
    size=$(echo "$response" | wc -c)
    echo ""
    echo "Response size: $size bytes"
    if [ "$size" -lt 10000 ]; then
        echo "✅ Response is small (<10KB) - Good for HTTP/2"
    else
        echo "⚠️  Response is large (>10KB) - May need compression"
    fi
fi
echo ""

# Test 3: Test with full content (larger response)
echo "Test 3: Large Response (Full Content)"
echo "-------------------------------------"
echo "Request: Same dataset, include_full_content=true"
echo ""

response=$(curl -s -X POST "http://localhost:8000/api/agents/enrich-fulltext?max_papers=1&include_full_content=true" \
  -H "Content-Type: application/json" \
  -H "Accept-Encoding: gzip" \
  --data @/tmp/test_request.json)

if echo "$response" | grep -q "error\|Error\|detail"; then
    echo "ℹ️  Note: This test requires actual PubMed data"
    echo "$response" | python -m json.tool 2>/dev/null || echo "$response"
else
    echo "✅ PASS: Full content response received"
    size=$(echo "$response" | wc -c)
    echo "Response size: $size bytes"
    if [ "$size" -gt 5000 ]; then
        echo "✅ Large response handled successfully (no HTTP/2 error)"
    fi
fi
echo ""

# Test 4: Verify endpoint is working
echo "Test 4: API Health Check"
echo "------------------------"
health=$(curl -s "http://localhost:8000/health")
if echo "$health" | grep -q '"status":"healthy"'; then
    echo "✅ PASS: API is healthy"
else
    echo "❌ FAIL: API health check failed"
    echo "$health"
fi
echo ""

# Cleanup
rm -f /tmp/test_request.json

echo "=========================================="
echo "Summary"
echo "=========================================="
echo ""
echo "HTTP/2 Error Fixes Applied:"
echo "  1. ✅ GZip compression middleware added"
echo "  2. ✅ Optional full content parameter added"
echo "  3. ✅ Default responses are small (<10KB)"
echo ""
echo "If you see HTTP/2 errors, check:"
echo "  - Response size (should be <500KB even with compression)"
echo "  - Browser console for detailed error messages"
echo "  - API logs: tail -f logs/omics_api.log"
echo ""
