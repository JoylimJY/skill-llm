#!/bin/bash
set -e

# Ensure node is available
node --version

# Ensure the health-tracker directory exists and is writable
chmod -R 755 /workspace/health-tracker/

echo "Setup complete. health-data.json does not exist yet."
ls /workspace/health-tracker/