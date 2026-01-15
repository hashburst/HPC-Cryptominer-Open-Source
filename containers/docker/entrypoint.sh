#!/bin/bash

# HPC Cryptominer Entrypoint Script for Docker
set -e

echo "Starting HPC Cryptominer..."
echo "Container: Docker (Ubuntu 24.04)"
echo "User: $(whoami)"
echo "Working Directory: $(pwd)"

# Create log directory if it doesn't exist
mkdir -p /app/logs

# Initialize hardware detection
echo "Detecting hardware..."
python3 -c "
import sys
sys.path.append('/app')
from mining_engine.hardware import HardwareManager
import asyncio

async def detect():
    hw = HardwareManager()
    await hw.initialize()
    print('Hardware detection completed')

asyncio.run(detect())
"

# Check for GPU support
echo "Checking GPU support..."
nvidia-smi > /dev/null 2>&1 && echo "NVIDIA GPU detected" || echo "No NVIDIA GPU detected"
rocm-smi > /dev/null 2>&1 && echo "AMD GPU detected" || echo "No AMD GPU detected"

# Set up environment
export PYTHONPATH="/app:$PYTHONPATH"
export PYTHONUNBUFFERED=1

# Check for configuration file
if [ ! -f "/app/config/mining_config.json" ]; then
    echo "Creating default configuration..."
    python3 /app/create_default_config.py
fi

# Start services based on environment variables
if [ "$MINING_MODE" = "standalone" ]; then
    echo "Starting in standalone mining mode..."
    exec python3 /app/main.py --mode=standalone
elif [ "$MINING_MODE" = "cluster" ]; then
    echo "Starting in cluster mode..."
    exec python3 /app/main.py --mode=cluster
elif [ "$MINING_MODE" = "node" ]; then
    echo "Starting as cluster node..."
    exec python3 /app/main.py --mode=node --cluster-master="$CLUSTER_MASTER"
else
    echo "Starting with supervisor (default)..."
    exec "$@"
fi