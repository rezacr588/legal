#!/bin/bash

# UK Legal Training Dataset - Auto-Start Service Script
# This script manages Flask backend and React frontend lifecycle

set -e

# Configuration
PROJECT_DIR="/Users/rezazeraat/Desktop/Data"
DASHBOARD_DIR="$PROJECT_DIR/legal-dashboard"
LOG_DIR="/Users/rezazeraat/Library/Logs/uk-legal-dashboard"
FLASK_LOG="$LOG_DIR/flask.log"
REACT_LOG="$LOG_DIR/react.log"
SERVICE_LOG="$LOG_DIR/service.log"
FLASK_PID="$LOG_DIR/flask.pid"
REACT_PID="$LOG_DIR/react.pid"

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$SERVICE_LOG"
}

# Cleanup function for graceful shutdown
cleanup() {
    log "Received shutdown signal, stopping services..."

    # Stop React
    if [ -f "$REACT_PID" ]; then
        REACT_PROC=$(cat "$REACT_PID")
        if ps -p "$REACT_PROC" > /dev/null 2>&1; then
            log "Stopping React (PID: $REACT_PROC)..."
            kill "$REACT_PROC" 2>/dev/null || true
            # Also kill any child processes
            pkill -P "$REACT_PROC" 2>/dev/null || true
        fi
        rm -f "$REACT_PID"
    fi

    # Stop Flask
    if [ -f "$FLASK_PID" ]; then
        FLASK_PROC=$(cat "$FLASK_PID")
        if ps -p "$FLASK_PROC" > /dev/null 2>&1; then
            log "Stopping Flask (PID: $FLASK_PROC)..."
            kill "$FLASK_PROC" 2>/dev/null || true
        fi
        rm -f "$FLASK_PID"
    fi

    # Kill any remaining processes on ports
    log "Cleaning up ports..."
    lsof -ti:5000 2>/dev/null | xargs kill -9 2>/dev/null || true
    lsof -ti:5001 2>/dev/null | xargs kill -9 2>/dev/null || true
    lsof -ti:5173 2>/dev/null | xargs kill -9 2>/dev/null || true

    log "Services stopped successfully"
    exit 0
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT SIGHUP

# Check if services are already running
check_running() {
    if lsof -ti:5000 >/dev/null 2>&1 || lsof -ti:5173 >/dev/null 2>&1; then
        log "ERROR: Services already running on ports 5000 or 5173"
        log "Run 'bash /Users/rezazeraat/Desktop/Data/stop_service.sh' to stop them first"
        exit 1
    fi
}

# Start Flask backend
start_flask() {
    log "Starting Flask backend..."
    cd "$DASHBOARD_DIR"

    # Ensure Python dependencies are installed
    if ! python3 -c "import flask" 2>/dev/null; then
        log "Installing Flask dependencies..."
        pip3 install flask flask-cors polars groq cerebras_cloud_sdk >/dev/null 2>&1
    fi

    # Start Flask in background
    python3 api_server.py >> "$FLASK_LOG" 2>&1 &
    FLASK_PROC=$!
    echo "$FLASK_PROC" > "$FLASK_PID"

    log "Flask started (PID: $FLASK_PROC)"

    # Wait for Flask to be ready
    log "Waiting for Flask to be ready..."
    for i in {1..30}; do
        if curl -s http://localhost:5000/api/health >/dev/null 2>&1; then
            log "Flask is ready!"
            return 0
        fi
        sleep 1
    done

    log "WARNING: Flask may not be fully ready yet"
}

# Start React frontend
start_react() {
    log "Starting React frontend..."
    cd "$DASHBOARD_DIR"

    # Ensure Node dependencies are installed
    if [ ! -d "node_modules" ]; then
        log "Installing Node dependencies..."
        npm install >/dev/null 2>&1
    fi

    # Start React dev server in background
    npm run dev >> "$REACT_LOG" 2>&1 &
    REACT_PROC=$!
    echo "$REACT_PROC" > "$REACT_PID"

    log "React started (PID: $REACT_PROC)"

    # Wait for React to be ready
    log "Waiting for React to be ready..."
    for i in {1..60}; do
        if curl -s http://localhost:5173 >/dev/null 2>&1; then
            log "React is ready!"
            return 0
        fi
        sleep 1
    done

    log "WARNING: React may not be fully ready yet"
}

# Monitor processes
monitor() {
    log "Monitoring services... (Press Ctrl+C to stop)"

    while true; do
        # Check Flask
        if [ -f "$FLASK_PID" ]; then
            FLASK_PROC=$(cat "$FLASK_PID")
            if ! ps -p "$FLASK_PROC" > /dev/null 2>&1; then
                log "ERROR: Flask process died! Restarting..."
                start_flask
            fi
        fi

        # Check React
        if [ -f "$REACT_PID" ]; then
            REACT_PROC=$(cat "$REACT_PID")
            if ! ps -p "$REACT_PROC" > /dev/null 2>&1; then
                log "ERROR: React process died! Restarting..."
                start_react
            fi
        fi

        sleep 10
    done
}

# Main execution
main() {
    log "=========================================="
    log "UK Legal Dashboard - Service Starting"
    log "=========================================="

    check_running
    start_flask
    sleep 3
    start_react

    log "=========================================="
    log "Services started successfully!"
    log "Flask: http://localhost:5000"
    log "React: http://localhost:5173"
    log "Logs: $LOG_DIR"
    log "=========================================="

    monitor
}

# Run main function
main
