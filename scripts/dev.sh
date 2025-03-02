#!/bin/bash

# Exit on error
set -e

# Define colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Function to cleanup background processes on exit
cleanup() {
  echo -e "${BLUE}Shutting down development servers...${NC}"
  # Kill all background processes
  kill $(jobs -p) 2>/dev/null || true
  exit 0
}

# Set up trap to catch SIGINT (Ctrl+C) and other termination signals
trap cleanup SIGINT SIGTERM EXIT

# Start the Python API server with watchfiles for hot reloading
echo -e "${GREEN}Starting Python API server with live reload...${NC}"
echo -e "${YELLOW}Watching for changes in Python files...${NC}"
watchfiles "poetry run python server.py --dev --host 127.0.0.1" . \
  --filter python \
  --ignore-paths "__pycache__" \
  --ignore-paths ".mypy_cache" \
  --ignore-paths "dist" \
  --ignore-paths "node_modules" \
  --ignore-paths "*.log" \
  --ignore-paths "*.log.*" &
API_PID=$!

# Wait a moment for the API to start
sleep 2

# Start frontend development server with hot reload
echo -e "${GREEN}Starting Bun/React frontend with hot reload...${NC}"
cd frontend && bun run dev --host &
FRONTEND_PID=$!

echo -e "${GREEN}Development servers running:${NC}"
echo -e "${BLUE}API server: http://127.0.0.1:8080${NC}"
echo -e "${BLUE}Frontend: http://127.0.0.1:5173${NC}"
echo -e "${GREEN}Press Ctrl+C to stop both servers${NC}"

# Wait for both processes to finish
wait $API_PID $FRONTEND_PID 