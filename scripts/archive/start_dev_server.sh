#!/bin/bash
# OmicsOracle Development Server Startup Script
# This script starts the API server with SQLite database (no PostgreSQL needed)

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧬 Starting OmicsOracle Development Server${NC}"
echo ""

# Navigate to project root
cd "$(dirname "$0")"

# Activate virtual environment
if [ -d "venv" ]; then
    echo -e "${GREEN}✓ Activating virtual environment${NC}"
    source venv/bin/activate
else
    echo -e "${YELLOW}⚠ Virtual environment not found. Creating one...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    pip install -e .
fi

# Export SQLite database URL (overrides .env default)
export OMICS_DB_URL="sqlite+aiosqlite:///./omics_oracle.db"

# Optional: Disable Redis warnings if not needed
export OMICS_RATE_LIMIT_FALLBACK_TO_MEMORY=true

echo -e "${GREEN}✓ Environment configured${NC}"
echo -e "${BLUE}  Database: SQLite (omics_oracle.db)${NC}"
echo -e "${BLUE}  Rate Limiting: In-memory cache${NC}"
echo ""

# Start the server
echo -e "${GREEN}🚀 Starting API server on http://localhost:8000${NC}"
echo ""
echo -e "${YELLOW}Access points:${NC}"
echo -e "  📊 Dashboard:  http://localhost:8000/dashboard"
echo -e "  📖 API Docs:   http://localhost:8000/docs"
echo -e "  ❤️  Health:     http://localhost:8000/health"
echo ""
echo -e "${YELLOW}Press CTRL+C to stop the server${NC}"
echo ""

# Run the server
python -m omics_oracle_v2.api.main
