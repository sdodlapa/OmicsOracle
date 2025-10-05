#!/bin/bash
# Frontend Testing Script for OmicsOracle

echo "🧬 OmicsOracle Frontend Testing Script"
echo "======================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if server is running
echo "1️⃣  Checking if server is running..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Server is running${NC}"
else
    echo -e "${RED}✗ Server is not running${NC}"
    echo -e "${YELLOW}Starting server...${NC}"
    cd "$(dirname "$0")"
    source venv/bin/activate
    python -m omics_oracle_v2.api.main &
    SERVER_PID=$!
    echo "Server PID: $SERVER_PID"
    sleep 5
fi

echo ""
echo "2️⃣  Testing API endpoints..."

# Test health endpoint
echo -n "   Health check: "
if curl -s http://localhost:8000/health | grep -q "status"; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
fi

# Test dashboard
echo -n "   Dashboard: "
if curl -s http://localhost:8000/dashboard | grep -q "OmicsOracle"; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
fi

# Test docs
echo -n "   API Docs: "
if curl -s http://localhost:8000/docs | grep -q "swagger"; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
fi

echo ""
echo "3️⃣  Testing authentication..."

# Register a test user
echo -n "   Register test user: "
REGISTER_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v2/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test123!@#",
    "username": "testuser",
    "full_name": "Test User"
  }' 2>&1)

if echo "$REGISTER_RESPONSE" | grep -q "email" || echo "$REGISTER_RESPONSE" | grep -q "already"; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${YELLOW}~ (User may already exist)${NC}"
fi

# Login
echo -n "   Login: "
LOGIN_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v2/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test123!@#"
  }')

TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -n "$TOKEN" ]; then
    echo -e "${GREEN}✓${NC}"
    echo "   Token: ${TOKEN:0:20}..."
else
    echo -e "${RED}✗${NC}"
    echo "   Response: $LOGIN_RESPONSE"
fi

echo ""
echo "4️⃣  Testing workflow execution..."

if [ -n "$TOKEN" ]; then
    echo -n "   Execute query agent: "
    QUERY_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v2/agents/query" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "query": "breast cancer gene expression"
      }')
    
    if echo "$QUERY_RESPONSE" | grep -q "query" || echo "$QUERY_RESPONSE" | grep -q "success"; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
        echo "   Response: ${QUERY_RESPONSE:0:100}..."
    fi
else
    echo -e "${YELLOW}   Skipped (no token)${NC}"
fi

echo ""
echo "======================================"
echo "🎉 Testing complete!"
echo ""
echo "📋 Summary:"
echo "   Dashboard URL: http://localhost:8000/dashboard"
echo "   API Docs: http://localhost:8000/docs"
echo "   Health: http://localhost:8000/health"
echo ""

if [ -n "$TOKEN" ]; then
    echo "   Test credentials:"
    echo "   Email: test@example.com"
    echo "   Password: Test123!@#"
    echo "   Token: $TOKEN"
    echo ""
    echo "   You can use this token in the browser console:"
    echo "   localStorage.setItem('access_token', '$TOKEN');"
fi

echo ""
