#!/bin/bash
# dev.sh — start the full AchieveCX dev environment

ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "🚀 Starting AchieveCX dev environment..."

# Start backend
echo "▶ Starting FastAPI backend on port 8000..."
cd "$ROOT/backend"
source venv/bin/activate
uvicorn api.main:app --reload --port 8000 &
BACKEND_PID=$!

# Start frontend
echo "▶ Starting Next.js frontend on port 3000..."
cd "$ROOT/frontend"
npm run dev &
FRONTEND_PID=$!

# Wait for servers to be ready then open browser
echo "⏳ Waiting for servers to start..."
sleep 4
open http://localhost:3000

echo ""
echo "✅ Running!"
echo "   Frontend: http://localhost:3000"
echo "   Backend:  http://localhost:8000"
echo "   API docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers."

# Wait and clean up on exit
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo 'Stopped.'" EXIT
wait