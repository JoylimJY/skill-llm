#!/bin/bash
set -e

# Ensure scripts are executable
chmod +x /workspace/scripts/scrape_dribbble.py
chmod +x /workspace/scripts/style_card.py

# Ensure data directory exists (agent should create it, but don't block)
mkdir -p /workspace/data

echo "Setup complete. Workspace ready."
ls -la /workspace/