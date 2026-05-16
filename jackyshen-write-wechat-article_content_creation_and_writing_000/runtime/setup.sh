#!/bin/bash
set -e

echo "Setting up workspace permissions..."
chmod -R 755 /workspace
chmod +x /workspace/tools/scripts/word_counter.sh 2>/dev/null || true

echo "Setup complete."