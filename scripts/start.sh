#!/bin/bash
# Unified OmicsOracle Startup Script

set -e

# Default values
MODE="dev"
SSL_BYPASS=false
DB_TYPE="postgres"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --mode)
            MODE="$2"
            shift 2
            ;;
        --ssl-bypass)
            SSL_BYPASS=true
            shift
            ;;
        --db)
            DB_TYPE="$2"
            shift 2
            ;;
        --help)
            echo "Usage: ./scripts/start.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --mode MODE        Set mode (dev|prod) [default: dev]"
            echo "  --ssl-bypass       Enable SSL bypass"
            echo "  --db DB_TYPE       Set database (postgres|sqlite) [default: postgres]"
            echo "  --help             Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Virtual environment not found. Please create it first:"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# Set environment variables based on options
export MODE="$MODE"

if [ "$SSL_BYPASS" = true ]; then
    export SSL_VERIFY=false
    echo "SSL verification disabled"
fi

if [ "$DB_TYPE" = "sqlite" ]; then
    export DATABASE_URL="sqlite:///./omics_oracle.db"
    echo "Using SQLite database"
fi

# Start server
echo "Starting OmicsOracle in $MODE mode..."

if [ "$MODE" = "dev" ]; then
    uvicorn omics_oracle_v2.api.main:app --reload --host 0.0.0.0 --port 8000
else
    uvicorn omics_oracle_v2.api.main:app --host 0.0.0.0 --port 8000
fi
