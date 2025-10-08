#!/bin/bash

# OmicsOracle Unified Startup Script
# Starts both FastAPI API server and Streamlit Dashboard

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${PURPLE}================================================${NC}"
echo -e "${PURPLE}                                                ${NC}"
echo -e "${PURPLE}        OmicsOracle Unified Startup             ${NC}"
echo -e "${PURPLE}                                                ${NC}"
echo -e "${PURPLE}================================================${NC}"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}[ERROR] Virtual environment not found!${NC}"
    echo -e "${YELLOW}[INFO] Please create one first: python -m venv venv${NC}"
    exit 1
fi

# Activate virtual environment
echo -e "${CYAN}[SETUP] Activating virtual environment...${NC}"
source venv/bin/activate

# Check for .env file
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}[WARN] .env file not found!${NC}"
    echo -e "${YELLOW}[INFO] Create .env with required API keys (NCBI_EMAIL, NCBI_API_KEY, OPENAI_API_KEY)${NC}"
fi

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}[CLEANUP] Shutting down OmicsOracle...${NC}"

    # Kill API server
    if [ ! -z "$API_PID" ]; then
        echo -e "${CYAN}[CLEANUP] Stopping API server (PID: $API_PID)...${NC}"
        kill $API_PID 2>/dev/null || true
    fi

    # Kill Dashboard
    if [ ! -z "$DASHBOARD_PID" ]; then
        echo -e "${CYAN}[CLEANUP] Stopping dashboard (PID: $DASHBOARD_PID)...${NC}"
        kill $DASHBOARD_PID 2>/dev/null || true
    fi

    # Extra cleanup - kill any remaining processes
    pkill -f "omics_oracle_v2.api.main" 2>/dev/null || true
    pkill -f "run_dashboard.py" 2>/dev/null || true
    pkill -f "streamlit" 2>/dev/null || true

    echo -e "${GREEN}[CLEANUP] Shutdown complete${NC}"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Check if ports are already in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Check API port (8000)
if check_port 8000; then
    echo -e "${YELLOW}[WARN] Port 8000 is already in use${NC}"
    echo -e "${RED}[ERROR] Please stop the existing process on port 8000${NC}"
    lsof -Pi :8000 -sTCP:LISTEN
    exit 1
fi

# Check Dashboard port (8502)
if check_port 8502; then
    echo -e "${YELLOW}[WARN] Port 8502 is already in use${NC}"
    echo -e "${RED}[ERROR] Please stop the existing process on port 8502${NC}"
    lsof -Pi :8502 -sTCP:LISTEN
    exit 1
fi

echo -e "${GREEN}[OK] Ports 8000 and 8502 are available${NC}"
echo ""

# Start API server in background
echo -e "${BLUE}[START] Starting FastAPI API server...${NC}"
export OMICS_DB_URL="sqlite+aiosqlite:///./omics_oracle.db"
export OMICS_RATE_LIMIT_FALLBACK_TO_MEMORY=true

python -m omics_oracle_v2.api.main > /tmp/omics_api.log 2>&1 &
API_PID=$!

# Wait a bit for API to start
sleep 3

# Check if API started successfully
if ! ps -p $API_PID > /dev/null; then
    echo -e "${RED}[ERROR] API server failed to start!${NC}"
    echo -e "${YELLOW}[INFO] Check logs: tail -f /tmp/omics_api.log${NC}"
    exit 1
fi

echo -e "${GREEN}[OK] API server started (PID: $API_PID)${NC}"

# Start Streamlit dashboard in background
echo -e "${BLUE}[START] Starting Streamlit dashboard...${NC}"
python scripts/run_dashboard.py --port 8502 > /tmp/omics_dashboard.log 2>&1 &
DASHBOARD_PID=$!

# Wait a bit for Dashboard to start
sleep 3

# Check if Dashboard started successfully
if ! ps -p $DASHBOARD_PID > /dev/null; then
    echo -e "${RED}[ERROR] Dashboard failed to start!${NC}"
    echo -e "${YELLOW}[INFO] Check logs: tail -f /tmp/omics_dashboard.log${NC}"
    cleanup
    exit 1
fi

echo -e "${GREEN}[OK] Dashboard started (PID: $DASHBOARD_PID)${NC}"
echo ""

# Display access information
echo -e "${PURPLE}================================================${NC}"
echo -e "${PURPLE}                                                ${NC}"
echo -e "${PURPLE}          OmicsOracle is Running!               ${NC}"
echo -e "${PURPLE}                                                ${NC}"
echo -e "${PURPLE}================================================${NC}"
echo ""
echo -e "${CYAN}Access Points:${NC}"
echo -e "  ${GREEN}Dashboard:${NC}      http://localhost:8502"
echo -e "  ${GREEN}API Server:${NC}     http://localhost:8000"
echo -e "  ${GREEN}API Docs:${NC}       http://localhost:8000/docs"
echo -e "  ${GREEN}Health Check:${NC}  http://localhost:8000/health"
echo -e "  ${GREEN}Debug Panel:${NC}    http://localhost:8000/debug/dashboard"
echo ""
echo -e "${CYAN}Process Information:${NC}"
echo -e "  ${BLUE}API PID:${NC}       $API_PID"
echo -e "  ${BLUE}Dashboard PID:${NC} $DASHBOARD_PID"
echo ""
echo -e "${CYAN}Logs:${NC}"
echo -e "  ${BLUE}API:${NC}       tail -f /tmp/omics_api.log"
echo -e "  ${BLUE}Dashboard:${NC} tail -f /tmp/omics_dashboard.log"
echo ""
echo -e "${YELLOW}Press CTRL+C to stop all services${NC}"
echo ""

# Wait for user interrupt
wait
