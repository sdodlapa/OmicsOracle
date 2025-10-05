#!/bin/bash
# Fixed startup script for OmicsOracle with SQLite

cd "$(dirname "$0")"

# Set SQLite database URL
export OMICS_DB_URL="sqlite+aiosqlite:///./omics_oracle.db"

# Activate virtual environment
source venv/bin/activate

# Start server
echo "🧬 Starting OmicsOracle with SQLite database..."
echo "   Database: omics_oracle.db"
echo "   URL: http://localhost:8000"
echo "   Dashboard: http://localhost:8000/dashboard"
echo ""

python -m omics_oracle_v2.api.main
