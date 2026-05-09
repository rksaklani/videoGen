#!/bin/bash
# Stop all Avatar Studio processes
echo "Stopping Avatar Studio..."
kill $(lsof -t -i:8000) 2>/dev/null && echo "Stopped Backend (port 8000)" || echo "Backend not running"
kill $(lsof -t -i:3000) 2>/dev/null && echo "Stopped Frontend (port 3000)" || echo "Frontend not running"
echo "Done."
