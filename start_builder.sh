#!/bin/bash

# Kill any existing processes on ports 8000 (API) and 5173 (UI) to avoid conflicts
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:5173 | xargs kill -9 2>/dev/null

echo "Starting Backend..."
./.venv/bin/python3 simulation-builder/api.py &
BACKEND_PID=$!

echo "Starting Frontend..."
cd simulation-builder/ui
npm run dev &
FRONTEND_PID=$!

# Handle shutdown
trap "kill $BACKEND_PID $FRONTEND_PID; exit" SIGINT SIGTERM

wait
