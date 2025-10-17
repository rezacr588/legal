#!/bin/bash

# UK Legal Training Dataset - Auto-Start Uninstallation Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/Users/rezazeraat/Desktop/Data"
PLIST_DEST="$HOME/Library/LaunchAgents/com.uklegaldashboard.service.plist"
LOG_DIR="$HOME/Library/Logs/uk-legal-dashboard"

echo -e "${RED}=========================================="
echo "UK Legal Dashboard - Auto-Start Removal"
echo -e "==========================================${NC}"

# Step 1: Unload LaunchAgent
echo -e "\n${GREEN}[1/4]${NC} Unloading LaunchAgent..."
if [ -f "$PLIST_DEST" ]; then
    launchctl unload "$PLIST_DEST" 2>/dev/null || true
    echo -e "  ✓ LaunchAgent unloaded"
else
    echo -e "  ${YELLOW}⚠${NC} LaunchAgent not found (may already be removed)"
fi

# Step 2: Stop services
echo -e "\n${GREEN}[2/4]${NC} Stopping services..."
cd "$PROJECT_DIR"
bash stop_service.sh 2>/dev/null || true
echo -e "  ✓ Services stopped"

# Step 3: Remove LaunchAgent plist
echo -e "\n${GREEN}[3/4]${NC} Removing LaunchAgent plist..."
if [ -f "$PLIST_DEST" ]; then
    rm -f "$PLIST_DEST"
    echo -e "  ✓ LaunchAgent plist removed"
else
    echo -e "  ${YELLOW}⚠${NC} LaunchAgent plist not found"
fi

# Step 4: Clean up (optional)
echo -e "\n${GREEN}[4/4]${NC} Cleanup options..."
echo -e "${YELLOW}Do you want to remove log files? (y/N):${NC}"
read -r -n 1 response
echo

if [[ "$response" =~ ^([yY])$ ]]; then
    if [ -d "$LOG_DIR" ]; then
        rm -rf "$LOG_DIR"
        echo -e "  ✓ Log directory removed"
    else
        echo -e "  ${YELLOW}⚠${NC} Log directory not found"
    fi
else
    echo -e "  ✓ Log files preserved at: $LOG_DIR"
fi

# Final status
echo -e "\n${GREEN}=========================================="
echo "Uninstallation Complete!"
echo -e "==========================================${NC}"
echo -e "${GREEN}✓${NC} Auto-start disabled"
echo -e "${GREEN}✓${NC} Services stopped"
echo -e "${GREEN}✓${NC} LaunchAgent removed"

echo -e "\n${GREEN}What's next:${NC}"
echo "  - The dashboard will no longer start automatically"
echo "  - To start manually: bash $PROJECT_DIR/start_service.sh"
echo "  - To re-enable auto-start: bash $PROJECT_DIR/install_autostart.sh"

if [ -d "$LOG_DIR" ]; then
    echo "  - Logs still available at: $LOG_DIR"
fi

echo -e "\n${GREEN}=========================================${NC}"
