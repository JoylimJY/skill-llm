#!/bin/bash
set -e

cd /workspace

# Ensure memory-engine is available
if [ ! -d "node_modules/memory-engine" ]; then
    npm install memory-engine 2>&1 | tail -5
fi

# Verify the package installed correctly
node -e "const m = require('memory-engine'); console.log('memory-engine loaded, exports:', Object.keys(m).join(', '));" 2>&1 || echo "WARNING: memory-engine may not be fully functional yet"

# Create the data directory for memory storage
mkdir -p /workspace/data

echo "Setup complete."