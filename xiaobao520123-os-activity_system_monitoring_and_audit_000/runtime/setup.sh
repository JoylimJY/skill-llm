#!/bin/bash
set -e

# Run the workspace initialization script
python3 /tmp/gen_inputs.py

echo "Setup complete. OpenClaw workspace initialized."
echo "Skill scripts directory:"
ls -la ~/.openclaw/workspace/skills/os-activity/scripts/