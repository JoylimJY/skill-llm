#!/usr/bin/env bash
set -e

# Make the checklist script executable
chmod +x /workspace/scripts/assembly_checklist.py

echo "Setup complete. Workspace ready."
echo "Script permissions:"
ls -la /workspace/scripts/assembly_checklist.py