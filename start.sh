#!/bin/bash
# Avatar Studio — Start Backend + Frontend with one command
# Usage: bash start.sh

set -e

echo "🎬 Avatar Studio — Starting..."
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# Kill any existing processes on our ports
kill $(lsof -t -i:8000) 2>/dev/null && echo "Freed port 8000" || true
kill $(lsof -t -i:3000) 2>/dev/null && echo "Freed port 3000" || true

# Kill any leftover Python GPU processes
pkill -9 -f "python.*Backend" 2>/dev/null || true
pkill -9 pt_main_thread 2>/dev/null || true
sleep 2

# Activate conda
source $(conda info --base)/etc/profile.d/conda.sh
conda activate VideoGen

# Set environment
export LD_LIBRARY_PATH=$CONDA_PREFIX/lib:$LD_LIBRARY_PATH
export PYTHONPATH=$(pwd)

# Create required directories
mkdir -p Backend/data/uploads Backend/data/outputs Backend/data/temp Backend/logs

# Start Backend (background)
echo -e "${BLUE}Starting Backend on port 8000...${NC}"
python -m Backend.main > Backend/logs/server.log 2>&1 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"

# Wait for backend to be ready
echo -n "Waiting for models to load"
for i in $(seq 1 180); do
    if curl -s http://localhost:8000/api/v1/health > /dev/null 2>&1; then
        echo ""
        echo -e "${GREEN}✅ Backend ready!${NC}"
        break
    fi
    echo -n "."
    sleep 2
done

# Start Frontend (background)
echo -e "${BLUE}Starting Frontend on port 3000...${NC}"
npm run dev --prefix Frontend > Backend/logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "Frontend PID: $FRONTEND_PID"
sleep 3

echo ""
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo -e "${GREEN}  🎬 Avatar Studio is Running!          ${NC}"
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo ""
echo -e "  Frontend:  ${BLUE}http://localhost:3000${NC}"
echo -e "  API Docs:  ${BLUE}http://localhost:8000/docs${NC}"
echo -e "  Health:    ${BLUE}http://localhost:8000/api/v1/health${NC}"
echo ""
echo -e "  Backend PID:  $BACKEND_PID"
echo -e "  Frontend PID: $FRONTEND_PID"
echo ""
echo -e "  Press ${RED}Ctrl+C${NC} to stop everything"
echo ""

# Trap Ctrl+C to kill both processes
cleanup() {
    echo ""
    echo "Shutting down..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "Done."
    exit 0
}
trap cleanup SIGINT SIGTERM

# Keep running and show backend logs
tail -f Backend/logs/server.log
