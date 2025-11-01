#!/bin/bash
# Start OmicsOracle v2 API Server for Testing
# This script starts the server with SQLite database for local testing

echo "=========================================="
echo "OmicsOracle v2 API - Test Server Startup"
echo "=========================================="
echo ""

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Virtual environment not activated!"
    echo "Please activate it first:"
    echo "  source venv/bin/activate"
    echo ""
    exit 1
fi

# Load test environment variables
export $(cat test_environment.env | grep -v '^#' | xargs)

echo "✅ Environment variables loaded from test_environment.env"
echo ""
echo "Configuration:"
echo "  - Database: SQLite (test_omics_oracle.db)"
echo "  - Redis: In-memory fallback (no Redis required)"
echo "  - Rate Limiting: Enabled with in-memory fallback"
echo "  - Environment: development"
echo "  - Host: $OMICS_API_HOST"
echo "  - Port: $OMICS_API_PORT"
echo ""

# Initialize database
echo "🔧 Initializing database..."
python -c "
import asyncio
from omics_oracle_v2.database import init_db

async def init():
    await init_db()
    print('✅ Database initialized successfully')

asyncio.run(init())
"

echo ""
echo "🚀 Starting API server..."
echo "   API docs: http://localhost:8000/docs"
echo "   Dashboard: http://localhost:8000/dashboard"
echo "   Health: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start server
uvicorn omics_oracle_v2.api.main:app \
    --host ${OMICS_API_HOST:-127.0.0.1} \
    --port ${OMICS_API_PORT:-8000} \
    --reload \
    --log-level info
