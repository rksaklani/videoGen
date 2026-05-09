#!/bin/bash
# Stop all videoGen processes
echo "Stopping videoGen..."
kill $(lsof -t -i:8000) 2>/dev/null && echo "Stopped Backend (port 8000)" || echo "Backend not running"
kill $(lsof -t -i:3000) 2>/dev/null && echo "Stopped Frontend (port 3000)" || echo "Frontend not running"
echo "Done."
