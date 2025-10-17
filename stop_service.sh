#!/bin/bash

# UK Legal Training Dataset - Stop Service Script

set -e

LOG_DIR="/Users/rezazeraat/Library/Logs/uk-legal-dashboard"
SERVICE_LOG="$LOG_DIR/service.log"
FLASK_PID="$LOG_DIR/flask.pid"
REACT_PID="$LOG_DIR/react.pid"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    [ -d "$LOG_DIR" ] && echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$SERVICE_LOG"
}

log "Stopping UK Legal Dashboard services..."

# Stop React
if [ -f "$REACT_PID" ]; then
    REACT_PROC=$(cat "$REACT_PID")
    if ps -p "$REACT_PROC" > /dev/null 2>&1; then
        log "Stopping React (PID: $REACT_PROC)..."
        kill "$REACT_PROC" 2>/dev/null || true
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

# Force kill any remaining processes on ports
log "Cleaning up ports..."
lsof -ti:5000 2>/dev/null | xargs kill -9 2>/dev/null || true
lsof -ti:5001 2>/dev/null | xargs kill -9 2>/dev/null || true
lsof -ti:5173 2>/dev/null | xargs kill -9 2>/dev/null || true

log "Services stopped successfully!"
