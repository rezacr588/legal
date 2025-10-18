#!/bin/bash

echo "🛑 Stopping All Services..."

# Kill backend (port 5000)
lsof -ti:5000 | xargs kill -9 2>/dev/null
echo "✅ Backend stopped"

# Kill frontend (port 5173)
lsof -ti:5173 | xargs kill -9 2>/dev/null
echo "✅ Frontend stopped"

echo ""
echo "All services stopped successfully."
