#!/bin/bash
set -e

# Ensure node is available
node --version

# Ensure the tracker directory exists and is writable
mkdir -p /workspace/tracker
chmod 755 /workspace/tracker

echo "Setup complete. Node.js version: $(node --version)"