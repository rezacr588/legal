#!/bin/bash

# UK Legal Dataset - Start Frontend & Backend
# This script starts the Flask API backend and React frontend

set -e

echo "🚀 Starting UK Legal Dataset Applications..."

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to cleanup background processes on exit
cleanup() {
    echo -e "\n${YELLOW}Shutting down applications...${NC}"
    if [ ! -z "$REACT_PID" ]; then
        kill $REACT_PID 2>/dev/null || true
    fi
    if [ ! -z "$FLASK_PID" ]; then
        kill $FLASK_PID 2>/dev/null || true
    fi
    echo -e "${GREEN}✓ Cleanup complete${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Kill any existing processes on the ports
echo -e "${BLUE}Cleaning up existing processes...${NC}"
lsof -ti:8501 | xargs kill -9 2>/dev/null || true
lsof -ti:5173 | xargs kill -9 2>/dev/null || true
lsof -ti:5000 | xargs kill -9 2>/dev/null || true
sleep 2

# Start Flask API Server
echo -e "${BLUE}Starting Flask API server on port 5000...${NC}"
cd legal-dashboard
python3 api_server.py > /tmp/flask.log 2>&1 &
FLASK_PID=$!
echo -e "${GREEN}✓ Flask API started (PID: $FLASK_PID)${NC}"

# Wait for backend to be ready
echo -e "${BLUE}Waiting for backend to initialize...${NC}"
sleep 3

# Start React Frontend
echo -e "${BLUE}Starting React frontend on port 5173...${NC}"
npm run dev > /tmp/react.log 2>&1 &
REACT_PID=$!
cd ..
echo -e "${GREEN}✓ React started (PID: $REACT_PID)${NC}"

# Display access information
echo ""
echo -e "${GREEN}════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ All applications started successfully!${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}⚛️  React Dashboard:${NC} http://localhost:5173"
echo -e "${BLUE}🔌 Flask API:${NC}        http://localhost:5000/api/health"
echo ""
echo -e "${YELLOW}API Endpoints:${NC}"
echo -e "  GET  /api/data                    - Get all samples"
echo -e "  GET  /api/stats                   - Get dataset statistics"
echo -e "  GET  /api/topics                  - Get available topics"
echo -e "  POST /api/generate                - Generate single sample"
echo -e "  POST /api/generate/batch/start    - Start batch generation"
echo -e "  POST /api/generate/batch/stop     - Stop batch generation"
echo -e "  GET  /api/generate/batch/status   - Get batch status"
echo -e "  POST /api/add                     - Add sample to dataset"
echo -e "  GET  /api/health                  - Health check"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all applications${NC}"
echo ""

# Monitor logs in the foreground
echo -e "${BLUE}Tailing logs (Ctrl+C to stop all services)...${NC}"
echo ""
tail -f /tmp/flask.log /tmp/react.log
