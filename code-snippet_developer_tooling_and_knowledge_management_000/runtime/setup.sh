#!/bin/bash
set -e

cd /workspace

# Ensure scripts directory exists and snippet.py is executable
chmod +x scripts/snippet.py 2>/dev/null || true
chmod +x snippets.py 2>/dev/null || true

# Verify Python dependencies are available
python3 -c "import click, json, os" && echo "Dependencies OK"

echo "Setup complete. Workspace ready."
echo "Working directory: $(pwd)"
echo "Scripts available:"
ls -la scripts/