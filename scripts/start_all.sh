#!/bin/bash

echo "🚀 Starting All Services..."

# Start backend in background
cd "$(dirname "$0")/../backend"
python3 app.py > /tmp/backend.log 2>&1 &
BACKEND_PID=$!

# Start frontend in background
cd ../frontend
npm run dev > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!

echo "✅ Backend started (PID: $BACKEND_PID)"
echo "✅ Frontend started (PID: $FRONTEND_PID)"
echo ""
echo "📊 Backend: http://localhost:5000"
echo "🎨 Frontend: http://localhost:5173"
echo ""
echo "Logs:"
echo "  Backend: tail -f /tmp/backend.log"
echo "  Frontend: tail -f /tmp/frontend.log"
echo ""
echo "To stop services, run: ./scripts/stop_all.sh"
