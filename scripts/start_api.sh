#!/bin/bash
#===========================================================
# PharmaKG API Server Startup Script
#===========================================================
# Description: Starts the FastAPI backend server
# Usage: ./scripts/start_api.sh [port]
#===========================================================

# Set default port
PORT=${1:-8000}

# Activate conda environment
source /root/miniconda3/etc/profile.d/conda.sh
conda activate pharmakg-api

# Change to project directory
cd /root/autodl-tmp/pj-pharmaKG

# Kill any existing uvicorn processes on this port
echo "Stopping any existing uvicorn processes on port $PORT..."
pkill -9 -f "uvicorn.*$PORT" 2>/dev/null
sleep 1

# Start the server
echo "Starting PharmaKG API server on port $PORT..."
echo "Logs will be written to /tmp/api.log"
echo "Press Ctrl+C to stop"

/root/miniconda3/envs/pharmakg-api/bin/python3 << EOF
import uvicorn
import sys
import os

os.chdir('/root/autodl-tmp/pj-pharmaKG')
sys.path.insert(0, '/root/autodl-tmp/pj-pharmaKG')

print("Starting uvicorn...")
uvicorn.run("api.main:app", host="0.0.0.0", port=$PORT, log_level="info")
EOF
