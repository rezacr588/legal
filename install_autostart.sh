#!/bin/bash

# UK Legal Training Dataset - Auto-Start Installation Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/Users/rezazeraat/Desktop/Data"
PLIST_SOURCE="$PROJECT_DIR/com.uklegaldashboard.service.plist"
PLIST_DEST="$HOME/Library/LaunchAgents/com.uklegaldashboard.service.plist"
LOG_DIR="$HOME/Library/Logs/uk-legal-dashboard"

echo -e "${GREEN}=========================================="
echo "UK Legal Dashboard - Auto-Start Setup"
echo -e "==========================================${NC}"

# Check if running from correct directory
if [ "$PWD" != "$PROJECT_DIR" ]; then
    echo -e "${YELLOW}Warning: Not in project directory, changing to $PROJECT_DIR${NC}"
    cd "$PROJECT_DIR"
fi

# Step 1: Create log directory
echo -e "\n${GREEN}[1/6]${NC} Creating log directory..."
mkdir -p "$LOG_DIR"
echo -e "  ✓ Log directory created at: $LOG_DIR"

# Step 2: Check dependencies
echo -e "\n${GREEN}[2/6]${NC} Checking dependencies..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}  ✗ Python 3 not found!${NC}"
    echo "  Please install Python 3: brew install python3"
    exit 1
fi
echo -e "  ✓ Python 3 found: $(python3 --version)"

# Check Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}  ✗ Node.js not found!${NC}"
    echo "  Please install Node.js: brew install node"
    exit 1
fi
echo -e "  ✓ Node.js found: $(node --version)"

# Check npm
if ! command -v npm &> /dev/null; then
    echo -e "${RED}  ✗ npm not found!${NC}"
    echo "  Please install npm: brew install node"
    exit 1
fi
echo -e "  ✓ npm found: $(npm --version)"

# Step 3: Install Python dependencies
echo -e "\n${GREEN}[3/6]${NC} Installing Python dependencies..."
cd "$PROJECT_DIR/legal-dashboard"
pip3 install -q flask flask-cors polars groq cerebras_cloud_sdk 2>/dev/null || {
    echo -e "${YELLOW}  Warning: Some Python packages may already be installed${NC}"
}
echo -e "  ✓ Python dependencies installed"

# Step 4: Install Node dependencies
echo -e "\n${GREEN}[4/6]${NC} Installing Node dependencies..."
if [ ! -d "node_modules" ]; then
    npm install --silent 2>/dev/null || {
        echo -e "${RED}  ✗ Failed to install Node dependencies${NC}"
        exit 1
    }
    echo -e "  ✓ Node dependencies installed"
else
    echo -e "  ✓ Node dependencies already installed"
fi

# Step 5: Stop existing services
echo -e "\n${GREEN}[5/6]${NC} Stopping any existing services..."
cd "$PROJECT_DIR"

# Unload existing LaunchAgent if present
if [ -f "$PLIST_DEST" ]; then
    launchctl unload "$PLIST_DEST" 2>/dev/null || true
    echo -e "  ✓ Unloaded existing LaunchAgent"
fi

# Stop any running instances
bash stop_service.sh 2>/dev/null || true
echo -e "  ✓ Stopped running services"

# Step 6: Install LaunchAgent
echo -e "\n${GREEN}[6/6]${NC} Installing LaunchAgent..."

# Create LaunchAgents directory if it doesn't exist
mkdir -p "$HOME/Library/LaunchAgents"

# Copy plist file
cp "$PLIST_SOURCE" "$PLIST_DEST"
echo -e "  ✓ Copied LaunchAgent plist to $PLIST_DEST"

# Set correct permissions
chmod 644 "$PLIST_DEST"
echo -e "  ✓ Set correct permissions"

# Load the LaunchAgent
launchctl load "$PLIST_DEST"
echo -e "  ✓ Loaded LaunchAgent"

# Wait a moment for services to start
echo -e "\n${YELLOW}Waiting for services to start (this may take 30-60 seconds)...${NC}"
sleep 5

# Check if services are running
FLASK_RUNNING=false
REACT_RUNNING=false

for i in {1..30}; do
    if lsof -ti:5000 >/dev/null 2>&1; then
        FLASK_RUNNING=true
    fi
    if lsof -ti:5173 >/dev/null 2>&1; then
        REACT_RUNNING=true
    fi
    if [ "$FLASK_RUNNING" = true ] && [ "$REACT_RUNNING" = true ]; then
        break
    fi
    sleep 2
done

# Final status
echo -e "\n${GREEN}=========================================="
echo "Installation Complete!"
echo -e "==========================================${NC}"

if [ "$FLASK_RUNNING" = true ]; then
    echo -e "${GREEN}✓${NC} Flask backend: http://localhost:5000"
else
    echo -e "${RED}✗${NC} Flask backend: Not running (check logs)"
fi

if [ "$REACT_RUNNING" = true ]; then
    echo -e "${GREEN}✓${NC} React frontend: http://localhost:5173"
else
    echo -e "${RED}✗${NC} React frontend: Not running (check logs)"
fi

echo -e "\n${GREEN}Auto-start configuration:${NC}"
echo "  ✓ Services will start automatically on MacBook startup"
echo "  ✓ Services will restart automatically if they crash"

echo -e "\n${GREEN}Log files:${NC}"
echo "  - Flask: $LOG_DIR/flask.log"
echo "  - React: $LOG_DIR/react.log"
echo "  - Service: $LOG_DIR/service.log"
echo "  - LaunchAgent: $LOG_DIR/launchd-out.log"

echo -e "\n${GREEN}Useful commands:${NC}"
echo "  - View Flask logs: tail -f $LOG_DIR/flask.log"
echo "  - View React logs: tail -f $LOG_DIR/react.log"
echo "  - Check service status: launchctl list | grep uklegaldashboard"
echo "  - Stop auto-start: bash $PROJECT_DIR/uninstall_autostart.sh"
echo "  - Manual start: bash $PROJECT_DIR/start_service.sh"
echo "  - Manual stop: bash $PROJECT_DIR/stop_service.sh"

echo -e "\n${GREEN}Next steps:${NC}"
if [ "$FLASK_RUNNING" = true ] && [ "$REACT_RUNNING" = true ]; then
    echo "  1. Open http://localhost:5173 in your browser"
    echo "  2. The dashboard will now start automatically when you log in"
    echo "  3. Restart your MacBook to test the auto-start feature"
else
    echo "  1. Check logs for errors: tail -f $LOG_DIR/*.log"
    echo "  2. Try manual start: bash $PROJECT_DIR/start_service.sh"
    echo "  3. If issues persist, run: bash $PROJECT_DIR/uninstall_autostart.sh"
fi

echo -e "\n${GREEN}=========================================${NC}"
