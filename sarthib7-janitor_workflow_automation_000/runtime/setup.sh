#!/bin/bash
set -e

# Ensure workspace permissions
chmod -R 755 /workspace

# Verify the Janitor library is present
if [ ! -f /workspace/janitor/src/Janitor.js ]; then
  echo "ERROR: Janitor.js not found"
  exit 1
fi

echo "Setup complete. Workspace ready."
echo "Janitor library: /workspace/janitor/src/Janitor.js"
echo "Project to clean: /workspace/fintech_project/"