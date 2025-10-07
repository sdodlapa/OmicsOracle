#!/bin/bash
#
# OmicsOracle - Unified Startup Script (SSL Workaround Version)
# ============================================================
#
# This version includes SSL verification bypass for institutional networks
# that use self-signed certificates (e.g., university/corporate networks).
#
# ⚠️  SECURITY WARNING: Only use this on trusted networks!
#
# Usage:
#   ./start_omics_oracle_ssl_bypass.sh
#
# Services:
#   - API Server: http://localhost:8000
#   - Dashboard: http://localhost:8502
#
# Logs:
#   - API: /tmp/omics_api.log
#   - Dashboard: /tmp/omics_dashboard.log

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
API_PORT=8000
DASHBOARD_PORT=8502
API_LOG="/tmp/omics_api.log"
DASHBOARD_LOG="/tmp/omics_dashboard.log"

# ⚠️ SSL BYPASS (TESTING ONLY)
echo -e "${YELLOW}⚠️  SSL VERIFICATION DISABLED (for institutional networks)${NC}"
export PYTHONHTTPSVERIFY=0
export SSL_CERT_FILE=""

echo "=========================================="
echo "  OmicsOracle Unified Startup"
echo "  (SSL Bypass Mode)"
echo "=========================================="
echo ""

# Function to check if port is available
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        return 1
    fi
    return 0
}

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Shutting down services..."
    
    # Kill API server
    if [ ! -z "$API_PID" ] && kill -0 $API_PID 2>/dev/null; then
        kill $API_PID
        echo "  - API server stopped"
    fi
    
    # Kill dashboard
    if [ ! -z "$DASHBOARD_PID" ] && kill -0 $DASHBOARD_PID 2>/dev/null; then
        kill $DASHBOARD_PID
        echo "  - Dashboard stopped"
    fi
    
    echo "All services stopped."
    exit 0
}

# Register cleanup on script exit
trap cleanup SIGINT SIGTERM EXIT

# Check port availability
echo "Checking port availability..."

if ! check_port $API_PORT; then
    echo -e "${RED}[ERROR]${NC} Port $API_PORT is already in use"
    echo "  Run: lsof -ti:$API_PORT | xargs kill -9"
    exit 1
fi

if ! check_port $DASHBOARD_PORT; then
    echo -e "${RED}[ERROR]${NC} Port $DASHBOARD_PORT is already in use"
    echo "  Run: lsof -ti:$DASHBOARD_PORT | xargs kill -9"
    exit 1
fi

echo -e "${GREEN}[OK]${NC} Ports available"
echo ""

# Start API Server
echo "Starting API server (port $API_PORT)..."
python scripts/run_api.py --port $API_PORT > $API_LOG 2>&1 &
API_PID=$!
sleep 2

if ! kill -0 $API_PID 2>/dev/null; then
    echo -e "${RED}[ERROR]${NC} API server failed to start"
    echo "  Check logs: tail -f $API_LOG"
    exit 1
fi

echo -e "${GREEN}[OK]${NC} API server started (PID: $API_PID)"
echo "  - URL: http://localhost:$API_PORT"
echo "  - Logs: $API_LOG"
echo ""

# Start Dashboard
echo "Starting dashboard (port $DASHBOARD_PORT)..."
python scripts/run_dashboard.py --port $DASHBOARD_PORT > $DASHBOARD_LOG 2>&1 &
DASHBOARD_PID=$!
sleep 3

if ! kill -0 $DASHBOARD_PID 2>/dev/null; then
    echo -e "${RED}[ERROR]${NC} Dashboard failed to start"
    echo "  Check logs: tail -f $DASHBOARD_LOG"
    exit 1
fi

echo -e "${GREEN}[OK]${NC} Dashboard started (PID: $DASHBOARD_PID)"
echo "  - URL: http://localhost:$DASHBOARD_PORT"
echo "  - Logs: $DASHBOARD_LOG"
echo ""

# Verify both services are running
sleep 1

if curl -s http://localhost:$API_PORT/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} API health check passed"
else
    echo -e "${YELLOW}⚠${NC} API health check failed (may still be starting)"
fi

if curl -s http://localhost:$DASHBOARD_PORT > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Dashboard is responding"
else
    echo -e "${YELLOW}⚠${NC} Dashboard not responding yet (may still be starting)"
fi

echo ""
echo "=========================================="
echo "  Services Running!"
echo "=========================================="
echo ""
echo "  📊 Dashboard: http://localhost:$DASHBOARD_PORT"
echo "  🔌 API:       http://localhost:$API_PORT"
echo "  📝 Docs:      http://localhost:$API_PORT/docs"
echo ""
echo "  ⚠️  SSL verification: DISABLED"
echo "     (for institutional networks only)"
echo ""
echo "Logs:"
echo "  API:       tail -f $API_LOG"
echo "  Dashboard: tail -f $DASHBOARD_LOG"
echo ""
echo "Press CTRL+C to stop all services..."
echo ""

# Keep script running
while true; do
    # Check if processes are still alive
    if ! kill -0 $API_PID 2>/dev/null; then
        echo -e "${RED}[ERROR]${NC} API server died unexpectedly"
        exit 1
    fi
    
    if ! kill -0 $DASHBOARD_PID 2>/dev/null; then
        echo -e "${RED}[ERROR]${NC} Dashboard died unexpectedly"
        exit 1
    fi
    
    sleep 5
done
