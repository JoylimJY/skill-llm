#!/bin/bash
set -e

# Make neon-soul.mjs executable
chmod +x /workspace/scripts/neon-soul.mjs

# Verify Node 22+
node --version

# Create output directory
mkdir -p /workspace/output

# Verify memory files exist
ls /workspace/consultant-memory/

echo "Setup complete. Workspace ready for agent."